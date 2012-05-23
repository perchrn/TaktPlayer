#!/bin/bash

PYTHONPATH=src:gui:pythonExtra:$PYTHONPATH
export PYTHONPATH

/opt/local/bin/python GuiMain.py --debug

