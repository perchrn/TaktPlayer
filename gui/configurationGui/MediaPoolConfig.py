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

class MediaFileGui(object): #@UndefinedVariable
    def __init__(self, parentPlane, mainConfig):
        self._parentPlane = parentPlane
        self._mainConfig = mainConfig
        self._mediaFileGuiPanel = wx.Panel(self._parentPlane, wx.ID_ANY) #@UndefinedVariable

        self._config = None
        self._mixModes = MixMode()
        self._loopModes = VideoLoopMode()
        self._sequenceModes = ImageSequenceMode()
        self._typeModes = MediaTypes()

        self._configSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._noteConfigPanel = wx.Panel(self._mediaFileGuiPanel, wx.ID_ANY, size=(300,-1)) #@UndefinedVariable
        self._effectConfigPanel = wx.Panel(self._mediaFileGuiPanel, wx.ID_ANY, size=(300,-1)) #@UndefinedVariable
        self._fadeConfigPanel = wx.Panel(self._mediaFileGuiPanel, wx.ID_ANY, size=(300,-1)) #@UndefinedVariable
        self._moulationConfigPanel = wx.Panel(self._mediaFileGuiPanel, wx.ID_ANY, size=(300,-1)) #@UndefinedVariable
        self._slidersPanel = wx.Panel(self._mediaFileGuiPanel, wx.ID_ANY, size=(300,-1)) #@UndefinedVariable

        self._configSizer.Add(self._noteConfigPanel) #@UndefinedVariable
        self._configSizer.Add(self._effectConfigPanel) #@UndefinedVariable
        self._configSizer.Add(self._fadeConfigPanel) #@UndefinedVariable
        self._configSizer.Add(self._moulationConfigPanel) #@UndefinedVariable
        self._configSizer.Add(self._slidersPanel) #@UndefinedVariable

        self._configSizer.Hide(self._effectConfigPanel)
        self._configSizer.Hide(self._fadeConfigPanel)
        self._configSizer.Hide(self._moulationConfigPanel)
        self._configSizer.Hide(self._slidersPanel)
        self._mediaFileGuiPanel.SetSizer(self._configSizer)

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
        fileNameSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText1 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "FileName:") #@UndefinedVariable
        self._fileNameField = wx.TextCtrl(self._noteConfigPanel, wx.ID_ANY, self._fileName, size=(200, -1)) #@UndefinedVariable
        self._fileNameField.SetEditable(False)
        self._fileNameField.SetBackgroundColour((232,232,232))
        fileOpenButton = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Select') #@UndefinedVariable
        self._mediaFileGuiPanel.Bind(wx.EVT_BUTTON, self._onOpenFile, id=fileOpenButton.GetId()) #@UndefinedVariable
        fileNameSizer.Add(tmpText1, 1, wx.ALL, 5) #@UndefinedVariable
        fileNameSizer.Add(self._fileNameField, 2, wx.ALL, 5) #@UndefinedVariable
        fileNameSizer.Add(fileOpenButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(fileNameSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        typeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText2 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Type:") #@UndefinedVariable
        self._typeField = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["VideoLoop"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateTypeChoices(self._typeField, "VideoLoop", "VideoLoop")
        typeHelpButton = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Help') #@UndefinedVariable
        self._mediaFileGuiPanel.Bind(wx.EVT_BUTTON, self._onTypeHelp, id=typeHelpButton.GetId()) #@UndefinedVariable
        typeSizer.Add(tmpText2, 1, wx.ALL, 5) #@UndefinedVariable
        typeSizer.Add(self._typeField, 2, wx.ALL, 5) #@UndefinedVariable
        typeSizer.Add(typeHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(typeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._noteConfigPanel.Bind(wx.EVT_COMBOBOX, self._onTypeChosen, id=self._typeField.GetId()) #@UndefinedVariable

        self._subModeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._subModeLabel = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Loop mode:") #@UndefinedVariable
        self._subModeField = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["Normal"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateLoopModeChoices(self._subModeField, "Normal", "Normal")
        subModeHelpButton = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Help') #@UndefinedVariable
        self._mediaFileGuiPanel.Bind(wx.EVT_BUTTON, self._onSubModeHelp, id=subModeHelpButton.GetId()) #@UndefinedVariable
        self._subModeSizer.Add(self._subModeLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._subModeSizer.Add(self._subModeField, 2, wx.ALL, 5) #@UndefinedVariable
        self._subModeSizer.Add(subModeHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._subModeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._noteConfigPanel.Bind(wx.EVT_COMBOBOX, self._onSubModeChosen, id=self._subModeField.GetId()) #@UndefinedVariable

        self._subModulationSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._subModulationLabel = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Playback modulation:") #@UndefinedVariable
        self._subModulationField = wx.TextCtrl(self._noteConfigPanel, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._subModulationField.SetInsertionPoint(0)
        subModulationEditButton = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Edit') #@UndefinedVariable
        self._mediaFileGuiPanel.Bind(wx.EVT_BUTTON, self._onSubmodulationEdit, id=subModulationEditButton.GetId()) #@UndefinedVariable
        self._subModulationSizer.Add(self._subModulationLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._subModulationSizer.Add(self._subModulationField, 2, wx.ALL, 5) #@UndefinedVariable
        self._subModulationSizer.Add(subModulationEditButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._subModulationSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._midiNote = 24
        noteSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText3 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Note:") #@UndefinedVariable
        self._noteField = wx.TextCtrl(self._noteConfigPanel, wx.ID_ANY, noteToNoteString(self._midiNote), size=(200, -1)) #@UndefinedVariable
        self._noteField.SetEditable(False)
        self._noteField.SetBackgroundColour((232,232,232))
        noteHelpButton = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Help') #@UndefinedVariable
        self._mediaFileGuiPanel.Bind(wx.EVT_BUTTON, self._onNoteHelp, id=noteHelpButton.GetId()) #@UndefinedVariable
        noteSizer.Add(tmpText3, 1, wx.ALL, 5) #@UndefinedVariable
        noteSizer.Add(self._noteField, 2, wx.ALL, 5) #@UndefinedVariable
        noteSizer.Add(noteHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(noteSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        syncSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText4 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Synchronization length:") #@UndefinedVariable
        self._syncField = wx.TextCtrl(self._noteConfigPanel, wx.ID_ANY, "4.0", size=(200, -1)) #@UndefinedVariable
        self._syncField.SetInsertionPoint(0)
        syncHelpButton = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Help') #@UndefinedVariable
        self._mediaFileGuiPanel.Bind(wx.EVT_BUTTON, self._onSyncHelp, id=syncHelpButton.GetId()) #@UndefinedVariable
        syncSizer.Add(tmpText4, 1, wx.ALL, 5) #@UndefinedVariable
        syncSizer.Add(self._syncField, 2, wx.ALL, 5) #@UndefinedVariable
        syncSizer.Add(syncHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(syncSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        quantizeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText5 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Quantization:") #@UndefinedVariable
        self._quantizeField = wx.TextCtrl(self._noteConfigPanel, wx.ID_ANY, "1.0", size=(200, -1)) #@UndefinedVariable
        self._quantizeField.SetInsertionPoint(0)
        quantizeHelpButton = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Help') #@UndefinedVariable
        self._mediaFileGuiPanel.Bind(wx.EVT_BUTTON, self._onQuantizeHelp, id=quantizeHelpButton.GetId()) #@UndefinedVariable
        quantizeSizer.Add(tmpText5, 1, wx.ALL, 5) #@UndefinedVariable
        quantizeSizer.Add(self._quantizeField, 2, wx.ALL, 5) #@UndefinedVariable
        quantizeSizer.Add(quantizeHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(quantizeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        mixSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText6 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Mix mode:") #@UndefinedVariable
        self._mixField = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["Add"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateMixModeChoices(self._mixField, "Add", "Add")
        mixHelpButton = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Help') #@UndefinedVariable
        self._mediaFileGuiPanel.Bind(wx.EVT_BUTTON, self._onMixHelp, id=mixHelpButton.GetId()) #@UndefinedVariable
        mixSizer.Add(tmpText6, 1, wx.ALL, 5) #@UndefinedVariable
        mixSizer.Add(self._mixField, 2, wx.ALL, 5) #@UndefinedVariable
        mixSizer.Add(mixHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(mixSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        effect1Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Effect 1 template:") #@UndefinedVariable
        self._effect1Field = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["MediaDefault1"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateEffecChoices(self._effect1Field, "MediaDefault1", "MediaDefault1")
        effect1Button = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Edit') #@UndefinedVariable
        self._mediaFileGuiPanel.Bind(wx.EVT_BUTTON, self._onEffect1Edit, id=effect1Button.GetId()) #@UndefinedVariable
        effect1Sizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        effect1Sizer.Add(self._effect1Field, 2, wx.ALL, 5) #@UndefinedVariable
        effect1Sizer.Add(effect1Button, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(effect1Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        effect2Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Effect 2 template:") #@UndefinedVariable
        self._effect2Field = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["MediaDefault2"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateEffecChoices(self._effect2Field, "MediaDefault2", "MediaDefault2")
        effect2Button = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Edit') #@UndefinedVariable
        self._mediaFileGuiPanel.Bind(wx.EVT_BUTTON, self._onEffect2Edit, id=effect2Button.GetId()) #@UndefinedVariable
        effect2Sizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        effect2Sizer.Add(self._effect2Field, 2, wx.ALL, 5) #@UndefinedVariable
        effect2Sizer.Add(effect2Button, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(effect2Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        fadeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Fade template:") #@UndefinedVariable
        self._fadeField = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["Default"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateFadeChoices(self._fadeField, "Default", "Default")
        fadeButton = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Edit') #@UndefinedVariable
        self._mediaFileGuiPanel.Bind(wx.EVT_BUTTON, self._onFadeEdit, id=fadeButton.GetId()) #@UndefinedVariable
        fadeSizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        fadeSizer.Add(self._fadeField, 2, wx.ALL, 5) #@UndefinedVariable
        fadeSizer.Add(fadeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(fadeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        saveButton = wx.Button(self._noteConfigPanel, wx.ID_ANY, 'Save') #@UndefinedVariable
        self._noteConfigPanel.Bind(wx.EVT_BUTTON, self._onSaveButton, id=saveButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(saveButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._selectedEditor = None
        self._type = "VideoLoop"
        self._setupSubConfig()

    def getPlane(self):
        return self._mediaFileGuiPanel

    class EditSelection():
        Effect1, Effect2, Fade, ImageSeqModulation = range(4)

    def _onOpenFile(self, event):
        dlg = wx.FileDialog(self._mediaFileGuiPanel, "Choose a file", os.getcwd(), "", "*.*", wx.OPEN) #@UndefinedVariable
        if dlg.ShowModal() == wx.ID_OK: #@UndefinedVariable
            self._fileName = dlg.GetPath()
            self._fileNameField.SetValue(os.path.basename(self._fileName))
        dlg.Destroy()

    def _onTypeChosen(self, event):
        selectedTypeId = self._typeField.GetSelection()
        self._type = self._typeModes.getNames(selectedTypeId)
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
        self._selectedEditor = self.EditSelection.ImageSeqModulation
        self._configSizer.Hide(self._effectConfigPanel)
        self._configSizer.Hide(self._slidersPanel)
        self._configSizer.Show(self._moulationConfigPanel)
        self._configSizer.Hide(self._fadeConfigPanel)
        self._parentPlane.Layout()
        self._mainConfig.updateModulationGui(self._subModulationField.GetValue(), self._subModulationField)

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
    def _onSyncHelp(self, event):
        text = """
Decides how long the video takes to loop
or how long the images are displayed.

\tGiven in beats (4:4)
"""
        dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Mix help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()
    def _onQuantizeHelp(self, event):
        text = """
Decides when the video or image starts.
All notes on events are quantized to this.

\tGiven in beats (4:4)
"""
        dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Mix help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onEffect1Edit(self, event):
        self._configSizer.Show(self._effectConfigPanel)
        self._configSizer.Hide(self._fadeConfigPanel)
        if(self._selectedEditor != self.EditSelection.Effect1):
            self._configSizer.Hide(self._moulationConfigPanel)
        self._parentPlane.Layout()
        selectedEffectConfig = self._effect1Field.GetValue()
        self._selectedEditor = self.EditSelection.Effect1
        self._mainConfig.updateEffectsGui(selectedEffectConfig, self._midiNote)

    def _onEffect2Edit(self, event):
        self._configSizer.Show(self._effectConfigPanel)
        self._configSizer.Hide(self._fadeConfigPanel)
        if(self._selectedEditor != self.EditSelection.Effect2):
            self._configSizer.Hide(self._moulationConfigPanel)
        self._parentPlane.Layout()
        selectedEffectConfig = self._effect2Field.GetValue()
        self._selectedEditor = self.EditSelection.Effect2
        self._mainConfig.updateEffectsGui(selectedEffectConfig, self._midiNote)

    def hideEffectsGui(self):
        self._configSizer.Hide(self._effectConfigPanel)
        self._parentPlane.Layout()

    def hideFadeGui(self):
        self._configSizer.Hide(self._fadeConfigPanel)
        self._parentPlane.Layout()

    def showModulationGui(self):
        self._configSizer.Show(self._moulationConfigPanel)
        self._parentPlane.Layout()

    def hideModulationGui(self):
        self._configSizer.Hide(self._moulationConfigPanel)
        self._parentPlane.Layout()

    def showSlidersGui(self):
        self._configSizer.Show(self._slidersPanel)
        self._parentPlane.Layout()

    def hideSlidersGui(self):
        self._configSizer.Hide(self._slidersPanel)
        self._parentPlane.Layout()

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
        self._mainConfig.updateFadeGui(selectedFadeConfig)

    def _onSaveButton(self, event):
        print "Save " * 20
        print "FileName: " + self._fileName
        print "Type: " + self._type
        if(self._type == "VideoLoop"):
            print "LoopMode: " + self._subModeField.GetValue()
        elif(self._type == "ImageSequence"):
            print "SequenceMode: " + self._subModeField.GetValue()
            print "PlayBackModulation: " + self._subModulationField.GetValue()
        print "Note: " + noteToNoteString(self._midiNote)
        print "SyncLength: " + self._syncField.GetValue()
        print "QuantizeLength: " + self._quantizeField.GetValue()
        print "MixMode: " + self._mixField.GetValue()
        print "Effect1Config: " + self._effect1Field.GetValue()
        print "Effect2Config: " + self._effect2Field.GetValue()
        print "FadeConfig: " + self._fadeField.GetValue()
        print "Save " * 20

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

    def updateGui(self, noteConfig, midiNote):
        config = noteConfig.getConfig()
        self._config = config
        self._midiNote = midiNote
        self._fileName = self._config.getValue("FileName")
        self._fileNameField.SetValue(os.path.basename(self._fileName))
        self._type = self._config.getValue("Type")
        self._updateTypeChoices(self._typeField, self._type, "VideoLoop")
        self._setupSubConfig()
        self._noteField.SetValue(self._config.getValue("Note"))
        self._syncField.SetValue(str(self._config.getValue("SyncLength")))
        self._quantizeField.SetValue(str(self._config.getValue("QuantizeLength")))
        self._updateMixModeChoices(self._mixField, self._config.getValue("MixMode"), "Add")
        self._updateEffecChoices(self._effect1Field, self._config.getValue("Effect1Config"), "MediaDefault1")
        self._updateEffecChoices(self._effect2Field, self._config.getValue("Effect2Config"), "MediaDefault2")
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


