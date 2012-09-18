'''
Created on 21. des. 2011

@author: pcn
'''
import logging
from video.Effects import getEmptyImage, createMask, createMat, getEffectByName
from video.media.MediaFile import MixMode, scaleAndSave
from video.media.MediaFileModes import getMixModeFromName
import os
import shutil
from cv2 import cv
from midi.MidiModulation import MidiModulation
from midi.MidiTiming import MidiTiming


class MediaMixer(object):
    def __init__(self, configurationTree, midiStateHolder, effectsConfiguration, effectImagesConfig, internalResolutionX, internalResolutionY):
        self._configurationTree = configurationTree
        self._midiStateHolder = midiStateHolder
        self._effectsConfigurationTemplates = effectsConfiguration
        self._effectImagesConfigurationTemplates = effectImagesConfig
        #Logging etc.
        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))

        self._internalResolutionX = internalResolutionX
        self._internalResolutionY = internalResolutionY
        self._midiTiming = MidiTiming()

        self._mixMat1 = createMat(self._internalResolutionX, self._internalResolutionY)
        self._mixMat2 = createMat(self._internalResolutionX, self._internalResolutionY)
        self._convertedMat = createMat(self._internalResolutionX, self._internalResolutionY)
        self._mixMask = createMask(self._internalResolutionX, self._internalResolutionY)

        self._previewMat = createMat(160, 120)

        self._blankImage = getEmptyImage(self._internalResolutionX, self._internalResolutionY)
        self._currentImage = self._blankImage
        self._currentImageId = 0
        self._nextImage = self._currentImage
        self._nextImageId = 0

        self._mediaTracks = []
        self._mediaTracksMixMode = []
        self._mediaTracksMidiModulation = []
        self._mediaTracksLevelMod = []
        self._mediaTracksEffects = []
        self._mediaTracksCurrentPreEffectValues = []
        self._mediaTracksCurrentPostEffectValues = []
        for i in range(16): #@UnusedVariable
            self._mediaTracks.append(None)
            self._mediaTracksMixMode.append(MixMode.Default)
            self._mediaTracksLevelMod.append(None)
            self._mediaTracksEffects.append(None)
            self._mediaTracksCurrentPreEffectValues.append((0.0, 0.0, 0.0, 0.0, 0.0))
            self._mediaTracksCurrentPostEffectValues.append((0.0, 0.0, 0.0, 0.0, 0.0))
        self._mediaTrackConfigs = []
        for i in range(16):
            trackConfig = self._configurationTree.addChildUniqueId("MediaTrack", "TrackId", str(i+1), i+1)
            midiModulation = MidiModulation(trackConfig, self._midiTiming)
            self.setupTrackConfig(trackConfig, midiModulation)
            self._mediaTrackConfigs.append(trackConfig)
            self._mediaTracksMidiModulation.append(midiModulation)
        self.loadMediaFromConfiguration()

        self._imagesSinceLastPreviewSave = 0
        self._imagesToSkipBetweenPreviewSave = 20
        self._tempPreviewName = os.path.normpath("thumbs/preview_tmp.jpg")
        self._previewName = os.path.normpath("thumbs/preview.jpg")

    def _getConfiguration(self):
        self.loadMediaFromConfiguration()

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print "mediaMixer config is updated..."
            self._getConfiguration()
            for mediaTrack in self._mediaTracks:
                if(mediaTrack != None):
                    mediaTrack.checkAndUpdateFromConfiguration()
            self._configurationTree.resetConfigurationUpdated()

    def setupTrackConfig(self, trackConfigHolder, trackMidiModulation):
        trackConfigHolder.addTextParameter("MixMode", "Default")
        trackMidiModulation.setModulationReceiver("LevelModulation", "None")
        self._defaultPreEffectSettingsName = "MixPreDefault"
        trackConfigHolder.addTextParameter("PreEffectConfig", self._defaultPreEffectSettingsName)#Default MixPreDefault
        self._defaultPostEffectSettingsName = "MixPostDefault"
        trackConfigHolder.addTextParameter("PostEffectConfig", self._defaultPostEffectSettingsName)#Default MixPostDefault

    def loadMediaFromConfiguration(self):
        mediaTrackState = []
        for i in range(16):
            mediaTrackState.append(False)
        xmlChildren = self._configurationTree.findXmlChildrenList("MediaTrack")
        if(xmlChildren != None):
            for xmlConfig in xmlChildren:
                trackId = self.updateTrackFromXml(xmlConfig)
                mediaTrackState[trackId - 1] = True
        for i in range(16):
            mediaState = mediaTrackState[i]
            if(mediaState == False):
                self.deafultTrackSettings(i)

    def updateTrackFromXml(self, xmlConfig):
        trackId = int(xmlConfig.get("trackid"))
        trackId = min(max(trackId - 1, 0), 15)
        trackConfig = self._mediaTrackConfigs[trackId]

        mixMode = xmlConfig.get("mixmode")
        trackConfig.setValue("MixMode", mixMode)
        self._mediaTracksMixMode[trackId] = getMixModeFromName(mixMode)

        self._mediaTracksLevelMod[trackId] = self._mediaTracksMidiModulation[trackId].connectModulation("LevelModulation")

        preEffectModulationTemplate = xmlConfig.get("preeffectconfig")
        trackConfig.setValue("PreEffectConfig", preEffectModulationTemplate)
        preEffectSettings = self._effectsConfigurationTemplates.getTemplate(preEffectModulationTemplate)
        if(preEffectSettings == None):
            preEffectSettings = self._effectsConfigurationTemplates.getTemplate(self._defaultPostEffectSettingsName)
        preEffect = getEffectByName(preEffectSettings.getEffectName(), self._configurationTree, self._effectImagesConfigurationTemplates, self._internalResolutionX, self._internalResolutionY)

        postEffectModulationTemplate = xmlConfig.get("posteffectconfig")
        trackConfig.setValue("PostEffectConfig", postEffectModulationTemplate)
        postEffectSettings = self._effectsConfigurationTemplates.getTemplate(postEffectModulationTemplate)
        if(postEffectSettings == None):
            postEffectSettings = self._effectsConfigurationTemplates.getTemplate(self._defaultPostEffectSettingsName)
        postEffect = getEffectByName(postEffectSettings.getEffectName(), self._configurationTree, self._effectImagesConfigurationTemplates, self._internalResolutionX, self._internalResolutionY)
#        print "DEBUG trackId: " + str(trackId) + " setting preeffect: " + str(preEffectSettings.getEffectName()) + " -> " + str(preEffect) + " setting posteffect: " + str(postEffectSettings.getEffectName()) + " -> " + str(postEffect)

        preEffectStartControllerValues = (None, None, None, None, None)
        postEffectStartControllerValues = (None, None, None, None, None)
        preEffectStartValues = (0.0, 0.0, 0.0, 0.0, 0.0)
        postEffectStartValues = (0.0, 0.0, 0.0, 0.0, 0.0)
        self._mediaTracksEffects[trackId] = (preEffect, preEffectSettings, preEffectStartControllerValues, preEffectStartValues, postEffect, postEffectSettings, postEffectStartControllerValues, postEffectStartValues)
        return trackId

    def deafultTrackSettings(self, trackIndex):
        trackConfig = self._mediaTrackConfigs[trackIndex]

        trackConfig.setValue("MixMode", "Default")
        self._mediaTracksMixMode[trackIndex] = MixMode.Default

        trackConfig.setValue("LevelModulation", "None")
        self._mediaTracksLevelMod[trackIndex] = self._mediaTracksMidiModulation[trackIndex].connectModulation("LevelModulation")

        trackConfig.setValue("PreEffectConfig", self._defaultPreEffectSettingsName)
        preEffectSettings = self._effectsConfigurationTemplates.getTemplate(self._defaultPreEffectSettingsName)
        preEffect = getEffectByName(preEffectSettings.getEffectName(), self._configurationTree, self._effectImagesConfigurationTemplates, self._internalResolutionX, self._internalResolutionY)

        trackConfig.setValue("PostEffectConfig", self._defaultPostEffectSettingsName)
        postEffectSettings = self._effectsConfigurationTemplates.getTemplate(self._defaultPostEffectSettingsName)
        postEffect = getEffectByName(postEffectSettings.getEffectName(), self._configurationTree, self._effectImagesConfigurationTemplates, self._internalResolutionX, self._internalResolutionY)
        preEffectStartControllerValues = (None, None, None, None, None)
        postEffectStartControllerValues = (None, None, None, None, None)
        preEffectStartValues = (0.0, 0.0, 0.0, 0.0, 0.0)
        postEffectStartValues = (0.0, 0.0, 0.0, 0.0, 0.0)
        self._mediaTracksEffects[trackIndex] = (preEffect, preEffectSettings, preEffectStartControllerValues, preEffectStartValues, postEffect, postEffectSettings, postEffectStartControllerValues, postEffectStartValues)

    def getImage(self):
        cv.ConvertImage(self._currentImage, self._convertedMat, cv.CV_CVTIMG_SWAP_RB)
        return self._convertedMat

    def gueueImage(self, media, midiChannel):
        self._mediaTracks[midiChannel] = media

    def _updateImage(self):
        if(self._currentImageId != self._nextImageId):
            self._currentImageId = self._nextImageId
            self._currentImage = self._nextImage

    def getEffectState(self, midiChannel):
        guiCtrlStateHolder = self._midiStateHolder.getMidiChannelControllerStateHolder(midiChannel)
        guiEffectValuesString = str(guiCtrlStateHolder.getGuiContollerState(0)) + ";"
        valuesString = str(self._mediaTracksCurrentPreEffectValues[midiChannel]) + ";"
        guiEffectValuesString += str(guiCtrlStateHolder.getGuiContollerState(5))
        valuesString += str(self._mediaTracksCurrentPostEffectValues[midiChannel])
        return (valuesString, guiEffectValuesString)

    def mixImages(self, midiTime):
        imageMix = None
        for midiChannel in range(16):
            currenMedia = self._mediaTracks[midiChannel]
            effects = self._mediaTracksEffects[midiChannel]
            if(currenMedia != None):
                mixMode = self._mediaTracksMixMode[midiChannel]
                midiChannelState = self._midiStateHolder.getMidiChannelState(midiChannel)
                guiCtrlStateHolder = self._midiStateHolder.getMidiChannelControllerStateHolder(midiChannel)
                midiNoteState = midiChannelState.getActiveNote(midiTime)
                mixLevel = 1.0 - self._mediaTracksMidiModulation[midiChannel].getModlulationValue(self._mediaTracksLevelMod[midiChannel], midiChannelState, midiNoteState, midiTime, 0.0)
                if(imageMix == None):
                    imageTest = currenMedia.getImage()
                    if(imageTest != None):
                        # Apply effects and level...
                        if(imageMix == self._mixMat1):
                            imageMix, preFxSettings, postFxSettings = currenMedia.mixWithImage(imageMix, MixMode.Replace, mixLevel, effects, midiTime, midiChannelState, guiCtrlStateHolder, midiNoteState, self._mixMat1, self._mixMask)
                        else:
                            imageMix, preFxSettings, postFxSettings  = currenMedia.mixWithImage(imageMix, MixMode.Replace, mixLevel, effects, midiTime, midiChannelState, guiCtrlStateHolder, midiNoteState, self._mixMat2, self._mixMask)
                        self._mediaTracksCurrentPreEffectValues[midiChannel] = preFxSettings
                        self._mediaTracksCurrentPostEffectValues[midiChannel] = postFxSettings
                else:
                    if(imageMix == self._mixMat1):
                        imageMix, preFxSettings, postFxSettings  = currenMedia.mixWithImage(imageMix, mixMode, mixLevel, effects, midiTime, midiChannelState, guiCtrlStateHolder, midiNoteState, self._mixMat1, self._mixMask)
                    else:
                        imageMix, preFxSettings, postFxSettings  = currenMedia.mixWithImage(imageMix, mixMode, mixLevel, effects, midiTime, midiChannelState, guiCtrlStateHolder, midiNoteState, self._mixMat2, self._mixMask)
                    self._mediaTracksCurrentPreEffectValues[midiChannel] = preFxSettings
                    self._mediaTracksCurrentPostEffectValues[midiChannel] = postFxSettings
            else:
                if(effects[0] != None):
                    effects[0].reset()
                if(effects[4] != None):
                    effects[4].reset()
        if(imageMix == None):
            imageMix = self._blankImage
        self._nextImage = imageMix
        self._nextImageId += 1
        self._updateImage()

        if(self._imagesSinceLastPreviewSave >= self._imagesToSkipBetweenPreviewSave):
            self._imagesSinceLastPreviewSave = 0
            scaleAndSave(self._currentImage, self._tempPreviewName, self._previewMat)
            try:
                shutil.move(self._tempPreviewName, self._previewName)
            except:
                pass
        else:
            self._imagesSinceLastPreviewSave += 1

