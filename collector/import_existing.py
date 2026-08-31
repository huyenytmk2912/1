#!/usr/bin/env python3
"""Import existing JSONL/JSON datasets without rewriting records that already fit the schema."""
import json, sys
from pathlib import Path

def main():
    if len(sys.argv) != 3: raise SystemExit('usage: import_existing.py INPUT OUTPUT')
    src,dst=map(Path,sys.argv[1:]); dst.parent.mkdir(parents=True,exist_ok=True); count=0
    with src.open(encoding='utf-8') as f, dst.open('a',encoding='utf-8') as out:
        for line in f:
            try: obj=json.loads(line)
            except Exception: continue
            if isinstance(obj,dict) and (isinstance(obj.get('messages'),list) or obj.get('prompt') is not None):
                obj.setdefault('source_type','existing_dataset'); obj.setdefault('quality',{'needs_review':True,'imported':True})
                out.write(json.dumps(obj,ensure_ascii=False)+'\n'); count+=1
    print(json.dumps({'imported':count,'output':str(dst)}))
if __name__=='__main__': main()
