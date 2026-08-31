#!/usr/bin/env python3
"""VPS-1 autonomous data factory. Training is deliberately out of scope."""
import hashlib,json,os,re,time,subprocess,sys,tempfile
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request,urlopen
ROOT=Path(os.getenv('PROJECT_HOME',Path.home()/'training-data-agent')); DATA=ROOT/'data'; RAW=DATA/'raw'; OUT=DATA/'dataset'; INBOX=DATA/'inbox'; REVIEW=DATA/'review'; LOG=DATA/'logs'
for p in (RAW,OUT,INBOX,REVIEW,LOG): p.mkdir(parents=True,exist_ok=True)
MODEL=os.getenv('MODEL',''); VERIFY_MODEL=os.getenv('VERIFIER_MODEL',''); OLLAMA=os.getenv('OLLAMA_URL','http://127.0.0.1:11434'); INTERVAL=int(os.getenv('INTERVAL','1800')); MAX=int(os.getenv('MAX_SOURCE_CHARS','30000'))
DOMAINS={'reasoning':['logic','mathematical reasoning','problem solving','scientific reasoning'],'coding':['software engineering','algorithms','programming','debugging'],'trading':['market microstructure','portfolio risk','financial econometrics','backtesting']}
def get(u,t=30):
 r=Request(u,headers={'User-Agent':'training-data-factory/1.0'}); return urlopen(r,timeout=t).read().decode('utf-8','ignore')
def put(obj):
 s=json.dumps(obj,ensure_ascii=False,sort_keys=True); h=hashlib.sha256(s.encode()).hexdigest(); p=RAW/f'{h}.json'
 if not p.exists(): p.write_text(s,encoding='utf-8'); return True
 return False
def discover():
 for domain,terms in DOMAINS.items():
  for q in terms:
   try:
    xml=get('https://export.arxiv.org/api/query?search_query=all:%22'+quote(q)+'%22&start=0&max_results=10')
    for m in re.findall(r'<entry>(.*?)</entry>',xml,re.S):
     link=re.search(r'<id>(.*?)</id>',m); title=re.search(r'<title>(.*?)</title>',m,re.S); summary=re.search(r'<summary>(.*?)</summary>',m,re.S)
     if link and summary: put({'source':link.group(1).strip(),'domain':domain,'title':re.sub(r'\s+',' ',title.group(1) if title else ''),'text':re.sub(r'\s+',' ',summary.group(1))[:MAX],'license_status':'needs_source_review','source_type':'arxiv_metadata'})
   except Exception as e: print('[discover]',e)
def ingest_inbox():
 for p in INBOX.glob('*'):
  if p.suffix.lower() not in {'.txt','.md','.json','.jsonl','.pdf','.html','.htm'}: continue
  try:
   if p.suffix.lower() in {'.pdf','.html','.htm'}:
    sys.path.insert(0,str(ROOT)); from extractors.document_extract import extract; text=extract(p)
   else:text=p.read_text(encoding='utf-8',errors='ignore')
   put({'source':str(p),'domain':'reasoning','title':p.name,'text':text[:MAX],'license_status':'user_supplied_review_required','source_type':'local_import'}); p.rename(REVIEW/p.name)
  except Exception as e: print('[inbox]',p,e)
def llm(prompt,model=None):
 model=model or MODEL
 if not model:return None
 try:
  body=json.dumps({'model':model,'prompt':prompt,'stream':False,'options':{'temperature':0.1}}).encode(); req=Request(OLLAMA+'/api/generate',data=body,headers={'Content-Type':'application/json'}); return json.loads(urlopen(req,timeout=180).read()).get('response','')
 except Exception as e: print('[llm]',e); return None
def make(d):
 prompt=f'''Bạn đang tạo dữ liệu huấn luyện bằng tiếng Việt. Hãy tạo DUY NHẤT một ví dụ huấn luyện thận trọng dưới dạng JSON hợp lệ, không markdown.
Các trường bắt buộc: messages, domain, source, source_type, quality.
Không bịa thông tin và không suy diễn vượt quá nguồn.
Reasoning: nêu bài toán, các bước chính ngắn gọn, đáp án và kiểm tra kết quả; không lưu chain-of-thought ẩn.
Coding: nêu nhiệm vụ, giải pháp và kiểm thử/hành vi mong đợi.
Trading: chỉ tập trung khái niệm, thống kê, rủi ro, cấu trúc thị trường, backtesting và phân tích kịch bản; không đưa lời khuyên cá nhân và không bịa lợi nhuận.
Ưu tiên nội dung tiếng Việt nếu nguồn cho phép; nếu nguồn là tiếng Anh thì diễn đạt kết quả bằng tiếng Việt.
Source={d['source']} Domain={d['domain']} Text={d['text'][:MAX]}'''
 raw=llm(prompt)
 if raw:
  try:return json.loads(raw.strip().removeprefix('```json').removesuffix('```').strip())
  except:pass
 return {'messages':[{'role':'user','content':f'Hãy giải thích bằng tiếng Việt các ý chính của nguồn thuộc lĩnh vực {d["domain"]}.'},{'role':'assistant','content':d['text'][:4000]}],'domain':d['domain'],'source':d['source'],'source_type':d.get('source_type','source'),'quality':{'needs_review':True,'generated':False}}
def ai_verify(o):
 if not VERIFY_MODEL:return {'decision':'REVIEW','reason':'no verifier model configured'}
 prompt='Kiểm tra ví dụ huấn luyện sau bằng tiếng Việt về căn cứ sự thật, tính nhất quán, tuyên bố không được nguồn hỗ trợ, an toàn lĩnh vực và mức phù hợp nhiệm vụ/đáp án. Chỉ trả JSON với decision PASS|REVIEW|REJECT, score 0..1, issues array. Không tiết lộ chain-of-thought ẩn. '+json.dumps(o,ensure_ascii=False)
 raw=llm(prompt,VERIFY_MODEL)
 try:return json.loads(raw.strip().removeprefix('```json').removesuffix('```').strip())
 except:return {'decision':'REVIEW','reason':'invalid verifier response'}
def valid(o):return isinstance(o,dict) and o.get('domain') in DOMAINS and isinstance(o.get('messages'),list) and len(o['messages'])>=2 and all(isinstance(x,dict) and x.get('role') in ('user','assistant') and isinstance(x.get('content'),str) and x['content'].strip() for x in o['messages'])
def process():
 out=OUT/'all.jsonl'; seen=set()
 if out.exists():
  for l in out.read_text(encoding='utf-8').splitlines():
   seen.add(hashlib.sha256(l.encode()).hexdigest())
 for p in RAW.glob('*.json'):
  try:
   d=json.loads(p.read_text(encoding='utf-8')); o=make(d)
   if not valid(o): continue
   o['source']=d['source'];o['domain']=d['domain'];o.setdefault('quality',{})['license_status']=d.get('license_status','unknown')
   v=ai_verify(o);o['quality']['verifier']=v
   if v.get('decision')=='REJECT': continue
   line=json.dumps(o,ensure_ascii=False); h=hashlib.sha256(line.encode()).hexdigest()
   if h not in seen: out.open('a',encoding='utf-8').write(line+'\n');seen.add(h)
  except Exception as e:print('[process]',p,e)
def split():
 src=OUT/'all.jsonl'; rows=[]
 if not src.exists():return
 for l in src.read_text(encoding='utf-8').splitlines():
  try: rows.append(json.loads(l))
  except:pass
 b={'train':[],'validation':[],'test':[]}
 for r in rows:
  h=int(hashlib.sha256(r['source'].encode()).hexdigest()[:8],16)%100;b['test' if h<10 else 'validation' if h<20 else 'train'].append(r)
 for n,a in b.items():(OUT/f'{n}.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in a),encoding='utf-8')
 (OUT/'stats.json').write_text(json.dumps({'total':len(rows),**{k:len(v) for k,v in b.items()}},indent=2),encoding='utf-8')
def run():
 print('VPS-1 data factory started; training is disabled here; language=vi.')
 while True:
  discover();ingest_inbox();process();split()
  if os.getenv('ONCE','0')=='1':return
  time.sleep(INTERVAL)
if __name__=='__main__':run()
