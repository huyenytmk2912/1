#!/usr/bin/env python3
import argparse,json,os,subprocess,sys
from pathlib import Path
from pipeline.dataset import build
ROOT=Path(os.getenv('PROJECT_HOME',Path.home()/'training-data-agent'))
def main():
 ap=argparse.ArgumentParser(description='Autonomous training-data factory'); sub=ap.add_subparsers(dest='cmd',required=True)
 for x in ('status','build','worker','train','evaluate'): sub.add_parser(x)
 a=sub.parse_args()
 if a.cmd=='status':
  p=ROOT/'data/dataset/stats.json'; print(p.read_text() if p.exists() else '{"status":"NO_DATASET"}')
 elif a.cmd=='build': print(json.dumps(build(ROOT/'data/raw',ROOT/'data/dataset',float(os.getenv('MIN_QUALITY_SCORE','0.80'))),indent=2))
 elif a.cmd=='worker':
  from agent.agent import run; run()
 elif a.cmd=='train':
  p=ROOT/'data/dataset/stats.json'
  if not p.exists(): raise SystemExit('TRAIN BLOCKED: run build first.')
  stats=json.loads(p.read_text())
  if stats.get('accepted',0)<20 or stats.get('validation',0)<2: raise SystemExit('TRAIN BLOCKED: dataset is too small. Collect and verify more data first.')
  subprocess.run([sys.executable,str(ROOT/'training/train.py')],check=True)
 elif a.cmd=='evaluate':
  print('Evaluation requires a trained checkpoint. Training outputs are kept versioned under models/trained.')
if __name__=='__main__': main()
