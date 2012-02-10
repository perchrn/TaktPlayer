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
        self._globalConf = GlobalConfig(self._configurationTree, self)
        self._mediaMixerConf = MediaMixerConfig(self._configurationTree)
        self._mediaPoolConf = MediaPoolConfig(self._mediaMixerConf.getConfTree())

        self._selectedMidiChannel = -1
        self._midiSender = SendMidiOverNet("127.0.0.1", 2020)
        self._latestMidiControllerRequestCallback = None


    def setLatestMidiControllerRequestCallback(self, callback):
        self._latestMidiControllerRequestCallback = callback

    def setFromXml(self, config):
        print "DEBUG: Setting from XML"
        self._configurationTree.setFromXml(config)
        self._mediaPoolConf.checkAndUpdateFromConfiguration()
        self._mediaMixerConf.checkAndUpdateFromConfiguration()
        self._globalConf.checkAndUpdateFromConfiguration()

    def getEffectChoices(self):
        return self._globalConf.getEffectChoices()

    def setupEffectsGui(self, plane, sizer, parentSizer, parentClass):
        self._globalConf.setupEffectsGui(plane, sizer, parentSizer, parentClass)

    def setupFadeGui(self, plane, sizer, parentSizer, parentClass):
        self._globalConf.setupFadeGui(plane, sizer, parentSizer, parentClass)

    def setupModulationGui(self, plane, sizer, parentSizer, parentClass):
        self._globalConf.setupModulationGui(plane, sizer, parentSizer, parentClass)

    def setupEffectsSlidersGui(self, plane, sizer, parentSizer, parentClass):
        self._globalConf.setupEffectsSlidersGui(plane, sizer, parentSizer, parentClass)

    def updateEffectsGui(self, configName, midiNote):
        self._globalConf.updateEffectsGui(configName, midiNote)

    def updateModulationGui(self, modulationString):
        self._globalConf.updateModulationGui(modulationString)

    def updateFadeGui(self, configName):
        self._globalConf.updateFadeGui(configName)

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

    def getLatestMidiControllers(self):
        return self._latestMidiControllerRequestCallback()

    def printConfiguration(self):
        print self.getXmlString()



