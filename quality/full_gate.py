#!/usr/bin/env python3
"""Final VPS-1 gate: all required checks must pass before export is considered ready."""
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(os.getenv('PROJECT_HOME',Path.home()/'training-data-agent')); D=ROOT/'data/dataset'
def run(script,*args): return subprocess.run([sys.executable,str(ROOT/script),*map(str,args)]).returncode
if __name__=='__main__':
 results={}
 results['contamination']=run('quality/contamination.py',D)==0
 results['readiness']=run('quality/readiness.py')==0
 results['versioning']=(ROOT/'data/versions/latest.json').exists()
 results['artifact']=(ROOT/'data/export/dataset.tar.gz').exists() and (ROOT/'data/export/dataset.tar.gz.sha256').exists()
 ready=all(results.values()); (D/'final_gate.json').write_text(json.dumps({'ready':ready,'checks':results},indent=2),encoding='utf-8')
 print(json.dumps({'ready':ready,'checks':results},indent=2)); raise SystemExit(0 if ready else 2)
