#!/usr/bin/env python3
import os, sys
from pathlib import Path
ROOT=Path(os.getenv('PROJECT_HOME',Path.home()/'training-data-agent'))
sys.path.insert(0,str(ROOT))
from agent.agent import run
if __name__=='__main__': run()
