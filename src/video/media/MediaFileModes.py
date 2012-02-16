'''
Created on 7. feb. 2012

@author: pcn
'''

class MixMode:
    Default, Add, Multiply, LumaKey, Replace = range(5)

    def getChoices(self):
        return ["Default", "Add", "Multiply", "LumaKey", "Replace"]

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
        elif(name == "Replace"):
            return MixMode.Replace
        else:
            return MixMode.Default

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

class MediaTypes:
    VideoLoop, Image, ImageSequence, Camera = range(4)

    def getChoices(self):
        return ["VideoLoop", "Image", "ImageSequence", "Camera"]

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



