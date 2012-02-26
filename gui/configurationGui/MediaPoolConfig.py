'''
Created on 6. feb. 2012

@author: pcn
'''
from midi.MidiUtilities import noteToNoteString, noteStringToNoteNumber
import wx
from widgets.PcnImageButton import PcnKeyboardButton, PcnImageButton,\
    addTrackButtonFrame
import os
from video.media.MediaFileModes import VideoLoopMode, ImageSequenceMode,\
    MediaTypes, MixMode, getMixModeFromName
from video.EffectModes import getEffectId, EffectTypes


class MediaPoolConfig(object):
    def __init__(self, configParent):
        self._configurationTree = configParent.addChildUnique("MediaPool")

        self._mediaPool = []
        for i in range(128): #@UnusedVariable
            self._mediaPool.append(None)

        self.loadMediaFromConfiguration()

    def _getConfiguration(self):
        self.loadMediaFromConfiguration()

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print "mediaPool config is updated..."
            self._getConfiguration()
            self._configurationTree.resetConfigurationUpdated()

    def loadMediaFromConfiguration(self):
        mediaPoolState = []
        for i in range(128):
            mediaPoolState.append(False)
        mediaFileChildren = self._configurationTree.findXmlChildrenList("MediaFile")
        if(mediaFileChildren != None):
            for xmlConfig in mediaFileChildren:
                midiNote = self.addXmlMedia(xmlConfig)
                mediaPoolState[midiNote] = True
        for i in range(128):
            mediaState = mediaPoolState[i]
            if(mediaState == False):
                noteLetter = noteToNoteString(i)
                self.addMedia("", noteLetter)

    def addXmlMedia(self, xmlConfig):
        fileName = xmlConfig.get("filename")
        noteLetter = xmlConfig.get("note")
        print "Adding " + str(fileName) + " - " + str(noteLetter)
        return self.addMedia(fileName, noteLetter, xmlConfig)

    def addMedia(self, fileName, noteLetter, xmlConfig = None):
        midiNote = noteStringToNoteNumber(noteLetter)
        midiNote = min(max(midiNote, 0), 127)

        #remove old:
        if(self._mediaPool[midiNote] != None):
            if(self._configurationTree.removeChildUniqueId("MediaFile", "Note", noteLetter) == False):
                print "Config child NOT removed -!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!"
            else:
                print "Config child removed OK"

        if(len(fileName) <= 0):
            self._mediaPool[midiNote] = None
        else:
            self._mediaPool[midiNote] = MediaFile(self._configurationTree, fileName, noteLetter, midiNote, xmlConfig)
        return midiNote

    def getNoteConfiguration(self, noteId):
        noteId = min(max(noteId, 0), 127)
        return self._mediaPool[noteId]

    def makeNoteConfig(self, fileName, noteLetter, midiNote):
        if((midiNote >= 0) and (midiNote < 128)):
            print "Making note: %s !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" % midiNote
            newMediaFile = MediaFile(self._configurationTree, fileName, noteLetter, midiNote, None)
            self._mediaPool[midiNote] = newMediaFile
            return newMediaFile
        return None

    def countNumberOfTimeEffectTemplateUsed(self, effectConfigName):
        returnNumer = 0
        for noteConfig in self._mediaPool:
            if(noteConfig != None):
                returnNumer += noteConfig.countNumberOfTimeEffectTemplateUsed(effectConfigName)
        return returnNumer

    def countNumberOfTimeFadeTemplateUsed(self, fadeConfigName):
        returnNumer = 0
        for noteConfig in self._mediaPool:
            if(noteConfig != None):
                returnNumer += noteConfig.countNumberOfTimeFadeTemplateUsed(fadeConfigName)
        return returnNumer

    def renameEffectTemplateUsed(self, oldName, newName):
        for noteConfig in self._mediaPool:
            if(noteConfig != None):
                noteConfig.renameEffectTemplateUsed(oldName, newName)

    def renameFadeTemplateUsed(self, oldName, newName):
        for noteConfig in self._mediaPool:
            if(noteConfig != None):
                noteConfig.renameFadeTemplateUsed(oldName, newName)

    def verifyEffectTemplateUsed(self, effectConfigNameList):
        for noteConfig in self._mediaPool:
            if(noteConfig != None):
                noteConfig.verifyEffectTemplateUsed(effectConfigNameList)

    def verifyFadeTemplateUsed(self, fadeConfigNameList):
        for noteConfig in self._mediaPool:
            if(noteConfig != None):
                noteConfig.verifyFadeTemplateUsed(fadeConfigNameList)

class MediaFile(object):
    def __init__(self, configParent, fileName, noteLetter, midiNote, xmlConfig):
        mediaType = None
        if(xmlConfig != None):
            mediaType = xmlConfig.get("type")
        if(mediaType == None):
            mediaType = "VideoLoop"
        self._configurationTree = configParent.addChildUniqueId("MediaFile", "Note", noteLetter, midiNote)
        self._configurationTree.addTextParameter("FileName", "")
        self._configurationTree.setValue("FileName", fileName)
        self._configurationTree.addTextParameter("Type", mediaType)
        self._configurationTree.addFloatParameter("SyncLength", 4.0) #Default one bar (re calculated on load)
        self._configurationTree.addFloatParameter("QuantizeLength", 4.0)#Default one bar
        self._configurationTree.addTextParameter("MixMode", "Add")#Default Add
        self._defaultEffect1SettingsName = "MediaDefault1"
        self._configurationTree.addTextParameter("Effect1Config", self._defaultEffect1SettingsName)#Default MediaDefault1
        self._defaultEffect2SettingsName = "MediaDefault2"
        self._configurationTree.addTextParameter("Effect2Config", self._defaultEffect2SettingsName)#Default MediaDefault2
        self._defaultFadeSettingsName = "Default"
        self._configurationTree.addTextParameter("FadeConfig", self._defaultFadeSettingsName)#Default Default
        if(mediaType == "VideoLoop"):
            self._configurationTree.addTextParameter("LoopMode", "Normal")
        elif(mediaType == "ImageSequence"):
            self._configurationTree.addTextParameter("SequenceMode", "Time")
            self._configurationTree.addTextParameter("PlayBackModulation", "None")
        if(xmlConfig != None):
            self._configurationTree._updateFromXml(xmlConfig)

    def getConfig(self):
        return self._configurationTree

    def updateFileName(self, fileName, isVideoFile):
        self._configurationTree.setValue("FileName", fileName)
        if(isVideoFile == False):
            self._configurationTree.setValue("Type", "Image")
            self._configurationTree.removeParameter("LoopMode")
            self._configurationTree.removeParameter("SequenceMode")
            self._configurationTree.removeParameter("PlayBackModulation")
        else:
            oldType = self._configurationTree.getValue("Type")
            if((oldType == "Image") or (oldType == "Camera")):
                self._configurationTree.setValue("Type", "VideoLoop")
                oldloopMode = self._configurationTree.getValue("LoopMode")
                if(oldloopMode == None):
                    self._configurationTree.setValue("LoopMode", "Normal")
                self._configurationTree.removeParameter("SequenceMode")
                self._configurationTree.removeParameter("PlayBackModulation")

    def getMixMode(self):
        return self._configurationTree.getValue("MixMode")

    def updateFrom(self, sourceMediaFile, dontChangeNote = True):
        sourceConfigTree = sourceMediaFile.getConfig()
        self._configurationTree.setValue("FileName", sourceConfigTree.getValue("FileName"))
        mediaType = sourceConfigTree.getValue("Type")
        self._configurationTree.setValue("Type", mediaType)
        self._configurationTree.setValue("SyncLength", sourceConfigTree.getValue("SyncLength"))
        self._configurationTree.setValue("QuantizeLength", sourceConfigTree.getValue("QuantizeLength"))
        self._configurationTree.setValue("MixMode", sourceConfigTree.getValue("MixMode"))
        self._configurationTree.setValue("Effect1Config", sourceConfigTree.getValue("Effect1Config"))
        self._configurationTree.setValue("Effect2Config", sourceConfigTree.getValue("Effect2Config"))
        self._configurationTree.setValue("FadeConfig", sourceConfigTree.getValue("FadeConfig"))

        if(mediaType == "VideoLoop"):
            self._configurationTree.addTextParameter("LoopMode", "Normal")
            loopMode = sourceConfigTree.getValue("LoopMode")
            if(loopMode != None):
                self._configurationTree.setValue("LoopMode", loopMode)
        else:
            self._configurationTree.removeParameter("LoopMode")

        if(mediaType == "ImageSequence"):
            self._configurationTree.addTextParameter("SequenceMode", "Time")
            self._configurationTree.addTextParameter("PlayBackModulation", "None")
            sequenceMode = sourceConfigTree.getValue("SequenceMode")
            if(sequenceMode != None):
                self._configurationTree.setValue("SequenceMode", sequenceMode)
            playBackMod = sourceConfigTree.getValue("PlayBackModulation")
            if(playBackMod != None):
                self._configurationTree.setValue("PlayBackModulation", playBackMod)
        else:
            self._configurationTree.removeParameter("SequenceMode")
            self._configurationTree.removeParameter("PlayBackModulation")
        
    def countNumberOfTimeEffectTemplateUsed(self, effectsConfigName):
        returnNumber = 0
        for configName in ["Effect1Config", "Effect2Config"]:
            usedConfigName = self._configurationTree.getValue(configName)
            if(usedConfigName == effectsConfigName):
                returnNumber += 1
        return returnNumber

    def countNumberOfTimeFadeTemplateUsed(self, fadeConfigName):
        returnNumber = 0
        for configName in ["FadeConfig"]:
            usedConfigName = self._configurationTree.getValue(configName)
            if(usedConfigName == fadeConfigName):
                returnNumber += 1
        return returnNumber

    def renameEffectTemplateUsed(self, oldName, newName):
        for configName in ["Effect1Config", "Effect2Config"]:
            usedConfigName = self._configurationTree.getValue(configName)
            if(usedConfigName == oldName):
                self._configurationTree.setValue(configName, newName)

    def renameFadeTemplateUsed(self, oldName, newName):
        for configName in ["FadeConfig"]:
            usedConfigName = self._configurationTree.getValue(configName)
            if(usedConfigName == oldName):
                self._configurationTree.setValue(configName, newName)

    def verifyEffectTemplateUsed(self, effectConfigNameList):
        usedConfigName = self._configurationTree.getValue("Effect1Config")
        nameOk = False
        for configName in effectConfigNameList:
            if(usedConfigName == configName):
                nameOk = True
                break
        if(nameOk == False):
            self._configurationTree.setValue("Effect1Config", self._defaultEffect1SettingsName)
        usedConfigName = self._configurationTree.getValue("Effect2Config")
        nameOk = False
        for configName in effectConfigNameList:
            if(usedConfigName == configName):
                nameOk = True
                break
        if(nameOk == False):
            self._configurationTree.setValue("Effect2Config", self._defaultEffect2SettingsName)

    def verifyFadeTemplateUsed(self, fadeConfigNameList):
        usedConfigName = self._configurationTree.getValue("FadeConfig")
        nameOk = False
        for configName in fadeConfigNameList:
            if(usedConfigName == configName):
                nameOk = True
                break
        if(nameOk == False):
            self._configurationTree.setValue("FadeConfig", self._defaultFadeSettingsName)

class MediaFileGui(object): #@UndefinedVariable
    def __init__(self, parentPlane, parentSizer, mainConfig, trackGui):
        self._parentPlane = parentPlane
        self._parentSizer = parentSizer
        self._mainConfig = mainConfig
        self._trackGui = trackGui
        self._mediaFileGuiPanel = wx.Panel(self._parentPlane, wx.ID_ANY) #@UndefinedVariable

        self._trackThumbnailBitmap = wx.Bitmap("graphics/blackClip.png") #@UndefinedVariable

        self._blankModeBitmap = wx.Bitmap("graphics/modeEmpty.png") #@UndefinedVariable
        self._modeBitmapCamera = wx.Bitmap("graphics/modeCamera.png") #@UndefinedVariable
        self._modeBitmapImage = wx.Bitmap("graphics/modeImage.png") #@UndefinedVariable
        self._modeBitmapImageScroll = wx.Bitmap("graphics/modeImageScroll.png") #@UndefinedVariable
        self._modeBitmapImageSeqModulation = wx.Bitmap("graphics/modeImageSeqModulation.png") #@UndefinedVariable
        self._modeBitmapImageSeqReTrigger = wx.Bitmap("graphics/modeImageSeqReTrigger.png") #@UndefinedVariable
        self._modeBitmapImageSeqTime = wx.Bitmap("graphics/modeImageSeqTime.png") #@UndefinedVariable
        self._modeBitmapLoop = wx.Bitmap("graphics/modeLoop.png") #@UndefinedVariable
        self._modeBitmapLoopReverse = wx.Bitmap("graphics/modeLoopReverse.png") #@UndefinedVariable
        self._modeBitmapPingPong = wx.Bitmap("graphics/modePingPong.png") #@UndefinedVariable
        self._modeBitmapPingPongReverse = wx.Bitmap("graphics/modePingPongReverse.png") #@UndefinedVariable
        self._modeBitmapPlayOnce = wx.Bitmap("graphics/modePlayOnce.png") #@UndefinedVariable
        self._modeBitmapPlayOnceReverse = wx.Bitmap("graphics/modePlayOnceReverse.png") #@UndefinedVariable

        self._blankMixBitmap = wx.Bitmap("graphics/mixEmpty.png") #@UndefinedVariable
        self._mixBitmapAdd = wx.Bitmap("graphics/mixAdd.png") #@UndefinedVariable
        self._mixBitmapDefault = wx.Bitmap("graphics/mixDefault.png") #@UndefinedVariable
        self._mixBitmapLumaKey = wx.Bitmap("graphics/mixLumaKey.png") #@UndefinedVariable
        self._mixBitmapMultiply = wx.Bitmap("graphics/mixMultiply.png") #@UndefinedVariable
        self._mixBitmapReplace = wx.Bitmap("graphics/mixReplace.png") #@UndefinedVariable
        self._mixBitmapSubtract = wx.Bitmap("graphics/mixSubtract.png") #@UndefinedVariable

        self._blankFxBitmap = wx.Bitmap("graphics/fxEmpty.png") #@UndefinedVariable
        self._fxBitmapBlur = wx.Bitmap("graphics/fxBlur.png") #@UndefinedVariable
        self._fxBitmapBlurMul = wx.Bitmap("graphics/fxBlurMultiply.png") #@UndefinedVariable
        self._fxBitmapColorize = wx.Bitmap("graphics/fxColorize.png") #@UndefinedVariable
        self._fxBitmapContrast = wx.Bitmap("graphics/fxContrast.png") #@UndefinedVariable
        self._fxBitmapDeSat = wx.Bitmap("graphics/fxDeSat.png") #@UndefinedVariable
        self._fxBitmapDist = wx.Bitmap("graphics/fxDist.png") #@UndefinedVariable
        self._fxBitmapEdge = wx.Bitmap("graphics/fxEdge.png") #@UndefinedVariable
        self._fxBitmapFlip = wx.Bitmap("graphics/fxFlip.png") #@UndefinedVariable
        self._fxBitmapHueSat = wx.Bitmap("graphics/fxHueSat.png") #@UndefinedVariable
        self._fxBitmapInverse = wx.Bitmap("graphics/fxInverse.png") #@UndefinedVariable
        self._fxBitmapMirror = wx.Bitmap("graphics/fxMirror.png") #@UndefinedVariable
        self._fxBitmapRotate = wx.Bitmap("graphics/fxRotate.png") #@UndefinedVariable
        self._fxBitmapThreshold = wx.Bitmap("graphics/fxThreshold.png") #@UndefinedVariable
        self._fxBitmapZoom = wx.Bitmap("graphics/fxZoom.png") #@UndefinedVariable

        self._config = None
        self._mixModes = MixMode()
        self._loopModes = VideoLoopMode()
        self._sequenceModes = ImageSequenceMode()
        self._typeModes = MediaTypes()

        self._configSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._trackOverviewGuiPlane = wx.Panel(self._mediaFileGuiPanel, wx.ID_ANY, size=(84,360)) #@UndefinedVariable
        self._trackGuiPlane = wx.Panel(self._mediaFileGuiPanel, wx.ID_ANY, size=(300,-1)) #@UndefinedVariable
        self._noteConfigPanel = wx.Panel(self._mediaFileGuiPanel, wx.ID_ANY, size=(300,-1)) #@UndefinedVariable
        self._effectConfigPanel = wx.Panel(self._mediaFileGuiPanel, wx.ID_ANY, size=(300,-1)) #@UndefinedVariable
        self._fadeConfigPanel = wx.Panel(self._mediaFileGuiPanel, wx.ID_ANY, size=(300,-1)) #@UndefinedVariable
        self._moulationConfigPanel = wx.Panel(self._mediaFileGuiPanel, wx.ID_ANY, size=(300,-1)) #@UndefinedVariable
        self._slidersPanel = wx.Panel(self._mediaFileGuiPanel, wx.ID_ANY, size=(300,-1)) #@UndefinedVariable

        self._configSizer.Add(self._trackOverviewGuiPlane)
        self._configSizer.Add(self._trackGuiPlane)
        self._configSizer.Add(self._noteConfigPanel)
        self._configSizer.Add(self._effectConfigPanel)
        self._configSizer.Add(self._fadeConfigPanel)
        self._configSizer.Add(self._moulationConfigPanel)
        self._configSizer.Add(self._slidersPanel)

        self._configSizer.Hide(self._trackGuiPlane)
        self._configSizer.Hide(self._noteConfigPanel)
        self._configSizer.Hide(self._effectConfigPanel)
        self._configSizer.Hide(self._fadeConfigPanel)
        self._configSizer.Hide(self._moulationConfigPanel)
        self._configSizer.Hide(self._slidersPanel)
        self._mediaFileGuiPanel.SetSizer(self._configSizer)

        self._trackOverviewGuiPlane.SetBackgroundColour((170,170,170))
        self.setupTrackClipOverviewGui(self._trackOverviewGuiPlane, self)
        self._trackGui.setupTrackOverviewGui(self._trackOverviewGuiPlane, self)

        self._trackGuiPlane.SetBackgroundColour((220,220,220))
        self._trackGuiSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._trackGuiPlane.SetSizer(self._trackGuiSizer)
        self._trackGui.setupTrackGui(self._trackGuiPlane, self._trackGuiSizer, self._configSizer, self)

        self._noteConfigPanel.SetBackgroundColour((0,120,120))
        self._noteConfigSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._noteConfigPanel.SetSizer(self._noteConfigSizer)

        self._effectConfigPanel.SetBackgroundColour((120,0,120))
        self._effectConfigSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._effectConfigPanel.SetSizer(self._effectConfigSizer)
        self._mainConfig.setupEffectsGui(self._effectConfigPanel, self._effectConfigSizer, self._configSizer, self)

        self._fadeConfigPanel.SetBackgroundColour((120,120,200))
        self._fadeConfigSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._fadeConfigPanel.SetSizer(self._fadeConfigSizer)
        self._mainConfig.setupFadeGui(self._fadeConfigPanel, self._fadeConfigSizer, self._configSizer, self)

        self._moulationConfigPanel.SetBackgroundColour((120,200,200))
        self._moulationConfigSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._moulationConfigPanel.SetSizer(self._moulationConfigSizer)
        self._mainConfig.setupModulationGui(self._moulationConfigPanel, self._moulationConfigSizer, self._configSizer, self)

        self._slidersPanel.SetBackgroundColour((120,120,0))
        self._slidersSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._slidersPanel.SetSizer(self._slidersSizer)
        self._mainConfig.setupEffectsSlidersGui(self._slidersPanel, self._slidersSizer, self._configSizer, self)

        self._fileName = ""
        self._cameraId = 0
        fileNameSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._fileNameLabel = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "FileName:") #@UndefinedVariable
        self._fileNameField = wx.TextCtrl(self._noteConfigPanel, wx.ID_ANY, self._fileName, size=(200, -1)) #@UndefinedVariable
        self._fileNameField.SetEditable(False)
        self._fileNameField.SetBackgroundColour((232,232,232))
        fileOpenButton = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Select', size=(60,-1)) #@UndefinedVariable
        fileOpenButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._noteConfigPanel.Bind(wx.EVT_BUTTON, self._onOpenFile, id=fileOpenButton.GetId()) #@UndefinedVariable
        fileNameSizer.Add(self._fileNameLabel, 1, wx.ALL, 5) #@UndefinedVariable
        fileNameSizer.Add(self._fileNameField, 2, wx.ALL, 5) #@UndefinedVariable
        fileNameSizer.Add(fileOpenButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(fileNameSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        typeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText2 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Type:") #@UndefinedVariable
        self._typeField = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["VideoLoop"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateTypeChoices(self._typeField, "VideoLoop", "VideoLoop")
        typeHelpButton = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        typeHelpButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._noteConfigPanel.Bind(wx.EVT_BUTTON, self._onTypeHelp, id=typeHelpButton.GetId()) #@UndefinedVariable
        typeSizer.Add(tmpText2, 1, wx.ALL, 5) #@UndefinedVariable
        typeSizer.Add(self._typeField, 2, wx.ALL, 5) #@UndefinedVariable
        typeSizer.Add(typeHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(typeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._noteConfigPanel.Bind(wx.EVT_COMBOBOX, self._onTypeChosen, id=self._typeField.GetId()) #@UndefinedVariable

        self._subModeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._subModeLabel = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Loop mode:") #@UndefinedVariable
        self._subModeField = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["Normal"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateLoopModeChoices(self._subModeField, "Normal", "Normal")
        subModeHelpButton = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        subModeHelpButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._noteConfigPanel.Bind(wx.EVT_BUTTON, self._onSubModeHelp, id=subModeHelpButton.GetId()) #@UndefinedVariable
        self._subModeSizer.Add(self._subModeLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._subModeSizer.Add(self._subModeField, 2, wx.ALL, 5) #@UndefinedVariable
        self._subModeSizer.Add(subModeHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._subModeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._noteConfigPanel.Bind(wx.EVT_COMBOBOX, self._onSubModeChosen, id=self._subModeField.GetId()) #@UndefinedVariable

        self._subModulationSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._subModulationLabel = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Playback modulation:") #@UndefinedVariable
        self._subModulationField = wx.TextCtrl(self._noteConfigPanel, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._subModulationField.SetInsertionPoint(0)
        self._subModulationEditButton = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Edit', size=(60,-1)) #@UndefinedVariable
        self._subModulationEditButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._noteConfigPanel.Bind(wx.EVT_BUTTON, self._onSubmodulationEdit, id=self._subModulationEditButton.GetId()) #@UndefinedVariable
        self._subModulationSizer.Add(self._subModulationLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._subModulationSizer.Add(self._subModulationField, 2, wx.ALL, 5) #@UndefinedVariable
        self._subModulationSizer.Add(self._subModulationEditButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._subModulationSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._midiNote = 24
        noteSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText3 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Note:") #@UndefinedVariable
        self._noteField = wx.TextCtrl(self._noteConfigPanel, wx.ID_ANY, noteToNoteString(self._midiNote), size=(200, -1)) #@UndefinedVariable
        self._noteField.SetEditable(False)
        self._noteField.SetBackgroundColour((232,232,232))
        noteHelpButton = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        noteHelpButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._noteConfigPanel.Bind(wx.EVT_BUTTON, self._onNoteHelp, id=noteHelpButton.GetId()) #@UndefinedVariable
        noteSizer.Add(tmpText3, 1, wx.ALL, 5) #@UndefinedVariable
        noteSizer.Add(self._noteField, 2, wx.ALL, 5) #@UndefinedVariable
        noteSizer.Add(noteHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(noteSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._syncSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText4 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Synchronization length:") #@UndefinedVariable
        self._syncField = wx.TextCtrl(self._noteConfigPanel, wx.ID_ANY, "4.0", size=(200, -1)) #@UndefinedVariable
        self._syncField.SetInsertionPoint(0)
        syncHelpButton = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        syncHelpButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._noteConfigPanel.Bind(wx.EVT_BUTTON, self._onSyncHelp, id=syncHelpButton.GetId()) #@UndefinedVariable
        self._syncSizer.Add(tmpText4, 1, wx.ALL, 5) #@UndefinedVariable
        self._syncSizer.Add(self._syncField, 2, wx.ALL, 5) #@UndefinedVariable
        self._syncSizer.Add(syncHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._syncSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        quantizeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText5 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Quantization:") #@UndefinedVariable
        self._quantizeField = wx.TextCtrl(self._noteConfigPanel, wx.ID_ANY, "1.0", size=(200, -1)) #@UndefinedVariable
        self._quantizeField.SetInsertionPoint(0)
        quantizeHelpButton = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        quantizeHelpButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._noteConfigPanel.Bind(wx.EVT_BUTTON, self._onQuantizeHelp, id=quantizeHelpButton.GetId()) #@UndefinedVariable
        quantizeSizer.Add(tmpText5, 1, wx.ALL, 5) #@UndefinedVariable
        quantizeSizer.Add(self._quantizeField, 2, wx.ALL, 5) #@UndefinedVariable
        quantizeSizer.Add(quantizeHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(quantizeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        mixSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText6 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Mix mode:") #@UndefinedVariable
        self._mixField = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["Add"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateMixModeChoices(self._mixField, "Add", "Add")
        mixHelpButton = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        mixHelpButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._noteConfigPanel.Bind(wx.EVT_BUTTON, self._onMixHelp, id=mixHelpButton.GetId()) #@UndefinedVariable
        mixSizer.Add(tmpText6, 1, wx.ALL, 5) #@UndefinedVariable
        mixSizer.Add(self._mixField, 2, wx.ALL, 5) #@UndefinedVariable
        mixSizer.Add(mixHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(mixSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        effect1Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Effect 1 template:") #@UndefinedVariable
        self._effect1Field = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["MediaDefault1"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateEffecChoices(self._effect1Field, "MediaDefault1", "MediaDefault1")
        self._effect1Button = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Edit', size=(60,-1)) #@UndefinedVariable
        self._effect1Button.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._noteConfigPanel.Bind(wx.EVT_BUTTON, self._onEffect1Edit, id=self._effect1Button.GetId()) #@UndefinedVariable
        effect1Sizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        effect1Sizer.Add(self._effect1Field, 2, wx.ALL, 5) #@UndefinedVariable
        effect1Sizer.Add(self._effect1Button, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(effect1Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        effect2Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Effect 2 template:") #@UndefinedVariable
        self._effect2Field = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["MediaDefault2"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateEffecChoices(self._effect2Field, "MediaDefault2", "MediaDefault2")
        self._effect2Button = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Edit', size=(60,-1)) #@UndefinedVariable
        self._effect2Button.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._noteConfigPanel.Bind(wx.EVT_BUTTON, self._onEffect2Edit, id=self._effect2Button.GetId()) #@UndefinedVariable
        effect2Sizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        effect2Sizer.Add(self._effect2Field, 2, wx.ALL, 5) #@UndefinedVariable
        effect2Sizer.Add(self._effect2Button, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(effect2Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        fadeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Fade template:") #@UndefinedVariable
        self._fadeField = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["Default"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateFadeChoices(self._fadeField, "Default", "Default")
        self._fadeButton = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Edit', size=(60,-1)) #@UndefinedVariable
        self._fadeButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._noteConfigPanel.Bind(wx.EVT_BUTTON, self._onFadeEdit, id=self._fadeButton.GetId()) #@UndefinedVariable
        fadeSizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        fadeSizer.Add(self._fadeField, 2, wx.ALL, 5) #@UndefinedVariable
        fadeSizer.Add(self._fadeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(fadeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Close') #@UndefinedVariable
        closeButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._noteConfigPanel.Bind(wx.EVT_BUTTON, self._onCloseButton, id=closeButton.GetId()) #@UndefinedVariable
        saveButton = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Save') #@UndefinedVariable
        saveButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._noteConfigPanel.Bind(wx.EVT_BUTTON, self._onSaveButton, id=saveButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 1, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(saveButton, 1, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._selectedEditor = self.EditSelection.Unselected
        self._type = "VideoLoop"
        self._setupSubConfig()

    def setupTrackClipOverviewGui(self, overviewPanel, parentClass):
        self._mainTrackOverviewPlane = overviewPanel

        wx.StaticText(self._mainTrackOverviewPlane, wx.ID_ANY, "TRACK CLIP:", pos=(4, 2)) #@UndefinedVariable
        self._overviewClipButton = PcnKeyboardButton(self._mainTrackOverviewPlane, self._trackThumbnailBitmap, (6, 16), wx.ID_ANY, size=(42, 32), isBlack=False) #@UndefinedVariable
        self._overviewClipButton.setFrqameAddingFunction(addTrackButtonFrame)
        self._overviewClipModeButton = PcnImageButton(self._mainTrackOverviewPlane, self._blankModeBitmap, self._blankModeBitmap, (52, 15), wx.ID_ANY, size=(25, 16)) #@UndefinedVariable
        self._overviewClipMixButton = PcnImageButton(self._mainTrackOverviewPlane, self._blankMixBitmap, self._blankMixBitmap, (52, 32), wx.ID_ANY, size=(25, 16)) #@UndefinedVariable
        self._overviewClipLengthLabel = wx.StaticText(self._mainTrackOverviewPlane, wx.ID_ANY, "L: N/A", pos=(12, 50)) #@UndefinedVariable
        self._overviewClipQuantizeLabel = wx.StaticText(self._mainTrackOverviewPlane, wx.ID_ANY, "Q: N/A", pos=(10, 62)) #@UndefinedVariable
        wx.StaticText(self._mainTrackOverviewPlane, wx.ID_ANY, "FX1:", pos=(8, 76)) #@UndefinedVariable
        wx.StaticText(self._mainTrackOverviewPlane, wx.ID_ANY, "FX2:", pos=(42, 76)) #@UndefinedVariable
        self._overviewFx1Button = PcnImageButton(self._mainTrackOverviewPlane, self._blankFxBitmap, self._blankFxBitmap, (10, 90), wx.ID_ANY, size=(32, 22)) #@UndefinedVariable
        self._overviewFx2Button = PcnImageButton(self._mainTrackOverviewPlane, self._blankFxBitmap, self._blankFxBitmap, (44, 90), wx.ID_ANY, size=(32, 22)) #@UndefinedVariable

    def getPlane(self):
        return self._mediaFileGuiPanel

    def getOverviewPlane(self):
        return self._trackOverviewGuiPlane

    def showNoteGui(self):
        self._configSizer.Show(self._noteConfigPanel)
        self._mediaFileGuiPanel.Layout()
        self._parentPlane.Layout()

    def hideNoteGui(self):
        self._configSizer.Hide(self._noteConfigPanel)
        self._mediaFileGuiPanel.Layout()
        self._parentPlane.Layout()
        #TODO: Note selection clear callback

    def showTrackGui(self):
        self._configSizer.Show(self._trackGuiPlane)
        self._mediaFileGuiPanel.Layout()
        self._parentPlane.Layout()

    def hideTrackGui(self):
        self._configSizer.Hide(self._trackGuiPlane)
        self._mediaFileGuiPanel.Layout()
        self._parentPlane.Layout()
        #TODO: Track selection clear callback

    class EditSelection():
        Unselected, Effect1, Effect2, Fade, ImageSeqModulation = range(5)

    def _onOpenFile(self, event):
        if(self._type == "Camera"):
            dlg = wx.NumberEntryDialog(self._mediaFileGuiPanel, "Choose camera input ID:", "ID:", "Camera input", self._cameraId, 0, 32) #@UndefinedVariable
            if dlg.ShowModal() == wx.ID_OK: #@UndefinedVariable
                self._cameraId = dlg.GetValue()
                self._fileNameField.SetValue(str(self._cameraId))
            dlg.Destroy()
        else:
            dlg = wx.FileDialog(self._mediaFileGuiPanel, "Choose a file", os.getcwd(), "", "*.*", wx.OPEN) #@UndefinedVariable
            if dlg.ShowModal() == wx.ID_OK: #@UndefinedVariable
                self._fileName = dlg.GetPath()
                self._fileNameField.SetValue(os.path.basename(self._fileName))
            dlg.Destroy()

    def _onTypeChosen(self, event):
        selectedTypeId = self._typeField.GetSelection()
        self._type = self._typeModes.getNames(selectedTypeId)
        if(self._type == "Camera"):
            self._fileNameField.SetValue(str(self._cameraId))
        else:
            self._fileNameField.SetValue(os.path.basename(self._fileName))
        self._setupSubConfig()

    def _onTypeHelp(self, event):
        text = """
Decides what kind of input this is.

VideoLoop:\tOur normal video file playing in loop.
Image:\t\tA single static image.
ImageSequence:\tA sequence of images.
Camera:\t\tCamera or capture input.
"""
        dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Type help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onSubModeChosen(self, event):
        if(self._type == "ImageSequence"):
            selectedSubModeId = self._subModeField.GetSelection()
            self._selectedSubMode = self._sequenceModes.getNames(selectedSubModeId)
            self._showOrHideSubModeModulation()

    def _onSubModeHelp(self, event):
        if(self._type == "VideoLoop"):
            text = """
Decides how we loop this video file.

Default:\tUses Add if no other mode has been selected by track.
Add:\tSums the images together.
Multiply:\tMultiplies the images together. Very handy for masking.
Lumakey:\tReplaces source everywhere the image is not black.
Replace:\tNo mixing. Just use this image.
"""
            dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Loop mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        elif(self._type == "ImageSequence"):
            text = """
Decides how we decide which image to show.

Time:\tShows each image synchronization length before skipping.
ReTrigger:\tShows a new image every time the note is pressed.
Modulation:\tUses modulation source to select image.

ReTrigger Will be restarted when another note is activated on the same track.
"""
            dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Sequence mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        else:
            return
        dlg.ShowModal()
        dlg.Destroy()

    def _onSubmodulationEdit(self, event):
        self._configSizer.Hide(self._effectConfigPanel)
        self._configSizer.Hide(self._slidersPanel)
        self._configSizer.Show(self._moulationConfigPanel)
        self._configSizer.Hide(self._fadeConfigPanel)
        self._selectedEditor = self.EditSelection.ImageSeqModulation
        self._highlightButton(self._selectedEditor)
        self._parentPlane.Layout()
        self._mainConfig.updateModulationGui(self._subModulationField.GetValue(), self._subModulationField, None)

        print "Sub modulation Edit..."

    def _onMixHelp(self, event):
        text = """
Decides how this image is mixed with images on lower MIDI channels.
\t(This only gets used if track mix mode is set to Default.)

Default:\tUses Add if no other mode has been selected by track.
Add:\tSums the images together.
Multiply:\tMultiplies the images together. Very handy for masking.
Lumakey:\tReplaces source everywhere the image is not black.
Replace:\tNo mixing. Just use this image.
"""
        dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Mix help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onNoteHelp(self, event):
        text = """
This is the note assigned to this configuration.
\t(Note \"""" + noteToNoteString(self._midiNote) + "\" has id " + str(self._midiNote) + """.)
"""
        dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Note help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onSyncValidate(self, event):
        valueString = self._syncField.GetValue()
        valueError = False
        try:
            valueFloat = float(valueString)
        except ValueError:
            valueFloat = 4.0
            valueError = True
        if(valueFloat < 0.0):
            valueFloat = 0.0
            valueError = True
        if(valueFloat > 1280.0):
            valueFloat = 1280.0
            valueError = True
        if(valueError):
            dlg = wx.MessageDialog(self._mediaFileGuiPanel, "Value must be a float between 0.0 and 1280.0", 'Synchronization length value error', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
            dlg.ShowModal()
            dlg.Destroy()
        valueString = str(valueFloat)
        self._syncField.SetValue(valueString)

    def _onSyncHelp(self, event):
        text = """
Decides how long the video takes to loop
or how long the images are displayed.

\tGiven in beats (4:4)
"""
        dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Synchronization help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onQuantizeValidate(self, event):
        valueString = self._quantizeField.GetValue()
        valueError = False
        try:
            valueFloat = float(valueString)
        except ValueError:
            valueFloat = 1.0
            valueError = True
        if(valueFloat < 0.0):
            valueFloat = 0.0
            valueError = True
        if(valueFloat > 1280.0):
            valueFloat = 1280.0
            valueError = True
        if(valueError):
            dlg = wx.MessageDialog(self._mediaFileGuiPanel, "Value must be a float between 0.0 and 1280.0", 'Quantize value error', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
            dlg.ShowModal()
            dlg.Destroy()
        valueString = str(valueFloat)
        self._quantizeField.SetValue(valueString)

    def _onQuantizeHelp(self, event):
        text = """
Decides when the video or image starts.
All notes on events are quantized to this.

\tGiven in beats (4:4)
"""
        dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Quantize help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _highlightButton(self, selected):
        if(selected == self.EditSelection.ImageSeqModulation):
            self._subModulationEditButton.SetBackgroundColour(wx.Colour(180,180,255)) #@UndefinedVariable
        else:
            self._subModulationEditButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        if(selected == self.EditSelection.Effect1):
            self._effect1Button.SetBackgroundColour(wx.Colour(180,180,255)) #@UndefinedVariable
        else:
            self._effect1Button.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        if(selected == self.EditSelection.Effect2):
            self._effect2Button.SetBackgroundColour(wx.Colour(180,180,255)) #@UndefinedVariable
        else:
            self._effect2Button.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        if(selected == self.EditSelection.Fade):
            self._fadeButton.SetBackgroundColour(wx.Colour(180,180,255)) #@UndefinedVariable
        else:
            self._fadeButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable

    def _onEffect1Edit(self, event):
        self._configSizer.Show(self._effectConfigPanel)
        self._configSizer.Hide(self._fadeConfigPanel)
        if(self._selectedEditor != self.EditSelection.Effect1):
            self._configSizer.Hide(self._moulationConfigPanel)
        self._parentPlane.Layout()
        selectedEffectConfig = self._effect1Field.GetValue()
        self._selectedEditor = self.EditSelection.Effect1
        self._highlightButton(self._selectedEditor)
        self._mainConfig.updateEffectsGui(selectedEffectConfig, self._midiNote)

    def _onEffect2Edit(self, event):
        self._configSizer.Show(self._effectConfigPanel)
        self._configSizer.Hide(self._fadeConfigPanel)
        if(self._selectedEditor != self.EditSelection.Effect2):
            self._configSizer.Hide(self._moulationConfigPanel)
        self._parentPlane.Layout()
        selectedEffectConfig = self._effect2Field.GetValue()
        self._selectedEditor = self.EditSelection.Effect2
        self._highlightButton(self._selectedEditor)
        self._mainConfig.updateEffectsGui(selectedEffectConfig, self._midiNote)

    def showEffectsGui(self):
        self._configSizer.Show(self._effectConfigPanel)
        self._selectedEditor = self.EditSelection.Unselected
        self._highlightButton(self._selectedEditor)
        self._parentPlane.Layout()
        self._mediaFileGuiPanel.Layout()

    def hideEffectsGui(self):
        self._configSizer.Hide(self._effectConfigPanel)
        self._selectedEditor = self.EditSelection.Unselected
        self._highlightButton(self._selectedEditor)
        self._parentPlane.Layout()
        self._mediaFileGuiPanel.Layout()

    def fixEffectsGuiLayout(self):
        self._parentPlane.Layout()
        self._mediaFileGuiPanel.Layout()

    def hideFadeGui(self):
        self._configSizer.Hide(self._fadeConfigPanel)
        self._selectedEditor = self.EditSelection.Unselected
        self._highlightButton(self._selectedEditor)
        self._parentPlane.Layout()
        self._mediaFileGuiPanel.Layout()

    def showModulationGui(self):
        self._configSizer.Show(self._moulationConfigPanel)
        self._parentPlane.Layout()
        self._mediaFileGuiPanel.Layout()

    def fixModulationGuiLayout(self):
        self._parentPlane.Layout()
        self._mediaFileGuiPanel.Layout()

    def hideModulationGui(self):
        self._configSizer.Hide(self._moulationConfigPanel)
        if(self._selectedEditor == self.EditSelection.ImageSeqModulation):
            self._selectedEditor = self.EditSelection.Unselected
            self._highlightButton(self._selectedEditor)
        self._parentPlane.Layout()
        self._mediaFileGuiPanel.Layout()

    def showSlidersGui(self):
        self._configSizer.Show(self._slidersPanel)
        self._parentPlane.Layout()
        self._mediaFileGuiPanel.Layout()

    def hideSlidersGui(self):
        self._configSizer.Hide(self._slidersPanel)
        self._parentPlane.Layout()
        self._mediaFileGuiPanel.Layout()

    def _onFadeEdit(self, event):
        self._configSizer.Hide(self._effectConfigPanel)
        self._configSizer.Hide(self._slidersPanel)
        if(self._selectedEditor != self.EditSelection.Fade):
            self._configSizer.Hide(self._moulationConfigPanel)
        self._configSizer.Show(self._fadeConfigPanel)
        self._mediaFileGuiPanel.Layout()
        self._parentPlane.Layout()
        selectedFadeConfig = self._fadeField.GetValue()
        self._selectedEditor = self.EditSelection.Fade
        self._highlightButton(self._selectedEditor)
        self._mainConfig.updateFadeGui(selectedFadeConfig)

    def _onCloseButton(self, event):
        self.hideNoteGui()
        self._configSizer.Hide(self._effectConfigPanel)
        self._configSizer.Hide(self._slidersPanel)
        self._configSizer.Hide(self._moulationConfigPanel)
        self._configSizer.Hide(self._fadeConfigPanel)
        self._selectedEditor = self.EditSelection.Unselected
        self._highlightButton(self._selectedEditor)
        self._parentPlane.Layout()

    def _onSaveButton(self, event):
        if(self._type == "Camera"):
            noteFileName = str(self._cameraId)
        else:
            guiVideoDir = self._mainConfig.getGuiVideoDir()
            if((guiVideoDir != "") and (self._fileName != "")):
                noteFileName = os.path.relpath(self._fileName, guiVideoDir)
            else:
                noteFileName = self._fileName
        noteLetter = noteToNoteString(self._midiNote)
        if(self._config == None):
            newConfig = self._mainConfig.makeNoteConfig(noteFileName, noteLetter, self._midiNote)
            if(newConfig != None):
                self._config = newConfig.getConfig()
        if(self._config != None):
            self._config.setValue("Type", self._type)
            if(self._type == "VideoLoop"):
                loopMode = self._subModeField.GetValue()
                self._config.addTextParameter("LoopMode", "Normal")
                self._config.setValue("LoopMode", loopMode)
                self._config.removeParameter("SequenceMode")
                self._config.removeParameter("PlayBackModulation")
            elif(self._type == "ImageSequence"):
                self._config.removeParameter("LoopMode")
                sequenceMode = self._subModeField.GetValue()
                self._config.addTextParameter("SequenceMode", "Time")
                self._config.setValue("SequenceMode", sequenceMode)
                sequenceModulation = self._midiModulation.validateModulationString(self._subModulationField.GetValue())
                self._subModulationField.SetValue(sequenceModulation)
                self._config.addTextParameter("PlayBackModulation", "None")
                self._config.setValue("PlayBackModulation", sequenceModulation)
            else:
                self._config.removeParameter("LoopMode")
                self._config.removeParameter("SequenceMode")
                self._config.removeParameter("PlayBackModulation")
            self._onSyncValidate(event)
            syncLength = self._syncField.GetValue()
            self._config.setValue("SyncLength", syncLength)
            self._onQuantizeValidate(event)
            quantizeLength = self._quantizeField.GetValue()
            self._config.setValue("QuantizeLength", quantizeLength)
            mixMode = self._mixField.GetValue()
            self._config.setValue("MixMode", mixMode)
            effect1Config = self._effect1Field.GetValue()
            self._config.setValue("Effect1Config", effect1Config)
            effect2Config = self._effect2Field.GetValue()
            self._config.setValue("Effect2Config", effect2Config)
            fadeConfig = self._fadeField.GetValue()
            self._config.setValue("FadeConfig", fadeConfig)

    def _showOrHideSubModeModulation(self):
        if(self._selectedSubMode == "Modulation"):
            self._noteConfigSizer.Show(self._subModulationSizer)
        else:
            self._noteConfigSizer.Hide(self._subModulationSizer)
        self._parentPlane.Layout()

    def _setupSubConfig(self):
        if(self._type == "VideoLoop"):
            self._subModeLabel.SetLabel("Loop mode:")
            if(self._config != None):
                self._updateLoopModeChoices(self._subModeField, self._config.getValue("LoopMode"), "Normal")
            else:
                self._updateLoopModeChoices(self._subModeField, "Normal", "Normal")
        elif(self._type == "ImageSequence"):
            self._subModeLabel.SetLabel("Sequence mode:")
            if(self._config != None):
                self._selectedSubMode = self._config.getValue("SequenceMode")
                self._updateSequenceModeChoices(self._subModeField, self._selectedSubMode, "Time")
                self._subModulationField.SetValue(self._config.getValue("PlayBackModulation"))
            else:
                self._selectedSubMode = "Time"
                self._updateSequenceModeChoices(self._subModeField, self._selectedSubMode, "Time")
                self._subModulationField.SetValue("None")

        if(self._type == "VideoLoop"):
            self._noteConfigSizer.Show(self._subModeSizer)
            self._noteConfigSizer.Hide(self._subModulationSizer)
        elif(self._type == "ImageSequence"):
            self._noteConfigSizer.Show(self._subModeSizer)
            self._showOrHideSubModeModulation()
        else:
            self._noteConfigSizer.Hide(self._subModeSizer)
            self._noteConfigSizer.Hide(self._subModulationSizer)
        if(self._type == "Image"):
            self._noteConfigSizer.Hide(self._syncSizer)
        elif(self._type == "Camera"):
            self._noteConfigSizer.Hide(self._syncSizer)
        else:
            self._noteConfigSizer.Show(self._syncSizer)
        self._parentPlane.Layout()

    def _updateEffecChoices(self, widget, value, defaultValue):
        if(self._mainConfig == None):
            self._updateChoices(widget, None, value, defaultValue)
        else:
            self._updateChoices(widget, self._mainConfig.getEffectChoices, value, defaultValue)

    def _updateFadeChoices(self, widget, value, defaultValue):
        if(self._mainConfig == None):
            self._updateChoices(widget, None, value, defaultValue)
        else:
            self._updateChoices(widget, self._mainConfig.getFadeChoices, value, defaultValue)

    def _updateMixModeChoices(self, widget, value, defaultValue):
        self._updateChoices(widget, self._mixModes.getChoices, value, defaultValue)

    def _updateLoopModeChoices(self, widget, value, defaultValue):
        self._updateChoices(widget, self._loopModes.getChoices, value, defaultValue)

    def _updateSequenceModeChoices(self, widget, value, defaultValue):
        self._updateChoices(widget, self._sequenceModes.getChoices, value, defaultValue)

    def _updateTypeChoices(self, widget, value, defaultValue):
        self._updateChoices(widget, self._typeModes.getChoices, value, defaultValue)

    def _updateChoices(self, widget, choicesFunction, value, defaultValue):
        if(choicesFunction == None):
            choiceList = [value]
        else:
            choiceList = choicesFunction()
        widget.Clear()
        valueOk = False
        for choice in choiceList:
            widget.Append(choice)
            if(choice == value):
                valueOk = True
        if(valueOk == True):
            widget.SetStringSelection(value)
        else:
            widget.SetStringSelection(defaultValue)

    def updateMixmodeThumb(self, widget, mixMode, noteMixMode):
        if(mixMode == "Default"):
            if(noteMixMode == "None"):
                widget.setBitmaps(self._mixBitmapDefault, self._mixBitmapDefault)
                return
            mixMode = noteMixMode
        mixModeId = getMixModeFromName(mixMode)
        if(mixModeId == self._mixModes.Add):
            widget.setBitmaps(self._mixBitmapAdd, self._mixBitmapAdd)
        elif(mixModeId == self._mixModes.Default):
            widget.setBitmaps(self._mixBitmapAdd, self._mixBitmapAdd)#Default is Add!
        elif(mixModeId == self._mixModes.LumaKey):
            widget.setBitmaps(self._mixBitmapLumaKey, self._mixBitmapLumaKey)
        elif(mixModeId == self._mixModes.Multiply):
            widget.setBitmaps(self._mixBitmapMultiply, self._mixBitmapMultiply)
        elif(mixModeId == self._mixModes.Replace):
            widget.setBitmaps(self._mixBitmapReplace, self._mixBitmapReplace)
#        elif(mixModeId == self._mixModes.Subtrackt):
#            widget.setBitmaps(self._mixBitmapSubtract, self._mixBitmapSubtract)

    def updateEffectThumb(self, widget, preEffectConfig):
        effectTemplate = self._mainConfig.getEffectTemplate(preEffectConfig)
        effectName = effectTemplate.getEffectName()
        effectId = getEffectId(effectName)
        if(effectId == None):
            widget.setBitmaps(self._blankFxBitmap, self._blankFxBitmap)
        elif(effectId == EffectTypes.Blur):
            widget.setBitmaps(self._fxBitmapBlur, self._fxBitmapBlur)
        elif(effectId == EffectTypes.BlurContrast):
            widget.setBitmaps(self._fxBitmapBlurMul, self._fxBitmapBlurMul)
        elif(effectId == EffectTypes.Colorize):
            widget.setBitmaps(self._fxBitmapColorize, self._fxBitmapColorize)
        elif(effectId == EffectTypes.Contrast):
            widget.setBitmaps(self._fxBitmapContrast, self._fxBitmapContrast)
        elif(effectId == EffectTypes.Desaturate):
            widget.setBitmaps(self._fxBitmapDeSat, self._fxBitmapDeSat)
        elif(effectId == EffectTypes.Distortion):
            widget.setBitmaps(self._fxBitmapDist, self._fxBitmapDist)
        elif(effectId == EffectTypes.Edge):
            widget.setBitmaps(self._fxBitmapEdge, self._fxBitmapEdge)
        elif(effectId == EffectTypes.Flip):
            widget.setBitmaps(self._fxBitmapFlip, self._fxBitmapFlip)
        elif(effectId == EffectTypes.HueSaturation):
            widget.setBitmaps(self._fxBitmapHueSat, self._fxBitmapHueSat)
        elif(effectId == EffectTypes.Invert):
            widget.setBitmaps(self._fxBitmapInverse, self._fxBitmapInverse)
        elif(effectId == EffectTypes.Threshold):
            widget.setBitmaps(self._fxBitmapThreshold, self._fxBitmapThreshold)
        elif(effectId == EffectTypes.Zoom):
            widget.setBitmaps(self._fxBitmapZoom, self._fxBitmapZoom)

    def updateMediaTypeThumb(self, widget, configHolder):
        mediaType = configHolder.getValue("Type")
        if(mediaType == "Camera"):
            widget.setBitmaps(self._modeBitmapCamera, self._modeBitmapCamera)
        elif(mediaType == "Image"):
            widget.setBitmaps(self._modeBitmapImage, self._modeBitmapImage)
        elif(mediaType == "VideoLoop"):
            loopMode = configHolder.getValue("LoopMode")
            if(loopMode == "Normal"):
                widget.setBitmaps(self._modeBitmapLoop, self._modeBitmapLoop)
            elif(loopMode == "Reverse"):
                widget.setBitmaps(self._modeBitmapLoopReverse, self._modeBitmapLoopReverse)
            elif(loopMode == "PingPong"):
                widget.setBitmaps(self._modeBitmapPingPong, self._modeBitmapPingPong)
            elif(loopMode == "PingPongReverse"):
                widget.setBitmaps(self._modeBitmapPingPongReverse, self._modeBitmapPingPongReverse)
            elif(loopMode == "DontLoop"):
                widget.setBitmaps(self._modeBitmapPlayOnce, self._modeBitmapPlayOnce)
            elif(loopMode == "DontLoopReverse"):
                widget.setBitmaps(self._modeBitmapPlayOnceReverse, self._modeBitmapPlayOnceReverse)
        elif(mediaType == "ImageSequence"):
            seqMode = configHolder.getValue("SequenceMode")
            if(seqMode == "Time"):
                widget.setBitmaps(self._modeBitmapImageSeqTime, self._modeBitmapImageSeqTime)
            elif(seqMode == "ReTrigger"):
                widget.setBitmaps(self._modeBitmapImageSeqReTrigger, self._modeBitmapImageSeqReTrigger)
            elif(seqMode == "Modulation"):
                widget.setBitmaps(self._modeBitmapImageSeqModulation, self._modeBitmapImageSeqModulation)
        
    def updateTrackOverviewGui(self, noteConfig, clipBitmap):
        config = noteConfig.getConfig()
        self._overviewClipButton.setBitmap(clipBitmap)
        self.updateMediaTypeThumb(self._overviewClipModeButton, config)
        mixMode = config.getValue("MixMode")
        self.updateMixmodeThumb(self._overviewClipMixButton, mixMode, mixMode)
        length = config.getValue("SyncLength")
        self._overviewClipLengthLabel.SetLabel("L: " + str(length))
        qLength = config.getValue("QuantizeLength")
        self._overviewClipQuantizeLabel.SetLabel("Q: " + str(qLength))
        effect1Config = config.getValue("Effect1Config")
        self.updateEffectThumb(self._overviewFx1Button, effect1Config)
        effect2Config = config.getValue("Effect2Config")
        self.updateEffectThumb(self._overviewFx2Button, effect2Config)

    def clearTrackOverviewGui(self):
        self._overviewClipButton.setBitmap(self._trackThumbnailBitmap)
        self._overviewClipModeButton.setBitmaps(self._blankModeBitmap, self._blankModeBitmap)
        self._overviewClipMixButton.setBitmaps(self._blankMixBitmap, self._blankMixBitmap)
        self._overviewClipLengthLabel.SetLabel("L: N/A")
        self._overviewClipQuantizeLabel.SetLabel("Q: N/A")
        self._overviewFx1Button.setBitmaps(self._blankFxBitmap, self._blankFxBitmap)
        self._overviewFx2Button.setBitmaps(self._blankFxBitmap, self._blankFxBitmap)

    def updateGui(self, noteConfig, midiNote):
        if(noteConfig != None):
            config = noteConfig.getConfig()
            self._config = config
            self._midiNote = midiNote
        if(self._config == None):
            return
        self._type = self._config.getValue("Type")
        if(self._type == "Camera"):
            self._cameraId = int(self._config.getValue("FileName"))
            self._fileName = ""
            self._fileNameField.SetValue(str(self._cameraId))
        else:
            self._cameraId = 0
            self._fileName = self._config.getValue("FileName")
            self._fileNameField.SetValue(os.path.basename(self._fileName))
        self._updateTypeChoices(self._typeField, self._type, "VideoLoop")
        self._setupSubConfig()
        self._noteField.SetValue(self._config.getValue("Note"))
        self._syncField.SetValue(str(self._config.getValue("SyncLength")))
        self._quantizeField.SetValue(str(self._config.getValue("QuantizeLength")))
        mixMode = self._config.getValue("MixMode")
        self._updateMixModeChoices(self._mixField, mixMode, "Add")
        effect1Config = self._config.getValue("Effect1Config")
        self._updateEffecChoices(self._effect1Field, effect1Config, "MediaDefault1")
        effect2Config = self._config.getValue("Effect2Config")
        self._updateEffecChoices(self._effect2Field, effect2Config, "MediaDefault2")
        self._updateFadeChoices(self._fadeField, self._config.getValue("FadeConfig"), "Default")

        if(self._selectedEditor != None):
            if(self._selectedEditor == self.EditSelection.Effect1):
                self._onEffect1Edit(None)
            elif(self._selectedEditor == self.EditSelection.Effect2):
                self._onEffect2Edit(None)
            elif(self._selectedEditor == self.EditSelection.Fade):
                self._onFadeEdit(None)

    def clearGui(self, midiNote):
        self._config = None
        self._midiNote = midiNote
        midiNoteString = noteToNoteString(self._midiNote)
        self._cameraId = 0
        self._fileName = ""
        self._fileNameField.SetValue("")
        self._type = "VideoLoop"
        self._updateTypeChoices(self._typeField, self._type, "VideoLoop")
        self._setupSubConfig()
        self._noteField.SetValue(midiNoteString)
        self._syncField.SetValue("4.0")
        self._quantizeField.SetValue("1.0")
        self._updateMixModeChoices(self._mixField, "Add", "Add")
        self._updateEffecChoices(self._effect1Field, "MediaDefault1", "MediaDefault1")
        self._updateEffecChoices(self._effect2Field, "MediaDefault2", "MediaDefault2")
        self._updateFadeChoices(self._fadeField, "Default", "Default")

        if(self._selectedEditor != None):
            if(self._selectedEditor == self.EditSelection.Effect1):
                self._onEffect1Edit(None)
            elif(self._selectedEditor == self.EditSelection.Effect2):
                self._onEffect2Edit(None)
            elif(self._selectedEditor == self.EditSelection.Fade):
                self._onFadeEdit(None)


