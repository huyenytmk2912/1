#!/usr/bin/env python3
"""Build a signed-by-hash dataset artifact for transfer to VPS 2."""
import hashlib,json,os,tarfile
from pathlib import Path
ROOT=Path(os.getenv('PROJECT_HOME',Path.home()/'training-data-agent')); D=ROOT/'data/dataset'; OUT=ROOT/'data/export'
def main():
 OUT.mkdir(parents=True,exist_ok=True); files=[p for p in (D/'train.jsonl',D/'validation.jsonl',D/'test.jsonl',D/'stats.json',D/'readiness.json') if p.exists()]
 if not files: raise SystemExit('no dataset files')
 manifest={'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 package=OUT/'dataset.tar.gz'
 with tarfile.open(package,'w:gz') as t:
  for p in files+[OUT/'manifest.json']:t.add(p,arcname=p.name)
 sha=hashlib.sha256(package.read_bytes()).hexdigest(); (OUT/'dataset.tar.gz.sha256').write_text(sha+'  dataset.tar.gz\n')
 print(f'Artifact: {package}\nSHA256: {sha}')
if __name__=='__main__':main()
