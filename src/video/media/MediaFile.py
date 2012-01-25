'''
Created on 12. okt. 2011

@author: pcn
'''
import os.path
import logging
from cv2 import cv
import numpy
from midi.MidiModulation import MidiModulation
from video.Effects import createMat, ZoomEffect, FlipEffect,\
    BlurEffect, BluredContrastEffect, DistortionEffect, EdgeEffect,\
    DesaturateEffect, ContrastBrightnessEffect, HueSaturationEffect,\
    InvertEffect, ThresholdEffect, ColorizeEffect

def copyImage(image):
    return cv.CloneImage(image)

def resizeImage(image, resizeMat):
    cv.Resize(image, resizeMat)
    return resizeMat

class FadeMode():
    Black, White = range(2)

def fadeImage(image, value, mode, tmpMat):
    if(mode == FadeMode.White):
        cv.ConvertScaleAbs(image, tmpMat, value, (1.0-value) * 256)
    else: #FadeMode.Black
        cv.ConvertScaleAbs(image, tmpMat, value, 0.0)
    return tmpMat

def mixImageSelfMask(image1, image2, mixMask, mixMat1, mixMat2):
    cv.Copy(image2, mixMat2)
    cv.CvtColor(image2, mixMask, cv.CV_BGR2GRAY);
    cv.CmpS(mixMask, 10, mixMask, cv.CV_CMP_GT)
#    cv.Copy(mixMat2, image1, mixMask)
#    return mixMat2
    cv.Merge(mixMask, mixMask, mixMask, None, mixMat1)
    cv.Sub(image1, mixMat1, mixMat1)
    cv.Add(mixMat1, mixMat2, image2)
    return image2

def mixImagesAdd(image1, image2, mixMat):
    cv.Add(image1, image2, mixMat)
    return mixMat

def mixImagesMultiply(image1, image2, mixMat):
    cv.Mul(image1, image2, mixMat, 0.003)
    return mixMat

class MixMode:
    (Default, Add, Multiply, LumaKey, Replace) = range(5)

def mixImages(mode, image1, image2, mixMat1, mixMat2, mixMask):
    if(mode == MixMode.Add):
        return mixImagesAdd(image1, image2, mixMat1)
    elif(mode == MixMode.Multiply):
        return mixImagesMultiply(image1, image2, mixMat1)
    elif(mode == MixMode.LumaKey):
        return mixImageSelfMask(image1, image2, mixMask, mixMat1, mixMat2)
    elif(mode == MixMode.Replace):
        return image2
    else:
        return mixImagesAdd(image1, image2, mixMat1)

def imageToArray(image):
    return numpy.asarray(image)

def imageFromArray(array):
    return cv.fromarray(array)

class MediaFile(object):
    def __init__(self, fileName, midiTimingClass, configurationTree):
        self._configurationTree = configurationTree
        self.setFileName(fileName)
        self._midiTiming = midiTimingClass
        self._internalResolutionX =  self._configurationTree.getValueFromPath("Global.ResolutionX")
        self._internalResolutionY =  self._configurationTree.getValueFromPath("Global.ResolutionY")
        self._resizeMat = createMat(self._internalResolutionX, self._internalResolutionY)
        self._fadeMat = createMat(self._internalResolutionX, self._internalResolutionY)
        self._fileOk = False
        self._image = None
        self._captureImage = None
        self._firstImage = None
        self._secondImage = None
        self._bufferedImageList = None
        self._numberOfFrames = 0
        self._originalFrameRate = 25
        self._originalTime = 0.0
        self._currentFrame = 0;
        self._startSongPosition = 0.0

        self._effect1 = EdgeEffect(self._configurationTree, self._internalResolutionX, self._internalResolutionY)
        self._effect2 = InvertEffect(self._configurationTree, self._internalResolutionX, self._internalResolutionY)

        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._log.setLevel(logging.WARNING)

        self._configurationTree.addTextParameterStatic("Type", self.getType())
        self._configurationTree.addTextParameterStatic("FileName", self._filename)
        self._midiModulation = MidiModulation(self._configurationTree.addChildUnique("Modulation"), self._midiTiming)
        self._setupConfiguration()
        self._getConfiguration()

    def _setupConfiguration(self):
        self._midiModulation.setModulationReceiver("PlayBack", "None")
        self._midiModulation.setModulationReceiver("FadeInOut", "None")
        self._midiModulation.setModulationReceiver("Level", "None")
        self._midiModulation.setModulationReceiver("EffectAAmount", "MidiChannel.Controller.ModWheel")
        self._midiModulation.setModulationReceiver("EffectAArg1", "None")
        self._midiModulation.setModulationReceiver("EffectAArg2", "None")
        self._midiModulation.setModulationReceiver("EffectAArg3", "None")
        self._midiModulation.setModulationReceiver("EffectAArg4", "None")
        self._midiModulation.setModulationReceiver("EffectBAmount", "MidiChannel.Controller.ModWheel")
        self._midiModulation.setModulationReceiver("EffectBArg1", "None")
        self._midiModulation.setModulationReceiver("EffectBArg2", "None")
        self._midiModulation.setModulationReceiver("EffectBArg3", "None")
        self._midiModulation.setModulationReceiver("EffectBArg4", "None")
        self._playbackModulationId = -1
        self._fadeModulationId = -1
        self._levelModulationId = -1
        self._effectAAmountModulationId = -1
        self._effectAArg1ModulationId = -1
        self._effectAArg2ModulationId = -1
        self._effectAArg3ModulationId = -1
        self._effectAArg4ModulationId = -1
        self._effectBAmountModulationId = -1
        self._effectBArg1ModulationId = -1
        self._effectBArg2ModulationId = -1
        self._effectBArg3ModulationId = -1
        self._effectBArg4ModulationId = -1

        self._configurationTree.addFloatParameter("SyncLength", 4.0) #Default one bar (re calculated on load)
        self._configurationTree.addFloatParameter("QuantizeLength", 4.0)#Default one bar
        self._configurationTree.addTextParameter("MixMode", "Add")#Default Add
        self._configurationTree.addTextParameter("FadeMode", "Black")#Default Add
        self._syncLength = -1.0
        self._quantizeLength = -1.0
        self._mixMode = MixMode.Add
        self._fadeMode = FadeMode.Black

    def getFadeModulation(self, songPosition, midiChannelStateHolder, midiNoteStateHolder):
        return self._midiModulation.getModlulationValue(self._fadeModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)

    def getLevelModulation(self, songPosition, midiChannelStateHolder, midiNoteStateHolder):
        return self._midiModulation.getModlulationValue(self._levelModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)

    def getEffectModulations(self, songPosition, midiChannelStateHolder, midiNoteStateHolder):
        aamount =  self._midiModulation.getModlulationValue(self._effectAAmountModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        aarg1 =  self._midiModulation.getModlulationValue(self._effectAArg1ModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        aarg2 =  self._midiModulation.getModlulationValue(self._effectAArg2ModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        aarg3 =  self._midiModulation.getModlulationValue(self._effectAArg3ModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        aarg4 =  self._midiModulation.getModlulationValue(self._effectAArg4ModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        bamount =  self._midiModulation.getModlulationValue(self._effectBAmountModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        barg1 =  self._midiModulation.getModlulationValue(self._effectBArg1ModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        barg2 =  self._midiModulation.getModlulationValue(self._effectBArg2ModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        barg3 =  self._midiModulation.getModlulationValue(self._effectBArg3ModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        barg4 =  self._midiModulation.getModlulationValue(self._effectBArg4ModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        return ((aamount, aarg1, aarg2, aarg3, aarg4), (bamount, barg1, barg2, barg3, barg4))

    def _getConfiguration(self):
        self._playbackModulationId = self._midiModulation.connectModulation("PlayBack")
        self._fadeModulationId = self._midiModulation.connectModulation("FadeInOut")
        self._levelModulationId = self._midiModulation.connectModulation("Level")
        self._effectAAmountModulationId = self._midiModulation.connectModulation("EffectAAmount")
        self._effectAArg1ModulationId = self._midiModulation.connectModulation("EffectAArg1")
        self._effectAArg2ModulationId = self._midiModulation.connectModulation("EffectAArg2")
        self._effectAArg3ModulationId = self._midiModulation.connectModulation("EffectAArg3")
        self._effectAArg4ModulationId = self._midiModulation.connectModulation("EffectAArg4")
        self._effectBAmountModulationId = self._midiModulation.connectModulation("EffectBAmount")
        self._effectBArg1ModulationId = self._midiModulation.connectModulation("EffectBArg1")
        self._effectBArg2ModulationId = self._midiModulation.connectModulation("EffectBArg2")
        self._effectBArg3ModulationId = self._midiModulation.connectModulation("EffectBArg3")
        self._effectBArg4ModulationId = self._midiModulation.connectModulation("EffectBArg4")

        self.setMidiLengthInBeats(self._configurationTree.getValue("SyncLength"))
        self.setQuantizeInBeats(self._configurationTree.getValue("QuantizeLength"))

        mixMode = self._configurationTree.getValue("MixMode")
        if(mixMode == "Add"):
            self._mixMode = MixMode.Add
        elif(mixMode == "Multiply"):
            self._mixMode = MixMode.Multiply
        elif(mixMode == "LumaKey"):
            self._mixMode = MixMode.LumaKey
        elif(mixMode == "Replace"):
            self._mixMode = MixMode.Replace
        else:
            self._mixMode = MixMode.Add #Defaults to add

        fadeMode = self._configurationTree.getValue("FadeMode")
        if(fadeMode == "Black"):
            self._fadeMode = FadeMode.Black
        elif(fadeMode == "White"):
            self._fadeMode = FadeMode.White
        else:
            self._fadeMode = FadeMode.Black #Defaults to add

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print "mediaFile config is updated..."
            self._getConfiguration()
            self._midiModulation.checkAndUpdateFromConfiguration()
            self._configurationTree.resetConfigurationUpdated()

    def close(self):
        pass

    def getType(self):
        return "Unknown"

    def equalFileName(self, fileName):
        return self._filename == os.path.normcase(fileName)

    def getFileName(self):
        return self._filename

    def setFileName(self, fileName):
        self._filename = os.path.normcase(fileName)

    def isFileOk(self):
        return self._fileOk
    
    def getImage(self):
        return self._image

    def getFirstImage(self):
        return self._firstImage
    
    def getNumberOfFrames(self):
        return self._numberOfFrames
    
    def getOriginalFps(self):
        return self._originalFrameRate

    def setMidiLengthInBeats(self, midiLength):
        syncLength = midiLength * self._midiTiming.getTicksPerQuarteNote()
        roundLength = round(syncLength)
        if(abs(syncLength - roundLength) < 0.01):
            syncLength = roundLength
        self._syncLength = syncLength

    def getQuantize(self):
        return self._quantizeLength

    def setQuantizeInBeats(self, midiLength):
        quantizeLength = midiLength * self._midiTiming.getTicksPerQuarteNote()
        roundLength = round(quantizeLength)
        if(abs(quantizeLength - roundLength) < 0.01):
            quantizeLength = roundLength
        self._quantizeLength = quantizeLength

    def setStartPosition(self, startSpp):
        self._startSongPosition = startSpp

    def restartSequence(self):
        pass

    def getCurrentFramePos(self):
        return self._currentFrame

    def _getFadeValue(self, currentSongPosition, midiNoteState, midiChannelState):
        fadeValue = self.getFadeModulation(currentSongPosition, midiChannelState, midiNoteState)
        levelValue = self.getLevelModulation(currentSongPosition, midiChannelState, midiNoteState)
        fadeValue = (1.0 - fadeValue) * (1.0 - levelValue)
        return fadeValue

    def _applyOneEffect(self, image, effect, effectArgs):
        if(effect != None):
            effectAmount, effectArg1, effectArg2, effectArg3, effectArg4 = effectArgs
            return effect.applyEffect(image, effectAmount, effectArg1, effectArg2, effectArg3, effectArg4)
        else:
            return image

    def _applyEffects(self, currentSongPosition, midiChannelState, midiNoteState, fadeValue):
        if((self._fadeMode == FadeMode.Black) and (fadeValue < 0.01)):
            self._image = None
        else:

            effect1Args, efect2Args = self.getEffectModulations(currentSongPosition, midiChannelState, midiNoteState) #@UnusedVariable

            imageSize = cv.GetSize(self._captureImage)
            if((imageSize[0] != self._internalResolutionX) and (imageSize[1] != self._internalResolutionY)):
                print "DEBUG: Needs resize because of size"
                self._image = resizeImage(self._captureImage, self._resizeMat)
            else:
                self._image = copyImage(self._captureImage)

            self._image = self._applyOneEffect(self._image, self._effect1, effect1Args)
            self._image = self._applyOneEffect(self._image, self._effect2, efect2Args)

#Blur/Distort
#            self._image = drawEdges(self._image, effectAmount, effectArg1, effectArg2, self._tmpMat2, self._tmpMask)
#            self._image = dilateErode(self._image, effectAmount, self._tmpMat2)
#            self._image = blurImage(self._image, effectAmount, self._tmpMat2)
#            self._image = blurMultiply(self._image, effectAmount, self._tmpMat2, self._tmpMat1)

#Change
#            self._image = self.zoomImage(self._captureImage, -0.25, -0.25, zoom, zoom, self._tmpMat1)
#            self._image = flipImage(self._image, effectArg1, self._tmpMat2)

#Color filters
#            self._image = hueSaturationBrightness(self._image, effectArg1, effectArg2, effectX, self._tmpMat2)
#            self._image = colorize(self._image, effectArg1, effectArg2, effectX, ColorizeMode.Add, effectAmount, self._tmpMat2)
#            self._image = contrastBrightness(self._image, effectAmount, effectArg1, self._tmpMat1)
#            self._image = invert(self._image, effectAmount, self._tmpMat1)
#            self._image = blackAndWhite(self._image, effectAmount, self._tmpMask, self._tmpMat1)
#            self._image = selectiveDesaturate(self._image, effectAmount, effectArg1, effectArg2, self._tmpMat2, self._tmpMask)
    
            if(fadeValue < 0.99):
                self._image = fadeImage(self._image, fadeValue, self._fadeMode, self._fadeMat)
        

    def skipFrames(self, currentSongPosition, midiNoteState, midiChannelState):
        pass

    def openVideoFile(self, midiLength):
        if (os.path.isfile(self._filename) == False):
            self._log.warning("Could not find file: %s in directory: %s", self._filename, os.getcwd())
            raise MediaError("File does not exist!")
        self._videoFile = cv.CaptureFromFile(self._filename)
        try:
            self._captureImage = cv.QueryFrame(self._videoFile)
            self._firstImage = copyImage(self._captureImage)
            self._captureImage = cv.QueryFrame(self._videoFile)
            self._secondImage = copyImage(self._captureImage)
            self._captureImage = self._firstImage
        except:
            self._log.warning("Exception while reading: %s", os.path.basename(self._filename))
            print "Exception while reading: " + os.path.basename(self._filename)
            raise MediaError("File caused exception!")
        if (self._captureImage == None):
            self._log.warning("Could not read frames from: %s", os.path.basename(self._filename))
            print "Could not read frames from: " + os.path.basename(self._filename)
            raise MediaError("File could not be read!")
        try:
            self._numberOfFrames = int(cv.GetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_FRAME_COUNT))
            self._originalFrameRate = int(cv.GetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_FPS))
        except:
            self._log.warning("Exception while getting number of frames from: %s", os.path.basename(self._filename))
            raise MediaError("File caused exception!")
        if(self._numberOfFrames < 20):
            try:
                self._bufferedImageList = []
                self._bufferedImageList.append(self._firstImage)
                self._bufferedImageList.append(self._secondImage)
                for i in range(self._numberOfFrames - 2): #@UnusedVariable
                    self._captureImage = cv.QueryFrame(self._videoFile)
                    self._bufferedImageList.append(copyImage(self._captureImage))
            except:
                self._log.warning("Exception while reading: %s", os.path.basename(self._filename))
                print "Exception while reading: " + os.path.basename(self._filename)
                raise MediaError("File caused exception!")
        self._captureImage = self._firstImage
        self._originalTime = float(self._numberOfFrames) / self._originalFrameRate
        if(midiLength != None): # Else we get length from configuration or default.
            if(midiLength <= 0.0):
                midiLength = self._midiTiming.guessMidiLength(self._originalTime)
            self.setMidiLengthInBeats(midiLength)
        self._log.warning("Read file %s with %d frames, framerate %d and length %f guessed MIDI length %f", os.path.basename(self._filename), self._numberOfFrames, self._originalFrameRate, self._originalTime, self._syncLength)
        self._fileOk = True

    def openFile(self, midiLength):
        pass

    def mixWithImage(self, image, mixMode, effects, mixMat1, mixMat2, mixMask):
        if(self._image == None):
            return image
        else:
            if(mixMode == MixMode.Default):
                mixMode = self._mixMode
            if(effects != None):
                preEffect, preEffectArgs, postEffect, postEffectArgs = effects
            else:
                preEffect, preEffectArgs, postEffect, postEffectArgs = (None, None, None, None)
            self._image = self._applyOneEffect(self._image, preEffect, preEffectArgs)
            mixedImage =  mixImages(mixMode, image, self._image, mixMat1, mixMat2, mixMask)
            mixedImage = self._applyOneEffect(mixedImage, postEffect, postEffectArgs)
            return mixedImage
    
class ImageFile(MediaFile):
    def __init__(self, fileName, midiTimingClass, configurationTree):
        MediaFile.__init__(self, fileName, midiTimingClass, configurationTree)

    def getType(self):
        return "Image"

    def close(self):
        pass

    def skipFrames(self, currentSongPosition, midiNoteState, midiChannelState):
        fadeValue = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState)
        if(fadeValue < 0.01):
            self._image = None
            return
        self._applyEffects(currentSongPosition, midiChannelState, midiNoteState, fadeValue)

    def openFile(self, midiLength):
        if (os.path.isfile(self._filename) == False):
            self._log.warning("Could not find file: %s in directory: %s", self._filename, os.getcwd())
            raise MediaError("File does not exist!")
        try:
            self._captureImage = cv.LoadImage(self._filename)
        except:
            self._log.warning("Exception while reading: %s", os.path.basename(self._filename))
            print "Exception while reading: " + os.path.basename(self._filename)
            raise MediaError("File caused exception!")
        if (self._captureImage == None):
            self._log.warning("Could not read frames from: %s", os.path.basename(self._filename))
            print "Could not read frames from: " + os.path.basename(self._filename)
            raise MediaError("File could not be read!")
        self._firstImage = self._captureImage
        self._originalTime = 1.0
        self._log.warning("Read image file %s", os.path.basename(self._filename))
        self._fileOk = True

class ImageSequenceFile(MediaFile):
    class Mode:
        Time, ReTrigger, Controller = range(3)

    def __init__(self, fileName, midiTimingClass, configurationTree):
        MediaFile.__init__(self, fileName, midiTimingClass, configurationTree)
        self._triggerCounter = 0
        self._firstTrigger = True
        self._sequenceMode = ImageSequenceFile.Mode.Time
        self._configurationTree.addTextParameter("SequenceMode", "Time")

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
        seqMode = self._configurationTree.getValue("SequenceMode")
        if(seqMode == "ReTrigger"):
            self._sequenceMode = ImageSequenceFile.Mode.ReTrigger
        elif(seqMode == "Controller"):
            self._sequenceMode = ImageSequenceFile.Mode.Controller
        else:
            self._sequenceMode = ImageSequenceFile.Mode.Time #Defaults to time

    def close(self):
        pass

    def getType(self):
        return "ImageSequence"

    def restartSequence(self):
        self._firstTrigger = True
        self._startSongPosition = 0.0
        self._triggerCounter = 0

    def setStartPosition(self, startSpp):
        lastSpp = self._startSongPosition
        if(startSpp != lastSpp):
            print "Trigger "
            if(self._firstTrigger == True):
                self._firstTrigger = False
            else:
                self._triggerCounter += 1
            print "TriggerCount: " + str(self._triggerCounter) + " startSPP: " + str(startSpp)
        self._startSongPosition = startSpp

    def getPlaybackModulation(self, songPosition, midiChannelStateHolder, midiNoteStateHolder):
        return self._midiModulation.getModlulationValue(self._playbackModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)

    def skipFrames(self, currentSongPosition, midiNoteState, midiChannelState):
        fadeValue = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState)
        if((self._fadeMode == FadeMode.Black) and (fadeValue < 0.01)):
            self._image = None
            return

        lastFrame = self._currentFrame
        
        if(self._sequenceMode == ImageSequenceFile.Mode.Time):
            self._currentFrame = (int((currentSongPosition - self._startSongPosition) / self._syncLength) % self._numberOfFrames)
        elif(self._sequenceMode == ImageSequenceFile.Mode.ReTrigger):
            self._currentFrame =  (self._triggerCounter % self._numberOfFrames)
        elif(self._sequenceMode == ImageSequenceFile.Mode.Controller):
            self._currentFrame = int(self.getPlaybackModulation(currentSongPosition, midiChannelState, midiNoteState) * self._numberOfFrames)

        if(lastFrame != self._currentFrame):
            if(self._bufferedImageList != None):
                self._captureImage = self._bufferedImageList[self._currentFrame]
                print "Buffered image!!!"
            else:
                cv.SetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_POS_FRAMES, self._currentFrame)
                if(self._currentFrame == 0):
                    self._captureImage = self._firstImage
                    self._log.debug("Setting firstframe %d", self._currentFrame)
                elif(self._currentFrame == 1):
                    self._captureImage = self._secondImage
                    self._log.debug("Setting secondframe %d", self._currentFrame)
                else:
                    self._captureImage = cv.QueryFrame(self._videoFile)
                    if(self._captureImage == None):
                        self._captureImage = self._firstImage
            self._applyEffects(currentSongPosition, midiChannelState, midiNoteState, fadeValue)
            return True
        else:
            self._log.debug("Same frame %d currentSongPosition %f", self._currentFrame, currentSongPosition)
            self._applyEffects(currentSongPosition, midiChannelState, midiNoteState, fadeValue)
            return False

    def openFile(self, midiLength):
        self.openVideoFile(midiLength)

class VideoLoopFile(MediaFile):
    class Mode:
        Normal, Reverse, PingPong, PingPongReverse, DontLoop, DontLoopReverse = range(6)

    def __init__(self, fileName, midiTimingClass, configurationTree):
        MediaFile.__init__(self, fileName, midiTimingClass, configurationTree)
        self._loopMode = VideoLoopFile.Mode.Normal
        self._configurationTree.addTextParameter("LoopMode", "Normal")

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
        loopMode = self._configurationTree.getValue("LoopMode")
        if(loopMode == "Normal"):
            self._loopMode = VideoLoopFile.Mode.Normal
        elif(loopMode == "Reverse"):
            self._loopMode = VideoLoopFile.Mode.Reverse
        elif(loopMode == "PingPong"):
            self._loopMode = VideoLoopFile.Mode.PingPong
        elif(loopMode == "PingPongReverse"):
            self._loopMode = VideoLoopFile.Mode.PingPongReverse
        elif(loopMode == "DontLoop"):
            self._loopMode = VideoLoopFile.Mode.DontLoop
        elif(loopMode == "DontLoopReverse"):
            self._loopMode = VideoLoopFile.Mode.DontLoopReverse
        else:
            self._loopMode = VideoLoopFile.Mode.Normal #Defaults to normal

    def close(self):
        pass

    def getType(self):
        return "VideoLoop"

    def skipFrames(self, currentSongPosition, midiNoteState, midiChannelState):
        fadeValue = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState)
        if((self._fadeMode == FadeMode.Black) and (fadeValue < 0.01)):
            self._image = None
            return
        lastFrame = self._currentFrame

        framePos = int(((currentSongPosition - self._startSongPosition) / self._syncLength) * self._numberOfFrames)
        if(self._loopMode == VideoLoopFile.Mode.Normal):
            self._currentFrame = framePos % self._numberOfFrames
        elif(self._loopMode == VideoLoopFile.Mode.Reverse):
            self._currentFrame = -framePos % self._numberOfFrames
        elif(self._loopMode == VideoLoopFile.Mode.PingPong):
            self._currentFrame = abs(((framePos + self._numberOfFrames) % (2 * self._numberOfFrames)) - self._numberOfFrames)
        elif(self._loopMode == VideoLoopFile.Mode.PingPongReverse):
            self._currentFrame = abs((framePos % (2 * self._numberOfFrames)) - self._numberOfFrames)
        elif(self._loopMode == VideoLoopFile.Mode.DontLoop):
            if(framePos < self._numberOfFrames):
                self._currentFrame = framePos
            else:
                self._image = None
        elif(self._loopMode == VideoLoopFile.Mode.DontLoopReverse):
            if(framePos < self._numberOfFrames):
                self._currentFrame = self._numberOfFrames - 1 - framePos
            else:
                self._image = None
        else: #Normal
            self._currentFrame = framePos % self._numberOfFrames

        if(lastFrame != self._currentFrame):
            cv.SetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_POS_FRAMES, self._currentFrame)
            if(self._currentFrame == 0):
                self._captureImage = self._firstImage
#                cv.SetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_POS_FRAMES, -1)
                self._log.debug("Setting firstframe %d", self._currentFrame)
            elif(self._currentFrame == 1):
                self._captureImage = self._secondImage
                self._log.debug("Setting secondframe %d", self._currentFrame)
            else:
                self._captureImage = cv.QueryFrame(self._videoFile)
                if(self._captureImage == None):
                    self._captureImage = self._firstImage
            self._applyEffects(currentSongPosition, midiChannelState, midiNoteState, fadeValue)
            return True
        else:
            self._log.debug("Same frame %d currentSongPosition %f", self._currentFrame, currentSongPosition)
            self._applyEffects(currentSongPosition, midiChannelState, midiNoteState, fadeValue)
            return False

    def openFile(self, midiLength):
        self.openVideoFile(midiLength)

class MediaError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)