'''
Created on 6. feb. 2012

@author: pcn
'''
from configuration.ConfigurationHolder import ConfigurationHolder,\
    getDefaultDirectories
from configurationGui.GlobalConfig import GlobalConfig
from configurationGui.MediaPoolConfig import MediaPoolConfig
from configurationGui.MediaMixerConfig import MediaMixerConfig
from network.SendMidiOverNet import SendMidiOverNet, SendModes
import os
from midi.MidiStateHolder import SpecialModulationHolder,\
    GenericModulationHolder

class Configuration(object):
    def __init__(self, configDir):
        self._specialModulationHolder = SpecialModulationHolder()
        self._noteModulation = GenericModulationHolder("Note", self._specialModulationHolder)
        self._effectsModulation = GenericModulationHolder("Effect", self._specialModulationHolder)

        self._guiConfigurationTree = ConfigurationHolder("TaktGUI")
        self._guiConfigurationTree.setSelfclosingTags(['video', 'player', 'gui'])
        self.setupGuiConfiguration()
        if((configDir != "") and (configDir != None)):
            self._configurationDefaultDirectory = configDir
        self._configurationFile = os.path.join(self._configurationDefaultDirectory, "GuiConfig.cfg")
        self._guiConfigurationTree.loadConfig(self._configurationFile)
        self.saveConfig()

        self._playerConfigurationTree = ConfigurationHolder("MusicalVideoPlayer")
        self._globalConf = GlobalConfig(self._playerConfigurationTree, self, self._specialModulationHolder, self._effectsModulation)
        self._mediaMixerConf = MediaMixerConfig(self._playerConfigurationTree)
        self._mixerGui = None

        self._mediaPoolConf = MediaPoolConfig(self._playerConfigurationTree, self._noteModulation)
        self._noteGui = None

        self._setNoteNewThumbCallback = None
        self._clearNoteNewThumbCallback = None
        self._draggedNoteName = ""

        self._selectedMidiChannel = -1
        self.setupMidiSender()
        self._latestMidiControllerRequestCallback = None
        self._effectStateRequestCallback = None
        self._getActiveNoteForTrackCallback = None

    def getGlobalConfig(self):
        return self._globalConf

    def setupSpecialModulations(self):
        self._mediaPoolConf.setupSpecialNoteModulations()
        self._globalConf.setupSpecialEffectModulations()

    def setupGuiConfiguration(self):
        self._configurationDefaultDirectory, taktVideoDefaultDir  = getDefaultDirectories()
        self._taktGuiAppDataDir = self._configurationDefaultDirectory

        self._guiPlayerConfig = self._guiConfigurationTree.addChildUnique("Player")
        self._guiPlayerConfig.addTextParameter("PlayerHost", "127.0.0.1")
        self._guiPlayerConfig.addIntParameter("MidiPort", 2020)
        self._guiPlayerConfig.addIntParameter("WebPort", 2021)
        self._guiPlayerConfig.addBoolParameter("MidiEnabled", True)
        self._guiVideoConfig = self._guiConfigurationTree.addChildUnique("Video")
        self._guiVideoConfig.addTextParameter("VideoDir", taktVideoDefaultDir)
        self._guiVideoConfig.addTextParameter("FfmpegBinary", os.path.normpath("ffmpeg"))
        self._guiVideoConfig.addTextParameter("FfmpegH264Options", "-c:v libx264 -preset slow -crf 20 -c:a copy")
        self._guiVideoConfig.addIntParameter("ScaleVideoX", -1)
        self._guiVideoConfig.addIntParameter("ScaleVideoY", -1)
        self._guiConfig = self._guiConfigurationTree.addChildUnique("GUI")
        self._guiConfig.addBoolParameter("AutoSend", True)
        self._guiConfig.addBoolParameter("MidiBroadcast", True)
        self._guiConfig.addTextParameter("MidiBindAddress", "0.0.0.0")
        self._guiConfig.addIntParameter("MidiPort", 2022)
        self._guiConfig.addTextParameter("WindowSize", "800,724") #default, xpos,ypos, 0,0 etc.
        self._guiConfig.addTextParameter("WindowPosition", "-1,-1") #auto, xpos,ypos, 0,0 etc.

    def setPlayerConfig(self, playerHost, midiPort, webPort, midiOn):
        self._guiPlayerConfig.setValue("PlayerHost", playerHost)
        self._guiPlayerConfig.setValue("MidiPort", midiPort)
        self._guiPlayerConfig.setValue("WebPort", webPort)
        self._guiPlayerConfig.setValue("MidiEnabled", midiOn)

    def setVideoConfig(self, videoDir, ffmpegBinary, ffmpegH264Options, scaleX, scaleY):
        self._guiVideoConfig.setValue("VideoDir", videoDir)
        self._guiVideoConfig.setValue("FfmpegBinary", ffmpegBinary)
        self._guiVideoConfig.setValue("FfmpegH264Options", ffmpegH264Options)
        self._guiVideoConfig.setValue("ScaleVideoX", scaleX)
        self._guiVideoConfig.setValue("ScaleVideoY", scaleY)

    def setGuiConfig(self, autoSend, midiBcast, midiBindAddress, midiPort, winSize, winPos):
        self._guiConfig.setValue("AutoSend", autoSend)
        self._guiConfig.setValue("MidiBroadcast", midiBcast)
        self._guiConfig.setValue("MidiBindAddress", midiBindAddress)
        self._guiConfig.setValue("MidiPort", midiPort)
        self._guiConfig.setValue("WindowSize", winSize)
        self._guiConfig.setValue("WindowPosition", winPos)

    def saveConfig(self):
        self._guiConfigurationTree.saveConfigFile(self._configurationFile)

    def setupMidiSender(self):
        host, port, mode = self.getMidiConfig()
        self._midiSender = SendMidiOverNet(host, port, mode)

    def getWebConfig(self):
        host = self._guiPlayerConfig.getValue("PlayerHost")
        port = self._guiPlayerConfig.getValue("WebPort")
        return (host, port)

    def getMidiConfig(self):
        host = self._guiPlayerConfig.getValue("PlayerHost")
        port = self._guiPlayerConfig.getValue("MidiPort")
        mode = SendModes.Mcast #TODO: add multicast mode!
        return (host, port, mode)

    def getMidiListenConfig(self):
        bcast = self._guiConfig.getValue("MidiBroadcast")
        host = self._guiConfig.getValue("MidiBindAddress")
        port = self._guiConfig.getValue("MidiPort")
        return (bcast, host, port)

    def getAppDataDirectory(self):
        return self._taktGuiAppDataDir

    def getGuiConfigDir(self):
        return self._guiConfig.getValue("ConfigDir")

    def getGuiVideoDir(self):
        return self._guiVideoConfig.getValue("VideoDir")

    def getFfmpegBinary(self):
        return self._guiVideoConfig.getValue("FfmpegBinary")

    def getFfmpegH264Options(self):
        return self._guiVideoConfig.getValue("FfmpegH264Options")

    def getVideoScaleX(self):
        return self._guiVideoConfig.getValue("ScaleVideoX")

    def getVideoScaleY(self):
        return self._guiVideoConfig.getValue("ScaleVideoY")

    def getWindowSize(self):
        positionTuplet = (-1, -1)
        positionString = self._guiConfig.getValue("WindowSize")
        positionList = positionString.split(',')
        if(len(positionList) < 2):
            positionList = positionString.split('.')
        if(len(positionList) < 2):
            positionList = positionString.split(':')
        if(len(positionList) < 2):
            positionList = positionString.split('x')
        if(len(positionList) < 2):
            positionList = positionString.split('X')
        if(len(positionList) == 2):
            positionTuplet = (int(positionList[0]), int(positionList[1]))
        return positionTuplet

    def getWindowPosition(self):
        positionTuplet = (-1, -1)
        positionString = self._guiConfig.getValue("WindowPosition")
        positionList = positionString.split(',')
        if(len(positionList) < 2):
            positionList = positionString.split('.')
        if(len(positionList) < 2):
            positionList = positionString.split(':')
        if(len(positionList) < 2):
            positionList = positionString.split('x')
        if(len(positionList) < 2):
            positionList = positionString.split('X')
        if(len(positionList) == 2):
            positionTuplet = (int(positionList[0]), int(positionList[1]))
        return positionTuplet

    def setLatestMidiControllerRequestCallback(self, callback):
        self._latestMidiControllerRequestCallback = callback

    def setEffectStateRequestCallback(self, callback):
        self._effectStateRequestCallback = callback

    def isMidiEnabled(self):
        return self._guiConfig.getValue("MidiBroadcast")

    def setMidiEnable(self, newValue):
        self._guiConfig.setValue("MidiBroadcast", newValue)

    def isAutoSendEnabled(self):
        return self._guiConfig.getValue("AutoSend")

    def setAutoSendEnable(self, newValue):
        self._guiConfig.setValue("AutoSend", newValue)

    def setFromXml(self, config):
        self._playerConfigurationTree.setFromXml(config)
        self.checkAndUpdateFromConfiguration()

    def checkAndUpdateFromConfiguration(self):
        self._mediaPoolConf.checkAndUpdateFromConfiguration()
        self._mediaMixerConf.checkAndUpdateFromConfiguration()
        self._globalConf.checkAndUpdateFromConfiguration()

    def setGetActiveNoteForTrackConfigCallback(self, callback):
        self._getActiveNoteForTrackCallback = callback

    def getActiveNoteForTrack(self, trackId):
        return self._getActiveNoteForTrackCallback(trackId)

    def setNoteGui(self, noteGui):
        self._noteGui = noteGui

    def updateNoteGui(self):
        if(self._noteGui != None):
            self._noteGui.updateGui(None, None)

    def setMixerGui(self, trackGui):
        self._mixerGui = trackGui

    def updateMixerGui(self):
        if(self._mixerGui != None):
            self._mixerGui.updateGui(None, None, None, None)

    def setNoteNewThumbCallback(self, setCallback):
        self._setNoteNewThumbCallback = setCallback

    def clearNoteNewThumbCallback(self, clearCallback):
        self._clearNoteNewThumbCallback = clearCallback

    def setNewNoteThumb(self, noteId):
        if(self._setNoteNewThumbCallback != None):
            self._setNoteNewThumbCallback(noteId)

    def clearNoteThumb(self, noteId):
        if(self._clearNoteNewThumbCallback != None):
            self._clearNoteNewThumbCallback(noteId)

    def verifyTimeModulationTemplateUsed(self):
        effectsConfigNames =  self._globalConf.getTimeModulationTemplateNamesList()
        self._mediaPoolConf.verifyTimeModulationTemplateUsed(effectsConfigNames)

    def countNumberOfTimeTimeModulationTemplateUsed(self, configName):
        returnNumber = 0
        returnNumber += self._mediaPoolConf.countNumberOfTimeTimeModulationTemplateUsed(configName)
        return returnNumber

    def getDraggedNoteName(self):
        return self._draggedNoteName

    def setDraggedNoteName(self, draggedNoteName):
        self._draggedNoteName = draggedNoteName

    def verifyEffectTemplateUsed(self):
        effectsConfigNames =  self._globalConf.getEffectTemplateNamesList()
        self._mediaPoolConf.verifyEffectTemplateUsed(effectsConfigNames)
        self._mediaMixerConf.verifyEffectTemplateUsed(effectsConfigNames)

    def verifyFadeTemplateUsed(self):
        effectsConfigNames =  self._globalConf.getFadeTemplateNamesList()
        self._mediaPoolConf.verifyFadeTemplateUsed(effectsConfigNames)
        self._mediaMixerConf.verifyFadeTemplateUsed(effectsConfigNames)

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

    def getNoteConfiguration(self, noteId):
        return self._mediaPoolConf.getNoteConfiguration(noteId)

    def getNoteList(self):
        return self._mediaPoolConf.getNoteList()

    def getTrackConfiguration(self, trackId):
        return self._mediaMixerConf.getTrackConfiguration(trackId)

    def makeNoteConfig(self, fileName, noteLetter, midiNote):
        return self._mediaPoolConf.makeNoteConfig(fileName, noteLetter, midiNote)

    def deleteNoteConfig(self, midiNote, noteLetter):
        self._mediaPoolConf.deleteNoteConfig(midiNote, noteLetter)

    def getXmlString(self):
        return self._playerConfigurationTree.getConfigurationXMLString()

    def setSelectedMidiChannel(self, midiChannel):
        self._selectedMidiChannel = midiChannel

    def getSelectedMidiChannel(self):
        return self._selectedMidiChannel

    def getMidiSender(self):
        return self._midiSender

    def getLatestMidiControllers(self):
        if(self._latestMidiControllerRequestCallback != None):
            return self._latestMidiControllerRequestCallback()

    def getEffectState(self, channel, note):
        if(self._effectStateRequestCallback != None):
            return self._effectStateRequestCallback(channel, note)

    def printConfiguration(self):
        print self.getXmlString()



