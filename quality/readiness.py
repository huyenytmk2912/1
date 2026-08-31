#!/usr/bin/env python3
import json, os
from pathlib import Path
ROOT=Path(os.getenv('PROJECT_HOME',Path.home()/'training-data-agent')); D=ROOT/'data/dataset'

def main():
    stats=D/'stats.json'; train=D/'train.jsonl'; val=D/'validation.jsonl'; test=D/'test.jsonl'
    s=json.loads(stats.read_text()) if stats.exists() else {}
    checks={
      'dataset_exists': D.exists(), 'train_nonempty': train.exists() and train.stat().st_size>0,
      'validation_nonempty': val.exists() and val.stat().st_size>0,
      'test_nonempty': test.exists() and test.stat().st_size>0,
      'minimum_total': s.get('total',0)>=100
    }
    ready=all(checks.values())
    report={'ready':ready,'checks':checks,'stats':s,'next':'TRAIN on VPS 2' if ready else 'BUILD / review more data on VPS 1'}
    (D/'readiness.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2)); raise SystemExit(0 if ready else 2)
if __name__=='__main__': main()
