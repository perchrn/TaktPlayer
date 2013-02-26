'''
Created on 12. okt. 2011

@author: pcn
'''
import os.path
from cv2 import cv #@UnresolvedImport
import numpy
from midi.MidiModulation import MidiModulation
from video.Effects import createMat, getEffectByName, getEmptyImage, createMask,\
    copyOrResizeImage, pilToCvImage, pilToCvMask, ZoomEffect, MediaError,\
    copyImage, setupEffectMemory
import hashlib
from video.media.MediaFileModes import MixMode, VideoLoopMode, ImageSequenceMode,\
    getMixModeFromName, ModulationValueMode, KinectMode, TimeModulationMode, WipeMode
import math
from utilities.FloatListText import textToFloatValues
import PIL.Image as Image
from midi.MidiUtilities import noteStringToNoteNumber
from video.media.TextRendrer import generateTextImageAndMask, findOsFontPath
from midi.MidiStateHolder import NoteState
import traceback
from video.media.ImageMixer import ImageMixer
from video.Curve import Curve
try:
    import freenect
except:
    freenect = None

def resizeImage(image, resizeMat):
    cv.Resize(image, resizeMat)
    return resizeMat

def scaleAndSave(image, osFileName, resizeMat):
    cv.Resize(image, resizeMat)
    cv.SaveImage(osFileName, resizeMat)


def imageToArray(image):
    return numpy.asarray(image)

def imageFromArray(array):
    return cv.fromarray(array)

imageMixerClass = None

class MediaFile(object):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        self._configurationTree = configurationTree
        self._effectsConfigurationTemplates = effectsConfiguration
        self._specialModulationHolder = specialModulationHolder
        self._timeModulationConfigurationTemplates = timeModulationConfiguration
        self._effectImagesConfigurationTemplates = effectImagesConfig
        self._mediaFadeConfigurationTemplates = fadeConfiguration
        self._videoDirectory = videoDir
        self.setFileName(fileName)
        self._midiTiming = midiTimingClass
        self._internalResolutionX =  internalResolutionX
        self._internalResolutionY =  internalResolutionY

        global imageMixerClass
        if(imageMixerClass == None):
            imageMixerClass = ImageMixer(self._internalResolutionX, self._internalResolutionY)
            setupEffectMemory(self._internalResolutionX, self._internalResolutionY)
        self._imageMixerClass = imageMixerClass

        self._firstImage = None
        self._firstImageMask = None
        self._secondImage = None
        self._bufferedImageList = None
        self._numberOfFrames = 0
        self._pingPongNumberOfFrames = 0
        self._originalFrameRate = 25
        self._originalTime = 0.0
        self._loopModulationMode = TimeModulationMode.Off
        self._fileOk = False

        self._configurationTree.addTextParameterStatic("Type", self.getType())
        self._configurationTree.addTextParameterStatic("FileName", self._cfgFileName)
        self._midiModulation = None
        self._setupConfiguration()

        self._curveConfig = Curve()
        self._curveMode = Curve.Off
        self._curveTableMat = cv.CreateMat(1, 256, cv.CV_8UC3)

        self._mediaSettingsHolder = MediaSettings(0)
        self._setupMediaSettingsHolder(self._mediaSettingsHolder)

    def _setupMediaSettingsHolder(self, mediaSettingsHolder):
        mediaSettingsHolder.image = None
        mediaSettingsHolder.imageMask = None
        mediaSettingsHolder.imageLevel = 1.0
        mediaSettingsHolder.captureImage = createMat(self._internalResolutionX, self._internalResolutionY)
        mediaSettingsHolder.captureMask = None
        mediaSettingsHolder.currentFrame = 0
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
            mediaSettingsHolder.guiCtrlStateHolder = None
            mediaSettingsHolder.noteId = -1
            mediaSettingsHolder.midiChannel = -1
            mediaSettingsHolder.effect1 = None
            mediaSettingsHolder.effect1StartMidiValues = (None, None, None, None, None)
            mediaSettingsHolder.effect1StartSumValues = mediaSettingsHolder.effect1StartMidiValues
            if(self._effect1Settings != None):
                mediaSettingsHolder.effect1StartValues = self._effect1Settings.getStartValues()
            else:
                mediaSettingsHolder.effect1StartValues = (0.0, 0.0, 0.0, 0.0, 0.0)
            mediaSettingsHolder.effect1OldValues = mediaSettingsHolder.effect1StartValues
            mediaSettingsHolder.effect2 = None
            mediaSettingsHolder.effect2StartMidiValues = (None, None, None, None, None)
            mediaSettingsHolder.effect2StartSumValues = mediaSettingsHolder.effect2StartMidiValues
            if(self._effect2Settings != None):
                mediaSettingsHolder.effect2StartValues = self._effect2Settings.getStartValues()
            else:
                mediaSettingsHolder.effect2StartValues = (0.0, 0.0, 0.0, 0.0, 0.0)
            mediaSettingsHolder.effect2OldValues = mediaSettingsHolder.effect2StartValues
            mediaSettingsHolder.resetEffect = True

    def _updateMediaSettingsHolder(self, mediaSettingsHolder):
        mediaSettingsHolder.image = None
        if(self.getType() != "Modulation"):
            effect1Name = self._effect1Settings.getEffectName()
            if((mediaSettingsHolder.effect1 == None) or (mediaSettingsHolder.effect1.getName() != effect1Name)):
                mediaSettingsHolder.effect1 = getEffectByName(effect1Name, self._effect1TemplateName, self._configurationTree, self._effectImagesConfigurationTemplates, self._specialModulationHolder, self._internalResolutionX, self._internalResolutionY)
            if(effect1Name == "Zoom"):
                mediaSettingsHolder.effect1.setExtraConfig(self._effect1Settings.getExtraValues())
            elif((effect1Name == "Feedback") or (effect1Name == "Repeat") or (effect1Name == "Delay")):
                mediaSettingsHolder.effect1.setExtraConfig(self._effect1Settings.getExtraValues())
            elif(effect1Name == "Edge"):
                mediaSettingsHolder.effect1.setExtraConfig(self._effect1Settings.getExtraValues())
            elif(effect1Name == "Curve"):
                mediaSettingsHolder.effect1.setExtraConfig(self._effect1Settings.getExtraValues())
            effect2Name = self._effect2Settings.getEffectName()
            if((mediaSettingsHolder.effect2 == None) or (effect2Name != self._effect2Settings.getEffectName())):
                mediaSettingsHolder.effect2 = getEffectByName(effect2Name, self._effect2TemplateName, self._configurationTree, self._effectImagesConfigurationTemplates, self._specialModulationHolder, self._internalResolutionX, self._internalResolutionY)
            if(effect2Name == "Zoom"):
                mediaSettingsHolder.effect2.setExtraConfig(self._effect2Settings.getExtraValues())
            elif((effect2Name == "Feedback") or (effect2Name == "Repeat") or (effect2Name == "Delay")):
                mediaSettingsHolder.effect2.setExtraConfig(self._effect2Settings.getExtraValues())
            elif(effect2Name == "Edge"):
                mediaSettingsHolder.effect2.setExtraConfig(self._effect2Settings.getExtraValues())
            elif(effect2Name == "Curve"):
                mediaSettingsHolder.effect2.setExtraConfig(self._effect2Settings.getExtraValues())

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
            self._configurationTree.addTextParameter("Curve", "Off")
            self._defaultFadeSettingsName = "Default"
            self._configurationTree.addTextParameter("FadeConfig", self._defaultFadeSettingsName)#Default Default
            self._fadeAndLevelSettings = self._mediaFadeConfigurationTemplates.getTemplate(self._defaultFadeSettingsName)
        self._configurationTree.addTextParameter("ModulationValuesMode", "KeepOld")#Default KeepOld
        
        self._syncLength = -1.0
        self._quantizeLength = -1.0
        self._mixMode = MixMode.Add
        self._wipeModeHolder = WipeMode()
        self._wipeSettings = WipeMode.Fade , False, (0.0)

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
            if(self._effect1Settings != None):
                self._effect1Settings.updateConfiguration()
            if((oldEffect1Name != self._effect1Settings.getEffectName()) or (oldEffect1Values != self._effect1Settings.getStartValuesString())):
                effect1StartValues = self._effect1Settings.getStartValues()
#                print "DEBUG pcn: Setting mediaSettingsHolder.effect1StartValues and mediaSettingsHolder.effect1OldValues to " + str(effect1StartValues)
                for mediaSettingsHolder in self._mediaSettingsHolder.getSettingsList():
                    mediaSettingsHolder.effect1StartValues = effect1StartValues
                    mediaSettingsHolder.effect1OldValues = mediaSettingsHolder.effect1StartValues
                    mediaSettingsHolder.resetEffect = True

            oldEffect2Name = "None"
            oldEffect2Values = "0.0|0.0|0.0|0.0|0.0"
            if(self._effect2Settings != None):
                oldEffect2Name = self._effect2Settings.getEffectName()
                oldEffect2Values = self._effect2Settings.getStartValuesString()
            self._effect2TemplateName = self._configurationTree.getValue("Effect2Config")
            self._effect2Settings = self._effectsConfigurationTemplates.getTemplate(self._effect2TemplateName)
            if(self._effect2Settings == None):
                self._effect2Settings = self._effectsConfigurationTemplates.getTemplate(self._defaultEffect2SettingsName)
            if(self._effect2Settings != None):
                self._effect2Settings.updateConfiguration()
            if((oldEffect2Name != self._effect2Settings.getEffectName()) or (oldEffect2Values != self._effect2Settings.getStartValuesString())):
                effect2StartValues = self._effect2Settings.getStartValues()
#                print "DEBUG pcn: Setting mediaSettingsHolder.effect2StartValues and mediaSettingsHolder.effect2OldValues to " + str(effect2StartValues)
                for mediaSettingsHolder in self._mediaSettingsHolder.getSettingsList():
                    mediaSettingsHolder.effect2StartValues = effect2StartValues
                    mediaSettingsHolder.effect2OldValues = mediaSettingsHolder.effect2StartValues
                    mediaSettingsHolder.resetEffect = True

            newCurveString = self._configurationTree.getValue("Curve")
            oldCurveString = self._curveConfig.getString()
            if(newCurveString != oldCurveString):
                self._curveConfig.setString(newCurveString)
                if(oldCurveString != self._curveConfig.getString()):
                    self._curveMode = self._curveConfig.getMode()
                    if(self._curveMode != Curve.Off):
                        for i in range(256):
                            curveValues = self._curveConfig.getArray()
                            if(len(curveValues) == 3):
                                if(self._curveMode == Curve.HSV):
                                    for i in range(256):
                                        cv.Set1D(self._curveTableMat, i, (curveValues[0][i], curveValues[1][i], curveValues[2][i]))
                                else:
                                    for i in range(256):
                                        cv.Set1D(self._curveTableMat, i, (curveValues[2][i], curveValues[1][i], curveValues[0][i]))
                            else:
                                for i in range(256):
                                    cv.Set1D(self._curveTableMat, i, (curveValues[i], curveValues[i], curveValues[i]))

            fadeAndLevelTemplate = self._configurationTree.getValue("FadeConfig")
            self._fadeAndLevelSettings = self._mediaFadeConfigurationTemplates.getTemplate(fadeAndLevelTemplate)
            if(self._fadeAndLevelSettings == None):
                self._fadeAndLevelSettings = self._mediaFadeConfigurationTemplates.getTemplate(self._defaultFadeSettingsName)
            self._wipeSettings = self._fadeAndLevelSettings.getWipeSettings()

            mixMode = self._configurationTree.getValue("MixMode")
            self._mixMode = getMixModeFromName(mixMode)

        self.setMidiLengthInBeats(self._configurationTree.getValue("SyncLength"))
        self.setQuantizeInBeats(self._configurationTree.getValue("QuantizeLength"))

        for mediaSettingsHolder in self._mediaSettingsHolder.getSettingsList():
            self._updateMediaSettingsHolder(mediaSettingsHolder)

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print "mediaFile config is updated in " + self.getType()
            self._getConfiguration()
            if(self._midiModulation != None):
                self._midiModulation.checkAndUpdateFromConfiguration()
            self._configurationTree.resetConfigurationUpdated()

    def getMediaStateHolder(self):
        mediaSettingsHolder = self._mediaSettingsHolder.getSettings()
        if(mediaSettingsHolder.isNew() == True):
#            print "DEBUG pcn: getMediaStateHolder() -> new holder with id: " + str(mediaSettingsHolder._uid) + " in: " + self.getType()
            try:
                self._setupMediaSettingsHolder(mediaSettingsHolder)
                copyOrResizeImage(self._firstImage, mediaSettingsHolder.captureImage)
                if(self._firstImageMask != None):
                    mediaSettingsHolder.captureMask = self._firstImageMask
                self._updateMediaSettingsHolder(mediaSettingsHolder)
            except MediaError, mediaError:
                self._mediaSettingsHolder.delete(mediaSettingsHolder)
                traceback.print_exc()
                raise mediaError
                return None
#        else:
#            print "DEBUG pcn: getMediaStateHolder() -> old holder with id: " + str(mediaSettingsHolder._uid) + " in: " + self.getType()
        return mediaSettingsHolder

    def close(self):
        pass

    def getType(self):
        return "Unknown"

    def equalFileName(self, fileName):
        return self._cfgFileName.encode("utf-8") == fileName.encode("utf-8")

    def getFileName(self):
        return self._cfgFileName

    def getThumbnailUniqueString(self):
        return self.getFileName()

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

    def _setupGuiCtrlStateHolder(self, mediaSettingsHolder, midiNoteStateHolder, dmxStateHolder, midiChannelStateHolder):
        newNoteId = midiNoteStateHolder.getNote()
        newMidichannel = midiChannelStateHolder.getMidiChannel()
        if((mediaSettingsHolder.noteId != newNoteId) or (mediaSettingsHolder.midiChannel != newMidichannel)):
            mediaSettingsHolder.noteId = newNoteId
            mediaSettingsHolder.midiChannel = newMidichannel
            mediaSettingsHolder.guiCtrlStateHolder = midiChannelStateHolder.getGuiControllerStateHolder(newNoteId)

    def setStartPosition(self, startSpp, mediaSettingsHolder, songPosition, midiNoteStateHolder, dmxStateHolder, midiChannelStateHolder, noteIsNew):
        if(noteIsNew):
            self._setupGuiCtrlStateHolder(mediaSettingsHolder, midiNoteStateHolder, dmxStateHolder, midiChannelStateHolder)
        if((self._loopModulationMode == TimeModulationMode.TriggeredJump) or (self._loopModulationMode == TimeModulationMode.TriggeredLoop)):
            if(noteIsNew):
                if(mediaSettingsHolder.firstNoteTrigger == True):
                    mediaSettingsHolder.firstNoteTrigger = False
                    mediaSettingsHolder.startSongPosition = startSpp
                    self._resetEffects(mediaSettingsHolder, songPosition, midiNoteStateHolder, dmxStateHolder, midiChannelStateHolder)
                    mediaSettingsHolder.triggerSongPosition = startSpp
                else:
                    mediaSettingsHolder.noteTriggerCounter += 1
                    mediaSettingsHolder.triggerSongPosition = startSpp
#                print "TriggerCount: " + str(self._noteTriggerCounter) + " startSPP: " + str(startSpp) + " lastSPP: " + str(lastSpp)
        else:
            if(startSpp != mediaSettingsHolder.startSongPosition):
                mediaSettingsHolder.startSongPosition = startSpp
                self._resetEffects(mediaSettingsHolder, songPosition, midiNoteStateHolder, dmxStateHolder, midiChannelStateHolder)

    def releaseMedia(self, mediaSettingsHolder):
        if(mediaSettingsHolder.guiCtrlStateHolder != None):
            mediaSettingsHolder.guiCtrlStateHolder.resetState()
            mediaSettingsHolder.guiCtrlStateHolder = None
            mediaSettingsHolder.noteId = -1
            mediaSettingsHolder.midiChannel = -1
        mediaSettingsHolder.image = None
        mediaSettingsHolder.noteTriggerCounter = 0
        mediaSettingsHolder.lastTriggerCount = 0
        mediaSettingsHolder.firstNoteTrigger = True
        mediaSettingsHolder.triggerModificationSum = 0.0
        mediaSettingsHolder.triggerSongPosition = 0.0
        mediaSettingsHolder.release()

#    def getCurrentFramePos(self):
#        return self._currentFrame

    def _resetEffects(self, mediaSettingsHolder, songPosition, midiNoteStateHolder, dmxStateHolder, midiChannelStateHolder):
        if(self._effect1Settings.getReStartMode() != ModulationValueMode.RawInput):
            mediaSettingsHolder.effect1StartMidiValues = self._effect1Settings.getValues(songPosition, midiChannelStateHolder, midiNoteStateHolder, dmxStateHolder, self._specialModulationHolder)
            mediaSettingsHolder.effect1StartSumValues = mediaSettingsHolder.effect1StartMidiValues
        else:
            mediaSettingsHolder.effect1StartMidiValues = (None, None, None, None, None)
            mediaSettingsHolder.effect1StartSumValues = mediaSettingsHolder.effect1StartMidiValues
        if(self._effect2Settings.getReStartMode() != ModulationValueMode.RawInput):
            mediaSettingsHolder.effect2StartMidiValues = self._effect2Settings.getValues(songPosition, midiChannelStateHolder, midiNoteStateHolder, dmxStateHolder, self._specialModulationHolder)
            mediaSettingsHolder.effect2StartSumValues = mediaSettingsHolder.effect2StartMidiValues
        else:
            mediaSettingsHolder.effect2StartMidiValues = (None, None, None, None, None)
            mediaSettingsHolder.effect2StartSumValues = mediaSettingsHolder.effect2StartMidiValues
        if(self._effect1Settings.getReStartMode() == ModulationValueMode.ResetToDefault):
            mediaSettingsHolder.effect1StartValues = self._effect1Settings.getStartValues()
        else: #KeepOldValues
            mediaSettingsHolder.effect1StartValues = mediaSettingsHolder.effect1OldValues
        if(self._effect2Settings.getReStartMode() == ModulationValueMode.ResetToDefault):
            mediaSettingsHolder.effect2StartValues = self._effect2Settings.getStartValues()
        else:
            mediaSettingsHolder.effect2StartValues = mediaSettingsHolder.effect2OldValues

        if(mediaSettingsHolder.effect1 != None):
            mediaSettingsHolder.effect1.reset()
        if(mediaSettingsHolder.effect2 != None):
            mediaSettingsHolder.effect2.reset()

    def _getFadeValue(self, currentSongPosition, midiNoteState, dmxState, midiChannelState):
        noteDone = False
        fadeValue, levelValue = self._fadeAndLevelSettings.getValues(currentSongPosition, midiChannelState, midiNoteState, dmxState, self._specialModulationHolder)
        if(fadeValue > 0.999999):
            noteDone = True
        fadeValue = (1.0 - fadeValue) * (1.0 - levelValue)
        return fadeValue, noteDone

    def getEffectState(self, mediaSettingsHolder):
        if(mediaSettingsHolder == None):
            mediaSettingsHolder = self._mediaSettingsHolder
        if(mediaSettingsHolder.guiCtrlStateHolder != None):
            guiValues1 = mediaSettingsHolder.guiCtrlStateHolder.getGuiContollerState(0)
            guiValues2 = mediaSettingsHolder.guiCtrlStateHolder.getGuiContollerState(5)
        else:
            guiValues1 = (0.0, 0.0, 0.0, 0.0, 0.0)
            guiValues2 = (0.0, 0.0, 0.0, 0.0, 0.0)
        guiEffectValuesString = str(guiValues1) + ";"
        valuesString = str(mediaSettingsHolder.effect1OldValues) + ";"
        guiEffectValuesString += str(guiValues2)
        valuesString += str(mediaSettingsHolder.effect2OldValues)
        return (valuesString, guiEffectValuesString)

    def _applyOneEffect(self, image, effect, effectSettings, effectStartSumValues, effectMidiStartValues, effectStartValues, songPosition, midiChannelStateHolder, midiNoteStateHolder, dmxStateHolder, guiCtrlStateHolder, guiCtrlStateStartId):
        if(effectSettings != None):
            midiEffectVaules = effectSettings.getValues(songPosition, midiChannelStateHolder, midiNoteStateHolder, dmxStateHolder, self._specialModulationHolder)
            if(guiCtrlStateHolder != None):
                effectAmount, effectArg1, effectArg2, effectArg3, effectArg4 = guiCtrlStateHolder.updateWithGuiSettings(guiCtrlStateStartId, midiEffectVaules, effectStartValues)
            else:
                effectAmount, effectArg1, effectArg2, effectArg3, effectArg4 = (None, None, None, None, None)
#            if(effect != None):
#                print "DEBUG controller values" + str(midiEffectVaules) + " +gui" + str((effectAmount, effectArg1, effectArg2, effectArg3, effectArg4)) + " start" + str(effectStartSumValues) + " sVals" + str(effectStartValues),
            #TODO: Add mode where values must pass start values?
            effectSCV0 = None
            if(effectAmount == None):
                effectAmount = midiEffectVaules[0]
                effectSCV0 = effectMidiStartValues[0]
            if(effectAmount == effectStartSumValues[0]):
                if(effectAmount != effectStartValues[0]):
                    effectAmount = effectStartValues[0]
                    effectSCV0 = effectStartSumValues[0]
            effectSCV1 = None
            if(effectArg1 == None):
                effectArg1 = midiEffectVaules[1]
                effectSCV1 = effectMidiStartValues[1]
            if(effectArg1 == effectStartSumValues[1]):
                if(effectArg1 != effectStartValues[1]):
                    effectArg1 = effectStartValues[1]
                    effectSCV1 = effectStartSumValues[1]
            effectSCV2 = None
            if(effectArg2 == None):
                effectArg2 = midiEffectVaules[2]
                effectSCV2 = effectMidiStartValues[2]
            if(effectArg2 == effectStartSumValues[2]):
                if(effectArg2 != effectStartValues[2]):
                    effectArg2 = effectStartValues[2]
                    effectSCV2 = effectStartSumValues[2]
            effectSCV3 = None
            if(effectArg3 == None):
                effectArg3 = midiEffectVaules[3]
                effectSCV3 = effectMidiStartValues[3]
            if(effectArg3 == effectStartSumValues[3]):
                if(effectArg3 != effectStartValues[3]):
                    effectArg3 = effectStartValues[3]
                    effectSCV3 = effectStartSumValues[3]
            effectSCV4 = None
            if(effectArg4 == None):
                effectArg4 = midiEffectVaules[4]
                effectSCV4 = effectMidiStartValues[4]
            if(effectArg4 == effectStartSumValues[4]):
                if(effectArg4 != effectStartValues[4]):
                    effectArg4 = effectStartValues[4]
                    effectSCV4 = effectStartSumValues[4]
            if(effect != None):
                image = effect.applyEffect(image, songPosition, effectAmount, effectArg1, effectArg2, effectArg3, effectArg4)
#                print "DEBUG pcn: modified values" + str((effectAmount, effectArg1, effectArg2, effectArg3, effectArg4)) + " ctrl: " + str((effectSCV0, effectSCV1, effectSCV2, effectSCV3, effectSCV4))
            return (image, (effectAmount, effectArg1, effectArg2, effectArg3, effectArg4), (effectSCV0, effectSCV1, effectSCV2, effectSCV3, effectSCV4))
        else:
            return (image, (0.0, 0.0, 0.0, 0.0, 0.0), (None, None, None, None, None))

    def _applyEffects(self, mediaSettingsHolder, currentSongPosition, midiChannelState, midiNoteState, dmxState, wipeSettings, fadeValue):
        if(mediaSettingsHolder.resetEffect == True):
            mediaSettingsHolder.resetEffect = False
            self._resetEffects(mediaSettingsHolder, currentSongPosition, midiNoteState, dmxState, midiChannelState)
        if(mediaSettingsHolder.image == None):
            mediaSettingsHolder.image = copyImage(mediaSettingsHolder.captureImage)
        else:
            copyOrResizeImage(mediaSettingsHolder.captureImage, mediaSettingsHolder.image)
        if(self._curveMode != Curve.Off):
            if(self._curveMode == Curve.HSV):
                cv.CvtColor(mediaSettingsHolder.image, mediaSettingsHolder.image, cv.CV_BGR2HSV)
                cv.LUT(mediaSettingsHolder.image, mediaSettingsHolder.image, self._curveTableMat)
                cv.CvtColor(mediaSettingsHolder.image, mediaSettingsHolder.image, cv.CV_HSV2BGR)
            else:
                cv.LUT(mediaSettingsHolder.image, mediaSettingsHolder.image, self._curveTableMat)

        (mediaSettingsHolder.image, mediaSettingsHolder.effect1OldValues, mediaSettingsHolder.effect1StartSumValues) = self._applyOneEffect(mediaSettingsHolder.image, mediaSettingsHolder.effect1, self._effect1Settings, mediaSettingsHolder.effect1StartSumValues, mediaSettingsHolder.effect1StartMidiValues, mediaSettingsHolder.effect1StartValues, currentSongPosition, midiChannelState, midiNoteState, dmxState, mediaSettingsHolder.guiCtrlStateHolder, 0)
        (mediaSettingsHolder.image, mediaSettingsHolder.effect2OldValues, mediaSettingsHolder.effect2StartSumValues) = self._applyOneEffect(mediaSettingsHolder.image, mediaSettingsHolder.effect2, self._effect2Settings, mediaSettingsHolder.effect2StartSumValues, mediaSettingsHolder.effect2StartMidiValues, mediaSettingsHolder.effect2StartValues, currentSongPosition, midiChannelState, midiNoteState, dmxState, mediaSettingsHolder.guiCtrlStateHolder, 5)

        self._wipeSettings = wipeSettings
        mediaSettingsHolder.imageLevel = fadeValue

    def _timeModulatePos(self, unmodifiedFramePos, currentSongPosition, mediaSettingsHolder, midiNoteState, dmxState, midiChannelState, syncLength):
        self._loopModulationMode, modulation, speedRange, speedQuantize = self._timeModulationSettings.getValues(currentSongPosition, midiChannelState, midiNoteState, dmxState, self._specialModulationHolder)

        if(mediaSettingsHolder.guiCtrlStateHolder != None):
            guiStates = mediaSettingsHolder.guiCtrlStateHolder.getGuiContollerState(10)
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

    def skipFrames(self, mediaSettingsHolder, currentSongPosition, midiNoteState, dmxState, midiChannelState, timeMultiplyer = None):
        pass

    def openVideoFile(self, midiLength):
        filePath = self._fullFilePath
        if(os.path.isfile(filePath) == False):
            filePath = self._packageFilePath
            print "Could not find file: %s in directory: %s" % (self._cfgFileName.encode("utf-8"), self._videoDirectory)
            print "Trying " + str(self._packageFilePath)
        if (os.path.isfile(filePath) == False):
            raise MediaError("File does not exist!")
        self._videoFile = cv.CaptureFromFile(filePath.encode("utf-8"))
        try:
            captureFrame = cv.QueryFrame(self._videoFile)
            if (captureFrame == None):
                print "Could not read frames from: " + os.path.basename(self._cfgFileName.encode("utf-8"))
                raise MediaError("File could not be read!")
            self._firstImage = copyImage(captureFrame)
            copyOrResizeImage(self._firstImage, self._mediaSettingsHolder.captureImage)
            captureFrame = cv.QueryFrame(self._videoFile)
            if (captureFrame == None):
                self._secondImage = self._firstImage
            else:
                self._secondImage = copyImage(captureFrame)
        except:
            traceback.print_exc()
            print "Exception while reading: " + os.path.basename(self._cfgFileName.encode("utf-8"))
            raise MediaError("File caused exception!")
        try:
            self._numberOfFrames = int(cv.GetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_FRAME_COUNT))
            self._originalFrameRate = int(cv.GetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_FPS))
        except:
            traceback.print_exc()
            print "Exception while getting number of frames from: %s" % (os.path.basename(self._cfgFileName.encode("utf-8")))
            raise MediaError("File caused exception!")
        if(self._numberOfFrames < 20):
            try:
                self._bufferedImageList = []
                self._bufferedImageList.append(self._firstImage)
                self._bufferedImageList.append(self._secondImage)
                for i in range(self._numberOfFrames - 2): #@UnusedVariable
                    captureFrame = cv.QueryFrame(self._videoFile)
                    self._bufferedImageList.append(copyImage(captureFrame))
            except:
                traceback.print_exc()
                print "Exception while reading: " + os.path.basename(self._cfgFileName.encode("utf-8"))
                raise MediaError("File caused exception!")
        self._originalTime = float(self._numberOfFrames) / self._originalFrameRate
        self._pingPongNumberOfFrames = (2 * self._numberOfFrames) - 2
        if(midiLength != None): # Else we get length from configuration or default.
            if(midiLength <= 0.0):
                midiLength = self._midiTiming.guessMidiLength(self._originalTime)
            self.setMidiLengthInBeats(midiLength)
        print "Read file %s with %d frames, framerate %d and length %f guessed MIDI length %f" % (os.path.basename(self._cfgFileName.encode("utf-8")), self._numberOfFrames, self._originalFrameRate, self._originalTime, self._syncLength)
        self._fileOk = True

    def getThumbnailId(self, videoPosition, appDataDir, forceUpdate):
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

        filenameHash = hashlib.sha224(self.getThumbnailUniqueString().encode("utf-8")).hexdigest()
        thumbsDir = os.path.join(os.path.normpath((appDataDir)), "thumbs")
        if(os.path.exists(thumbsDir) == False):
            os.makedirs(thumbsDir)
        if(os.path.isdir(thumbsDir) == False):
            print "Error!!! thumbs directory does not exist " + thumbsDir + " cwd: " + os.getcwd()
            return None
        else:
            thumbnailName = os.path.join(thumbsDir, "%s.jpg" % (filenameHash))
            returnThumbnailName = os.path.join("thumbs", "%s.jpg" % (filenameHash))
            osFileName = os.path.normpath(thumbnailName)
            if((forceUpdate == True) or (os.path.isfile(osFileName) == False)):
                print "Thumb file does not exist. Generating... " + os.path.basename(thumbnailName)
                destWidth, destHeight = (40, 30)
                resizeMat = createMat(destWidth, destHeight)
                if(image == None):
                    print "Error! thumbnail image == None for " + self.getType() + "!"
                else:
                    scaleAndSave(image, osFileName, resizeMat)
            else:
                print "Thumb file already exist. " + os.path.basename(thumbnailName)
            return returnThumbnailName

    def openFile(self, midiLength):
        pass

    def doPostConfigurations(self):
        if(self._fileOk):
            self._getConfiguration() #Make sure we can connect to any loaded ModulationMedia

    def mixWithImage(self, image, mixMode, wipeSettings, mixLevel, effects, preCtrlValues, postCtrlValues, mediaSettingsHolder, currentSongPosition, midiChannelState, guiCtrlStateHolder, midiNoteState, dmxState, mixMat):
        if(mediaSettingsHolder.image == None):
            return (image, None, None, None, None)
        else:
            emptyStartValues = (None, None, None, None, None)
            if(mixMode == MixMode.Default):
                mixMode = self._mixMode
            wipeMode, _, _ = wipeSettings
            if(wipeMode == WipeMode.Default):
                wipeSettings = self._wipeSettings
            mixLevel = mixLevel * mediaSettingsHolder.imageLevel #update with note level
            if(effects != None):
                preFx, preFxSettings, preFxStartVal, postFx, postFxSettings, postFxStartVal = effects
            else:
                preFx, preFxSettings, preFxStartVal, postFx, postFxSettings, postFxStartVal = (None, None, None, None, None, None)
            (mediaSettingsHolder.image, currentPreValues, preEffectStartSumValues) = self._applyOneEffect(mediaSettingsHolder.image, preFx, preFxSettings, preCtrlValues, emptyStartValues, preFxStartVal, currentSongPosition, midiChannelState, midiNoteState, dmxState, guiCtrlStateHolder, 0)
            mixedImage =  self._imageMixerClass.mixImages(mixMode, wipeSettings, mixLevel, image, mediaSettingsHolder.image, mediaSettingsHolder.imageMask, mixMat)
            (mixedImage, currentPostValues, postEffectStartSumValues) = self._applyOneEffect(mixedImage, postFx, postFxSettings, postCtrlValues, emptyStartValues, postFxStartVal, currentSongPosition, midiChannelState, midiNoteState, dmxState, guiCtrlStateHolder, 5)
            return (mixedImage, currentPreValues, currentPostValues, preEffectStartSumValues, postEffectStartSumValues)

class MediaSettings(object):
    def __init__(self, uid):
        self._subSettings = None
        self._inUse = False
        self._isNew = True
        self._uid = uid

    def needsUpdate(self):
        if(self._isNew == False):
            return True
        else:
            return False

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

    def delete(self, mediaSettings):
        if(self._subSettings != None):
            if(self._subSettings == mediaSettings):
                self._subSettings = None
            else:
                self._subSettings.delete(mediaSettings)

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
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        self._mediaList = []
        MediaFile.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
        self._getMediaCallback = None
        self._noteList = fileName.split(",")
        self._groupName = fileName

        self._getConfiguration()

    def setMixMatBuffers(self, buffers):
        self._mixMat1 = buffers[0]
        self._mixMat2 = buffers[1]

    def _setupMediaSettingsHolder(self, mediaSettingsHolder):
        MediaFile._setupMediaSettingsHolder(self, mediaSettingsHolder)
        mediaSettingsHolder.mediaSettingsList = []
        for media in self._mediaList:
            mediaSettingsHolder.mediaSettingsList.append(media.getMediaStateHolder())

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
        self._timeMultiplyer = self._configurationTree.getValue("SyncLength")

    def getType(self):
        return "Group"

    def getThumbnailUniqueString(self):
        groupIdString = self._groupName + ":"
        for media in self._mediaList:
            if(groupIdString != ""):
                groupIdString += ","
            groupIdString += "," + media.getThumbnailUniqueString()
        return groupIdString

    def close(self):
        pass

    def setStartPosition(self, startSpp, mediaSettingsHolder, songPosition, midiNoteStateHolder, dmxStateHolder, midiChannelStateHolder, noteIsNew):
        if(noteIsNew):
            self._setupGuiCtrlStateHolder(mediaSettingsHolder, midiNoteStateHolder, dmxStateHolder, midiChannelStateHolder)
            mediaSettingsHolder.startSongPosition = startSpp
            self._resetEffects(mediaSettingsHolder, songPosition, midiNoteStateHolder, dmxStateHolder, midiChannelStateHolder)
            for i in range(len(self._mediaList)):
                media = self._mediaList[i]
                mediaSettings = mediaSettingsHolder.mediaSettingsList[i]
                media.setStartPosition(startSpp, mediaSettings, songPosition, midiNoteStateHolder, dmxStateHolder, midiChannelStateHolder, noteIsNew)

    def releaseMedia(self, mediaSettingsHolder):
        for i in range(len(self._mediaList)):
            media = self._mediaList[i]
            mediaSettings = mediaSettingsHolder.mediaSettingsList[i]
            media.releaseMedia(mediaSettings)
        mediaSettingsHolder.release()

    def skipFrames(self, mediaSettingsHolder, currentSongPosition, midiNoteState, dmxState, midiChannelState, timeMultiplyer = None):
        if(mediaSettingsHolder.guiCtrlStateHolder == None):
            self._setupGuiCtrlStateHolder(mediaSettingsHolder, midiNoteState, dmxState, midiChannelState)
        if(timeMultiplyer == None):
            timeMultiplyer = self._timeMultiplyer
        loopModulationMode, _, _, _ = self._timeModulationSettings.getValues(currentSongPosition, midiChannelState, midiNoteState, dmxState, self._specialModulationHolder)
        if(loopModulationMode == TimeModulationMode.SpeedModulation):
            modifiedMultiplyer = self._timeModulatePos(timeMultiplyer, currentSongPosition, mediaSettingsHolder, midiNoteState, dmxState, midiChannelState, None)
            timeMultiplyer = modifiedMultiplyer * timeMultiplyer

        fadeValue, noteDone = self._getFadeValue(currentSongPosition, midiNoteState, dmxState, midiChannelState)
        if(fadeValue < 0.00001):
            mediaSettingsHolder.image = None
            return noteDone

        for i in range(len(self._mediaList)):
            media = self._mediaList[i]
            mediaSettings = mediaSettingsHolder.mediaSettingsList[i]
            media.skipFrames(mediaSettings, currentSongPosition, midiNoteState, dmxState, midiChannelState, timeMultiplyer)

        imageMix = None
        for i in range(len(self._mediaList)):
            media = self._mediaList[i]
            mediaSettings = mediaSettingsHolder.mediaSettingsList[i]
            mixLevel = 1.0
            mixEffects = None
            guiCtrlStateHolder = None
            if(imageMix == None):
                imageTest = media.getImage(mediaSettings)
                if(imageTest != None):
                    mixMode = MixMode.Replace
                    wipeSettings = WipeMode.Default, False, (0.0)
                    imageMix, _, _, _, _ = media.mixWithImage(imageMix, mixMode, wipeSettings, mixLevel, mixEffects, None, None, mediaSettings, currentSongPosition, midiChannelState, guiCtrlStateHolder, midiNoteState, dmxState, self._mixMat1)
            else:
                mixMode = MixMode.Default
                wipeSettings = WipeMode.Default, False, (0.0)
                if(imageMix == self._mixMat1):
                    imageMix, _, _, _, _ = media.mixWithImage(imageMix, mixMode, wipeSettings, mixLevel, mixEffects, None, None, mediaSettings, currentSongPosition, midiChannelState, guiCtrlStateHolder, midiNoteState, dmxState, self._mixMat2)
                else:
                    imageMix, _, _, _, _ = media.mixWithImage(imageMix, mixMode, wipeSettings, mixLevel, mixEffects, None, None, mediaSettings, currentSongPosition, midiChannelState, guiCtrlStateHolder, midiNoteState, dmxState, self._mixMat1)

        if(imageMix != None):
            copyOrResizeImage(imageMix, mediaSettingsHolder.captureImage)
        else:
            cv.SetZero(mediaSettingsHolder.captureImage)

        self._applyEffects(mediaSettingsHolder, currentSongPosition, midiChannelState, midiNoteState, dmxState, self._wipeSettings, fadeValue)

        return False

    def setGetMediaCallback(self, callback):
        self._getMediaCallback = callback

    def openFile(self, midiLength):
        self._mediaList = []
        fontPath = findOsFontPath()
        try:
            fontPILImage, _ = generateTextImageAndMask("Group\\n" + self._groupName, "Arial", fontPath, 12, 255, 255, 255)
        except:
            traceback.print_exc()
            raise MediaError("Error generating text!")
        labelImage = pilToCvImage(fontPILImage)
        copyOrResizeImage(labelImage, self._mediaSettingsHolder.captureImage)
        self._firstImage = self._mediaSettingsHolder.captureImage
        self._fileOk = True

    def doPostConfigurations(self):
        newMediaList = []
        mediaListUpdated = False
        for i in range(len(self._noteList)):
            noteString = self._noteList[i]
            noteId = noteStringToNoteNumber(noteString)
            media = self._getMediaCallback(noteId)
            if(media != None):
                newMediaList.append(media)
            if(i < len(self._mediaList)):
                oldMedia = self._mediaList[i]
                if(oldMedia != media):
                    mediaListUpdated = True
        if(len(self._mediaList) != len(newMediaList)):
            mediaListUpdated = True
        if(mediaListUpdated == True):
            subMediaSettingsList = self._mediaSettingsHolder.getSettingsList()
            for i in range(len(subMediaSettingsList)):
                mediaSettings = subMediaSettingsList[i]
                for j in range(len(self._mediaList)):
                    media = self._mediaList[j]
                    media.releaseMedia(mediaSettings)
            self._mediaList = newMediaList
            for mediaSettings in self._mediaSettingsHolder.getSettingsList():
                if(mediaSettings.needsUpdate() == True):
                    for mediaSettingsSettings in mediaSettings.mediaSettingsList:
                        mediaSettingsSettings.release()
                    mediaSettings.mediaSettingsList = []
                    for media in self._mediaList:
                        mediaSettings.mediaSettingsList.append(media.getMediaStateHolder())
        MediaFile.doPostConfigurations(self)

class ImageFile(MediaFile):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
        self._radians360 = math.radians(360)

        self._configurationTree.addTextParameter("StartValues", "0.0|0.0|0.0")
        self._configurationTree.addTextParameter("EndValues", "0.0|0.0|0.0")
        self._configurationTree.addTextParameter("DisplayMode", "Crop")

        self._startZoom, self._startMove, self._startAngle = textToFloatValues("0.0|0.0|0.0", 3)
        self._endZoom, self._endMove, self._endAngle = textToFloatValues("0.0|0.0|0.0", 3)
        self._startX, self._startY = self._angleAndMoveToXY(self._startAngle, self._startMove)
        self._endX, self._endY = self._angleAndMoveToXY(self._endAngle, self._endMove)
        self._cropMode = "Crop"

        self._zoomResizeMat = createMat(self._internalResolutionX, self._internalResolutionY)

        self._getConfiguration()

    def _setupMediaSettingsHolder(self, mediaSettingsHolder):
        MediaFile._setupMediaSettingsHolder(self, mediaSettingsHolder)
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

    def skipFrames(self, mediaSettingsHolder, currentSongPosition, midiNoteState, dmxState, midiChannelState, timeMultiplyer = None):
        fadeValue, noteDone = self._getFadeValue(currentSongPosition, midiNoteState, dmxState, midiChannelState)
        if(fadeValue < 0.00001):
            self._image = None
            return noteDone

        if(mediaSettingsHolder.guiCtrlStateHolder == None):
            self._setupGuiCtrlStateHolder(mediaSettingsHolder, midiNoteState, dmxState, midiChannelState)

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
        modifiedPos = self._timeModulatePos(unmodifiedPos, currentSongPosition, mediaSettingsHolder, midiNoteState, dmxState, midiChannelState, syncLength)
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
        if(mediaSettingsHolder.guiCtrlStateHolder != None):
            guiStates = mediaSettingsHolder.guiCtrlStateHolder.getGuiContollerState(10)
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
#            print "DEBUG zoom: " + str(zoom) + " multiplicator: " + str(multiplicator) + " dst: " + str((0, 0, self._internalResolutionX, self._internalResolutionY))
            dst_region = cv.GetSubRect(self._zoomResizeMat, (0, 0, self._internalResolutionX, self._internalResolutionY))
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
                cv.SetZero(self._zoomResizeMat)
#                print "DEBUG pcn: scale: left: " + str(destLeft) + " top: " + str(destTop)
                dst_region = cv.GetSubRect(self._zoomResizeMat, (destLeft, destTop, destRectangleX, destRectangleY))
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
            copyOrResizeImage(self._zoomResizeMat, mediaSettingsHolder.captureImage)
        self._applyEffects(mediaSettingsHolder, currentSongPosition, midiChannelState, midiNoteState, dmxState, self._wipeSettings, fadeValue)
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
            print "Error! Could not find file: %s in directory: %s" % (self._cfgFileName.encode("utf-8"), self._videoDirectory)
            raise MediaError("File does not exist!")
        try:
            pilImage = Image.open(filePath)
            pilImage.load()
        except:
            traceback.print_exc()
            print "Exception while reading: " + os.path.basename(self._cfgFileName.encode("utf-8"))
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
        self._firstImage = pilToCvImage(pilRgb)
        if(self._firstImage == None):
            print "Could not read image from: " + os.path.basename(self._cfgFileName.encode("utf-8"))
            raise MediaError("File could not be read!")
        copyOrResizeImage(self._firstImage, self._mediaSettingsHolder.captureImage)
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
        print "Read image file %s" % (os.path.basename(self._cfgFileName.encode("utf-8")))
        self._fileOk = True

class ScrollImageFile(MediaFile):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)

        self._midiModulation = MidiModulation(self._configurationTree, self._midiTiming, self._specialModulationHolder)
        self._configurationTree.addBoolParameter("HorizontalMode", True)
        self._configurationTree.addBoolParameter("ReverseMode", False)
        self._midiModulation.setModulationReceiver("ScrollModulation", "None")
        self._scrollModulationId = None

        self._scrollResizeMat = createMat(self._internalResolutionX, self._internalResolutionY)

        self._getConfiguration()

    def _setupMediaSettingsHolder(self, mediaSettingsHolder):
        MediaFile._setupMediaSettingsHolder(self, mediaSettingsHolder)
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

    def skipFrames(self, mediaSettingsHolder, currentSongPosition, midiNoteState, dmxState, midiChannelState, timeMultiplyer = None):
        fadeValue, noteDone = self._getFadeValue(currentSongPosition, midiNoteState, dmxState, midiChannelState)
        if(fadeValue < 0.00001):
            mediaSettingsHolder.image = None
            return noteDone

        if(mediaSettingsHolder.guiCtrlStateHolder == None):
            self._setupGuiCtrlStateHolder(mediaSettingsHolder, midiNoteState, dmxState, midiChannelState)

        syncLength = self._syncLength
        if(timeMultiplyer != None):
            syncLength = self._syncLength * timeMultiplyer

        #Find scroll length.
        if(self._scrollModulationId == None):
            unmodifiedPos = (currentSongPosition - mediaSettingsHolder.startSongPosition) / syncLength
            modifiedPos = self._timeModulatePos(unmodifiedPos, currentSongPosition, mediaSettingsHolder, midiNoteState, dmxState, midiChannelState, syncLength)
            scrollLength = modifiedPos % 1.0
            if(self._isScrollModeHorizontal == True):
                scrollLength = 1.0 - scrollLength
            if(self._isScrollModeReverse == False):
                scrollLength = 1.0 - scrollLength
        else:
            scrollLength = self._midiModulation.getModlulationValue(self._scrollModulationId, midiChannelState, midiNoteState, dmxState, currentSongPosition, self._specialModulationHolder)
        if(mediaSettingsHolder.guiCtrlStateHolder != None):
            guiStates = mediaSettingsHolder.guiCtrlStateHolder.getGuiContollerState(10)
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
                    dstRegion = cv.GetSubRect(self._scrollResizeMat, (0, 0, self._internalResolutionX, self._internalResolutionY) )
                    if(self._firstImageMask != None):
                        srcRegionMask = cv.GetSubRect(self._firstImageMask, (left, 0, self._source100percentCropX, self._source100percentCropY) )
                        dstRegionMask = cv.GetSubRect(mediaSettingsHolder.scrollResizeMask, (0, 0, self._internalResolutionX, self._internalResolutionY) )
                else:
                    extraWidth = (left + self._source100percentCropX) - self._sourceX
                    destinationWidth = int((extraWidth * self._internalResolutionX) / self._source100percentCropX)
                    #Rest:
                    srcRegion = cv.GetSubRect(self._firstImage, (0, 0, extraWidth, self._source100percentCropY))
                    dstRegion = cv.GetSubRect(self._scrollResizeMat, (self._internalResolutionX - destinationWidth, 0, destinationWidth, self._internalResolutionY) )
                    cv.Resize(srcRegion, dstRegion)
                    if(self._firstImageMask != None):
                        srcRegionMask = cv.GetSubRect(self._firstImageMask, (0, 0, extraWidth, self._source100percentCropY))
                        dstRegionMask = cv.GetSubRect(mediaSettingsHolder.scrollResizeMask, (self._internalResolutionX - destinationWidth, 0, destinationWidth, self._internalResolutionY) )
                        cv.Resize(srcRegionMask, dstRegionMask)
                    #Main:
                    width = self._sourceX - left
                    srcRegion = cv.GetSubRect(self._firstImage, (left, 0, width, self._source100percentCropY))
                    dstRegion = cv.GetSubRect(self._scrollResizeMat, (0, 0, self._internalResolutionX - destinationWidth, self._internalResolutionY) )
                    if(self._firstImageMask != None):
                        srcRegionMask = cv.GetSubRect(self._firstImageMask, (left, 0, width, self._source100percentCropY))
                        dstRegionMask = cv.GetSubRect(mediaSettingsHolder.scrollResizeMask, (0, 0, self._internalResolutionX - destinationWidth, self._internalResolutionY) )
                cv.Resize(srcRegion, dstRegion)
                copyOrResizeImage(self._scrollResizeMat, mediaSettingsHolder.captureImage)
                if(self._firstImageMask != None):
                    cv.Resize(srcRegionMask, dstRegionMask)
                    mediaSettingsHolder.captureMask = mediaSettingsHolder.scrollResizeMask
                else:
                    mediaSettingsHolder.captureMask = None
            else: # self._isScrollModeHorizontal == False -> Vertical mode
                top = int(scrollLength * (self._sourceY - 1))
                if((top + self._source100percentCropY) <= self._sourceY):
                    srcRegion = cv.GetSubRect(self._firstImage, (0, top, self._source100percentCropX, self._source100percentCropY) )
                    dstRegion = cv.GetSubRect(self._scrollResizeMat, (0, 0, self._internalResolutionX, self._internalResolutionY) )
                    if(self._firstImageMask != None):
                        srcRegionMask = cv.GetSubRect(self._firstImageMask, (0, top, self._source100percentCropX, self._source100percentCropY) )
                        dstRegionMask = cv.GetSubRect(mediaSettingsHolder.scrollResizeMask, (0, 0, self._internalResolutionX, self._internalResolutionY) )
                else:
                    extraHeight = (top + self._source100percentCropY) - self._sourceY
                    destinationHeight = int((extraHeight * self._internalResolutionY) / self._source100percentCropY)
                    #Rest:
                    srcRegion = cv.GetSubRect(self._firstImage, (0, 0, self._source100percentCropX, extraHeight))
                    dstRegion = cv.GetSubRect(self._scrollResizeMat, (0, self._internalResolutionY - destinationHeight, self._internalResolutionX, destinationHeight) )
                    cv.Resize(srcRegion, dstRegion)
                    if(self._firstImageMask != None):
                        srcRegionMask = cv.GetSubRect(self._firstImageMask, (0, 0, self._source100percentCropX, extraHeight))
                        dstRegionMask = cv.GetSubRect(mediaSettingsHolder.scrollResizeMask, (0, self._internalResolutionY - destinationHeight, self._internalResolutionX, destinationHeight) )
                        cv.Resize(srcRegionMask, dstRegionMask)
                    #Main:
                    height = self._sourceY - top
                    srcRegion = cv.GetSubRect(self._firstImage, (0, top, self._source100percentCropX, height))
                    dstRegion = cv.GetSubRect(self._scrollResizeMat, (0, 0, self._internalResolutionX, self._internalResolutionY - destinationHeight) )
                    if(self._firstImageMask != None):
                        srcRegionMask = cv.GetSubRect(self._firstImageMask, (0, top, self._source100percentCropX, height))
                        dstRegionMask = cv.GetSubRect(mediaSettingsHolder.scrollResizeMask, (0, 0, self._internalResolutionX, self._internalResolutionY - destinationHeight) )
                cv.Resize(srcRegion, dstRegion)
                copyOrResizeImage(self._scrollResizeMat, mediaSettingsHolder.captureImage)
                if(self._firstImageMask != None):
                    cv.Resize(srcRegionMask, dstRegionMask)
                    mediaSettingsHolder.captureMask = mediaSettingsHolder.scrollResizeMask
                else:
                    mediaSettingsHolder.captureMask = None

        mediaSettingsHolder.imageMask = mediaSettingsHolder.captureMask
        self._applyEffects(mediaSettingsHolder, currentSongPosition, midiChannelState, midiNoteState, dmxState, self._wipeSettings, fadeValue)
        return False

    def openFile(self, midiLength):
        filePath = self._fullFilePath
        if(os.path.isfile(filePath) == False):
            filePath = self._packageFilePath
        if (os.path.isfile(filePath) == False):
            print "Could not find file: %s in directory: %s" % (self._cfgFileName.encode("utf-8"), self._videoDirectory)
            raise MediaError("File does not exist!")
        try:
            pilImage = Image.open(filePath)
            pilImage.load()
        except:
            traceback.print_exc()
            print "Exception while reading: " + os.path.basename(self._cfgFileName.encode("utf-8"))
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
        self._firstImage = pilToCvImage(pilRgb)
        if(pilMask != None):
            self._mediaSettingsHolder.captureMask = pilToCvMask(pilMask, maskThreshold)
        else:
            self._mediaSettingsHolder.captureMask = None
        if (self._firstImage == None):
            print "Could not read image from: " + os.path.basename(self._cfgFileName.encode("utf-8"))
            raise MediaError("File could not be read!")
        copyOrResizeImage(self._firstImage, self._mediaSettingsHolder.captureImage)
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
        print "Read image file %s" % (os.path.basename(self._cfgFileName.encode("utf-8")))
        self._fileOk = True

class SpriteMediaBase(MediaFile):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)

        self._midiModulation = MidiModulation(self._configurationTree, self._midiTiming, self._specialModulationHolder)
        self._configurationTree.addTextParameter("StartPosition", "0.5|0.5|0.0")
        self._configurationTree.addTextParameter("EndPosition", "0.5|0.5|0.0")
        self._midiModulation.setModulationReceiver("XModulation", "None")
        self._midiModulation.setModulationReceiver("YModulation", "None")
        self._midiModulation.setModulationReceiver("ZModulation", "None")
        self._startX, self._startY, self._startZ = textToFloatValues("0.5|0.5|0.0", 3)
        self._endX, self._endY, self._endZ = textToFloatValues("0.5|0.5|0.0", 3)
        self._xModulationId = None
        self._yModulationId = None
        self._zModulationId = None

        self._bufferedImageList = []
        self._bufferedImageMasks = []

        self._spritePlacementMat = createMat(self._internalResolutionX, self._internalResolutionY)

        self._getConfiguration()

    def _setupMediaSettingsHolder(self, mediaSettingsHolder):
        MediaFile._setupMediaSettingsHolder(self, mediaSettingsHolder)
        mediaSettingsHolder.spritePlacementMask = createMask(self._internalResolutionX, self._internalResolutionY)
        mediaSettingsHolder.oldX = -2.0
        mediaSettingsHolder.oldY = -2.0
        mediaSettingsHolder.oldZ = -2.0
        mediaSettingsHolder.oldCurrentFrame = -1

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
        startValuesString = self._configurationTree.getValue("StartPosition")
        self._startX, self._startY, self._startZ = textToFloatValues(startValuesString, 3)
        endValuesString = self._configurationTree.getValue("EndPosition")
        self._endX, self._endY, self._endZ = textToFloatValues(endValuesString, 3)
        self._xModulationId = self._midiModulation.connectModulation("XModulation")
        self._yModulationId = self._midiModulation.connectModulation("YModulation")
        self._zModulationId = self._midiModulation.connectModulation("ZModulation")

    def getType(self):
        return "SpriteMediaBase"

    def close(self):
        pass

    def skipFrames(self, mediaSettingsHolder, currentSongPosition, midiNoteState, dmxState, midiChannelState, timeMultiplyer = None):
        fadeValue, noteDone = self._getFadeValue(currentSongPosition, midiNoteState, dmxState, midiChannelState)
        if(fadeValue < 0.00001):
            mediaSettingsHolder.image = None
            return noteDone

        if(mediaSettingsHolder.guiCtrlStateHolder == None):
            self._setupGuiCtrlStateHolder(mediaSettingsHolder, midiNoteState, dmxState, midiChannelState)

        syncLength = self._syncLength
        if(timeMultiplyer != None):
            syncLength = self._syncLength * timeMultiplyer

        #Find pos.
        posX = 0.5
        posY = 0.5
        posZ = 0.0
        modulationIsActive = False
        if((self._xModulationId != None)):
            posX = self._midiModulation.getModlulationValue(self._xModulationId, midiChannelState, midiNoteState, dmxState, currentSongPosition, self._specialModulationHolder)
            modulationIsActive = True
        if((self._yModulationId != None)):
            posY = self._midiModulation.getModlulationValue(self._yModulationId, midiChannelState, midiNoteState, dmxState, currentSongPosition, self._specialModulationHolder)
            modulationIsActive = True
        if((self._zModulationId != None)):
            posZ = self._midiModulation.getModlulationValue(self._zModulationId, midiChannelState, midiNoteState, dmxState, currentSongPosition, self._specialModulationHolder)
            modulationIsActive = True

        if(modulationIsActive == False):
            posX = self._startX
            posY = self._startY
            posZ = self._startZ
            unmodifiedPos = (currentSongPosition - mediaSettingsHolder.startSongPosition) / syncLength
            modifiedPos = self._timeModulatePos(unmodifiedPos, currentSongPosition, mediaSettingsHolder, midiNoteState, dmxState, midiChannelState, syncLength)
            if(modifiedPos >= 1.0):
                posX = self._endX
                posY = self._endY
                posZ = self._endZ
            elif(mediaSettingsHolder.startSongPosition < currentSongPosition):
                if(self._endX != self._startX):
                    posX = self._startX + ((self._endX - self._startX) * modifiedPos)
                if(self._endY != self._startY):
                    posY = self._startY + ((self._endY - self._startY) * modifiedPos)
                if(self._endZ != self._startZ):
                    posZ = self._startZ + ((self._endZ - self._startZ) * modifiedPos)

        if(mediaSettingsHolder.guiCtrlStateHolder != None):
            guiStates = mediaSettingsHolder.guiCtrlStateHolder.getGuiContollerState(10)
            if(guiStates[0] != None):
                if(guiStates[0] > -0.5):
                    posX = guiStates[0]
            if(guiStates[1] != None):
                if(guiStates[1] > -0.5):
                    posY = guiStates[1]
            if(guiStates[2] != None):
                if(guiStates[2] > -0.5):
                    posZ = guiStates[2]

        #Select frame.
        if(self._numberOfFrames == 1):
            mediaSettingsHolder.currentFrame = 0
        else:
            unmodifiedFramePos = ((currentSongPosition - mediaSettingsHolder.startSongPosition) / syncLength) * self._numberOfFrames
            mediaSettingsHolder.currentFrame = int(unmodifiedFramePos) % self._numberOfFrames

        #Scroll image + mask
        if((posX != mediaSettingsHolder.oldX) or (posY != mediaSettingsHolder.oldY) or (posZ != mediaSettingsHolder.oldZ) or (mediaSettingsHolder.currentFrame != mediaSettingsHolder.oldCurrentFrame)):
            mediaSettingsHolder.oldX = posX
            mediaSettingsHolder.oldY = posY
            mediaSettingsHolder.oldZ = posZ
            zoom = 1.0 - posZ
            mediaSettingsHolder.oldCurrentFrame = mediaSettingsHolder.currentFrame
            cv.SetZero(self._spritePlacementMat)
            cv.SetZero(mediaSettingsHolder.spritePlacementMask)
            if(zoom > 0.001):
                currentSource = self._bufferedImageList[mediaSettingsHolder.currentFrame]
                currentSourceMask = self._bufferedImageMasks[mediaSettingsHolder.currentFrame]
                sourceX, sourceY = cv.GetSize(currentSource)
                width = int(sourceX * zoom)
                height = int(sourceY * zoom)
                xMovmentRange = self._internalResolutionX + sourceX
                yMovmentRange = self._internalResolutionY + sourceX
                left = int(xMovmentRange * posX) - sourceX
                top = int(yMovmentRange * (1.0 - posY)) - sourceX
                if(zoom < 1.0):
                    left = left + int((sourceX - width) / 2)
                    top = top + int((sourceY - height) / 2)
                sourceLeft = 0
                sourceTop = 0
                sourceWidth = sourceX
                sourceHeight = sourceY
                if(left < 0):
                    sourceLeft = -int(left / zoom)
                    sourceWidth = sourceWidth + int(left / zoom)
                    width = width + left
                    left = 0
                elif((left + width) > self._internalResolutionX):
                    overflow = (left + width - self._internalResolutionX)
                    sourceWidth = sourceWidth - int(overflow / zoom)
                    width = width - overflow
                if(top < 0):
                    sourceTop = -int(top / zoom)
                    sourceHeight = sourceHeight + int(top / zoom)
                    height = height + top
                    top = 0
                elif((top + height) > self._internalResolutionY):
                    overflow = (top + height - self._internalResolutionY)
                    sourceHeight = sourceHeight - int(overflow / zoom)
                    height = height - overflow
                if(sourceWidth > sourceX):
                    sourceWidth = sourceX
                if(sourceHeight > sourceY):
                    sourceHeight = sourceY
                if((width > 0) and (height > 0)):
                    srcRegion = cv.GetSubRect(currentSource, (sourceLeft, sourceTop, sourceWidth, sourceHeight))
                    dstRegion = cv.GetSubRect(self._spritePlacementMat, (left, top, width, height))
                    cv.Resize(srcRegion, dstRegion)
                    srcRegion = cv.GetSubRect(currentSourceMask, (sourceLeft, sourceTop, sourceWidth, sourceHeight))
                    dstRegion = cv.GetSubRect(mediaSettingsHolder.spritePlacementMask, (left, top, width, height))
                    cv.Resize(srcRegion, dstRegion)
            copyOrResizeImage(self._spritePlacementMat, mediaSettingsHolder.captureImage)
            mediaSettingsHolder.captureMask = mediaSettingsHolder.spritePlacementMask

        mediaSettingsHolder.imageMask = mediaSettingsHolder.captureMask
        self._applyEffects(mediaSettingsHolder, currentSongPosition, midiChannelState, midiNoteState, dmxState, self._wipeSettings, fadeValue)
        return False

    def openFile(self, midiLength):
        pass

class SpriteImageFile(SpriteMediaBase):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        SpriteMediaBase.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
        self._configurationTree.addBoolParameter("InvertFirstFrameMask", False)
        self._invertFirstImageMask = False
        self._getConfiguration()

    def _getConfiguration(self):
        SpriteMediaBase._getConfiguration(self)
        if(self._fileOk):
            oldInvState = self._invertFirstImageMask
            self._invertFirstImageMask = self._configurationTree.getValue("InvertFirstFrameMask")
            if(oldInvState != self._invertFirstImageMask):
#                print "InvertFirstFrameMask is updated -> Sprite is re-loaded."
                self._loadFile()

    def getType(self):
        return "Sprite"

    def _loadFile(self):
        filePath = self._fullFilePath
        if(os.path.isfile(filePath) == False):
            filePath = self._packageFilePath
        if (os.path.isfile(filePath) == False):
            print "Could not find file: %s in directory: %s" % (self._cfgFileName.encode("utf-8"), self._videoDirectory)
            raise MediaError("File does not exist!")
        try:
            pilImage = Image.open(filePath)
            pilImage.load()
        except:
            traceback.print_exc()
            print "Exception while reading: " + os.path.basename(self._cfgFileName.encode("utf-8"))
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
        self._firstImage = pilToCvImage(pilRgb)
        if(pilMask != None):
            self._mediaSettingsHolder.captureMask = pilToCvMask(pilMask, maskThreshold)
        else:
            sizeX, sizeY = cv.GetSize(self._firstImage)
            captureMask = createMask(sizeX, sizeY)
            cv.Set(captureMask, 255)
            self._mediaSettingsHolder.captureMask = captureMask
        if (self._firstImage == None):
            print "Could not read image from: " + os.path.basename(self._cfgFileName.encode("utf-8"))
            raise MediaError("File could not be read!")
        self._bufferedImageList.append(self._firstImage)
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
        copyOrResizeImage(self._firstImage, self._mediaSettingsHolder.captureImage)
        self._firstImageMask = self._mediaSettingsHolder.captureMask
        self._numberOfFrames = len(self._bufferedImageList)
        self._originalTime = 1.0
        for mediaSettingsHolder in self._mediaSettingsHolder.getSettingsList():
            mediaSettingsHolder.oldCurrentFrame = -1
        print "Read image file %s" % (os.path.basename(self._cfgFileName.encode("utf-8")))

    def openFile(self, midiLength):
        self._loadFile()
        if(midiLength != None): # Else we get length from configuration or default.
            if(midiLength > 0.0):
                self.setMidiLengthInBeats(midiLength)
        self._fileOk = True

class TextMedia(SpriteMediaBase):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        SpriteMediaBase.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
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

    def getThumbnailUniqueString(self):
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

        try:
            fontPILImage, textPILMask = generateTextImageAndMask(text, startFont, self._fontPath, startSize, startRed, startGreen, startBlue)
        except:
            traceback.print_exc()
            raise MediaError("Error generating text!")
        self._firstImage = pilToCvImage(fontPILImage)
        self._mediaSettingsHolder.captureMask = pilToCvMask(textPILMask, 2)

        copyOrResizeImage(self._firstImage, self._mediaSettingsHolder.captureImage)
        self._firstImageMask = self._mediaSettingsHolder.captureMask
        self._bufferedImageList = []
        self._bufferedImageMasks = []
        self._bufferedImageList.append(self._firstImage)
        self._bufferedImageMasks.append(self._firstImageMask)
        self._numberOfFrames = len(self._bufferedImageList)
        self._originalTime = 1.0

        for mediaSettingsHolder in self._mediaSettingsHolder.getSettingsList():
            mediaSettingsHolder.oldCurrentFrame = -1
        print "Generated text media: %s" % (self._cfgFileName.encode("utf-8"))

    def openFile(self, midiLength):
#        print "DEBUG pcn: openFile -> _getConfiguration()"
        if(midiLength != None): # Else we get length from configuration or default.
            if(midiLength > 0.0):
                self.setMidiLengthInBeats(midiLength)
        self._fileOk = True
        self._getConfiguration()

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
                colourRotatedImage = createMat(pilImage.size[0], pilImage.size[1])
                cv.CvtColor(cvImage, colourRotatedImage, cv.CV_BGR2RGB)
                self._bufferdImages[cameraId] = colourRotatedImage
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
        openOk = False
        if(self._cameraList[cameraId] == None):
            try:
                self._cameraList[cameraId] = cv.CaptureFromCAM(cameraId)
                captureImage = cv.QueryFrame(self._cameraList[cameraId])
                if(captureImage != None):
                    self._bufferdImages[cameraId] = captureImage
                    openOk = True
                self._cameraFrameRates[cameraId] = int(cv.GetCaptureProperty(self._cameraList[cameraId], cv.CV_CAP_PROP_FPS))
            except:
                traceback.print_exc()
        return openOk

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
            captureImage = cv.QueryFrame(self._cameraList[cameraId])
            if(captureImage != None):
                self._bufferdImages[cameraId] = captureImage
            self._cameraTimeStamps[cameraId] = timeStamp
#        else:
#            print "DEBUG: using buffered image!!!"
        return self._bufferdImages[cameraId]

videoCaptureCameras = VideoCaptureCameras()
openCvCameras = OpenCvCameras()

class CameraInput(MediaFile):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
        self._cameraId = int(fileName)
        self._getConfiguration()
        self._cameraMode = self.CameraModes.OpenCV
        self._cropMode = "Crop"
        self._configurationTree.addTextParameter("DisplayMode", "Crop")

        self._zoomResizeMat = createMat(self._internalResolutionX, self._internalResolutionY)
        self._getConfiguration()

    def _setupMediaSettingsHolder(self, mediaSettingsHolder):
        MediaFile._setupMediaSettingsHolder(self, mediaSettingsHolder)

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
        self._cropMode = self._configurationTree.getValue("DisplayMode")

    class CameraModes():
        OpenCV, VideoCapture = range(2)

    def getType(self):
        return "Camera"

    def getThumbnailUniqueString(self):
        return self.getType() + ":" + str(self._cameraId)

    def close(self):
        pass

    def skipFrames(self, mediaSettingsHolder, currentSongPosition, midiNoteState, dmxState, midiChannelState, timeMultiplyer = None):
        fadeValue, noteDone = self._getFadeValue(currentSongPosition, midiNoteState, dmxState, midiChannelState)
        if(fadeValue < 0.00001):
            mediaSettingsHolder.image = None
            return noteDone
        if(self._cameraMode == self.CameraModes.OpenCV):
            captureImage = openCvCameras.getCameraImage(self._cameraId, currentSongPosition)
        else:
            captureImage = videoCaptureCameras.getCameraImage(self._cameraId, currentSongPosition)

        if(mediaSettingsHolder.guiCtrlStateHolder == None):
            self._setupGuiCtrlStateHolder(mediaSettingsHolder, midiNoteState, dmxState, midiChannelState)

        if(captureImage != None):
            if(self._cropMode != "Stretch"):
                imageSize = cv.GetSize(captureImage)
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
                    src_region = cv.GetSubRect(captureImage, (left, top, xSize, ySize) )
                    cv.Resize(src_region, self._zoomResizeMat)
                    copyOrResizeImage(self._zoomResizeMat, mediaSettingsHolder.captureImage)
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
                    dst_region = cv.GetSubRect(self._zoomResizeMat, (left, top, xSize, ySize) )
                    cv.SetZero(self._zoomResizeMat)
                    cv.Resize(captureImage, dst_region)
                    copyOrResizeImage(self._zoomResizeMat, mediaSettingsHolder.captureImage)

        self._applyEffects(mediaSettingsHolder, currentSongPosition, midiChannelState, midiNoteState, dmxState, self._wipeSettings, fadeValue)
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
                captureImage = openCvCameras.getFirstImage(self._cameraId)
            else:
                captureImage = videoCaptureCameras.getFirstImage(self._cameraId)
        except:
            traceback.print_exc()
            print "Exception while opening camera with ID: %s" % (self._cameraId)
            raise MediaError("File caused exception!")
        if (captureImage == None):
            print "Could not read frames from camera with ID: %d" % (self._cameraId)
            raise MediaError("Could not open camera with ID: %d!" % (self._cameraId))
        self._firstImage = copyImage(captureImage)
        if(self._cameraMode == self.CameraModes.OpenCV):
            self._originalFrameRate = openCvCameras.getFrameRate(self._cameraId)
        copyOrResizeImage(self._firstImage, self._mediaSettingsHolder.captureImage)
        print "Opened camera %d with framerate %d",self._cameraId, self._originalFrameRate
        self._fileOk = True

class RawCamera(object):
    def __init__(self, cameraId):
        self._cameraId = int(cameraId)
        self._cameraMode = self.CameraModes.OpenCV
        self._internalResolutionX = 800
        self._internalResolutionY = 600

    class CameraModes():
        OpenCV, VideoCapture = range(2)

    def getFrames(self, captureTime):
        if(self._cameraMode == self.CameraModes.OpenCV):
            captureImage = openCvCameras.getCameraImage(self._cameraId, captureTime)
        else:
            captureImage = videoCaptureCameras.getCameraImage(self._cameraId, captureTime)
        return captureImage

    def openFile(self):
        if(self._cameraMode == self.CameraModes.OpenCV):
            if(openCvCameras.openCamera(self._cameraId, self._internalResolutionX, self._internalResolutionY) == False):
                raise MediaError("Could not open OpenCV camera with ID: %d!" %(self._cameraId))
        else:
            if(videoCaptureCameras.openCamera(self._cameraId, self._internalResolutionX, self._internalResolutionY) == False):
                raise MediaError("Could not open VideoCapture camera with ID: %d!" %(self._cameraId))
        try:
            if(self._cameraMode == self.CameraModes.OpenCV):
                captureImage = openCvCameras.getFirstImage(self._cameraId)
            else:
                captureImage = videoCaptureCameras.getFirstImage(self._cameraId)
        except:
            traceback.print_exc()
            print "Exception while opening camera with ID: %s" % (self._cameraId)
            raise MediaError("File caused exception!")
        if (captureImage == None):
            print "Could not read frames from camera with ID: %d" % (self._cameraId)
            raise MediaError("Could not open camera with ID: %d!" % (self._cameraId))
        if(self._cameraMode == self.CameraModes.OpenCV):
            self._originalFrameRate = openCvCameras.getFrameRate(self._cameraId)
        print "Opened camera %d with framerate %d" %(self._cameraId, self._originalFrameRate)
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
        self._errorCount = 0

    def openCamera(self, internalResolutionX, internalResolutionY):
        if(self._errorCount > 10):
            return False
        if(freenect == None):
            print "Error while importing kinect!"
            return False # Failed to open kinect camera.
        self._internalResolutionX = internalResolutionX
        self._internalResolutionY = internalResolutionY
        if((self._depthMask == None) and (self._videoImage == None)):
            self._depthMask = createMask(self._internalResolutionX, self._internalResolutionY)
            self._videoImage = getEmptyImage(self._internalResolutionX, self._internalResolutionY)
            self._convertMat = createMat(self._internalResolutionX, self._internalResolutionY)
            try:
                depthArray, _ = freenect.sync_get_depth(0)
                depthCapture = cv.fromarray(depthArray.astype(numpy.uint8))
                resizeImage(depthCapture, self._depthMask)
#                depthArray, _ = freenect.sync_get_video(0, freenect.VIDEO_IR_8BIT)
                rgbImage, _ = freenect.sync_get_video(0)
                rgbCapture = cv.fromarray(rgbImage.astype(numpy.uint8))
                resizeImage(rgbCapture, self._videoImage)
            except:
                traceback.print_exc()
                self._errorCount += 1
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
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
        self._cameraId = int(fileName)
        self._blackFilterModulationId = -1
        self._diffFilterModulationId = -1
        self._erodeFilterModulationId = -1
        self._midiModulation = MidiModulation(self._configurationTree, self._midiTiming, self._specialModulationHolder)
#        self._midiModulation.setModulationReceiver("DisplayModeModulation", "None")
        self._configurationTree.addTextParameter("FilterValues", "0.0|0.0|0.0|0.0")
        self._configurationTree.addTextParameter("ZoomValues", "0.5|0.5|0.5|0.5")
        self._kinectModesHolder = KinectMode()
        self._zoomEffect = ZoomEffect(None, self._internalResolutionX, self._internalResolutionY)
        self._filterValues = 0.0, 0.0, 0.0, 0.0
        self._zoomValues = 0.5, 0.5, 0.5, 0.5
        self._lastGuiModesValue = -1.0
        self._getConfiguration()
#        self._modeModulationId = None

    def _setupMediaSettingsHolder(self, mediaSettingsHolder):
        MediaFile._setupMediaSettingsHolder(self, mediaSettingsHolder)
        mediaSettingsHolder.tmpMat1 = createMask(self._internalResolutionX, self._internalResolutionY)
        mediaSettingsHolder.tmpMat2 = createMask(self._internalResolutionX, self._internalResolutionY)

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
#        self._modeModulationId = self._midiModulation.connectModulation("DisplayModeModulation")
        filterValuesString = self._configurationTree.getValue("FilterValues")
        self._filterValues = textToFloatValues(filterValuesString, 4)
        zoomValuesString = self._configurationTree.getValue("ZoomValues")
        self._zoomValues = textToFloatValues(zoomValuesString, 4)

    def getType(self):
        return "KinectCamera"

    def getThumbnailUniqueString(self):
        return self.getType() + ":" + str(self._cameraId)

    def close(self):
        pass

    def releaseMedia(self, mediaSettingsHolder):
        MediaFile.releaseMedia(self, mediaSettingsHolder)

    def findKinectMode(self, value, currentSongPosition, midiNoteState, dmxState, midiChannelState):
#        value = self._midiModulation.getModlulationValue(self._modeModulationId, midiChannelState, midiNoteState, dmxState, currentSongPosition, self._specialModulationHolder)
        maxValue = len(self._kinectModesHolder.getChoices()) * 0.99999999
        modeSelected = int(value*maxValue)
        return modeSelected

    def _getFilterValues(self, mediaSettingsHolder):
        displayModeVal, blackThreshold, diffThreshold, erodeValue = self._filterValues
        if(mediaSettingsHolder.guiCtrlStateHolder != None):
            guiStates = mediaSettingsHolder.guiCtrlStateHolder.getGuiContollerState(10)
            if(guiStates[4] != None):
                if(guiStates[4] < 0.5):
                    if(guiStates[4] != self._lastGuiModesValue):
                        self._lastGuiModesValue = guiStates[4]
                        mediaSettingsHolder.guiCtrlStateHolder.resetState(10)
                        mediaSettingsHolder.guiCtrlStateHolder.controllerChange(0, 14)
                        guiStates = mediaSettingsHolder.guiCtrlStateHolder.getGuiContollerState(10)
                    if(guiStates[0] != None):
                        if(guiStates[0] > -0.5):
                            displayModeVal = guiStates[0]
                    if(guiStates[1] != None):
                        if(guiStates[1] > -0.5):
                            blackThreshold = guiStates[1]
                    if(guiStates[2] != None):
                        if(guiStates[2] > -0.5):
                            diffThreshold = guiStates[2]
                    if(guiStates[3] != None):
                        if(guiStates[3] > -0.5):
                            erodeValue = guiStates[3]
            self._filterValues = displayModeVal, blackThreshold, diffThreshold, erodeValue
        return displayModeVal, blackThreshold, diffThreshold, erodeValue

    def _getZoomValues(self, mediaSettingsHolder):
        zoomAmount, xyrate, xcenter, ycenter = self._zoomValues
        if(mediaSettingsHolder.guiCtrlStateHolder != None):
            guiStates = mediaSettingsHolder.guiCtrlStateHolder.getGuiContollerState(10)
            if(guiStates[4] != None):
                if(guiStates[4] > 0.5):
                    if(guiStates[4] != self._lastGuiModesValue):
                        self._lastGuiModesValue = guiStates[4]
                        mediaSettingsHolder.guiCtrlStateHolder.resetState(10)
                        mediaSettingsHolder.guiCtrlStateHolder.controllerChange(127, 14)
                        guiStates = mediaSettingsHolder.guiCtrlStateHolder.getGuiContollerState(10)
                    if(guiStates[0] != None):
                        if(guiStates[0] > -0.5):
                            zoomAmount = guiStates[0]
                    if(guiStates[1] != None):
                        if(guiStates[1] > -0.5):
                            xyrate = guiStates[1]
                    if(guiStates[2] != None):
                        if(guiStates[2] > -0.5):
                            xcenter = guiStates[2]
                    if(guiStates[3] != None):
                        if(guiStates[3] > -0.5):
                            ycenter = guiStates[3]
            self._zoomValues = zoomAmount, xyrate, xcenter, ycenter
        return zoomAmount, xyrate, xcenter, ycenter

    def skipFrames(self, mediaSettingsHolder, currentSongPosition, midiNoteState, dmxState, midiChannelState, timeMultiplyer = None):
        if(freenect == None):
            mediaSettingsHolder.image = None
            return True
        fadeValue, noteDone = self._getFadeValue(currentSongPosition, midiNoteState, dmxState, midiChannelState)
        if(fadeValue < 0.00001):
            mediaSettingsHolder.image = None
            return noteDone

        if(mediaSettingsHolder.guiCtrlStateHolder == None):
            self._setupGuiCtrlStateHolder(mediaSettingsHolder, midiNoteState, dmxState, midiChannelState)

        displayModeVal, blackThreshold, diffThreshold, erodeValue = self._getFilterValues(mediaSettingsHolder)
        kinectMode = self.findKinectMode(displayModeVal, currentSongPosition, midiNoteState, dmxState, midiChannelState)
        if(kinectMode == KinectMode.RGBImage):
            copyOrResizeImage(kinectCameras.getCameraImage(kinectCameras.KinectImageTypes.RGB, currentSongPosition), mediaSettingsHolder.captureImage)
        elif(kinectMode == KinectMode.IRImage):
            copyOrResizeImage(kinectCameras.getCameraImage(kinectCameras.KinectImageTypes.IR, currentSongPosition), mediaSettingsHolder.captureImage)
        elif(kinectMode == KinectMode.DepthImage):
            depthImage = kinectCameras.getCameraImage(kinectCameras.KinectImageTypes.Depth, currentSongPosition)
            cv.Merge(depthImage, depthImage, depthImage, None, mediaSettingsHolder.captureImage)
        elif(kinectMode == KinectMode.DepthMask):
            depthImage = kinectCameras.getCameraImage(kinectCameras.KinectImageTypes.Depth, currentSongPosition)
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
            darkFilterValue = 256 - int(blackThreshold * 256)
            lightFilterValue = int(diffThreshold * 256)
            cv.CmpS(depthImage, darkFilterValue, mediaSettingsHolder.tmpMat1, cv.CV_CMP_LE)
            cv.CmpS(depthImage, lightFilterValue, mediaSettingsHolder.tmpMat2, cv.CV_CMP_GE)
            cv.Mul(mediaSettingsHolder.tmpMat1, mediaSettingsHolder.tmpMat2, mediaSettingsHolder.tmpMat1)
            cv.Merge(mediaSettingsHolder.tmpMat1, mediaSettingsHolder.tmpMat1, mediaSettingsHolder.tmpMat1, None, mediaSettingsHolder.captureImage)
        else: # (kinectMode == KinectMode.Reset):
            depthImage = kinectCameras.getCameraImage(kinectCameras.KinectImageTypes.Depth, currentSongPosition)
            cv.CmpS(depthImage, 10 + (50 * blackThreshold), mediaSettingsHolder.tmpMat2, cv.CV_CMP_LE)
            cv.Add(depthImage, mediaSettingsHolder.tmpMat2, self._startDepthMat)
            cv.Zero(mediaSettingsHolder.tmpMat1)
            cv.Merge(self._startDepthMat, mediaSettingsHolder.tmpMat1, mediaSettingsHolder.tmpMat2, None, mediaSettingsHolder.captureImage)

        zoomAmount, xyrate, xcenter, ycenter = self._getZoomValues(mediaSettingsHolder)
        if((zoomAmount != 0.5) or (xyrate != 0.5)):
            mediaSettingsHolder.captureImage = self._zoomEffect.applyEffect(mediaSettingsHolder.captureImage, zoomAmount, xyrate, xcenter, ycenter, 1.0, 0.25, 0.75)
        self._applyEffects(mediaSettingsHolder, currentSongPosition, midiChannelState, midiNoteState, dmxState, self._wipeSettings, fadeValue)
        return False

    def openFile(self, midiLength):
        openOk = kinectCameras.openCamera(self._internalResolutionX, self._internalResolutionY)
        if(openOk == False):
            print "Error while opening kinect camera!"
            raise MediaError("Kinect not installed correctly?")
        depthMat = kinectCameras.getFirstImage()
        if(depthMat == None):
            print "Exception while getting first image from kinnect."
            raise MediaError("File caused exception!")
        self._startDepthMat = cv.CloneMat(depthMat)
        cv.CmpS(depthMat, 20, self._mediaSettingsHolder.tmpMat2, cv.CV_CMP_LE)
        cv.Add(depthMat, self._mediaSettingsHolder.tmpMat2, self._startDepthMat)
        fontPath = findOsFontPath()
        try:
            fontPILImage, _ = generateTextImageAndMask("Freenect\\n" + str(self._cameraId), "Arial", fontPath, 12, 255, 255, 255)
        except:
            traceback.print_exc()
            raise MediaError("Error generating text!")
        labelImage = pilToCvImage(fontPILImage)
        copyOrResizeImage(labelImage, self._mediaSettingsHolder.captureImage)
        self._firstImage = self._mediaSettingsHolder.captureImage
        print "Opened kinect camera %d with framerate %d",self._cameraId, self._originalFrameRate
        self._fileOk = True

class ImageSequenceFile(MediaFile):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
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

    def setStartPosition(self, startSpp, mediaSettingsHolder, songPosition, midiNoteStateHolder, dmxStateHolder, midiChannelStateHolder, noteIsNew):
        if(noteIsNew):
            self._setupGuiCtrlStateHolder(mediaSettingsHolder, midiNoteStateHolder, dmxStateHolder, midiChannelStateHolder)
            if(mediaSettingsHolder.firstNoteTrigger == True):
                mediaSettingsHolder.firstNoteTrigger = False
                mediaSettingsHolder.startSongPosition = startSpp
                self._resetEffects(mediaSettingsHolder, songPosition, midiNoteStateHolder, dmxStateHolder, midiChannelStateHolder)
                mediaSettingsHolder.triggerSongPosition = startSpp
            else:
                mediaSettingsHolder.noteTriggerCounter += 1
                mediaSettingsHolder.triggerSongPosition = startSpp
#                print "TriggerCount: " + str(self._noteTriggerCounter) + " startSPP: " + str(startSpp) + " lastSPP: " + str(lastSpp)

    def getPlaybackModulation(self, songPosition, midiChannelStateHolder, midiNoteStateHolder, dmxStateHolder, timeMultiplyer = None):
        return self._midiModulation.getModlulationValue(self._playbackModulationId, midiChannelStateHolder, midiNoteStateHolder, dmxStateHolder, songPosition, self._specialModulationHolder)

    def skipFrames(self, mediaSettingsHolder, currentSongPosition, midiNoteState, dmxState, midiChannelState, timeMultiplyer = None):
        fadeValue, noteDone = self._getFadeValue(currentSongPosition, midiNoteState, dmxState, midiChannelState)
        if(fadeValue < 0.00001):
            mediaSettingsHolder.image = None
            return noteDone

        if(mediaSettingsHolder.guiCtrlStateHolder == None):
            self._setupGuiCtrlStateHolder(mediaSettingsHolder, midiNoteState, dmxState, midiChannelState)

        syncLength = self._syncLength
        if(timeMultiplyer != None):
            syncLength = self._syncLength * timeMultiplyer

        lastFrame = mediaSettingsHolder.currentFrame
        
        if(self._sequenceMode == ImageSequenceMode.Time):
            unmodifiedFramePos = ((currentSongPosition - mediaSettingsHolder.startSongPosition) / syncLength) * self._numberOfFrames
            modifiedFramePos = self._timeModulatePos(unmodifiedFramePos, currentSongPosition, mediaSettingsHolder, midiNoteState, dmxState, midiChannelState, syncLength)
            mediaSettingsHolder.currentFrame = int(modifiedFramePos / self._numberOfFrames) % self._numberOfFrames
        elif(self._sequenceMode == ImageSequenceMode.ReTrigger):
            mediaSettingsHolder.currentFrame =  (mediaSettingsHolder.noteTriggerCounter % self._numberOfFrames)
        elif(self._sequenceMode == ImageSequenceMode.Modulation):
            mediaSettingsHolder.currentFrame = int(self.getPlaybackModulation(currentSongPosition, midiChannelState, midiNoteState, dmxState) * (self._numberOfFrames - 1))

        if(lastFrame != mediaSettingsHolder.currentFrame):
            if(self._bufferedImageList != None):
                copyOrResizeImage(self._bufferedImageList[mediaSettingsHolder.currentFrame], mediaSettingsHolder.captureImage)
#                print "Buffered image!!!"
            else:
                cv.SetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_POS_FRAMES, mediaSettingsHolder.currentFrame)
                if(mediaSettingsHolder.currentFrame == 0):
                    copyOrResizeImage(self._firstImage, mediaSettingsHolder.captureImage)
#                    print "Setting firstframe %d", mediaSettingsHolder.currentFrame
                elif(mediaSettingsHolder.currentFrame == 1):
                    copyOrResizeImage(self._secondImage, mediaSettingsHolder.captureImage)
#                    print "Setting secondframe %d", mediaSettingsHolder.currentFrame
                else:
                    captureFrame = cv.QueryFrame(self._videoFile)
                    if(captureFrame != None):
                        copyOrResizeImage(captureFrame, mediaSettingsHolder.captureImage)
                    else:
                        print "Warning! Bad capture! Keeping last frame instead of frame number: " + str(mediaSettingsHolder.currentFrame) + " of: " + str(self._numberOfFrames)
            self._applyEffects(mediaSettingsHolder, currentSongPosition, midiChannelState, midiNoteState, dmxState, self._wipeSettings, fadeValue)
            return False
        else:
#            print "Same frame %d currentSongPosition %f", mediaSettingsHolder.currentFrame, currentSongPosition
            self._applyEffects(mediaSettingsHolder, currentSongPosition, midiChannelState, midiNoteState, dmxState, self._wipeSettings, fadeValue)
            return False

    def openFile(self, midiLength):
        self.openVideoFile(midiLength)


class VideoLoopFile(MediaFile):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
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
        elif(loopMode == "KeepLast"):
            self._loopMode = VideoLoopMode.KeepLast
        elif(loopMode == "AdvancedLoop"):
            self._loopMode = VideoLoopMode.AdvancedLoop
        elif(loopMode == "AdvancedPingPong"):
            self._loopMode = VideoLoopMode.AdvancedPingPong
        else:
            self._loopMode = VideoLoopMode.Normal #Defaults to normal

        if((self._loopMode == VideoLoopMode.AdvancedLoop) or (self._loopMode == VideoLoopMode.AdvancedPingPong)):
            self._configurationTree.addTextParameter("AdvancedLoopValues", "0.0|0.25|0.75|1.0")
            loopValues = self._configurationTree.getValue("AdvancedLoopValues")
            self._startPos, self._loopStart, self._loopEnd, self._endPos = textToFloatValues(loopValues, 4)
        else:
            self._configurationTree.removeParameter("AdvancedLoopValues")

    def close(self):
        pass

    def getType(self):
        return "VideoLoop"

    def skipFrames(self, mediaSettingsHolder, currentSongPosition, midiNoteState, dmxState, midiChannelState, timeMultiplyer = None):
        fadeValue, noteDone = self._getFadeValue(currentSongPosition, midiNoteState, dmxState, midiChannelState)
        if(fadeValue < 0.00001):
            mediaSettingsHolder.image = None
            return noteDone
        lastFrame = mediaSettingsHolder.currentFrame

        if(mediaSettingsHolder.guiCtrlStateHolder == None):
            self._setupGuiCtrlStateHolder(mediaSettingsHolder, midiNoteState, dmxState, midiChannelState)

        syncLength = self._syncLength
        if(timeMultiplyer != None):
            syncLength = self._syncLength * timeMultiplyer

        unmodifiedFramePos = ((currentSongPosition - mediaSettingsHolder.startSongPosition) / syncLength) * self._numberOfFrames
        modifiedFramePos = self._timeModulatePos(unmodifiedFramePos, currentSongPosition, mediaSettingsHolder, midiNoteState, dmxState, midiChannelState, syncLength)

        framePos = int(modifiedFramePos)
        if(self._loopMode == VideoLoopMode.Normal):
            mediaSettingsHolder.currentFrame = framePos % self._numberOfFrames
        elif(self._loopMode == VideoLoopMode.Reverse):
            mediaSettingsHolder.currentFrame = -framePos % self._numberOfFrames
        elif(self._loopMode == VideoLoopMode.PingPong):
            mediaSettingsHolder.currentFrame = abs(((framePos + self._numberOfFrames) % (self._pingPongNumberOfFrames)) - self._numberOfFrames)
        elif(self._loopMode == VideoLoopMode.PingPongReverse):
            mediaSettingsHolder.currentFrame = abs(((framePos) % (self._pingPongNumberOfFrames)) - (self._numberOfFrames - 1))
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
        elif(self._loopMode == VideoLoopMode.KeepLast):
            if(framePos < self._numberOfFrames):
                mediaSettingsHolder.currentFrame = framePos
            else:
                mediaSettingsHolder.currentFrame = self._numberOfFrames - 1
        elif((self._loopMode == VideoLoopMode.AdvancedLoop) or (self._loopMode == VideoLoopMode.AdvancedPingPong)):
            if(self._loopMode == VideoLoopMode.AdvancedPingPong):
                pingPong = True
            else:
                pingPong = False
            positionIsFound = False
            loopPos = float(framePos) / self._numberOfFrames
            startPos = 0.0
            if(self._startPos != None):
                startPos = self._startPos
                startPos = max(0.0, min(1.0, startPos))
            loopStart = 0.0
            if(self._loopStart != None):
                loopStart = self._loopStart
                loopStart = max(0.0, min(1.0, loopStart))
            startLength = loopStart - startPos
            loopEnd = 1.0
            if(self._loopEnd != None):
                loopEnd = self._loopEnd
                loopEnd = max(0.0, min(1.0, loopEnd))
            if(pingPong == True):
                pingPongLength = (loopEnd - loopStart)
                loopLength = 2 * pingPongLength
                endStart = loopStart
            else:
                loopLength = loopEnd - loopStart
                endStart = loopEnd
            endPos = 1.0
            if(self._endPos != None):
                endPos = self._endPos
                endPos = max(0.0, min(1.0, endPos))
            endLength = endPos - endStart

#            print "DEBUG pcn: advanced: " + str(currentSongPosition) + " : " + str((loopPos, startPos, startLength, loopStart, loopLength, endStart, endLength)),
            if(loopPos < 0.0):
                loopPos = 0.0
                positionIsFound = True
            else:
                if(loopPos < abs(startLength)):
                    if(startLength < 0.0):
                        loopPos = startPos - loopPos
                    else:
                        loopPos = startPos + loopPos
                    positionIsFound = True
            if(positionIsFound == False):
                noteLength = midiNoteState.getNoteLength() / syncLength
                relativePos = loopPos - abs(startLength)
                if(noteLength > 0.0):
                    restLength = noteLength - abs(startLength)
                    if(loopLength < 0.0001):
                        loopEnd = max(restLength, 0.0)
                        loopLength = None
                    else:
                        numberOfLoops = int(restLength / abs(loopLength))
                        if((restLength > 0.0) and (restLength % abs(loopLength)) > 0.001):
                            numberOfLoops += 1
                        if(numberOfLoops == 0):
                            numberOfLoops = 1
                        loopEnd = numberOfLoops * abs(loopLength)
                    if(loopEnd > relativePos):
                        if(loopLength == None):
                            loopPos = loopStart
                        else:
                            if(pingPong == True):
                                loopSubPos = abs(((relativePos + pingPongLength) % abs(loopLength)) - pingPongLength)
                            else:
                                loopSubPos = relativePos % abs(loopLength)
                            if(loopLength < 0.0):
                                loopPos = loopStart - loopSubPos
                            else:
                                loopPos = loopStart + loopSubPos
                    else:
                        relativePos = relativePos - loopEnd
                        if(relativePos < abs(endLength)):
                            if(endLength < 0.0):
                                loopPos = endStart - relativePos
                            else:
                                loopPos = endStart + relativePos
                        else:
                            mediaSettingsHolder.image = None
                            return False
                else:
                    if(loopLength < 0.0001):
                        loopSubPos = 0.0
                    else:
                        if(pingPong == True):
                            loopSubPos = abs(((relativePos + pingPongLength) % abs(loopLength)) - pingPongLength)
                        else:
                            loopSubPos = relativePos % abs(loopLength)
                    if(loopLength < 0.0):
                        loopPos = loopStart - loopSubPos
                    else:
                        loopPos = loopStart + loopSubPos
            if((loopPos >= 0.0) and loopPos < 1.0):
                mediaSettingsHolder.currentFrame = int(loopPos * self._numberOfFrames)
#            else:
#                print "DEBUG pcn: bad pos returned from advanced loop: " + str(loopPos)
#            print " loopPos: " + str(loopPos) + " frame: " + str(mediaSettingsHolder.currentFrame)
        else: #Normal
            mediaSettingsHolder.currentFrame = framePos % self._numberOfFrames

        if(lastFrame != mediaSettingsHolder.currentFrame):
            cv.SetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_POS_FRAMES, mediaSettingsHolder.currentFrame)
            if(mediaSettingsHolder.currentFrame == 0):
                copyOrResizeImage(self._firstImage, mediaSettingsHolder.captureImage)
            elif(mediaSettingsHolder.currentFrame == 1):
                copyOrResizeImage(self._secondImage, mediaSettingsHolder.captureImage)
            else:
                captureFrame = cv.QueryFrame(self._videoFile)
                if(captureFrame != None):
                    copyOrResizeImage(captureFrame, mediaSettingsHolder.captureImage)
                else:
                    print "Warning! Bad capture! Keeping last frame instead of frame number: " + str(mediaSettingsHolder.currentFrame) + " of: " + str(self._numberOfFrames)
            self._applyEffects(mediaSettingsHolder, currentSongPosition, midiChannelState, midiNoteState, dmxState, self._wipeSettings, fadeValue)
            return False
        else:
#            print "DEBUG pcn: Same frame %d for holderId %d" % (mediaSettingsHolder.currentFrame, mediaSettingsHolder._uid)
            self._applyEffects(mediaSettingsHolder, currentSongPosition, midiChannelState, midiNoteState, dmxState, self._wipeSettings, fadeValue)
            return False

    def openFile(self, midiLength):
        self.openVideoFile(midiLength)

#class VideoRecorderMedia(MediaFile):
#    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
#        MediaFile.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
#        self._videoWriter = None
#        self._midiModulation = MidiModulation(self._configurationTree, self._midiTiming, self._specialModulationHolder)
#        self._midiModulation.setModulationReceiver("RecordingOnModulation", "None")
#        self._autoLoadStartNote = "C1"
#        self._saveSubDir = "Recorder"
#        self._getConfiguration()
#
#    def _getConfiguration(self):
#        MediaFile._getConfiguration(self)
#        self._recOnModulationId = self._midiModulation.connectModulation("RecordingOnModulation")
#
#    def close(self):
#        pass
#
#    def getType(self):
#        return "VideoRecorder"
#
#    def releaseMedia(self, mediaSettingsHolder):
#        pass
#
#    def setStartPosition(self, startSpp, songPosition, midiNoteStateHolder, dmxStateHolder, midiChannelStateHolder, noteIsNew):
#        pass
#
#    def skipFrames(self, mediaSettingsHolder, currentSongPosition, midiNoteState, dmxState, midiChannelState, timeMultiplyer = None):
#        if(mediaSettingsHolder.guiCtrlStateHolder == None):
#            self._setupGuiCtrlStateHolder(mediaSettingsHolder, midiNoteState, dmxState, midiChannelState)
#
#        recOnValue = self._midiModulation.getModlulationValue(self._recOnModulationId, midiChannelState, midiNoteState, dmxState, currentSongPosition, self._specialModulationHolder)
#        if(recOnValue > 0.5):
#            recOn = True
#        else:
#            recOn = False
#        if((recOn) and (self._videoWriter != None) and (mediaSettingsHolder.currentFrame != None)):
#            cv.WriteFrame(self._videoWriter, mediaSettingsHolder.currentFrame)
#
#        mediaSettingsHolder.currentFrame = None
#        return False
#
#    def openFile(self, midiLength):
#        fourcc = cv.CV_FOURCC('M','J','P','G')
#        self._videoWriter = cv.CreateVideoWriter("test.avi", fourcc, 30, (self._internalResolutionX, self._internalResolutionY))
#
#    def mixWithImage(self, image, mixMode, wipeMode, mixLevel, effects, preCtrlValues, postCtrlValues, mediaSettingsHolder, currentSongPosition, midiChannelState, guiCtrlStateHolder, midiNoteState, dmxState, mixMat1, mixMask):
#        if(mixMode == MixMode.Default):
#            mixMode = self._mixMode
#        emptyStartValues = (None, None, None, None, None)
#        if(effects != None):
#            preFx, preFxSettings, preFxStartVal, postFx, postFxSettings, postFxStartVal = effects
#        else:
#            preFx, preFxSettings, preFxStartVal, postFx, postFxSettings, postFxStartVal = (None, None, None, None, None, None)
#        (self._captureImage, currentPreValues, preEffectStartSumValues) = self._applyOneEffect(image, preFx, preFxSettings, preCtrlValues, emptyStartValues, preFxStartVal, currentSongPosition, midiChannelState, midiNoteState, dmxState, guiCtrlStateHolder, 0)
#        (self._captureImage, currentPostValues, postEffectStartSumValues) = self._applyOneEffect(image, postFx, postFxSettings, postCtrlValues, emptyStartValues, postFxStartVal, currentSongPosition, midiChannelState, midiNoteState, dmxState, guiCtrlStateHolder, 5)
#        return (self._captureImage, currentPreValues, currentPostValues, preEffectStartSumValues, postEffectStartSumValues)

class ModulationMedia(MediaFile):
    def __init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, timeModulationConfiguration, specialModulationHolder, effectsConfiguration, effectImagesConfig, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)

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
        self._valueSmootherLen = -1
        self._getConfiguration()
        self._lastNoteState = NoteState(0)
        self._startSongPosition = 0.0

    def setMidiChannelState(self, midiChannelState):
        self._lastChannelState = midiChannelState

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
            smootherLen = 2
        if(smootherMode == "Smooth"):
            smootherLen = 4
        if(smootherMode == "Smoother"):
            smootherLen = 8
        if(smootherMode == "Smoothest"):
            smootherLen = 16
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
        return self._modulationName

    def getThumbnailUniqueString(self):
        return self.getType() + ":" + self._modulationName

    def releaseMedia(self, mediaSettingsHolder):
        pass

    def setStartPosition(self, startSpp, mediaSettingsHolder, songPosition, midiNoteStateHolder, dmxStateHolder, midiChannelStateHolder, noteIsNew):
        mediaSettingsHolder = self._mediaSettingsHolder
        if(noteIsNew):
            self._startSongPosition = startSpp
            for i in range(self._valueSmootherLen):
                self._valueSmoother[i] = -1.0
            #discard last value and recalculate if we get a new start position:
            self._lastNoteState = midiNoteStateHolder
            self._dmxStateHolder = dmxStateHolder
            self._lastChannelState = midiChannelStateHolder
            self.updateModulationValues(mediaSettingsHolder, songPosition)
        else:
            if((self._lastNoteState != midiNoteStateHolder) or (self._lastChannelState != midiChannelStateHolder)):
                #discard last value and recalculate if we get a new note or channel object:
                self._lastNoteState = midiNoteStateHolder
                self._lastChannelState = midiChannelStateHolder
                if(self._valueSmootherLen > 1):
                    self._valueSmootherIndex = (self._valueSmootherIndex - 1) % self._valueSmootherLen

    def skipFrames(self, mediaSettingsHolder, currentSongPosition, midiNoteState, dmxState, midiChannelState, timeMultiplyer = None):
        return False

    def updateModulationValues(self, mediaSettingsHolder, currentSongPosition):
        if(self._noteModulationHolder != None):
            midiNoteState = self._lastNoteState
            midiChannelState = self._lastChannelState
#            mediaSettingsHolder = self._mediaSettingsHolder
            firstValue = self._midiModulation.getModlulationValue(self._firstModulationId, midiChannelState, midiNoteState, self._dmxStateHolder, currentSongPosition, self._specialModulationHolder)
            secondValue = self._midiModulation.getModlulationValue(self._secondModulationId, midiChannelState, midiNoteState, self._dmxStateHolder, currentSongPosition, self._specialModulationHolder)
            thirdValue = self._midiModulation.getModlulationValue(self._thirdModulationId, midiChannelState, midiNoteState, self._dmxStateHolder, currentSongPosition, self._specialModulationHolder)

            #Summing...
            sumValue = 0.0
            if(self._modulationCombiner1 == self.AddModes.IfThenElse):
                if(firstValue > 0.5):
                    sumValue = secondValue
                else:
                    sumValue = thirdValue
            else:
                if(self._modulationCombiner1 == self.AddModes.Add):
                    sumValue = firstValue + secondValue
                    sumValue = min(sumValue, 1.0)
                elif(self._modulationCombiner1 == self.AddModes.Subtract):
                    sumValue = firstValue - secondValue
                    sumValue = max(sumValue, 0.0)
                elif(self._modulationCombiner1 == self.AddModes.Mask):
                    sumValue = firstValue * secondValue
                else:
                    sumValue = (firstValue * secondValue * 2)
                    sumValue = min(sumValue, 1.0)

#                print "DEBUG pcn: sum1: " + str(sumValue),
                if(self._modulationCombiner2 == self.AddModes.Add):
                    sumValue = sumValue + thirdValue
                    sumValue = min(sumValue, 1.0)
                elif(self._modulationCombiner2 == self.AddModes.Subtract):
                    sumValue = sumValue - thirdValue
                    sumValue = max(sumValue, 0.0)
                elif(self._modulationCombiner2 == self.AddModes.Mask):
                    sumValue = sumValue * thirdValue
                else:
                    sumValue = (sumValue * thirdValue * 2)
                    sumValue = min(sumValue, 1.0)
#                print "DEBUG pcn: sum2: " + str(sumValue),

            sumValue = min(max(sumValue, 0.0), 1.0)
            if((self._limiterAdd > 0.01) or (self._limiterMultiply < 1.0)):
                sumValue = self._limiterAdd + (sumValue * self._limiterMultiply)

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
#            print "DEBUG pcn: sumSmooth: " + str(sumValue)

#            print "DEBUG pcn: ModulationMedia: updateModulationValues() sum: " + str(sumValue)
            #Publishing...
            noteMidiChannel = midiNoteState.getMidiChannel() + 1
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
        try:
            fontPILImage, _ = generateTextImageAndMask("Mod\\n" + self._modulationName, "Arial", fontPath, 10, 255, 255, 255)
        except:
            traceback.print_exc()
            raise MediaError("Error generating text!")
        self._mediaSettingsHolder.captureImage = pilToCvImage(fontPILImage)
        self._firstImage = self._mediaSettingsHolder.captureImage
        self._fileOk = True

    def mixWithImage(self, image, mixMode, wipeMode, mixLevel, effects, preCtrlValues, postCtrlValues, mediaSettingsHolder, currentSongPosition, midiChannelState, guiCtrlStateHolder, midiNoteState, dmxState, mixMat):
        return (image, None, None, None, None)
