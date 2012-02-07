'''
Created on 7. feb. 2012

@author: pcn
'''

class MixMode:
    Default, Add, Multiply, LumaKey, Replace = range(5)

    def getChoices(self):
        return ["Default", "Add", "Multiply", "LumaKey", "Replace"]

class VideoLoopMode:
    Normal, Reverse, PingPong, PingPongReverse, DontLoop, DontLoopReverse = range(6)

    def getChoices(self):
        return ["Normal", "Reverse", "PingPong", "PingPongReverse", "DontLoop", "DontLoopReverse"]

class ImageSequenceMode:
    Time, ReTrigger, Controller = range(3)

    def getChoices(self):
        return ["Time", "ReTrigger", "Controller"]

class MediaTypes:
    VideoLoop, Image, ImageSequence, Camera = range(4)

    def getChoices(self):
        return ["VideoLoop", "Image", "ImageSequence", "Camera"]

