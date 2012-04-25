'''
Created on 26. jan. 2012

@author: pcn
'''
import os
import sys
import multiprocessing
from configurationGui.GuiMainWindow import startGui

if __name__ == '__main__':
    multiprocessing.freeze_support()
    debugMode = False
    for i in range(len(sys.argv) - 1):
        if(sys.argv[i+1] == "--debug"):
            debugMode = True
    dirOk = True
    scriptDir = os.path.dirname(sys.argv[0])
    if((scriptDir != "") and (scriptDir != os.getcwd())):
        os.chdir(scriptDir)
        if(scriptDir != os.getcwd()):
            print "Could not go to correct directory: " + scriptDir + " we are in " + os.getcwd()
            dirOk = False
#    print "CWD: %s" % os.getcwd()
    if(dirOk):
        startGui(debugMode)
    else:
        print "Exiting..."
