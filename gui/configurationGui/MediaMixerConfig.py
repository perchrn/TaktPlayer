'''
Created on 6. feb. 2012

@author: pcn
'''

import wx
from video.media.MediaFileModes import MixMode
from widgets.PcnImageButton import PcnKeyboardButton, PcnImageButton,\
    addTrackButtonFrame, EVT_DOUBLE_CLICK_EVENT, EVT_DRAG_DONE_EVENT,\
    PcnPopupMenu

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

        preEffectModulationTemplate = xmlConfig.get("preeffectconfig")
        trackConfig.setValue("PreEffectConfig", preEffectModulationTemplate)

        postEffectModulationTemplate = xmlConfig.get("posteffectconfig")
        trackConfig.setValue("PostEffectConfig", postEffectModulationTemplate)

        return trackId

    def deafultTrackSettings(self, trackIndex):
        trackConfig = self._mediaTrackConfigs[trackIndex]
        trackConfig.setValue("MixMode", "Default")
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
        self._mixMode = MixMode.Default
        self._latestOverviewMixMode = MixMode.Add
        self._midiNote = -1
        self._selectedEditor = self.EditSelection.Unselected

        self._blankModeBitmap = wx.Bitmap("graphics/modeEmpty.png") #@UndefinedVariable
        self._blankMixBitmap = wx.Bitmap("graphics/mixEmpty.png") #@UndefinedVariable
        self._blankFxBitmap = wx.Bitmap("graphics/fxEmpty.png") #@UndefinedVariable

    class EditSelection():
        Unselected, PreEffect, PostEffect = range(3)

    def setupTrackOverviewGui(self, overviewPanel, trackOverviewPanel, parentClass):
        self._mainOverviePlane = overviewPanel
        self._mainTrackOverviewPlane = trackOverviewPanel

        self.updateMixmodeThumb = parentClass.updateMixmodeThumb
        self.updateEffectThumb = parentClass.updateEffectThumb
        self.showEffectList = parentClass.showEffectList
        self._clearDragCursorCallback = parentClass.clearDragCursor
        self._mixImages = parentClass._mixImages
        self._mixLabels = parentClass._mixLabels

        wx.StaticText(self._mainTrackOverviewPlane, wx.ID_ANY, "TRACK MIXER:", pos=(4, 120)) #@UndefinedVariable
        inBitmap = wx.Bitmap("graphics/gfxInput.png") #@UndefinedVariable
        PcnImageButton(self._mainTrackOverviewPlane, inBitmap, inBitmap, (44, 134), wx.ID_ANY, size=(32, 22)) #@UndefinedVariable
        wx.StaticText(self._mainTrackOverviewPlane, wx.ID_ANY, "Pre FX:", pos=(4, 164)) #@UndefinedVariable
        self._overviewPreFxButton = PcnImageButton(self._mainTrackOverviewPlane, self._blankFxBitmap, self._blankFxBitmap, (44, 160), wx.ID_ANY, size=(32, 22)) #@UndefinedVariable
        self._overviewPreFxButton.enableDoubleClick()
        self._overviewPreFxButton.Bind(wx.EVT_BUTTON, self._onPreEffectClick) #@UndefinedVariable
        self._overviewPreFxButton.Bind(EVT_DOUBLE_CLICK_EVENT, self._onPreFxButtonDouble)
        self._overviewPreFxButton.Bind(EVT_DRAG_DONE_EVENT, self._onDragPreFxDone)
        wx.StaticText(self._mainTrackOverviewPlane, wx.ID_ANY, "Mix mode:", pos=(3, 186)) #@UndefinedVariable
        self._overviewTrackClipMixButton = PcnImageButton(self._mainTrackOverviewPlane, self._blankMixBitmap, self._blankMixBitmap, (51, 186), wx.ID_ANY, size=(25, 16)) #@UndefinedVariable
        self._overviewTrackMixModeButtonPopup = PcnPopupMenu(self, self._mixImages, self._mixLabels, self._onTrackMixModeChosen)
        self._overviewTrackClipMixButton.Bind(wx.EVT_BUTTON, self._onTrackMixButton) #@UndefinedVariable
        wx.StaticText(self._mainTrackOverviewPlane, wx.ID_ANY, "Post FX:", pos=(4, 210)) #@UndefinedVariable
        self._overviewPostFxButton = PcnImageButton(self._mainTrackOverviewPlane, self._blankFxBitmap, self._blankFxBitmap, (44, 206), wx.ID_ANY, size=(32, 22)) #@UndefinedVariable
        self._overviewPostFxButton.enableDoubleClick()
        self._overviewPostFxButton.Bind(wx.EVT_BUTTON, self._onPostEffectClick) #@UndefinedVariable
        self._overviewPostFxButton.Bind(EVT_DOUBLE_CLICK_EVENT, self._onPostFxButtonDouble)
        self._overviewPostFxButton.Bind(EVT_DRAG_DONE_EVENT, self._onDragPostFxDone)
        outBitmap = wx.Bitmap("graphics/gfxOutput.png") #@UndefinedVariable
        PcnImageButton(self._mainTrackOverviewPlane, outBitmap, outBitmap, (44, 232), wx.ID_ANY, size=(32, 22)) #@UndefinedVariable

        self._editBitmap = wx.Bitmap("graphics/editButton.png") #@UndefinedVariable
        self._editPressedBitmap = wx.Bitmap("graphics/editButtonPressed.png") #@UndefinedVariable
        self._editSelectedBitmap = wx.Bitmap("graphics/editButtonSelected.png") #@UndefinedVariable
        self._helpBitmap = wx.Bitmap("graphics/helpButton.png") #@UndefinedVariable
        self._helpPressedBitmap = wx.Bitmap("graphics/helpButtonPressed.png") #@UndefinedVariable
        self._saveBitmap = wx.Bitmap("graphics/saveButton.png") #@UndefinedVariable
        self._savePressedBitmap = wx.Bitmap("graphics/saveButtonPressed.png") #@UndefinedVariable
        self._saveGreyBitmap = wx.Bitmap("graphics/saveButtonGrey.png") #@UndefinedVariable
        self._overviewTrackSaveButtonDissabled = True
        self._overviewTrackEditButton = PcnImageButton(self._mainTrackOverviewPlane, self._editBitmap, self._editPressedBitmap, (25, 260), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._overviewTrackEditButton.Bind(wx.EVT_BUTTON, self._onOverviewTrackEditButton) #@UndefinedVariable
        self._overviewTrackSaveButton = PcnImageButton(self._mainTrackOverviewPlane, self._saveGreyBitmap, self._saveGreyBitmap, (45, 260), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._overviewTrackSaveButton.Bind(wx.EVT_BUTTON, self._onOverviewTrackSaveButton) #@UndefinedVariable

        wx.StaticText(overviewPanel, wx.ID_ANY, "PREVIEW:", pos=(4, 290)) #@UndefinedVariable
        previewBitmap = wx.Bitmap("graphics/blackPreview.png") #@UndefinedVariable
        self._overviewPreviewButton = PcnKeyboardButton(self._mainOverviePlane, previewBitmap, (3, 304), wx.ID_ANY, size=(162, 142), isBlack=False) #@UndefinedVariable
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
        trackSizer.Add(self._trackField, 2, wx.ALL, 5) #@UndefinedVariable
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
        mixSizer.Add(self._mixField, 2, wx.ALL, 5) #@UndefinedVariable
        mixSizer.Add(mixHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainTrackGuiSizer.Add(mixSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        preEffectSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self._mainTrackPlane, wx.ID_ANY, "Pre effect template:") #@UndefinedVariable
        self._preEffectField = wx.ComboBox(self._mainTrackPlane, wx.ID_ANY, size=(200, -1), choices=["MediaDefault1"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateEffecChoices(self._preEffectField, "MixPreDefault", "MixPreDefault")
        self._preEffectField.Bind(wx.EVT_COMBOBOX, self._onUpdate) #@UndefinedVariable
        self._preEffectButton = PcnImageButton(self._mainTrackPlane, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._preEffectButton.Bind(wx.EVT_BUTTON, self._onPreEffectEdit) #@UndefinedVariable
        preEffectSizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        preEffectSizer.Add(self._preEffectField, 2, wx.ALL, 5) #@UndefinedVariable
        preEffectSizer.Add(self._preEffectButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainTrackGuiSizer.Add(preEffectSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        postEffectSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self._mainTrackPlane, wx.ID_ANY, "Post effect template:") #@UndefinedVariable
        self._postEffectField = wx.ComboBox(self._mainTrackPlane, wx.ID_ANY, size=(200, -1), choices=["MediaDefault2"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateEffecChoices(self._postEffectField, "MixPostDefault", "MixPostDefault")
        self._postEffectField.Bind(wx.EVT_COMBOBOX, self._onUpdate) #@UndefinedVariable
        self._postEffectButton = PcnImageButton(self._mainTrackPlane, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._postEffectButton.Bind(wx.EVT_BUTTON, self._onPostEffectEdit) #@UndefinedVariable
        postEffectSizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        postEffectSizer.Add(self._postEffectField, 2, wx.ALL, 5) #@UndefinedVariable
        postEffectSizer.Add(self._postEffectButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainTrackGuiSizer.Add(postEffectSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = wx.Button(self._mainTrackPlane, wx.ID_ANY, 'Close') #@UndefinedVariable
        closeButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainTrackPlane.Bind(wx.EVT_BUTTON, self._onCloseButton, id=closeButton.GetId()) #@UndefinedVariable
        self._saveButton = PcnImageButton(self._mainTrackPlane, self._saveGreyBitmap, self._saveGreyBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._saveButton.Bind(wx.EVT_BUTTON, self._onSaveButton) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 1, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(self._saveButton, 1, wx.ALL, 5) #@UndefinedVariable
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
        self._mainTrackOverviewPlane.PopupMenu(self._overviewTrackMixModeButtonPopup, (77,183))

    def _onTrackMixModeChosen(self, index):
        if((index >= 0) and (index < len(self._mixLabels))):
            self._mixMode = self._mixLabels[index]
            self._updateChoices(self._mixField, self._mixModes.getChoices, self._mixMode, "Default")
            self.updateMixmodeThumb(self._overviewTrackClipMixButton, self._mixMode, self._mixMode, True)
            self._showOrHideSaveButton()

    def _onPreEffectEdit(self, event):
        if(self._selectedEditor != self.EditSelection.PreEffect):
            self._hideModulationCallback()
        selectedEffectConfig = self._preEffectField.GetValue()
        self._selectedEditor = self.EditSelection.PreEffect
        self._highlightButton(self._selectedEditor)
        self._mainConfig.updateEffectsGui(selectedEffectConfig, None, "PreEffect")
        self._showEffectsCallback()
        self._showOrHideSaveButton()

    def _onPostEffectEdit(self, event):
        if(self._selectedEditor != self.EditSelection.PostEffect):
            self._hideModulationCallback()
        selectedEffectConfig = self._postEffectField.GetValue()
        self._selectedEditor = self.EditSelection.PostEffect
        self._highlightButton(self._selectedEditor)
        self._mainConfig.updateEffectsGui(selectedEffectConfig, None, "PostEffect")
        self._showEffectsCallback()
        self._showOrHideSaveButton()

    def _onPreEffectClick(self, event):
        if(self._selectedEditor != self.EditSelection.PreEffect):
            self._hideModulationCallback()
        selectedEffectConfig = self._preEffectField.GetValue()
        self._selectedEditor = self.EditSelection.PreEffect
        self._highlightButton(self._selectedEditor)
        self._mainConfig.updateEffectsGui(selectedEffectConfig, None, "PreEffect")
        self._mainConfig.showSliderGuiEditButton()
        self._showSlidersCallback()
        self._showOrHideSaveButton()

    def _onPostEffectClick(self, event):
        if(self._selectedEditor != self.EditSelection.PostEffect):
            self._hideModulationCallback()
        selectedEffectConfig = self._postEffectField.GetValue()
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
        fxName = self._mainConfig.getDraggedFxName()
        if(fxName != None):
            if(self._trackId != None):
                self._updateEffecChoices(self._preEffectField, fxName, "MixPreDefault")
                self.updateEffectThumb(self._overviewPreFxButton, fxName)
                self._showOrHideSaveButton()
        self._clearDragCursorCallback()

    def _onDragPostFxDone(self, event):
        fxName = self._mainConfig.getDraggedFxName()
        if(fxName != None):
            if(self._trackId != None):
                self._updateEffecChoices(self._postEffectField, fxName, "MixPreDefault")
                self.updateEffectThumb(self._overviewPostFxButton, fxName)
                self._showOrHideSaveButton()
        self._clearDragCursorCallback()

    def _onOverviewTrackEditButton(self, event):
        self._showTrackGuiCallback()

    def _onOverviewTrackSaveButton(self, event):
        if(self._overviewTrackSaveButtonDissabled == False):
            self._onSaveButton(event)

    def _onCloseButton(self, event):
        self._hideTrackGuiCallback()
        self._hideEffectsCallback()
        self._hideModulationCallback()
        self._hideSlidersCallback()
        self._selectedEditor = self.EditSelection.Unselected
        self._highlightButton(self._selectedEditor)

    def _onSaveButton(self, event):
        if(self._config != None):
            self._mixMode = self._mixField.GetValue()
            self._config.setValue("MixMode", self._mixMode)
            self.updateMixModeOverviewThumb(self._latestOverviewMixMode)
            preEffectConfig = self._preEffectField.GetValue()
            self._config.setValue("PreEffectConfig", preEffectConfig)
            self.updateEffectThumb(self._overviewPreFxButton, preEffectConfig)
            postEffectConfig = self._postEffectField.GetValue()
            self._config.setValue("PostEffectConfig", postEffectConfig)
            self.updateEffectThumb(self._overviewPostFxButton, postEffectConfig)
        self._showOrHideSaveButton()

    def _checkIfUpdated(self):
        if(self._config == None):
            return False
        guiMixMode = self._mixField.GetValue()
        configMixMode = self._config.getValue("MixMode")
        if(guiMixMode != configMixMode):
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
            self._overviewTrackSaveButton.setBitmaps(self._saveGreyBitmap, self._saveGreyBitmap)
            self._saveButton.setBitmaps(self._saveGreyBitmap, self._saveGreyBitmap)
            self._overviewTrackSaveButtonDissabled = True
        if(updated == True):
            self._overviewTrackSaveButton.setBitmaps(self._saveBitmap, self._savePressedBitmap)
            self._saveButton.setBitmaps(self._saveBitmap, self._savePressedBitmap)
            self._overviewTrackSaveButtonDissabled = False

    def updateMixModeOverviewThumb(self, noteMixMode):
        self.updateMixmodeThumb(self._overviewTrackClipMixButton, self._mixMode, noteMixMode)
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
        self._mixMode = self._config.getValue("MixMode")
        self._updateChoices(self._mixField, self._mixModes.getChoices, self._mixMode, "Default")
        self.updateMixModeOverviewThumb(self._latestOverviewMixMode)
        preEffectConfig = self._config.getValue("PreEffectConfig")
        self._updateEffecChoices(self._preEffectField, preEffectConfig, "MixPreDefault")
        self.updateEffectThumb(self._overviewPreFxButton, preEffectConfig)
        postEffectConfig = self._config.getValue("PostEffectConfig")
        self._updateEffecChoices(self._postEffectField, postEffectConfig, "MixPostDefault")
        self.updateEffectThumb(self._overviewPostFxButton, postEffectConfig)

        if(self._selectedEditor != self.EditSelection.Unselected):
            if(self._selectedEditor == self.EditSelection.PreEffect):
                self._onPreEffectEdit(None)
            elif(self._selectedEditor == self.EditSelection.PostEffect):
                self._onPostEffectEdit(None)

        self._showOrHideSaveButton()

