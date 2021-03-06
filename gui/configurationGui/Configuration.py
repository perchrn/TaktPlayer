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
        self._guiConfigurationTree.setSelfclosingTags(['video', 'player1', 'player2', 'player3', 'gui'])
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

        self._guiPlayer1Config = self._guiConfigurationTree.addChildUnique("Player1")
        self._guiPlayer1Config.addTextParameter("PlayerHost1", "127.0.0.1")
        self._guiPlayer1Config.addIntParameter("MidiPort1", 2020)
        self._guiPlayer1Config.addIntParameter("WebPort1", 2021)
        self._guiPlayer1Config.addBoolParameter("MidiEnabled1", True)
        self._guiPlayer2Config = self._guiConfigurationTree.addChildUnique("Player2")
        self._guiPlayer2Config.addTextParameter("PlayerHost2", "127.0.0.1")
        self._guiPlayer2Config.addIntParameter("MidiPort2", 2020)
        self._guiPlayer2Config.addIntParameter("WebPort2", 2021)
        self._guiPlayer2Config.addBoolParameter("MidiEnabled2", True)
        self._guiPlayer3Config = self._guiConfigurationTree.addChildUnique("Player3")
        self._guiPlayer3Config.addTextParameter("PlayerHost3", "127.0.0.1")
        self._guiPlayer3Config.addIntParameter("MidiPort3", 2020)
        self._guiPlayer3Config.addIntParameter("WebPort3", 2021)
        self._guiPlayer3Config.addBoolParameter("MidiEnabled3", True)
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
        self._guiConfig.addBoolParameter("ShowDMX", False)
        self._guiConfig.addBoolParameter("ShowKinect", False)
        self._cueServerConfig = self._guiConfigurationTree.addChildUnique("CueServer")
        self._cueServerConfig.addTextParameter("CueWebBindAddress", "0.0.0.0")
        self._cueServerConfig.addIntParameter("CueWebPort", 2222)
        self._cueServerConfig.addTextParameter("CueStreamList", "Main")

    def setPlayerConfig(self, hostId, playerHost, midiPort, webPort, midiOn):
        if(hostId == 3):
            self._guiPlayer3Config.setValue("PlayerHost3", playerHost)
            self._guiPlayer3Config.setValue("MidiPort3", midiPort)
            self._guiPlayer3Config.setValue("WebPort3", webPort)
            self._guiPlayer3Config.setValue("MidiEnabled3", midiOn)
        elif(hostId == 2):
            self._guiPlayer2Config.setValue("PlayerHost2", playerHost)
            self._guiPlayer2Config.setValue("MidiPort2", midiPort)
            self._guiPlayer2Config.setValue("WebPort2", webPort)
            self._guiPlayer2Config.setValue("MidiEnabled2", midiOn)
        else:
            self._guiPlayer1Config.setValue("PlayerHost1", playerHost)
            self._guiPlayer1Config.setValue("MidiPort1", midiPort)
            self._guiPlayer1Config.setValue("WebPort1", webPort)
            self._guiPlayer1Config.setValue("MidiEnabled1", midiOn)

    def setVideoConfig(self, videoDir, ffmpegBinary, ffmpegH264Options, scaleX, scaleY):
        self._guiVideoConfig.setValue("VideoDir", videoDir)
        self._guiVideoConfig.setValue("FfmpegBinary", ffmpegBinary)
        self._guiVideoConfig.setValue("FfmpegH264Options", ffmpegH264Options)
        self._guiVideoConfig.setValue("ScaleVideoX", scaleX)
        self._guiVideoConfig.setValue("ScaleVideoY", scaleY)

    def setGuiConfig(self, autoSend, midiBcast, midiBindAddress, midiPort, winSize, winPos, showDmx, showKinect):
        self._guiConfig.setValue("AutoSend", autoSend)
        self._guiConfig.setValue("MidiBroadcast", midiBcast)
        self._guiConfig.setValue("MidiBindAddress", midiBindAddress)
        self._guiConfig.setValue("MidiPort", midiPort)
        self._guiConfig.setValue("WindowSize", winSize)
        self._guiConfig.setValue("WindowPosition", winPos)
        self._guiConfig.setValue("ShowDMX", showDmx)
        self._guiConfig.setValue("ShowKinect", showKinect)

    def saveConfig(self):
        self._guiConfigurationTree.saveConfigFile(self._configurationFile)

    def setupMidiSender(self):
        host, port, mode = self.getMidiConfig(1)
        self._midiSender = SendMidiOverNet(host, port, mode)

    def getWebConfig(self, hostId):
        if(hostId == 3):
            host = self._guiPlayer3Config.getValue("PlayerHost3")
            port = self._guiPlayer3Config.getValue("WebPort3")
        elif(hostId == 2):
            host = self._guiPlayer2Config.getValue("PlayerHost2")
            port = self._guiPlayer2Config.getValue("WebPort2")
        else:
            host = self._guiPlayer1Config.getValue("PlayerHost1")
            port = self._guiPlayer1Config.getValue("WebPort1")
        return (host, port)

    def getMidiConfig(self, hostId):
        if(hostId == 3):
            host = self._guiPlayer3Config.getValue("PlayerHost3")
            port = self._guiPlayer3Config.getValue("MidiPort3")
        elif(hostId == 2):
            host = self._guiPlayer2Config.getValue("PlayerHost2")
            port = self._guiPlayer2Config.getValue("MidiPort2")
        else:
            host = self._guiPlayer1Config.getValue("PlayerHost1")
            port = self._guiPlayer1Config.getValue("MidiPort1")
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

    def isShowDMX(self):
        return self._guiConfig.getValue("ShowDMX")

    def isShowKinect(self):
        return self._guiConfig.getValue("ShowKinect")

    def setLatestMidiControllerRequestCallback(self, callback):
        self._latestMidiControllerRequestCallback = callback

    def setEffectStateRequestCallback(self, callback):
        self._effectStateRequestCallback = callback

    def isMidiEnabled(self, hostId):
        if(hostId == 3):
            return self._guiPlayer3Config.getValue("MidiEnabled3")
        elif(hostId == 2):
            return self._guiPlayer2Config.getValue("MidiEnabled2")
        else:
            return self._guiPlayer1Config.getValue("MidiEnabled1")

    def setMidiEnable(self, newValue):
        self._guiConfig.setValue("MidiBroadcast", newValue)

    def isAutoSendEnabled(self):
        return self._guiConfig.getValue("AutoSend")

    def setAutoSendEnable(self, newValue):
        self._guiConfig.setValue("AutoSend", newValue)

    def getCueWebServerAddress(self):
        return self._cueServerConfig.getValue("CueWebBindAddress")

    def getCueWebServerPort(self):
        return self._cueServerConfig.getValue("CueWebPort")

    def getCueStreamList(self):
        return self._cueServerConfig.getValue("CueStreamList").split(",")

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



