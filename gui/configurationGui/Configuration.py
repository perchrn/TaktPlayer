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
        self._mixerGui = None

        self._mediaPoolConf = MediaPoolConfig(self._mediaMixerConf.getConfTree())
        self._noteGui = None

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

    def setNoteGui(self, noteGui):
        self._noteGui = noteGui

    def updateNoteGui(self):
        if(self._noteGui != None):
            self._noteGui.updateGui(None, None)

    def setMixerGui(self, noteGui):
        self._mixerGui = noteGui

    def updateMixerGui(self):
        if(self._mixerGui != None):
            self._mixerGui.updateGui(None, None)

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

    def getEffectTemplate(self, configName):
        return self._globalConf.getEffectTemplate(configName)

    def getFadeTemplate(self, configName):
        return self._globalConf.getFadeTemplate(configName)

    def makeEffectTemplate(self, saveName, effectName, ammountMod, arg1Mod, arg2Mod, arg3Mod, arg4Mod):
        return self._globalConf.makeEffectTemplate(saveName, effectName, ammountMod, arg1Mod, arg2Mod, arg3Mod, arg4Mod)

    def makeFadeTemplate(self, saveName, fadeMode, fadeMod, levelMod):
        return self._globalConf.makeFadeTemplate(saveName, fadeMode, fadeMod, levelMod)

    def deleteEffectTemplate(self, configName):
        return self._globalConf.deleteEffectTemplate(configName)

    def deleteFadeTemplate(self, configName):
        return self._globalConf.deleteFadeTemplate(configName)

    def verifyEffectTemplateUsed(self):
        effectsConfigNames =  self._globalConf.getEffectTemplateNamesList()
        self._mediaPoolConf.verifyEffectTemplateUsed(effectsConfigNames)
        self._mediaMixerConf.verifyEffectTemplateUsed(effectsConfigNames)

    def verifyFadeTemplateUsed(self):
        effectsConfigNames =  self._globalConf.getFadeTemplateNamesList()
        self._mediaPoolConf.verifyFadeTemplateUsed(effectsConfigNames)
        self._mediaMixerConf.verifyFadeTemplateUsed(effectsConfigNames)

    def checkIfNameIsDefaultEffectName(self, configName):
        return self._globalConf.checkIfNameIsDefaultEffectName(configName)

    def checkIfNameIsDefaultFadeName(self, configName):
        return self._globalConf.checkIfNameIsDefaultFadeName(configName)

    def countNumberOfTimeEffectTemplateUsed(self, configName):
        returnNumber = 0
        returnNumber += self._mediaPoolConf.countNumberOfTimeEffectTemplateUsed(configName)
        returnNumber += self._mediaMixerConf.countNumberOfTimeEffectTemplateUsed(configName)
        return returnNumber

    def countNumberOfTimeFadeTemplateUsed(self, configName):
        returnNumber = 0
        returnNumber += self._mediaPoolConf.countNumberOfTimeFadeTemplateUsed(configName)
        returnNumber += self._mediaMixerConf.countNumberOfTimeFadeTemplateUsed(configName)
        return returnNumber

    def renameEffectTemplateUsed(self, oldName, newName):
        self._mediaPoolConf.renameEffectTemplateUsed(oldName, newName)
        self._mediaMixerConf.renameEffectTemplateUsed(oldName, newName)

    def renameFadeTemplateUsed(self, oldName, newName):
        self._mediaPoolConf.renameFadeTemplateUsed(oldName, newName)
        self._mediaMixerConf.renameFadeTemplateUsed(oldName, newName)

    def updateModulationGui(self, modulationString, widget):
        self._globalConf.updateModulationGui(modulationString, widget)

    def updateFadeGui(self, configName):
        self._globalConf.updateFadeGui(configName)

    def getFadeChoices(self):
        return self._globalConf.getFadeChoices()

    def getNoteConfiguration(self, noteId):
        return self._mediaPoolConf.getNoteConfiguration(noteId)

    def makeNoteConfig(self, fileName, noteLetter, midiNote):
        return self._mediaPoolConf.makeNoteConfig(fileName, noteLetter, midiNote)

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



