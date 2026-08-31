#!/usr/bin/env python3
"""Conservative optional AI verifier. Returns PASS/REVIEW; never silently approves failures."""
import json,os,sys
from urllib.request import Request,urlopen
MODEL=os.getenv('VERIFIER_MODEL') or os.getenv('MODEL',''); URL=os.getenv('OLLAMA_URL','http://127.0.0.1:11434')
def verify(record):
 if not MODEL:return {'decision':'REVIEW','reason':'no verifier model configured'}
 prompt='''Review this training example. Return JSON only: {"decision":"PASS|REVIEW|REJECT","score":0.0,"issues":[]}. Check factual support, internal consistency, task/answer alignment, unsupported claims, and domain safety. Never approve merely because JSON is valid. For coding, require tests/expected behavior. For trading, reject fabricated returns or personalized financial advice. Do not reproduce hidden chain-of-thought.'''+json.dumps(record,ensure_ascii=False)
 try:
  body=json.dumps({'model':MODEL,'prompt':prompt,'stream':False,'options':{'temperature':0}}).encode(); req=Request(URL+'/api/generate',data=body,headers={'Content-Type':'application/json'}); raw=json.loads(urlopen(req,timeout=180).read()).get('response','').strip(); return json.loads(raw.removeprefix('```json').removesuffix('```').strip())
 except Exception as e:return {'decision':'REVIEW','reason':str(e)}
def main():
 if len(sys.argv)!=2:raise SystemExit('usage: ai_verifier.py RECORD.json')
 print(json.dumps(verify(json.loads(open(sys.argv[1],encoding='utf-8').read())),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
