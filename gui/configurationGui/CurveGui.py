'''
Created on 27. dec. 2012

@author: pcn
'''

import wx
from widgets.PcnImageButton import PcnImageButton
from widgets.PcnCurveDisplayWindget import PcnCurveDisplayWidget
from widgets.PcnEvents import EVT_DOUBLE_CLICK_EVENT, EVT_MOUSE_MOVE_EVENT
from configurationGui.UtilityDialogs import updateChoices
from video.Curve import Curve

class CurveGui(object):
    def __init__(self, mainConfing):
        self._mainConfig = mainConfing
        self._updateWidget = None
        self._closeCallback = None
        self._saveCallback = None
        self._saveArgument = None

        self._curveConfig = Curve()

        self._helpBitmap = wx.Bitmap("graphics/helpButton.png") #@UndefinedVariable
        self._helpPressedBitmap = wx.Bitmap("graphics/helpButtonPressed.png") #@UndefinedVariable

        self._closeButtonBitmap = wx.Bitmap("graphics/closeButton.png") #@UndefinedVariable
        self._closeButtonPressedBitmap = wx.Bitmap("graphics/closeButtonPressed.png") #@UndefinedVariable
        self._updateButtonBitmap = wx.Bitmap("graphics/updateButton.png") #@UndefinedVariable
        self._updateButtonPressedBitmap = wx.Bitmap("graphics/updateButtonPressed.png") #@UndefinedVariable
        self._updateRedButtonBitmap = wx.Bitmap("graphics/updateButtonRed.png") #@UndefinedVariable
        self._updateRedButtonPressedBitmap = wx.Bitmap("graphics/updateButtonRedPressed.png") #@UndefinedVariable
        self._saveBigBitmap = wx.Bitmap("graphics/saveButtonBig.png") #@UndefinedVariable
        self._saveBigPressedBitmap = wx.Bitmap("graphics/saveButtonBigPressed.png") #@UndefinedVariable
        self._saveBigGreyBitmap = wx.Bitmap("graphics/saveButtonBigGrey.png") #@UndefinedVariable
        self._deleteColourButtonBitmap = wx.Bitmap("graphics/deleteColourButton.png") #@UndefinedVariable
        self._deleteColourButtonPressedBitmap = wx.Bitmap("graphics/deleteColourButtonPressed.png") #@UndefinedVariable
        self._deletePointButtonBitmap = wx.Bitmap("graphics/deletePointButton.png") #@UndefinedVariable
        self._deletePointButtonPressedBitmap = wx.Bitmap("graphics/deletePointButtonPressed.png") #@UndefinedVariable

    def setupCurveGui(self, plane, sizer, parentSizer, parentClass):
        self._mainCurveGuiPlane = plane
        self._mainCurveGuiSizer = sizer
        self._parentSizer = parentSizer
        self._hideCurveCallback = parentClass.hideCurveGui
        self._fixCurveGuiLayout = parentClass.fixCurveGuiLayout

        headerLabel = wx.StaticText(self._mainCurveGuiPlane, wx.ID_ANY, "Curve editor:") #@UndefinedVariable
        headerFont = headerLabel.GetFont()
        headerFont.SetWeight(wx.BOLD) #@UndefinedVariable
        headerLabel.SetFont(headerFont)
        self._mainCurveGuiSizer.Add(headerLabel, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        curveModeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText1 = wx.StaticText(self._mainCurveGuiPlane, wx.ID_ANY, "Curve mode:") #@UndefinedVariable
        self._curveModeField = wx.ComboBox(self._mainCurveGuiPlane, wx.ID_ANY, size=(200, -1), choices=["Off"], style=wx.CB_READONLY) #@UndefinedVariable
        updateChoices(self._curveModeField, self._curveConfig.getChoices, "Off", "Off")
        curveModeButton = PcnImageButton(self._mainCurveGuiPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        curveModeButton.Bind(wx.EVT_BUTTON, self._onCurveModeHelp) #@UndefinedVariable
        curveModeSizer.Add(tmpText1, 1, wx.ALL, 5) #@UndefinedVariable
        curveModeSizer.Add(self._curveModeField, 2, wx.ALL, 5) #@UndefinedVariable
        curveModeSizer.Add(curveModeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainCurveGuiSizer.Add(curveModeSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._mainCurveGuiPlane.Bind(wx.EVT_COMBOBOX, self._onCurveModeChosen, id=self._curveModeField.GetId()) #@UndefinedVariable

        self._curveSubModeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText1 = wx.StaticText(self._mainCurveGuiPlane, wx.ID_ANY, "Curve sub mode:") #@UndefinedVariable
        self._curveSubModeField = wx.ComboBox(self._mainCurveGuiPlane, wx.ID_ANY, size=(200, -1), choices=["Linear"], style=wx.CB_READONLY) #@UndefinedVariable
        updateChoices(self._curveSubModeField, self._curveConfig.getSubChoices, "Linear", "Linear")
        curveSubModeButton = PcnImageButton(self._mainCurveGuiPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        curveSubModeButton.Bind(wx.EVT_BUTTON, self._onCurveSubModeHelp) #@UndefinedVariable
        self._curveSubModeSizer.Add(tmpText1, 1, wx.ALL, 5) #@UndefinedVariable
        self._curveSubModeSizer.Add(self._curveSubModeField, 2, wx.ALL, 5) #@UndefinedVariable
        self._curveSubModeSizer.Add(curveSubModeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainCurveGuiSizer.Add(self._curveSubModeSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._mainCurveGuiPlane.Bind(wx.EVT_COMBOBOX, self._onCurveSubModeChosen, id=self._curveSubModeField.GetId()) #@UndefinedVariable

        self._curveChannelSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText1 = wx.StaticText(self._mainCurveGuiPlane, wx.ID_ANY, "Edit channel:") #@UndefinedVariable
        self._curveChannelField = wx.ComboBox(self._mainCurveGuiPlane, wx.ID_ANY, size=(200, -1), choices=["Red"], style=wx.CB_READONLY) #@UndefinedVariable
        updateChoices(self._curveChannelField, None, "Red", "Red", ["Red", "Green", "Blue"])
        curveChannelButton = PcnImageButton(self._mainCurveGuiPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        curveChannelButton.Bind(wx.EVT_BUTTON, self._onCurveChannelHelp) #@UndefinedVariable
        self._curveChannelSizer.Add(tmpText1, 1, wx.ALL, 5) #@UndefinedVariable
        self._curveChannelSizer.Add(self._curveChannelField, 2, wx.ALL, 5) #@UndefinedVariable
        self._curveChannelSizer.Add(curveChannelButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainCurveGuiSizer.Add(self._curveChannelSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._mainCurveGuiPlane.Bind(wx.EVT_COMBOBOX, self._onCurveChannelChosen, id=self._curveChannelField.GetId()) #@UndefinedVariable

        self._curveGraphicsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._curveGraphicsLabel = wx.StaticText(self._mainCurveGuiPlane, wx.ID_ANY, "Curve graph:") #@UndefinedVariable
        self._curveGraphicsDisplay = PcnCurveDisplayWidget(self._mainCurveGuiPlane)
        curveGraphicsValueButton = PcnImageButton(self._mainCurveGuiPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        curveGraphicsValueButton.Bind(wx.EVT_BUTTON, self._onCurveGraphicsHelp) #@UndefinedVariable
        self._curveGraphicsDisplay.Bind(wx.EVT_BUTTON, self._onCurveSingleClick) #@UndefinedVariable
        self._curveGraphicsDisplay.Bind(EVT_DOUBLE_CLICK_EVENT, self._onCurveDoubleClick) #@UndefinedVariable
        self._curveGraphicsDisplay.Bind(EVT_MOUSE_MOVE_EVENT, self._onMouseMove) #@UndefinedVariable
        self._curveGraphicsSizer.Add(self._curveGraphicsLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._curveGraphicsSizer.Add(self._curveGraphicsDisplay, 2, wx.ALL, 5) #@UndefinedVariable
        self._curveGraphicsSizer.Add(curveGraphicsValueButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainCurveGuiSizer.Add(self._curveGraphicsSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        self._pointSelectSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._pointSelectLabel = wx.StaticText(self._mainCurveGuiPlane, wx.ID_ANY, "Select:") #@UndefinedVariable
        self._pointSelectSlider = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=255, size=(200, -1)) #@UndefinedVariable
        self._pointSelectDisplay = wx.StaticText(plane, wx.ID_ANY, "1", size=(30,-1)) #@UndefinedVariable
        self._pointSelectSizer.Add(self._pointSelectLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._pointSelectSizer.Add(self._pointSelectSlider, 2, wx.ALL, 5) #@UndefinedVariable
        self._pointSelectSizer.Add(self._pointSelectDisplay, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainCurveGuiSizer.Add(self._pointSelectSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        self._pointPositionSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._pointPositionLabel = wx.StaticText(self._mainCurveGuiPlane, wx.ID_ANY, "Position:") #@UndefinedVariable
        self._pointPositionSlider = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=255, size=(200, -1)) #@UndefinedVariable
        self._pointPositionDisplay = wx.StaticText(plane, wx.ID_ANY, "1", size=(30,-1)) #@UndefinedVariable
        self._pointPositionSizer.Add(self._pointPositionLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._pointPositionSizer.Add(self._pointPositionSlider, 2, wx.ALL, 5) #@UndefinedVariable
        self._pointPositionSizer.Add(self._pointPositionDisplay, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainCurveGuiSizer.Add(self._pointPositionSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        self._pointValue1Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._pointValue1Label = wx.StaticText(self._mainCurveGuiPlane, wx.ID_ANY, "Red:") #@UndefinedVariable
        self._pointValue1Slider = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=255, size=(200, -1)) #@UndefinedVariable
        self._pointValue1Display = wx.StaticText(plane, wx.ID_ANY, "1", size=(30,-1)) #@UndefinedVariable
        self._pointValue1Sizer.Add(self._pointValue1Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._pointValue1Sizer.Add(self._pointValue1Slider, 2, wx.ALL, 5) #@UndefinedVariable
        self._pointValue1Sizer.Add(self._pointValue1Display, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainCurveGuiSizer.Add(self._pointValue1Sizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        self._pointValue2Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._pointValue2Label = wx.StaticText(self._mainCurveGuiPlane, wx.ID_ANY, "Green:") #@UndefinedVariable
        self._pointValue2Slider = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=255, size=(200, -1)) #@UndefinedVariable
        self._pointValue2Display = wx.StaticText(plane, wx.ID_ANY, "1", size=(30,-1)) #@UndefinedVariable
        self._pointValue2Sizer.Add(self._pointValue2Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._pointValue2Sizer.Add(self._pointValue2Slider, 2, wx.ALL, 5) #@UndefinedVariable
        self._pointValue2Sizer.Add(self._pointValue2Display, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainCurveGuiSizer.Add(self._pointValue2Sizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        self._pointValue3Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._pointValue3Label = wx.StaticText(self._mainCurveGuiPlane, wx.ID_ANY, "Blue:") #@UndefinedVariable
        self._pointValue3Slider = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=255, size=(200, -1)) #@UndefinedVariable
        self._pointValue3Display = wx.StaticText(plane, wx.ID_ANY, "1", size=(30,-1)) #@UndefinedVariable
        self._pointValue3Sizer.Add(self._pointValue3Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._pointValue3Sizer.Add(self._pointValue3Slider, 2, wx.ALL, 5) #@UndefinedVariable
        self._pointValue3Sizer.Add(self._pointValue3Display, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainCurveGuiSizer.Add(self._pointValue3Sizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        self._selectSliderId = self._pointSelectSlider.GetId()
        self._selectedPointId = 0
        self._positionSliderId = self._pointPositionSlider.GetId()
        self._value1SliderId = self._pointValue1Slider.GetId()
        self._value2SliderId = self._pointValue2Slider.GetId()
        self._value3SliderId = self._pointValue3Slider.GetId()
        plane.Bind(wx.EVT_SLIDER, self._onSlide) #@UndefinedVariable

        """Buttons"""

        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = PcnImageButton(self._mainCurveGuiPlane, self._closeButtonBitmap, self._closeButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(55, 17)) #@UndefinedVariable
        closeButton.Bind(wx.EVT_BUTTON, self._onCloseButton) #@UndefinedVariable
        self._saveButton = PcnImageButton(self._mainCurveGuiPlane, self._updateButtonBitmap, self._updateButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(67, 17)) #@UndefinedVariable
        self._saveButton.Bind(wx.EVT_BUTTON, self._onSaveButton) #@UndefinedVariable
        self._deleteButton = PcnImageButton(self._mainCurveGuiPlane, self._deletePointButtonBitmap, self._deletePointButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(97, 17)) #@UndefinedVariable
        self._deleteButton.Bind(wx.EVT_BUTTON, self._onDeleteButton) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(self._saveButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(self._deleteButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainCurveGuiSizer.Add(self._buttonsSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

    def _onCurveModeHelp(self, event):
        text = "Selects curve mode.\n"
        text += "\n"
        text += "Off:\tNo curve modifications are done.\n"
        text += "All:\tOne curve controlls all channels.\n"
        text += "RGB:\tOne curve for each RGB colour.\n"
        text += "HSV:\tOne curve for each HSV channel.\n"
        dlg = wx.MessageDialog(self._mainCurveGuiPlane, text, 'Curve mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onCurveModeChosen(self, event):
        updateChoices(self._curveModeField, self._curveConfig.getChoices, self._curveModeField.GetValue(), "Off")
        self._curveConfig.changeModeString(self._curveModeField.GetValue())
        self._onCurveChannelChosen(None)
        if(self._curveConfig.getMode() == Curve.Threshold):
            self._mainCurveGuiSizer.Hide(self._curveSubModeSizer)
        else:
            self._mainCurveGuiSizer.Show(self._curveSubModeSizer)
        self._autoUpdateSliders()
        self._updateCurveGraph()

    def _onCurveSubModeHelp(self, event):
        text = "Selects how we edit the curve.\n"
        text += "\n"
        text += "Linear:\tAdd points to define curve.\n"
        text += "Threshold:\tSets colours for different levels. Use BW input\n"
        text += "Curve:\tAdd points to define bendt curve.\n"
        text += "Array:\tDraw the curve pixel by pixel.\n"
        dlg = wx.MessageDialog(self._mainCurveGuiPlane, text, 'Curve sub mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onCurveSubModeChosen(self, event):
        updateChoices(self._curveSubModeField, self._curveConfig.getSubChoices, self._curveSubModeField.GetValue(), "Linear")
        self._curveConfig.changeSubModeString(self._curveSubModeField.GetValue())
        self._autoUpdateSliders()
        self._updateCurveGraph()

    def _onCurveChannelHelp(self, event):
        if(self._curveConfig.getMode() == Curve.HSV):
            text = "Selects which channel we are editing now.\n"
            text += "\n"
            text += "Hue:\tEdits hue curve. (Colour rotation.)\n"
            text += "Saturation:\tEdits saturation curve.\n"
            text += "Value:\tEdits value curve.\n"
        else:
            text = "Selects which channel we are editing now.\n"
            text += "\n"
            text += "Red:\tEdits red colour curve.\n"
            text += "Green:\tEdits green colour curve.\n"
            text += "Blue:\tEdits blue colour curve.\n"
        dlg = wx.MessageDialog(self._mainCurveGuiPlane, text, 'Curve sub mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onCurveChannelChosen(self, event):
        if(self._curveConfig.getMode() == Curve.HSV):
            self._mainCurveGuiSizer.Show(self._curveChannelSizer)
            updateChoices(self._curveChannelField, None, self._curveChannelField.GetValue(), "Hue", ["Hue", "Saturation", "Value"])
        elif(self._curveConfig.getMode() == Curve.RGB):
            self._mainCurveGuiSizer.Show(self._curveChannelSizer)
            updateChoices(self._curveChannelField, None, self._curveChannelField.GetValue(), "Red", ["Red", "Green", "Blue"])
        else:
            self._mainCurveGuiSizer.Hide(self._curveChannelSizer)
        self._autoUpdateSliders()
        self._fixCurveGuiLayout()

    def _onCurveGraphicsHelp(self, event):
        if(self._curveConfig.getSubMode() == Curve.Linear):
            text = "Shows the curve\n"
            text += "\n"
            text += "Add points by doubble clicking.\n"
            text += "Select and drag points with left button."
        if(self._curveConfig.getSubMode() == Curve.Curve):
            text = "Shows the curve\n"
            text += "\n"
            text += "Add points by doubble clicking.\n"
            text += "Select and drag points with left button."
        if(self._curveConfig.getSubMode() == Curve.Array):
            text = "Shows the curve\n"
            text += "\n"
            text += "Set point(s) with left button."
        else:
            text = "Shows the curve."
        dlg = wx.MessageDialog(self._mainCurveGuiPlane, text, 'Curve display help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def getSubId(self):
        if(self._curveConfig.getMode() == Curve.Off):
            return -1
        if(self._curveConfig.getMode() == Curve.All):
            return -1
        channelString = self._curveChannelField.GetValue()
        if((channelString == "Red") or (channelString == "Hue")):
            return 0
        if((channelString == "Green") or (channelString == "Saturation")):
            return 1
        if((channelString == "Blue") or (channelString == "Value")):
            return 2

    def _onSlide(self, event):
        sliderId = event.GetEventObject().GetId()
        curveMode = self._curveConfig.getMode()
        if(sliderId == self._selectSliderId):
            if(curveMode == Curve.Threshold):
                self._updateThresholdId(False)
            elif(((curveMode == Curve.Off) and (curveMode == Curve.Array)) == False):
                self._updatePointId(False)
            else:
                self._hideSliders(curveMode == Curve.Off)
        elif(sliderId == self._positionSliderId):
            value = self._pointPositionSlider.GetValue()
            self._pointPositionDisplay.SetLabel(str(value))
            if(curveMode == Curve.Threshold):
                self._updateThresholdSetting(value, None, None, None)
            else:
                self._updatePointSetting(value, None)
        elif(sliderId == self._value1SliderId):
            value = self._pointValue1Slider.GetValue()
            if(curveMode == Curve.Threshold):
                self._pointValue1Display.SetLabel("%02X" %(value))
                self._updateThresholdSetting(None, value, None, None)
            else:
                self._pointValue1Display.SetLabel(str(value))
                self._updatePointSetting(None, value)
        elif(sliderId == self._value2SliderId):
            value = self._pointValue2Slider.GetValue()
            self._pointValue2Display.SetLabel("%02X" %(value))
            self._updateThresholdSetting(None, None, value, None)
        elif(sliderId == self._value3SliderId):
            value = self._pointValue3Slider.GetValue()
            self._pointValue3Display.SetLabel("%02X" %(value))
            self._updateThresholdSetting(None, None, None, value)

    def _updateThresholdSetting(self, value, red, green, blue):
        if(self._selectedPointId != None):
            settingsList = self._curveConfig.getThresholdsSettings()
            settingsListLen = len(settingsList)
            if((self._selectedPointId >= 0) and (self._selectedPointId < settingsListLen)):
                colour, xPos = settingsList[self._selectedPointId]
                if(value != None):
                    settingsList[self._selectedPointId] = colour, value
                elif(red != None):
                    newColour = (colour & 0x00ffff) + (red * 0x010000)
                    settingsList[self._selectedPointId] = newColour, xPos
                elif(green != None):
                    newColour = (colour & 0xff00ff) + (green * 0x000100)
                    settingsList[self._selectedPointId] = newColour, xPos
                elif(blue != None):
                    newColour = (colour & 0xffff00) + blue
                    settingsList[self._selectedPointId] = newColour, xPos
                self._curveConfig.updateFromThresholdsSettings()
                self._updateCurveGraph()
        
    def _updatePointSetting(self, pos, value):
        if(self._selectedPointId != None):
            settingsList = self._curveConfig.getPoints(self.getSubId())[0]
            settingsListLen = len(settingsList)
            if((self._selectedPointId >= 0) and (self._selectedPointId < settingsListLen)):
                xPos, yPos = settingsList[self._selectedPointId]
                if(pos != None):
                    self._curveConfig.movePoint((xPos, yPos), (pos, yPos), self.getSubId())
                elif(value != None):
                    self._curveConfig.movePoint((xPos, yPos), (xPos, value), self.getSubId())
                self._updateCurveGraph()
        
    def _autoUpdateSliders(self):
        curveMode = self._curveConfig.getMode()
        curveSubMode = self._curveConfig.getSubMode()
        if(curveMode == Curve.Threshold):
            self._updateThresholdId(True)
        elif(curveMode == Curve.Off):
            self._hideSliders(True)
        elif(curveSubMode == Curve.Array):
            self._hideSliders(False)
        else:
            self._updatePointId(True)
        self._fixCurveGuiLayout()

    def _hideSliders(self, isOff):
        self._mainCurveGuiSizer.Hide(self._pointSelectSizer)
        if(isOff == True):
            self._mainCurveGuiSizer.Hide(self._pointPositionSizer)
            self._mainCurveGuiSizer.Hide(self._pointValue1Sizer)
        else:
            self._mainCurveGuiSizer.Show(self._pointPositionSizer)
            self._mainCurveGuiSizer.Show(self._pointValue1Sizer)
            self._pointValue1Label.SetLabel("Value:")
        self._mainCurveGuiSizer.Hide(self._pointValue2Sizer)
        self._mainCurveGuiSizer.Hide(self._pointValue3Sizer)

    def _updateThresholdId(self, forceUpdate):
        settingsList = self._curveConfig.getThresholdsSettings()
        settingsListLen = len(settingsList)
        if(forceUpdate == True):
            thresholdId = self._selectedPointId
            self._selectedPointId = -1
        else:
            value = self._pointSelectSlider.GetValue()
            thresholdId = int((float(value) / 256) * settingsListLen)
        self._mainCurveGuiSizer.Show(self._pointSelectSizer)
        self._mainCurveGuiSizer.Show(self._pointPositionSizer)
        self._pointValue1Label.SetLabel("Red:")
        self._mainCurveGuiSizer.Show(self._pointValue1Sizer)
        self._mainCurveGuiSizer.Show(self._pointValue2Sizer)
        self._mainCurveGuiSizer.Show(self._pointValue3Sizer)
        if(thresholdId >= settingsListLen):
            thresholdId = settingsListLen - 1
        if(thresholdId != self._selectedPointId):
            self._selectedPointId = thresholdId
            self._pointSelectDisplay.SetLabel(str(thresholdId+1))
            colour, xPos = settingsList[thresholdId]
            red = (int(colour)&0xff0000) / 0x010000
            green = (int(colour)&0x00ff00) / 0x000100
            blue = (int(colour)&0x0000ff)
            self._pointPositionSlider.SetValue(int(xPos))
            self._pointPositionDisplay.SetLabel(str(xPos))
            self._pointValue1Slider.SetValue(red)
            self._pointValue1Display.SetLabel("%02X" %(red))
            self._pointValue2Slider.SetValue(green)
            self._pointValue2Display.SetLabel("%02X" %(green))
            self._pointValue3Slider.SetValue(blue)
            self._pointValue3Display.SetLabel("%02X" %(blue))

    def _updatePointId(self, forceUpdate):
        subId = self.getSubId()
        curveMode = self._curveConfig.getMode()
        self._mainCurveGuiSizer.Show(self._pointSelectSizer)
        self._mainCurveGuiSizer.Show(self._pointPositionSizer)
        self._pointValue1Label.SetLabel("Value:")
        self._mainCurveGuiSizer.Show(self._pointValue1Sizer)
        self._mainCurveGuiSizer.Hide(self._pointValue2Sizer)
        self._mainCurveGuiSizer.Hide(self._pointValue3Sizer)
        if((subId == -1) and (curveMode != Curve.All)):
            return
        settingsList = self._curveConfig.getPoints(self.getSubId())[0]
        settingsListLen = len(settingsList)
        if(forceUpdate == True):
            pointId = self._selectedPointId
            self._selectedPointId = -1
        else:
            value = self._pointSelectSlider.GetValue()
            pointId = int((float(value) / 256) * settingsListLen)
        if(pointId >= settingsListLen):
            pointId = settingsListLen - 1
        if(pointId != self._selectedPointId):
            self._selectedPointId = pointId
            self._pointSelectSlider.SetValue(int(pointId*256/settingsListLen))
            self._pointSelectDisplay.SetLabel(str(pointId+1))
            xPos, yPos = settingsList[pointId]
            self._pointPositionSlider.SetValue(int(xPos))
            self._pointPositionDisplay.SetLabel(str(xPos))
            self._pointValue1Slider.SetValue(yPos)
            self._pointValue1Display.SetLabel("%d" %(yPos))

    def _onCurveSingleClick(self, event):
        self._curveConfig.drawingDone(self.getSubId())
        self._updateCurveGraph()
        self._autoUpdateSliders()
        if((self._curveConfig.getSubMode() == Curve.Linear) or (self._curveConfig.getSubMode() == Curve.Curve)):
            self._curveConfig.findActivePointId(self.getSubId(), self._curveGraphicsDisplay.getLastPos())
            curveActivePoint = self._curveConfig.getActivePointId(self.getSubId())
            if(curveActivePoint != None):
                self._selectedPointId = curveActivePoint
                self._updatePointId(True)

    def _onCurveDoubleClick(self, event):
        self._curveConfig.addPoint(self._curveGraphicsDisplay.getLastPos(), self.getSubId())
        self._updateCurveGraph()
        self._autoUpdateSliders()
        if((self._curveConfig.getSubMode() == Curve.Linear) or (self._curveConfig.getSubMode() == Curve.Curve)):
            self._curveConfig.findActivePointId(self.getSubId(), self._curveGraphicsDisplay.getLastPos())
            curveActivePoint = self._curveConfig.getActivePointId(self.getSubId())
            if(curveActivePoint != None):
                self._selectedPointId = curveActivePoint
                self._updatePointId(True)

    def _onMouseMove(self, event):
        if(event.mousePressed == True):
            self._curveConfig.drawPoint(event.mousePosition, self.getSubId())
            self._updateCurveGraph()
        else:
            self._curveConfig.drawingDone(-1)
#            self._curveConfig.findActivePointId(self.getSubId(), event.mousePosition)
        if(self._curveConfig.getSubMode() == Curve.Array):
            xPos, yPos = event.mousePosition
            self._pointPositionSlider.SetValue(int(xPos))
            self._pointPositionDisplay.SetLabel(str(xPos))
            self._pointValue1Slider.SetValue(yPos)
            self._pointValue1Display.SetLabel("%d" %(yPos))

    def _updateCurveGraph(self):
        self._curveGraphicsDisplay.drawCurve(self._curveConfig)
        self._checkForUpdates()

    def _onCloseButton(self, event):
        if(self._closeCallback != None):
            self._closeCallback()
        self._hideCurveCallback()


    def _onSaveButton(self, event):
        curveString = self._curveConfig.getString()
        if(self._updateWidget != None):
            self._updateWidget.SetValue(curveString)
        if(self._saveCallback):
            if(self._saveArgument != None):
                self._saveCallback(self._saveArgument, curveString)
            else:
                self._saveCallback(None)
        self._lastSavedCurveString = curveString
        self._checkForUpdates()

    def _onDeleteButton(self, event):
        pass

    def _checkForUpdates(self, event = None):
        newCurveString = self._curveConfig.getString()
        if(self._lastSavedCurveString != newCurveString):
            if(self._saveArgument == None):
                self._saveButton.setBitmaps(self._updateRedButtonBitmap, self._updateRedButtonPressedBitmap)
            else:
                self._saveButton.setBitmaps(self._saveBigBitmap, self._saveBigPressedBitmap)
        else:
            if(self._saveArgument == None):
                self._saveButton.setBitmaps(self._updateButtonBitmap, self._updateButtonPressedBitmap)
            else:
                self._saveButton.setBitmaps(self._saveBigGreyBitmap, self._saveBigGreyBitmap)

    def updateGui(self, curveConfigString, widget, closeCallback, saveCallback, saveArgument):
        self._updateWidget = widget
        self._closeCallback = closeCallback
        self._saveCallback = saveCallback
        self._saveArgument = saveArgument
        self._lastSavedCurveString = curveConfigString
        self._curveConfig.setString(curveConfigString)
        updateChoices(self._curveModeField, self._curveConfig.getChoices, self._curveConfig.getChoices()[self._curveConfig.getMode()], "Off")
        updateChoices(self._curveSubModeField, self._curveConfig.getSubChoices, self._curveConfig.getSubChoices()[self._curveConfig.getSubMode()], "Linear")
        self._onCurveChannelChosen(None)
        if(self._curveConfig.getMode() == Curve.Threshold):
            self._mainCurveGuiSizer.Hide(self._curveSubModeSizer)
        else:
            self._mainCurveGuiSizer.Show(self._curveSubModeSizer)
        self._autoUpdateSliders()
        self._updateCurveGraph()
        self._checkForUpdates()

