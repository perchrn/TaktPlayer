#!/bin/bash

PYTHONPATH=src:gui:pythonExtra:$PYTHONPATH
export PYTHONPATH

arch -i386 /opt/local/bin/python GuiMain.py --debug $*

