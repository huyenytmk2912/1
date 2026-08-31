#!/usr/bin/env python3
"""Minimal isolated coding-test runner. Default: no network, bounded time, temp workspace."""
import subprocess,sys,tempfile,os

def run(code,tests,timeout=5):
 with tempfile.TemporaryDirectory(prefix='dataset-code-') as d:
  src=os.path.join(d,'solution.py'); test=os.path.join(d,'test_solution.py')
  open(src,'w',encoding='utf-8').write(code); open(test,'w',encoding='utf-8').write(tests)
  try:
   p=subprocess.run([sys.executable,'-I',test],cwd=d,capture_output=True,text=True,timeout=timeout)
   return {'passed':p.returncode==0,'returncode':p.returncode,'stdout':p.stdout[-4000:],'stderr':p.stderr[-4000:]}
  except subprocess.TimeoutExpired:return {'passed':False,'reason':'timeout'}
if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('usage: coding_test.py SOLUTION.py TEST.py')
 print(run(open(sys.argv[1],encoding='utf-8').read(),open(sys.argv[2],encoding='utf-8').read()))
