#!/usr/bin/env python3
"""Guarded QLoRA/SFT runner for the prepared JSONL dataset."""
import json, os
from pathlib import Path
ROOT=Path(os.getenv('PROJECT_HOME',Path.home()/'training-data-agent')); CFG=json.loads((ROOT/'config/default.json').read_text())
TRAIN=ROOT/'data/dataset/train.jsonl'; VAL=ROOT/'data/dataset/validation.jsonl'
if not TRAIN.exists() or TRAIN.stat().st_size==0: raise SystemExit('TRAIN BLOCKED: train.jsonl is empty. Run build first.')
if not VAL.exists() or VAL.stat().st_size==0: raise SystemExit('TRAIN BLOCKED: validation.jsonl is empty. Build enough data before training.')
try:
 import torch
 from datasets import load_dataset
 from transformers import AutoTokenizer,AutoModelForCausalLM,BitsAndBytesConfig,TrainingArguments,Trainer,DataCollatorForLanguageModeling
 from peft import LoraConfig,get_peft_model,prepare_model_for_kbit_training
except ImportError as e: raise SystemExit(f'TRAIN BLOCKED: missing GPU dependency: {e}. Run install-gpu.sh first.')
if not torch.cuda.is_available(): raise SystemExit('TRAIN BLOCKED: CUDA GPU not available.')
base=CFG['training']['base_model']; out=ROOT/CFG['training']['output_dir']; out.mkdir(parents=True,exist_ok=True)
print('Base:',base); print('GPU:',torch.cuda.get_device_name(0)); print('Output:',out)
tok=AutoTokenizer.from_pretrained(base,use_fast=True,trust_remote_code=True)
if tok.pad_token is None: tok.pad_token=tok.eos_token
def render(x):
 msgs=x.get('messages',[])
 return tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=False) if hasattr(tok,'apply_chat_template') else '\n'.join(f"{m['role']}: {m['content']}" for m in msgs)
bnb=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,bnb_4bit_use_double_quant=True)
model=AutoModelForCausalLM.from_pretrained(base,quantization_config=bnb,device_map='auto',trust_remote_code=True)
model=prepare_model_for_kbit_training(model)
model=get_peft_model(model,LoraConfig(r=16,lora_alpha=32,lora_dropout=0.05,bias='none',task_type='CAUSAL_LM',target_modules='all-linear'))
model.print_trainable_parameters()
ds=load_dataset('json',data_files={'train':str(TRAIN),'validation':str(VAL)})
ds=ds.filter(lambda x:isinstance(x.get('messages'),list) and len(x['messages'])>=2)
def tokenize(batch): return tok([render(x) for x in batch],truncation=True,max_length=CFG['training']['max_seq_length'])
enc=ds.map(tokenize,batched=True,remove_columns=ds['train'].column_names)
args=TrainingArguments(output_dir=str(out),num_train_epochs=CFG['training']['epochs'],learning_rate=CFG['training']['learning_rate'],per_device_train_batch_size=1,per_device_eval_batch_size=1,gradient_accumulation_steps=8,gradient_checkpointing=True,logging_steps=10,eval_strategy='steps',eval_steps=100,save_steps=100,save_total_limit=2,report_to='none',bf16=torch.cuda.is_bf16_supported(),fp16=not torch.cuda.is_bf16_supported(),optim='paged_adamw_8bit')
trainer=Trainer(model=model,args=args,train_dataset=enc['train'],eval_dataset=enc['validation'],data_collator=DataCollatorForLanguageModeling(tok,mlm=False))
trainer.train(); trainer.save_model(str(out)); tok.save_pretrained(str(out)); print('TRAIN COMPLETE:',out)
