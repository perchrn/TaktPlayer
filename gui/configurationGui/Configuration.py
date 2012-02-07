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

    def getEffectChoices(self):
        return self._globalConf.getEffectChoices()

    def getFadeChoices(self):
        return self._globalConf.getFadeChoices()

    def getNoteConfiguration(self, noteId):
        return self._mediaPoolConf.getNoteConfiguration(noteId)

    def getXmlString(self):
        return self._configurationTree.getConfigurationXMLString()

    def printConfiguration(self):
        print self.getXmlString()



