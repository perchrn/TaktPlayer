'''
Created on 6. feb. 2012

@author: pcn
'''

import wx
from video.media.MediaFileModes import MixMode

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
        else:
            print "DEBUG: MediaMixerConfig.checkAndUpdateFromConfiguration NOT updated..."

    def countNumberOfTimeEffectTemplateUsed(self, effectConfigName):
        returnNumer = 0
#        for trackConfig in self._mediaPool:
#            if(trackConfig != None):
#                returnNumer += trackConfig.countNumberOfTimeEffectTemplateUsed(effectConfigName)
        return returnNumer

    def countNumberOfTimeFadeTemplateUsed(self, fadeConfigName):
        returnNumer = 0
#        for trackConfig in self._mediaPool:
#            if(trackConfig != None):
#                returnNumer += trackConfig.countNumberOfTimeFadeTemplateUsed(fadeConfigName)
        return returnNumer

    def renameEffectTemplateUsed(self, oldName, newName):
        pass
#        for trackConfig in self._mediaPool:
#            if(trackConfig != None):
#                trackConfig.renameEffectTemplateUsed(oldName, newName)

    def renameFadeTemplateUsed(self, oldName, newName):
        pass
#        for trackConfig in self._mediaPool:
#            if(trackConfig != None):
#                trackConfig.renameFadeTemplateUsed(oldName, newName)

    def verifyEffectTemplateUsed(self, effectConfigNameList):
        pass
#        for trackConfig in self._mediaPool:
#            if(trackConfig != None):
#                trackConfig.verifyEffectTemplateUsed(effectConfigNameList)

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
        self._selectedEditor = self.EditSelection.Unselected

    class EditSelection():
        Unselected, PreEffect, PostEffect = range(3)

    def setupTrackGui(self, plane, sizer, parentSizer, parentClass):
        self._mainTrackPlane = plane
        self._mainTrackGuiSizer = sizer
        self._parentSizer = parentSizer
        self._hideTrackGuiCallback = parentClass.hideTrackGui
        self._showEffectsCallback = parentClass.showEffectsGui
        self._hideEffectsCallback = parentClass.hideEffectsGui
        self._showModulationCallback = parentClass.showModulationGui
        self._hideModulationCallback = parentClass.hideModulationGui
        self._hideSlidersCallback = parentClass.hideSlidersGui

        self._trackId = 0
        trackSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText1 = wx.StaticText(self._mainTrackPlane, wx.ID_ANY, "Channel:") #@UndefinedVariable
        self._trackField = wx.TextCtrl(self._mainTrackPlane, wx.ID_ANY, str(self._trackId + 1), size=(200, -1)) #@UndefinedVariable
        self._trackField.SetEditable(False)
        self._trackField.SetBackgroundColour((232,232,232))
        trackHelpButton = wx.Button(self._mainTrackPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        trackHelpButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._mainTrackPlane.Bind(wx.EVT_BUTTON, self._onTrackHelp, id=trackHelpButton.GetId()) #@UndefinedVariable
        trackSizer.Add(tmpText1, 1, wx.ALL, 5) #@UndefinedVariable
        trackSizer.Add(self._trackField, 2, wx.ALL, 5) #@UndefinedVariable
        trackSizer.Add(trackHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainTrackGuiSizer.Add(trackSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        mixSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText6 = wx.StaticText(self._mainTrackPlane, wx.ID_ANY, "Mix mode:") #@UndefinedVariable
        self._mixField = wx.ComboBox(self._mainTrackPlane, wx.ID_ANY, size=(200, -1), choices=["Default"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateChoices(self._mixField, self._mixModes.getChoices, "Default", "Default")
        mixHelpButton = wx.Button(self._mainTrackPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        mixHelpButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._mainTrackPlane.Bind(wx.EVT_BUTTON, self._onMixHelp, id=mixHelpButton.GetId()) #@UndefinedVariable
        mixSizer.Add(tmpText6, 1, wx.ALL, 5) #@UndefinedVariable
        mixSizer.Add(self._mixField, 2, wx.ALL, 5) #@UndefinedVariable
        mixSizer.Add(mixHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainTrackGuiSizer.Add(mixSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        preEffectSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self._mainTrackPlane, wx.ID_ANY, "Pre effect template:") #@UndefinedVariable
        self._preEffectField = wx.ComboBox(self._mainTrackPlane, wx.ID_ANY, size=(200, -1), choices=["MediaDefault1"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateEffecChoices(self._preEffectField, "MixPreDefault", "MixPreDefault")
        self._preEffectButton = wx.Button(self._mainTrackPlane, wx.ID_ANY, 'Edit', size=(60,-1)) #@UndefinedVariable
        self._preEffectButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainTrackPlane.Bind(wx.EVT_BUTTON, self._onPreEffectEdit, id=self._preEffectButton.GetId()) #@UndefinedVariable
        preEffectSizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        preEffectSizer.Add(self._preEffectField, 2, wx.ALL, 5) #@UndefinedVariable
        preEffectSizer.Add(self._preEffectButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainTrackGuiSizer.Add(preEffectSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        postEffectSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self._mainTrackPlane, wx.ID_ANY, "Post effect template:") #@UndefinedVariable
        self._postEffectField = wx.ComboBox(self._mainTrackPlane, wx.ID_ANY, size=(200, -1), choices=["MediaDefault2"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateEffecChoices(self._postEffectField, "MixPostDefault", "MixPostDefault")
        self._postEffectButton = wx.Button(self._mainTrackPlane, wx.ID_ANY, 'Edit', size=(60,-1)) #@UndefinedVariable
        self._postEffectButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainTrackPlane.Bind(wx.EVT_BUTTON, self._onPostEffectEdit, id=self._postEffectButton.GetId()) #@UndefinedVariable
        postEffectSizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        postEffectSizer.Add(self._postEffectField, 2, wx.ALL, 5) #@UndefinedVariable
        postEffectSizer.Add(self._postEffectButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainTrackGuiSizer.Add(postEffectSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = wx.Button(self._mainTrackPlane, wx.ID_ANY, 'Close') #@UndefinedVariable
        closeButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainTrackPlane.Bind(wx.EVT_BUTTON, self._onCloseButton, id=closeButton.GetId()) #@UndefinedVariable
        saveButton = wx.Button(self._mainTrackPlane, wx.ID_ANY, 'Save') #@UndefinedVariable
        saveButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainTrackPlane.Bind(wx.EVT_BUTTON, self._onSaveButton, id=saveButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 1, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(saveButton, 1, wx.ALL, 5) #@UndefinedVariable
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
        dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Track help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
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
        dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Mix help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _highlightButton(self, selected):
        if(selected == self.EditSelection.PreEffect):
            self._preEffectButton.SetBackgroundColour(wx.Colour(180,180,255)) #@UndefinedVariable
        else:
            self._preEffectButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        if(selected == self.EditSelection.PostEffect):
            self._postEffectButton.SetBackgroundColour(wx.Colour(180,180,255)) #@UndefinedVariable
        else:
            self._postEffectButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable

    def _onPreEffectEdit(self, event):
        self._showEffectsCallback()
        if(self._selectedEditor != self.EditSelection.PreEffect):
            self._hideModulationCallback()
        selectedEffectConfig = self._preEffectField.GetValue()
        self._selectedEditor = self.EditSelection.PreEffect
        self._highlightButton(self._selectedEditor)
        self._mainConfig.updateEffectsGui(selectedEffectConfig, None)

    def _onPostEffectEdit(self, event):
        self._showEffectsCallback()
        if(self._selectedEditor != self.EditSelection.PostEffect):
            self._hideModulationCallback()
        selectedEffectConfig = self._postEffectField.GetValue()
        self._selectedEditor = self.EditSelection.PostEffect
        self._highlightButton(self._selectedEditor)
        self._mainConfig.updateEffectsGui(selectedEffectConfig, None)

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
            postEffectConfig = self._preEffectField.GetValue()
            self._config.setValue("PreEffectConfig", postEffectConfig)
            preEffectConfig = self._postEffectField.GetValue()
            self._config.setValue("PostEffectConfig", preEffectConfig)

    def updateGui(self, trackConfig, trackId):
        self._trackId = trackId
        self._config = trackConfig
        if(self._config == None):
            return
        self._trackField.SetValue(str(self._trackId + 1))
        self._updateChoices(self._mixField, self._mixModes.getChoices, self._config.getValue("MixMode"), "Default")
        self._updateEffecChoices(self._preEffectField, self._config.getValue("PreEffectConfig"), "MixPreDefault")
        self._updateEffecChoices(self._postEffectField, self._config.getValue("PostEffectConfig"), "MixPostDefault")

        if(self._selectedEditor != self.EditSelection.Unselected):
            if(self._selectedEditor == self.EditSelection.PreEffect):
                self._onPreEffectEdit(None)
            elif(self._selectedEditor == self.EditSelection.PostEffect):
                self._onPostEffectEdit(None)


