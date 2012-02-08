'''
Created on 6. feb. 2012

@author: pcn
'''
from configuration.ConfigurationHolder import ConfigurationHolder
from configurationGui.GlobalConfig import GlobalConfig
from configurationGui.MediaPoolConfig import MediaPoolConfig
from configurationGui.MediaMixerConfig import MediaMixerConfig

class Configuration(object):
    def __init__(self):
        pass
        self._configurationTree = ConfigurationHolder("MusicalVideoPlayer")
        self._globalConf = GlobalConfig(self._configurationTree)
        self._mediaMixerConf = MediaMixerConfig(self._configurationTree)
        self._mediaPoolConf = MediaPoolConfig(self._mediaMixerConf.getConfTree())

    def setFromXml(self, config):
        print "DEBUG: Setting from XML"
        self._configurationTree.setFromXml(config)
        self._mediaPoolConf.checkAndUpdateFromConfiguration()
        self._mediaMixerConf.checkAndUpdateFromConfiguration()
        self._globalConf.checkAndUpdateFromConfiguration()

    def getEffectChoices(self):
        return self._globalConf.getEffectChoices()

    def setupEffectsGui(self, plane, sizer):
        self._globalConf.setupEffectsGui(plane, sizer)

    def setupEffectsSlidersGui(self, plane, sizer):
        self._globalConf.setupEffectsSlidersGui(plane, sizer)

    def editEffectsConfig(self, configName, midiChannel, midiNote, midiSender):
        self._globalConf.editEffectsConfig(configName, midiChannel, midiNote, midiSender)

    def getFadeChoices(self):
        return self._globalConf.getFadeChoices()

    def getNoteConfiguration(self, noteId):
        return self._mediaPoolConf.getNoteConfiguration(noteId)

    def getXmlString(self):
        return self._configurationTree.getConfigurationXMLString()

    def printConfiguration(self):
        print self.getXmlString()



