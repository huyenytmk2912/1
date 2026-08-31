#!/usr/bin/env python3
"""Best-effort PDF/HTML/text extraction. Optional heavy parsers are detected at runtime."""
from pathlib import Path
import re

def extract(path):
 p=Path(path); ext=p.suffix.lower()
 if ext in {'.txt','.md','.json','.jsonl','.csv'}:
  return p.read_text(encoding='utf-8',errors='ignore')
 if ext=='.html' or ext=='.htm':
  try:
   from bs4 import BeautifulSoup
   return BeautifulSoup(p.read_text(encoding='utf-8',errors='ignore'),'html.parser').get_text('\n')
  except ImportError:
   return re.sub(r'<[^>]+>',' ',p.read_text(encoding='utf-8',errors='ignore'))
 if ext=='.pdf':
  try:
   import pypdf
   reader=pypdf.PdfReader(str(p)); return '\n'.join((x.extract_text() or '') for x in reader.pages)
  except ImportError as e: raise RuntimeError('Install pypdf for PDF extraction') from e
 raise ValueError(f'Unsupported document type: {ext}')
