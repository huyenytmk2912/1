#!/usr/bin/env python3
"""Single VPS-1 pipeline: build -> contamination -> readiness -> version -> export."""
import os,subprocess,sys
from pathlib import Path
ROOT=Path(os.getenv('PROJECT_HOME',Path.home()/'training-data-agent'))
def run(path,*args): subprocess.run([sys.executable,str(ROOT/path),*map(str,args)],check=True)
def main():
 run('cli.py','build'); run('quality/contamination.py',ROOT/'data/dataset'); run('quality/readiness.py'); run('quality/version.py'); run('transfer/export_secure.py')
 print('VPS-1 PIPELINE COMPLETE — artifact is ready for transfer to VPS 2.')
if __name__=='__main__':main()
