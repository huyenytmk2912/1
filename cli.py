#!/usr/bin/env python3
import argparse,json,os,subprocess,sys
from pathlib import Path
from pipeline.dataset import build
ROOT=Path(os.getenv('PROJECT_HOME',Path.home()/'training-data-agent'))
def main():
 ap=argparse.ArgumentParser(description='VPS-1 autonomous data factory'); sub=ap.add_subparsers(dest='cmd',required=True)
 for x in ('status','build','worker','verify','check-leakage','readiness','version','export','pipeline'): sub.add_parser(x)
 a=sub.parse_args()
 if a.cmd=='status':
  p=ROOT/'data/dataset/stats.json'; print(p.read_text() if p.exists() else '{"status":"NO_DATASET"}')
 elif a.cmd=='build': print(json.dumps(build(ROOT/'data/raw',ROOT/'data/dataset',float(os.getenv('MIN_QUALITY_SCORE','0.80'))),indent=2))
 elif a.cmd=='worker': from agent.agent import run; run()
 elif a.cmd=='verify': print('AI verifier available at verifier/ai_verifier.py; records without a verifier are REVIEW, never PASS.')
 elif a.cmd=='check-leakage': subprocess.run([sys.executable,str(ROOT/'quality/contamination.py'),str(ROOT/'data/dataset')],check=True)
 elif a.cmd=='readiness': subprocess.run([sys.executable,str(ROOT/'quality/readiness.py')],check=True)
 elif a.cmd=='version': subprocess.run([sys.executable,str(ROOT/'quality/version.py')],check=True)
 elif a.cmd=='export': subprocess.run([sys.executable,str(ROOT/'export/export_dataset.py')],check=True)
 elif a.cmd=='pipeline': subprocess.run([sys.executable,str(ROOT/'integration/pipeline.py')],check=True)
if __name__=='__main__': main()
