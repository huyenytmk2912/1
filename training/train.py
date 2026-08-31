#!/usr/bin/env python3
"""Conservative QLoRA launcher. It refuses to train until a non-empty dataset exists."""
import json, os, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(os.getenv('PROJECT_HOME',Path.home()/'training-data-agent'))
CFG=json.loads((ROOT/'config/default.json').read_text())
train=ROOT/'data/dataset/train.jsonl'
if not train.exists() or train.stat().st_size==0: raise SystemExit('TRAIN BLOCKED: no training dataset. Run build first.')
if shutil.which('nvidia-smi') is None: raise SystemExit('TRAIN BLOCKED: no NVIDIA GPU detected. Use a compatible GPU VPS for QLoRA.')
try:
 import transformers, datasets, peft, trl, accelerate
except ImportError:
 raise SystemExit('TRAIN BLOCKED: GPU training packages are not installed. Run: python3 -m pip install -r training/requirements-gpu.txt')
print('Dataset gate: PASS')
print('GPU detected: PASS')
print('Training stack: PASS')
print('Configured base model:',CFG['training']['base_model'])
print('This launcher intentionally stops before modifying weights until the model-specific training recipe is validated for the installed transformers/TRL version.')
