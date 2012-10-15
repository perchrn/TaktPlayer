'''
Created on 12. okt. 2011

@author: pcn
'''
import os.path
import logging
from cv2 import cv #@UnresolvedImport
import numpy
from midi.MidiModulation import MidiModulation
from video.Effects import createMat, getEffectByName, getEmptyImage, createMask,\
    copyImage, pilToCvImage, pilToCvMask
import hashlib
from video.media.MediaFileModes import MixMode, VideoLoopMode, ImageSequenceMode,\
    FadeMode, getMixModeFromName, ModulationValueMode,\
    getModulationValueModeFromName, KinectMode, TimeModulationMode
import math
from utilities.FloatListText import textToFloatValues
import PIL.Image as Image
from midi.MidiUtilities import noteStringToNoteNumber
from video.media.TextRendrer import generateTextImageAndMask, findOsFontPath
from midi.MidiStateHolder import NoteState, MidiControllerLatestModified,\
    MidiChannelStateHolder
try:
    import freenect
except:
    freenect = None

windowName = "TAKT Player"
def createCvWindow(fullScreenMode, sizeX, sizeY, posX=-1, posY=-1):
    if(fullScreenMode == "off"):
        cv.NamedWindow(windowName, cv.CV_WINDOW_NORMAL)
        cv.ResizeWindow(windowName, sizeX, sizeY)
        if(posX >= 0 and posY >=0):
            cv.MoveWindow(windowName, posX, posY)
    else:
        cv.NamedWindow(windowName, cv.CV_WINDOW_FULLSCREEN)

def addCvMouseCallback(callBack):
    cv.SetMouseCallback(windowName, callBack)

def showCvImage(image):
    cv.ShowImage(windowName, image)

def hasCvWindowStoped():
    k = cv.WaitKey(1);
    if k == 27: #Escape
        return "Escape"
    elif k == 3:
        return "Ctrl c"
    elif k == 17:
        return "Ctrl q"
    elif k == 24:
        return "Ctrl x"
    elif k == 113:
        return "q"
    elif k == 81:
        return "Q"
    else:
        if k != -1:
            print "DEBUG WaitKey: " + str(k)
    return None

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

def mixImageSelfMask(level, image1, image2, mixMask, mixMat1, whiteMode):
    cv.Copy(image2, mixMat1)
    cv.CvtColor(image2, mixMask, cv.CV_BGR2GRAY);
    if(whiteMode == True):
        cv.CmpS(mixMask, 250, mixMask, cv.CV_CMP_LT)
    else:
        cv.CmpS(mixMask, 5, mixMask, cv.CV_CMP_GT)
    return mixImageAlphaMask(level, image1, mixMat1, mixMask, image2)
    mixImageAlphaMask(level, mixMat1, image1, mixMask, image2)
    cv.Copy(mixMat1, image1, mixMask)
    return image1

def mixImageAlphaMask(level, image1, image2, image2mask, mixMat1):
    if(level < 0.99):
        valueCalc = int(256 * (1.0 - level))
        rgbColor = cv.CV_RGB(valueCalc, valueCalc, valueCalc)
        whiteColor = cv.CV_RGB(255, 255, 255)
        cv.Set(mixMat1, whiteColor)
        cv.Set(mixMat1, rgbColor, image2mask)
        cv.Mul(image1, mixMat1, image1, 0.004)
        valueCalc = int(256 * level)
        rgbColor = cv.CV_RGB(valueCalc, valueCalc, valueCalc)
        cv.Zero(mixMat1)
        cv.Set(mixMat1, rgbColor, image2mask)
        cv.Mul(image2, mixMat1, image2, 0.004)
        cv.Add(image1, image2, image1)
    else:
        cv.Copy(image2, image1, image2mask)
    return image1

def mixImagesAdd(level, image1, image2, mixMat):
    if(level < 0.99):
        cv.ConvertScaleAbs(image2, image2, level, 0.0)
        cv.Add(image1, image2, mixMat)
    else:
        cv.Add(image1, image2, mixMat)
    return mixMat

def mixImagesReplace(level, image1, image2, mixMat):
    if(level < 0.99):
        if(image1 != None):
            cv.ConvertScaleAbs(image2, image2, level, 0.0)
            cv.ConvertScaleAbs(image1, image1, 1.0 - level, 0.0)
            cv.Add(image1, image2, mixMat)
        else:
            cv.ConvertScaleAbs(image2, mixMat, level, 0.0)
    else:
        return image2
    return mixMat

def mixImagesMultiply(level, image1, image2, mixMat):
    cv.Mul(image1, image2, mixMat, 0.004)
    if(level < 0.99):
        cv.ConvertScaleAbs(image1, image1, 1.0 - level, 0.0)
        cv.ConvertScaleAbs(mixMat, mixMat, level, 0.0)
        cv.Add(mixMat, image1, mixMat)
    return mixMat

def mixImages(mode, level, image1, image2, image2mask, mixMat1, mixMask):
    if(level < 0.01):
        return image1
    if(mode == MixMode.Multiply):
        return mixImagesMultiply(level, image1, image2, mixMat1)
    elif(mode == MixMode.LumaKey):
        return mixImageSelfMask(level, image1, image2, mixMask, mixMat1, False)
    elif(mode == MixMode.WhiteLumaKey):
        return mixImageSelfMask(level, image1, image2, mixMask, mixMat1, True)
    elif(mode == MixMode.AlphaMask):
        if(image2mask != None):
            return mixImageAlphaMask(level, image1, image2, image2mask, mixMat1)
        #Will fall back to Add mode if there is no mask.
    elif(mode == MixMode.Replace):
        return mixImagesReplace(level, image1, image2, mixMat1)
    #Default is Add!
    return mixImagesAdd(level, image1, image2, mixMat1)

def imageToArray(image):
    return numpy.asarray(image)

def imageFromArray(array):
    return cv.fromarray(array)

class MediaFile(object):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        self._configurationTree = configurationTree
        self._effectsConfigurationTemplates = effectsConfiguration
        self._specialModulationHolder = specialModulationHolder
        self._timeModulationConfigurationTemplates = timeModulationConfiguration
        self._effectImagesConfigurationTemplates = effectImagesConfig
        self._guiCtrlStateHolder = guiCtrlStateHolder
        self._mediaFadeConfigurationTemplates = fadeConfiguration
        self._videoDirectory = videoDir
        self.setFileName(fileName)
        self._midiTiming = midiTimingClass
        self._internalResolutionX =  internalResolutionX
        self._internalResolutionY =  internalResolutionY

        self._firstImage = None
        self._firstImageMask = None
        self._secondImage = None
        self._bufferedImageList = None
        self._numberOfFrames = 0
        self._originalFrameRate = 25
        self._originalTime = 0.0
        self._loopModulationMode = TimeModulationMode.Off
        self._fileOk = False

        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._log.setLevel(logging.WARNING)

        self._configurationTree.addTextParameterStatic("Type", self.getType())
        self._configurationTree.addTextParameterStatic("FileName", self._cfgFileName)
        self._midiModulation = None
        self._setupConfiguration()

        self._mediaSettingsHolder = MediaSettings(0)
        self._setupMediaSettingsHolder(self._mediaSettingsHolder)

    def _setupMediaSettingsHolder(self, mediaSettingsHolder):
        mediaSettingsHolder.resizeMat = createMat(self._internalResolutionX, self._internalResolutionY)
        mediaSettingsHolder.fadeMat = createMat(self._internalResolutionX, self._internalResolutionY)
        mediaSettingsHolder.image = None
        mediaSettingsHolder.imageMask = None
        mediaSettingsHolder.captureImage = None
        mediaSettingsHolder.captureMask = None
        mediaSettingsHolder.currentFrame = 0;
        mediaSettingsHolder.startSongPosition = 0.0

        mediaSettingsHolder.lastFramePos = 0.0
        mediaSettingsHolder.lastFramePosSongPosition = 0.0
        mediaSettingsHolder.isLastFrameSpeedModified = False

        #Time Modulation etc.
        mediaSettingsHolder.noteTriggerCounter = 0
        mediaSettingsHolder.lastTriggerCount = 0
        mediaSettingsHolder.firstNoteTrigger = True
        mediaSettingsHolder.triggerModificationSum = 0.0
        mediaSettingsHolder.triggerSongPosition = 0.0
        mediaSettingsHolder.loopEndSongPosition = -1.0

        if(self.getType() != "Modulation"):
            mediaSettingsHolder.effect1 = None
            mediaSettingsHolder.effect2 = None

    def _updateMediaSettingsHolder(self, mediaSettingsHolder):
        if(self.getType() != "Modulation"):
            mediaSettingsHolder.effect1 = getEffectByName(self._effect1Settings.getEffectName(), self._effect1TemplateName, self._configurationTree, self._effectImagesConfigurationTemplates, self._specialModulationHolder, self._internalResolutionX, self._internalResolutionY)
            mediaSettingsHolder.effect2 = getEffectByName(self._effect2Settings.getEffectName(), self._effect2TemplateName, self._configurationTree, self._effectImagesConfigurationTemplates, self._specialModulationHolder, self._internalResolutionX, self._internalResolutionY)

    def _setupConfiguration(self):
        self._configurationTree.addFloatParameter("SyncLength", 4.0) #Default one bar (re calculated on load)
        self._configurationTree.addFloatParameter("QuantizeLength", 1.0)#Default one beat
        if(self.getType() != "Modulation"):
            self._configurationTree.addTextParameter("MixMode", "Add")#Default Add
            self._defaultTimeModulationSettingsName = "Default"
            self._configurationTree.addTextParameter("TimeModulationConfig", self._defaultTimeModulationSettingsName)#Default Default
            self._defaultEffect1SettingsName = "MediaDefault1"
            self._configurationTree.addTextParameter("Effect1Config", self._defaultEffect1SettingsName)#Default MediaDefault1
            self._defaultEffect2SettingsName = "MediaDefault2"
            self._configurationTree.addTextParameter("Effect2Config", self._defaultEffect2SettingsName)#Default MediaDefault2
            self._defaultFadeSettingsName = "Default"
            self._configurationTree.addTextParameter("FadeConfig", self._defaultFadeSettingsName)#Default Default
        self._configurationTree.addTextParameter("ModulationValuesMode", "KeepOld")#Default KeepOld
        
        self._syncLength = -1.0
        self._quantizeLength = -1.0
        self._mixMode = MixMode.Add

        self._modulationRestartMode = ModulationValueMode.KeepOld
        self._effect1StartControllerValues = (None, None, None, None, None)
        self._effect2StartControllerValues = (None, None, None, None, None)
        self._effect1StartValues = (0.0, 0.0, 0.0, 0.0, 0.0)
        self._effect2StartValues = (0.0, 0.0, 0.0, 0.0, 0.0)
        self._effect1OldValues = (0.0, 0.0, 0.0, 0.0, 0.0)
        self._effect2OldValues = (0.0, 0.0, 0.0, 0.0, 0.0)
        self._effect1Settings = None
        self._effect2Settings = None
        self._timeModulationSettings = None

    def _getConfiguration(self):
        if(self.getType() != "Modulation"):
            timeModulationTemplateName = self._configurationTree.getValue("TimeModulationConfig")
            self._timeModulationSettings = self._timeModulationConfigurationTemplates.getTemplate(timeModulationTemplateName)
            if(self._timeModulationSettings == None):
                self._timeModulationSettings = self._timeModulationConfigurationTemplates.getTemplate(self._defaultTimeModulationSettingsName)
        
            oldEffect1Name = "None"
            oldEffect1Values = "0.0|0.0|0.0|0.0|0.0"
            if(self._effect1Settings != None):
                oldEffect1Name = self._effect1Settings.getEffectName()
                oldEffect1Values = self._effect1Settings.getStartValuesString()
            self._effect1TemplateName = self._configurationTree.getValue("Effect1Config")
            self._effect1Settings = self._effectsConfigurationTemplates.getTemplate(self._effect1TemplateName)
            if(self._effect1Settings == None):
                self._effect1Settings = self._effectsConfigurationTemplates.getTemplate(self._defaultEffect1SettingsName)
            if((oldEffect1Name != self._effect1Settings.getEffectName()) or (oldEffect1Values != self._effect1Settings.getStartValuesString())):
                self._effect1StartValues = self._effect1Settings.getStartValues()
                self._effect1OldValues = self._effect1StartValues

            oldEffect2Name = "None"
            oldEffect2Values = "0.0|0.0|0.0|0.0|0.0"
            if(self._effect2Settings != None):
                oldEffect2Name = self._effect2Settings.getEffectName()
                oldEffect2Values = self._effect2Settings.getStartValuesString()
            self._effect2TemplateName = self._configurationTree.getValue("Effect2Config")
            self._effect2Settings = self._effectsConfigurationTemplates.getTemplate(self._effect2TemplateName)
            if(self._effect2Settings == None):
                self._effect2Settings = self._effectsConfigurationTemplates.getTemplate(self._defaultEffect2SettingsName)
            if((oldEffect2Name != self._effect2Settings.getEffectName()) or (oldEffect2Values != self._effect2Settings.getStartValuesString())):
                self._effect2StartValues = self._effect2Settings.getStartValues()
                self._effect2OldValues = self._effect2StartValues

            self._fadeAndLevelTemplate = self._configurationTree.getValue("FadeConfig")
            self._fadeAndLevelSettings = self._mediaFadeConfigurationTemplates.getTemplate(self._fadeAndLevelTemplate)
            if(self._fadeAndLevelSettings == None):
                self._fadeAndLevelSettings = self._mediaFadeConfigurationTemplates.getTemplate(self._defaultFadeSettingsName)

            mixMode = self._configurationTree.getValue("MixMode")
            self._mixMode = getMixModeFromName(mixMode)

        self.setMidiLengthInBeats(self._configurationTree.getValue("SyncLength"))
        self.setQuantizeInBeats(self._configurationTree.getValue("QuantizeLength"))

        modulationRestartMode = self._configurationTree.getValue("ModulationValuesMode")
        self._modulationRestartMode = getModulationValueModeFromName(modulationRestartMode)

        for mediaSettingsHolder in self._mediaSettingsHolder.getSettingsList():
            self._updateMediaSettingsHolder(mediaSettingsHolder)

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print "mediaFile config is updated..."
            self._getConfiguration()
            if(self._midiModulation != None):
                self._midiModulation.checkAndUpdateFromConfiguration()
            self._configurationTree.resetConfigurationUpdated()

    def getMediaStateHolder(self):
        mediaSettingsHolder = self._mediaSettingsHolder.getSettings()
        if(mediaSettingsHolder.isNew() == True):
            self._setupMediaSettingsHolder(mediaSettingsHolder)
            mediaSettingsHolder.captureImage = self._firstImage
            mediaSettingsHolder.captureMask = self._firstImageMask
            self._updateMediaSettingsHolder(mediaSettingsHolder)
        return mediaSettingsHolder

    def close(self):
        pass

    def getType(self):
        return "Unknown"

    def equalFileName(self, fileName):
        return self._cfgFileName.encode("utf-8") == fileName.encode("utf-8")

    def getFileName(self):
        return self._cfgFileName

    def setFileName(self, fileName):
        self._cfgFileName = fileName
        self._fullFilePath = os.path.join(os.path.normpath(self._videoDirectory), os.path.normpath(self._cfgFileName))
        self._packageFilePath = os.path.join(os.getcwd(), "testFiles", os.path.normpath(self._cfgFileName))

    def isFileOk(self):
        return self._fileOk
    
    def getImage(self, mediaSettingsHolder):
        return mediaSettingsHolder.image

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

    def setStartPosition(self, startSpp, mediaSettingsHolder, songPosition, midiNoteStateHolder, midiChannelStateHolder):
        if((self._loopModulationMode == TimeModulationMode.TriggeredJump) or (self._loopModulationMode == TimeModulationMode.TriggeredLoop)):
            lastSpp = mediaSettingsHolder.triggerSongPosition
            if(startSpp != lastSpp):
                if(mediaSettingsHolder.firstNoteTrigger == True):
                    mediaSettingsHolder.firstNoteTrigger = False
                    mediaSettingsHolder.startSongPosition = startSpp
                    self._resetEffects(mediaSettingsHolder, songPosition, midiNoteStateHolder, midiChannelStateHolder)
                    mediaSettingsHolder.triggerSongPosition = startSpp
                else:
                    mediaSettingsHolder.noteTriggerCounter += 1
                    mediaSettingsHolder.triggerSongPosition = startSpp
#                print "TriggerCount: " + str(self._noteTriggerCounter) + " startSPP: " + str(startSpp) + " lastSPP: " + str(lastSpp)
        else:
            if(startSpp != mediaSettingsHolder.startSongPosition):
                mediaSettingsHolder.startSongPosition = startSpp
                self._resetEffects(mediaSettingsHolder, songPosition, midiNoteStateHolder, midiChannelStateHolder)

    def releaseMedia(self, mediaSettingsHolder):
        mediaSettingsHolder.noteTriggerCounter = 0
        mediaSettingsHolder.lastTriggerCount = 0
        mediaSettingsHolder.firstNoteTrigger = True
        mediaSettingsHolder.triggerModificationSum = 0.0
        mediaSettingsHolder.triggerSongPosition = 0.0
        mediaSettingsHolder.release()

#    def getCurrentFramePos(self):
#        return self._currentFrame

    def _resetEffects(self, mediaSettingsHolder, songPosition, midiNoteStateHolder, midiChannelStateHolder):
        self._guiCtrlStateHolder.resetState()
        if(self._modulationRestartMode != ModulationValueMode.RawInput):
            self._effect1StartControllerValues = self._effect1Settings.getValues(songPosition, midiChannelStateHolder, midiNoteStateHolder, self._specialModulationHolder)
            self._effect2StartControllerValues = self._effect2Settings.getValues(songPosition, midiChannelStateHolder, midiNoteStateHolder, self._specialModulationHolder)
        else:
            self._effect1StartControllerValues = (None, None, None, None, None)
            self._effect2StartControllerValues = (None, None, None, None, None)
        if(self._modulationRestartMode == ModulationValueMode.ResetToDefault):
            self._effect1StartValues = self._effect1Settings.getStartValues()
            self._effect2StartValues = self._effect2Settings.getStartValues()
        else: #KeepOldValues
            self._effect1StartValues = self._effect1OldValues
            self._effect2StartValues = self._effect2OldValues

        if(mediaSettingsHolder.effect1 != None):
            mediaSettingsHolder.effect1.reset()
        if(mediaSettingsHolder.effect2 != None):
            mediaSettingsHolder.effect2.reset()

    def _getFadeValue(self, currentSongPosition, midiNoteState, midiChannelState):
        noteDone = False
        fadeMode, fadeValue, levelValue = self._fadeAndLevelSettings.getValues(currentSongPosition, midiChannelState, midiNoteState)
        if(fadeValue > 0.999999):
            noteDone = True
        fadeValue = (1.0 - fadeValue) * (1.0 - levelValue)
        return fadeMode, fadeValue, noteDone

    def getEffectState(self):
        guiEffectValuesString = str(self._guiCtrlStateHolder.getGuiContollerState(0)) + ";"
        valuesString = str(self._effect1OldValues) + ";"
        guiEffectValuesString += str(self._guiCtrlStateHolder.getGuiContollerState(5))
        valuesString += str(self._effect2OldValues)
        return (valuesString, guiEffectValuesString)

    def _applyOneEffect(self, image, effect, effectSettings, effectStartControllerValues, effectStartValues, songPosition, midiChannelStateHolder, midiNoteStateHolder, guiCtrlStateHolder, guiCtrlStateStartId):
        if(effectSettings != None):
            midiEffectVaules = effectSettings.getValues(songPosition, midiChannelStateHolder, midiNoteStateHolder, self._specialModulationHolder)
            effectAmount, effectArg1, effectArg2, effectArg3, effectArg4 = guiCtrlStateHolder.updateWithGuiSettings(guiCtrlStateStartId, midiEffectVaules, effectStartValues)
            #print "DEBUG controller values" + str((effectAmount, effectArg1, effectArg2, effectArg3, effectArg4)) + " start" + str(effectStartControllerValues) + " sVals" + str(effectStartValues)
            #TODO: Add mode where values must pass start values?
            effectSCV0 = None
            if(effectAmount == effectStartControllerValues[0]):
                if(effectAmount != effectStartValues[0]):
                    effectAmount = effectStartValues[0]
                    effectSCV0 = effectStartControllerValues[0]
            effectSCV1 = None
            if(effectArg1 == effectStartControllerValues[1]):
                if(effectArg1 != effectStartValues[1]):
                    effectArg1 = effectStartValues[1]
                    effectSCV1 = effectStartControllerValues[1]
            effectSCV2 = None
            if(effectArg2 == effectStartControllerValues[2]):
                if(effectArg2 != effectStartValues[2]):
                    effectArg2 = effectStartValues[2]
                    effectSCV2 = effectStartControllerValues[2]
            effectSCV3 = None
            if(effectArg3 == effectStartControllerValues[3]):
                if(effectArg3 != effectStartValues[3]):
                    effectArg3 = effectStartValues[3]
                    effectSCV3 = effectStartControllerValues[3]
            effectSCV4 = None
            if(effectArg4 == effectStartControllerValues[4]):
                if(effectArg4 != effectStartValues[4]):
                    effectArg4 = effectStartValues[4]
                    effectSCV4 = effectStartControllerValues[4]
            if(effect != None):
                image = effect.applyEffect(image, effectAmount, effectArg1, effectArg2, effectArg3, effectArg4)
#            print "DEBUG modified values" + str((effectAmount, effectArg1, effectArg2, effectArg3, effectArg4))
            return (image, (effectAmount, effectArg1, effectArg2, effectArg3, effectArg4), (effectSCV0, effectSCV1, effectSCV2, effectSCV3, effectSCV4))
        else:
            return (image, (0.0, 0.0, 0.0, 0.0, 0.0), (None, None, None, None, None))

    def _applyEffects(self, mediaSettingsHolder, currentSongPosition, midiChannelState, midiNoteState, fadeMode, fadeValue):
        imageSize = cv.GetSize(mediaSettingsHolder.captureImage)
        if((imageSize[0] != self._internalResolutionX) or (imageSize[1] != self._internalResolutionY)):
            mediaSettingsHolder.image = resizeImage(mediaSettingsHolder.captureImage, mediaSettingsHolder.resizeMat)
        else:
            mediaSettingsHolder.image = copyImage(mediaSettingsHolder.captureImage)

        (mediaSettingsHolder.image, self._effect1OldValues, self._effect1StartControllerValues) = self._applyOneEffect(mediaSettingsHolder.image, mediaSettingsHolder.effect1, self._effect1Settings, self._effect1StartControllerValues, self._effect1StartValues, currentSongPosition, midiChannelState, midiNoteState, self._guiCtrlStateHolder, 0)
        (mediaSettingsHolder.image, self._effect2OldValues, self._effect2StartControllerValues) = self._applyOneEffect(mediaSettingsHolder.image, mediaSettingsHolder.effect2, self._effect2Settings, self._effect2StartControllerValues, self._effect2StartValues, currentSongPosition, midiChannelState, midiNoteState, self._guiCtrlStateHolder, 5)

        if(fadeValue < 0.99):
            mediaSettingsHolder.image = fadeImage(mediaSettingsHolder.image, fadeValue, fadeMode, mediaSettingsHolder.fadeMat)

    def _timeModulatePos(self, unmodifiedFramePos, currentSongPosition, mediaSettingsHolder, midiNoteState, midiChannelState, syncLength):
        self._loopModulationMode, modulation, speedRange, speedQuantize = self._timeModulationSettings.getValues(currentSongPosition, midiChannelState, midiNoteState)

        guiStates = self._guiCtrlStateHolder.getGuiContollerState(10)
        if(guiStates[4] != None):
            if(guiStates[4] > -0.5):
                modulation = guiStates[4]

        if(syncLength != None):
            jumpQuantize = speedQuantize * self._midiTiming.getTicksPerQuarteNote()
            jumpRange = ((speedRange * self._midiTiming.getTicksPerQuarteNote()) / syncLength) * self._numberOfFrames
            jumpSppStep = speedRange * self._midiTiming.getTicksPerQuarteNote()

#        timeMod = TimeModulationMode() #DEBUG
#        print "DEBUG _timeModulateFramePos: val: " + str(modulation) + " mode: " + timeMod.getNames(self._loopModulationMode) + " speedRange: " + str(speedRange) + " speedQuantize: " + str(speedQuantize) + " jump (r,q,step): " + str((jumpRange, jumpQuantize, jumpSppStep))

        if(self._loopModulationMode == TimeModulationMode.SpeedModulation):
            speedMod = (2.0 * modulation) - 1.0
            if(speedRange < 0.0):
                #Invert
                speedRange = -speedRange
                speedMod = -speedMod
            if(mediaSettingsHolder.startSongPosition > mediaSettingsHolder.lastFramePosSongPosition):
                mediaSettingsHolder.lastFramePosSongPosition = mediaSettingsHolder.startSongPosition
            if(speedQuantize > 0.02):
                steps = int(speedRange / speedQuantize)
                if(steps < 1):
                    steps = 1
                currentStep = int((steps + 0.5) * speedMod)
                speedMod = float(currentStep) / steps
#                print "DEBUG steps: " + str(steps) + " currentStep: " + str(currentStep)
            if((speedMod < -0.01) or (speedMod > 0.01)):
                twoTimesPosition = 2.0 / speedRange
                absSpeedMod = abs(speedMod)
                if(absSpeedMod > twoTimesPosition):
                    speedMultiplyer = 2.0 * (absSpeedMod / twoTimesPosition)
                else:
                    speedMultiplyer = 1.0 + (absSpeedMod / twoTimesPosition)
                if(speedMod < 0):
                    speedMultiplyer = 1.0 / speedMultiplyer
#                print "DEBUG speedMod: " + str(speedMod) + " -> " + str(speedMultiplyer)
                if(syncLength == None):
                    return speedMultiplyer
                framePosFloat = mediaSettingsHolder.lastFramePos + ((self._numberOfFrames * speedMultiplyer) / syncLength)
                mediaSettingsHolder.isLastFrameSpeedModified = True
            else:
                if(syncLength == None):
                    return 1.0
                if(mediaSettingsHolder.isLastFrameSpeedModified == True):
                    framesDiff = ((unmodifiedFramePos % (2 * self._numberOfFrames)) - (mediaSettingsHolder.lastFramePos % (2 * self._numberOfFrames))) % (2 * self._numberOfFrames)
                    framesSpeed = float(self._numberOfFrames) / syncLength
                    if(framesDiff > (2.0 * framesSpeed)):
                        if(framesDiff < self._numberOfFrames):
                            framePosFloat = mediaSettingsHolder.lastFramePos + 2.0 * framesSpeed
                        else:
                            framePosFloat = mediaSettingsHolder.lastFramePos + 0.25 * framesSpeed                    
    #                    print "DEBUG diff: " + str(framesDiff) + " speed: " + str(framesSpeed) + " maxframe x 2: " + str(2* self._numberOfFrames)
                    else:
                        framePosFloat = unmodifiedFramePos
                        mediaSettingsHolder.isLastFrameSpeedModified = False
                else:
                    framePosFloat = unmodifiedFramePos
            mediaSettingsHolder.lastFramePos = framePosFloat
            mediaSettingsHolder.lastFramePosSongPosition = currentSongPosition
        elif(self._loopModulationMode == TimeModulationMode.TriggeredJump):
            if(mediaSettingsHolder.noteTriggerCounter != mediaSettingsHolder.lastTriggerCount):
                speedMod = (2.0 * modulation) - 1.0
                if(jumpRange < 0.0):
                    #Invert
                    jumpRange = -jumpRange
                    speedMod = -speedMod
                if(jumpQuantize > 0.02):
                    steps = int(jumpRange / jumpQuantize)
                    if(steps < 1):
                        steps = 1
                    currentStep = int((steps + 0.5) * speedMod)
                    speedMod = float(currentStep) / steps
                if((speedMod < -0.01) or (speedMod > 0.01)):
                    jumpLength = jumpRange * speedMod
                    mediaSettingsHolder.triggerModificationSum += jumpLength
#                    print "Adding " + str(jumpLength) + " sum: " + str(mediaSettingsHolder.triggerModificationSum)
#                else:
#                    print "SpeedMod == 0.0 :-(  ->  No jump!"
                mediaSettingsHolder.lastTriggerCount = mediaSettingsHolder.noteTriggerCounter
            framePosFloat = unmodifiedFramePos + mediaSettingsHolder.triggerModificationSum
        elif(self._loopModulationMode == TimeModulationMode.TriggeredLoop):
            trigger = mediaSettingsHolder.noteTriggerCounter != mediaSettingsHolder.lastTriggerCount
            if((trigger == True) and (mediaSettingsHolder.loopEndSongPosition < 0.0)):
                mediaSettingsHolder.loopEndSongPosition = currentSongPosition
            if(currentSongPosition >= mediaSettingsHolder.loopEndSongPosition):
                loopLength = modulation
                if(trigger == True):
                    if(jumpQuantize > 0.02):
                        steps = int(jumpRange / jumpQuantize)
                        if(steps < 1):
                            steps = 1
                        currentStep = int((steps + 0.5) * loopLength)
                        loopLength = float(currentStep) / steps
                    if(loopLength > 0.01):
                        jumpLength = jumpRange * loopLength
                        mediaSettingsHolder.triggerModificationSum += jumpLength
                        mediaSettingsHolder.loopEndSongPosition += loopLength * jumpSppStep
#                        print "Subtracting " + str(jumpLength) + " sum: " + str(mediaSettingsHolder.triggerModificationSum) + " unmod: " + str(unmodifiedFramePos) + " loopEnd: " + str(mediaSettingsHolder.loopEndSongPosition) + " calc: " + str(currentSongPosition - mediaSettingsHolder.triggerModificationSum) + " calc2: " + str(unmodifiedFramePos - mediaSettingsHolder.triggerModificationSum)
                    else:
#                        print "loopLength == 0.0 ->  Freeze frame!"
                        jumpLength = ((currentSongPosition - mediaSettingsHolder.loopEndSongPosition) / syncLength) * self._numberOfFrames
                        mediaSettingsHolder.triggerModificationSum += jumpLength
                        mediaSettingsHolder.loopEndSongPosition = currentSongPosition
                else:
                    mediaSettingsHolder.loopEndSongPosition = -1.0
            framePosFloat = unmodifiedFramePos - mediaSettingsHolder.triggerModificationSum
        else:
            framePosFloat = unmodifiedFramePos
        return framePosFloat

    def skipFrames(self, mediaStateHolder, currentSongPosition, midiNoteState, midiChannelState):
        pass

    def openVideoFile(self, midiLength):
        filePath = self._fullFilePath
        if(os.path.isfile(filePath) == False):
            filePath = self._packageFilePath
        if (os.path.isfile(filePath) == False):
            self._log.warning("Could not find file: %s in directory: %s", self._cfgFileName, self._videoDirectory)
            print "Could not find file: %s in directory: %s" % (self._cfgFileName, self._videoDirectory)
            raise MediaError("File does not exist!")
        self._videoFile = cv.CaptureFromFile(filePath.encode("utf-8"))
        try:
            self._mediaSettingsHolder.captureImage = cv.QueryFrame(self._videoFile)
            self._firstImage = copyImage(self._mediaSettingsHolder.captureImage)
            self._mediaSettingsHolder.captureImage = cv.QueryFrame(self._videoFile)
            self._secondImage = copyImage(self._mediaSettingsHolder.captureImage)
            self._mediaSettingsHolder.captureImage = self._firstImage
        except:
            self._log.warning("Exception while reading: %s", os.path.basename(self._cfgFileName))
            print "Exception while reading: " + os.path.basename(self._cfgFileName)
            raise MediaError("File caused exception!")
        if (self._mediaSettingsHolder.captureImage == None):
            self._log.warning("Could not read frames from: %s", os.path.basename(self._cfgFileName))
            print "Could not read frames from: " + os.path.basename(self._cfgFileName)
            raise MediaError("File could not be read!")
        try:
            self._numberOfFrames = int(cv.GetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_FRAME_COUNT))
            self._originalFrameRate = int(cv.GetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_FPS))
        except:
            self._log.warning("Exception while getting number of frames from: %s", os.path.basename(self._cfgFileName))
            raise MediaError("File caused exception!")
        if(self._numberOfFrames < 20):
            try:
                self._bufferedImageList = []
                self._bufferedImageList.append(self._firstImage)
                self._bufferedImageList.append(self._secondImage)
                for i in range(self._numberOfFrames - 2): #@UnusedVariable
                    self._mediaSettingsHolder.captureImage = cv.QueryFrame(self._videoFile)
                    self._bufferedImageList.append(copyImage(self._mediaSettingsHolder.captureImage))
                self._mediaSettingsHolder.captureImage = self._firstImage
            except:
                self._log.warning("Exception while reading: %s", os.path.basename(self._cfgFileName))
                print "Exception while reading: " + os.path.basename(self._cfgFileName)
                raise MediaError("File caused exception!")
        self._originalTime = float(self._numberOfFrames) / self._originalFrameRate
        if(midiLength != None): # Else we get length from configuration or default.
            if(midiLength <= 0.0):
                midiLength = self._midiTiming.guessMidiLength(self._originalTime)
            self.setMidiLengthInBeats(midiLength)
        self._log.warning("Read file %s with %d frames, framerate %d and length %f guessed MIDI length %f", os.path.basename(self._cfgFileName), self._numberOfFrames, self._originalFrameRate, self._originalTime, self._syncLength)
        self._fileOk = True

    def getThumbnailId(self, videoPosition, forceUpdate):
        image = self._firstImage # Default
        ourType = self.getType()
        if((ourType == "Group") or (ourType == "Camera") or (ourType == "KinectCamera")):
            image = self._mediaSettingsHolder.captureImage
        else:
            if(videoPosition >= 0.00):
                if(((ourType == "VideoLoop") or (ourType == "ImageSequence")) and (videoPosition > 0.12)):
                    if(videoPosition < 0.28):
                        videoPosition = 0.25
                    elif(videoPosition < 0.41):
                        videoPosition = 0.33
                    elif(videoPosition < 0.66):
                        videoPosition = 0.50
                    elif(videoPosition < 0.87):
                        videoPosition = 0.75
                    else:
                        videoPosition = 1.00
                    cv.SetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_POS_AVI_RATIO, videoPosition)
                    image = cv.QueryFrame(self._videoFile)
            else:
                #Get current image...
                image = self._mediaSettingsHolder.captureImage

        filenameHash = hashlib.sha224(self.getFileName().encode("utf-8")).hexdigest()
        if(os.path.exists("thumbs") == False):
            os.makedirs("thumbs")
        if(os.path.isdir("thumbs") == False):
            print "Error!!! thumbs directory is not in: " + os.getcwd()
            return None
        else:
            thumbnailName = "thumbs/%s.jpg" % (filenameHash)
            osFileName = os.path.normpath(thumbnailName)
            if((forceUpdate == True) or (os.path.isfile(osFileName) == False)):
                print "Thumb file does not exist. Generating... " + thumbnailName
                destWidth, destHeight = (40, 30)
                resizeMat = createMat(destWidth, destHeight)
                if(image == None):
                    print "Error! thumbnail image == None for " + self.getType() + "!"
                else:
                    scaleAndSave(image, osFileName, resizeMat)
            else:
                print "Thumb file already exist. " + thumbnailName
            return thumbnailName

    def openFile(self, midiLength):
        pass

    def doPostConfigurations(self):
        if(self._fileOk):
            self._getConfiguration() #Make sure we can connect to any loaded ModulationMedia

    def mixWithImage(self, image, mixMode, mixLevel, effects, mediaStateHolder, currentSongPosition, midiChannelState, guiCtrlStateHolder, midiNoteState, mixMat1, mixMask):
        if(mediaStateHolder.image == None):
            return (image, None, None)
        else:
            if(mixMode == MixMode.Default):
                mixMode = self._mixMode
            if(effects != None):
                preFx, preFxSettings, preFxCtrlVal, preFxStartVal, postFx, postFxSettings, postFxCtrlVal, postFxStartVal = effects
            else:
                preFx, preFxSettings, preFxCtrlVal, preFxStartVal, postFx, postFxSettings, postFxCtrlVal, postFxStartVal = (None, None, (None, None, None, None, None), None, None, None, (None, None, None, None, None), None)
            (mediaStateHolder.image, currentPreValues, unusedStarts) = self._applyOneEffect(mediaStateHolder.image, preFx, preFxSettings, preFxCtrlVal, preFxStartVal, currentSongPosition, midiChannelState, midiNoteState, guiCtrlStateHolder, 0) #@UnusedVariable
            mixedImage =  mixImages(mixMode, mixLevel, image, mediaStateHolder.image, mediaStateHolder.imageMask, mixMat1, mixMask)
            (mixedImage, currentPostValues, unusedStarts) = self._applyOneEffect(mixedImage, postFx, postFxSettings, postFxCtrlVal, postFxStartVal, currentSongPosition, midiChannelState, midiNoteState, guiCtrlStateHolder, 5) #@UnusedVariable
            return (mixedImage, currentPreValues, currentPostValues)

class MediaSettings(object):
    def __init__(self, uid):
        self._subSettings = None
        self._inUse = False
        self._isNew = True
        self._uid = uid

    def isNew(self):
        if(self._isNew == True):
            self._isNew = False
            return True
        return False

    def getSettings(self):
        if(self._inUse == False):
            self._inUse = True
            return self
        if(self._subSettings == None):
            self._subSettings = MediaSettings(self._uid+1)
        return self._subSettings.getSettings()

    def release(self):
        self._inUse = False

    def getSettingsList(self, settingsList = None):
        if(settingsList == None):
            settingsList = []
        settingsList.append(self)
        if(self._subSettings == None):
            return settingsList
        else:
            return self._subSettings.getSettingsList(settingsList)

class MediaGroup(MediaFile):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
        self._mediaList = []
        self._mediaSettingsList = []
        self._getMediaCallback = None
        self._noteList = fileName.split(",")
        self._groupName = fileName

        self._blankImage = getEmptyImage(self._internalResolutionX, self._internalResolutionY)

        self._mixMat1 = createMat(self._internalResolutionX, self._internalResolutionY)
        self._mixMat2 = createMat(self._internalResolutionX, self._internalResolutionY)
        self._mixMask = createMask(self._internalResolutionX, self._internalResolutionY)

        self._getConfiguration()

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
        self._timeMultiplyer = self._configurationTree.getValue("SyncLength")

    def getType(self):
        return "Group"

    def close(self):
        pass

    def setStartPosition(self, startSpp, mediaSettingsHolder, songPosition, midiNoteStateHolder, midiChannelStateHolder):
        if(startSpp != mediaSettingsHolder.startSongPosition):
            mediaSettingsHolder.startSongPosition = startSpp
            self._resetEffects(mediaSettingsHolder, songPosition, midiNoteStateHolder, midiChannelStateHolder)
            for i in range(len(self._mediaList)):
                media = self._mediaList[i]
                mediaSettings = mediaSettingsHolder.mediaSettingsList[i]
                media.setStartPosition(startSpp, mediaSettings, songPosition, midiNoteStateHolder, midiChannelStateHolder)

    def releaseMedia(self, mediaSettingsHolder):
        for i in range(len(self._mediaList)):
            media = self._mediaList[i]
            mediaSettings = mediaSettingsHolder.mediaSettingsList[i]
            media.releaseMedia(mediaSettings)

    def skipFrames(self, mediaSettingsHolder, currentSongPosition, midiNoteState, midiChannelState, timeMultiplyer = None):
        if(timeMultiplyer == None):
            timeMultiplyer = self._timeMultiplyer
        loopModulationMode, _, _, _ = self._timeModulationSettings.getValues(currentSongPosition, midiChannelState, midiNoteState)
        if(loopModulationMode == TimeModulationMode.SpeedModulation):
            modifiedMultiplyer = self._timeModulatePos(timeMultiplyer, currentSongPosition, mediaSettingsHolder, midiNoteState, midiChannelState, None)
            timeMultiplyer = modifiedMultiplyer * timeMultiplyer

        fadeMode, fadeValue, noteDone = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState)
        if((fadeMode == FadeMode.Black) and (fadeValue < 0.00001)):
            mediaSettingsHolder.image = None
            return noteDone

        for i in range(len(self._mediaList)):
            media = self._mediaList[i]
            mediaSettings = mediaSettingsHolder.mediaSettingsList[i]
            media.skipFrames(mediaSettings, currentSongPosition, midiNoteState, midiChannelState, timeMultiplyer)

        imageMix = None
        for i in range(len(self._mediaList)):
            media = self._mediaList[i]
            mediaSettings = mediaSettingsHolder.mediaSettingsList[i]
            mixLevel = 1.0
            mixEffects = None
            guiCtrlStateHolder = None
            if(imageMix == None):
                imageTest = media.getImage()
                if(imageTest != None):
                    mixMode = MixMode.Replace
                    if(imageMix == self._mixMat1):
                        imageMix, _, _ = media.mixWithImage(imageMix, mixMode, mixLevel, mixEffects, mediaSettings, currentSongPosition, midiChannelState, guiCtrlStateHolder, midiNoteState, self._mixMat1, self._mixMask)
                    else:
                        imageMix, _, _ = media.mixWithImage(imageMix, mixMode, mixLevel, mixEffects, mediaSettings, currentSongPosition, midiChannelState, guiCtrlStateHolder, midiNoteState, self._mixMat2, self._mixMask)
            else:
                mixMode = MixMode.Default
                if(imageMix == self._mixMat1):
                    imageMix, _, _ = media.mixWithImage(imageMix, mixMode, mixLevel, mixEffects, mediaSettings, currentSongPosition, midiChannelState, guiCtrlStateHolder, midiNoteState, self._mixMat1, self._mixMask)
                else:
                    imageMix, _, _ = media.mixWithImage(imageMix, mixMode, mixLevel, mixEffects, mediaSettings, currentSongPosition, midiChannelState, guiCtrlStateHolder, midiNoteState, self._mixMat2, self._mixMask)

        if(imageMix == None):
            imageMix = self._blankImage

        mediaSettingsHolder.captureImage = imageMix
        self._applyEffects(mediaSettingsHolder, currentSongPosition, midiChannelState, midiNoteState, fadeMode, fadeValue)

        return False

    def setGetMediaCallback(self, callback):
        self._getMediaCallback = callback

    def openFile(self, midiLength):
        self._mediaList = []
        fontPath = findOsFontPath()
        fontPILImage, _ = generateTextImageAndMask("Group\\n" + self._groupName, "Arial", fontPath, 12, 255, 255, 255)
        self._mediaSettingsHolder.captureImage = pilToCvImage(fontPILImage)
        self._firstImage = self._mediaSettingsHolder.captureImage
        self._fileOk = True

    def doPostConfigurations(self):
        self._mediaList = []
        self._mediaSettingsHolder.mediaSettingsHolder = []
        for noteString in self._noteList:
            noteId = noteStringToNoteNumber(noteString)
            media = self._getMediaCallback(noteId)
            if(media != None):
                self._mediaList.append(media)
                self._mediaSettingsHolder.mediaSettingsHolder.append(media.getMediaStateHolder())
        MediaFile.doPostConfigurations(self)

class ImageFile(MediaFile):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
        self._radians360 = math.radians(360)

        self._configurationTree.addTextParameter("StartValues", "0.0|0.0|0.0")
        self._configurationTree.addTextParameter("EndValues", "0.0|0.0|0.0")
        self._configurationTree.addTextParameter("DisplayMode", "Crop")

        self._startZoom, self._startMove, self._startAngle = textToFloatValues("0.0|0.0|0.0", 3)
        self._endZoom, self._endMove, self._endAngle = textToFloatValues("0.0|0.0|0.0", 3)
        self._startX, self._startY = self._angleAndMoveToXY(self._startAngle, self._startMove)
        self._endX, self._endY = self._angleAndMoveToXY(self._endAngle, self._endMove)
        self._cropMode = "Crop"

        self._getConfiguration()

    def _setupMediaSettingsHolder(self, mediaSettingsHolder):
        MediaFile._setupMediaSettingsHolder(self, mediaSettingsHolder)
        mediaSettingsHolder.zoomResizeMat = createMat(self._internalResolutionX, self._internalResolutionY)
        mediaSettingsHolder.oldZoom = -1.0
        mediaSettingsHolder.oldMoveX = -1.0
        mediaSettingsHolder.oldMoveY = -1.0
        mediaSettingsHolder.oldCrop = "-1"

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
        startValuesString = self._configurationTree.getValue("StartValues")
        self._startZoom, self._startMove, self._startAngle = textToFloatValues(startValuesString, 3)
        endValuesString = self._configurationTree.getValue("EndValues")
        self._endZoom, self._endMove, self._endAngle = textToFloatValues(endValuesString, 3)
        self._startX, self._startY = self._angleAndMoveToXY(self._startAngle, self._startMove)
        self._endX, self._endY = self._angleAndMoveToXY(self._endAngle, self._endMove)
        self._cropMode = self._configurationTree.getValue("DisplayMode")

    def getType(self):
        return "Image"

    def close(self):
        pass

    def skipFrames(self, mediaSettingsHolder, currentSongPosition, midiNoteState, midiChannelState, timeMultiplyer = None):
        fadeMode, fadeValue, noteDone = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState)
        if((fadeMode == FadeMode.Black) and (fadeValue < 0.00001)):
            self._image = None
            return noteDone

        syncLength = self._syncLength
        if(timeMultiplyer != None):
            syncLength = self._syncLength * timeMultiplyer

        zoom = self._startZoom
        moveX = self._startX
        moveY = self._startY
        angle = self._startAngle
        move = self._startMove
        guiMove = False
        unmodifiedPos = (currentSongPosition - mediaSettingsHolder.startSongPosition) / syncLength
        modifiedPos = self._timeModulatePos(unmodifiedPos, currentSongPosition, mediaSettingsHolder, midiNoteState, midiChannelState, syncLength)
        if(modifiedPos >= 1.0):
            zoom = self._endZoom
            moveX = self._endX
            moveY = self._endY
        elif(mediaSettingsHolder.startSongPosition < currentSongPosition):
#            print "DEBUG middle: currentSPP: " + str(currentSongPosition) + " startSPP: " + str(mediaSettingsHolder.startSongPosition) + " zoomTime: " + str(syncLength)
            if(self._endZoom != self._startZoom):
                zoom = self._startZoom + (((self._endZoom - self._startZoom)) * (modifiedPos))
            if(self._endX != self._startX):
                moveX = self._startX + (((self._endX - self._startX)) * (modifiedPos))
            if(self._endY != self._startY):
                moveY = self._startY + (((self._endY - self._startY)) * (modifiedPos))
        guiStates = self._guiCtrlStateHolder.getGuiContollerState(10)
        if(guiStates[0] != None):
            if(guiStates[0] > -0.5):
                zoom = guiStates[0]
        if(guiStates[1] != None):
            if(guiStates[1] > -0.5):
                move = guiStates[1]
                guiMove = True
        if(guiStates[2] != None):
            if(guiStates[2] > -0.5):
                angle = guiStates[2]
                guiMove = True
        if(guiMove == True):
            moveX, moveY = self._angleAndMoveToXY(angle, move)
        if((zoom != mediaSettingsHolder.oldZoom) or (moveX != mediaSettingsHolder.oldMoveX) or (moveY != mediaSettingsHolder.oldMoveY) or (self._cropMode != mediaSettingsHolder.oldCrop)):
#            print "DEBUG pcn: render image!!!!!!!!! " + str(mediaSettingsHolder._uid)
            mediaSettingsHolder.oldZoom = zoom
            mediaSettingsHolder.oldMoveX = moveX
            mediaSettingsHolder.oldMoveY = moveY
            mediaSettingsHolder.oldCrop = self._cropMode
            if(zoom <= 0.5):
                multiplicator = 1.0 - zoom
            elif(zoom <= 0.75):
                multiplicator = 0.5 - (0.1666666 * ((zoom - 0.5) * 4))
            else:
                multiplicator = 0.3333333 - (0.08333333 *((zoom - 0.75) * 4))
#            print "DEBUG zoom: " + str(zoom) + " multiplicator: " + str(multiplicator)
            dst_region = cv.GetSubRect(mediaSettingsHolder.zoomResizeMat, (0, 0, self._internalResolutionX, self._internalResolutionY))
            if(self._cropMode == "Crop"):
                sourceRectangleX = int(self._source100percentCropX * multiplicator)
                sourceRectangleY = int(self._source100percentCropY * multiplicator)
            elif(self._cropMode == "Scale"):
                destRectangleX = int(self._dest100percentScaleX / multiplicator)
                destRectangleY = int(self._dest100percentScaleY / multiplicator)
                sourceRectangleX = self._sourceX
                sourceRectangleY = self._sourceY
#                print "DEBUG pcn: scale: PRE x: " + str(destRectangleX) + " y: " + str(destRectangleY)
                if(destRectangleX > self._internalResolutionX):
                    destScaleX = float(self._internalResolutionX) / destRectangleX
                    destRectangleX = min(destRectangleX, self._internalResolutionX)
                    sourceRectangleX = int(self._sourceX * destScaleX)
                if(destRectangleY > self._internalResolutionY):
                    destScaleY = float(self._internalResolutionY) / destRectangleY
                    destRectangleY = min(destRectangleY, self._internalResolutionY)
                    sourceRectangleY = int(self._sourceY * destScaleY)
#                print "DEBUG pcn: scale: mul: " + str(multiplicator) + " x: " + str(destRectangleX) + " y: " + str(destRectangleY)
                destLeft = 0
                destTop = 0
                if(destRectangleX < self._internalResolutionX):
                    destLeft = (self._internalResolutionX - destRectangleX) / 2
                if(destRectangleY < self._internalResolutionY):
                    destTop = (self._internalResolutionY - destRectangleY) / 2
                cv.SetZero(mediaSettingsHolder.zoomResizeMat)
#                print "DEBUG pcn: scale: left: " + str(destLeft) + " top: " + str(destTop)
                dst_region = cv.GetSubRect(mediaSettingsHolder.zoomResizeMat, (destLeft, destTop, destRectangleX, destRectangleY))
            else:
                sourceRectangleX = int(self._sourceX * multiplicator)
                sourceRectangleY = int(self._sourceY * multiplicator)                
            if(sourceRectangleX < self._sourceX):
                left = int((self._sourceX - sourceRectangleX) / 2)
            else:
                sourceRectangleX = self._sourceX
                left = 0
            maxXmovmentPlussMinus = left
            if(sourceRectangleY < self._sourceY):
                top = int((self._sourceY - sourceRectangleY) / 2)
            else:
                sourceRectangleY = self._sourceY
                top = 0
            maxYmovmentPlussMinus = top
            left = int(moveX * maxXmovmentPlussMinus) + left
            left = int(moveX) + left
            if(left < 0):
                left = 0
            elif((left + sourceRectangleX) > self._sourceX):
                left = self._sourceX - sourceRectangleX
            top = int(moveY * maxYmovmentPlussMinus) + top
            if(top < 0):
                top = 0
            elif((top + sourceRectangleY) > self._sourceY):
                top = self._sourceY - sourceRectangleY
#            print "DEBUG Move X: %d Y: %d" %(moveX, moveY)
#            print "DEBUG pcn: src_region: " + str((left, top, sourceRectangleX, sourceRectangleY))
            src_region = cv.GetSubRect(self._firstImage, (left, top, sourceRectangleX, sourceRectangleY) )
            cv.Resize(src_region, dst_region)
            mediaSettingsHolder.captureImage = mediaSettingsHolder.zoomResizeMat
#        self._applyEffects(mediaSettingsHolder, currentSongPosition, midiChannelState, midiNoteState, fadeMode, fadeValue)
        mediaSettingsHolder.image = mediaSettingsHolder.captureImage
        return False

    def _angleAndMoveToXY(self, angle, move):
        angle360 = angle * 360
        if(angle360 < 45.0):
            moveX = -move
            moveY = math.tan(self._radians360 * angle) * -move
        elif(angle360 < 135):
            moveX = math.tan(self._radians360 * (angle-0.25)) * move
            moveY = -move
        elif(angle360 < 225):
            moveX = move
            moveY = math.tan(self._radians360 * (angle-0.5)) * move
        elif(angle360 < 315):
            moveX = math.tan(self._radians360 * (angle-0.75)) * -move
            moveY = move
        else:
            moveX = -move
            moveY = math.tan(self._radians360 * angle) * -move
        return moveX, moveY
        
    def openFile(self, midiLength):
        filePath = self._fullFilePath
        if(os.path.isfile(filePath) == False):
            filePath = self._packageFilePath
        if (os.path.isfile(filePath) == False):
            self._log.warning("Could not find file: %s in directory: %s", self._cfgFileName, self._videoDirectory)
            print "Error! Could not find file: %s in directory: %s" % (self._cfgFileName, self._videoDirectory)
            raise MediaError("File does not exist!")
        try:
            pilImage = Image.open(filePath)
            pilImage.load()
        except:
            self._log.warning("Exception while reading: %s", os.path.basename(self._cfgFileName))
            print "Exception while reading: " + os.path.basename(self._cfgFileName)
            raise MediaError("File caused exception!")
        pilSplit = pilImage.split()
#        print "DEBUG Image split: " + str(len(pilSplit)) + " mode: " + str(pilImage.mode)
        pilDepth = len(pilSplit)
        if(pilDepth == 1):
            if(pilImage.mode == "P"):
                pilRgb = pilImage.convert("RGB")
                pilSplit2 = pilRgb.split()
                pilRgb = Image.merge("RGB", (pilSplit2[2], pilSplit2[1], pilSplit2[0])) #We need "BGR" and not "RGB"
            else:
                pilRgb = Image.merge("RGB", (pilSplit[0], pilSplit[0], pilSplit[0]))
        if(pilDepth > 2):
            pilRgb = Image.merge("RGB", (pilSplit[2], pilSplit[1], pilSplit[0])) #We need "BGR" and not "RGB"
        self._mediaSettingsHolder.captureImage = pilToCvImage(pilRgb)
        if(self._mediaSettingsHolder.captureImage == None):
            self._log.warning("Could not read image from: %s", os.path.basename(self._cfgFileName))
            print "Could not read image from: " + os.path.basename(self._cfgFileName)
            raise MediaError("File could not be read!")
        self._firstImage = self._mediaSettingsHolder.captureImage
        self._originalTime = 1.0
        self._sourceX, self._sourceY = cv.GetSize(self._firstImage)
        self._sourceAspect = float(self._sourceX) / self._sourceY
        self._destinationAspect = float(self._internalResolutionX) / self._internalResolutionY
        if(self._sourceAspect > self._destinationAspect):
            self._source100percentCropX = int(self._sourceY * self._destinationAspect)
            self._source100percentCropY = self._sourceY
            self._dest100percentScaleX = self._internalResolutionX
            self._dest100percentScaleY = int(self._internalResolutionX / self._sourceAspect)
#            print "DEBUG pcn: scale1 x: " + str(self._dest100percentScaleX) + " y: " + str(self._dest100percentScaleY)
        else:
            self._source100percentCropX = self._sourceX
            self._source100percentCropY = int(self._sourceX / self._destinationAspect)
            self._dest100percentScaleX = int(self._internalResolutionY * self._sourceAspect)
            self._dest100percentScaleY = self._internalResolutionY
#            print "DEBUG pcn: scale2 x: " + str(self._dest100percentScaleX) + " y: " + str(self._dest100percentScaleY)
        self._log.warning("Read image file %s", os.path.basename(self._cfgFileName))
        self._fileOk = True

class ScrollImageFile(MediaFile):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)

        self._midiModulation = MidiModulation(self._configurationTree, self._midiTiming, self._specialModulationHolder)
        self._configurationTree.addBoolParameter("HorizontalMode", True)
        self._configurationTree.addBoolParameter("ReverseMode", False)
        self._midiModulation.setModulationReceiver("ScrollModulation", "None")
        self._scrollModulationId = None

        self._getConfiguration()

    def _setupMediaSettingsHolder(self, mediaSettingsHolder):
        MediaFile._setupMediaSettingsHolder(self, mediaSettingsHolder)
        mediaSettingsHolder.scrollResizeMat = createMat(self._internalResolutionX, self._internalResolutionY)
        mediaSettingsHolder.scrollResizeMask = createMask(self._internalResolutionX, self._internalResolutionY)
        mediaSettingsHolder.oldScrollLength = -1.0
        mediaSettingsHolder.oldScrollMode = False

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
        self._isScrollModeHorizontal = self._configurationTree.getValue("HorizontalMode")
        self._isScrollModeReverse = self._configurationTree.getValue("ReverseMode")
        self._scrollModulationId = self._midiModulation.connectModulation("ScrollModulation")

    def getType(self):
        return "ScrollImage"

    def close(self):
        pass

    def skipFrames(self, mediaSettingsHolder, currentSongPosition, midiNoteState, midiChannelState, timeMultiplyer = None):
        fadeMode, fadeValue, noteDone = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState)
        if((fadeMode == FadeMode.Black) and (fadeValue < 0.00001)):
            mediaSettingsHolder.image = None
            return noteDone

        syncLength = self._syncLength
        if(timeMultiplyer != None):
            syncLength = self._syncLength * timeMultiplyer

        #Find scroll length.
        if(self._scrollModulationId == None):
            unmodifiedPos = (currentSongPosition - mediaSettingsHolder.startSongPosition) / syncLength
            modifiedPos = self._timeModulatePos(unmodifiedPos, currentSongPosition, mediaSettingsHolder, midiNoteState, midiChannelState, syncLength)
            scrollLength = modifiedPos % 1.0
            if(self._isScrollModeHorizontal == True):
                scrollLength = 1.0 - scrollLength
            if(self._isScrollModeReverse == False):
                scrollLength = 1.0 - scrollLength
        else:
            scrollLength = self._midiModulation.getModlulationValue(self._scrollModulationId, midiChannelState, midiNoteState, currentSongPosition, self._specialModulationHolder)
        guiStates = self._guiCtrlStateHolder.getGuiContollerState(10)
        if(guiStates[0] != None):
            if(guiStates[0] > -0.5):
                scrollLength = guiStates[0]

        #Scroll image + mask
        if((self._isScrollModeHorizontal != mediaSettingsHolder.oldScrollMode) or (scrollLength != mediaSettingsHolder.oldScrollLength)):
            mediaSettingsHolder.oldScrollLength = scrollLength
            mediaSettingsHolder.oldScrollMode = self._isScrollModeHorizontal
            if(self._isScrollModeHorizontal == True):
                left = int(scrollLength * (self._sourceX - 1))
                if((left + self._source100percentCropX) <= self._sourceX):
                    srcRegion = cv.GetSubRect(self._firstImage, (left, 0, self._source100percentCropX, self._source100percentCropY) )
                    dstRegion = cv.GetSubRect(mediaSettingsHolder.scrollResizeMat, (0, 0, self._internalResolutionX, self._internalResolutionY) )
                    if(self._firstImageMask != None):
                        srcRegionMask = cv.GetSubRect(self._firstImageMask, (left, 0, self._source100percentCropX, self._source100percentCropY) )
                        dstRegionMask = cv.GetSubRect(mediaSettingsHolder.scrollResizeMask, (0, 0, self._internalResolutionX, self._internalResolutionY) )
                else:
                    extraWidth = (left + self._source100percentCropX) - self._sourceX
                    destinationWidth = int((extraWidth * self._internalResolutionX) / self._source100percentCropX)
                    #Rest:
                    srcRegion = cv.GetSubRect(self._firstImage, (0, 0, extraWidth, self._source100percentCropY))
                    dstRegion = cv.GetSubRect(mediaSettingsHolder.scrollResizeMat, (self._internalResolutionX - destinationWidth, 0, destinationWidth, self._internalResolutionY) )
                    cv.Resize(srcRegion, dstRegion)
                    if(self._firstImageMask != None):
                        srcRegionMask = cv.GetSubRect(self._firstImageMask, (0, 0, extraWidth, self._source100percentCropY))
                        dstRegionMask = cv.GetSubRect(mediaSettingsHolder.scrollResizeMask, (self._internalResolutionX - destinationWidth, 0, destinationWidth, self._internalResolutionY) )
                        cv.Resize(srcRegionMask, dstRegionMask)
                    #Main:
                    width = self._sourceX - left
                    srcRegion = cv.GetSubRect(self._firstImage, (left, 0, width, self._source100percentCropY))
                    dstRegion = cv.GetSubRect(mediaSettingsHolder.scrollResizeMat, (0, 0, self._internalResolutionX - destinationWidth, self._internalResolutionY) )
                    if(self._firstImageMask != None):
                        srcRegionMask = cv.GetSubRect(self._firstImageMask, (left, 0, width, self._source100percentCropY))
                        dstRegionMask = cv.GetSubRect(mediaSettingsHolder.scrollResizeMask, (0, 0, self._internalResolutionX - destinationWidth, self._internalResolutionY) )
                cv.Resize(srcRegion, dstRegion)
                mediaSettingsHolder.captureImage = mediaSettingsHolder.scrollResizeMat
                if(self._firstImageMask != None):
                    cv.Resize(srcRegionMask, dstRegionMask)
                    mediaSettingsHolder.captureMask = mediaSettingsHolder.scrollResizeMask
                else:
                    mediaSettingsHolder.captureMask = None
            else: # self._isScrollModeHorizontal == False -> Vertical mode
                top = int(scrollLength * (self._sourceY - 1))
                if((top + self._source100percentCropY) <= self._sourceY):
                    srcRegion = cv.GetSubRect(self._firstImage, (0, top, self._source100percentCropX, self._source100percentCropY) )
                    dstRegion = cv.GetSubRect(mediaSettingsHolder.scrollResizeMat, (0, 0, self._internalResolutionX, self._internalResolutionY) )
                    if(self._firstImageMask != None):
                        srcRegionMask = cv.GetSubRect(self._firstImageMask, (0, top, self._source100percentCropX, self._source100percentCropY) )
                        dstRegionMask = cv.GetSubRect(mediaSettingsHolder.scrollResizeMask, (0, 0, self._internalResolutionX, self._internalResolutionY) )
                else:
                    extraHeight = (top + self._source100percentCropY) - self._sourceY
                    destinationHeight = int((extraHeight * self._internalResolutionY) / self._source100percentCropY)
                    #Rest:
                    srcRegion = cv.GetSubRect(self._firstImage, (0, 0, self._source100percentCropX, extraHeight))
                    dstRegion = cv.GetSubRect(mediaSettingsHolder.scrollResizeMat, (0, self._internalResolutionY - destinationHeight, self._internalResolutionX, destinationHeight) )
                    cv.Resize(srcRegion, dstRegion)
                    if(self._firstImageMask != None):
                        srcRegionMask = cv.GetSubRect(self._firstImageMask, (0, 0, self._source100percentCropX, extraHeight))
                        dstRegionMask = cv.GetSubRect(mediaSettingsHolder.scrollResizeMask, (0, self._internalResolutionY - destinationHeight, self._internalResolutionX, destinationHeight) )
                        cv.Resize(srcRegionMask, dstRegionMask)
                    #Main:
                    height = self._sourceY - top
                    srcRegion = cv.GetSubRect(self._firstImage, (0, top, self._source100percentCropX, height))
                    dstRegion = cv.GetSubRect(mediaSettingsHolder.scrollResizeMat, (0, 0, self._internalResolutionX, self._internalResolutionY - destinationHeight) )
                    if(self._firstImageMask != None):
                        srcRegionMask = cv.GetSubRect(self._firstImageMask, (0, top, self._source100percentCropX, height))
                        dstRegionMask = cv.GetSubRect(mediaSettingsHolder.scrollResizeMask, (0, 0, self._internalResolutionX, self._internalResolutionY - destinationHeight) )
                cv.Resize(srcRegion, dstRegion)
                mediaSettingsHolder.captureImage = mediaSettingsHolder.scrollResizeMat
                if(self._firstImageMask != None):
                    cv.Resize(srcRegionMask, dstRegionMask)
                    mediaSettingsHolder.captureMask = mediaSettingsHolder.scrollResizeMask
                else:
                    mediaSettingsHolder.captureMask = None

        mediaSettingsHolder.imageMask = mediaSettingsHolder.captureMask
        self._applyEffects(mediaSettingsHolder, currentSongPosition, midiChannelState, midiNoteState, fadeMode, fadeValue)
        return False

    def openFile(self, midiLength):
        filePath = self._fullFilePath
        if(os.path.isfile(filePath) == False):
            filePath = self._packageFilePath
        if (os.path.isfile(filePath) == False):
            self._log.warning("Could not find file: %s in directory: %s", self._cfgFileName, self._videoDirectory)
            raise MediaError("File does not exist!")
        try:
            pilImage = Image.open(filePath)
            pilImage.load()
        except:
            self._log.warning("Exception while reading: %s", os.path.basename(self._cfgFileName))
            print "Exception while reading: " + os.path.basename(self._cfgFileName)
            raise MediaError("File caused exception!")
        pilSplit = pilImage.split()
#        print "DEBUG Image split: " + str(len(pilSplit)) + " mode: " + str(pilImage.mode)
        pilDepth = len(pilSplit)
        maskThreshold = 128
        if(pilDepth == 1):
            if(pilImage.mode == "P"):
                try:
                    transparencyIndex = pilImage.info["transparency"]
                    pilMask = pilImage.point(lambda i: i != transparencyIndex and 255).convert("L")
                    maskThreshold = 255
                except:
                    pilMask = None
                pilRgb = pilImage.convert("RGB")
                pilSplit2 = pilRgb.split()
                pilRgb = Image.merge("RGB", (pilSplit2[2], pilSplit2[1], pilSplit2[0])) #We need "BGR" and not "RGB"
            else:
                pilRgb = Image.merge("RGB", (pilSplit[0], pilSplit[0], pilSplit[0]))
                pilMask = None
        if(pilDepth > 2):
            pilRgb = Image.merge("RGB", (pilSplit[2], pilSplit[1], pilSplit[0])) #We need "BGR" and not "RGB"
            if(pilDepth > 3):
                pilMask = pilSplit[3]
            else:
                pilMask = None
        self._mediaSettingsHolder.captureImage = pilToCvImage(pilRgb)
        if(pilMask != None):
            self._mediaSettingsHolder.captureMask = pilToCvMask(pilMask, maskThreshold)
        else:
            self._mediaSettingsHolder.captureMask = None
        if (self._mediaSettingsHolder.captureImage == None):
            self._log.warning("Could not read image from: %s", os.path.basename(self._cfgFileName))
            print "Could not read image from: " + os.path.basename(self._cfgFileName)
            raise MediaError("File could not be read!")
        self._firstImage = self._mediaSettingsHolder.captureImage
        self._firstImageMask = self._mediaSettingsHolder.captureMask
        self._originalTime = 1.0
        self._sourceX, self._sourceY = cv.GetSize(self._firstImage)
        self._sourceAspect = float(self._sourceX) / self._sourceY
        self._destinationAspect = float(self._internalResolutionX) / self._internalResolutionY
        if(self._sourceAspect > self._destinationAspect):
            self._source100percentCropX = int(self._sourceY * self._destinationAspect)
            self._source100percentCropY = self._sourceY
        else:
            self._source100percentCropX = self._sourceX
            self._source100percentCropY = int(self._sourceX / self._destinationAspect)
        self._log.warning("Read image file %s", os.path.basename(self._cfgFileName))
        self._fileOk = True

class SpriteMediaBase(MediaFile):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)

        self._midiModulation = MidiModulation(self._configurationTree, self._midiTiming, self._specialModulationHolder)
        self._configurationTree.addTextParameter("StartPosition", "0.5|0.5")
        self._configurationTree.addTextParameter("EndPosition", "0.5|0.5")
        self._midiModulation.setModulationReceiver("XModulation", "None")
        self._midiModulation.setModulationReceiver("YModulation", "None")
        self._startX, self._startY = textToFloatValues("0.5|0.5", 2)
        self._endX, self._endY = textToFloatValues("0.5|0.5", 2)
        self._xModulationId = None
        self._yModulationId = None

        self._bufferedImageList = []
        self._bufferedImageMasks = []

        self._getConfiguration()

    def _setupMediaSettingsHolder(self, mediaSettingsHolder):
        MediaFile._setupMediaSettingsHolder(self, mediaSettingsHolder)
        mediaSettingsHolder.spritePlacementMat = createMat(self._internalResolutionX, self._internalResolutionY)
        mediaSettingsHolder.spritePlacementMask = createMask(self._internalResolutionX, self._internalResolutionY)
        mediaSettingsHolder.oldX = -2.0
        mediaSettingsHolder.oldY = -2.0
        mediaSettingsHolder.oldCurrentFrame = -1

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
        startValuesString = self._configurationTree.getValue("StartPosition")
        self._startX, self._startY = textToFloatValues(startValuesString, 2)
        endValuesString = self._configurationTree.getValue("EndPosition")
        self._endX, self._endY = textToFloatValues(endValuesString, 2)
        self._xModulationId = self._midiModulation.connectModulation("XModulation")
        self._yModulationId = self._midiModulation.connectModulation("YModulation")

    def getType(self):
        return "SpriteMediaBase"

    def close(self):
        pass

    def skipFrames(self, mediaSettingsHolder, currentSongPosition, midiNoteState, midiChannelState, timeMultiplyer = None):
        fadeMode, fadeValue, noteDone = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState)
        if((fadeMode == FadeMode.Black) and (fadeValue < 0.00001)):
            mediaSettingsHolder.image = None
            return noteDone

        syncLength = self._syncLength
        if(timeMultiplyer != None):
            syncLength = self._syncLength * timeMultiplyer

        #Find pos.
        posX = 0.5
        posY = 0.5
        modulationIsActive = False
        if((self._xModulationId != None)):
            posX = self._midiModulation.getModlulationValue(self._xModulationId, midiChannelState, midiNoteState, currentSongPosition, self._specialModulationHolder)
            modulationIsActive = True
        if((self._yModulationId != None)):
            posY = self._midiModulation.getModlulationValue(self._yModulationId, midiChannelState, midiNoteState, currentSongPosition, self._specialModulationHolder)
            modulationIsActive = True

        if(modulationIsActive == False):
            posX = self._startX
            posY = self._startY
            unmodifiedPos = (currentSongPosition - mediaSettingsHolder.startSongPosition) / syncLength
            modifiedPos = self._timeModulatePos(unmodifiedPos, currentSongPosition, mediaSettingsHolder, midiNoteState, midiChannelState, syncLength)
            if(modifiedPos >= 1.0):
                posX = self._endX
                posY = self._endY
            elif(mediaSettingsHolder.startSongPosition < currentSongPosition):
                if(self._endX != self._startX):
                    posX = self._startX + ((self._endX - self._startX) * modifiedPos)
                if(self._endY != self._startY):
                    posY = self._startY + ((self._endY - self._startY) * modifiedPos)

        guiStates = self._guiCtrlStateHolder.getGuiContollerState(10)
        if(guiStates[0] != None):
            if(guiStates[0] > -0.5):
                posX = guiStates[0]
        if(guiStates[1] != None):
            if(guiStates[1] > -0.5):
                posY = guiStates[1]

        #Select frame.
        if(self._numberOfFrames == 1):
            mediaSettingsHolder.currentFrame = 0
        else:
            unmodifiedFramePos = ((currentSongPosition - mediaSettingsHolder.startSongPosition) / syncLength) * self._numberOfFrames
            mediaSettingsHolder.currentFrame = int(unmodifiedFramePos) % self._numberOfFrames

        #Scroll image + mask
        if((posX != mediaSettingsHolder.oldX) or(posY != mediaSettingsHolder.oldY) or (mediaSettingsHolder.currentFrame != mediaSettingsHolder.oldCurrentFrame)):
            mediaSettingsHolder.oldX = posX
            mediaSettingsHolder.oldY = posY
            mediaSettingsHolder.oldCurrentFrame = mediaSettingsHolder.currentFrame
            cv.SetZero(mediaSettingsHolder.spritePlacementMat)
            cv.SetZero(mediaSettingsHolder.spritePlacementMask)
            currentSource = self._bufferedImageList[mediaSettingsHolder.currentFrame]
            currentSourceMask = self._bufferedImageMasks[mediaSettingsHolder.currentFrame]
            sourceX, sourceY = cv.GetSize(currentSource)
            xMovmentRange = self._internalResolutionX + sourceX
            yMovmentRange = self._internalResolutionY + sourceY
            left = int(xMovmentRange * posX) - sourceX
            top = int(yMovmentRange * posY) - sourceY
            width = sourceX
            height = sourceY
            sourceLeft = 0
            sourceTop = 0
            sourceWidth = sourceX
            sourceHeight = sourceY
            if(left < 0):
                sourceLeft = -left
                sourceWidth = sourceWidth + left
                width = width + left
                left = 0
            elif((left + sourceX) > self._internalResolutionX):
                overflow = (left + sourceX - self._internalResolutionX)
                sourceWidth = sourceWidth - overflow
                width = width - overflow
            if(top < 0):
                sourceTop = -top
                sourceHeight = sourceHeight + top
                height = height + top
                top = 0
            elif((top + sourceY) > self._internalResolutionY):
                overflow = (top + sourceY - self._internalResolutionY)
                sourceHeight = sourceHeight - overflow
                height = height - overflow
            if(left < 0):
                width = width + left
                left = 0
            if(width > (left + self._internalResolutionX)):
                overflow = (width + left - self._internalResolutionX)
                sourceWidth = sourceWidth - overflow
                width = width - overflow
            if(top < 0):
                top = 0
                height = height + top
            if(height > (top + self._internalResolutionY)):
                overflow = (height + top - self._internalResolutionY)
                sourceHeight = sourceHeight - overflow
                height = height - overflow
            if((width > 0) and (height > 0)):
                srcRegion = cv.GetSubRect(currentSource, (sourceLeft, sourceTop, sourceWidth, sourceHeight))
                dstRegion = cv.GetSubRect(mediaSettingsHolder.spritePlacementMat, (left, top, width, height))
                cv.Resize(srcRegion, dstRegion)
                srcRegion = cv.GetSubRect(currentSourceMask, (sourceLeft, sourceTop, sourceWidth, sourceHeight))
                dstRegion = cv.GetSubRect(mediaSettingsHolder.spritePlacementMask, (left, top, width, height))
                cv.Resize(srcRegion, dstRegion)
            mediaSettingsHolder.captureImage = mediaSettingsHolder.spritePlacementMat
            mediaSettingsHolder.captureMask = mediaSettingsHolder.spritePlacementMask

        mediaSettingsHolder.imageMask = mediaSettingsHolder.captureMask
        self._applyEffects(mediaSettingsHolder, currentSongPosition, midiChannelState, midiNoteState, fadeMode, fadeValue)
        return False

    def openFile(self, midiLength):
        pass

class SpriteImageFile(SpriteMediaBase):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        SpriteMediaBase.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
        self._configurationTree.addBoolParameter("InvertFirstFrameMask", False)
        self._invertFirstImageMask = False
        self._getConfiguration()

    def _getConfiguration(self):
        SpriteMediaBase._getConfiguration(self)
        if(self._fileOk):
            oldInvState = self._invertFirstImageMask
            self._invertFirstImageMask = self._configurationTree.getValue("InvertFirstFrameMask")
            if(oldInvState != self._invertFirstImageMask):
                print "InvertFirstFrameMask is updated -> Sprite is re-loaded."
                self._loadFile()

    def getType(self):
        return "Sprite"

    def _loadFile(self):
        filePath = self._fullFilePath
        if(os.path.isfile(filePath) == False):
            filePath = self._packageFilePath
        if (os.path.isfile(filePath) == False):
            self._log.warning("Could not find file: %s in directory: %s", self._cfgFileName, self._videoDirectory)
            print "Could not find file: %s in directory: %s" % (self._cfgFileName, self._videoDirectory)
            raise MediaError("File does not exist!")
        try:
            pilImage = Image.open(filePath)
            pilImage.load()
        except:
            self._log.warning("Exception while reading: %s", os.path.basename(self._cfgFileName))
            print "Exception while reading: " + os.path.basename(self._cfgFileName)
            raise MediaError("File caused exception!")
        pilSplit = pilImage.split()
        pilDepth = len(pilSplit)
        maskThreshold = 128
        if(pilDepth == 1):
            if(pilImage.mode == "P"):
                try:
                    transparencyIndex = pilImage.info["transparency"]
                    maskThreshold = 255
                    if(self._invertFirstImageMask == True):
                        pilMask = pilImage.point(lambda i: i == transparencyIndex and 255).convert("L")
                    else:
                        pilMask = pilImage.point(lambda i: i != transparencyIndex and 255).convert("L")
#                        pilMask = pilImage.point(lambda i: i != transparencyIndex and 255).convert("L")
                except:
                    pilMask = None
                firstImagePallette = pilImage.getpalette()
                pilRgb = pilImage.convert("RGB")
                pilSplit2 = pilRgb.split()
                pilRgb = Image.merge("RGB", (pilSplit2[2], pilSplit2[1], pilSplit2[0])) #We need "BGR" and not "RGB"
            else:
                pilRgb = Image.merge("RGB", (pilSplit[0], pilSplit[0], pilSplit[0]))
                pilMask = None
        elif(pilDepth > 2):
            pilRgb = Image.merge("RGB", (pilSplit[2], pilSplit[1], pilSplit[0])) #We need "BGR" and not "RGB"
            if(pilDepth > 3):
                pilMask = pilSplit[3]
            else:
                pilMask = None
        self._mediaSettingsHolder.captureImage = pilToCvImage(pilRgb)
        if(pilMask != None):
            self._mediaSettingsHolder.captureMask = pilToCvMask(pilMask, maskThreshold)
        else:
            sizeX, sizeY = cv.GetSize(self._captureImage)
            captureMask = createMask(sizeX, sizeY)
            cv.Set(captureMask, 255)
            self._mediaSettingsHolder.captureMask = captureMask
        if (self._mediaSettingsHolder.captureImage == None):
            self._log.warning("Could not read image from: %s", os.path.basename(self._cfgFileName))
            print "Could not read image from: " + os.path.basename(self._cfgFileName)
            raise MediaError("File could not be read!")
        self._bufferedImageList.append(self._mediaSettingsHolder.captureImage)
        self._bufferedImageMasks.append(self._mediaSettingsHolder.captureMask)
        try:
            while(True):
                pilImage.seek(pilImage.tell()+1)
                pilSplit = pilImage.split()
                pilDepth = len(pilSplit)
                if(pilDepth == 1):
                    if(pilImage.mode == "P"):
                        try:
                            transparencyIndex = pilImage.info["transparency"]
                            pilMask = pilImage.point(lambda i: i != transparencyIndex and 255).convert("L")
                        except:
                            pilMask = None
                        pilImage.putpalette(firstImagePallette)
                        pilRgb = pilImage.convert("RGB")
                        pilSplit2 = pilRgb.split()
                        pilRgb = Image.merge("RGB", (pilSplit2[2], pilSplit2[1], pilSplit2[0])) #We need "BGR" and not "RGB"
                    else:
                        pilRgb = Image.merge("RGB", (pilSplit[0], pilSplit[0], pilSplit[0]))
                        pilMask = None
                elif(pilDepth > 2):
                    pilRgb = Image.merge("RGB", (pilSplit[2], pilSplit[1], pilSplit[0])) #We need "BGR" and not "RGB"
                    if(pilDepth > 3):
                        pilMask = pilSplit[3]
                    else:
                        pilMask = None
                self._bufferedImageList.append(pilToCvImage(pilRgb))
                if(pilMask != None):
                    self._bufferedImageMasks.append(pilToCvMask(pilMask, maskThreshold))
                else:
                    self._bufferedImageMasks.append(self._mediaSettingsHolder.captureMask)
        except EOFError:
            pass
        self._firstImage = self._mediaSettingsHolder.captureImage
        self._firstImageMask = self._mediaSettingsHolder.captureMask
        self._numberOfFrames = len(self._bufferedImageList)
        self._originalTime = 1.0
        for mediaSettingsHolder in self._mediaSettingsHolder.getSettingsList():
            mediaSettingsHolder.oldCurrentFrame = -1
        self._log.warning("Read image file %s", os.path.basename(self._cfgFileName))

    def openFile(self, midiLength):
        self._loadFile()
        if(midiLength != None): # Else we get length from configuration or default.
            if(midiLength > 0.0):
                self.setMidiLengthInBeats(midiLength)
        self._fileOk = True

class TextMedia(SpriteMediaBase):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        SpriteMediaBase.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
        self._configurationTree.addTextParameter("Font", "Arial;32;#FFFFFF")
        self._font = "Undefined"
        self._getConfiguration()
        self._fontPath = findOsFontPath()

#    def _setupMediaSettingsHolder(self, mediaSettingsHolder):
#        SpriteMediaBase._setupMediaSettingsHolder(self, mediaSettingsHolder)

    def _getConfiguration(self):
        SpriteMediaBase._getConfiguration(self)
        if(self._fileOk):
            oldFont = self._font
            self._font = self._configurationTree.getValue("Font")
            if(oldFont != self._font):
#                print "DEBUG pcn: _getConfiguration -> _renderText()"
                self._renderText()

    def getType(self):
        return "Text"

    def getFileName(self):
        return self.getType() + ":" + self._cfgFileName

    def _renderText(self):
        text = self._cfgFileName
        fontString = self._font
        fontStringSplit = fontString.split(";")
        startFont = fontStringSplit[0]
        try:
            startSize = int(fontStringSplit[1])
        except:
            startSize = 32
        try:
            startColour = fontStringSplit[2]
        except:
            startColour = "#FFFFFF"
        startPos = 0
        if(startColour.startswith("#")):
            startPos = 1
        startRed = int(startColour[startPos:startPos+2], 16)
        startGreen = int(startColour[startPos+2:startPos+4], 16)
        startBlue = int(startColour[startPos+4:startPos+6], 16)

        fontPILImage, textPILMask = generateTextImageAndMask(text, startFont, self._fontPath, startSize, startRed, startGreen, startBlue)
        self._mediaSettingsHolder.captureImage = pilToCvImage(fontPILImage)
        self._mediaSettingsHolder.captureMask = pilToCvMask(textPILMask, 2)

        self._firstImage = self._mediaSettingsHolder.captureImage
        self._firstImageMask = self._mediaSettingsHolder.captureMask
        self._bufferedImageList = []
        self._bufferedImageMasks = []
        self._bufferedImageList.append(self._mediaSettingsHolder.captureImage)
        self._bufferedImageMasks.append(self._mediaSettingsHolder.captureMask)
        self._numberOfFrames = len(self._bufferedImageList)
        self._originalTime = 1.0

        for mediaSettingsHolder in self._mediaSettingsHolder.getSettingsList():
            mediaSettingsHolder.oldCurrentFrame = -1
        self._log.warning("Generated text media: %s", self._cfgFileName)

    def openFile(self, midiLength):
#        print "DEBUG pcn: openFile -> _getConfiguration()"
        self._getConfiguration()
        if(midiLength != None): # Else we get length from configuration or default.
            if(midiLength > 0.0):
                self.setMidiLengthInBeats(midiLength)
        self._fileOk = True

class VideoCaptureCameras(object):
    def __init__(self):
        self._cameraList = []
        self._cameraTimeStamps = []
        self._bufferdImages = []
        self._internalResolutionX = 800
        self._internalResolutionY = 600

    def openCamera(self, cameraId, internalResolutionX, internalResolutionY):
        self._internalResolutionX = internalResolutionX
        self._internalResolutionY = internalResolutionY
        minNumCamearas = cameraId + 1
        while(minNumCamearas > len(self._cameraList)):
            self._cameraList.append(None)
            self._cameraTimeStamps.append(-1.0)
            blankImage = getEmptyImage(self._internalResolutionX, self._internalResolutionY)
            self._bufferdImages.append(blankImage)
        if(self._cameraList[cameraId] == None):
            import VideoCapture #@UnresolvedImport
            try:
                self._cameraList[cameraId] = VideoCapture.Device(cameraId)
            except:
                return False # Failed to open camera id.
        return True

    def getFirstImage(self, cameraId):
        return self.getCameraImage(cameraId, None)

    def getCameraImage(self, cameraId, timeStamp):
        if(self._cameraList[cameraId] == None):
            return self._bufferdImages[cameraId]
        minNumCamearas = cameraId + 1
        if(minNumCamearas > len(self._cameraList)):
            print "ERROR: Camera with id %d is not initialized! We only got %d number of cameras." %(minNumCamearas, len(self._cameraList))
            return None
        if((timeStamp != None) and (self._cameraTimeStamps[cameraId] != timeStamp)):
            pilImage = self._cameraList[cameraId].getImage()
            if(pilImage != None):
                cvImage = cv.CreateImageHeader(pilImage.size, cv.IPL_DEPTH_8U, 3)
                cv.SetData(cvImage, pilImage.tostring())
                rotatedImage = createMat(pilImage.size[0], pilImage.size[1])
                cv.CvtColor(cvImage, rotatedImage, cv.CV_BGR2RGB)
#                rezizedImage = createMat(self._internalResolutionX, self._internalResolutionY)
                self._bufferdImages[cameraId] = rotatedImage#resizeImage(rotatedImage, rezizedImage)
                self._cameraTimeStamps[cameraId] = timeStamp
#        else:
#            print "DEBUG: using buffered image!!!"
        return self._bufferdImages[cameraId]

class OpenCvCameras(object):
    def __init__(self):
        self._cameraList = []
        self._cameraTimeStamps = []
        self._cameraFrameRates = []
        self._bufferdImages = []
        self._internalResolutionX = 800
        self._internalResolutionY = 600

    def openCamera(self, cameraId, internalResolutionX, internalResolutionY):
        self._internalResolutionX = internalResolutionX
        self._internalResolutionY = internalResolutionY
        minNumCamearas = cameraId + 1
        while(minNumCamearas > len(self._cameraList)):
            self._cameraList.append(None)
            self._cameraTimeStamps.append(-1.0)
            self._cameraFrameRates.append(0.0)
            blankImage = getEmptyImage(self._internalResolutionX, self._internalResolutionY)
            self._bufferdImages.append(blankImage)
        if(self._cameraList[cameraId] == None):
            try:
                self._cameraList[cameraId] = cv.CaptureFromCAM(cameraId)
                self._bufferdImages[cameraId] = cv.QueryFrame(self._cameraList[cameraId])
                self._cameraFrameRates[cameraId] = int(cv.GetCaptureProperty(self._cameraList[cameraId], cv.CV_CAP_PROP_FPS))
            except:
                return False # Failed to open camera id.
        return True

    def getFirstImage(self, cameraId):
        return self.getCameraImage(cameraId, None)

    def getFrameRate(self, cameraId):
        return self._cameraFrameRates[cameraId]

    def getCameraImage(self, cameraId, timeStamp):
        if(self._cameraList[cameraId] == None):
            return self._bufferdImages[cameraId]
        minNumCamearas = cameraId + 1
        if(minNumCamearas > len(self._cameraList)):
            print "ERROR: Camera with id %d is not initialized! We only got %d number of cameras." %(minNumCamearas, len(self._cameraList))
            return None
        if((timeStamp != None) and (self._cameraTimeStamps[cameraId] != timeStamp)):
            self._bufferdImages[cameraId] = cv.QueryFrame(self._cameraList[cameraId])
            self._cameraTimeStamps[cameraId] = timeStamp
#        else:
#            print "DEBUG: using buffered image!!!"
        return self._bufferdImages[cameraId]

videoCaptureCameras = VideoCaptureCameras()
openCvCameras = OpenCvCameras()

class CameraInput(MediaFile):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
        self._cameraId = int(fileName)
        self._getConfiguration()
        self._cameraMode = self.CameraModes.OpenCV
        self._cropMode = "Crop"
        self._configurationTree.addTextParameter("DisplayMode", "Crop")
        self._getConfiguration()

    def _setupMediaSettingsHolder(self, mediaSettingsHolder):
        MediaFile._setupMediaSettingsHolder(self, mediaSettingsHolder)
        mediaSettingsHolder.zoomResizeMat = createMat(self._internalResolutionX, self._internalResolutionY)

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
        self._cropMode = self._configurationTree.getValue("DisplayMode")

    class CameraModes():
        OpenCV, VideoCapture = range(2)

    def getType(self):
        return "Camera"

    def close(self):
        pass

    def skipFrames(self, mediaSettingsHolder, currentSongPosition, midiNoteState, midiChannelState):
        fadeMode, fadeValue, noteDone = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState)
        if((fadeMode == FadeMode.Black) and (fadeValue < 0.00001)):
            mediaSettingsHolder.image = None
            return noteDone
        if(self._cameraMode == self.CameraModes.OpenCV):
            mediaSettingsHolder.captureImage = openCvCameras.getCameraImage(self._cameraId, currentSongPosition)
        else:
            mediaSettingsHolder.captureImage = videoCaptureCameras.getCameraImage(self._cameraId, currentSongPosition)

        if(self._cropMode != "Stretch"):
            imageSize = cv.GetSize(mediaSettingsHolder.captureImage)
            xRatio = float(imageSize[0]) / self._internalResolutionX
            yRatio = float(imageSize[1]) / self._internalResolutionY
            if(self._cropMode == "Crop"):
                left = 0
                top = 0
                if(xRatio > yRatio):
                    xSize = int(imageSize[0] / xRatio * yRatio)
                    ySize = imageSize[1]
                else:
                    xSize = imageSize[0]
                    ySize = int(imageSize[1] / yRatio * xRatio)
                if(xSize < imageSize[0]):
                    left = int((imageSize[0] - xSize) / 2)
                if(ySize < imageSize[1]):
                    top = int((imageSize[1] - ySize) / 2)
                src_region = cv.GetSubRect(mediaSettingsHolder.captureImage, (left, top, xSize, ySize) )
                cv.Resize(src_region, mediaSettingsHolder.resizeMat)
                mediaSettingsHolder.captureImage = mediaSettingsHolder.resizeMat
            elif(self._cropMode == "Scale"):
                left = 0
                top = 0
                if(xRatio > yRatio):
                    xSize = self._internalResolutionX
                    ySize = int(self._internalResolutionY / xRatio * yRatio)
                else:
                    xSize = int(self._internalResolutionX / yRatio * xRatio)
                    ySize = self._internalResolutionY
                if(xSize < self._internalResolutionX):
                    left = int((self._internalResolutionX - xSize) / 2)
                if(ySize < self._internalResolutionY):
                    top = int((self._internalResolutionY - ySize) / 2)
#                print "DEBUG pcn: Scale: dst_region: " + str((left, top, xSize, ySize))
                dst_region = cv.GetSubRect(mediaSettingsHolder.resizeMat, (left, top, xSize, ySize) )
                cv.SetZero(mediaSettingsHolder.resizeMat)
                cv.Resize(mediaSettingsHolder.captureImage, dst_region)
                mediaSettingsHolder.captureImage = mediaSettingsHolder.resizeMat

        self._applyEffects(mediaSettingsHolder, currentSongPosition, midiChannelState, midiNoteState, fadeMode, fadeValue)
        return False

    def openFile(self, midiLength):
        if(self._cameraMode == self.CameraModes.OpenCV):
            if(openCvCameras.openCamera(self._cameraId, self._internalResolutionX, self._internalResolutionY) == False):
                raise MediaError("Could not open OpenCV camera with ID: %d!" %(self._cameraId))
        else:
            if(videoCaptureCameras.openCamera(self._cameraId, self._internalResolutionX, self._internalResolutionY) == False):
                raise MediaError("Could not open VideoCapture camera with ID: %d!" %(self._cameraId))
        try:
            if(self._cameraMode == self.CameraModes.OpenCV):
                self._mediaSettingsHolder.captureImage = openCvCameras.getFirstImage(self._cameraId)
            else:
                self._mediaSettingsHolder.captureImage = videoCaptureCameras.getFirstImage(self._cameraId)
        except:
            self._log.warning("Exception while opening camera with ID: %d" % (self._cameraId))
            print "Exception while opening camera with ID: %s" % (self._cameraId)
            raise MediaError("File caused exception!")
        if (self._mediaSettingsHolder.captureImage == None):
            self._log.warning("Could not read frames from camera with ID: %d" % (self._cameraId))
            print "Could not read frames from camera with ID: %d" % (self._cameraId)
            raise MediaError("Could not open camera with ID: %d!" % (self._cameraId))
        if(self._cameraMode == self.CameraModes.OpenCV):
            self._originalFrameRate = openCvCameras.getFrameRate(self._cameraId)
        self._firstImage = self._mediaSettingsHolder.captureImage
        self._log.warning("Opened camera %d with framerate %d",self._cameraId, self._originalFrameRate)
        self._fileOk = True

class KinectCameras(object):
    def __init__(self):
        self._depthTimeStamp = -1.0
        self._videoTimeStamp = -1.0
        self._depthMask = None
        self._videoImage = None
        self._convertMat = None
        self._irMask = None
        self._internalResolutionX = 800
        self._internalResolutionY = 600

    def openCamera(self, internalResolutionX, internalResolutionY):
        if(freenect == None):
            self._log.warning("Error while importing kinect!")
            print "Error while importing kinect!"
            return False # Failed to open kinect camera.
        self._internalResolutionX = internalResolutionX
        self._internalResolutionY = internalResolutionY
        if((self._depthMask == None) and (self._videoImage == None)):
            self._depthMask = createMask(self._internalResolutionX, self._internalResolutionY)
            self._videoImage = getEmptyImage(self._internalResolutionX, self._internalResolutionY)
            self._convertMat = createMat(self._internalResolutionX, self._internalResolutionY)
            try:
                depthArray, _ = freenect.sync_get_depth()
                depthCapture = cv.fromarray(depthArray.astype(numpy.uint8))
                resizeImage(depthCapture, self._depthMask)
#                depthArray, _ = freenect.sync_get_video(0, freenect.VIDEO_IR_8BIT)
                rgbImage, _ = freenect.sync_get_video()
                rgbCapture = cv.fromarray(rgbImage.astype(numpy.uint8))
                resizeImage(rgbCapture, self._videoImage)
            except:
                print "Exception while opening kinnect camera!"
                self._depthMask = None
                self._videoImage = None
                self._irMask = None
                return False
        return True

    class KinectImageTypes():
        Depth, RGB, IR = range(3)

    def getFirstImage(self):
        return self.getCameraImage(self.KinectImageTypes.Depth, None)

    def getCameraImage(self, typeId, timeStamp):
        if((self._depthMask == None) or (self._videoImage == None)):
            return None
        if((typeId == self.KinectImageTypes.RGB) or (typeId == self.KinectImageTypes.IR)):
            if((timeStamp != None) and (self._videoTimeStamp != timeStamp)):
                if(typeId == self.KinectImageTypes.IR):
                    if(self._irMask == None):
                        self._irMask = createMask(self._internalResolutionX, self._internalResolutionY)
                    irArray, _ = freenect.sync_get_video(0, freenect.VIDEO_IR_8BIT)
                    irCapture = cv.fromarray(irArray.astype(numpy.uint8))
                    resizeImage(irCapture, self._irMask)
                    cv.Merge(self._irMask, self._irMask, self._irMask, None, self._videoImage)
                else: #RGB!
                    rgbImage, _ = freenect.sync_get_video()
                    rgbCapture = cv.fromarray(rgbImage.astype(numpy.uint8))
                    resizeImage(rgbCapture, self._convertMat)
                    cv.ConvertImage(self._convertMat, self._videoImage, cv.CV_CVTIMG_SWAP_RB)
                self._videoTimeStamp = timeStamp
            return self._videoImage
        else:
            if((timeStamp != None) and (self._depthTimeStamp != timeStamp)):
                depthArray, _ = freenect.sync_get_depth()
                depthCapture = cv.fromarray(depthArray.astype(numpy.uint8))
                resizeImage(depthCapture, self._depthMask)
                self._depthTimeStamp = timeStamp
            return self._depthMask

kinectCameras = KinectCameras()
    
class KinectCameraInput(MediaFile):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
        self._cameraId = int(fileName)
        self._blackFilterModulationId = -1
        self._diffFilterModulationId = -1
        self._erodeFilterModulationId = -1
        self._midiModulation = MidiModulation(self._configurationTree, self._midiTiming, self._specialModulationHolder)
        self._midiModulation.setModulationReceiver("DisplayModeModulation", "None")
        self._configurationTree.addTextParameter("FilterValues", "0.0|0.0|0.0")
        self._kinectModesHolder = KinectMode()
        self._getConfiguration()
        self._filterValues = 0.0, 0.0, 0.0
        self._modeModulationId = None

    def _setupMediaSettingsHolder(self, mediaSettingsHolder):
        MediaFile._setupMediaSettingsHolder(self, mediaSettingsHolder)
        mediaSettingsHolder.tmpMat1 = createMask(self._internalResolutionX, self._internalResolutionY)
        mediaSettingsHolder.tmpMat2 = createMask(self._internalResolutionX, self._internalResolutionY)

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
        self._modeModulationId = self._midiModulation.connectModulation("DisplayModeModulation")
        filterValuesString = self._configurationTree.getValue("FilterValues")
        self._filterValues = textToFloatValues(filterValuesString, 3)

    def getType(self):
        return "KinectCamera"

    def close(self):
        pass

    def releaseMedia(self, mediaSettingsHolder):
        MediaFile.releaseMedia(self, mediaSettingsHolder)

    def findKinectMode(self, currentSongPosition, midiNoteState, midiChannelState):
        value = self._midiModulation.getModlulationValue(self._modeModulationId, midiChannelState, midiNoteState, currentSongPosition, self._specialModulationHolder)
        maxValue = len(self._kinectModesHolder.getChoices()) * 0.99999999
        modeSelected = int(value*maxValue)
        return modeSelected

    def _getFilterValues(self):
        blackThreshold, diffThreshold, erodeValue = self._filterValues
        guiStates = self._guiCtrlStateHolder.getGuiContollerState(10)
        if(guiStates[0] != None):
            if(guiStates[0] > -0.5):
                blackThreshold = guiStates[0]
        if(guiStates[1] != None):
            if(guiStates[1] > -0.5):
                diffThreshold = guiStates[1]
        if(guiStates[2] != None):
            if(guiStates[2] > -0.5):
                erodeValue = guiStates[2]
        return blackThreshold, diffThreshold, erodeValue

    def skipFrames(self, mediaSettingsHolder, currentSongPosition, midiNoteState, midiChannelState):
        if(freenect == None):
            mediaSettingsHolder.image = None
            return True
        fadeMode, fadeValue, noteDone = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState)
        if((fadeMode == FadeMode.Black) and (fadeValue < 0.00001)):
            mediaSettingsHolder.image = None
            return noteDone

        kinectMode = self.findKinectMode(currentSongPosition, midiNoteState, midiChannelState)
        if(kinectMode == KinectMode.RGBImage):
            mediaSettingsHolder.captureImage = copyImage(kinectCameras.getCameraImage(kinectCameras.KinectImageTypes.RGB, currentSongPosition))
        elif(kinectMode == KinectMode.IRImage):
            mediaSettingsHolder.captureImage = copyImage(kinectCameras.getCameraImage(kinectCameras.KinectImageTypes.IR, currentSongPosition))
        elif(kinectMode == KinectMode.DepthImage):
            depthImage = kinectCameras.getCameraImage(kinectCameras.KinectImageTypes.Depth, currentSongPosition)
            cv.Merge(depthImage, depthImage, depthImage, None, mediaSettingsHolder.captureImage)
        elif(kinectMode == KinectMode.DepthMask):
            depthImage = kinectCameras.getCameraImage(kinectCameras.KinectImageTypes.Depth, currentSongPosition)
            blackThreshold, diffThreshold, erodeValue = self._getFilterValues()
            cv.CmpS(depthImage, 10 + (50 * blackThreshold), mediaSettingsHolder.tmpMat2, cv.CV_CMP_LE)
            cv.Add(depthImage, mediaSettingsHolder.tmpMat2, mediaSettingsHolder.tmpMat1)
            cv.AddS(mediaSettingsHolder.tmpMat1, 5 + (35 * diffThreshold), mediaSettingsHolder.tmpMat2)
            cv.Cmp(mediaSettingsHolder.tmpMat2, self._startDepthMat, mediaSettingsHolder.tmpMat1, cv.CV_CMP_LT)
            erodeIttrations = int(10 * erodeValue)
            if(erodeIttrations > 0):
                cv.Erode(mediaSettingsHolder.tmpMat1, mediaSettingsHolder.tmpMat2, None, erodeIttrations)
                cv.Merge(mediaSettingsHolder.tmpMat2, mediaSettingsHolder.tmpMat2, mediaSettingsHolder.tmpMat2, None, mediaSettingsHolder.captureImage)
            else:
                cv.Merge(mediaSettingsHolder.tmpMat1, mediaSettingsHolder.tmpMat1, mediaSettingsHolder.tmpMat1, None, mediaSettingsHolder.captureImage)
        elif(kinectMode == KinectMode.DepthThreshold):
            depthImage = kinectCameras.getCameraImage(kinectCameras.KinectImageTypes.Depth, currentSongPosition)
            blackThreshold, diffThreshold, erodeValue = self._getFilterValues()
            darkFilterValue = 256 - int(blackThreshold * 256)
            lightFilterValue = int(diffThreshold * 256)
            cv.CmpS(depthImage, darkFilterValue, mediaSettingsHolder.tmpMat1, cv.CV_CMP_LE)
            cv.CmpS(depthImage, lightFilterValue, mediaSettingsHolder.tmpMat2, cv.CV_CMP_GE)
            cv.Mul(mediaSettingsHolder.tmpMat1, mediaSettingsHolder.tmpMat2, mediaSettingsHolder.tmpMat1)
            cv.Merge(mediaSettingsHolder.tmpMat1, mediaSettingsHolder.tmpMat1, mediaSettingsHolder.tmpMat1, None, mediaSettingsHolder.captureImage)
        else: # (kinectMode == KinectMode.Reset):
            depthImage = kinectCameras.getCameraImage(kinectCameras.KinectImageTypes.Depth, currentSongPosition)
            blackThreshold, diffThreshold, erodeValue = self._getFilterValues()
            cv.CmpS(depthImage, 10 + (50 * blackThreshold), mediaSettingsHolder.tmpMat2, cv.CV_CMP_LE)
            cv.Add(depthImage, mediaSettingsHolder.tmpMat2, self._startDepthMat)
            cv.Merge(self._startDepthMat, mediaSettingsHolder.tmpMat1, mediaSettingsHolder.tmpMat2, None, mediaSettingsHolder.captureImage)

        self._applyEffects(mediaSettingsHolder, currentSongPosition, midiChannelState, midiNoteState, fadeMode, fadeValue)
        return False

    def openFile(self, midiLength):
        openOk = kinectCameras.openCamera(self._internalResolutionX, self._internalResolutionY)
        if(openOk == False):
            self._log.warning("Error while opening kinect camera!")
            print "Error while opening kinect camera!"
            raise MediaError("Kinect not installed correctly?")
        depthMat = kinectCameras.getFirstImage()
        if(depthMat == None):
            self._log.warning("Exception while getting first image from kinnect.")
            print "Exception while getting first image from kinnect."
            raise MediaError("File caused exception!")
        self._startDepthMat = cv.CloneMat(depthMat)
        cv.CmpS(depthMat, 20, self._mediaSettingsHolder.tmpMat2, cv.CV_CMP_LE)
        cv.Add(depthMat, self._mediaSettingsHolder.tmpMat2, self._startDepthMat)
        self._mediaSettingsHolder.captureImage = getEmptyImage(self._internalResolutionX, self._internalResolutionY)
        self._firstImage = self._mediaSettingsHolder.captureImage
        self._log.warning("Opened kinect camera %d with framerate %d",self._cameraId, self._originalFrameRate)
        self._fileOk = True

class ImageSequenceFile(MediaFile):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
        self._sequenceMode = ImageSequenceMode.Time
        self._midiModulation = MidiModulation(self._configurationTree, self._midiTiming, self._specialModulationHolder)
        self._configurationTree.addTextParameter("SequenceMode", "Time")
        self._midiModulation.setModulationReceiver("PlaybackModulation", "None")
        self._playbackModulationId = None
        self._getConfiguration()

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
        self._playbackModulationId = self._midiModulation.connectModulation("PlaybackModulation")
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

    def setStartPosition(self, startSpp, mediaSettingsHolder, songPosition, midiNoteStateHolder, midiChannelStateHolder):
        lastSpp = mediaSettingsHolder.triggerSongPosition
        if(startSpp != lastSpp):
            if(mediaSettingsHolder.firstNoteTrigger == True):
                mediaSettingsHolder.firstNoteTrigger = False
                mediaSettingsHolder.startSongPosition = startSpp
                self._resetEffects(mediaSettingsHolder, songPosition, midiNoteStateHolder, midiChannelStateHolder)
                mediaSettingsHolder.triggerSongPosition = startSpp
            else:
                mediaSettingsHolder.noteTriggerCounter += 1
                mediaSettingsHolder.triggerSongPosition = startSpp
#                print "TriggerCount: " + str(self._noteTriggerCounter) + " startSPP: " + str(startSpp) + " lastSPP: " + str(lastSpp)

    def getPlaybackModulation(self, songPosition, midiChannelStateHolder, midiNoteStateHolder, timeMultiplyer = None):
        return self._midiModulation.getModlulationValue(self._playbackModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, self._specialModulationHolder)

    def skipFrames(self, mediaStateHolder, currentSongPosition, midiNoteState, midiChannelState, timeMultiplyer = None):
        fadeMode, fadeValue, noteDone = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState)
        if((fadeMode == FadeMode.Black) and (fadeValue < 0.00001)):
            mediaStateHolder.image = None
            return noteDone

        syncLength = self._syncLength
        if(timeMultiplyer != None):
            syncLength = self._syncLength * timeMultiplyer

        lastFrame = mediaStateHolder.currentFrame
        
        if(self._sequenceMode == ImageSequenceMode.Time):
            unmodifiedFramePos = ((currentSongPosition - mediaStateHolder.startSongPosition) / syncLength) * self._numberOfFrames
            modifiedFramePos = self._timeModulatePos(unmodifiedFramePos, currentSongPosition, mediaStateHolder, midiNoteState, midiChannelState, syncLength)
            mediaStateHolder.currentFrame = int(modifiedFramePos / self._numberOfFrames) % self._numberOfFrames
        elif(self._sequenceMode == ImageSequenceMode.ReTrigger):
            mediaStateHolder.currentFrame =  (mediaStateHolder.noteTriggerCounter % self._numberOfFrames)
        elif(self._sequenceMode == ImageSequenceMode.Modulation):
            mediaStateHolder.currentFrame = int(self.getPlaybackModulation(currentSongPosition, midiChannelState, midiNoteState) * (self._numberOfFrames - 1))

        if(lastFrame != mediaStateHolder.currentFrame):
            if(self._bufferedImageList != None):
                mediaStateHolder.captureImage = self._bufferedImageList[mediaStateHolder.currentFrame]
#                print "Buffered image!!!"
            else:
                cv.SetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_POS_FRAMES, mediaStateHolder.currentFrame)
                if(mediaStateHolder.currentFrame == 0):
                    mediaStateHolder.captureImage = self._firstImage
                    self._log.debug("Setting firstframe %d", mediaStateHolder.currentFrame)
                elif(mediaStateHolder.currentFrame == 1):
                    mediaStateHolder.captureImage = self._secondImage
                    self._log.debug("Setting secondframe %d", mediaStateHolder.currentFrame)
                else:
                    mediaStateHolder.captureImage = cv.CloneImage(cv.QueryFrame(self._videoFile))
#                    mediaStateHolder.captureImage = cv.QueryFrame(self._videoFile)
                    if(mediaStateHolder.captureImage == None):
                        mediaStateHolder.captureImage = self._firstImage
            self._applyEffects(mediaStateHolder, currentSongPosition, midiChannelState, midiNoteState, fadeMode, fadeValue)
            return False
        else:
            self._log.debug("Same frame %d currentSongPosition %f", mediaStateHolder.currentFrame, currentSongPosition)
            self._applyEffects(mediaStateHolder, currentSongPosition, midiChannelState, midiNoteState, fadeMode, fadeValue)
            return False

    def openFile(self, midiLength):
        self.openVideoFile(midiLength)


class VideoLoopFile(MediaFile):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
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

    def skipFrames(self, mediaSettingsHolder, currentSongPosition, midiNoteState, midiChannelState, timeMultiplyer = None):
        fadeMode, fadeValue, noteDone = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState)
        if((fadeMode == FadeMode.Black) and (fadeValue < 0.00001)):
            mediaSettingsHolder.image = None
            return noteDone
        lastFrame = mediaSettingsHolder.currentFrame

        syncLength = self._syncLength
        if(timeMultiplyer != None):
            syncLength = self._syncLength * timeMultiplyer

        unmodifiedFramePos = ((currentSongPosition - mediaSettingsHolder.startSongPosition) / syncLength) * self._numberOfFrames
        modifiedFramePos = self._timeModulatePos(unmodifiedFramePos, currentSongPosition, mediaSettingsHolder, midiNoteState, midiChannelState, syncLength)

        framePos = int(modifiedFramePos)
        if(self._loopMode == VideoLoopMode.Normal):
            mediaSettingsHolder.currentFrame = framePos % self._numberOfFrames
        elif(self._loopMode == VideoLoopMode.Reverse):
            mediaSettingsHolder.currentFrame = -framePos % self._numberOfFrames
        elif(self._loopMode == VideoLoopMode.PingPong):
            mediaSettingsHolder.currentFrame = abs(((framePos + self._numberOfFrames) % (2 * self._numberOfFrames)) - self._numberOfFrames)
        elif(self._loopMode == VideoLoopMode.PingPongReverse):
            mediaSettingsHolder.currentFrame = abs((framePos % (2 * self._numberOfFrames)) - self._numberOfFrames)
        elif(self._loopMode == VideoLoopMode.DontLoop):
            if(framePos < self._numberOfFrames):
                mediaSettingsHolder.currentFrame = framePos
            else:
                mediaSettingsHolder.image = None
                return False
        elif(self._loopMode == VideoLoopMode.DontLoopReverse):
            if(framePos < self._numberOfFrames):
                mediaSettingsHolder.currentFrame = self._numberOfFrames - 1 - framePos
            else:
                mediaSettingsHolder.image = None
                return False
        else: #Normal
            mediaSettingsHolder.currentFrame = framePos % self._numberOfFrames

        if(lastFrame != mediaSettingsHolder.currentFrame):
            cv.SetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_POS_FRAMES, mediaSettingsHolder.currentFrame)
            if(mediaSettingsHolder.currentFrame == 0):
                mediaSettingsHolder.captureImage = self._firstImage
#                cv.SetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_POS_FRAMES, -1)
#                self._log.debug("Setting firstframe %d", mediaSettingsHolder.currentFrame)
            elif(mediaSettingsHolder.currentFrame == 1):
                mediaSettingsHolder.captureImage = self._secondImage
#                self._log.debug("Setting secondframe %d", mediaSettingsHolder.currentFrame)
            else:
                mediaSettingsHolder.captureImage = cv.CloneImage(cv.QueryFrame(self._videoFile))
                if(mediaSettingsHolder.captureImage == None):
                    mediaSettingsHolder.captureImage = self._firstImage
            self._applyEffects(mediaSettingsHolder, currentSongPosition, midiChannelState, midiNoteState, fadeMode, fadeValue)
            return False
        else:
            print "DEBUG pcn: Same frame %d for holderId %d" % (mediaSettingsHolder.currentFrame, mediaSettingsHolder._uid)
#            self._log.debug("Same frame %d currentSongPosition %f", mediaSettingsHolder.currentFrame, currentSongPosition)
            self._applyEffects(mediaSettingsHolder, currentSongPosition, midiChannelState, midiNoteState, fadeMode, fadeValue)
            return False

    def openFile(self, midiLength):
        self.openVideoFile(midiLength)

class VideoRecorderMedia(MediaFile):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
        self._videoWriter = None
        self._midiModulation = MidiModulation(self._configurationTree, self._midiTiming, self._specialModulationHolder)
        self._midiModulation.setModulationReceiver("RecordingOnModulation", "None")
        self._autoLoadStartNote = "C1"
        self._saveSubDir = "Recorder"
        self._getConfiguration()

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
        self._recOnModulationId = self._midiModulation.connectModulation("RecordingOnModulation")

    def close(self):
        pass

    def getType(self):
        return "VideoRecorder"

    def releaseMedia(self, mediaSettingsHolder):
        pass

    def setStartPosition(self, startSpp, songPosition, midiNoteStateHolder, midiChannelStateHolder):
        pass

    def skipFrames(self, mediaSettingsHolder, currentSongPosition, midiNoteState, midiChannelState, timeMultiplyer = None):
        recOnValue = self._midiModulation.getModlulationValue(self._recOnModulationId, midiChannelState, midiNoteState, currentSongPosition, self._specialModulationHolder)
        if(recOnValue > 0.5):
            recOn = True
        else:
            recOn = False
        if((recOn) and (self._videoWriter != None) and (mediaSettingsHolder.currentFrame != None)):
            cv.WriteFrame(self._videoWriter, mediaSettingsHolder.currentFrame)

        mediaSettingsHolder.currentFrame = None
        return False

    def openFile(self, midiLength):
        fourcc = cv.CV_FOURCC('M','J','P','G')
        self._videoWriter = cv.CreateVideoWriter("test.avi", fourcc, 30, (self._internalResolutionX, self._internalResolutionY))

    def mixWithImage(self, image, mixMode, mixLevel, effects, mediaSettingsHolder, currentSongPosition, midiChannelState, guiCtrlStateHolder, midiNoteState, mixMat1, mixMask):
        if(mixMode == MixMode.Default):
            mixMode = self._mixMode
        if(effects != None):
            preFx, preFxSettings, preFxCtrlVal, preFxStartVal, postFx, postFxSettings, postFxCtrlVal, postFxStartVal = effects
        else:
            preFx, preFxSettings, preFxCtrlVal, preFxStartVal, postFx, postFxSettings, postFxCtrlVal, postFxStartVal = (None, None, (None, None, None, None, None), None, None, None, (None, None, None, None, None), None)
        (self._captureImage, currentPreValues, unusedStarts) = self._applyOneEffect(image, preFx, preFxSettings, preFxCtrlVal, preFxStartVal, currentSongPosition, midiChannelState, midiNoteState, guiCtrlStateHolder, 0) #@UnusedVariable
        (self._captureImage, currentPostValues, unusedStarts) = self._applyOneEffect(image, postFx, postFxSettings, postFxCtrlVal, postFxStartVal, currentSongPosition, midiChannelState, midiNoteState, guiCtrlStateHolder, 5) #@UnusedVariable
        return (self._captureImage, currentPreValues, currentPostValues)

class ModulationMedia(MediaFile):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)

        self._modulationName = fileName

        self._midiModulation = MidiModulation(self._configurationTree, self._midiTiming, self._specialModulationHolder)
        self._midiModulation.setModulationReceiver("FirstModulation", "None")
        self._configurationTree.addTextParameter("ModulationCombiner1", "Add")
        self._midiModulation.setModulationReceiver("SecondModulation", "None")
        self._configurationTree.addTextParameter("ModulationCombiner2", "Add")
        self._midiModulation.setModulationReceiver("ThirdModulation", "None")
        self._configurationTree.addFloatParameter("MinValue", 0.0)
        self._configurationTree.addFloatParameter("MaxValue", 1.0)
        self._configurationTree.addTextParameter("Smoother", "Off")

        self._noteModulationHolder = None
        if(self._specialModulationHolder != None):
            self._noteModulationHolder = self._specialModulationHolder.getSubHolder("Note")
        self._sumModulationDestId = None
        self._firstModulationDestId = None
        self._secondModulationDestId = None
        self._thirdModulationDestId = None
        self._valueSmoother = []
        if(self._noteModulationHolder != None):
            self._sumModulationDestId = []
            self._firstModulationDestId = []
            self._secondModulationDestId = []
            self._thirdModulationDestId = []
            descSum = "Modulation;" + self._modulationName + ";Any;Sum"
            desc1st = "Modulation;" + self._modulationName + ";Any;1st"
            desc2nd = "Modulation;" + self._modulationName + ";Any;2nd"
            desc3rd = "Modulation;" + self._modulationName + ";Any;3rd"
            self._sumModulationDestId.append(self._noteModulationHolder.addModulation(descSum))
            self._firstModulationDestId.append(self._noteModulationHolder.addModulation(desc1st))
            self._secondModulationDestId.append(self._noteModulationHolder.addModulation(desc2nd))
            self._thirdModulationDestId.append(self._noteModulationHolder.addModulation(desc3rd))
            for midiChannel in range(16):
                descSum = "Modulation;" + self._modulationName + ";" + str(midiChannel + 1) + ";Sum"
                desc1st = "Modulation;" + self._modulationName + ";" + str(midiChannel + 1) + ";1st"
                desc2nd = "Modulation;" + self._modulationName + ";" + str(midiChannel + 1) + ";2nd"
                desc3rd = "Modulation;" + self._modulationName + ";" + str(midiChannel + 1) + ";3rd"
                self._sumModulationDestId.append(self._noteModulationHolder.addModulation(descSum))
                self._firstModulationDestId.append(self._noteModulationHolder.addModulation(desc1st))
                self._secondModulationDestId.append(self._noteModulationHolder.addModulation(desc2nd))
                self._thirdModulationDestId.append(self._noteModulationHolder.addModulation(desc3rd))
        self._limiterAdd = 0.0
        self._limiterMultiply = 1.0
        self._getConfiguration()
        self._lastNoteState = NoteState(0)
        self._dummyMidiControllerLatestModified = MidiControllerLatestModified()
        self._lastChannelState = MidiChannelStateHolder(1, self._dummyMidiControllerLatestModified)
        self._startSongPosition = 0.0
        self._valueSmootherLen = -1

    def _setupMediaSettingsHolder(self, mediaSettingsHolder):
        MediaFile._setupMediaSettingsHolder(self, mediaSettingsHolder)

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
        self._firstModulationId = self._midiModulation.connectModulation("FirstModulation")
        modCombiner1 = self._configurationTree.getValue("ModulationCombiner1")
        if(modCombiner1 == "Add"):
            self._modulationCombiner1 = self.AddModes.Add
        elif(modCombiner1 == "Subtract"):
            self._modulationCombiner1 = self.AddModes.Subtract
        elif(modCombiner1 == "Multiply"):
            self._modulationCombiner1 = self.AddModes.Multiply
        elif(modCombiner1 == "Mask"):
            self._modulationCombiner1 = self.AddModes.Mask
        else:
            self._modulationCombiner1 = self.AddModes.IfThenElse
        self._secondModulationId = self._midiModulation.connectModulation("SecondModulation")
        if(self._modulationCombiner1 == self.AddModes.IfThenElse):
            self._modulationCombiner2 = self.AddModes.IfThenElse
        else:
            modCombiner2 = self._configurationTree.getValue("ModulationCombiner2")
            if(modCombiner2 == "Add"):
                self._modulationCombiner2 = self.AddModes.Add
            elif(modCombiner2 == "Subtract"):
                self._modulationCombiner2 = self.AddModes.Subtract
            elif(modCombiner1 == "Mask"):
                self._modulationCombiner2 = self.AddModes.Mask
            else:
                self._modulationCombiner2 = self.AddModes.Multiply
        self._thirdModulationId = self._midiModulation.connectModulation("ThirdModulation")
        minValue = max(min(self._configurationTree.getValue("MinValue"), 1.0), 0.0)
        maxValue = max(min(self._configurationTree.getValue("MaxValue"), 1.0), 0.0)
        self._limiterAdd = minValue
        self._limiterMultiply = maxValue - minValue
        smootherMode = self._configurationTree.getValue("Smoother")
        smootherLen = 0
        if(smootherMode == "Smoothish"):
            smootherLen = 4
        if(smootherMode == "Smooth"):
            smootherLen = 16
        if(smootherMode == "Smoother"):
            smootherLen = 48
        if(smootherMode == "Smoothest"):
            smootherLen = 128
        if(smootherLen != self._valueSmootherLen):
            self._valueSmoother = []
            for _ in range(smootherLen):
                self._valueSmoother.append(-1.0)
            self._valueSmootherIndex = 0
            self._valueSmootherLen = len(self._valueSmoother)

    class AddModes():
        Add, Subtract, Multiply, Mask, IfThenElse = range(5)

    def close(self):
        pass

    def getType(self):
        return "Modulation"

    def getFileName(self):
        return self.getType() + ":" + self._modulationName

    def releaseMedia(self, mediaSettingsHolder):
        pass

    def setStartPosition(self, startSpp, mediaSettingsHolder, songPosition, midiNoteStateHolder, midiChannelStateHolder):
        lastSpp = self._startSongPosition
        mediaSettingsHolder = self._mediaSettingsHolder
        if(startSpp != lastSpp):
            self._startSongPosition = startSpp
            for i in range(self._valueSmootherLen):
                self._valueSmoother[i] = -1.0
            #discard last value and recalculate if we get a new start position:
            self._lastNoteState = midiNoteStateHolder
            self._lastChannelState = midiChannelStateHolder
            self.updateModulationValues(mediaSettingsHolder, songPosition)
        else:
            if((self._lastNoteState != midiNoteStateHolder) or (self._lastChannelState != midiChannelStateHolder)):
                #discard last value and recalculate if we get a new note or channel object:
                self._lastNoteState = midiNoteStateHolder
                self._lastChannelState = midiChannelStateHolder
                self._valueSmootherIndex = (self._valueSmootherIndex - 1) % self._valueSmootherLen

    def skipFrames(self, mediaSettingsHolder, currentSongPosition, midiNoteState, midiChannelState, timeMultiplyer = None):
        return False

    def updateModulationValues(self, mediaSettingsHolder, currentSongPosition):
        if(self._noteModulationHolder != None):
            midiNoteState = self._lastNoteState
            midiChannelState = self._lastChannelState
#            mediaSettingsHolder = self._mediaSettingsHolder
            firstValue = self._midiModulation.getModlulationValue(self._firstModulationId, midiChannelState, midiNoteState, currentSongPosition, self._specialModulationHolder)
            secondValue = self._midiModulation.getModlulationValue(self._secondModulationId, midiChannelState, midiNoteState, currentSongPosition, self._specialModulationHolder)
            thirdValue = self._midiModulation.getModlulationValue(self._thirdModulationId, midiChannelState, midiNoteState, currentSongPosition, self._specialModulationHolder)

            #Summing...
            sumValue = 0.0
            print "DEBUG pcn: firstValue: " + str(firstValue),
            if(self._modulationCombiner1 == self.AddModes.IfThenElse):
                if(firstValue > 0.5):
                    sumValue = secondValue
                else:
                    sumValue = thirdValue
            else:
                if(self._modulationCombiner1 == self.AddModes.Add):
                    print "add",
                    sumValue = firstValue + secondValue
                    sumValue = min(sumValue, 1.0)
                elif(self._modulationCombiner1 == self.AddModes.Subtract):
                    print "sub",
                    sumValue = firstValue - secondValue
                    sumValue = max(sumValue, 0.0)
                elif(self._modulationCombiner1 == self.AddModes.Mask):
                    print "mask",
                    sumValue = firstValue * secondValue
                else:
                    print "mul",
                    sumValue = (firstValue * secondValue * 2)
                    sumValue = min(sumValue, 1.0)

                print "sum1: " + str(sumValue),
                if(self._modulationCombiner2 == self.AddModes.Add):
                    print "add",
                    sumValue = sumValue + thirdValue
                    sumValue = min(sumValue, 1.0)
                elif(self._modulationCombiner2 == self.AddModes.Subtract):
                    print "sub",
                    sumValue = sumValue - thirdValue
                    sumValue = max(sumValue, 0.0)
                elif(self._modulationCombiner2 == self.AddModes.Mask):
                    print "mask",
                    sumValue = sumValue * thirdValue
                else:
                    print "mul",
                    sumValue = (sumValue * thirdValue * 2)
                    sumValue = min(sumValue, 1.0)
                print "sum2: " + str(sumValue),

            sumValue = min(max(sumValue, 0.0), 1.0)
            print "sumLim1: " + str(sumValue),
            print "self._limiterAdd: " + str(self._limiterAdd),
            print "self._limiterMultiply: " + str(self._limiterMultiply),
            if((self._limiterAdd > 0.01) or (self._limiterMultiply < 1.0)):
                sumValue = self._limiterAdd + (sumValue * self._limiterMultiply)
            print "sumLim2: " + str(sumValue),

            if(self._valueSmootherLen > 0):
                self._valueSmootherIndex = (self._valueSmootherIndex + 1) % self._valueSmootherLen
                self._valueSmoother[self._valueSmootherIndex] = sumValue
                valSum = 0.0
                numSums = 0
                for val in self._valueSmoother:
                    if(val >= 0.0):
                        valSum += val
                        numSums += 1
                sumValue = valSum / numSums
            print "sumSmooth: " + str(sumValue)

            #Publishing...
            noteMidiChannel = midiNoteState.getMidiChannel() + 1
#            print "+ " + str(self._firstModulationDestId[16]) + " + " + str(firstValue) + " + " + str(secondValue) + " + " + str(thirdValue) + "+"
            self._noteModulationHolder.setValue(self._firstModulationDestId[noteMidiChannel], firstValue)
            self._noteModulationHolder.setValue(self._secondModulationDestId[noteMidiChannel], secondValue)
            self._noteModulationHolder.setValue(self._thirdModulationDestId[noteMidiChannel], thirdValue)
            self._noteModulationHolder.setValue(self._sumModulationDestId[noteMidiChannel], sumValue)
            #Any channels:
            self._noteModulationHolder.setValue(self._firstModulationDestId[0], firstValue)
            self._noteModulationHolder.setValue(self._secondModulationDestId[0], secondValue)
            self._noteModulationHolder.setValue(self._thirdModulationDestId[0], thirdValue)
            self._noteModulationHolder.setValue(self._sumModulationDestId[0], sumValue)

    def openFile(self, midiLength):
        fontPath = findOsFontPath()
        fontPILImage, _ = generateTextImageAndMask("Mod\\n" + self._modulationName, "Arial", fontPath, 10, 255, 255, 255)
        self._mediaSettingsHolder.captureImage = pilToCvImage(fontPILImage)
        self._firstImage = self._mediaSettingsHolder.captureImage
        self._fileOk = True

    def mixWithImage(self, image, mixMode, mixLevel, effects, mediaSettingsHolder, currentSongPosition, midiChannelState, guiCtrlStateHolder, midiNoteState, mixMat1, mixMask):
        return (image, None, None)

class MediaError(Exception):
    def __init__(self, value):
        self.value = value.encode("utf-8")

    def __str__(self):
        return repr(self.value)
