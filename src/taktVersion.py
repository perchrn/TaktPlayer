'''
Created on 15. nov. 2012

@author: pcn
'''
import os

def getTaktInfoFileContentString():
    infoFilePath = os.path.normpath(os.path.join(os.getcwd(), "VersionInfo.log"))
    try:
        loadFile = open(infoFilePath, 'r')
        infoFileString = loadFile.read()
        return infoFileString
    except:
        print "Error reading version information from: " + infoFilePath
        return ""


def getVersionNumberString():
    return "1.1.1"

def getVersionDateString():
    infoFileString = getTaktInfoFileContentString()
    for line in infoFileString.split("\n", 10):
#        print line
        if(line.startswith("Date:")):
            return line[5:]
    return "Unknown"

def getVersionGitIdString():
    infoFileString = getTaktInfoFileContentString()
    for line in infoFileString.split("\n", 10):
        if(line.startswith("commit ")):
            return line[7:]
    return "Unknown"

if __name__ == '__main__':
    print getVersionNumberString()
