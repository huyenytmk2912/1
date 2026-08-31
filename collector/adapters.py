#!/usr/bin/env python3
"""Small source-adapter registry. Adapters return normalized source records."""
import json
from pathlib import Path

def local_jsonl(path):
    for line in Path(path).read_text(encoding='utf-8',errors='ignore').splitlines():
        try:
            x=json.loads(line)
            if isinstance(x,dict): yield x
        except Exception: continue

def local_text(path,domain='reasoning'):
    p=Path(path); yield {'source':str(p),'domain':domain,'title':p.name,'text':p.read_text(encoding='utf-8',errors='ignore'),'license_status':'user_supplied_review_required','source_type':'local_text'}

def adapter_names(): return ['arxiv','local_jsonl','local_text']
