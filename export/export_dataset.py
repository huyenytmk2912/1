#!/usr/bin/env python3
import hashlib, json, os, tarfile
from pathlib import Path
ROOT=Path(os.getenv('PROJECT_HOME',Path.home()/'training-data-agent')); OUT=ROOT/'data/dataset'; PKG=ROOT/'data/export'

def main():
    PKG.mkdir(parents=True,exist_ok=True); files=[OUT/'train.jsonl',OUT/'validation.jsonl',OUT/'test.jsonl',OUT/'stats.json',OUT/'readiness.json']
    missing=[str(p) for p in files if not p.exists()]
    if missing: raise SystemExit('Export blocked; missing: '+', '.join(missing))
    name='dataset-export.tar.gz'; path=PKG/name
    with tarfile.open(path,'w:gz') as tar:
        for p in files: tar.add(p,arcname=p.name)
    sha=hashlib.sha256(path.read_bytes()).hexdigest(); (PKG/'SHA256').write_text(sha+'  '+name+'\n')
    print(f'{path}\nSHA256={sha}')
if __name__=='__main__': main()
