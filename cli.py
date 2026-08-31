#!/usr/bin/env python3
import argparse, json, os, subprocess, sys
from pathlib import Path
from pipeline.dataset import build

ROOT=Path(os.getenv("PROJECT_HOME",Path.home()/"training-data-agent"))

def main():
    ap=argparse.ArgumentParser(description="Autonomous training-data factory")
    sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("status")
    sub.add_parser("build")
    sub.add_parser("train")
    sub.add_parser("evaluate")
    a=sub.parse_args()
    if a.cmd=="status":
        p=ROOT/"data/dataset/stats.json"
        print(p.read_text() if p.exists() else '{"status":"NO_DATASET"}')
    elif a.cmd=="build":
        print(json.dumps(build(ROOT/"data/raw",ROOT/"data/dataset"),indent=2))
    elif a.cmd=="train":
        ready=ROOT/"data/dataset/train.jsonl"
        if not ready.exists() or ready.stat().st_size==0:
            raise SystemExit("Training blocked: dataset/train.jsonl is empty. Run build and review the dataset first.")
        print("TRAINING GATE PASSED. Fine-tuning runner is intentionally separate; configure training/base model before launching GPU work.")
    elif a.cmd=="evaluate":
        print("Evaluation runner is reserved for the trained checkpoint. No model was changed.")
if __name__=="__main__": main()
