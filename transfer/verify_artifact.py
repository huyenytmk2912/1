#!/usr/bin/env python3
"""Verify a VPS-2 artifact before extraction."""
import hashlib,json,sys,tarfile
from pathlib import Path
def sha(p):
 h=hashlib.sha256();
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 if len(sys.argv)!=2:raise SystemExit('usage: verify_artifact.py dataset.tar.gz')
 p=Path(sys.argv[1]); side=p.with_suffix(p.suffix+'.sha256')
 if not side.exists():raise SystemExit('missing SHA256 sidecar')
 expected=side.read_text().split()[0]; actual=sha(p)
 if expected!=actual:raise SystemExit('SHA256 mismatch — artifact rejected')
 with tarfile.open(p,'r:gz') as t:
  names=t.getnames()
  allowed={'train.jsonl','validation.jsonl','test.jsonl','stats.json','readiness.json','manifest.json'}
  if any(n not in allowed for n in names):raise SystemExit('unexpected file in artifact — rejected')
 print('ARTIFACT VERIFIED')
if __name__=='__main__':main()
