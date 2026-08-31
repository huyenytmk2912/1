#!/usr/bin/env python3
import hashlib, json
from pathlib import Path
from .quality import accept

def build(raw_path, out_dir, minimum=0.80):
    raw_path=Path(raw_path); out_dir=Path(out_dir); out_dir.mkdir(parents=True,exist_ok=True)
    accepted=[]; rejected=[]; seen=set()
    for p in sorted(raw_path.glob("*.json")):
        try: r=json.loads(p.read_text(encoding="utf-8"))
        except Exception as e: rejected.append({"file":str(p),"reason":"invalid_json"}); continue
        sig=hashlib.sha256(json.dumps(r,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        if sig in seen: rejected.append({"file":str(p),"reason":"duplicate"}); continue
        seen.add(sig); ok,s,reasons=accept(r,minimum)
        r.setdefault("quality",{}).update({"score":s,"reasons":reasons})
        (accepted if ok else rejected).append(r if ok else {"record":r,"reasons":reasons})
    for name,rows in (("all",accepted),("rejected",rejected)):
        (out_dir/f"{name}.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in rows),encoding="utf-8")
    buckets={"train":[],"validation":[],"test":[]}
    for r in accepted:
        source=r.get("source", "")
        h=int(hashlib.sha256(source.encode()).hexdigest()[:8],16)%100
        buckets["test" if h<10 else "validation" if h<20 else "train"].append(r)
    for k,v in buckets.items(): (out_dir/f"{k}.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in v),encoding="utf-8")
    report={"accepted":len(accepted),"rejected":len(rejected),"train":len(buckets["train"]),"validation":len(buckets["validation"]),"test":len(buckets["test"]),"status":"READY" if accepted else "EMPTY"}
    (out_dir/"stats.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    return report
