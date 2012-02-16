'''
Created on 21. des. 2011

@author: pcn
'''
import logging
from video.Effects import getEmptyImage, createMask, createMat, getEffectByName
from video.media.MediaFile import MixMode
from video.media.MediaFileModes import getMixModeFromName


class MediaMixer(object):
    def __init__(self, configurationTree, midiStateHolder, effectsConfiguration):
        self._configurationTree = configurationTree
        self._midiStateHolder = midiStateHolder
        self._effectsConfigurationTemplates = effectsConfiguration
        #Logging etc.
        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))

        self._internalResolutionX =  self._configurationTree.getValueFromPath("Global.ResolutionX")
        self._internalResolutionY =  self._configurationTree.getValueFromPath("Global.ResolutionY")

        self._mixMat1 = createMat(self._internalResolutionX, self._internalResolutionY)
        self._mixMat2 = createMat(self._internalResolutionX, self._internalResolutionY)
        self._mixMat3 = createMat(self._internalResolutionX, self._internalResolutionY)
        self._mixMask = createMask(self._internalResolutionX, self._internalResolutionY)

        self._blankImage = getEmptyImage(self._internalResolutionX, self._internalResolutionY)
        self._currentImage = self._blankImage
        self._currentImageId = 0
        self._nextImage = self._currentImage
        self._nextImageId = 0

        self._mediaTracks = []
        self._mediaTracksMixMode = []
        self._mediaTracksEffects = []
        for i in range(16): #@UnusedVariable
            self._mediaTracks.append(None)
            self._mediaTracksMixMode.append(MixMode.Default)
            self._mediaTracksEffects.append(None)
        self._mediaTrackConfigs = []
        for i in range(16):
            trackConfig = self._configurationTree.addChildUniqueId("MediaTrack", "TrackId", str(i+1), i+1)
            self.setupTrackConfig(trackConfig)
            self._mediaTrackConfigs.append(trackConfig)
        self.loadMediaFromConfiguration()

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

    def setupTrackConfig(self, trackConfigHolder):
        trackConfigHolder.addTextParameter("MixMode", "Default")
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

        preEffectModulationTemplate = xmlConfig.get("preeffectconfig")
        trackConfig.setValue("PreEffectConfig", preEffectModulationTemplate)
        preEffectSettings = self._effectsConfigurationTemplates.getTemplate(preEffectModulationTemplate)
        if(preEffectSettings == None):
            preEffectSettings = self._effectsConfigurationTemplates.getTemplate(self._defaultPostEffectSettingsName)
        preEffect = getEffectByName(preEffectSettings.getEffectName(), self._configurationTree, self._internalResolutionX, self._internalResolutionY)

        postEffectModulationTemplate = xmlConfig.get("posteffectconfig")
        trackConfig.setValue("PostEffectConfig", postEffectModulationTemplate)
        postEffectSettings = self._effectsConfigurationTemplates.getTemplate(postEffectModulationTemplate)
        if(postEffectSettings == None):
            postEffectSettings = self._effectsConfigurationTemplates.getTemplate(self._defaultPostEffectSettingsName)
        postEffect = getEffectByName(postEffectSettings.getEffectName(), self._configurationTree, self._internalResolutionX, self._internalResolutionY)

        self._mediaTracksEffects[trackId] = (preEffect, preEffectSettings, postEffect, postEffectSettings)
        return trackId

    def deafultTrackSettings(self, trackIndex):
        trackConfig = self._mediaTrackConfigs[trackIndex]

        trackConfig.setValue("MixMode", "Default")
        self._mediaTracksMixMode[trackIndex] = MixMode.Default

        trackConfig.setValue("PreEffectConfig", self._defaultPreEffectSettingsName)
        preEffectSettings = self._effectsConfigurationTemplates.getTemplate(self._defaultPreEffectSettingsName)
        preEffect = getEffectByName(preEffectSettings.getEffectName(), self._configurationTree, self._internalResolutionX, self._internalResolutionY)

        trackConfig.setValue("PostEffectConfig", self._defaultPostEffectSettingsName)
        postEffectSettings = self._effectsConfigurationTemplates.getTemplate(self._defaultPostEffectSettingsName)
        postEffect = getEffectByName(postEffectSettings.getEffectName(), self._configurationTree, self._internalResolutionX, self._internalResolutionY)
        self._mediaTracksEffects[trackIndex] = (preEffect, preEffectSettings, postEffect, postEffectSettings)

    def getImage(self):
        return self._currentImage

    def gueueImage(self, media, midiChannel):
        self._mediaTracks[midiChannel] = media

    def _updateImage(self):
        if(self._currentImageId != self._nextImageId):
            self._currentImageId = self._nextImageId
            self._currentImage = self._nextImage

    def mixImages(self, midiTime):
        imageMix = None
        for midiChannel in range(16):
            currenMedia = self._mediaTracks[midiChannel]
            mixMode = self._mediaTracksMixMode[midiChannel]
            effects = self._mediaTracksEffects[midiChannel]
            midiChannelState = self._midiStateHolder.getMidiChannelState(midiChannel)
            midiNoteState = midiChannelState.getActiveNote(midiTime)
            if(currenMedia != None):
                if(imageMix == None):
                    imageMix = currenMedia.getImage()
                else:
                    if(imageMix == self._mixMat1):
                        imageMix = currenMedia.mixWithImage(imageMix, mixMode, effects, midiTime, midiChannelState, midiNoteState, self._mixMat1, self._mixMat2, self._mixMask)
                    else:
                        imageMix = currenMedia.mixWithImage(imageMix, mixMode, effects, midiTime, midiChannelState, midiNoteState, self._mixMat2, self._mixMat3, self._mixMask)
        if(imageMix == None):
            imageMix = self._blankImage
        self._nextImage = imageMix
        self._nextImageId += 1
        self._updateImage()


