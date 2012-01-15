'''
Created on 12. okt. 2011

@author: pcn
'''
import os.path
import logging
from cv2 import cv
import numpy
from midi.MidiModulation import MidiModulation

def getEmptyImage(x, y):
    resizeMat = crateMat(x,y)
    return resizeImage(cv.CreateImage((x,y), cv.IPL_DEPTH_8U, 3), resizeMat)

def crateMat(width, heigth):
    return cv.CreateMat(heigth, width, cv.CV_8UC3)

def crateMask(width, heigth):
    return cv.CreateMat(heigth, width, cv.CV_8UC1)

def copyImage(image):
    return cv.CloneImage(image)

def resizeImage(image, resizeMat):
    cv.Resize(image, resizeMat)
    return resizeMat

def zoomImage(image, xcenter, ycenter, zoomX, zoomY, minRange, maxRange, resizeMat):
    originalWidth, originalHeight = cv.GetSize(image)
    rangeFraction = maxRange - minRange
    zoomXFraction = minRange + (rangeFraction * zoomX)
    zoomYFraction = minRange + (rangeFraction * zoomY)
    width = int(float(originalWidth) * zoomXFraction)
    height = int(float(originalHeight) * zoomYFraction)
    left = int((originalWidth / 2) + (originalWidth * xcenter / 2) - (width / 2))
    top = int((originalHeight / 2) + (originalHeight * ycenter / 2) - (height / 2))
    right = left + width
    bottom = top + height
    outputRect = False
    outPutLeft = 0
    outPutWidth = -1
    outPutTop = 0
    outPutHeight = -1
    if(left < 0):
        outPutLeft = -int(float(left) / zoomXFraction)
        width = width + left
        left = 0
        outputRect = True
    if(right > originalWidth):
        outPutWidth = originalWidth+int(float(originalWidth - right) / zoomXFraction) - outPutLeft
        width = originalWidth - left
        outputRect = True
    if(top < 0):
        outPutTop = -int(float(top) / zoomYFraction)
        height = height + top
        top = 0
        outputRect = True
    if(bottom > originalHeight):
        outPutHeight = originalHeight+int(float(originalHeight - bottom) / zoomYFraction) - outPutTop
        height = originalHeight - top
        outputRect = True
#    print "Zoom: " + str(zoomX) + " M: " + str(minRange) + " R:(+) " + str(rangeFraction) + " w: " + str(width) + " h: " + str(height) + " l: " + str(left) + " t: " + str(top)
    src_region = cv.GetSubRect(image, (left, top, width, height) )
    if(outputRect):
        if(outPutWidth < 0):
            outPutWidth = originalWidth - outPutLeft
        if(outPutHeight < 0):
            outPutHeight = originalHeight - outPutTop
#        print "Zoom OUT: " + str(outPutWidth) + " h: " + str(outPutHeight) + " l: " + str(outPutLeft) + " t: " + str(outPutTop)
        tmpMat = crateMat(outPutWidth, outPutHeight)
        resized = resizeImage(src_region, tmpMat)
        cv.SetZero(resizeMat)
        dst_region = cv.GetSubRect(resizeMat, (outPutLeft, outPutTop, outPutWidth, outPutHeight) )
        cv.Copy(resized, dst_region)
        return resizeMat
    return resizeImage(src_region, resizeMat)

def fadeImage(image, value, tmpMat):
    cv.ConvertScaleAbs(image, tmpMat, value, 0.0)
    return tmpMat

def mixImageSelfMask(image1, image2, mixMask, mixMat):
    cv.Copy(image1, mixMat)
    cv.CmpS(image2, 0.1, mixMask, cv.CV_CMP_GT)
    cv.Merge(mixMask, mixMask, mixMask, None, mixMat)
    tmpMat = crateMat(800, 600)
    cv.ConvertScale(mixMat, tmpMat, 255)
    return tmpMat
    cv.Copy(image2, mixMat, mixMask)
    return mixMat

def mixImagesAdd(image1, image2, mixMat):
    cv.Add(image1, image2, mixMat)
    return mixMat

def mixImagesMultiply(image1, image2, mixMat):
    cv.Mul(image1, image2, mixMat, 0.002)
    return mixMat

class MixMode:
    (Add, Multiply, LumaKey, Replace) = range(4)

def mixImages(mode, image1, image2, mixMat, mixMask):
    if(mode == MixMode.Add):
        return mixImagesAdd(image1, image2, mixMat)
    if(mode == MixMode.Multiply):
        return mixImagesMultiply(image1, image2, mixMat)
    if(mode == MixMode.LumaKey):
        return mixImageSelfMask(image1, image2, mixMask, mixMat)
    if(mode == MixMode.Replace):
        return image2

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
        self._tmpMat = crateMat(self._internalResolutionX, self._internalResolutionY)
        self._tmpMask = crateMask(self._internalResolutionX, self._internalResolutionY)
        self._fileOk = False
        self._image = None
        self._captureImage = None
        self._firstImage = None
        self._secondImage = None
        self._numberOfFrames = 0
        self._originalFrameRate = 25
        self._originalTime = 0.0
        self._currentFrame = 0;
        self._startSongPosition = 0.0

        self._minZoomPercent = 0.25
        self._maxZoomPercent = 4.0

        self._mixMode = MixMode.Add

        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._log.setLevel(logging.WARNING)

        self._configurationTree.addTextParameterStatic("Type", self.getType())
        self._configurationTree.addTextParameterStatic("FileName", self._filename)
        self._midiModulation = MidiModulation(self._configurationTree.addChildUnique("Modulation"), self._midiTiming)
        self._setupConfiguration()
        self._getConfiguration()

    def _setupConfiguration(self):
        self._midiModulation.setModulationReceiver("PlayBack", "MidiChannel.Controller.ModWheel")
        self._midiModulation.setModulationReceiver("FadeInOut", "ADSR.AR.0.0|8.0")
        self._midiModulation.setModulationReceiver("Level", "None")
        self._midiModulation.setModulationReceiver("EffectX", "None")
        self._midiModulation.setModulationReceiver("EffectY", "None")
        self._midiModulation.setModulationReceiver("EffectAmount", "MidiChannel.Controller.ModWheel")
        self._midiModulation.setModulationReceiver("EffectArgument1", "None")
        self._midiModulation.setModulationReceiver("EffectArgument2", "None")
        self._playbackModulationId = -1
        self._fadeModulationId = -1
        self._levelModulationId = -1
        self._effectXModulationId = -1
        self._effectYModulationId = -1
        self._effectAmountModulationId = -1
        self._effectArgument1ModulationId = -1
        self._effectArgument2ModulationId = -1

        self._configurationTree.addFloatParameter("SyncLength", 4.0) #Default one bar (re calculated on load)
        self._configurationTree.addFloatParameter("QuantizeLength", 4.0)#Default one bar
        self._syncLength = -1.0
        self._quantizeLength = -1.0

    def getFadeModulation(self, songPosition, midiChannelStateHolder, midiNoteStateHolder):
        return self._midiModulation.getModlulationValue(self._fadeModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)

    def getLevelModulation(self, songPosition, midiChannelStateHolder, midiNoteStateHolder):
        return self._midiModulation.getModlulationValue(self._levelModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)

    def _getConfiguration(self):
        self._playbackModulationId = self._midiModulation.connectModulation("PlayBack")
        self._fadeModulationId = self._midiModulation.connectModulation("FadeInOut")
        self._levelModulationId = self._midiModulation.connectModulation("Level")
        self._effectXModulationId = self._midiModulation.connectModulation("EffectX")
        self._effectYModulationId = self._midiModulation.connectModulation("EffectY")
        self._effectAmountModulationId = self._midiModulation.connectModulation("EffectAmount")
        self._effectArgument1ModulationId = self._midiModulation.connectModulation("EffectArgument1")
        self._effectArgument2ModulationId = self._midiModulation.connectModulation("EffectArgument2")

        self.setMidiLengthInBeats(self._configurationTree.getValue("SyncLength"))
        self.setQuantizeInBeats(self._configurationTree.getValue("QuantizeLength"))

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
        self._configurationTree.setValue("SyncLength", midiLength)
        self._syncLength = midiLength * self._midiTiming.getTicksPerQuarteNote()

    def getQuantize(self):
        return self._quantizeLength

    def setQuantizeInBeats(self, midiLength):
        self._configurationTree.setValue("QuantizeLength", midiLength)
        self._quantizeLength = midiLength * self._midiTiming.getTicksPerQuarteNote()

    def setStartPosition(self, startSpp):
        self._startSongPosition = startSpp

    def restartSequence(self):
        pass

    def getCurrentFramePos(self):
        return self._currentFrame

    def resizeImage(self, image):
        return resizeImage(image, self._tmpMat)

    def zoomImage(self, image, xcenter, ycenter, xzoom, yzoom):
        return zoomImage(image, xcenter, ycenter, xzoom, yzoom, self._minZoomPercent, self._maxZoomPercent, self._tmpMat)

    def _aplyEffects(self, currentSongPosition, midiChannelState, midiNoteState):
        fadeValue = self.getFadeModulation(currentSongPosition, midiChannelState, midiNoteState)
        levelValue = self.getLevelModulation(currentSongPosition, midiChannelState, midiNoteState)
        fadeValue = (1.0 - fadeValue) * (1.0 - levelValue)
        if(fadeValue < 0.01):
            self._image = None
        else:
    
#            zoom = abs((2 * float(self._currentFrame) / self._numberOfFrames) -1.0)
#            self._image = self.zoomImage(self._captureImage, -0.25, -0.25, zoom, zoom)
            self._image = self.resizeImage(self._captureImage)
#            self._image = self._captureImage
    
            if(fadeValue < 0.99):
                self._image = fadeImage(self._image, fadeValue, self._tmpMat)
        

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
        self._originalTime = float(self._numberOfFrames) / self._originalFrameRate
        if(midiLength != None): # Else we get length from configuration or default.
            if(midiLength <= 0.0):
                midiLength = self._midiTiming.guessMidiLength(self._originalTime)
            self.setMidiLengthInBeats(midiLength)
        self._log.warning("Read file %s with %d frames, framerate %d and length %f guessed MIDI length %f", os.path.basename(self._filename), self._numberOfFrames, self._originalFrameRate, self._originalTime, self._syncLength)
        self._fileOk = True

    def openFile(self, midiLength):
        pass

    def mixWithImage(self, image):
        if(self._image == None):
            return image
        else:
            return mixImages(self._mixMode, image, self._image, self._tmpMat, self._tmpMask)
    
class ImageFile(MediaFile):
    def __init__(self, fileName, midiTimingClass, configurationTree):
        MediaFile.__init__(self, fileName, midiTimingClass, configurationTree)

    def getType(self):
        return "Image"

    def close(self):
        pass

    def skipFrames(self, currentSongPosition, midiNoteState, midiChannelState):
        self._aplyEffects(currentSongPosition, midiChannelState, midiNoteState)

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
        self.setQuantizeInBeats(1.0)
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
            if(self._firstTrigger == True):
                self._firstTrigger = False
            else:
                self._triggerCounter += 1
        self._startSongPosition = startSpp

    def getPlaybackModulation(self, songPosition, midiChannelStateHolder, midiNoteStateHolder):
        return self._midiModulation.getModlulationValue(self._playbackModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)

    def skipFrames(self, currentSongPosition, midiNoteState, midiChannelState):
        lastFrame = self._currentFrame
        
        if(self._sequenceMode == ImageSequenceFile.Mode.Time):
            self._currentFrame = (int((currentSongPosition - self._startSongPosition) / self._syncLength) % self._numberOfFrames) - 1
        elif(self._sequenceMode == ImageSequenceFile.Mode.ReTrigger):
            self._currentFrame =  (self._triggerCounter % self._numberOfFrames) - 1
        elif(self._sequenceMode == ImageSequenceFile.Mode.Controller):
            self._currentFrame = int(self.getPlaybackModulation(currentSongPosition, midiChannelState, midiNoteState) * self._numberOfFrames) - 1

        if(lastFrame != self._currentFrame):
            cv.SetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_POS_FRAMES, self._currentFrame)
            if(self._currentFrame == -1):
                self._captureImage = self._firstImage
                self._log.debug("Setting firstframe %d", self._currentFrame)
            elif(self._currentFrame == 0):
                self._captureImage = self._secondImage
                self._log.debug("Setting secondframe %d", self._currentFrame)
            else:
                self._captureImage = cv.QueryFrame(self._videoFile)
                if(self._captureImage == None):
                    self._captureImage = self._firstImage
            self._aplyEffects(currentSongPosition, midiChannelState, midiNoteState)
            return True
        else:
            self._log.debug("Same frame %d currentSongPosition %f", self._currentFrame, currentSongPosition)
            self._aplyEffects(currentSongPosition, midiChannelState, midiNoteState)
            return False

    def openFile(self, midiLength):
        self.openVideoFile(midiLength)

class VideoLoopFile(MediaFile):
    def __init__(self, fileName, midiTimingClass, configurationTree):
        MediaFile.__init__(self, fileName, midiTimingClass, configurationTree)

    def close(self):
        pass

    def getType(self):
        return "VideoLoop"

    def skipFrames(self, currentSongPosition, midiNoteState, midiChannelState):
        lastFrame = self._currentFrame
        self._currentFrame = int((((currentSongPosition - self._startSongPosition) / self._syncLength) * self._numberOfFrames) % self._numberOfFrames) - 1

        if(lastFrame != self._currentFrame):
            cv.SetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_POS_FRAMES, self._currentFrame)
            if(self._currentFrame == -1):
                self._captureImage = self._firstImage
#                cv.SetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_POS_FRAMES, -1)
                self._log.debug("Setting firstframe %d", self._currentFrame)
            elif(self._currentFrame == 0):
                self._captureImage = self._secondImage
                self._log.debug("Setting secondframe %d", self._currentFrame)
            else:
                self._captureImage = cv.QueryFrame(self._videoFile)
                if(self._captureImage == None):
                    self._captureImage = self._firstImage
            self._aplyEffects(currentSongPosition, midiChannelState, midiNoteState)
            return True
        else:
            self._log.debug("Same frame %d currentSongPosition %f", self._currentFrame, currentSongPosition)
            self._aplyEffects(currentSongPosition, midiChannelState, midiNoteState)
            return False

    def openFile(self, midiLength):
        self.openVideoFile(midiLength)

class MediaError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)