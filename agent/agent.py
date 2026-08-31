#!/usr/bin/env python3
"""Autonomous training-data pipeline for reasoning, coding and trading."""
import hashlib, json, os, re, time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT=Path(os.getenv("PROJECT_HOME",Path.home()/"training-data-agent")); DATA=ROOT/"data"; RAW=DATA/"raw"; OUT=DATA/"dataset"; STATE=DATA/"state.json"
for p in (RAW,OUT): p.mkdir(parents=True,exist_ok=True)
MODEL=os.getenv("MODEL",""); OLLAMA=os.getenv("OLLAMA_URL","http://127.0.0.1:11434"); INTERVAL=int(os.getenv("INTERVAL","1800")); MAX_DOC=int(os.getenv("MAX_DOC_CHARS","30000"))
DOMAINS={"reasoning":["reasoning","logic","problem solving","mathematical reasoning"],"coding":["software engineering","programming","algorithms","code review"],"trading":["market microstructure","portfolio risk","financial econometrics","backtesting"]}

def get(url,timeout=30):
    req=Request(url,headers={"User-Agent":"training-data-agent/1.0"})
    with urlopen(req,timeout=timeout) as r:return r.read().decode("utf-8","ignore")
def save_raw(text,source,domain,license_status="unknown"):
    h=hashlib.sha256((source+text).encode()).hexdigest(); p=RAW/f"{h}.json"
    if not p.exists(): p.write_text(json.dumps({"source":source,"domain":domain,"text":text,"license_status":license_status},ensure_ascii=False),encoding="utf-8")

def discover():
    found=[]
    for domain,terms in DOMAINS.items():
        for q in terms:
            try:
                xml=get("https://export.arxiv.org/api/query?search_query=all:%22"+quote(q)+"%22&start=0&max_results=5")
                for m in re.findall(r'<entry>(.*?)</entry>',xml,re.S):
                    link=re.search(r'<id>(.*?)</id>',m); title=re.search(r'<title>(.*?)</title>',m,re.S); summary=re.search(r'<summary>(.*?)</summary>',m,re.S)
                    if link and summary: found.append((domain,link.group(1).strip(),re.sub(r'\s+',' ',(title.group(1) if title else '')+' '+summary.group(1))))
            except Exception as e: print('[discover]',e)
    return found

def ingest_discovered():
    n=0
    for domain,url,text in discover():
        try: save_raw(text,url,domain,"source-specific-review-required"); n+=1
        except Exception as e: print('[ingest]',e)
    return n

def llm(prompt):
    if not MODEL:return None
    try:
        body=json.dumps({"model":MODEL,"prompt":prompt,"stream":False,"options":{"temperature":0.15}}).encode()
        req=Request(f"{OLLAMA}/api/generate",data=body,headers={"Content-Type":"application/json","User-Agent":"training-data-agent/1.0"})
        with urlopen(req,timeout=180) as r:return json.loads(r.read()).get("response","")
    except Exception as e: print('[llm]',e); return None

def fallback(text,domain,source):
    return {"messages":[{"role":"user","content":f"Analyze this {domain} material and answer using only the evidence provided."},{"role":"assistant","content":text[:4000]}],"domain":domain,"source":source,"source_type":"discovered_summary","quality":{"generated":False,"needs_review":True}}

def generate(doc):
    domain,source,text=doc["domain"],doc["source"],doc["text"][:MAX_DOC]
    prompt=f'''Create one high-quality training example from the source below. Return JSON only with keys messages,domain,source,source_type,quality. Use concise key_steps or verification notes instead of hidden chain-of-thought. For reasoning require multi-step problem solving and an explicit verification step. For coding create an executable task when possible and include tests or expected behavior. For trading teach concepts, statistics, risk, market structure and scenario analysis; do not fabricate performance or give personalized financial advice. Do not invent facts not supported by the source. SOURCE={source}\nDOMAIN={domain}\nTEXT={text}'''
    raw=llm(prompt)
    if raw:
        try:
            raw=raw.strip().removeprefix('```json').removesuffix('```').strip(); obj=json.loads(raw); obj["source"]=source; obj["domain"]=domain; return obj
        except Exception: pass
    return fallback(text,domain,source)

def valid(o):
    if not isinstance(o,dict) or not isinstance(o.get('messages'),list) or len(o['messages'])<2:return False
    if o.get('domain') not in DOMAINS or not o.get('source'):return False
    return all(isinstance(x,dict) and x.get('role') in ('user','assistant') and isinstance(x.get('content'),str) and x['content'].strip() for x in o['messages'])

def process():
    dataset=OUT/"all.jsonl"; existing=set(); made=0
    if dataset.exists():
        for line in dataset.read_text(encoding='utf-8').splitlines():
            try: existing.add(hashlib.sha256(json.dumps(json.loads(line),sort_keys=True,ensure_ascii=False).encode()).hexdigest())
            except: pass
    for p in sorted(RAW.glob('*.json')):
        try:
            d=json.loads(p.read_text(encoding='utf-8')); key=hashlib.sha256((d['source']+d['text']).encode()).hexdigest()
            if key in existing: continue
            o=generate(d)
            if not valid(o): continue
            sig=hashlib.sha256(json.dumps(o,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
            if sig in existing: continue
            with dataset.open('a',encoding='utf-8') as f:f.write(json.dumps(o,ensure_ascii=False)+'\n')
            existing.add(sig); made+=1
        except Exception as e: print('[process]',p,e)
    return made

def split():
    src=OUT/"all.jsonl"; rows=[]
    if not src.exists(): return
    for line in src.read_text(encoding='utf-8').splitlines():
        try: rows.append(json.loads(line))
        except: pass
    buckets={"train":[],"validation":[],"test":[]}
    for r in rows:
        h=int(hashlib.sha256(r['source'].encode()).hexdigest()[:8],16)%100
        buckets['test' if h<10 else 'validation' if h<20 else 'train'].append(r)
    for name,items in buckets.items(): (OUT/f"{name}.jsonl").write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in items),encoding='utf-8')
    (OUT/'stats.json').write_text(json.dumps({"total":len(rows),**{k:len(v) for k,v in buckets.items()}},indent=2),encoding='utf-8')

def run():
    print(f'worker model={MODEL or "none"} root={ROOT}')
    once=os.getenv('ONCE','0')=='1'
    while True:
        print('discovered',ingest_discovered(),'sources'); print('generated',process()); split()
        if once: break
        time.sleep(INTERVAL)
if __name__=='__main__': run()
