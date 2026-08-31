#!/usr/bin/env python3
import argparse,json,os,subprocess,sys
from pathlib import Path
from pipeline.dataset import build
ROOT=Path(os.getenv('PROJECT_HOME',Path.home()/'training-data-agent'))
def main():
 ap=argparse.ArgumentParser(description='Autonomous training-data factory'); sub=ap.add_subparsers(dest='cmd',required=True)
 for x in ('status','build','worker','readiness','export'): sub.add_parser(x)
 a=sub.parse_args()
 if a.cmd=='status':
  p=ROOT/'data/dataset/stats.json'; print(p.read_text() if p.exists() else '{"status":"NO_DATASET"}')
 elif a.cmd=='build': print(json.dumps(build(ROOT/'data/raw',ROOT/'data/dataset',float(os.getenv('MIN_QUALITY_SCORE','0.80'))),indent=2))
 elif a.cmd=='worker':
  from agent.agent import run; run()
 elif a.cmd=='readiness':
  subprocess.run([sys.executable,str(ROOT/'quality/readiness.py')],check=True)
 elif a.cmd=='export':
  subprocess.run([sys.executable,str(ROOT/'export/export_dataset.py')],check=True)
if __name__=='__main__': main()
