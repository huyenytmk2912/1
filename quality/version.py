#!/usr/bin/env python3
import hashlib,json,datetime,os
from pathlib import Path
ROOT=Path(os.getenv('PROJECT_HOME',Path.home()/'training-data-agent')); D=ROOT/'data/dataset'; V=ROOT/'data/versions'
def snapshot():
 V.mkdir(parents=True,exist_ok=True); files={}
 for p in sorted(D.glob('*.jsonl')):
  files[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'); payload={'version':stamp,'created_at':stamp,'files':files}
 (V/f'{stamp}.json').write_text(json.dumps(payload,indent=2),encoding='utf-8'); (V/'latest.json').write_text(json.dumps(payload,indent=2),encoding='utf-8'); print(stamp)
if __name__=='__main__':snapshot()
