#!/usr/bin/env python3
"""Hard acceptance gate for VPS-1 training data."""
import json, os
from pathlib import Path
ROOT=Path(os.getenv('PROJECT_HOME',Path.home()/'training-data-agent')); D=ROOT/'data/dataset'
def main():
 stats=D/'stats.json';
 if not stats.exists(): raise SystemExit('NOT_READY: build dataset first')
 s=json.loads(stats.read_text()); checks={'has_train':s.get('train',0)>0,'has_validation':s.get('validation',0)>0,'has_test':s.get('test',0)>0,'enough_records':s.get('accepted',s.get('total',0))>=20}
 contamination=ROOT/'quality/contamination.py'
 import subprocess,sys
 rc=subprocess.run([sys.executable,str(contamination),str(D)]).returncode if contamination.exists() else 2
 checks['no_split_overlap']=rc==0
 ready=all(checks.values())
 report={'ready':ready,'checks':checks,'stats':s}
 (D/'gate.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report,indent=2)); raise SystemExit(0 if ready else 2)
if __name__=='__main__':main()
