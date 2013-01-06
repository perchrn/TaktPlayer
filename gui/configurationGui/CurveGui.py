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

        curveSubModeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText1 = wx.StaticText(self._mainCurveGuiPlane, wx.ID_ANY, "Curve sub mode:") #@UndefinedVariable
        self._curveSubModeField = wx.ComboBox(self._mainCurveGuiPlane, wx.ID_ANY, size=(200, -1), choices=["Linear"], style=wx.CB_READONLY) #@UndefinedVariable
        updateChoices(self._curveSubModeField, self._curveConfig.getSubChoices, "Linear", "Linear")
        curveSubModeButton = PcnImageButton(self._mainCurveGuiPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        curveSubModeButton.Bind(wx.EVT_BUTTON, self._onCurveSubModeHelp) #@UndefinedVariable
        curveSubModeSizer.Add(tmpText1, 1, wx.ALL, 5) #@UndefinedVariable
        curveSubModeSizer.Add(self._curveSubModeField, 2, wx.ALL, 5) #@UndefinedVariable
        curveSubModeSizer.Add(curveSubModeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainCurveGuiSizer.Add(curveSubModeSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
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
        self._curveGraphicsId = self._curveGraphicsDisplay.GetId()


        """Buttons"""

        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = PcnImageButton(self._mainCurveGuiPlane, self._closeButtonBitmap, self._closeButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(55, 17)) #@UndefinedVariable
        closeButton.Bind(wx.EVT_BUTTON, self._onCloseButton) #@UndefinedVariable
        self._saveButton = PcnImageButton(self._mainCurveGuiPlane, self._updateButtonBitmap, self._updateButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(67, 17)) #@UndefinedVariable
        self._saveButton.Bind(wx.EVT_BUTTON, self._onSaveButton) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(self._saveButton, 0, wx.ALL, 5) #@UndefinedVariable
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
        self._updateCurveGraph()

    def _onCurveSubModeHelp(self, event):
        text = "Selects how we edit the curve.\n"
        text += "\n"
        text += "Linear:\tAdd points to define curve.\n"
        text += "Curve:\tAdd points to define bendt curve.\n"
        text += "Array:\tDraw the curve pixel by pixel.\n"
        dlg = wx.MessageDialog(self._mainCurveGuiPlane, text, 'Curve sub mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onCurveSubModeChosen(self, event):
        updateChoices(self._curveSubModeField, self._curveConfig.getSubChoices, self._curveSubModeField.GetValue(), "Linear")
        self._curveConfig.changeSubModeString(self._curveSubModeField.GetValue())
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

    def _onCurveSingleClick(self, event):
        self._curveConfig.drawingDone()
        self._updateCurveGraph()

    def _onCurveDoubleClick(self, event):
        self._curveConfig.addPoint(self._curveGraphicsDisplay.getLastPos(), self.getSubId())
        self._updateCurveGraph()

    def _onMouseMove(self, event):
        if(event.mousePressed == True):
            self._curveConfig.drawPoint(event.mousePosition, self.getSubId())
            self._updateCurveGraph()
        else:
            self._curveConfig.drawingDone()

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
        self._updateCurveGraph()
        self._checkForUpdates()

