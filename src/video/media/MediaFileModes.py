'''
Created on 7. feb. 2012

@author: pcn
'''
import ntpath
import posixpath
#Media file utility to force unix paths in configurations.
def forceUnixPath(pathPart):
    firstPart, lastPart = ntpath.split(pathPart)
    if(firstPart != ""):
        unixPathPart = forceUnixPath(firstPart)
        return posixpath.join(unixPathPart, lastPart)
    return lastPart

class MixMode:
    Default, Add, Multiply, LumaKey, WhiteLumaKey, Replace = range(6)

    def getChoices(self):
        return ["Default", "Add", "Multiply", "LumaKey", "WhiteLumaKey", "Replace"]

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
    elif(name == "LumaKey"):
        return MixMode.LumaKey
    elif(name == "WhiteLumaKey"):
        return MixMode.WhiteLumaKey
    elif(name == "Replace"):
        return MixMode.Replace
    else:
        return MixMode.Default

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
    Normal, Reverse, PingPong, PingPongReverse, DontLoop, DontLoopReverse = range(6)

    def getChoices(self):
        return ["Normal", "Reverse", "PingPong", "PingPongReverse", "DontLoop", "DontLoopReverse"]

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
    VideoLoop, Image, ImageSequence, Camera, KinectCamera = range(5)

    def getChoices(self):
        return ["VideoLoop", "Image", "ImageSequence", "Camera", "KinectCamera"]

    def getNames(self, typeId):
        for i in range(len(self.getChoices())):
            if(typeId == i):
                return self.getChoices()[i]
        return self.getChoices()[0]

class FadeMode():
    Black, White = range(2)

    def getChoices(self):
        return ["Black", "White"]

    def getNames(self, typeId):
        for i in range(len(self.getChoices())):
            if(typeId == i):
                return self.getChoices()[i]
        return self.getChoices()[0]



