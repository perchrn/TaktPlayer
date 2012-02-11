'''
Created on 6. feb. 2012

@author: pcn
'''
from midi.MidiTiming import MidiTiming
from configuration.EffectSettings import EffectTemplates, FadeTemplates
import wx
from video.Effects import EffectTypes, getEffectId, getEffectName, FlipModes,\
    ZoomModes, DistortionModes, EdgeModes, EdgeColourModes, DesaturateModes,\
    ColorizeModes
from video.media.MediaFile import FadeMode
from midi.MidiModulation import ModulationSources, AdsrShapes, LfoShapes,\
    MidiModulation
from midi.MidiStateHolder import MidiChannelModulationSources,\
    NoteModulationSources
from midi.MidiController import MidiControllers

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
        self._fadeConfiguration = FadeTemplates(self._configurationTree, self._midiTiming)
        self._fadeGui = FadeGui(self._mainConfig)
        self._modulationGui = ModulationGui(self._mainConfig, self._midiTiming)

    def _getConfiguration(self):
        self._effectsConfiguration._getConfiguration()
        self._fadeConfiguration._getConfiguration()

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print "GlobalConfig config is updated..."
            self._getConfiguration()
            self._configurationTree.resetConfigurationUpdated()

    def getEffectChoices(self):
        return self._effectsConfiguration.getChoices()

    def getFadeChoices(self):
        return self._fadeConfiguration.getChoices()

    def setupEffectsGui(self, plane, sizer, parentSizer, parentClass):
        self._effectsGui.setupEffectsGui(plane, sizer, parentSizer, parentClass)

    def setupFadeGui(self, plane, sizer, parentSizer, parentClass):
        self._fadeGui.setupFadeGui(plane, sizer, parentSizer, parentClass)

    def setupModulationGui(self, plane, sizer, parentSizer, parentClass):
        self._modulationGui.setupModulationGui(plane, sizer, parentSizer, parentClass)

    def setupEffectsSlidersGui(self, plane, sizer, parentSizer, parentClass):
        self._effectsGui.setupEffectsSlidersGui(plane, sizer, parentSizer, parentClass)

    def updateEffectsGui(self, configName, midiNote):
        template = self._effectsConfiguration.getTemplate(configName)
        if(template != None):
            self._effectsGui.updateGui(template, midiNote)

    def updateModulationGui(self, modulationString, widget):
        self._modulationGui.updateGui(modulationString, widget)

    def updateFadeGui(self, configName):
        template = self._fadeConfiguration.getTemplate(configName)
        if(template != None):
            self._fadeGui.updateGui(template)

class EffectsGui(object):
    def __init__(self, mainConfing):
        self._mainConfig = mainConfing

    def setupEffectsGui(self, plane, sizer, parentSizer, parentClass):
        self._mainEffectsGuiSizer = sizer
        self._parentSizer = parentSizer
        self._hideEffectsCallback = parentClass.hideEffectsGui
        self._showSlidersCallback = parentClass.showSlidersGui
        self._showModulationCallback = parentClass.showModulationGui
        self._hideModulationCallback = parentClass.hideModulationGui

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
        ammountButton = wx.Button(plane, wx.ID_ANY, 'Edit') #@UndefinedVariable
        plane.Bind(wx.EVT_BUTTON, self._onAmmountEdit, id=ammountButton.GetId()) #@UndefinedVariable
        self._ammountSizer.Add(self._amountLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._ammountSizer.Add(self._ammountField, 2, wx.ALL, 5) #@UndefinedVariable
        self._ammountSizer.Add(ammountButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._ammountSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._arg1Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg1Label = wx.StaticText(plane, wx.ID_ANY, "Argument 1:") #@UndefinedVariable
        self._arg1Field = wx.TextCtrl(plane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._arg1Field.SetInsertionPoint(0)
        arg1Button = wx.Button(plane, wx.ID_ANY, 'Edit') #@UndefinedVariable
        plane.Bind(wx.EVT_BUTTON, self._onArg1Edit, id=arg1Button.GetId()) #@UndefinedVariable
        self._arg1Sizer.Add(self._arg1Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg1Sizer.Add(self._arg1Field, 2, wx.ALL, 5) #@UndefinedVariable
        self._arg1Sizer.Add(arg1Button, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._arg1Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._arg2Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg2Label = wx.StaticText(plane, wx.ID_ANY, "Argument 2:") #@UndefinedVariable
        self._arg2Field = wx.TextCtrl(plane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._arg2Field.SetInsertionPoint(0)
        arg2Button = wx.Button(plane, wx.ID_ANY, 'Edit') #@UndefinedVariable
        plane.Bind(wx.EVT_BUTTON, self._onArg2Edit, id=arg2Button.GetId()) #@UndefinedVariable
        self._arg2Sizer.Add(self._arg2Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg2Sizer.Add(self._arg2Field, 2, wx.ALL, 5) #@UndefinedVariable
        self._arg2Sizer.Add(arg2Button, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._arg2Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._arg3Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg3Label = wx.StaticText(plane, wx.ID_ANY, "Argument 3:") #@UndefinedVariable
        self._arg3Field = wx.TextCtrl(plane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._arg3Field.SetInsertionPoint(0)
        arg3Button = wx.Button(plane, wx.ID_ANY, 'Edit') #@UndefinedVariable
        plane.Bind(wx.EVT_BUTTON, self._onArg3Edit, id=arg3Button.GetId()) #@UndefinedVariable
        self._arg3Sizer.Add(self._arg3Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg3Sizer.Add(self._arg3Field, 2, wx.ALL, 5) #@UndefinedVariable
        self._arg3Sizer.Add(arg3Button, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._arg3Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._arg4Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg4Label = wx.StaticText(plane, wx.ID_ANY, "Argument 4:") #@UndefinedVariable
        self._arg4Field = wx.TextCtrl(plane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._arg4Field.SetInsertionPoint(0)
        arg4Button = wx.Button(plane, wx.ID_ANY, 'Edit') #@UndefinedVariable
        plane.Bind(wx.EVT_BUTTON, self._onArg4Edit, id=arg4Button.GetId()) #@UndefinedVariable
        self._arg4Sizer.Add(self._arg4Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg4Sizer.Add(self._arg4Field, 2, wx.ALL, 5) #@UndefinedVariable
        self._arg4Sizer.Add(arg4Button, 0, wx.ALL, 5) #@UndefinedVariable
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
        self._midiControllers = MidiControllers()

    def _onAmmountEdit(self, event):
        self._showModulationCallback()
        self._parentSizer.Layout()
        self._mainConfig.updateModulationGui(self._ammountField.GetValue(), self._ammountField)

    def _onArg1Edit(self, event):
        self._showModulationCallback()
        self._parentSizer.Layout()
        self._mainConfig.updateModulationGui(self._arg1Field.GetValue(), self._arg1Field)

    def _onArg2Edit(self, event):
        self._showModulationCallback()
        self._parentSizer.Layout()
        self._mainConfig.updateModulationGui(self._arg2Field.GetValue(), self._arg2Field)

    def _onArg3Edit(self, event):
        self._showModulationCallback()
        self._parentSizer.Layout()
        self._mainConfig.updateModulationGui(self._arg3Field.GetValue(), self._arg3Field)

    def _onArg4Edit(self, event):
        self._showModulationCallback()
        self._parentSizer.Layout()
        self._mainConfig.updateModulationGui(self._arg4Field.GetValue(), self._arg4Field)

    def _onCloseButton(self, event):
        self._hideEffectsCallback()
        self._hideModulationCallback()
        self._hideSlidersCallback()

    def _onSaveButton(self, event):
        print "Save " * 20
        print "Name: " + self._templateNameField.GetValue()
        print "Effect: " + self._effectNameField.GetValue()
        print "Amount: " + self._ammountField.GetValue()
        print "Arg1: " + self._arg1Field.GetValue()
        print "Arg2: " + self._arg2Field.GetValue()
        print "Arg3: " + self._arg3Field.GetValue()
        print "Arg4: " + self._arg4Field.GetValue()
        print "Save " * 20

    def _onSlidersButton(self, event):
        self._showSlidersCallback()
        self._parentSizer.Layout()

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
                        controllerId = self._midiControllers.getId(descriptionSplit[2])
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

class FadeGui(object):
    def __init__(self, mainConfing):
        self._mainConfig = mainConfing

    def setupFadeGui(self, plane, sizer, parentSizer, parentClass):
        self._mainFadeGuiPlane = plane
        self._mainFadeGuiSizer = sizer
        self._parentSizer = parentSizer
        self._hideFadeCallback = parentClass.hideFadeGui
        self._showModulationCallback = parentClass.showModulationGui
        self._hideModulationCallback = parentClass.hideModulationGui

        templateNameSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText1 = wx.StaticText(self._mainFadeGuiPlane, wx.ID_ANY, "Name:") #@UndefinedVariable
        self._templateNameField = wx.TextCtrl(self._mainFadeGuiPlane, wx.ID_ANY, "Default", size=(200, -1)) #@UndefinedVariable
        self._templateNameField.SetInsertionPoint(0)
        templateNameSizer.Add(tmpText1, 1, wx.ALL, 5) #@UndefinedVariable
        templateNameSizer.Add(self._templateNameField, 2, wx.ALL, 5) #@UndefinedVariable
        self._mainFadeGuiSizer.Add(templateNameSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        fadeModeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText2 = wx.StaticText(self._mainFadeGuiPlane, wx.ID_ANY, "Mode:") #@UndefinedVariable
        self._fadeModes = FadeMode()
        self._fadeModesField = wx.ComboBox(self._mainFadeGuiPlane, wx.ID_ANY, size=(200, -1), choices=["Black"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateChoices(self._fadeModesField, self._fadeModes.getChoices, "Black", "Black")
        fadeModeButton = wx.Button(self._mainFadeGuiPlane, wx.ID_ANY, 'Help') #@UndefinedVariable
        self._mainFadeGuiPlane.Bind(wx.EVT_BUTTON, self._onFadeModeHelp, id=fadeModeButton.GetId()) #@UndefinedVariable
        fadeModeSizer.Add(tmpText2, 1, wx.ALL, 5) #@UndefinedVariable
        fadeModeSizer.Add(self._fadeModesField, 2, wx.ALL, 5) #@UndefinedVariable
        fadeModeSizer.Add(fadeModeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainFadeGuiSizer.Add(fadeModeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._mainFadeGuiPlane.Bind(wx.EVT_COMBOBOX, self._onFadeModeChosen, id=self._fadeModesField.GetId()) #@UndefinedVariable

        fadeModulationSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText3 = wx.StaticText(self._mainFadeGuiPlane, wx.ID_ANY, "Fade modulation:") #@UndefinedVariable
        self._fadeModulationField = wx.TextCtrl(self._mainFadeGuiPlane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._fadeModulationField.SetInsertionPoint(0)
        fadeModulationButton = wx.Button(self._mainFadeGuiPlane, wx.ID_ANY, 'Edit') #@UndefinedVariable
        self._mainFadeGuiPlane.Bind(wx.EVT_BUTTON, self._onFadeModulationEdit, id=fadeModulationButton.GetId()) #@UndefinedVariable
        fadeModulationSizer.Add(tmpText3, 1, wx.ALL, 5) #@UndefinedVariable
        fadeModulationSizer.Add(self._fadeModulationField, 2, wx.ALL, 5) #@UndefinedVariable
        fadeModulationSizer.Add(fadeModulationButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainFadeGuiSizer.Add(fadeModulationSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        levelModulationSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText3 = wx.StaticText(self._mainFadeGuiPlane, wx.ID_ANY, "Level modulation:") #@UndefinedVariable
        self._levelModulationField = wx.TextCtrl(self._mainFadeGuiPlane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._levelModulationField.SetInsertionPoint(0)
        levelModulationButton = wx.Button(self._mainFadeGuiPlane, wx.ID_ANY, 'Edit') #@UndefinedVariable
        self._mainFadeGuiPlane.Bind(wx.EVT_BUTTON, self._onLevelModulationEdit, id=levelModulationButton.GetId()) #@UndefinedVariable
        levelModulationSizer.Add(tmpText3, 1, wx.ALL, 5) #@UndefinedVariable
        levelModulationSizer.Add(self._levelModulationField, 2, wx.ALL, 5) #@UndefinedVariable
        levelModulationSizer.Add(levelModulationButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainFadeGuiSizer.Add(levelModulationSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable


        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = wx.Button(self._mainFadeGuiPlane, wx.ID_ANY, 'Close') #@UndefinedVariable
        self._mainFadeGuiPlane.Bind(wx.EVT_BUTTON, self._onCloseButton, id=closeButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 1, wx.ALL, 5) #@UndefinedVariable
        saveButton = wx.Button(self._mainFadeGuiPlane, wx.ID_ANY, 'Save') #@UndefinedVariable
        self._mainFadeGuiPlane.Bind(wx.EVT_BUTTON, self._onSaveButton, id=saveButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(saveButton, 1, wx.ALL, 5) #@UndefinedVariable
        self._mainFadeGuiSizer.Add(self._buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

    def _onFadeModeChosen(self, event):
        pass

    def _onFadeModeHelp(self, event):
        text = """
Decides if this image fades to black or white.
"""
        dlg = wx.MessageDialog(self._mainFadeGuiPlane, text, 'Fade mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onFadeModulationEdit(self, event):
        self._showModulationCallback()
        self._parentSizer.Layout()
        self._mainConfig.updateModulationGui(self._fadeModulationField.GetValue(), self._fadeModulationField)

    def _onLevelModulationEdit(self, event):
        self._showModulationCallback()
        self._parentSizer.Layout()
        self._mainConfig.updateModulationGui(self._levelModulationField.GetValue(), self._levelModulationField)

    def _onCloseButton(self, event):
        self._hideFadeCallback()
        self._hideModulationCallback()
        self._mainConfig.stopModulationGui()

    def _onSaveButton(self, event):
        print "Save " * 20
        print "Name: " + self._templateNameField.GetValue()
        print "Mode: " + self._fadeModesField.GetValue()
        print "Modulation: " + self._fadeModulationField.GetValue()
        print "Level: " + self._levelModulationField.GetValue()
        print "Save " * 20

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

    def updateGui(self, effectTemplate):
        config = effectTemplate.getConfigHolder()
        self._templateNameField.SetValue(config.getValue("Name"))
        self._updateChoices(self._fadeModesField, self._fadeModes.getChoices, config.getValue("Mode"), "Black")
        self._fadeModulationField.SetValue(config.getValue("Modulation"))
        self._levelModulationField.SetValue(config.getValue("Level"))

class ModulationGui(object):
    def __init__(self, mainConfing, midiTiming):
        self._mainConfig = mainConfing
        self._midiTiming = midiTiming
        self._updateWidget = None

    def setupModulationGui(self, plane, sizer, parentSizer, parentClass):
        self._mainModulationGuiPlane = plane
        self._mainModulationGuiSizer = sizer
        self._parentSizer = parentSizer
        self._hideModulationCallback = parentClass.hideModulationGui

        self._midiModulation = MidiModulation(None, self._midiTiming)

        modulationSorcesSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText1 = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "Modulation:") #@UndefinedVariable
        self._modulationSorces = ModulationSources()
        self._modulationSorcesField = wx.ComboBox(self._mainModulationGuiPlane, wx.ID_ANY, size=(200, -1), choices=["None"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateChoices(self._modulationSorcesField, self._modulationSorces.getChoices, "None", "None")
        modulationSorcesButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help') #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onModulationModeHelp, id=modulationSorcesButton.GetId()) #@UndefinedVariable
        modulationSorcesSizer.Add(tmpText1, 1, wx.ALL, 5) #@UndefinedVariable
        modulationSorcesSizer.Add(self._modulationSorcesField, 2, wx.ALL, 5) #@UndefinedVariable
        modulationSorcesSizer.Add(modulationSorcesButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(modulationSorcesSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_COMBOBOX, self._onModulationSourceChosen, id=self._modulationSorcesField.GetId()) #@UndefinedVariable

        """MidiChannel"""

        self._midiChannelSourceSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText2 = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "Channel source:") #@UndefinedVariable
        self._midiChannelSource = MidiChannelModulationSources()
        self._midiChannelSourceField = wx.ComboBox(self._mainModulationGuiPlane, wx.ID_ANY, size=(200, -1), choices=["Controller"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateChoices(self._midiChannelSourceField, self._midiChannelSource.getChoices, "Controller", "Controller")
        midiChannelSourceButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help') #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onMidiChannelSourceHelp, id=midiChannelSourceButton.GetId()) #@UndefinedVariable
        self._midiChannelSourceSizer.Add(tmpText2, 1, wx.ALL, 5) #@UndefinedVariable
        self._midiChannelSourceSizer.Add(self._midiChannelSourceField, 2, wx.ALL, 5) #@UndefinedVariable
        self._midiChannelSourceSizer.Add(midiChannelSourceButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._midiChannelSourceSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_COMBOBOX, self._onMidiChannelSourceChosen, id=self._midiChannelSourceField.GetId()) #@UndefinedVariable

        self._midiControllerSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText3 = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "Controller:") #@UndefinedVariable
        self._midiControllers = MidiControllers()
        self._midiControllerField = wx.ComboBox(self._mainModulationGuiPlane, wx.ID_ANY, size=(200, -1), choices=["ModWheel"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateChoices(self._midiControllerField, self._midiControllers.getChoices, "ModWheel", "ModWheel")
        midiControllerButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help') #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onMidiChannelControllerHelp, id=midiControllerButton.GetId()) #@UndefinedVariable
        self._midiControllerSizer.Add(tmpText3, 1, wx.ALL, 5) #@UndefinedVariable
        self._midiControllerSizer.Add(self._midiControllerField, 2, wx.ALL, 5) #@UndefinedVariable
        self._midiControllerSizer.Add(midiControllerButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._midiControllerSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_COMBOBOX, self._onMidiControllerChosen, id=self._midiControllerField.GetId()) #@UndefinedVariable

        self._midiActiveControllerSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText4 = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "Active controllers:") #@UndefinedVariable
        self._midiActiveControllerField = wx.ListBox(self._mainModulationGuiPlane, wx.ID_ANY, size=(200, 100), choices=["None"], style=wx.LB_SINGLE) #@UndefinedVariable
        midiActiveControllerButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help') #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onMidiChannelActiveControllerHelp, id=midiActiveControllerButton.GetId()) #@UndefinedVariable
        self._midiActiveControllerSizer.Add(tmpText4, 1, wx.ALL, 5) #@UndefinedVariable
        self._midiActiveControllerSizer.Add(self._midiActiveControllerField, 2, wx.ALL, 5) #@UndefinedVariable
        self._midiActiveControllerSizer.Add(midiActiveControllerButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._midiActiveControllerSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_LISTBOX, self._onMidiActiveControllerChosen, id=self._midiActiveControllerField.GetId()) #@UndefinedVariable

        """MidiNote"""

        self._midiNoteSourceSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText5 = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "Note source:") #@UndefinedVariable
        self._midiNoteSource = NoteModulationSources()
        self._midiNoteSourceField = wx.ComboBox(self._mainModulationGuiPlane, wx.ID_ANY, size=(200, -1), choices=["Velocity"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateChoices(self._midiNoteSourceField, self._midiNoteSource.getChoices, "Velocity", "Velocity")
        midiNoteSourceButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help') #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onMidiNoteSourceHelp, id=midiNoteSourceButton.GetId()) #@UndefinedVariable
        self._midiNoteSourceSizer.Add(tmpText5, 1, wx.ALL, 5) #@UndefinedVariable
        self._midiNoteSourceSizer.Add(self._midiNoteSourceField, 2, wx.ALL, 5) #@UndefinedVariable
        self._midiNoteSourceSizer.Add(midiNoteSourceButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._midiNoteSourceSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
#        self._mainModulationGuiPlane.Bind(wx.EVT_COMBOBOX, self._onMidiNoteSourceChosen, id=self._midiNoteSourceField.GetId()) #@UndefinedVariable

        """LFO"""

        self._lfoTypeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText6 = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "LFO type:") #@UndefinedVariable
        self._lfoType = LfoShapes()
        self._lfoTypeField = wx.ComboBox(self._mainModulationGuiPlane, wx.ID_ANY, size=(200, -1), choices=["Triangle"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateChoices(self._lfoTypeField, self._lfoType.getChoices, "Triangle", "Triangle")
        lfoTypeButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help') #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onLfoTypeHelp, id=lfoTypeButton.GetId()) #@UndefinedVariable
        self._lfoTypeSizer.Add(tmpText6, 1, wx.ALL, 5) #@UndefinedVariable
        self._lfoTypeSizer.Add(self._lfoTypeField, 2, wx.ALL, 5) #@UndefinedVariable
        self._lfoTypeSizer.Add(lfoTypeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._lfoTypeSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_COMBOBOX, self._onLfoTypeChosen, id=self._lfoTypeField.GetId()) #@UndefinedVariable

        self._lfoLengthSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "LFO length:") #@UndefinedVariable
        self._lfoLengthField = wx.TextCtrl(self._mainModulationGuiPlane, wx.ID_ANY, "4.0", size=(200, -1)) #@UndefinedVariable
        self._lfoLengthField.SetInsertionPoint(0)
        lfoLengthButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help') #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onLfoLengthHelp, id=lfoLengthButton.GetId()) #@UndefinedVariable
        self._lfoLengthSizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        self._lfoLengthSizer.Add(self._lfoLengthField, 2, wx.ALL, 5) #@UndefinedVariable
        self._lfoLengthSizer.Add(lfoLengthButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._lfoLengthSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._lfoPhaseSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText8 = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "LFO ofset:") #@UndefinedVariable
        self._lfoPhaseField = wx.TextCtrl(self._mainModulationGuiPlane, wx.ID_ANY, "0.0", size=(200, -1)) #@UndefinedVariable
        self._lfoPhaseField.SetInsertionPoint(0)
        lfoPhaseButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help') #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onLfoPhaseHelp, id=lfoPhaseButton.GetId()) #@UndefinedVariable
        self._lfoPhaseSizer.Add(tmpText8, 1, wx.ALL, 5) #@UndefinedVariable
        self._lfoPhaseSizer.Add(self._lfoPhaseField, 2, wx.ALL, 5) #@UndefinedVariable
        self._lfoPhaseSizer.Add(lfoPhaseButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._lfoPhaseSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._lfoMinValueSliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._lfoMinValueSliderLabel = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "Min value:") #@UndefinedVariable
        self._lfoMinValueSlider = wx.Slider(self._mainModulationGuiPlane, wx.ID_ANY, minValue=0, maxValue=101, size=(200, -1)) #@UndefinedVariable
        self._lfoMinValueLabel = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "0.0", size=(60,-1)) #@UndefinedVariable
        self._lfoMinValueSliderSizer.Add(self._lfoMinValueSliderLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._lfoMinValueSliderSizer.Add(self._lfoMinValueSlider, 2, wx.ALL, 5) #@UndefinedVariable
        self._lfoMinValueSliderSizer.Add(self._lfoMinValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._lfoMinValueSliderSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._lfoMinValueSliderId = self._lfoMinValueSlider.GetId()
        self._mainModulationGuiPlane.Bind(wx.EVT_SLIDER, self._onSlide) #@UndefinedVariable

        self._lfoMaxValueSliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._lfoMaxValueSliderLabel = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "Max value:") #@UndefinedVariable
        self._lfoMaxValueSlider = wx.Slider(self._mainModulationGuiPlane, wx.ID_ANY, minValue=0, maxValue=101, size=(200, -1)) #@UndefinedVariable
        self._lfoMaxValueLabel = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "0.0", size=(60,-1)) #@UndefinedVariable
        self._lfoMaxValueSliderSizer.Add(self._lfoMaxValueSliderLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._lfoMaxValueSliderSizer.Add(self._lfoMaxValueSlider, 2, wx.ALL, 5) #@UndefinedVariable
        self._lfoMaxValueSliderSizer.Add(self._lfoMaxValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._lfoMaxValueSliderSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._lfoMaxValueSliderId = self._lfoMaxValueSlider.GetId()
        self._mainModulationGuiPlane.Bind(wx.EVT_SLIDER, self._onSlide) #@UndefinedVariable

        """ADSR"""

        self._adsrTypeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText3 = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "ADSR type:") #@UndefinedVariable
        self._adsrType = AdsrShapes()
        self._adsrTypeField = wx.ComboBox(self._mainModulationGuiPlane, wx.ID_ANY, size=(200, -1), choices=["ADSR"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateChoices(self._adsrTypeField, self._adsrType.getChoices, "ADSR", "ADSR")
        adsrTypeButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help') #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onAdsrTypeHelp, id=adsrTypeButton.GetId()) #@UndefinedVariable
        self._adsrTypeSizer.Add(tmpText3, 1, wx.ALL, 5) #@UndefinedVariable
        self._adsrTypeSizer.Add(self._adsrTypeField, 2, wx.ALL, 5) #@UndefinedVariable
        self._adsrTypeSizer.Add(adsrTypeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._adsrTypeSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
#        self._mainModulationGuiPlane.Bind(wx.EVT_COMBOBOX, self._onAdsrTypeChosen, id=self._adsrTypeField.GetId()) #@UndefinedVariable

        """Value"""

        self._valueSliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._valueSliderLabel = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "Value:") #@UndefinedVariable
        self._valueSlider = wx.Slider(self._mainModulationGuiPlane, wx.ID_ANY, minValue=0, maxValue=101, size=(200, -1)) #@UndefinedVariable
        self._valueValueLabel = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "0.0", size=(60,-1)) #@UndefinedVariable
        self._valueSliderSizer.Add(self._valueSliderLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._valueSliderSizer.Add(self._valueSlider, 2, wx.ALL, 5) #@UndefinedVariable
        self._valueSliderSizer.Add(self._valueValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._valueSliderSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._valueSliderId = self._valueSlider.GetId()
        self._mainModulationGuiPlane.Bind(wx.EVT_SLIDER, self._onSlide) #@UndefinedVariable

        """Buttons"""

        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Close') #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onCloseButton, id=closeButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 1, wx.ALL, 5) #@UndefinedVariable
        saveButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Save') #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onSaveButton, id=saveButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(saveButton, 1, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._buttonsSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        self._activeControllersUpdate = wx.Timer(self._mainModulationGuiPlane, -1) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_TIMER, self._onActiveControllersUpdate) #@UndefinedVariable

        self._onModulationSourceChosen(None)

    def closeConfig(self):
        if(self._activeControllersUpdate.IsRunning() == True):
            self._activeControllersUpdate.Stop()

    def _onModulationSourceChosen(self, event):
        choice = self._modulationSorcesField.GetValue()
        if(choice == "MidiChannel"):
            self._mainModulationGuiSizer.Show(self._midiChannelSourceSizer)
            self._parentSizer.Layout()
            self._onMidiChannelSourceChosen(event)
        else:
            self._mainModulationGuiSizer.Hide(self._midiChannelSourceSizer)
            self._mainModulationGuiSizer.Hide(self._midiControllerSizer)
            self._mainModulationGuiSizer.Hide(self._midiActiveControllerSizer)
            self._parentSizer.Layout()
        if(choice == "MidiNote"):
            self._mainModulationGuiSizer.Show(self._midiNoteSourceSizer)
            self._parentSizer.Layout()
        else:
            self._mainModulationGuiSizer.Hide(self._midiNoteSourceSizer)
            self._parentSizer.Layout()
        if(choice == "LFO"):
            self._mainModulationGuiSizer.Show(self._lfoTypeSizer)
            self._mainModulationGuiSizer.Show(self._lfoLengthSizer)
            self._mainModulationGuiSizer.Show(self._lfoPhaseSizer)
            self._mainModulationGuiSizer.Show(self._lfoMinValueSliderSizer)
            self._mainModulationGuiSizer.Show(self._lfoMaxValueSliderSizer)
            self._parentSizer.Layout()
        else:
            self._mainModulationGuiSizer.Hide(self._lfoTypeSizer)
            self._mainModulationGuiSizer.Hide(self._lfoLengthSizer)
            self._mainModulationGuiSizer.Hide(self._lfoPhaseSizer)
            self._mainModulationGuiSizer.Hide(self._lfoMinValueSliderSizer)
            self._mainModulationGuiSizer.Hide(self._lfoMaxValueSliderSizer)
            self._parentSizer.Layout()
        if(choice == "ADSR"):
            self._mainModulationGuiSizer.Show(self._adsrTypeSizer)
            self._parentSizer.Layout()
        else:
            self._mainModulationGuiSizer.Hide(self._adsrTypeSizer)
            self._parentSizer.Layout()
        if(choice == "Value"):
            self._mainModulationGuiSizer.Show(self._valueSliderSizer)
            self._parentSizer.Layout()
        else:
            self._mainModulationGuiSizer.Hide(self._valueSliderSizer)
            self._parentSizer.Layout()

    def _onModulationModeHelp(self, event):
        text = """
Selects modulation type.

MidiChannel:\tChannel wide MIDI controllers.
MidiNote:\t\tVelocity and note pressures.
LFO:\t\tLow Frequency Oscillator
ADSR:\t\tAttach/Release based on note timing.
Value;\t\tStatic value.
"""
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'Modulation mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _getActiveControllersStringList(self):
        idList = self._mainConfig.getLatestMidiControllers()
        returnList = []
        if(idList != None):
            for ctrlId in idList:
                ctrlName = self._midiControllers.getName(int(ctrlId))
                if(ctrlName != None):
                    returnList.append(ctrlName)
        return returnList

    def _onActiveControllersUpdate(self, event):
        selected = self._midiControllerField.GetValue()
        self._updateChoices(self._midiActiveControllerField, self._getActiveControllersStringList, selected, "ModWheel")

    def _onMidiChannelSourceChosen(self, event):
        choice = self._midiChannelSourceField.GetValue()
        if(choice == "Controller"):
            self._mainModulationGuiSizer.Show(self._midiControllerSizer)
            self._mainModulationGuiSizer.Show(self._midiActiveControllerSizer)
            if(self._activeControllersUpdate.IsRunning() == False):
                self._activeControllersUpdate.Start(500)#2 times a second
            self._parentSizer.Layout()
        else:
            self._mainModulationGuiSizer.Hide(self._midiActiveControllerSizer)
            self._mainModulationGuiSizer.Hide(self._midiControllerSizer)
            if(self._activeControllersUpdate.IsRunning() == True):
                self._activeControllersUpdate.Stop()
            self._parentSizer.Layout()

    def _onMidiChannelSourceHelp(self, event):
        text = """
Selects modulation type.
"""
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'Modulation mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onMidiControllerChosen(self, event):
        pass

    def _onMidiActiveControllerChosen(self, event):
        choice = self._midiActiveControllerField.GetStringSelection()
        self._midiControllerField.SetValue(choice)

    def _onMidiChannelControllerHelp(self, event):
        text = """
Selects modulation type.
"""
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'MIDI channel mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onMidiChannelActiveControllerHelp(self, event):
        text = """
Selects modulation type.
"""
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'MIDI channel mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onMidiNoteSourceHelp(self, event):
        text = """
TODO: bla bla bla
"""#TODO: bla bla bla
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'MIDI note help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onLfoTypeHelp(self, event):
        text = """
TODO: bla bla bla
"""#TODO: bla bla bla
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'LFO mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onLfoTypeChosen(self, event):
        lfoType = self._lfoTypeField.GetValue()
        if(lfoType != "Random"):
            self._mainModulationGuiSizer.Show(self._lfoLengthSizer)
            self._mainModulationGuiSizer.Show(self._lfoPhaseSizer)
            self._mainModulationGuiSizer.Show(self._lfoMinValueSliderSizer)
            self._mainModulationGuiSizer.Show(self._lfoMaxValueSliderSizer)
            self._parentSizer.Layout()
        else:
            self._mainModulationGuiSizer.Hide(self._lfoLengthSizer)
            self._mainModulationGuiSizer.Hide(self._lfoPhaseSizer)
            self._mainModulationGuiSizer.Show(self._lfoMinValueSliderSizer)
            self._mainModulationGuiSizer.Show(self._lfoMaxValueSliderSizer)
            self._parentSizer.Layout()
            
    def _onLfoLengthHelp(self, event):
        text = """
The length of the LFO in beats.
"""
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'LFO length help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onLfoPhaseHelp(self, event):
        text = """
The start offset or phase of the LFO in beats.
"""
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'LFO offset help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()


    def _onAdsrTypeHelp(self, event):
        text = """
Selects full ADSR or just Attack/Release
"""
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'ADSR mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onSlide(self, event):
        sliderId = event.GetEventObject().GetId()
        if(sliderId == self._lfoMinValueSliderId):
            valueString = "%.2f" % (float(self._lfoMinValueSlider.GetValue()) / 101.0)
            self._lfoMinValueLabel.SetLabel(valueString)
        if(sliderId == self._lfoMaxValueSliderId):
            valueString = "%.2f" % (float(self._lfoMaxValueSlider.GetValue()) / 101.0)
            self._lfoMaxValueLabel.SetLabel(valueString)
        if(sliderId == self._valueSliderId):
            valueString = "%.2f" % (float(self._valueSlider.GetValue()) / 101.0)
            self._valueValueLabel.SetLabel(valueString)

    def _onCloseButton(self, event):
        self._hideModulationCallback()

    def _onSaveButton(self, event):
        modType = self._modulationSorcesField.GetValue()
        modeString = modType
        if(modType == "MidiChannel"):
            channelType = self._midiChannelSourceField.GetValue()
            modeString += "." + channelType
            if(channelType == "Controller"):
                controllerName = self._midiControllerField.GetValue()
                modeString += "." + controllerName
        if(modType == "MidiNote"):
            noteMod = self._midiNoteSourceField.GetValue()
            modeString += "." + noteMod
        if(modType == "LFO"):
            lfoType = self._lfoTypeField.GetValue()
            modeString += "." + lfoType
            lfoLength = self._lfoLengthField.GetValue()
            modeString += "." + lfoLength
            lfoPhase = self._lfoPhaseField.GetValue()
            modeString += "|" + lfoPhase
            valueString = "%.2f" % (float(self._lfoMinValueSlider.GetValue()) / 101.0)
            modeString += "|" + valueString
            valueString = "%.2f" % (float(self._lfoMaxValueSlider.GetValue()) / 101.0)
            modeString += "|" + valueString
        if(modType == "ADSR"):
            adsrType = self._adsrTypeField.GetValue()
            modeString += "." + adsrType
        if(modType == "Value"):
            valueString = "%.2f" % (float(self._valueSlider.GetValue()) / 101.0)
            modeString += "." + valueString
        if(self._updateWidget != None):
            self._updateWidget.SetValue(modeString)

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

    def updateGui(self, modulationString, widget):
        self._updateWidget = widget
        modulationIdTuplet = self._midiModulation.findModulationId(modulationString)
        updatedId = None
        if(modulationIdTuplet == None):
            self._modulationSorcesField.SetValue("None")
        else:
            updatedId = self._modulationSorces.getNames(modulationIdTuplet[0])
            self._modulationSorcesField.SetValue(updatedId)
            if(modulationIdTuplet[0] == ModulationSources.MidiChannel):
                subModIdTuplet = modulationIdTuplet[1]
                isInt = isinstance(subModIdTuplet, int)
                if((isInt == False) and (len(subModIdTuplet) == 2)):
                    if(subModIdTuplet[0] == MidiChannelModulationSources.Controller):
                        controllerName = self._midiControllers.getName(subModIdTuplet[1])
                        self._midiControllerField.SetValue(controllerName)
                        self._midiChannelSourceField.SetValue("Controller")
                else:
                    channelSourceName = self._midiChannelSource.getNames(subModIdTuplet)
                    self._midiChannelSourceField.SetValue(channelSourceName)
                    self._midiControllerField.SetValue("ModWheel")
            elif(modulationIdTuplet[0] == ModulationSources.MidiNote):
                subModId = modulationIdTuplet[1]
                isInt = isinstance(subModId, int)
                if(isInt == False):
                    subModId = subModId[0]
                subModeName = self._midiNoteSource.getNames(subModId)
                self._midiNoteSourceField.SetValue(subModeName)
            elif(modulationIdTuplet[0] == ModulationSources.LFO):
                subModId = modulationIdTuplet[1]
                isInt = isinstance(subModId, int)
                if(isInt == True):
                    subModId = [subModId]
                subModName = self._lfoType.getNames(subModId[0])
                self._lfoTypeField.SetValue(subModName)
                if(len(subModId) > 1):
                    self._lfoLengthField.SetValue(str(subModId[1]))
                if(len(subModId) > 2):
                    self._lfoPhaseField.SetValue(str(subModId[2] / self._midiTiming.getTicksPerQuarteNote()))
                if(len(subModId) > 3):
                    calcValue = int(101.0 * subModId[3])
                    self._lfoMinValueSlider.SetValue(calcValue)
                    self._lfoMinValueLabel.SetLabel("%.2f" % (subModId[3]))
                if(len(subModId) > 4):
                    calcValue = int(101.0 * subModId[4])
                    self._lfoMaxValueSlider.SetValue(calcValue)
                    self._lfoMaxValueLabel.SetLabel("%.2f" % (subModId[4]))
            elif(modulationIdTuplet[0] == ModulationSources.ADSR):
                subModId = modulationIdTuplet[1]
                isInt = isinstance(subModId, int)
                if(isInt == True):
                    subModId = [subModId]
                subModName = self._adsrType.getNames(subModId[0])
                self._adsrTypeField.SetValue(subModName)
            elif(modulationIdTuplet[0] == ModulationSources.Value):
                subModId = modulationIdTuplet[1]
                isFloat = isinstance(subModId, float)
                if(isFloat != True):
                    subModId = subModId[0]
                calcValue = int(101.0 * subModId)
                self._valueSlider.SetValue(calcValue)
                self._valueValueLabel.SetLabel("%.2f" % (subModId))

        if(updatedId != "MidiChannel"):
            self._midiChannelSourceField.SetValue("Controller")
            self._midiControllerField.SetValue("ModWheel")
        if(updatedId != "MidiNote"):
            self._midiNoteSourceField.SetValue("Velocity")
        if(updatedId != "LFO"):
            self._lfoTypeField.SetValue("Triangle")
            self._lfoLengthField.SetValue("4.0")
            self._lfoPhaseField.SetValue("0.0")
            self._lfoMinValueSlider.SetValue(0)
            self._lfoMaxValueSlider.SetValue(101)
        if(updatedId != "ADSR"):
            self._adsrTypeField.SetValue("ADSR")
        if(updatedId != "Value"):
            self._valueSlider.SetValue(0)
            self._valueValueLabel.SetLabel("0.00")

        self._onModulationSourceChosen(None)

