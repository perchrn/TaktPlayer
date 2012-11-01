'''
Created on 6. feb. 2012

@author: pcn
'''
from configuration.ConfigurationHolder import ConfigurationHolder
from configurationGui.GlobalConfig import GlobalConfig
from configurationGui.MediaPoolConfig import MediaPoolConfig
from configurationGui.MediaMixerConfig import MediaMixerConfig
from network.SendMidiOverNet import SendMidiOverNet, SendModes
import os
import sys
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

    def setupSpecialModulations(self):
        self._mediaPoolConf.setupSpecialNoteModulations()
        self._globalConf.setupSpecialEffectModulations()

    def setupGuiConfiguration(self):
        taktPackageConfigDir = os.path.join(os.getcwd(), "config")
        if(sys.platform == "win32"):
            appDataDir = os.getenv('APPDATA')
            taktConfigDefaultDir = os.path.join(appDataDir, "TaktPlayer")
        elif(sys.platform == "darwin"):
            appDataDir = os.path.join(os.getenv('USERPROFILE') or os.getenv('HOME'), "Library")
            taktConfigDefaultDir = os.path.join(appDataDir, "TaktPlayer")
        else:
            appDataDir = os.getenv('USERPROFILE') or os.getenv('HOME')
            taktConfigDefaultDir = os.path.join(appDataDir, ".TaktPlayer")
        if(os.path.isdir(appDataDir) == True):
            if(os.path.isdir(taktConfigDefaultDir) == False):
                os.makedirs(taktConfigDefaultDir)
            if(os.path.isdir(taktConfigDefaultDir) == False):
                taktConfigDefaultDir = taktPackageConfigDir
                taktVideoDefaultDir = os.path.join(os.getcwd(), "testVideo")
            else:
                taktVideoDefaultDir = os.path.join(taktConfigDefaultDir, "Video")
                if(os.path.isdir(taktVideoDefaultDir) == False):
                    os.makedirs(taktVideoDefaultDir)
                if(os.path.isdir(taktVideoDefaultDir) == False):
                    taktVideoDefaultDir = os.path.join(os.getcwd(), "testVideo")
        else:
            taktConfigDefaultDir = taktPackageConfigDir
            taktVideoDefaultDir = os.path.join(os.getcwd(), "testVideo")
        print "*" * 100
        print "DEBUG pcn: appDataDir: " + str(appDataDir)
        print "DEBUG pcn: taktConfigDefaultDir: " + str(taktConfigDefaultDir)
        print "DEBUG pcn: taktVideoDefaultDir: " + str(taktVideoDefaultDir)
        print "*" * 100
        self._configurationDefaultDirectory = taktConfigDefaultDir

        self._guiPlayerConfig = self._guiConfigurationTree.addChildUnique("Player")
        self._guiPlayerConfig.addTextParameter("PlayerHost", "127.0.0.1")
        self._guiPlayerConfig.addIntParameter("MidiPort", 2020)
        self._guiPlayerConfig.addIntParameter("WebPort", 2021)
        self._guiPlayerConfig.addBoolParameter("MidiEnabled", True)
        self._guiVideoConfig = self._guiConfigurationTree.addChildUnique("Video")
        self._guiVideoConfig.addTextParameter("VideoDir", taktVideoDefaultDir)
        self._guiVideoConfig.addTextParameter("FfmpegBinary", os.path.normpath("ffmpeg"))
        self._guiVideoConfig.addIntParameter("ScaleVideoX", -1)
        self._guiVideoConfig.addIntParameter("ScaleVideoY", -1)
        self._guiConfig = self._guiConfigurationTree.addChildUnique("GUI")
        self._guiConfig.addBoolParameter("AutoSend", True)
        self._guiConfig.addBoolParameter("MidiBroadcast", True)
        self._guiConfig.addTextParameter("MidiBindAddress", "0.0.0.0")
        self._guiConfig.addIntParameter("MidiPort", 2022)
        self._guiConfig.addTextParameter("WindowSize", "800,600") #default, xpos,ypos, 0,0 etc.
        self._guiConfig.addTextParameter("WindowPosition", "-1,-1") #auto, xpos,ypos, 0,0 etc.

    def setPlayerConfig(self, playerHost, midiPort, webPort, midiOn):
        self._guiPlayerConfig.setValue("PlayerHost", playerHost)
        self._guiPlayerConfig.setValue("MidiPort", midiPort)
        self._guiPlayerConfig.setValue("WebPort", webPort)
        self._guiPlayerConfig.setValue("MidiEnabled", midiOn)

    def setVideoConfig(self, videoDir, ffmpegBinary, scaleX, scaleY):
        self._guiVideoConfig.setValue("VideoDir", videoDir)
        self._guiVideoConfig.setValue("FfmpegBinary", ffmpegBinary)
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

    def getGuiConfigDir(self):
        return self._guiConfig.getValue("ConfigDir")

    def getGuiVideoDir(self):
        return self._guiVideoConfig.getValue("VideoDir")

    def getFfmpegBinary(self):
        return self._guiVideoConfig.getValue("FfmpegBinary")

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

    def getSpecialModulationHolder(self):
        return self._globalConf.getSpecialModulationHolder()

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

    def getTimeModulationTemplate(self, configName):
        return self._globalConf.getTimeModulationTemplate(configName)

    def getTimeModulationTemplateByIndex(self, index):
        return self._globalConf.getTimeModulationTemplateByIndex(index)

    def duplicateTimeModulationTemplate(self, configName):
        return self._globalConf.duplicateTimeModulationTemplate(configName)

    def makeTimeModulationTemplate(self, saveName, mode, modulation, rangeVal, rangeQuantize):
        return self._globalConf.makeTimeModulationTemplate(saveName, mode, modulation, rangeVal, rangeQuantize)

    def deleteTimeModulationTemplate(self, configName):
        return self._globalConf.deleteTimeModulationTemplate(configName)

    def renameTimeModulationTemplateUsed(self, oldName, newName):
        self._mediaPoolConf.renameTimeModulationTemplateUsed(oldName, newName)

    def checkIfNameIsDefaultTimeModulationName(self, configName):
        return self._globalConf.checkIfNameIsDefaultTimeModulationName(configName)

    def verifyTimeModulationTemplateUsed(self):
        effectsConfigNames =  self._globalConf.getTimeModulationTemplateNamesList()
        self._mediaPoolConf.verifyTimeModulationTemplateUsed(effectsConfigNames)

    def countNumberOfTimeTimeModulationTemplateUsed(self, configName):
        returnNumber = 0
        returnNumber += self._mediaPoolConf.countNumberOfTimeTimeModulationTemplateUsed(configName)
        return returnNumber

    def getTimeModulationChoices(self):
        return self._globalConf.getTimeModulationChoices()

    def setupTimeModulationsGui(self, plane, sizer, parentSizer, parentClass):
        self._globalConf.setupTimeModulationsGui(plane, sizer, parentSizer, parentClass)

    def setupTimeModulationsListGui(self, plane, sizer, parentSizer, parentClass):
        self._globalConf.setupTimeModulationsListGui(plane, sizer, parentSizer, parentClass)

    def updateTimeModulationGui(self, configName, midiNote, editFieldWidget = None):
        self._globalConf.updateTimeModulationGui(configName, midiNote, editFieldWidget)

    def updateTimeModulationList(self, selectedName):
        self._globalConf.updateTimeModulationList(selectedName)

    def getEffectConfiguration(self):
        return self._globalConf.getEffectConfiguration()

    def getEffectChoices(self):
        return self._globalConf.getEffectChoices()

    def setupEffectsGui(self, plane, sizer, parentSizer, parentClass):
        self._globalConf.setupEffectsGui(plane, sizer, parentSizer, parentClass)

    def setupEffectsListGui(self, plane, sizer, parentSizer, parentClass):
        self._globalConf.setupEffectsListGui(plane, sizer, parentSizer, parentClass)

    def setupEffectImageListGui(self, plane, sizer, parentSizer, parentClass):
        self._globalConf.setupEffectImageListGui(plane, sizer, parentSizer, parentClass)

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

    def updateEffectsGui(self, configName, midiNote, editFieldName, editFieldWidget = None):
        self._globalConf.updateEffectsGui(configName, midiNote, editFieldName, editFieldWidget)

    def updateEffectsSliders(self, valuesString, guiString):
        self._globalConf.updateEffectsSliders(valuesString, guiString)

    def showSliderGuiEditButton(self, show = True):
        self._globalConf.showSliderGuiEditButton(show)

    def updateEffectList(self, selectedName):
        self._globalConf.updateEffectList(selectedName)

    def updateEffectImageList(self):
        self._globalConf.updateEffectImageList()

    def updateEffectListHeight(self, height):
        self._globalConf.updateEffectListHeight(height)

    def getDraggedFxName(self):
        return self._globalConf.getDraggedFxName()

    def getDraggedNoteName(self):
        return self._draggedNoteName

    def setDraggedNoteName(self, draggedNoteName):
        self._draggedNoteName = draggedNoteName

    def getEffectTemplate(self, configName):
        return self._globalConf.getEffectTemplate(configName)

    def getEffectTemplateByIndex(self, index):
        return self._globalConf.getEffectTemplateByIndex(index)

    def getFadeTemplate(self, configName):
        return self._globalConf.getFadeTemplate(configName)

    def getFadeTemplateByIndex(self, index):
        return self._globalConf.getFadeTemplateByIndex(index)

    def getEffectImage(self, fileName):
        return self._globalConf.getEffectImage(fileName)

    def getEffectImageByIndex(self, index):
        return self._globalConf.getEffectImageByIndex(index)

    def makeEffectTemplate(self, saveName, effectName, ammountMod, arg1Mod, arg2Mod, arg3Mod, arg4Mod, startValuesString):
        return self._globalConf.makeEffectTemplate(saveName, effectName, ammountMod, arg1Mod, arg2Mod, arg3Mod, arg4Mod, startValuesString)

    def makeFadeTemplate(self, saveName, fadeMode, fadeMod, levelMod):
        return self._globalConf.makeFadeTemplate(saveName, fadeMode, fadeMod, levelMod)

    def deleteEffectTemplate(self, configName):
        return self._globalConf.deleteEffectTemplate(configName)

    def deleteFadeTemplate(self, configName):
        return self._globalConf.deleteFadeTemplate(configName)

    def deleteEffectImage(self, fileName):
        return self._globalConf.deleteEffectImage(fileName)

    def duplicateEffectTemplate(self, configName):
        return self._globalConf.duplicateEffectTemplate(configName)

    def duplicateFadeTemplate(self, configName):
        return self._globalConf.duplicateFadeTemplate(configName)

    def makeNewEffectImage(self, fileName):
        return self._globalConf.makeNewEffectImage(fileName)

    def getEffectImageFileListString(self):
        return self._globalConf.getEffectImageFileListString()

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

    def updateModulationGui(self, modulationString, widget, closeCallback, saveCallback, saveArgument = None):
        self._globalConf.updateModulationGui(modulationString, widget, closeCallback, saveCallback, saveArgument)

    def updateModulationGuiButton(self, widget, modulationString):
        self._globalConf.updateModulationGuiButton(modulationString, widget)

    def stopModulationGui(self):
        self._globalConf.stopModulationGui()

    def startSlidersUpdate(self):
        self._globalConf.startSlidersUpdate()

    def stopSlidersUpdate(self):
        self._globalConf.stopSlidersUpdate()

    def updateFadeGui(self, configName, editFieldName = None, editFieldWidget = None):
        self._globalConf.updateFadeGui(configName, editFieldName, editFieldWidget)

    def updateFadeList(self, selectedName):
        self._globalConf.updateFadeList(selectedName)

    def updateFadeGuiButtons(self, configName, modeWidget, modulationWidget, levelWidget):
        self._globalConf.updateFadeGuiButtons(configName, modeWidget, modulationWidget, levelWidget)

    def getFadeChoices(self):
        return self._globalConf.getFadeChoices()

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



