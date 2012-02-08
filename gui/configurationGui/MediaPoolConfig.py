'''
Created on 6. feb. 2012

@author: pcn
'''
from midi.MidiUtilities import noteToNoteString, noteStringToNoteNumber
import wx
import os
from video.media.MediaFile import MixMode
from video.media.MediaFileModes import VideoLoopMode, ImageSequenceMode,\
    MediaTypes

class MediaPoolConfig(object):
    def __init__(self, configParent):
        self._configurationTree = configParent.addChildUnique("MediaPool")

        self._mediaPool = []
        for i in range(128): #@UnusedVariable
            self._mediaPool.append(None)

        self.loadMediaFromConfiguration()

    def _getConfiguration(self):
        print "DEBUG: MediaPoolConfig._getConfiguration"
        self.loadMediaFromConfiguration()

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print "mediaPool config is updated..."
            self._getConfiguration()
            self._configurationTree.resetConfigurationUpdated()
        else:
            print "DEBUG: MediaPoolConfig.checkAndUpdateFromConfiguration NOT updated..."

    def loadMediaFromConfiguration(self):
        mediaPoolState = []
        for i in range(128):
            mediaPoolState.append(False)
        mediaFileChildren = self._configurationTree.findXmlChildrenList("MediaFile")
        if(mediaFileChildren != None):
            print "self._configurationTree.findXmlChildrenList(\"MediaFile\") != None"
            for xmlConfig in mediaFileChildren:
                print "adding one..."
                midiNote = self.addXmlMedia(xmlConfig)
                mediaPoolState[midiNote] = True
        else:
            print "self._configurationTree.findXmlChildrenList(\"MediaFile\") == None"
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
            print "DEBUG media added to pool pos: " + str(midiNote)
            self._mediaPool[midiNote] = MediaFile(self._configurationTree, fileName, noteLetter, midiNote, xmlConfig)
        return midiNote

    def getNoteConfiguration(self, noteId):
        noteId = min(max(noteId, 0), 127)
        return self._mediaPool[noteId]

class MediaFile(object):
    def __init__(self, configParent, fileName, noteLetter, midiNote, xmlConfig):
        self._mediaType = xmlConfig.get("type")
        if(self._mediaType == None):
            self._mediaType = "VideoLoop"
        self._configurationTree = configParent.addChildUniqueId("MediaFile", "Note", noteLetter, midiNote)
        self._configurationTree.addTextParameter("FileName", "")
        self._configurationTree.addTextParameter("Type", self._mediaType)
        self._configurationTree.addFloatParameter("SyncLength", 4.0) #Default one bar (re calculated on load)
        self._configurationTree.addFloatParameter("QuantizeLength", 4.0)#Default one bar
        self._configurationTree.addTextParameter("MixMode", "Add")#Default Add
        self._defaultEffect1SettingsName = "MediaDefault1"
        self._configurationTree.addTextParameter("Effect1Config", self._defaultEffect1SettingsName)#Default MediaDefault1
        self._defaultEffect2SettingsName = "MediaDefault2"
        self._configurationTree.addTextParameter("Effect2Config", self._defaultEffect2SettingsName)#Default MediaDefault2
        self._defaultFadeSettingsName = "Default"
        self._configurationTree.addTextParameter("FadeConfig", self._defaultFadeSettingsName)#Default Default
        if(self._mediaType == "VideoLoop"):
            self._configurationTree.addTextParameter("LoopMode", "Normal")
        elif(self._mediaType == "ImageSequence"):
            self._configurationTree.addTextParameter("SequenceMode", "Time")
            self._configurationTree.addTextParameter("PlayBackModulation", "None")
        if(xmlConfig != None):
            self._configurationTree._updateFromXml(xmlConfig)

    def getConfig(self):
        return self._configurationTree

class MediaFileGui(wx.Panel): #@UndefinedVariable
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs) #@UndefinedVariable

        self._mainConfig = None
        self._config = None
        self._mixModes = MixMode()
        self._loopModes = VideoLoopMode()
        self._sequenceModes = ImageSequenceMode()
        self._typeModes = MediaTypes()

        self._configSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._noteConfigSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._effectConfigSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._slidersSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._configSizer.Add(self._noteConfigSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._configSizer.Add(self._effectConfigSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._configSizer.Add(self._slidersSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._configSizer.Hide(self._effectConfigSizer)
        self._configSizer.Hide(self._slidersSizer)
        self.SetSizer(self._configSizer)

        self._fileName = ""
        fileNameSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText1 = wx.StaticText(self, wx.ID_ANY, "FileName:") #@UndefinedVariable
        self._fileNameField = wx.TextCtrl(self, wx.ID_ANY, self._fileName, size=(200, -1)) #@UndefinedVariable
        self._fileNameField.SetInsertionPoint(0)
        fileNameSizer.Add(tmpText1, 1, wx.ALL, 5) #@UndefinedVariable
        fileNameSizer.Add(self._fileNameField, 2, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(fileNameSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        typeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText2 = wx.StaticText(self, wx.ID_ANY, "Type:") #@UndefinedVariable
        self._typeField = wx.ComboBox(self, wx.ID_ANY, size=(200, -1), choices=["VideoLoop"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateTypeChoices(self._typeField, "VideoLoop", "VideoLoop")
        typeSizer.Add(tmpText2, 1, wx.ALL, 5) #@UndefinedVariable
        typeSizer.Add(self._typeField, 2, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(typeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._subModeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._subModeLabel = wx.StaticText(self, wx.ID_ANY, "Loop mode:") #@UndefinedVariable
        self._subModeField = wx.ComboBox(self, wx.ID_ANY, size=(200, -1), choices=["Normal"], style=wx.CB_READONLY) #@UndefinedVariable
        self._subModeSizer.Add(self._subModeLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._subModeSizer.Add(self._subModeField, 2, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._subModeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._subModulationSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._subModulationLabel = wx.StaticText(self, wx.ID_ANY, "Playback modulation:") #@UndefinedVariable
        self._subModulationField = wx.TextCtrl(self, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._subModulationField.SetInsertionPoint(0)
        self._subModulationSizer.Add(self._subModulationLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._subModulationSizer.Add(self._subModulationField, 2, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._subModulationSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        noteSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText3 = wx.StaticText(self, wx.ID_ANY, "Note:") #@UndefinedVariable
        self._noteField = wx.TextCtrl(self, wx.ID_ANY, "0C", size=(200, -1)) #@UndefinedVariable
        self._noteField.SetInsertionPoint(0)
        noteSizer.Add(tmpText3, 1, wx.ALL, 5) #@UndefinedVariable
        noteSizer.Add(self._noteField, 2, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(noteSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        syncSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText4 = wx.StaticText(self, wx.ID_ANY, "Syncronization length:") #@UndefinedVariable
        self._syncField = wx.TextCtrl(self, wx.ID_ANY, "4.0", size=(200, -1)) #@UndefinedVariable
        self._syncField.SetInsertionPoint(0)
        syncSizer.Add(tmpText4, 1, wx.ALL, 5) #@UndefinedVariable
        syncSizer.Add(self._syncField, 2, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(syncSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        quantizeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText5 = wx.StaticText(self, wx.ID_ANY, "Quantization:") #@UndefinedVariable
        self._quantizeField = wx.TextCtrl(self, wx.ID_ANY, "4.0", size=(200, -1)) #@UndefinedVariable
        self._quantizeField.SetInsertionPoint(0)
        quantizeSizer.Add(tmpText5, 1, wx.ALL, 5) #@UndefinedVariable
        quantizeSizer.Add(self._quantizeField, 2, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(quantizeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        mixSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText6 = wx.StaticText(self, wx.ID_ANY, "Mix mode:") #@UndefinedVariable
        self._mixField = wx.ComboBox(self, wx.ID_ANY, size=(200, -1), choices=["Add"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateMixModeChoices(self._mixField, "Add", "Add")
        mixSizer.Add(tmpText6, 1, wx.ALL, 5) #@UndefinedVariable
        mixSizer.Add(self._mixField, 2, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(mixSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        effect1Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self, wx.ID_ANY, "Effect 1 template:") #@UndefinedVariable
        self._effect1Field = wx.ComboBox(self, wx.ID_ANY, size=(200, -1), choices=["MediaDefault1"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateEffecChoices(self._effect1Field, "MediaDefault1", "MediaDefault1")
        effect1Button = wx.Button(self, wx.ID_ANY, 'Edit') #@UndefinedVariable
        self.Bind(wx.EVT_BUTTON, self._onEffect1Edit, id=effect1Button.GetId()) #@UndefinedVariable
        effect1Sizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        effect1Sizer.Add(self._effect1Field, 2, wx.ALL, 5) #@UndefinedVariable
        effect1Sizer.Add(effect1Button, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(effect1Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        effect2Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self, wx.ID_ANY, "Effect 2 template:") #@UndefinedVariable
        self._effect2Field = wx.ComboBox(self, wx.ID_ANY, size=(200, -1), choices=["MediaDefault2"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateEffecChoices(self._effect2Field, "MediaDefault2", "MediaDefault2")
        effect2Button = wx.Button(self, wx.ID_ANY, 'Edit') #@UndefinedVariable
        self.Bind(wx.EVT_BUTTON, self._onEffect2Edit, id=effect2Button.GetId()) #@UndefinedVariable
        effect2Sizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        effect2Sizer.Add(self._effect2Field, 2, wx.ALL, 5) #@UndefinedVariable
        effect2Sizer.Add(effect2Button, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(effect2Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        fadeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self, wx.ID_ANY, "Fade template:") #@UndefinedVariable
        self._fadeField = wx.ComboBox(self, wx.ID_ANY, size=(200, -1), choices=["Default"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateEffecChoices(self._fadeField, "Default", "Default")
        fadeButton = wx.Button(self, wx.ID_ANY, 'Edit') #@UndefinedVariable
        self.Bind(wx.EVT_BUTTON, self._onFadeEdit, id=fadeButton.GetId()) #@UndefinedVariable
        fadeSizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        fadeSizer.Add(self._fadeField, 2, wx.ALL, 5) #@UndefinedVariable
        fadeSizer.Add(fadeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(fadeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self.setupSubConfig("VideoLoop")

    def setMainConfig(self, mainConfig):
        self._mainConfig = mainConfig
        self._mainConfig.setupEffectsGui(self, self._effectConfigSizer)
        self._mainConfig.setupEffectsSlidersGui(self, self._slidersSizer)

    def _onEffect1Edit(self, event):
        if(self._config != None):
            selectedEffectConfig = self._config.getValue("Effect1Config")
            print "Effect 1 Edit: " + selectedEffectConfig
            self._mainConfig.editEffectsConfig(selectedEffectConfig, self._midiChannel, self._midiNote, self._midiSender)
        else:
            print "Effect 1 Edit: No config selected :-("

    def _onEffect2Edit(self, event):
        if(self._config != None):
            selectedEffectConfig = self._config.getValue("Effect2Config")
            print "Effect 2 Edit: " + selectedEffectConfig
            self._mainConfig.editEffectsConfig(selectedEffectConfig, self._midiChannel, self._midiNote, self._midiSender)
        else:
            print "Effect 2 Edit: No config selected :-("

    def _onFadeEdit(self, event):
        print "Fade Edit"

    def setupSubConfig(self, fileType):
        if(fileType == "VideoLoop"):
            self._noteConfigSizer.Show(self._subModeSizer)
            self._noteConfigSizer.Hide(self._subModulationSizer)
        elif(fileType == "ImageSequence"):
            self._noteConfigSizer.Show(self._subModeSizer)
            self._noteConfigSizer.Show(self._subModulationSizer)
        else:
            self._noteConfigSizer.Hide(self._subModeSizer)
            self._noteConfigSizer.Hide(self._subModulationSizer)
        self.Layout()

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

    def updateGui(self, noteConfig, midiChannel, midiNote, midiSender):
        config = noteConfig.getConfig()
        self._config = config
        self._midiChannel = midiChannel
        self._midiNote = midiNote
        self._midiSender = midiSender
        self._fileName = config.getValue("FileName")
        self._fileNameField.SetValue(os.path.basename(self._fileName))
        self._type = config.getValue("Type")
        self._updateTypeChoices(self._typeField, self._type, "VideoLoop")
        if(self._type == "VideoLoop"):
            self._subModeLabel.SetLabel("Loop mode:")
            self._updateLoopModeChoices(self._subModeField, config.getValue("LoopMode"), "Add")
        elif(self._type == "ImageSequence"):
            self._subModeLabel.SetLabel("Sequence mode:")
            self._updateSequenceModeChoices(self._subModeField, config.getValue("SequenceMode"), "Add")
            self._subModulationField.SetValue(config.getValue("PlayBackModulation"))
        self.setupSubConfig(self._type)
        self._noteField.SetValue(config.getValue("Note"))
        self._syncField.SetValue(str(config.getValue("SyncLength")))
        self._quantizeField.SetValue(str(config.getValue("QuantizeLength")))
        self._updateMixModeChoices(self._mixField, config.getValue("MixMode"), "Add")
        self._updateEffecChoices(self._effect1Field, config.getValue("Effect1Config"), "MediaDefault1")
        self._updateEffecChoices(self._effect2Field, config.getValue("Effect2Config"), "MediaDefault2")
        self._updateFadeChoices(self._fadeField, config.getValue("FadeConfig"), "Default")


