'''
Created on 6. feb. 2012

@author: pcn
'''
from video.media.MediaFileModes import getMixModeFromName

class MediaMixerConfig(object):
    def __init__(self, configParent):
        self._configurationTree = configParent.addChildUnique("MediaMixer")

        self._mediaTrackConfigs = []
        for i in range(16):
            trackConfig = self._configurationTree.addChildUniqueId("MediaTrack", "TrackId", str(i+1), i+1)
            self.setupTrackConfig(trackConfig)
            self._mediaTrackConfigs.append(trackConfig)

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
        for i in range(128):
            mediaState = mediaTrackState[i]
            if(mediaState == False):
                self.deafultTrackSettings(i)

    def updateTrackFromXml(self, xmlConfig):
        trackId = int(xmlConfig.get("trackid"))
        trackId = min(max(trackId, 0), 16)
        trackConfig = self._mediaTrackConfigs[trackId]

        mixMode = xmlConfig.get("mixmode")
        trackConfig.setValue("MixMode", mixMode)

        preEffectModulationTemplate = xmlConfig.get("preeffectconfig")
        trackConfig.setValue("PreEffectConfig", preEffectModulationTemplate)

        postEffectModulationTemplate = xmlConfig.get("posteffectconfig")
        trackConfig.setValue("PostEffectConfig", postEffectModulationTemplate)

        return trackId

    def deafultTrackSettings(self, trackIndex):
        trackConfig = self._mediaTrackConfigs[trackIndex]
        trackConfig.setValue("MixMode", "Default")
        trackConfig.setValue("PreEffectConfig", self._defaultPreEffectSettingsName)
        trackConfig.setValue("PostEffectConfig", self._defaultPostEffectSettingsName)

    def getConfTree(self):
        return self._configurationTree

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print "MediaMixerConfig config is updated..."
        else:
            print "DEBUG: MediaMixerConfig.checkAndUpdateFromConfiguration NOT updated..."

    def countNumberOfTimeEffectTemplateUsed(self, effectConfigName):
        returnNumer = 0
#        for noteConfig in self._mediaPool:
#            if(noteConfig != None):
#                returnNumer += noteConfig.countNumberOfTimeEffectTemplateUsed(effectConfigName)
        return returnNumer

    def countNumberOfTimeFadeTemplateUsed(self, fadeConfigName):
        returnNumer = 0
#        for noteConfig in self._mediaPool:
#            if(noteConfig != None):
#                returnNumer += noteConfig.countNumberOfTimeFadeTemplateUsed(fadeConfigName)
        return returnNumer

    def renameEffectTemplateUsed(self, oldName, newName):
        pass
#        for noteConfig in self._mediaPool:
#            if(noteConfig != None):
#                noteConfig.renameEffectTemplateUsed(oldName, newName)

    def renameFadeTemplateUsed(self, oldName, newName):
        pass
#        for noteConfig in self._mediaPool:
#            if(noteConfig != None):
#                noteConfig.renameFadeTemplateUsed(oldName, newName)

    def verifyEffectTemplateUsed(self, effectConfigNameList):
        pass
#        for noteConfig in self._mediaPool:
#            if(noteConfig != None):
#                noteConfig.verifyEffectTemplateUsed(effectConfigNameList)

    def verifyFadeTemplateUsed(self, fadeConfigNameList):
        pass
#        for noteConfig in self._mediaPool:
#            if(noteConfig != None):
#                noteConfig.verifyFadeTemplateUsed(fadeConfigNameList)
