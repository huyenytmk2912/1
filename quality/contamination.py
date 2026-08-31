#!/usr/bin/env python3
"""Detect exact/near-exact overlap between train, validation and test by normalized text hashes."""
import hashlib,json,re,sys
from pathlib import Path
def norm(s):return re.sub(r'\s+',' ',s.lower()).strip()
def sig(r):
 text=' '.join(str(x.get('content','')) for x in r.get('messages',[]) if isinstance(x,dict)); return hashlib.sha256(norm(text).encode()).hexdigest()
def load(p):
 out={}
 for l in Path(p).read_text(encoding='utf-8').splitlines():
  try:r=json.loads(l);out[sig(r)]=1
  except:pass
 return out
if __name__=='__main__':
 if len(sys.argv)!=2:raise SystemExit('usage: contamination.py DATASET_DIR')
 d=Path(sys.argv[1]); a={n:load(d/f'{n}.jsonl') for n in ('train','validation','test')}; overlap={}
 for x,y in (('train','validation'),('train','test'),('validation','test')):overlap[f'{x}_vs_{y}']=len(set(a[x])&set(a[y]))
 print(json.dumps({'overlap':overlap,'clean':all(v==0 for v in overlap.values())},indent=2)); raise SystemExit(0 if all(v==0 for v in overlap.values()) else 2)
