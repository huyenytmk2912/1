#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
from .quality import accept

def build(raw_path,out_dir,minimum=0.80):
 raw_path=Path(raw_path); out_dir=Path(out_dir); out_dir.mkdir(parents=True,exist_ok=True)
 accepted=[];rejected=[];seen_source=set();seen_record=set()
 for p in sorted(raw_path.glob('*.json')):
  try:r=json.loads(p.read_text(encoding='utf-8'))
  except Exception:rejected.append({'file':str(p),'reason':'invalid_json'});continue
  source=r.get('source','')
  source_key=hashlib.sha256(source.encode()).hexdigest() if source else ''
  record_key=hashlib.sha256(json.dumps(r,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
  if record_key in seen_record or (source_key and source_key in seen_source):
   rejected.append({'file':str(p),'reason':'duplicate_source_or_record'});continue
  seen_record.add(record_key)
  if source_key:seen_source.add(source_key)
  ok,score,reasons=accept(r,minimum);r.setdefault('quality',{}).update({'score':score,'reasons':reasons})
  (accepted if ok else rejected).append(r if ok else {'record':r,'reasons':reasons})
 for name,rows in (('all',accepted),('rejected',rejected)):(out_dir/f'{name}.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows),encoding='utf-8')
 buckets={'train':[],'validation':[],'test':[]}
 for r in accepted:
  h=int(hashlib.sha256(r.get('source','').encode()).hexdigest()[:8],16)%100;buckets['test' if h<10 else 'validation' if h<20 else 'train'].append(r)
 for k,v in buckets.items():(out_dir/f'{k}.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in v),encoding='utf-8')
 report={'accepted':len(accepted),'rejected':len(rejected),'train':len(buckets['train']),'validation':len(buckets['validation']),'test':len(buckets['test']),'status':'READY' if len(accepted)>=20 and len(buckets['validation'])>0 and len(buckets['test'])>0 else 'NOT_READY'}
 (out_dir/'stats.json').write_text(json.dumps(report,indent=2),encoding='utf-8');return report
