'''
Created on 6. feb. 2012

@author: pcn
'''
from midi.MidiTiming import MidiTiming
from configuration.EffectSettings import EffectTemplates, FadeTemplates
import wx
from midi.MidiController import getControllerId
from video.Effects import EffectTypes, getEffectId, getEffectName, FlipModes,\
    ZoomModes, DistortionModes, EdgeModes, EdgeColourModes, DesaturateModes,\
    ColorizeModes

class GlobalConfig(object):
    def __init__(self, configParent, mainConfig):
        self._mainConfig = mainConfig
        self._configurationTree = configParent.addChildUnique("Global")
        self._configurationTree.addIntParameter("ResolutionX", 800)
        self._configurationTree.addIntParameter("ResolutionY", 600)
        self._internalResolutionX =  self._configurationTree.getValueFromPath("Global.ResolutionX")
        self._internalResolutionY =  self._configurationTree.getValueFromPath("Global.ResolutionY")

        self._midiTiming = MidiTiming()

        self._effectsConfiguration = EffectTemplates(self._configurationTree, self._midiTiming, self._internalResolutionX, self._internalResolutionY)
        self._effectsGui = EffectsGui(self._mainConfig)
        self._mediaFadeConfiguration = FadeTemplates(self._configurationTree, self._midiTiming)

    def _getConfiguration(self):
        self._effectsConfiguration._getConfiguration()
        self._mediaFadeConfiguration._getConfiguration()

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print "GlobalConfig config is updated..."
            self._getConfiguration()
            self._configurationTree.resetConfigurationUpdated()
        else:
            print "DEBUG: GlobalConfig.checkAndUpdateFromConfiguration NOT updated..."

    def getEffectChoices(self):
        return self._effectsConfiguration.getChoices()

    def getFadeChoices(self):
        return self._mediaFadeConfiguration.getChoices()

    def setupEffectsGui(self, plane, sizer, parentSizer, parentClass):
        self._effectsGui.setupEffectsGui(plane, sizer, parentSizer, parentClass)

    def setupEffectsSlidersGui(self, plane, sizer, parentSizer, parentClass):
        self._effectsGui.setupEffectsSlidersGui(plane, sizer, parentSizer, parentClass)

    def updateEffectsGui(self, configName, midiNote):
        template = self._effectsConfiguration.getTemplate(configName)
        if(template != None):
            self._effectsGui.updateGui(template, midiNote)

class EffectsGui(object):
    def __init__(self, mainConfing):
        self._mainConfig = mainConfing

    def setupEffectsGui(self, plane, sizer, parentSizer, parentClass):
        self._mainEffectsGuiSizer = sizer
        self._parentSizer = parentSizer
        self._hideEffectsCallback = parentClass.hideEffectsGui
        self._showSlidersCallback = parentClass.showSlidersGui

        templateNameSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText1 = wx.StaticText(plane, wx.ID_ANY, "Name:") #@UndefinedVariable
        self._templateNameField = wx.TextCtrl(plane, wx.ID_ANY, "MediaDefault1", size=(200, -1)) #@UndefinedVariable
        self._templateNameField.SetInsertionPoint(0)
        templateNameSizer.Add(tmpText1, 1, wx.ALL, 5) #@UndefinedVariable
        templateNameSizer.Add(self._templateNameField, 2, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(templateNameSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        effectNameSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText2 = wx.StaticText(plane, wx.ID_ANY, "Effect:") #@UndefinedVariable
        self._effectChoices = EffectTypes()
        self._effectNameField = wx.ComboBox(plane, wx.ID_ANY, size=(200, -1), choices=["None"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateChoices(self._effectNameField, self._effectChoices.getChoices, "None", "None")
        effectNameSizer.Add(tmpText2, 1, wx.ALL, 5) #@UndefinedVariable
        effectNameSizer.Add(self._effectNameField, 2, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(effectNameSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        plane.Bind(wx.EVT_COMBOBOX, self._onEffectChosen, id=self._effectNameField.GetId()) #@UndefinedVariable

        self._ammountSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._amountLabel = wx.StaticText(plane, wx.ID_ANY, "Amount:") #@UndefinedVariable
        self._ammountField = wx.TextCtrl(plane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._ammountField.SetInsertionPoint(0)
        self._ammountSizer.Add(self._amountLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._ammountSizer.Add(self._ammountField, 2, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._ammountSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._arg1Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg1Label = wx.StaticText(plane, wx.ID_ANY, "Argument 1:") #@UndefinedVariable
        self._arg1Field = wx.TextCtrl(plane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._arg1Field.SetInsertionPoint(0)
        self._arg1Sizer.Add(self._arg1Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg1Sizer.Add(self._arg1Field, 2, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._arg1Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._arg2Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg2Label = wx.StaticText(plane, wx.ID_ANY, "Argument 2:") #@UndefinedVariable
        self._arg2Field = wx.TextCtrl(plane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._arg2Field.SetInsertionPoint(0)
        self._arg2Sizer.Add(self._arg2Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg2Sizer.Add(self._arg2Field, 2, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._arg2Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._arg3Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg3Label = wx.StaticText(plane, wx.ID_ANY, "Argument 3:") #@UndefinedVariable
        self._arg3Field = wx.TextCtrl(plane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._arg3Field.SetInsertionPoint(0)
        self._arg3Sizer.Add(self._arg3Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg3Sizer.Add(self._arg3Field, 2, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._arg3Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._arg4Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg4Label = wx.StaticText(plane, wx.ID_ANY, "Argument 4:") #@UndefinedVariable
        self._arg4Field = wx.TextCtrl(plane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._arg4Field.SetInsertionPoint(0)
        self._arg4Sizer.Add(self._arg4Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg4Sizer.Add(self._arg4Field, 2, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._arg4Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = wx.Button(plane, wx.ID_ANY, 'Close') #@UndefinedVariable
        plane.Bind(wx.EVT_BUTTON, self._onCloseButton, id=closeButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 1, wx.ALL, 5) #@UndefinedVariable
        saveButton = wx.Button(plane, wx.ID_ANY, 'Save') #@UndefinedVariable
        plane.Bind(wx.EVT_BUTTON, self._onSaveButton, id=saveButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(saveButton, 1, wx.ALL, 5) #@UndefinedVariable
        slidersButton = wx.Button(plane, wx.ID_ANY, 'Sliders') #@UndefinedVariable
        plane.Bind(wx.EVT_BUTTON, self._onSlidersButton, id=slidersButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(slidersButton, 1, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._flipModes = FlipModes()
        self._zoomModes = ZoomModes()
        self._distortionModes = DistortionModes()
        self._edgeModes = EdgeModes()
        self._edgeColourModes = EdgeColourModes()
        self._desaturateModes = DesaturateModes()
        self._colorizeModes = ColorizeModes()

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

    def setupEffectsSlidersGui(self, plane, sizer, parentSizer, parentClass):
        self._mainSliderSizer = sizer
        self._parentSizer = parentSizer
        self._hideSlidersCallback = parentClass.hideSlidersGui

        self._ammountSliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._amountSliderLabel = wx.StaticText(plane, wx.ID_ANY, "Amount:") #@UndefinedVariable
        self._ammountSlider = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=127, size=(200, -1)) #@UndefinedVariable
        self._amountValueLabel = wx.StaticText(plane, wx.ID_ANY, "0.0", size=(60,-1)) #@UndefinedVariable
        self._ammountSliderSizer.Add(self._amountSliderLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._ammountSliderSizer.Add(self._ammountSlider, 2, wx.ALL, 5) #@UndefinedVariable
        self._ammountSliderSizer.Add(self._amountValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainSliderSizer.Add(self._ammountSliderSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._amountSliderId = self._ammountSlider.GetId()

        self._arg1SliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg1SliderLabel = wx.StaticText(plane, wx.ID_ANY, "Argument 1:") #@UndefinedVariable
        self._arg1Slider = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=127, size=(200, -1)) #@UndefinedVariable
        self._arg1ValueLabel = wx.StaticText(plane, wx.ID_ANY, "0.0", size=(60,-1)) #@UndefinedVariable
        self._arg1SliderSizer.Add(self._arg1SliderLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg1SliderSizer.Add(self._arg1Slider, 2, wx.ALL, 5) #@UndefinedVariable
        self._arg1SliderSizer.Add(self._arg1ValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainSliderSizer.Add(self._arg1SliderSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._arg1SliderId = self._arg1Slider.GetId()

        self._arg2SliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg2SliderLabel = wx.StaticText(plane, wx.ID_ANY, "Argument 2:") #@UndefinedVariable
        self._arg2Slider = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=127, size=(200, -1)) #@UndefinedVariable
        self._arg2ValueLabel = wx.StaticText(plane, wx.ID_ANY, "0.0", size=(60,-1)) #@UndefinedVariable
        self._arg2SliderSizer.Add(self._arg2SliderLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg2SliderSizer.Add(self._arg2Slider, 2, wx.ALL, 5) #@UndefinedVariable
        self._arg2SliderSizer.Add(self._arg2ValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainSliderSizer.Add(self._arg2SliderSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._arg2SliderId = self._arg2Slider.GetId()

        self._arg3SliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg3SliderLabel = wx.StaticText(plane, wx.ID_ANY, "Argument 3:") #@UndefinedVariable
        self._arg3Slider = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=127, size=(200, -1)) #@UndefinedVariable
        self._arg3ValueLabel = wx.StaticText(plane, wx.ID_ANY, "0.0", size=(60,-1)) #@UndefinedVariable
        self._arg3SliderSizer.Add(self._arg3SliderLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg3SliderSizer.Add(self._arg3Slider, 2, wx.ALL, 5) #@UndefinedVariable
        self._arg3SliderSizer.Add(self._arg3ValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainSliderSizer.Add(self._arg3SliderSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._arg3SliderId = self._arg3Slider.GetId()

        self._arg4SliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg4SliderLabel = wx.StaticText(plane, wx.ID_ANY, "Argument 4:") #@UndefinedVariable
        self._arg4Slider = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=127, size=(200, -1)) #@UndefinedVariable
        self._arg4ValueLabel = wx.StaticText(plane, wx.ID_ANY, "0.0", size=(60,-1)) #@UndefinedVariable
        self._arg4SliderSizer.Add(self._arg4SliderLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg4SliderSizer.Add(self._arg4Slider, 2, wx.ALL, 5) #@UndefinedVariable
        self._arg4SliderSizer.Add(self._arg4ValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainSliderSizer.Add(self._arg4SliderSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._arg4SliderId = self._arg4Slider.GetId()

        self._sliderButtonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = wx.Button(plane, wx.ID_ANY, 'Close') #@UndefinedVariable
        plane.Bind(wx.EVT_BUTTON, self._onSliderCloseButton, id=closeButton.GetId()) #@UndefinedVariable
        self._sliderButtonsSizer.Add(closeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainSliderSizer.Add(self._sliderButtonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        plane.Bind(wx.EVT_SLIDER, self._onSlide) #@UndefinedVariable

    def _onSliderCloseButton(self, event):
        self._hideSlidersCallback()

    def _onCloseButton(self, event):
        self._hideEffectsCallback()
        self._hideSlidersCallback()

    def _onSaveButton(self, event):
        print "Save"

    def _onSlidersButton(self, event):
        self._showSlidersCallback()
        self._parentSizer.Layout()

    def _onSlide(self, event):
        sliderId = event.GetEventObject().GetId()
        midiChannel = self._mainConfig.getSelectedMidiChannel()
        if(sliderId == self._amountSliderId):
#            print "Ammount: " + str(self._ammountSlider.GetValue())
            if((midiChannel > -1) and (midiChannel < 16)):
                self.sendMidi(midiChannel, self._ammountField.GetValue(), self._ammountSlider.GetValue())
        elif(sliderId == self._arg1SliderId):
#            print "Arg 1: " + str(self._arg1Slider.GetValue())
            if((midiChannel > -1) and (midiChannel < 16)):
                self.sendMidi(midiChannel, self._arg1Field.GetValue(), self._arg1Slider.GetValue())
        elif(sliderId == self._arg2SliderId):
#            print "Arg 2: " + str(self._arg2Slider.GetValue())
            if((midiChannel > -1) and (midiChannel < 16)):
                self.sendMidi(midiChannel, self._arg2Field.GetValue(), self._arg2Slider.GetValue())
        elif(sliderId == self._arg3SliderId):
#            print "Arg 3: " + str(self._arg3Slider.GetValue())
            if((midiChannel > -1) and (midiChannel < 16)):
                self.sendMidi(midiChannel, self._arg3Field.GetValue(), self._arg3Slider.GetValue())
        elif(sliderId == self._arg4SliderId):
#            print "Arg 4: " + str(self._arg4Slider.GetValue())
            if((midiChannel > -1) and (midiChannel < 16)):
                self.sendMidi(midiChannel, self._arg4Field.GetValue(), self._arg4Slider.GetValue())
        self._updateValueLabels()

    def _onEffectChosen(self, event):
        selectedEffectId = self._effectNameField.GetSelection()
        self._setEffect(getEffectName(selectedEffectId-1))

    def sendMidi(self, channel, controllerDescription, value):
        midiSender = self._mainConfig.getMidiSender()
        if(controllerDescription.startswith("MidiChannel.")):
            descriptionSplit = controllerDescription.split('.', 6)
            if(len(descriptionSplit) > 1):
                if(descriptionSplit[1] == "Controller"):
                    if(len(descriptionSplit) > 2):
                        controllerId = getControllerId(descriptionSplit[2])
#                        print "Sending controller: " + descriptionSplit[2] + " -> " + str(controllerId)
                        midiSender.sendMidiController(channel, controllerId, value)
                elif(descriptionSplit[1] == "PitchBend"):
                    midiSender.sendPitchbend(channel, value)
                elif(descriptionSplit[1] == "Aftertouch"):
                    midiSender.sendAftertouch(channel, value)
        if(controllerDescription.startswith("MidiNote.")):
            descriptionSplit = controllerDescription.split('.', 6)
            if(len(descriptionSplit) > 1):
                if((descriptionSplit[1] == "NotePreasure") or (descriptionSplit[1] == "Preasure")):
                    midiSender.sendPolyPreasure(self._mainConfig.getSelectedMidiChannel(), self._midiNote, value)

    def _setLabels(self, amountLabel, arg1Label, arg2Label, arg3Label, arg4Label):
        self._amountLabel.SetLabel(amountLabel)
        self._amountSliderLabel.SetLabel(amountLabel)
        if(arg1Label != None):
            self._mainEffectsGuiSizer.Show(self._arg1Sizer)
            self._mainSliderSizer.Show(self._arg1SliderSizer)
            self._arg1Label.SetLabel(arg1Label)
            self._arg1SliderLabel.SetLabel(arg1Label)
        else:
            self._mainEffectsGuiSizer.Hide(self._arg1Sizer)
            self._mainSliderSizer.Hide(self._arg1SliderSizer)
        if(arg2Label != None):
            self._mainEffectsGuiSizer.Show(self._arg2Sizer)
            self._mainSliderSizer.Show(self._arg2SliderSizer)
            self._arg2Label.SetLabel(arg2Label)
            self._arg2SliderLabel.SetLabel(arg2Label)
        else:
            self._mainEffectsGuiSizer.Hide(self._arg2Sizer)
            self._mainSliderSizer.Hide(self._arg2SliderSizer)
        if(arg3Label != None):
            self._mainEffectsGuiSizer.Show(self._arg3Sizer)
            self._mainSliderSizer.Show(self._arg3SliderSizer)
            self._arg3Label.SetLabel(arg3Label)
            self._arg3SliderLabel.SetLabel(arg3Label)
        else:
            self._mainEffectsGuiSizer.Hide(self._arg3Sizer)
            self._mainSliderSizer.Hide(self._arg3SliderSizer)
        if(arg4Label != None):
            self._mainEffectsGuiSizer.Show(self._arg4Sizer)
            self._mainSliderSizer.Show(self._arg4SliderSizer)
            self._arg4Label.SetLabel(arg4Label)
            self._arg4SliderLabel.SetLabel(arg4Label)
        else:
            self._mainEffectsGuiSizer.Hide(self._arg4Sizer)
            self._mainSliderSizer.Hide(self._arg4SliderSizer)
        self._parentSizer.Layout()

    def _updateValueLabels(self):
        if(self._ammountValueLabels == None):
            valueString = "%.2f" % (float(self._ammountSlider.GetValue()) / 127.0)
            self._amountValueLabel.SetLabel(valueString)
        elif(type(self._ammountValueLabels) is list):
            index = int((float(self._ammountSlider.GetValue()) / 128.0) * len(self._ammountValueLabels))
            self._amountValueLabel.SetLabel(self._ammountValueLabels[index])
        else:
            print str(type(self._ammountValueLabels))
        if(self._arg1ValueLabels == None):
            valueString = "%.2f" % (float(self._arg1Slider.GetValue()) / 127.0)
            self._arg1ValueLabel.SetLabel(valueString)
        elif(type(self._arg1ValueLabels) is list):
            index = int((float(self._arg1Slider.GetValue()) / 128.0) * len(self._arg1ValueLabels))
            self._arg1ValueLabel.SetLabel(self._arg1ValueLabels[index])
        else:
            print str(type(self._arg1ValueLabels))
        if(self._arg2ValueLabels == None):
            valueString = "%.2f" % (float(self._arg2Slider.GetValue()) / 127.0)
            self._arg2ValueLabel.SetLabel(valueString)
        elif(type(self._arg2ValueLabels) is list):
            index = int((float(self._arg2Slider.GetValue()) / 128.0) * len(self._arg2ValueLabels))
            self._arg2ValueLabel.SetLabel(self._arg2ValueLabels[index])
        else:
            print str(type(self._arg2ValueLabels))
        if(self._arg3ValueLabels == None):
            valueString = "%.2f" % (float(self._arg3Slider.GetValue()) / 127.0)
            self._arg3ValueLabel.SetLabel(valueString)
        elif(type(self._arg3ValueLabels) is list):
            index = int((float(self._arg3Slider.GetValue()) / 128.0) * len(self._arg3ValueLabels))
            self._arg3ValueLabel.SetLabel(self._arg3ValueLabels[index])
        else:
            print str(type(self._arg3ValueLabels))
        if(self._arg4ValueLabels == None):
            valueString = "%.2f" % (float(self._arg4Slider.GetValue()) / 127.0)
            self._arg4ValueLabel.SetLabel(valueString)
        elif(type(self._arg4ValueLabels) is list):
            index = int((float(self._arg4Slider.GetValue()) / 128.0) * len(self._arg4ValueLabels))
            self._arg4ValueLabel.SetLabel(self._arg4ValueLabels[index])
        else:
            print str(type(self._arg4ValueLabels))

    def _setupValueLabels(self, amount=None, arg1=None, arg2=None, arg3=None, arg4=None):
        print "DEBUG: _setupValueLabels " + str(amount) + " - " + str(arg1) + " - " + str(arg2) + " - " + str(arg3) + " - " + str(arg4)
        self._ammountValueLabels = amount
        self._arg1ValueLabels = arg1
        self._arg2ValueLabels = arg2
        self._arg3ValueLabels = arg3
        self._arg4ValueLabels = arg4

    def _updateLabels(self):            
        if(self._chosenEffectId == EffectTypes.Zoom):
            self._setLabels("Amount:", "XY ratio", "X position", "Y position", "Zoom mode")
            self._setupValueLabels(None, None, None, None, self._zoomModes.getChoices())
        elif(self._chosenEffectId == EffectTypes.Flip):
            self._setLabels("Flip mode:", None, None, None, None)
            self._setupValueLabels(self._flipModes.getChoices(), None, None, None, None)
        elif(self._chosenEffectId == EffectTypes.Blur):
            self._setLabels("Amount:", None, None, None, None)
            self._setupValueLabels(None, None, None, None, None)
        elif(self._chosenEffectId == EffectTypes.BlurContrast):
            self._setLabels("Amount:", None, None, None, None)
            self._setupValueLabels(None, None, None, None, None)
        elif(self._chosenEffectId == EffectTypes.Distortion):
            self._setLabels("Distortion amount:", "Distortion mode", None, None, None)
            self._setupValueLabels(None, self._distortionModes.getChoices(), None, None, None)
        elif(self._chosenEffectId == EffectTypes.Edge):
            self._setLabels("Amount:", "Edge mode", "Value/Hue/Saturation", "Line color:", "Line saturation")
            self._setupValueLabels(None, self._edgeModes.getChoices(), self._edgeColourModes.getChoices(), None, None)
        elif(self._chosenEffectId == EffectTypes.Desaturate):
            self._setLabels("Colour:", "Range", "Mode", None, None)
            self._setupValueLabels(None, None, self._desaturateModes.getChoices(), None, None)
        elif(self._chosenEffectId == EffectTypes.Contrast):
            self._setLabels("Contrast:", "Brightness", None, None, None)
            self._setupValueLabels(None, None, None, None, None)
        elif(self._chosenEffectId == EffectTypes.HueSaturation):
            self._setLabels("Color rotate:", "Saturation", "Brightness", None, None)
            self._setupValueLabels(None, None, None, None, None)
        elif(self._chosenEffectId == EffectTypes.Colorize):
            self._setLabels("Amount:", "Red", "Green", "Blue", "Mode")
            self._setupValueLabels(None, None, None, None, self._golorizeModes.getChoices())
        elif(self._chosenEffectId == EffectTypes.Invert):
            self._setLabels("Amount:", None, None, None, None)
            self._setupValueLabels(None, None, None, None, None)
        elif(self._chosenEffectId == EffectTypes.Threshold):
            self._setLabels("Threshold:", None, None, None, None)
            self._setupValueLabels(None, None, None, None, None)
        else:
            self._setLabels("Amount:", "Argument 1:", "Argument 2:", "Argument 3:", "Argument 4:")
            self._setupValueLabels(None, None, None, None, None)
        self._updateValueLabels()

    def _setEffect(self, value):
        if(value == None):
            self._chosenEffectId = -1
            self._chosenEffect = "None"
        else:
            self._chosenEffectId = getEffectId(value)
            self._chosenEffect = getEffectName(self._chosenEffectId)
        self._updateChoices(self._effectNameField, self._effectChoices.getChoices, self._chosenEffect, "None")
        self._updateLabels()
        
    def updateGui(self, effectTemplate, midiNote):
        self._midiNote = midiNote
        config = effectTemplate.getConfigHolder()
        self._templateNameField.SetValue(config.getValue("Name"))
        self._setEffect(config.getValue("Effect"))
        self._ammountField.SetValue(config.getValue("Amount"))
        self._arg1Field.SetValue(config.getValue("Arg1"))
        self._arg2Field.SetValue(config.getValue("Arg2"))
        self._arg3Field.SetValue(config.getValue("Arg3"))
        self._arg4Field.SetValue(config.getValue("Arg4"))

