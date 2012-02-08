'''
Created on 6. feb. 2012

@author: pcn
'''
from midi.MidiTiming import MidiTiming
from configuration.EffectSettings import EffectTemplates, FadeTemplates
import wx
from midi.MidiController import getControllerId

class GlobalConfig(object):
    def __init__(self, configParent):
        self._configurationTree = configParent.addChildUnique("Global")
        self._configurationTree.addIntParameter("ResolutionX", 800)
        self._configurationTree.addIntParameter("ResolutionY", 600)
        self._internalResolutionX =  self._configurationTree.getValueFromPath("Global.ResolutionX")
        self._internalResolutionY =  self._configurationTree.getValueFromPath("Global.ResolutionY")

        self._midiTiming = MidiTiming()

        self._effectsConfiguration = EffectTemplates(self._configurationTree, self._midiTiming, self._internalResolutionX, self._internalResolutionY)
        self._effectsGui = EffectsGui()
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

    def setupEffectsGui(self, plane, sizer):
        self._effectsGui.setupEffectsGui(plane, sizer)

    def setupEffectsSlidersGui(self, plane, sizer):
        self._effectsGui.setupEffectsSlidersGui(plane, sizer)

    def editEffectsConfig(self, configName, midiChannel, midiNote, midiSender):
        template = self._effectsConfiguration.getTemplate(configName)
        if(template != None):
            self._effectsGui.editEffectsConfig(template, midiChannel, midiNote, midiSender)

class EffectsGui(object):
    def __init__(self):
        pass

    def setupEffectsGui(self, plane, sizer):
        templateNameSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText1 = wx.StaticText(plane, wx.ID_ANY, "Name:") #@UndefinedVariable
        self._templateNameField = wx.TextCtrl(plane, wx.ID_ANY, "MediaDefault1", size=(200, -1)) #@UndefinedVariable
        self._templateNameField.SetInsertionPoint(0)
        templateNameSizer.Add(tmpText1, 1, wx.ALL, 5) #@UndefinedVariable
        templateNameSizer.Add(self._templateNameField, 2, wx.ALL, 5) #@UndefinedVariable
        sizer.Add(templateNameSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        effectNameSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText2 = wx.StaticText(plane, wx.ID_ANY, "Effect:") #@UndefinedVariable
        self._effectNameField = wx.TextCtrl(plane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._effectNameField.SetInsertionPoint(0)
        effectNameSizer.Add(tmpText2, 1, wx.ALL, 5) #@UndefinedVariable
        effectNameSizer.Add(self._effectNameField, 2, wx.ALL, 5) #@UndefinedVariable
        sizer.Add(effectNameSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        ammountSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText3 = wx.StaticText(plane, wx.ID_ANY, "Ammount:") #@UndefinedVariable
        self._ammountField = wx.TextCtrl(plane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._ammountField.SetInsertionPoint(0)
        ammountSizer.Add(tmpText3, 1, wx.ALL, 5) #@UndefinedVariable
        ammountSizer.Add(self._ammountField, 2, wx.ALL, 5) #@UndefinedVariable
        sizer.Add(ammountSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        arg1Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText4 = wx.StaticText(plane, wx.ID_ANY, "Argument 1:") #@UndefinedVariable
        self._arg1Field = wx.TextCtrl(plane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._arg1Field.SetInsertionPoint(0)
        arg1Sizer.Add(tmpText4, 1, wx.ALL, 5) #@UndefinedVariable
        arg1Sizer.Add(self._arg1Field, 2, wx.ALL, 5) #@UndefinedVariable
        sizer.Add(arg1Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        arg2Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText5 = wx.StaticText(plane, wx.ID_ANY, "Argument 2:") #@UndefinedVariable
        self._arg2Field = wx.TextCtrl(plane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._arg2Field.SetInsertionPoint(0)
        arg2Sizer.Add(tmpText5, 1, wx.ALL, 5) #@UndefinedVariable
        arg2Sizer.Add(self._arg2Field, 2, wx.ALL, 5) #@UndefinedVariable
        sizer.Add(arg2Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        arg3Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText6 = wx.StaticText(plane, wx.ID_ANY, "Argument 3:") #@UndefinedVariable
        self._arg3Field = wx.TextCtrl(plane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._arg3Field.SetInsertionPoint(0)
        arg3Sizer.Add(tmpText6, 1, wx.ALL, 5) #@UndefinedVariable
        arg3Sizer.Add(self._arg3Field, 2, wx.ALL, 5) #@UndefinedVariable
        sizer.Add(arg3Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        arg4Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(plane, wx.ID_ANY, "Argument 4:") #@UndefinedVariable
        self._arg4Field = wx.TextCtrl(plane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._arg4Field.SetInsertionPoint(0)
        arg4Sizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        arg4Sizer.Add(self._arg4Field, 2, wx.ALL, 5) #@UndefinedVariable
        sizer.Add(arg4Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

    def setupEffectsSlidersGui(self, plane, sizer):
        ammountSliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText3 = wx.StaticText(plane, wx.ID_ANY, "Ammount:") #@UndefinedVariable
        self._ammountSlider = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=127, size=(200, -1)) #@UndefinedVariable
        ammountSliderSizer.Add(tmpText3, 1, wx.ALL, 5) #@UndefinedVariable
        ammountSliderSizer.Add(self._ammountSlider, 2, wx.ALL, 5) #@UndefinedVariable
        sizer.Add(ammountSliderSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._amountSliderId = self._ammountSlider.GetId()

        arg1SliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText4 = wx.StaticText(plane, wx.ID_ANY, "Argument 1:") #@UndefinedVariable
        self._arg1Slider = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=127, size=(200, -1)) #@UndefinedVariable
        arg1SliderSizer.Add(tmpText4, 1, wx.ALL, 5) #@UndefinedVariable
        arg1SliderSizer.Add(self._arg1Slider, 2, wx.ALL, 5) #@UndefinedVariable
        sizer.Add(arg1SliderSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._arg1SliderId = self._arg1Slider.GetId()

        arg2SliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText5 = wx.StaticText(plane, wx.ID_ANY, "Argument 2:") #@UndefinedVariable
        self._arg2Slider = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=127, size=(200, -1)) #@UndefinedVariable
        arg2SliderSizer.Add(tmpText5, 1, wx.ALL, 5) #@UndefinedVariable
        arg2SliderSizer.Add(self._arg2Slider, 2, wx.ALL, 5) #@UndefinedVariable
        sizer.Add(arg2SliderSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._arg2SliderId = self._arg2Slider.GetId()

        arg3SliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText6 = wx.StaticText(plane, wx.ID_ANY, "Argument 3:") #@UndefinedVariable
        self._arg3Slider = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=127, size=(200, -1)) #@UndefinedVariable
        arg3SliderSizer.Add(tmpText6, 1, wx.ALL, 5) #@UndefinedVariable
        arg3SliderSizer.Add(self._arg3Slider, 2, wx.ALL, 5) #@UndefinedVariable
        sizer.Add(arg3SliderSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._arg3SliderId = self._arg3Slider.GetId()

        arg4SliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(plane, wx.ID_ANY, "Argument 4:") #@UndefinedVariable
        self._arg4Slider = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=127, size=(200, -1)) #@UndefinedVariable
        arg4SliderSizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        arg4SliderSizer.Add(self._arg4Slider, 2, wx.ALL, 5) #@UndefinedVariable
        sizer.Add(arg4SliderSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._arg4SliderId = self._arg4Slider.GetId()

        plane.Bind(wx.EVT_SLIDER, self._onSlide) #@UndefinedVariable

    def _onSlide(self, event):
        sliderId = event.GetEventObject().GetId()
        if(sliderId == self._amountSliderId):
            print "Ammount: " + str(self._ammountSlider.GetValue())
            if((self._midiChannel > -1) and (self._midiChannel < 16)):
                self.sendMidi(self._midiChannel, self._ammountField.GetValue(), self._ammountSlider.GetValue())
        elif(sliderId == self._arg1SliderId):
            print "Arg 1: " + str(self._arg1Slider.GetValue())
            if((self._midiChannel > -1) and (self._midiChannel < 16)):
                self.sendMidi(self._midiChannel, self._arg1Field.GetValue(), self._arg1Slider.GetValue())
        elif(sliderId == self._arg2SliderId):
            print "Arg 2: " + str(self._arg2Slider.GetValue())
            if((self._midiChannel > -1) and (self._midiChannel < 16)):
                self.sendMidi(self._midiChannel, self._arg2Field.GetValue(), self._arg2Slider.GetValue())
        elif(sliderId == self._arg3SliderId):
            print "Arg 3: " + str(self._arg3Slider.GetValue())
            if((self._midiChannel > -1) and (self._midiChannel < 16)):
                self.sendMidi(self._midiChannel, self._arg3Field.GetValue(), self._arg3Slider.GetValue())
        elif(sliderId == self._arg4SliderId):
            print "Arg 4: " + str(self._arg4Slider.GetValue())
            if((self._midiChannel > -1) and (self._midiChannel < 16)):
                self.sendMidi(self._midiChannel, self._arg4Field.GetValue(), self._arg4Slider.GetValue())

    def sendMidi(self, channel, controllerDescription, value):
        if(controllerDescription.startswith("MidiChannel.")):
            descriptionSplit = controllerDescription.split('.', 6)
            if(len(descriptionSplit) > 1):
                if(descriptionSplit[1] == "Controller"):
                    if(len(descriptionSplit) > 2):
                        controllerId = getControllerId(descriptionSplit[2])
#                        print "Sending controller: " + descriptionSplit[2] + " -> " + str(controllerId)
                        self._midiSender.sendMidiController(channel, controllerId, value)
                elif(descriptionSplit[1] == "PitchBend"):
                    self._midiSender.sendPitchbend(channel, value)
                elif(descriptionSplit[1] == "Aftertouch"):
                    self._midiSender.sendAftertouch(channel, value)
        if(controllerDescription.startswith("MidiNote.")):
            descriptionSplit = controllerDescription.split('.', 6)
            if(len(descriptionSplit) > 1):
                if((descriptionSplit[1] == "NotePreasure") or (descriptionSplit[1] == "Preasure")):
                    self._midiSender.sendPolyPreasure(self._midiChannel, self._midiNote, value)
            
    def editEffectsConfig(self, effectTemplate, midiChannel, midiNote, midiSender):
        self._midiChannel = midiChannel
        self._midiNote = midiNote
        self._midiSender = midiSender
        config = effectTemplate.getConfigHolder()
        self._templateNameField.SetValue(config.getValue("Name"))
        self._effectNameField.SetValue(config.getValue("Effect"))
        self._ammountField.SetValue(config.getValue("Amount"))
        self._arg1Field.SetValue(config.getValue("Arg1"))
        self._arg2Field.SetValue(config.getValue("Arg2"))
        self._arg3Field.SetValue(config.getValue("Arg3"))
        self._arg4Field.SetValue(config.getValue("Arg4"))

