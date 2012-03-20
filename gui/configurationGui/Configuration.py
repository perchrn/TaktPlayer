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
        self._guiConfigurationTree = ConfigurationHolder("MusicalVideoPlayerGUI")
        self._guiConfigurationTree.loadConfig("GuiConfig.cfg")
        self.setupGuiConfiguration()
        self._playerConfigurationTree = ConfigurationHolder("MusicalVideoPlayer")
        self._globalConf = GlobalConfig(self._playerConfigurationTree, self)
        self._mediaMixerConf = MediaMixerConfig(self._playerConfigurationTree)
        self._mixerGui = None

        self._mediaPoolConf = MediaPoolConfig(self._playerConfigurationTree)
        self._noteGui = None

        self._selectedMidiChannel = -1
        self.setupMidiSender()
        self._latestMidiControllerRequestCallback = None

    def setupGuiConfiguration(self):
        self._guiPlayerConfig = self._guiConfigurationTree.addChildUnique("Player")
        self._guiPlayerConfig.addTextParameter("PlayerHost", "127.0.0.1")
        self._guiPlayerConfig.addIntParameter("MidiPort", 2020)
        self._guiPlayerConfig.addIntParameter("WebPort", 2021)
        self._guiPlayerConfig.addBoolParameter("MidiEnabled", True)
        self._guiConfigurationTree.addTextParameter("VideoDir", "")

    def setupMidiSender(self):
        host, port = self.getMidiConfig()
        self._midiSender = SendMidiOverNet(host, port)

    def getWebConfig(self):
        host = self._guiPlayerConfig.getValue("PlayerHost")
        port = self._guiPlayerConfig.getValue("WebPort")
        return (host, port)

    def getMidiConfig(self):
        host = self._guiPlayerConfig.getValue("PlayerHost")
        port = self._guiPlayerConfig.getValue("MidiPort")
        return (host, port)

    def getGuiVideoDir(self):
        return self._guiConfigurationTree.getValue("VideoDir")

    def setLatestMidiControllerRequestCallback(self, callback):
        self._latestMidiControllerRequestCallback = callback

    def isMidiEnabled(self):
        return self._guiPlayerConfig.getValue("MidiEnabled")

    def setMidiEnable(self, newValue):
        self._guiPlayerConfig.setValue("MidiEnabled", newValue)

    def setFromXml(self, config):
        self._playerConfigurationTree.setFromXml(config)
        self._mediaPoolConf.checkAndUpdateFromConfiguration()
        self._mediaMixerConf.checkAndUpdateFromConfiguration()
        self._globalConf.checkAndUpdateFromConfiguration()

    def setNoteGui(self, noteGui):
        self._noteGui = noteGui

    def updateNoteGui(self):
        if(self._noteGui != None):
            self._noteGui.updateGui(None, None)

    def setMixerGui(self, trackGui):
        self._mixerGui = trackGui

    def updateMixerGui(self):
        if(self._mixerGui != None):
            self._mixerGui.updateGui(None, None, None)

    def getEffectChoices(self):
        return self._globalConf.getEffectChoices()

    def setupEffectsGui(self, plane, sizer, parentSizer, parentClass):
        self._globalConf.setupEffectsGui(plane, sizer, parentSizer, parentClass)

    def setupEffectsListGui(self, plane, sizer, parentSizer, parentClass):
        self._globalConf.setupEffectsListGui(plane, sizer, parentSizer, parentClass)

    def getFadeModeLists(self):
        return self._globalConf.getFadeModeLists()

    def setupFadeGui(self, plane, sizer, parentSizer, parentClass):
        self._globalConf.setupFadeGui(plane, sizer, parentSizer, parentClass)

    def setupFadeListGui(self, plane, sizer, parentSizer, parentClass):
        self._globalConf.setupFadeListGui(plane, sizer, parentSizer, parentClass)

    def setupModulationGui(self, plane, sizer, parentSizer, parentClass):
        self._globalConf.setupModulationGui(plane, sizer, parentSizer, parentClass)

    def setupEffectsSlidersGui(self, plane, sizer, parentSizer, parentClass):
        self._globalConf.setupEffectsSlidersGui(plane, sizer, parentSizer, parentClass)

    def updateEffectsGui(self, configName, midiNote):
        self._globalConf.updateEffectsGui(configName, midiNote)

    def updateEffectList(self, selectedName):
        self._globalConf.updateEffectList(selectedName)

    def updateEffectListHeight(self, height):
        self._globalConf.updateEffectListHeight(height)

    def getDraggedFxName(self):
        return self._globalConf.getDraggedFxName()

    def getEffectTemplate(self, configName):
        return self._globalConf.getEffectTemplate(configName)

    def getEffectTemplateByIndex(self, index):
        return self._globalConf.getEffectTemplateByIndex(index)

    def getFadeTemplate(self, configName):
        return self._globalConf.getFadeTemplate(configName)

    def getFadeTemplateByIndex(self, index):
        return self._globalConf.getFadeTemplateByIndex(index)

    def makeEffectTemplate(self, saveName, effectName, ammountMod, arg1Mod, arg2Mod, arg3Mod, arg4Mod):
        return self._globalConf.makeEffectTemplate(saveName, effectName, ammountMod, arg1Mod, arg2Mod, arg3Mod, arg4Mod)

    def makeFadeTemplate(self, saveName, fadeMode, fadeMod, levelMod):
        return self._globalConf.makeFadeTemplate(saveName, fadeMode, fadeMod, levelMod)

    def deleteEffectTemplate(self, configName):
        return self._globalConf.deleteEffectTemplate(configName)

    def deleteFadeTemplate(self, configName):
        return self._globalConf.deleteFadeTemplate(configName)

    def duplicateEffectTemplate(self, configName):
        return self._globalConf.duplicateEffectTemplate(configName)

    def duplicateFadeTemplate(self, configName):
        return self._globalConf.duplicateFadeTemplate(configName)

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

    def updateModulationGui(self, modulationString, widget, closeCallback, saveCallback):
        self._globalConf.updateModulationGui(modulationString, widget, closeCallback, saveCallback)

    def updateModulationGuiButton(self, widget, modulationString):
        self._globalConf.updateModulationGuiButton(modulationString, widget)

    def stopModulationGui(self):
        self._globalConf.stopModulationGui()

    def updateFadeGui(self, configName, editField = None):
        self._globalConf.updateFadeGui(configName, editField)

    def updateFadeList(self, selectedName):
        self._globalConf.updateFadeList(selectedName)

    def updateFadeGuiButtons(self, configName, modeWidget, modulationWidget, levelWidget):
        self._globalConf.updateFadeGuiButtons(configName, modeWidget, modulationWidget, levelWidget)

    def getFadeChoices(self):
        return self._globalConf.getFadeChoices()

    def getNoteConfiguration(self, noteId):
        return self._mediaPoolConf.getNoteConfiguration(noteId)

    def getTrackConfiguration(self, trackId):
        return self._mediaMixerConf.getTrackConfiguration(trackId)

    def makeNoteConfig(self, fileName, noteLetter, midiNote):
        return self._mediaPoolConf.makeNoteConfig(fileName, noteLetter, midiNote)

    def getXmlString(self):
        return self._playerConfigurationTree.getConfigurationXMLString()

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



