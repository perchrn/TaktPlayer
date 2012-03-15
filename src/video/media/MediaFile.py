'''
Created on 12. okt. 2011

@author: pcn
'''
import os.path
import logging
from cv2 import cv
import numpy
from midi.MidiModulation import MidiModulation
from video.Effects import createMat, getEffectByName
import hashlib
from video.media.MediaFileModes import MixMode, VideoLoopMode, ImageSequenceMode,\
    FadeMode, getMixModeFromName, ModulationValueMode

def copyImage(image):
    return cv.CloneImage(image)

def resizeImage(image, resizeMat):
    cv.Resize(image, resizeMat)
    return resizeMat

def scaleAndSave(image, osFileName, resizeMat):
    cv.Resize(image, resizeMat)
    cv.SaveImage(osFileName, resizeMat)

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
    def __init__(self, fileName, midiTimingClass, effectsConfiguration, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY):
        self._configurationTree = configurationTree
        self._effectsConfigurationTemplates = effectsConfiguration
        self._mediaFadeConfigurationTemplates = fadeConfiguration
        self.setFileName(fileName)
        self._midiTiming = midiTimingClass
        self._internalResolutionX =  internalResolutionX
        self._internalResolutionY =  internalResolutionY
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

        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._log.setLevel(logging.WARNING)

        self._configurationTree.addTextParameterStatic("Type", self.getType())
        self._configurationTree.addTextParameterStatic("FileName", self._filename)
        self._midiModulation = None
        self._setupConfiguration()

    def _setupConfiguration(self):
        self._configurationTree.addFloatParameter("SyncLength", 4.0) #Default one bar (re calculated on load)
        self._configurationTree.addFloatParameter("QuantizeLength", 4.0)#Default one bar
        self._configurationTree.addTextParameter("MixMode", "Add")#Default Add
        self._defaultEffect1SettingsName = "MediaDefault1"
        self._configurationTree.addTextParameter("Effect1Config", self._defaultEffect1SettingsName)#Default MediaDefault1
        self._defaultEffect2SettingsName = "MediaDefault2"
        self._configurationTree.addTextParameter("Effect2Config", self._defaultEffect2SettingsName)#Default MediaDefault2
        self._defaultFadeSettingsName = "Default"
        self._configurationTree.addTextParameter("FadeConfig", self._defaultFadeSettingsName)#Default Default
        
        self._syncLength = -1.0
        self._quantizeLength = -1.0
        self._mixMode = MixMode.Add

        self._modulationRestartMode = ModulationValueMode.KeepOld
        self._effect1StartControllerValues = (None, None, None, None, None)
        self._effect2StartControllerValues = (None, None, None, None, None)
        self._effect1StartValues = (0.0, 0.0, 0.0, 0.0, 0.0)
        self._effect2StartValues = (0.0, 0.0, 0.0, 0.0, 0.0)
        self._effect1ConfigStartValues = (0.0, 0.0, 0.0, 0.0, 0.0)
        self._effect2ConfigStartValues = (0.0, 0.0, 0.0, 0.0, 0.0)
        self._effect1OldValues = (0.0, 0.0, 0.0, 0.0, 0.0)
        self._effect2OldValues = (0.0, 0.0, 0.0, 0.0, 0.0)

    def _getConfiguration(self):
        self._effect1ModulationTemplate = self._configurationTree.getValue("Effect1Config")
        self._effect1Settings = self._effectsConfigurationTemplates.getTemplate(self._effect1ModulationTemplate)
        if(self._effect1Settings == None):
            self._effect1Settings = self._effectsConfigurationTemplates.getTemplate(self._defaultEffect1SettingsName)
        self._effect1 = getEffectByName(self._effect1Settings.getEffectName(), self._configurationTree, self._internalResolutionX, self._internalResolutionY)
        self._effect2ModulationTemplate = self._configurationTree.getValue("Effect2Config")
        self._effect2Settings = self._effectsConfigurationTemplates.getTemplate(self._effect2ModulationTemplate)
        if(self._effect2Settings == None):
            self._effect2Settings = self._effectsConfigurationTemplates.getTemplate(self._defaultEffect2SettingsName)
        self._effect2 = getEffectByName(self._effect2Settings.getEffectName(), self._configurationTree, self._internalResolutionX, self._internalResolutionY)

        self._fadeAndLevelTemplate = self._configurationTree.getValue("FadeConfig")
        self._fadeAndLevelSettings = self._mediaFadeConfigurationTemplates.getTemplate(self._fadeAndLevelTemplate)
        if(self._fadeAndLevelSettings == None):
            self._fadeAndLevelSettings = self._mediaFadeConfigurationTemplates.getTemplate(self._defaultFadeSettingsName)

        self.setMidiLengthInBeats(self._configurationTree.getValue("SyncLength"))
        self.setQuantizeInBeats(self._configurationTree.getValue("QuantizeLength"))

        mixMode = self._configurationTree.getValue("MixMode")
        self._mixMode = getMixModeFromName(mixMode)

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print "mediaFile config is updated..."
            self._getConfiguration()
            if(self._midiModulation != None):
                self._midiModulation.checkAndUpdateFromConfiguration()
            self._configurationTree.resetConfigurationUpdated()

    def close(self):
        pass

    def getType(self):
        return "Unknown"

    def equalFileName(self, fileName):
        print "equalFileName " + self._filename + " == " + os.path.normcase(fileName)
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

    def noteJustTriggered(self, songPosition, midiNoteStateHolder, midiChannelStateHolder):
        if(self._modulationRestartMode != ModulationValueMode.RawInput):
            self._effect1StartControllerValues = self._effect1Settings.getValues(songPosition, midiChannelStateHolder, midiNoteStateHolder)
            self._effect2StartControllerValues = self._effect2Settings.getValues(songPosition, midiChannelStateHolder, midiNoteStateHolder)
        else:
            self._effect1StartControllerValues = (None, None, None, None, None)
            self._effect2StartControllerValues = (None, None, None, None, None)
        if(self._modulationRestartMode == ModulationValueMode.ResetToDefault):
            self._effect1StartValues = self._effect1ConfigStartValues
            self._effect2StartValues = self._effect2ConfigStartValues
        else: #KeepOldValues
            self._effect1StartValues = self._effect1OldValues
            self._effect2StartValues = self._effect2OldValues

    def _getFadeValue(self, currentSongPosition, midiNoteState, midiChannelState):
        fadeMode, fadeValue, levelValue = self._fadeAndLevelSettings.getValues(currentSongPosition, midiNoteState, midiChannelState)
        fadeValue = (1.0 - fadeValue) * (1.0 - levelValue)
        return fadeMode, fadeValue

    def _applyOneEffect(self, image, effect, effectSettings, effectStartControllerValues, effectStartValues, songPosition, midiChannelStateHolder, midiNoteStateHolder):
        if(effectSettings != None):
            effectAmount, effectArg1, effectArg2, effectArg3, effectArg4 = effectSettings.getValues(songPosition, midiChannelStateHolder, midiNoteStateHolder)
            #TODO: Add mode where values must pass start values?
            if(effectAmount == effectStartControllerValues[0]):
                effectAmount = effectStartValues[0]
            if(effectArg1 == effectStartControllerValues[1]):
                effectArg1 = effectStartValues[1]
            if(effectArg2 == effectStartControllerValues[2]):
                effectArg2 = effectStartValues[2]
            if(effectArg3 == effectStartControllerValues[3]):
                effectArg3 = effectStartValues[3]
            if(effectArg4 == effectStartControllerValues[4]):
                effectArg4 = effectStartValues[4]
            if(effect != None):
                image = effect.applyEffect(image, effectAmount, effectArg1, effectArg2, effectArg3, effectArg4)
            return (image, (effectAmount, effectArg1, effectArg2, effectArg3, effectArg4))
        else:
            return (image, (0.0, 0.0, 0.0, 0.0, 0.0))

    def _applyEffects(self, currentSongPosition, midiChannelState, midiNoteState, fadeValue):
        imageSize = cv.GetSize(self._captureImage)
        if((imageSize[0] != self._internalResolutionX) and (imageSize[1] != self._internalResolutionY)):
            self._image = resizeImage(self._captureImage, self._resizeMat)
        else:
            self._image = copyImage(self._captureImage)

        (self._image, self._effect1OldValues) = self._applyOneEffect(self._image, self._effect1, self._effect1Settings, self._effect1StartControllerValues, self._effect1StartValues, currentSongPosition, midiChannelState, midiNoteState)
        (self._image, self._effect2OldValues) = self._applyOneEffect(self._image, self._effect2, self._effect2Settings, self._effect2StartControllerValues, self._effect2StartValues, currentSongPosition, midiChannelState, midiNoteState)

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

    def getThumbnailId(self, videoPosition):
        image = self._firstImage
        if(videoPosition > 0.0):
            if(videoPosition < 0.28):
                videoPosition = 0.25
            elif(videoPosition < 0.41):
                videoPosition = 0.33
            elif(videoPosition < 0.66):
                videoPosition = 0.50
            else:
                videoPosition = 0.75
            #TODO: skipFrames etc.
        else:
            videoPosition = 0.0

        filenameHash = hashlib.sha224(self._filename).hexdigest()
        thumbnailName = "thumbs/%s_%0.2f.jpg" % (filenameHash, videoPosition)
        osFileName = os.path.normpath(thumbnailName)
        if (os.path.isfile(osFileName) == False):
            print "Thumb file does not exist. Generating... " + thumbnailName
            destWidth, destHeight = (40, 30)
            resizeMat = createMat(destWidth, destHeight)
            scaleAndSave(image, osFileName, resizeMat)
        else:
            print "Thumb file already exist. " + thumbnailName
        return thumbnailName

    def openFile(self, midiLength):
        pass

    def mixWithImage(self, image, mixMode, effects, currentSongPosition, midiChannelState, midiNoteState, mixMat1, mixMat2, mixMask):
        if(self._image == None):
            return image
        else:
            if(mixMode == MixMode.Default):
                mixMode = self._mixMode
            if(effects != None):
                preEffect, preEffectSettings, postEffect, postEffectSettings = effects
            else:
                preEffect, preEffectSettings, postEffect, postEffectSettings = (None, None, None, None)
            dummy1Values = (None, None, None, None, None)
            dummy2Values = None
            (self._image, usedValues) = self._applyOneEffect(self._image, preEffect, preEffectSettings, dummy1Values, dummy1Values, currentSongPosition, midiChannelState, midiNoteState) #@UnusedVariable
            mixedImage =  mixImages(mixMode, image, self._image, mixMat1, mixMat2, mixMask)
            (self._image, usedValues) = self._applyOneEffect(self._image, postEffect, postEffectSettings, dummy1Values, dummy1Values, currentSongPosition, midiChannelState, midiNoteState) #@UnusedVariable
            return mixedImage
    
class ImageFile(MediaFile):
    def __init__(self, fileName, midiTimingClass, effectsConfiguration, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY):
        MediaFile.__init__(self, fileName, midiTimingClass, effectsConfiguration, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY)
        self._getConfiguration()

    def getType(self):
        return "Image"

    def close(self):
        pass

    def skipFrames(self, currentSongPosition, midiNoteState, midiChannelState):
        fadeMode, fadeValue = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState)
        if((fadeMode == FadeMode.Black) and (fadeValue < 0.01)):
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

class CameraInput(MediaFile):
    def __init__(self, fileName, midiTimingClass, effectsConfiguration, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY):
        MediaFile.__init__(self, fileName, midiTimingClass, effectsConfiguration, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY)
        self._cameraId = int(fileName)
        self._getConfiguration()

    def getType(self):
        return "Camera"

    def close(self):
        pass

    def skipFrames(self, currentSongPosition, midiNoteState, midiChannelState, internalResolutionX, internalResolutionY):
        fadeMode, fadeValue = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState, internalResolutionX, internalResolutionY)
        if((fadeMode == FadeMode.Black) and (fadeValue < 0.01)):
            self._image = None
            return
        self._captureImage = cv.QueryFrame(self._videoFile)
        self._applyEffects(currentSongPosition, midiChannelState, midiNoteState, fadeValue)

    def openFile(self, midiLength):
        self._videoFile = cv.CaptureFromCAM(self._cameraId)
        try:
            self._captureImage = cv.QueryFrame(self._videoFile)
            self._firstImage = copyImage(self._captureImage)
        except:
            self._log.warning("Exception while reading: %d", self._cameraId)
            print "Exception while reading: " + str(self._cameraId)
            raise MediaError("File caused exception!")
        if (self._captureImage == None):
            self._log.warning("Could not read frames from: %d", self._cameraId)
            print "Could not read frames from: " + str(self._cameraId)
            raise MediaError("File could not be read!")
        try:
            self._originalFrameRate = int(cv.GetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_FPS))
        except:
            self._log.warning("Exception while getting number of frames per second from: %d", self._cameraId)
            raise MediaError("File caused exception!")
        self._log.warning("Opened camera %d with framerate %d",self._cameraId, self._originalFrameRate)
        self._fileOk = True

class ImageSequenceFile(MediaFile):
    def __init__(self, fileName, midiTimingClass, effectsConfiguration, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY):
        MediaFile.__init__(self, fileName, midiTimingClass, effectsConfiguration, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY)
        self._triggerCounter = 0
        self._firstTrigger = True
        self._sequenceMode = ImageSequenceMode.Time
        self._midiModulation = MidiModulation(self._configurationTree, self._midiTiming)
        self._configurationTree.addTextParameter("SequenceMode", "Time")
        self._midiModulation.setModulationReceiver("PlayBackModulation", "None")
        self._playbackModulationId = -1
        self._getConfiguration()

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
        self._playbackModulationId = self._midiModulation.connectModulation("PlayBackModulation")
        seqMode = self._configurationTree.getValue("SequenceMode")
        if(seqMode == "ReTrigger"):
            self._sequenceMode = ImageSequenceMode.ReTrigger
        elif(seqMode == "Modulation"):
            self._sequenceMode = ImageSequenceMode.Modulation
        else:
            self._sequenceMode = ImageSequenceMode.Time #Defaults to time

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
        fadeMode, fadeValue = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState)
        if((fadeMode == FadeMode.Black) and (fadeValue < 0.01)):
            self._image = None
            return

        lastFrame = self._currentFrame
        
        if(self._sequenceMode == ImageSequenceMode.Time):
            self._currentFrame = (int((currentSongPosition - self._startSongPosition) / self._syncLength) % self._numberOfFrames)
        elif(self._sequenceMode == ImageSequenceMode.ReTrigger):
            self._currentFrame =  (self._triggerCounter % self._numberOfFrames)
        elif(self._sequenceMode == ImageSequenceMode.Modulation):
            self._currentFrame = int(self.getPlaybackModulation(currentSongPosition, midiChannelState, midiNoteState) * (self._numberOfFrames - 1))

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
    def __init__(self, fileName, midiTimingClass, effectsConfiguration, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY):
        MediaFile.__init__(self, fileName, midiTimingClass, effectsConfiguration, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY)
        self._loopMode = VideoLoopMode.Normal
        self._configurationTree.addTextParameter("LoopMode", "Normal")
        self._getConfiguration()

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
        loopMode = self._configurationTree.getValue("LoopMode")
        if(loopMode == "Normal"):
            self._loopMode = VideoLoopMode.Normal
        elif(loopMode == "Reverse"):
            self._loopMode = VideoLoopMode.Reverse
        elif(loopMode == "PingPong"):
            self._loopMode = VideoLoopMode.PingPong
        elif(loopMode == "PingPongReverse"):
            self._loopMode = VideoLoopMode.PingPongReverse
        elif(loopMode == "DontLoop"):
            self._loopMode = VideoLoopMode.DontLoop
        elif(loopMode == "DontLoopReverse"):
            self._loopMode = VideoLoopMode.DontLoopReverse
        else:
            self._loopMode = VideoLoopMode.Normal #Defaults to normal

    def close(self):
        pass

    def getType(self):
        return "VideoLoop"

    def skipFrames(self, currentSongPosition, midiNoteState, midiChannelState):
        fadeMode, fadeValue = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState)
        if((fadeMode == FadeMode.Black) and (fadeValue < 0.01)):
            self._image = None
            return
        lastFrame = self._currentFrame

        framePos = int(((currentSongPosition - self._startSongPosition) / self._syncLength) * self._numberOfFrames)
        if(self._loopMode == VideoLoopMode.Normal):
            self._currentFrame = framePos % self._numberOfFrames
        elif(self._loopMode == VideoLoopMode.Reverse):
            self._currentFrame = -framePos % self._numberOfFrames
        elif(self._loopMode == VideoLoopMode.PingPong):
            self._currentFrame = abs(((framePos + self._numberOfFrames) % (2 * self._numberOfFrames)) - self._numberOfFrames)
        elif(self._loopMode == VideoLoopMode.PingPongReverse):
            self._currentFrame = abs((framePos % (2 * self._numberOfFrames)) - self._numberOfFrames)
        elif(self._loopMode == VideoLoopMode.DontLoop):
            if(framePos < self._numberOfFrames):
                self._currentFrame = framePos
            else:
                self._image = None
                return False
        elif(self._loopMode == VideoLoopMode.DontLoopReverse):
            if(framePos < self._numberOfFrames):
                self._currentFrame = self._numberOfFrames - 1 - framePos
            else:
                self._image = None
                return False
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