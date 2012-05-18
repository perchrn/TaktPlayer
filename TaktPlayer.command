#!/bin/bash

PYTHONPATH=src:gui:$PYTHONPATH
export PYTHONPATH

kivy PlayerMain.py --config DEFAULT:playerOnly:0
