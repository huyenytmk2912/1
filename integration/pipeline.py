#!/usr/bin/env python3
"""End-to-end VPS-1 integration: collect/import -> build -> contamination -> readiness -> version -> export."""
import os,subprocess,sys
from pathlib import Path
ROOT=Path(os.getenv('PROJECT_HOME',Path.home()/'training-data-agent'))
def run(cmd):
 print('[pipeline]', ' '.join(cmd)); subprocess.run(cmd,check=True,cwd=ROOT)
def main():
 run([sys.executable,str(ROOT/'cli.py'),'build'])
 run([sys.executable,str(ROOT/'quality/contamination.py'),str(ROOT/'data/dataset')])
 try: run([sys.executable,str(ROOT/'quality/readiness.py')])
 except subprocess.CalledProcessError: raise SystemExit('DATASET NOT READY: collect/review more data before export')
 run([sys.executable,str(ROOT/'quality/version.py')])
 run([sys.executable,str(ROOT/'export/export_dataset.py')])
if __name__=='__main__':main()
