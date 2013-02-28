#!/bin/bash

PYTHONPATH=src:gui:pythonExtra:/opt/local/lib/python2.7/site-packages:$PYTHONPATH
export PYTHONPATH

/opt/local/bin/python CameraServerMain.py --debug $*
