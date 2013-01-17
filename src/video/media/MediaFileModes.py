'''
Created on 7. feb. 2012

@author: pcn
'''
import ntpath
import posixpath
#Media file utility to force unix paths in configurations.
def forceUnixPath(pathPart):
    if(pathPart == None):
        return
    drive, _ = ntpath.splitdrive(pathPart)
    if(drive != ""):
        if((drive == pathPart) or ((drive + "\\") == pathPart)):
            return drive
    firstPart, lastPart = ntpath.split(pathPart)
    if((firstPart != "") and (lastPart != "")):
        unixPathPart = forceUnixPath(firstPart)
        if(unixPathPart == None):
            return lastPart
        return posixpath.join(unixPathPart, lastPart)
    if(firstPart != ""):
        return firstPart
    else:
        return lastPart

class MixMode:
    Default, Add, Subtract, Multiply, LumaKey, WhiteLumaKey, AlphaMask, Replace = range(8)

    def getChoices(self):
        return ["Default", "Add", "Subtract", "Multiply", "LumaKey", "WhiteLumaKey", "AlphaMask", "Replace"]

    def getNames(self, typeId):
        for i in range(len(self.getChoices())):
            if(typeId == i):
                return self.getChoices()[i]
        return self.getChoices()[0]

def getMixModeFromName(name):
    if(name == "Add"):
        return MixMode.Add
    elif(name == "Multiply"):
        return MixMode.Multiply
    elif(name == "Subtract"):
        return MixMode.Subtract
    elif(name == "LumaKey"):
        return MixMode.LumaKey
    elif(name == "WhiteLumaKey"):
        return MixMode.WhiteLumaKey
    elif(name == "AlphaMask"):
        return MixMode.AlphaMask
    elif(name == "Replace"):
        return MixMode.Replace
    else:
        return MixMode.Default

class WipeMode:
    Default, Fade, Push, Noize, Zoom, Flip = range(6)

    def getChoices(self):
        return ["Default", "Fade", "Push", "Noize", "Zoom", "Flip"]

    def getChoicesNoDefault(self):
        return ["Fade", "Push", "Noize", "Zoom", "Flip"]

    def getNames(self, typeId):
        for i in range(len(self.getChoices())):
            if(typeId == i):
                return self.getChoices()[i]
        return self.getChoices()[0]

    def findMode(self, modeString):
        modesList = self.getChoices()
        for i in range(len(modesList)):
            if(modesList[i] == modeString):
                return i
        return 0

class ModulationValueMode:
    RawInput, KeepOld, ResetToDefault = range(3)

    def getChoices(self):
        return ["RawInput", "KeepOld", "ResetToDefault"]

    def getNames(self, typeId):
        for i in range(len(self.getChoices())):
            if(typeId == i):
                return self.getChoices()[i]
        return self.getChoices()[0]

def getModulationValueModeFromName(name):
    if(name == "RawInput"):
        return ModulationValueMode.RawInput
    elif(name == "KeepOld"):
        return ModulationValueMode.KeepOld
    elif(name == "ResetToDefault"):
        return ModulationValueMode.ResetToDefault
    else:
        return ModulationValueMode.RawInput

class VideoLoopMode:
    Normal, Reverse, PingPong, PingPongReverse, DontLoop, DontLoopReverse, KeepLast, AdvancedLoop, AdvancedPingPong = range(9)

    def getChoices(self):
        return ["Normal", "Reverse", "PingPong", "PingPongReverse", "DontLoop", "DontLoopReverse", "KeepLast", "AdvancedLoop", "AdvancedPingPong"]

    def getNames(self, typeId):
        for i in range(len(self.getChoices())):
            if(typeId == i):
                return self.getChoices()[i]
        return self.getChoices()[0]

class ImageSequenceMode:
    Time, ReTrigger, Modulation = range(3)

    def getChoices(self):
        return ["Time", "ReTrigger", "Modulation"]

    def getNames(self, typeId):
        for i in range(len(self.getChoices())):
            if(typeId == i):
                return self.getChoices()[i]
        return self.getChoices()[0]

class KinectMode:
    RGBImage, IRImage, DepthImage, DepthMask, DepthThreshold, Reset = range(6)

    def getChoices(self):
        return ["RGBImage", "IRImage", "DepthImage", "DepthMask", "DepthThreshold", "Reset"]

    def getNames(self, typeId):
        for i in range(len(self.getChoices())):
            if(typeId == i):
                return self.getChoices()[i]
        return self.getChoices()[0]

class MediaTypes:
    VideoLoop, Image, ImageSequence, ScrollImage, Sprite, Text, Camera, KinectCamera, Group, Modulation = range(10)

    def getChoices(self):
        return ["VideoLoop", "Image", "ImageSequence", "ScrollImage", "Sprite", "Text", "Camera", "KinectCamera", "Group", "Modulation"]

    def getNames(self, typeId):
        for i in range(len(self.getChoices())):
            if(typeId == i):
                return self.getChoices()[i]
        return self.getChoices()[0]

class TimeModulationMode():
    Off, SpeedModulation, TriggeredJump, TriggeredLoop = range(4)

    def getChoices(self):
        return ["Off", "SpeedModulation", "TriggeredJump", "TriggeredLoop"]

    def getNames(self, typeId):
        for i in range(len(self.getChoices())):
            if(typeId == i):
                return self.getChoices()[i]
        return self.getChoices()[0]


