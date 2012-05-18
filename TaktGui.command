#!/bin/bash

PYTHONPATH=src:gui:$PYTHONPATH
export PYTHONPATH

python GuiMain.py --debug
