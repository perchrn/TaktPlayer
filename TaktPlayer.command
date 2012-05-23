#!/bin/bash

PYTHONPATH=src:gui:pythonExtra:$PYTHONPATH
export PYTHONPATH

/opt/local/bin/python PlayerMain.py --config DEFAULT:playerOnly:0
