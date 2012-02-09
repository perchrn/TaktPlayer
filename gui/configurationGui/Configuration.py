'''
Created on 6. feb. 2012

@author: pcn
'''
from configuration.ConfigurationHolder import ConfigurationHolder
from configurationGui.GlobalConfig import GlobalConfig
from configurationGui.MediaPoolConfig import MediaPoolConfig
from configurationGui.MediaMixerConfig import MediaMixerConfig
from network.SendMidiOverNet import SendMidiOverNet

class Configuration(object):
    def __init__(self):
        self._configurationTree = ConfigurationHolder("MusicalVideoPlayer")
        self._globalConf = GlobalConfig(self._configurationTree)
        self._mediaMixerConf = MediaMixerConfig(self._configurationTree)
        self._mediaPoolConf = MediaPoolConfig(self._mediaMixerConf.getConfTree())

        self._selectedMidiChannel = -1
        self._midiSender = SendMidiOverNet("127.0.0.1", 2020)

    def setFromXml(self, config):
        print "DEBUG: Setting from XML"
        self._configurationTree.setFromXml(config)
        self._mediaPoolConf.checkAndUpdateFromConfiguration()
        self._mediaMixerConf.checkAndUpdateFromConfiguration()
        self._globalConf.checkAndUpdateFromConfiguration()

    def getEffectChoices(self):
        return self._globalConf.getEffectChoices()

    def setupEffectsGui(self, plane, sizer, parentSizer):
        self._globalConf.setupEffectsGui(plane, sizer, parentSizer)

    def setupEffectsSlidersGui(self, plane, sizer, parentSizer):
        self._globalConf.setupEffectsSlidersGui(plane, sizer, parentSizer)

    def updateEffectsGui(self, configName, midiNote):
        self._globalConf.updateEffectsGui(configName, midiNote)

    def getFadeChoices(self):
        return self._globalConf.getFadeChoices()

    def getNoteConfiguration(self, noteId):
        return self._mediaPoolConf.getNoteConfiguration(noteId)

    def getXmlString(self):
        return self._configurationTree.getConfigurationXMLString()

    def setSelectedMidiChannel(self, midiChannel):
        self._selectedMidiChannel = midiChannel

    def getSelectedMidiChannel(self):
        return self._selectedMidiChannel

    def getMidiSender(self):
        return self._midiSender

    def printConfiguration(self):
        print self.getXmlString()



