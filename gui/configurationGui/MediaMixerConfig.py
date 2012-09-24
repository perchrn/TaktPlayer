'''
Created on 6. feb. 2012

@author: pcn
'''

import wx
from video.media.MediaFileModes import MixMode
from widgets.PcnImageButton import PcnKeyboardButton, PcnImageButton,\
    addTrackButtonFrame, EVT_DOUBLE_CLICK_EVENT, EVT_DRAG_DONE_EVENT,\
    PcnPopupMenu
import sys
from midi.MidiModulation import MidiModulation
from midi.MidiTiming import MidiTiming

class MediaMixerConfig(object):
    def __init__(self, configParent):
        self._configurationTree = configParent.addChildUnique("MediaMixer")

        self._mediaTrackConfigs = []
        for i in range(16):
            trackConfig = self._configurationTree.addChildUniqueId("MediaTrack", "TrackId", str(i+1), i+1)
            self.setupTrackConfig(trackConfig)
            self._mediaTrackConfigs.append(trackConfig)

    def setupTrackConfig(self, trackConfigHolder):
        trackConfigHolder.addTextParameter("MixMode", "Default")
        trackConfigHolder.addTextParameter("LevelModulation", "None")
        self._defaultPreEffectSettingsName = "MixPreDefault"
        trackConfigHolder.addTextParameter("PreEffectConfig", self._defaultPreEffectSettingsName)#Default MixPreDefault
        self._defaultPostEffectSettingsName = "MixPostDefault"
        trackConfigHolder.addTextParameter("PostEffectConfig", self._defaultPostEffectSettingsName)#Default MixPostDefault

    def loadMediaFromConfiguration(self):
        mediaTrackState = []
        for i in range(16):
            mediaTrackState.append(False)
        xmlChildren = self._configurationTree.findXmlChildrenList("MediaTrack")
        if(xmlChildren != None):
            for xmlConfig in xmlChildren:
                trackId = self.updateTrackFromXml(xmlConfig)
                mediaTrackState[trackId - 1] = True
        for i in range(16):
            mediaState = mediaTrackState[i]
            if(mediaState == False):
                self.deafultTrackSettings(i)

    def getTrackConfiguration(self, trackId):
        trackId = min(max(trackId, 0), 15)
        return self._mediaTrackConfigs[trackId]

    def updateTrackFromXml(self, xmlConfig):
        trackId = int(xmlConfig.get("trackid"))
        trackId = min(max(trackId, 0), 16)
        trackConfig = self._mediaTrackConfigs[trackId]

        mixMode = xmlConfig.get("mixmode")
        trackConfig.setValue("MixMode", mixMode)

        levelMod = xmlConfig.get("levelmodulation")
        trackConfig.setValue("LevelModulation", levelMod)

        preEffectModulationTemplate = xmlConfig.get("preeffectconfig")
        trackConfig.setValue("PreEffectConfig", preEffectModulationTemplate)

        postEffectModulationTemplate = xmlConfig.get("posteffectconfig")
        trackConfig.setValue("PostEffectConfig", postEffectModulationTemplate)

        return trackId

    def deafultTrackSettings(self, trackIndex):
        trackConfig = self._mediaTrackConfigs[trackIndex]
        trackConfig.setValue("MixMode", "Default")
        trackConfig.setValue("LevelModulation", "None")
        trackConfig.setValue("PreEffectConfig", self._defaultPreEffectSettingsName)
        trackConfig.setValue("PostEffectConfig", self._defaultPostEffectSettingsName)

    def getConfTree(self):
        return self._configurationTree

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print "MediaMixerConfig config is updated..."

    def countNumberOfTimeEffectTemplateUsed(self, effectConfigName):
        returnNumer = 0
        for trackConfig in self._mediaTrackConfigs:
            if(trackConfig != None):
                for configName in ["PreEffectConfig", "PostEffectConfig"]:
                    usedConfigName = trackConfig.getValue(configName)
                    if(usedConfigName == effectConfigName):
                        returnNumer += 1
        return returnNumer

    def countNumberOfTimeFadeTemplateUsed(self, fadeConfigName):
        returnNumer = 0
#        for trackConfig in self._mediaTrackConfigs:
#            if(trackConfig != None):
#                returnNumer += trackConfig.countNumberOfTimeFadeTemplateUsed(fadeConfigName)
        return returnNumer

    def renameEffectTemplateUsed(self, oldName, newName):
        for trackConfig in self._mediaTrackConfigs:
            if(trackConfig != None):
                for configName in ["PreEffectConfig", "PostEffectConfig"]:
                    usedConfigName = trackConfig.getValue(configName)
                    if(usedConfigName == oldName):
                        trackConfig.setValue(configName, newName)

    def renameFadeTemplateUsed(self, oldName, newName):
        pass
#        for trackConfig in self._mediaPool:
#            if(trackConfig != None):
#                trackConfig.renameFadeTemplateUsed(oldName, newName)

    def verifyEffectTemplateUsed(self, effectConfigNameList):
        for trackConfig in self._mediaTrackConfigs:
            if(trackConfig != None):
                usedConfigName = trackConfig.getValue("PreEffectConfig")
                nameOk = False
                for configName in effectConfigNameList:
                    if(usedConfigName == configName):
                        nameOk = True
                        break
                if(nameOk == False):
                    trackConfig.setValue("PreEffectConfig", self._defaultPreEffectSettingsName)
                usedConfigName = trackConfig.getValue("PostEffectConfig")
                nameOk = False
                for configName in effectConfigNameList:
                    if(usedConfigName == configName):
                        nameOk = True
                        break
                if(nameOk == False):
                    trackConfig.setValue("PostEffectConfig", self._defaultPostEffectSettingsName)

    def verifyFadeTemplateUsed(self, fadeConfigNameList):
        pass
#        for trackConfig in self._mediaPool:
#            if(trackConfig != None):
#                trackConfig.verifyFadeTemplateUsed(fadeConfigNameList)

class MediaTrackGui(object): #@UndefinedVariable
    def __init__(self, mainConfig):
        self._mainConfig = mainConfig
        self._config = None
        self._mixModes = MixMode()
        self._latestOverviewMixMode = MixMode.Add
        self._midiNote = -1
        self._selectedEditor = self.EditSelection.Unselected
        self._trackEditorOpen = False

        self._midiTiming = MidiTiming()
        self._midiModulation = MidiModulation(None, self._midiTiming)

        self._blankModeBitmap = wx.Bitmap("graphics/modeEmpty.png") #@UndefinedVariable
        self._blankMixBitmap = wx.Bitmap("graphics/mixEmpty.png") #@UndefinedVariable
        self._blankFxBitmap = wx.Bitmap("graphics/fxEmpty.png") #@UndefinedVariable

        self._editBitmap = wx.Bitmap("graphics/editButton.png") #@UndefinedVariable
        self._editPressedBitmap = wx.Bitmap("graphics/editButtonPressed.png") #@UndefinedVariable
        self._editSelectedBitmap = wx.Bitmap("graphics/editButtonSelected.png") #@UndefinedVariable
        self._helpBitmap = wx.Bitmap("graphics/helpButton.png") #@UndefinedVariable
        self._helpPressedBitmap = wx.Bitmap("graphics/helpButtonPressed.png") #@UndefinedVariable

        self._closeButtonBitmap = wx.Bitmap("graphics/closeButton.png") #@UndefinedVariable
        self._closeButtonPressedBitmap = wx.Bitmap("graphics/closeButtonPressed.png") #@UndefinedVariable
        self._saveBigBitmap = wx.Bitmap("graphics/saveButtonBig.png") #@UndefinedVariable
        self._saveBigPressedBitmap = wx.Bitmap("graphics/saveButtonBigPressed.png") #@UndefinedVariable
        self._saveBigGreyBitmap = wx.Bitmap("graphics/saveButtonBigGrey.png") #@UndefinedVariable

        self._overviewTrackMixModeButtonPopup = None
        self._overviewTrackMixModePopupButtonIndex = -1

    class EditSelection():
        Unselected, PreEffect, PostEffect = range(3)

    def setupTrackOverviewGui(self, plane, noteGuiClass, midiChannel, trackSettings, trackGuiSettingsList):
        self._midiTracksPlane = plane
        self._trackGuiSettingsList = trackGuiSettingsList

        self.updateMixmodeThumb = noteGuiClass.updateMixmodeThumb
        self.updateEffectThumb = noteGuiClass.updateEffectThumb
        self.showEffectList = noteGuiClass.showEffectList
        self._clearDragCursorCallback = noteGuiClass.clearDragCursor
        self._mixImages = noteGuiClass._mixImages
        self._mixLabels = noteGuiClass._mixLabels

        if(self._overviewTrackMixModeButtonPopup == None):
            self._overviewTrackMixModeButtonPopup = PcnPopupMenu(self, self._mixImages, self._mixLabels, self._onTrackMixModeChosen)

        self._currentTrackEffectEditorIndex = -1

        isMac = False
        if(sys.platform == "darwin"):
            isMac = True
            font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT) #@UndefinedVariable
            font.SetPointSize(10)

        txt = wx.StaticText(self._midiTracksPlane, wx.ID_ANY, "Pre:", pos=(79, 2+36*midiChannel)) #@UndefinedVariable
        if(isMac == True):
            txt.SetFont(font)
        overviewPreFxButton = PcnImageButton(self._midiTracksPlane, self._blankFxBitmap, self._blankFxBitmap, (79, 14+36*midiChannel), wx.ID_ANY, size=(32, 22)) #@UndefinedVariable
        overviewPreFxButton.enableDoubleClick()
        overviewPreFxButton.Bind(wx.EVT_BUTTON, self._onPreEffectClick) #@UndefinedVariable
        overviewPreFxButton.Bind(EVT_DOUBLE_CLICK_EVENT, self._onPreFxButtonDouble)
        overviewPreFxButton.Bind(EVT_DRAG_DONE_EVENT, self._onDragPreFxDone)
        trackSettings.setPreFxWidget(overviewPreFxButton)

        txt = wx.StaticText(self._midiTracksPlane, wx.ID_ANY, "Mix:", pos=(113, 2+36*midiChannel)) #@UndefinedVariable
        if(isMac == True):
            txt.SetFont(font)
        overviewTrackClipMixButton = PcnImageButton(self._midiTracksPlane, self._blankMixBitmap, self._blankMixBitmap, (113, 17+36*midiChannel), wx.ID_ANY, size=(25, 16)) #@UndefinedVariable
        overviewTrackClipMixButton.Bind(wx.EVT_BUTTON, self._onTrackMixButton) #@UndefinedVariable
        trackSettings.setMixWidget(overviewTrackClipMixButton)

        txt = wx.StaticText(self._midiTracksPlane, wx.ID_ANY, "Lvl:", pos=(140, 2+36*midiChannel)) #@UndefinedVariable
        if(isMac == True):
            txt.SetFont(font)
        overviewTrackClipLvlButton = PcnImageButton(self._midiTracksPlane, self._blankMixBitmap, self._blankMixBitmap, (140, 17+36*midiChannel), wx.ID_ANY, size=(25, 16)) #@UndefinedVariable
        overviewTrackClipLvlButton.Bind(wx.EVT_BUTTON, self._onTrackLvlButton) #@UndefinedVariable
        trackSettings.setLvlWidget(overviewTrackClipLvlButton)

        txt = wx.StaticText(self._midiTracksPlane, wx.ID_ANY, "Post:", pos=(167, 2+36*midiChannel)) #@UndefinedVariable
        if(isMac == True):
            txt.SetFont(font)
        overviewPostFxButton = PcnImageButton(self._midiTracksPlane, self._blankFxBitmap, self._blankFxBitmap, (167, 14+36*midiChannel), wx.ID_ANY, size=(32, 22)) #@UndefinedVariable
        overviewPostFxButton.enableDoubleClick()
        overviewPostFxButton.Bind(wx.EVT_BUTTON, self._onPostEffectClick) #@UndefinedVariable
        overviewPostFxButton.Bind(EVT_DOUBLE_CLICK_EVENT, self._onPostFxButtonDouble)
        overviewPostFxButton.Bind(EVT_DRAG_DONE_EVENT, self._onDragPostFxDone)
        trackSettings.setPostFxWidget(overviewPostFxButton)

    def setupPreviewGui(self, overviewPanel):
        self._previewPlane = overviewPanel
        wx.StaticText(overviewPanel, wx.ID_ANY, "PREVIEW:", pos=(4, 6)) #@UndefinedVariable
        previewBitmap = wx.Bitmap("graphics/blackPreview.png") #@UndefinedVariable
        self._overviewPreviewButton = PcnKeyboardButton(self._previewPlane, previewBitmap, (20, 20), wx.ID_ANY, size=(162, 142), isBlack=False) #@UndefinedVariable
        self._overviewPreviewButton.setFrqameAddingFunction(addTrackButtonFrame)

    def setupTrackGui(self, plane, sizer, parentSizer, parentClass):
        self._mainTrackPlane = plane
        self._mainTrackGuiSizer = sizer
        self._parentSizer = parentSizer
        self._showTrackGuiCallback = parentClass.showTrackGui
        self._hideTrackGuiCallback = parentClass.hideTrackGui
        self._showSlidersCallback = parentClass.showSlidersGui
        self._hideSlidersCallback = parentClass.hideSlidersGui
        self._showEffectsCallback = parentClass.showEffectsGui
        self._hideEffectsCallback = parentClass.hideEffectsGui
        self._showModulationCallback = parentClass.showModulationGui
        self._hideModulationCallback = parentClass.hideModulationGui

        headerLabel = wx.StaticText(self._mainTrackPlane, wx.ID_ANY, "Track configuration:") #@UndefinedVariable
        headerFont = headerLabel.GetFont()
        headerFont.SetWeight(wx.BOLD) #@UndefinedVariable
        headerLabel.SetFont(headerFont)
        self._mainTrackGuiSizer.Add(headerLabel, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        self._trackId = 0
        trackSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText1 = wx.StaticText(self._mainTrackPlane, wx.ID_ANY, "Channel:") #@UndefinedVariable
        self._trackField = wx.TextCtrl(self._mainTrackPlane, wx.ID_ANY, str(self._trackId + 1), size=(200, -1)) #@UndefinedVariable
        self._trackField.SetEditable(False)
        self._trackField.SetBackgroundColour((232,232,232))
        self._trackField.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        trackHelpButton = PcnImageButton(self._mainTrackPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        trackHelpButton.Bind(wx.EVT_BUTTON, self._onTrackHelp) #@UndefinedVariable
        trackSizer.Add(tmpText1, 1, wx.ALL, 5) #@UndefinedVariable
        trackSizer.Add(self._trackField, 1, wx.ALL, 5) #@UndefinedVariable
        trackSizer.Add(trackHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainTrackGuiSizer.Add(trackSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        mixSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText6 = wx.StaticText(self._mainTrackPlane, wx.ID_ANY, "Mix mode:") #@UndefinedVariable
        self._mixField = wx.ComboBox(self._mainTrackPlane, wx.ID_ANY, size=(200, -1), choices=["Default"], style=wx.CB_READONLY) #@UndefinedVariable
        self._mixField.Bind(wx.EVT_COMBOBOX, self._onUpdate) #@UndefinedVariable
        self._updateChoices(self._mixField, self._mixModes.getChoices, "Default", "Default")
        mixHelpButton = PcnImageButton(self._mainTrackPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        mixHelpButton.Bind(wx.EVT_BUTTON, self._onMixHelp) #@UndefinedVariable
        mixSizer.Add(tmpText6, 1, wx.ALL, 5) #@UndefinedVariable
        mixSizer.Add(self._mixField, 1, wx.ALL, 5) #@UndefinedVariable
        mixSizer.Add(mixHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainTrackGuiSizer.Add(mixSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        levelModulationSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self._mainTrackPlane, wx.ID_ANY, "Level modulation:") #@UndefinedVariable
        self._levelModulationField = wx.TextCtrl(self._mainTrackPlane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._levelModulationField.SetInsertionPoint(0)
        self._levelModulationField.Bind(wx.EVT_COMBOBOX, self._onUpdate) #@UndefinedVariable
        levelModulationButton = PcnImageButton(self._mainTrackPlane, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        levelModulationButton.Bind(wx.EVT_BUTTON, self._onLevelModulationEdit) #@UndefinedVariable
        levelModulationSizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        levelModulationSizer.Add(self._levelModulationField, 1, wx.ALL, 5) #@UndefinedVariable
        levelModulationSizer.Add(levelModulationButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainTrackGuiSizer.Add(levelModulationSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        preEffectSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText8 = wx.StaticText(self._mainTrackPlane, wx.ID_ANY, "Pre effect template:") #@UndefinedVariable
        self._preEffectField = wx.ComboBox(self._mainTrackPlane, wx.ID_ANY, size=(200, -1), choices=["MediaDefault1"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateEffecChoices(self._preEffectField, "MixPreDefault", "MixPreDefault")
        self._preEffectField.Bind(wx.EVT_COMBOBOX, self._onUpdate) #@UndefinedVariable
        self._preEffectButton = PcnImageButton(self._mainTrackPlane, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._preEffectButton.Bind(wx.EVT_BUTTON, self._onPreEffectEdit) #@UndefinedVariable
        preEffectSizer.Add(tmpText8, 1, wx.ALL, 5) #@UndefinedVariable
        preEffectSizer.Add(self._preEffectField, 1, wx.ALL, 5) #@UndefinedVariable
        preEffectSizer.Add(self._preEffectButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainTrackGuiSizer.Add(preEffectSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        postEffectSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText9 = wx.StaticText(self._mainTrackPlane, wx.ID_ANY, "Post effect template:") #@UndefinedVariable
        self._postEffectField = wx.ComboBox(self._mainTrackPlane, wx.ID_ANY, size=(200, -1), choices=["MediaDefault2"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateEffecChoices(self._postEffectField, "MixPostDefault", "MixPostDefault")
        self._postEffectField.Bind(wx.EVT_COMBOBOX, self._onUpdate) #@UndefinedVariable
        self._postEffectButton = PcnImageButton(self._mainTrackPlane, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._postEffectButton.Bind(wx.EVT_BUTTON, self._onPostEffectEdit) #@UndefinedVariable
        postEffectSizer.Add(tmpText9, 1, wx.ALL, 5) #@UndefinedVariable
        postEffectSizer.Add(self._postEffectField, 1, wx.ALL, 5) #@UndefinedVariable
        postEffectSizer.Add(self._postEffectButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainTrackGuiSizer.Add(postEffectSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = PcnImageButton(self._mainTrackPlane, self._closeButtonBitmap, self._closeButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(55, 17)) #@UndefinedVariable
        closeButton.Bind(wx.EVT_BUTTON, self._onCloseButton) #@UndefinedVariable
        self._saveButton = PcnImageButton(self._mainTrackPlane, self._saveBigGreyBitmap, self._saveBigGreyBitmap, (-1, -1), wx.ID_ANY, size=(52, 17)) #@UndefinedVariable
        self._saveButton.Bind(wx.EVT_BUTTON, self._onSaveButton) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(self._saveButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainTrackGuiSizer.Add(self._buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

    def _updateEffecChoices(self, widget, value, defaultValue):
        if(self._mainConfig == None):
            self._updateChoices(widget, None, value, defaultValue)
        else:
            self._updateChoices(widget, self._mainConfig.getEffectChoices, value, defaultValue)

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

    def _onTrackHelp(self, event):
        text = """
This is the track number and MIDI channel.
"""
        dlg = wx.MessageDialog(self._mainTrackPlane, text, 'Track help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onMixHelp(self, event):
        text = """
Decides how this image is mixed with images on lower MIDI channels.
\t(This overrides media mix mode if not set to Default.)

Default:\tUses Add if no other mode has been selected by media.
Add:\tSums the images together.
Multiply:\tMultiplies the images together. Very handy for masking.
Lumakey:\tReplaces source everywhere the image is not black.
Replace:\tNo mixing. Just use this image.
"""
        dlg = wx.MessageDialog(self._mainTrackPlane, text, 'Mix help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _highlightButton(self, selected):
        if(selected == self.EditSelection.PreEffect):
            self._preEffectButton.setBitmaps(self._editSelectedBitmap, self._editSelectedBitmap)
        else:
            self._preEffectButton.setBitmaps(self._editBitmap, self._editPressedBitmap)
        if(selected == self.EditSelection.PostEffect):
            self._postEffectButton.setBitmaps(self._editSelectedBitmap, self._editSelectedBitmap)
        else:
            self._postEffectButton.setBitmaps(self._editBitmap, self._editPressedBitmap)

    def _onTrackMixButton(self, event):
        buttonId = event.GetEventObject().GetId()
        foundTrackId = None
        for i in range(16):
            if(self._trackGuiSettingsList[i].hasMixWidgetId(buttonId)):
                foundTrackId = i
                break
        if(foundTrackId != None):
            trackSettings = self._trackGuiSettingsList[foundTrackId]
            self._overviewTrackMixModePopupButtonIndex = foundTrackId
            trackSettings.getMixWidget().PopupMenu(self._overviewTrackMixModeButtonPopup, (23,0))

    def _onTrackMixModeChosen(self, index):
        if((index >= 0) and (index < len(self._mixLabels))):
            mixMode = self._mixLabels[index]
            self._updateChoices(self._mixField, self._mixModes.getChoices, mixMode, "Default")
            if(self._overviewTrackMixModePopupButtonIndex >= 0):
                trackSettings = self._trackGuiSettingsList[self._overviewTrackMixModePopupButtonIndex]
                self.updateMixmodeThumb(trackSettings.getMixWidget(), mixMode, mixMode, True)
                trackConfig = self._mainConfig.getTrackConfiguration(self._overviewTrackMixModePopupButtonIndex)
                trackConfig.setValue("MixMode", mixMode)
            self._showOrHideSaveButton()

    def _onTrackLvlButton(self, event):
        buttonId = event.GetEventObject().GetId()
        foundTrackId = None
        for i in range(16):
            if(self._trackGuiSettingsList[i].hasLvlWidgetId(buttonId)):
                foundTrackId = i
                break
        if(foundTrackId != None):
            trackConfig = self._mainConfig.getTrackConfiguration(foundTrackId)
            self._mainConfig.updateModulationGui(trackConfig.getValue("LevelModulation"), None, None, self._onTrackLvlButtonEditSave, foundTrackId)
            self._showModulationCallback()

    def _onTrackLvlButtonEditSave(self, trackId, value):
        trackConfig = self._mainConfig.getTrackConfiguration(trackId)
        if(trackConfig != None):
            levelMod = self._midiModulation.validateModulationString(value)
            trackConfig.setValue("LevelModulation", levelMod)

    def _onLevelModulationEdit(self, event):
        self._showModulationCallback()
        self._mainConfig.updateModulationGui(self._levelModulationField.GetValue(), self._levelModulationField, None, None)

    def _onPreEffectEdit(self, event):
        if(self._selectedEditor != self.EditSelection.PreEffect):
            self._selectedEditor = self.EditSelection.PreEffect
            self._showEffectsCallback()
        else:
            self._selectedEditor = self.EditSelection.Unselected
            self._hideEffectsCallback()
        self._hideModulationCallback()
        selectedEffectConfig = self._preEffectField.GetValue()
        self._mainConfig.updateEffectsGui(selectedEffectConfig, None, "PreEffect")
        self._showOrHideSaveButton()
        self._highlightButton(self._selectedEditor)

    def _onPostEffectEdit(self, event):
        if(self._selectedEditor != self.EditSelection.PostEffect):
            self._selectedEditor = self.EditSelection.PostEffect
            self._showEffectsCallback()
        else:
            self._selectedEditor = self.EditSelection.Unselected
            self._hideEffectsCallback()
        self._hideModulationCallback()
        selectedEffectConfig = self._postEffectField.GetValue()
        self._mainConfig.updateEffectsGui(selectedEffectConfig, None, "PostEffect")
        self._showOrHideSaveButton()
        self._highlightButton(self._selectedEditor)

    def _onPreEffectClick(self, event):
        buttonId = event.GetEventObject().GetId()
        foundTrackId = None
        for i in range(16):
            if(self._trackGuiSettingsList[i].hasPreFxWidgetId(buttonId)):
                foundTrackId = i
                break
        if(foundTrackId != None):
            self._currentTrackEffectEditorIndex = foundTrackId
            trackConfig = self._mainConfig.getTrackConfiguration(foundTrackId)
            if(self._selectedEditor != self.EditSelection.PreEffect):
                self._hideModulationCallback()
            selectedEffectConfig = trackConfig.getValue("PreEffectConfig")
            self._selectedEditor = self.EditSelection.PreEffect
            self._highlightButton(self._selectedEditor)
            self._mainConfig.updateEffectsGui(selectedEffectConfig, None, "PreEffect")
            self._mainConfig.showSliderGuiEditButton()
            self._showSlidersCallback()
            self._showOrHideSaveButton()

    def _onPostEffectClick(self, event):
        buttonId = event.GetEventObject().GetId()
        foundTrackId = None
        for i in range(16):
            if(self._trackGuiSettingsList[i].hasPostFxWidgetId(buttonId)):
                foundTrackId = i
                break
        if(foundTrackId != None):
            self._currentTrackEffectEditorIndex = foundTrackId
            trackConfig = self._mainConfig.getTrackConfiguration(foundTrackId)
            if(self._selectedEditor != self.EditSelection.PostEffect):
                self._hideModulationCallback()
            selectedEffectConfig = trackConfig.getValue("PostEffectConfig")
            self._selectedEditor = self.EditSelection.PostEffect
            self._highlightButton(self._selectedEditor)
            self._mainConfig.updateEffectsGui(selectedEffectConfig, None, "PostEffect")
            self._mainConfig.showSliderGuiEditButton()
            self._showSlidersCallback()
            self._showOrHideSaveButton()

    def _onPreFxButtonDouble(self, event):
        selectedEffectConfig = self._preEffectField.GetValue()
        self._mainConfig.updateEffectList(selectedEffectConfig)
        self.showEffectList()

    def _onPostFxButtonDouble(self, event):
        selectedEffectConfig = self._postEffectField.GetValue()
        self._mainConfig.updateEffectList(selectedEffectConfig)
        self.showEffectList()

    def _onDragPreFxDone(self, event):
        buttonId = event.GetEventObject().GetId()
        foundTrackId = None
        for i in range(16):
            if(self._trackGuiSettingsList[i].hasPreFxWidgetId(buttonId)):
                foundTrackId = i
                break
        if(foundTrackId != None):
            trackSettings = self._trackGuiSettingsList[foundTrackId]
            self._currentTrackEffectEditorIndex = foundTrackId
            trackConfig = self._mainConfig.getTrackConfiguration(foundTrackId)
            fxName = self._mainConfig.getDraggedFxName()
            if(fxName != None):
                if(self._trackId != None):
                    trackConfig.setValue("PreEffectConfig", fxName)
                    if(foundTrackId == self._trackId):
                        self._updateEffecChoices(self._preEffectField, fxName, "MixPreDefault")
                    self.updateEffectThumb(trackSettings.getPreFxWidget(), fxName)
                    self._showOrHideSaveButton()
            self._clearDragCursorCallback()

    def _onDragPostFxDone(self, event):
        buttonId = event.GetEventObject().GetId()
        foundTrackId = None
        for i in range(16):
            if(self._trackGuiSettingsList[i].hasPostFxWidgetId(buttonId)):
                foundTrackId = i
                break
        if(foundTrackId != None):
            trackSettings = self._trackGuiSettingsList[foundTrackId]
            self._currentTrackEffectEditorIndex = foundTrackId
            trackConfig = self._mainConfig.getTrackConfiguration(foundTrackId)
            fxName = self._mainConfig.getDraggedFxName()
            if(fxName != None):
                if(self._trackId != None):
                    trackConfig.setValue("PostEffectConfig", fxName)
                    if(foundTrackId == self._trackId):
                        self._updateEffecChoices(self._postEffectField, fxName, "MixPostDefault")
                    self.updateEffectThumb(trackSettings.getPostFxWidget(), fxName)
                    self._showOrHideSaveButton()
            self._clearDragCursorCallback()

    def closeTackGui(self):
        self._onCloseButton(None)

    def _onCloseButton(self, event):
        self._hideTrackGuiCallback()
        self._hideEffectsCallback()
        self._hideModulationCallback()
        self._hideSlidersCallback()
        self._selectedEditor = self.EditSelection.Unselected
        self._highlightButton(self._selectedEditor)

    def _onSaveButton(self, event):
        if(self._config != None):
            mixMode = self._mixField.GetValue()
            self._config.setValue("MixMode", mixMode)
            levelMod = self._midiModulation.validateModulationString(self._levelModulationField.GetValue())
            self._levelModulationField.SetValue(levelMod)
            self._config.setValue("LevelModulation", levelMod)
            preEffectConfig = self._preEffectField.GetValue()
            self._config.setValue("PreEffectConfig", preEffectConfig)
            postEffectConfig = self._postEffectField.GetValue()
            self._config.setValue("PostEffectConfig", postEffectConfig)
            if((self._trackId >= 0) and (self._trackId < 16)):
                trackSettings = self._trackGuiSettingsList[self._trackId]
                self.updateTrackMixModeThumb(self._trackId, self._config, "None")
                self.updateTrackLvlModThumb(self._trackId, self._config)
                self.updateEffectThumb(trackSettings.getPreFxWidget(), preEffectConfig)
                self.updateEffectThumb(trackSettings.getPostFxWidget(), postEffectConfig)
                
        self._showOrHideSaveButton()

    def _checkIfUpdated(self):
        if(self._config == None):
            return False
        guiMixMode = self._mixField.GetValue()
        configMixMode = self._config.getValue("MixMode")
        if(guiMixMode != configMixMode):
            return True
        guiLvlMode = self._levelModulationField.GetValue()
        configLvlMode = self._config.getValue("LevelModulation")
        if(guiLvlMode != configLvlMode):
            return True
        guiPreEffect = self._preEffectField.GetValue()
        configPreEffect = self._config.getValue("PreEffectConfig")
        if(guiPreEffect != configPreEffect):
            return True
        guiPostEffect = self._postEffectField.GetValue()
        configPostEffect = self._config.getValue("PostEffectConfig")
        if(guiPostEffect != configPostEffect):
            return True
        return False

    def _onUpdate(self, event):
        self._showOrHideSaveButton()

    def _showOrHideSaveButton(self):
        updated = self._checkIfUpdated()
        if(updated == False):
            self._saveButton.setBitmaps(self._saveBigGreyBitmap, self._saveBigGreyBitmap)
        if(updated == True):
            self._saveButton.setBitmaps(self._saveBigBitmap, self._saveBigPressedBitmap)

    def updateTrackMixModeThumb(self, index, trackConfig, noteMixMode):
        widget = self._trackGuiSettingsList[index].getMixWidget()
        if(trackConfig != None):
            mixMode = trackConfig.getValue("MixMode")
        else:
            mixMode = "Default"
        self.updateMixmodeThumb(widget, mixMode, noteMixMode)
        self._showOrHideSaveButton()

    def updateTrackLvlModThumb(self, index, trackConfig):
        widget = self._trackGuiSettingsList[index].getLvlWidget()
        if(trackConfig != None):
            mixMode = trackConfig.getValue("LevelModulation")
        else:
            mixMode = "None"
        self._mainConfig.updateModulationGuiButton(widget, mixMode)
        self._showOrHideSaveButton()

    def updateTrackEffectsThumb(self, index, trackConfig):
        trackSettings = self._trackGuiSettingsList[index]
        if(trackConfig != None):
            preFxName = trackConfig.getValue("PreEffectConfig")
            postFxName = trackConfig.getValue("PostEffectConfig")
        else:
            preFxName = "MixPreDefault"
            postFxName = "MixPostDefault"
        self.updateEffectThumb(trackSettings.getPreFxWidget(), preFxName)
        self.updateEffectThumb(trackSettings.getPostFxWidget(), postFxName)
        self._showOrHideSaveButton()

    def updatePreviewImage(self, fileName):
        self._overviewPreviewButton.setBitmapFile(fileName)

    def updateGui(self, trackConfig, trackId, midiNote, noteMixMode):
        if(trackConfig != None):
            self._trackId = trackId
            self._config = trackConfig
            self._midiNote = midiNote
            self._latestOverviewMixMode = noteMixMode
        if(self._config == None):
            return
        self._trackField.SetValue(str(self._trackId + 1))
        mixMode = self._config.getValue("MixMode")
        self._updateChoices(self._mixField, self._mixModes.getChoices, mixMode, "Default")
        levelMod = self._config.getValue("LevelModulation")
        self._levelModulationField.SetValue(levelMod)
        preEffectConfig = self._config.getValue("PreEffectConfig")
        self._updateEffecChoices(self._preEffectField, preEffectConfig, "MixPreDefault")
        postEffectConfig = self._config.getValue("PostEffectConfig")
        self._updateEffecChoices(self._postEffectField, postEffectConfig, "MixPostDefault")

        if(self._selectedEditor != self.EditSelection.Unselected):
            if(self._selectedEditor == self.EditSelection.PreEffect):
                self._onPreEffectEdit(None)
            elif(self._selectedEditor == self.EditSelection.PostEffect):
                self._onPostEffectEdit(None)

        self._showOrHideSaveButton()

