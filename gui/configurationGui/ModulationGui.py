'''
Created on 22. feb. 2012

@author: pcn
'''

import wx
from widgets.PcnAdsrDisplayWindget import PcnAdsrDisplayWidget
from widgets.PcnLfoDisplayWindget import PcnLfoDisplayWidget

from midi.MidiModulation import ModulationSources, AdsrShapes, LfoShapes,\
    MidiModulation, AttackDecaySustainRelease, getLfoShapeId,\
    LowFrequencyOscilator, getAdsrShapeId
from midi.MidiStateHolder import MidiChannelModulationSources,\
    NoteModulationSources
from midi.MidiController import MidiControllers

class ModulationGui(object):
    def __init__(self, mainConfing, midiTiming):
        self._mainConfig = mainConfing
        self._midiTiming = midiTiming
        self._midiModulation = MidiModulation(None, self._midiTiming)
        self._updateWidget = None
        self._closeCallback = None

        self._blankModBitmap = wx.Bitmap("graphics/modeEmpty.png") #@UndefinedVariable
        self._modBitmatController = wx.Bitmap("graphics/modulationController.png") #@UndefinedVariable
        self._modBitmatNote = wx.Bitmap("graphics/modulationNote.png") #@UndefinedVariable
        self._modBitmatLfo = wx.Bitmap("graphics/modulationLfo.png") #@UndefinedVariable
        self._modBitmatAdsr = wx.Bitmap("graphics/modulationAdsr.png") #@UndefinedVariable
        self._modBitmatValue = wx.Bitmap("graphics/modulationValue.png") #@UndefinedVariable

        self._modBitmatBlankBig = wx.Bitmap("graphics/modulationBlankBig.png") #@UndefinedVariable
        self._modBitmatControllerBig = wx.Bitmap("graphics/modulationControllerBig.png") #@UndefinedVariable
        self._modBitmatNoteBig = wx.Bitmap("graphics/modulationNoteBig.png") #@UndefinedVariable
        self._modBitmatLfoBig = wx.Bitmap("graphics/modulationLfoBig.png") #@UndefinedVariable
        self._modBitmatAdsrBig = wx.Bitmap("graphics/modulationAdsrBig.png") #@UndefinedVariable
        self._modBitmatValueBig = wx.Bitmap("graphics/modulationValueBig.png") #@UndefinedVariable

        self._modulationSorces = ModulationSources()

    def setupModulationGui(self, plane, sizer, parentSizer, parentClass):
        self._mainModulationGuiPlane = plane
        self._mainModulationGuiSizer = sizer
        self._parentSizer = parentSizer
        self._hideModulationCallback = parentClass.hideModulationGui
        self._fixModulationGuiLayout = parentClass.fixModulationGuiLayout

        modulationSorcesSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText1 = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "Modulation:") #@UndefinedVariable
        self._modulationSorcesField = wx.ComboBox(self._mainModulationGuiPlane, wx.ID_ANY, size=(200, -1), choices=["None"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateChoices(self._modulationSorcesField, self._modulationSorces.getChoices, "None", "None")
        modulationSorcesButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        modulationSorcesButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
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
        midiChannelSourceButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        midiChannelSourceButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
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
        midiControllerButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        midiControllerButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onMidiChannelControllerHelp, id=midiControllerButton.GetId()) #@UndefinedVariable
        self._midiControllerSizer.Add(tmpText3, 1, wx.ALL, 5) #@UndefinedVariable
        self._midiControllerSizer.Add(self._midiControllerField, 2, wx.ALL, 5) #@UndefinedVariable
        self._midiControllerSizer.Add(midiControllerButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._midiControllerSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_COMBOBOX, self._onMidiControllerChosen, id=self._midiControllerField.GetId()) #@UndefinedVariable

        self._midiActiveControllerSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText4 = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "Active controllers:") #@UndefinedVariable
        self._midiActiveControllerField = wx.ListBox(self._mainModulationGuiPlane, wx.ID_ANY, size=(120, 100), choices=["None"], style=wx.LB_SINGLE) #@UndefinedVariable
        midiActiveControllerButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        midiActiveControllerButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
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
        midiNoteSourceButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        midiNoteSourceButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
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
        lfoTypeButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        lfoTypeButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onLfoTypeHelp, id=lfoTypeButton.GetId()) #@UndefinedVariable
        self._lfoTypeSizer.Add(tmpText6, 1, wx.ALL, 5) #@UndefinedVariable
        self._lfoTypeSizer.Add(self._lfoTypeField, 2, wx.ALL, 5) #@UndefinedVariable
        self._lfoTypeSizer.Add(lfoTypeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._lfoTypeSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_COMBOBOX, self._onLfoTypeChosen, id=self._lfoTypeField.GetId()) #@UndefinedVariable

        self._lfoLengthSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "LFO length:") #@UndefinedVariable
        self._lfoLengthSlider = wx.Slider(self._mainModulationGuiPlane, wx.ID_ANY, minValue=0, maxValue=160, size=(200, -1)) #@UndefinedVariable
        self._lfoLengthLabel = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "0.0", size=(30,-1)) #@UndefinedVariable
        lfoLengthButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        lfoLengthButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onLfoLengthHelp, id=lfoLengthButton.GetId()) #@UndefinedVariable
        self._lfoLengthSizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        self._lfoLengthSizer.Add(self._lfoLengthSlider, 2, wx.ALL, 5) #@UndefinedVariable
        self._lfoLengthSizer.Add(self._lfoLengthLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._lfoLengthSizer.Add(lfoLengthButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._lfoLengthSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._lfoLengthSliderId = self._lfoLengthSlider.GetId()

        self._lfoPhaseSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText8 = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "LFO offset:") #@UndefinedVariable
        self._lfoPhaseSlider = wx.Slider(self._mainModulationGuiPlane, wx.ID_ANY, minValue=0, maxValue=160, size=(200, -1)) #@UndefinedVariable
        self._lfoPhaseLabel = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "0.0", size=(30,-1)) #@UndefinedVariable
        lfoPhaseButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        lfoPhaseButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onLfoPhaseHelp, id=lfoPhaseButton.GetId()) #@UndefinedVariable
        self._lfoPhaseSizer.Add(tmpText8, 1, wx.ALL, 5) #@UndefinedVariable
        self._lfoPhaseSizer.Add(self._lfoPhaseSlider, 2, wx.ALL, 5) #@UndefinedVariable
        self._lfoPhaseSizer.Add(self._lfoPhaseLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._lfoPhaseSizer.Add(lfoPhaseButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._lfoPhaseSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._lfoPhaseSliderId = self._lfoPhaseSlider.GetId()

        self._lfoMinValueSliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._lfoMinValueSliderLabel = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "Min value:") #@UndefinedVariable
        self._lfoMinValueSlider = wx.Slider(self._mainModulationGuiPlane, wx.ID_ANY, minValue=0, maxValue=101, size=(200, -1)) #@UndefinedVariable
        self._lfoMinValueLabel = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "0.0", size=(30,-1)) #@UndefinedVariable
        lfoMinValueButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        lfoMinValueButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onLfoMinValueHelp, id=lfoMinValueButton.GetId()) #@UndefinedVariable
        self._lfoMinValueSliderSizer.Add(self._lfoMinValueSliderLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._lfoMinValueSliderSizer.Add(self._lfoMinValueSlider, 2, wx.ALL, 5) #@UndefinedVariable
        self._lfoMinValueSliderSizer.Add(self._lfoMinValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._lfoMinValueSliderSizer.Add(lfoMinValueButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._lfoMinValueSliderSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._lfoMinValueSliderId = self._lfoMinValueSlider.GetId()
        self._mainModulationGuiPlane.Bind(wx.EVT_SLIDER, self._onSlide) #@UndefinedVariable

        self._lfoMaxValueSliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._lfoMaxValueSliderLabel = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "Max value:") #@UndefinedVariable
        self._lfoMaxValueSlider = wx.Slider(self._mainModulationGuiPlane, wx.ID_ANY, minValue=0, maxValue=101, size=(200, -1)) #@UndefinedVariable
        self._lfoMaxValueLabel = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "0.0", size=(30,-1)) #@UndefinedVariable
        lfoMaxValueButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        lfoMaxValueButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onLfoMaxValueHelp, id=lfoMaxValueButton.GetId()) #@UndefinedVariable
        self._lfoMaxValueSliderSizer.Add(self._lfoMaxValueSliderLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._lfoMaxValueSliderSizer.Add(self._lfoMaxValueSlider, 2, wx.ALL, 5) #@UndefinedVariable
        self._lfoMaxValueSliderSizer.Add(self._lfoMaxValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._lfoMaxValueSliderSizer.Add(lfoMaxValueButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._lfoMaxValueSliderSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._lfoMaxValueSliderId = self._lfoMaxValueSlider.GetId()
        self._mainModulationGuiPlane.Bind(wx.EVT_SLIDER, self._onSlide) #@UndefinedVariable

        self._lfoGraphicsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._lfoGraphicsLabel = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "LFO graph:") #@UndefinedVariable
        emptyLfoBitMap = wx.EmptyBitmap (200, 80, depth=3) #@UndefinedVariable
        self._lfoGraphicsDisplay = PcnLfoDisplayWidget(self._mainModulationGuiPlane, emptyLfoBitMap)
        lfoGraphicsValueButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        lfoGraphicsValueButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onLfoGraphicsHelp, id=lfoGraphicsValueButton.GetId()) #@UndefinedVariable
        self._lfoGraphicsSizer.Add(self._lfoGraphicsLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._lfoGraphicsSizer.Add(self._lfoGraphicsDisplay, 2, wx.ALL, 5) #@UndefinedVariable
        self._lfoGraphicsSizer.Add(lfoGraphicsValueButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._lfoGraphicsSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._lfoGraphicsId = self._lfoGraphicsDisplay.GetId()

        """ADSR"""
        self._adsrTypeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText3 = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "ADSR type:") #@UndefinedVariable
        self._adsrType = AdsrShapes()
        self._adsrTypeField = wx.ComboBox(self._mainModulationGuiPlane, wx.ID_ANY, size=(200, -1), choices=["ADSR"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateChoices(self._adsrTypeField, self._adsrType.getChoices, "ADSR", "ADSR")
        adsrTypeButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        adsrTypeButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onAdsrTypeHelp, id=adsrTypeButton.GetId()) #@UndefinedVariable
        self._adsrTypeSizer.Add(tmpText3, 1, wx.ALL, 5) #@UndefinedVariable
        self._adsrTypeSizer.Add(self._adsrTypeField, 2, wx.ALL, 5) #@UndefinedVariable
        self._adsrTypeSizer.Add(adsrTypeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._adsrTypeSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_COMBOBOX, self._onAdsrTypeChosen, id=self._adsrTypeField.GetId()) #@UndefinedVariable

        self._adsrAttackhSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "ADSR attack:") #@UndefinedVariable
        self._adsrAttackSlider = wx.Slider(self._mainModulationGuiPlane, wx.ID_ANY, minValue=0, maxValue=160, size=(200, -1)) #@UndefinedVariable
        self._adsrAttackLabel = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "0.0", size=(30,-1)) #@UndefinedVariable
        adsrAttackhButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        adsrAttackhButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onAdsrAttackHelp, id=adsrAttackhButton.GetId()) #@UndefinedVariable
        self._adsrAttackhSizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        self._adsrAttackhSizer.Add(self._adsrAttackSlider, 2, wx.ALL, 5) #@UndefinedVariable
        self._adsrAttackhSizer.Add(self._adsrAttackLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._adsrAttackhSizer.Add(adsrAttackhButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._adsrAttackhSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._adsrAttackSliderId = self._adsrAttackSlider.GetId()

        self._adsrDecaySizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText8 = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "ADSR decay:") #@UndefinedVariable
        self._adsrDecaySlider = wx.Slider(self._mainModulationGuiPlane, wx.ID_ANY, minValue=0, maxValue=160, size=(200, -1)) #@UndefinedVariable
        self._adsrDecayLabel = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "0.0", size=(30,-1)) #@UndefinedVariable
        adsrDecayButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        adsrDecayButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onAdsrDecayHelp, id=adsrDecayButton.GetId()) #@UndefinedVariable
        self._adsrDecaySizer.Add(tmpText8, 1, wx.ALL, 5) #@UndefinedVariable
        self._adsrDecaySizer.Add(self._adsrDecaySlider, 2, wx.ALL, 5) #@UndefinedVariable
        self._adsrDecaySizer.Add(self._adsrDecayLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._adsrDecaySizer.Add(adsrDecayButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._adsrDecaySizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._adsrDecaySliderId = self._adsrDecaySlider.GetId()

        self._adsrSustainSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._adsrSustainLabel = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "ADSR sustain:") #@UndefinedVariable
        self._adsrSustainSlider = wx.Slider(self._mainModulationGuiPlane, wx.ID_ANY, minValue=0, maxValue=101, size=(200, -1)) #@UndefinedVariable
        self._adsrSustainValueLabel = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "0.0", size=(30,-1)) #@UndefinedVariable
        adsrSustainValueButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        adsrSustainValueButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onAdsrSustainHelp, id=adsrSustainValueButton.GetId()) #@UndefinedVariable
        self._adsrSustainSizer.Add(self._adsrSustainLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._adsrSustainSizer.Add(self._adsrSustainSlider, 2, wx.ALL, 5) #@UndefinedVariable
        self._adsrSustainSizer.Add(self._adsrSustainValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._adsrSustainSizer.Add(adsrSustainValueButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._adsrSustainSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._adsrSustainId = self._adsrSustainSlider.GetId()
        self._mainModulationGuiPlane.Bind(wx.EVT_SLIDER, self._onSlide) #@UndefinedVariable

        self._adsrReleaseSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._adsrReleaseLabel = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "ADSR release:") #@UndefinedVariable
        self._adsrReleaseSlider = wx.Slider(self._mainModulationGuiPlane, wx.ID_ANY, minValue=0, maxValue=160, size=(200, -1)) #@UndefinedVariable
        self._adsrReleaseValueLabel = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "0.0", size=(30,-1)) #@UndefinedVariable
        adsrReleaseValueButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        adsrReleaseValueButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onAdsrReleaseHelp, id=adsrReleaseValueButton.GetId()) #@UndefinedVariable
        self._adsrReleaseSizer.Add(self._adsrReleaseLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._adsrReleaseSizer.Add(self._adsrReleaseSlider, 2, wx.ALL, 5) #@UndefinedVariable
        self._adsrReleaseSizer.Add(self._adsrReleaseValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._adsrReleaseSizer.Add(adsrReleaseValueButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._adsrReleaseSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._adsrReleaseId = self._adsrReleaseSlider.GetId()
        self._mainModulationGuiPlane.Bind(wx.EVT_SLIDER, self._onSlide) #@UndefinedVariable

        self._adsrGraphicsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._adsrGraphicsLabel = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "ADSR graph:") #@UndefinedVariable
        emptyAdsrBitMap = wx.EmptyBitmap (200, 80, depth=3) #@UndefinedVariable
        self._adsrGraphicsDisplay = PcnAdsrDisplayWidget(self._mainModulationGuiPlane, emptyAdsrBitMap)
        adsrGraphicsValueButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        adsrGraphicsValueButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onAdsrGraphicsHelp, id=adsrGraphicsValueButton.GetId()) #@UndefinedVariable
        self._adsrGraphicsSizer.Add(self._adsrGraphicsLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._adsrGraphicsSizer.Add(self._adsrGraphicsDisplay, 2, wx.ALL, 5) #@UndefinedVariable
        self._adsrGraphicsSizer.Add(adsrGraphicsValueButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._adsrGraphicsSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._adsrGraphicsId = self._adsrGraphicsDisplay.GetId()

        """Value"""

        self._valueSliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._valueSliderLabel = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "Value:") #@UndefinedVariable
        self._valueSlider = wx.Slider(self._mainModulationGuiPlane, wx.ID_ANY, minValue=0, maxValue=101, size=(200, -1)) #@UndefinedVariable
        self._valueValueLabel = wx.StaticText(self._mainModulationGuiPlane, wx.ID_ANY, "0.0", size=(30,-1)) #@UndefinedVariable
        valueValueButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        valueValueButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onValueHelp, id=valueValueButton.GetId()) #@UndefinedVariable
        self._valueSliderSizer.Add(self._valueSliderLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._valueSliderSizer.Add(self._valueSlider, 2, wx.ALL, 5) #@UndefinedVariable
        self._valueSliderSizer.Add(self._valueValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._valueSliderSizer.Add(valueValueButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainModulationGuiSizer.Add(self._valueSliderSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._valueSliderId = self._valueSlider.GetId()
        self._mainModulationGuiPlane.Bind(wx.EVT_SLIDER, self._onSlide) #@UndefinedVariable

        """Buttons"""

        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Close') #@UndefinedVariable
        closeButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainModulationGuiPlane.Bind(wx.EVT_BUTTON, self._onCloseButton, id=closeButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 1, wx.ALL, 5) #@UndefinedVariable
        saveButton = wx.Button(self._mainModulationGuiPlane, wx.ID_ANY, 'Save') #@UndefinedVariable
        saveButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
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
            self._onMidiChannelSourceChosen(event)
        else:
            self._mainModulationGuiSizer.Hide(self._midiChannelSourceSizer)
            self._mainModulationGuiSizer.Hide(self._midiControllerSizer)
            self._mainModulationGuiSizer.Hide(self._midiActiveControllerSizer)
        if(choice == "MidiNote"):
            self._mainModulationGuiSizer.Show(self._midiNoteSourceSizer)
        else:
            self._mainModulationGuiSizer.Hide(self._midiNoteSourceSizer)
        if(choice == "LFO"):
            self._mainModulationGuiSizer.Show(self._lfoTypeSizer)
            self._onLfoTypeChosen(event)
        else:
            self._mainModulationGuiSizer.Hide(self._lfoTypeSizer)
            self._mainModulationGuiSizer.Hide(self._lfoLengthSizer)
            self._mainModulationGuiSizer.Hide(self._lfoPhaseSizer)
            self._mainModulationGuiSizer.Hide(self._lfoMinValueSliderSizer)
            self._mainModulationGuiSizer.Hide(self._lfoMaxValueSliderSizer)
            self._mainModulationGuiSizer.Hide(self._lfoGraphicsSizer)
        if(choice == "ADSR"):
            self._mainModulationGuiSizer.Show(self._adsrTypeSizer)
            self._onAdsrTypeChosen(event)
        else:
            self._mainModulationGuiSizer.Hide(self._adsrTypeSizer)
            self._mainModulationGuiSizer.Hide(self._adsrAttackhSizer)
            self._mainModulationGuiSizer.Hide(self._adsrDecaySizer)
            self._mainModulationGuiSizer.Hide(self._adsrSustainSizer)
            self._mainModulationGuiSizer.Hide(self._adsrReleaseSizer)
            self._mainModulationGuiSizer.Hide(self._adsrGraphicsSizer)
        if(choice == "Value"):
            self._mainModulationGuiSizer.Show(self._valueSliderSizer)
        else:
            self._mainModulationGuiSizer.Hide(self._valueSliderSizer)

        self._fixModulationGuiLayout()

    def _onModulationModeHelp(self, event):
        text = """
Selects modulation type.

MidiChannel:\tChannel wide MIDI controllers.
MidiNote:\t\tVelocity and note pressures.
LFO:\t\tLow Frequency Oscillator
ADSR:\t\tAttach/Release based on note timing.
Value:\t\tStatic value.
"""
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'Modulation mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _getActiveControllersStringList(self):
        idList = self._mainConfig.getLatestMidiControllers()
        returnList = []
        if(idList != None):
            for ctrlId in idList:
                if(ctrlId != ""):
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
            self._mainModulationGuiSizer.Layout()
            self._parentSizer.Layout()
        else:
            self._mainModulationGuiSizer.Hide(self._midiActiveControllerSizer)
            self._mainModulationGuiSizer.Hide(self._midiControllerSizer)
            if(self._activeControllersUpdate.IsRunning() == True):
                self._activeControllersUpdate.Stop()
            self._mainModulationGuiSizer.Layout()
            self._parentSizer.Layout()

    def stopModulationUpdate(self):
        if(self._activeControllersUpdate.IsRunning() == True):
            self._activeControllersUpdate.Stop()

    def _onMidiChannelSourceHelp(self, event):
        text = """
Selects MIDI channel modulation source.

Controller:\tMIDI controllers like ModWheel etc.
PitchBend:\tMIDI pitch bend.
Aftertouch:\tPreasure applied while note is pressed down.
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
Select from all available controllers.

You can always fiddle with the controller you want and select it in active controllers instead.
"""
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'MIDI controller help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onMidiChannelActiveControllerHelp(self, event):
        text = """
Shows the latest controllers received by the program on any MIDI channel.

Just turn or push the controller you want to use and it should show up here.
"""
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'Active controllers help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onMidiNoteSourceHelp(self, event):
        text = """
Midi notes modulation sources

Velocity:\t\tNote on velocity.
ReleaseVelocity:\tNote off velocity.
NotePreasure:\tPolyphonic pressure.
"""
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'MIDI note help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onLfoTypeHelp(self, event):
        text = """
Selects LFO shape.

Triangle:\t\tLinear up and down.
SawTooth:\tLinear up and instant down again.
Ramp:\t\tInstant up and linear down.
Sine:\t\tSine curve.
Random:\t\tNo phase just random numbers.
"""
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
            self._mainModulationGuiSizer.Show(self._lfoGraphicsSizer)
            self._mainModulationGuiSizer.Layout()
            self._parentSizer.Layout()
        else:
            self._mainModulationGuiSizer.Hide(self._lfoLengthSizer)
            self._mainModulationGuiSizer.Hide(self._lfoPhaseSizer)
            self._mainModulationGuiSizer.Show(self._lfoMinValueSliderSizer)
            self._mainModulationGuiSizer.Show(self._lfoMaxValueSliderSizer)
            self._mainModulationGuiSizer.Show(self._lfoGraphicsSizer)
            self._mainModulationGuiSizer.Layout()
            self._parentSizer.Layout()
        lfoLengthValue = float(self._lfoLengthSlider.GetValue()) / 160.0 * 32.0
        lfoPhaseValue = float(self._lfoPhaseSlider.GetValue()) / 160.0 * 32.0
        lfoMinValue = float(self._lfoMinValueSlider.GetValue()) / 101.0
        lfoMaxValue = float(self._lfoMaxValueSlider.GetValue()) / 101.0
        self._updateLfoGraph(self._lfoTypeField.GetValue(), lfoLengthValue, lfoPhaseValue, lfoMinValue, lfoMaxValue)

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


    def _onLfoMinValueHelp(self, event):
        text = """
Minimum output value from the LFO.
"""
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'LFO minimum value help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onLfoMaxValueHelp(self, event):
        text = """
Maximum output value from the LFO.
"""
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'LFO maximum value help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onLfoGraphicsHelp(self, event):
        text = """
Shows a graphic representation of the LFO settings over 64 beats.
"""
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'LFO graph help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onAdsrTypeHelp(self, event):
        text = """
Selects full ADSR or just Attack/Release mode
"""
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'ADSR mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onAdsrTypeChosen(self, event):
        adsrType = self._adsrTypeField.GetValue()
        if(adsrType == "ADSR"):
            self._mainModulationGuiSizer.Show(self._adsrAttackhSizer)
            self._mainModulationGuiSizer.Show(self._adsrDecaySizer)
            self._mainModulationGuiSizer.Show(self._adsrSustainSizer)
            self._mainModulationGuiSizer.Show(self._adsrReleaseSizer)
            self._mainModulationGuiSizer.Show(self._adsrGraphicsSizer)
            self._mainModulationGuiSizer.Layout()
            self._parentSizer.Layout()
        else:
            self._mainModulationGuiSizer.Hide(self._adsrDecaySizer)
            self._mainModulationGuiSizer.Hide(self._adsrSustainSizer)
            self._mainModulationGuiSizer.Show(self._adsrAttackhSizer)
            self._mainModulationGuiSizer.Show(self._adsrReleaseSizer)
            self._mainModulationGuiSizer.Show(self._adsrGraphicsSizer)
            self._mainModulationGuiSizer.Layout()
            self._parentSizer.Layout()
        attackValue = float(self._adsrAttackSlider.GetValue()) / 160.0 * 32.0
        decayValue = float(self._adsrDecaySlider.GetValue()) / 160.0 * 32.0
        sustainValue = float(self._adsrSustainSlider.GetValue()) / 101.0
        releaseValue = float(self._adsrReleaseSlider.GetValue()) / 160.0 * 32.0
        self._updateAdsrGraph(self._adsrTypeField.GetValue(), attackValue, decayValue, sustainValue, releaseValue)
            
    def _onAdsrAttackHelp(self, event):
        text = """
Sets attack time.
"""
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'ADSR attack help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onAdsrDecayHelp(self, event):
        text = """
Sets decay time.
"""
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'ADSR decay help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onAdsrSustainHelp(self, event):
        text = """
Sets sustain level.
"""
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'ADSR sustain help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onAdsrReleaseHelp(self, event):
        text = """
Sets release time.
"""
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'ADSR release help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onAdsrGraphicsHelp(self, event):
        text = """
Shows a graphic representation of the ADSR settings.
This graph auto adjusts to the length of the ADSR.
"""
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'ADSR graph help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _updateLfoGraph(self, lfoTypeString, length, phase, minLevel, maxLevel):
        lfoType = getLfoShapeId(lfoTypeString)
        self._lfoGraphicsDisplay.drawLfo(LowFrequencyOscilator(self._midiTiming, lfoType, length, phase, minLevel, maxLevel))
        
    def _updateAdsrGraph(self, adsrTypeString, attack, decay, sustain, release):
        adsrType = getAdsrShapeId(adsrTypeString)
        self._adsrGraphicsDisplay.drawAdsr(AttackDecaySustainRelease(self._midiTiming, adsrType, attack, decay, sustain, release))

    def _onSlide(self, event):
        sliderId = event.GetEventObject().GetId()
        adsrModified = False
        lfoModified = False
        if(sliderId == self._lfoLengthSliderId):
            valueString = "%.1f" % (float(self._lfoLengthSlider.GetValue()) / 160.0 * 32.0)
            self._lfoLengthLabel.SetLabel(valueString)
            lfoModified = True
        elif(sliderId == self._lfoPhaseSliderId):
            valueString = "%.1f" % (float(self._lfoPhaseSlider.GetValue()) / 160.0 * 32.0)
            self._lfoPhaseLabel.SetLabel(valueString)
            lfoModified = True
        elif(sliderId == self._lfoMinValueSliderId):
            valueString = "%.2f" % (float(self._lfoMinValueSlider.GetValue()) / 101.0)
            self._lfoMinValueLabel.SetLabel(valueString)
            lfoModified = True
        elif(sliderId == self._lfoMaxValueSliderId):
            valueString = "%.2f" % (float(self._lfoMaxValueSlider.GetValue()) / 101.0)
            self._lfoMaxValueLabel.SetLabel(valueString)
            lfoModified = True
        elif(sliderId == self._adsrAttackSliderId):
            valueString = "%.1f" % (float(self._adsrAttackSlider.GetValue()) / 160.0 * 32.0)
            self._adsrAttackLabel.SetLabel(valueString)
            adsrModified = True
        elif(sliderId == self._adsrDecaySliderId):
            valueString = "%.1f" % (float(self._adsrDecaySlider.GetValue()) / 160.0 * 32.0)
            self._adsrDecayLabel.SetLabel(valueString)
            adsrModified = True
        elif(sliderId == self._adsrSustainId):
            valueString = "%.2f" % (float(self._adsrSustainSlider.GetValue()) / 101.0)
            self._adsrSustainValueLabel.SetLabel(valueString)
            adsrModified = True
        elif(sliderId == self._adsrReleaseId):
            valueString = "%.1f" % (float(self._adsrReleaseSlider.GetValue()) / 160.0 * 32.0)
            self._adsrReleaseValueLabel.SetLabel(valueString)
            adsrModified = True
        elif(sliderId == self._valueSliderId):
            valueString = "%.2f" % (float(self._valueSlider.GetValue()) / 101.0)
            self._valueValueLabel.SetLabel(valueString)
        if(lfoModified == True):
            lfoLengthValue = float(self._lfoLengthSlider.GetValue()) / 160.0 * 32.0
            lfoPhaseValue = float(self._lfoPhaseSlider.GetValue()) / 160.0 * 32.0
            lfoMinValue = float(self._lfoMinValueSlider.GetValue()) / 101.0
            lfoMaxValue = float(self._lfoMaxValueSlider.GetValue()) / 101.0
            self._updateLfoGraph(self._lfoTypeField.GetValue(), lfoLengthValue, lfoPhaseValue, lfoMinValue, lfoMaxValue)
        if(adsrModified == True):
            attackValue = float(self._adsrAttackSlider.GetValue()) / 160.0 * 32.0
            decayValue = float(self._adsrDecaySlider.GetValue()) / 160.0 * 32.0
            sustainValue = float(self._adsrSustainSlider.GetValue()) / 101.0
            releaseValue = float(self._adsrReleaseSlider.GetValue()) / 160.0 * 32.0
            self._updateAdsrGraph(self._adsrTypeField.GetValue(), attackValue, decayValue, sustainValue, releaseValue)

    def _onValueHelp(self, event):
        text = """
Constant static value.
"""
        dlg = wx.MessageDialog(self._mainModulationGuiPlane, text, 'Value help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onCloseButton(self, event):
        if(self._closeCallback != None):
            self._closeCallback()
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
            valueString = "%.2f" % (float(self._lfoLengthSlider.GetValue()) / 160.0 * 32.0)
            modeString += "." + valueString
            valueString = "%.2f" % (float(self._lfoPhaseSlider.GetValue()) / 160.0 * 32.0)
            modeString += "|" + valueString
            valueString = "%.2f" % (float(self._lfoMinValueSlider.GetValue()) / 101.0)
            modeString += "|" + valueString
            valueString = "%.2f" % (float(self._lfoMaxValueSlider.GetValue()) / 101.0)
            modeString += "|" + valueString
        if(modType == "ADSR"):
            adsrType = self._adsrTypeField.GetValue()
            modeString += "." + adsrType
            valueString = "%.2f" % (float(self._adsrAttackSlider.GetValue()) / 160.0 * 32.0)
            modeString += "." + valueString
            if(adsrType == "ADSR"):
                valueString = "%.2f" % (float(self._adsrDecaySlider.GetValue()) / 160.0 * 32.0)
                modeString += "|" + valueString
                valueString = "%.2f" % (float(self._adsrSustainSlider.GetValue()) / 101.0)
                modeString += "|" + valueString
            valueString = "%.2f" % (float(self._adsrReleaseSlider.GetValue()) / 160.0 * 32.0)
            modeString += "|" + valueString
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

    def getModulationImageId(self, modulationString):
        modulationIdTuplet = self._midiModulation.findModulationId(modulationString)
        if(modulationIdTuplet == None):
            return ModulationSources.NoModulation
        else:
            if(modulationIdTuplet[0] == ModulationSources.MidiChannel):
                return ModulationSources.MidiChannel
            elif(modulationIdTuplet[0] == ModulationSources.MidiNote):
                return ModulationSources.MidiChannel
            elif(modulationIdTuplet[0] == ModulationSources.LFO):
                return ModulationSources.MidiChannel
            elif(modulationIdTuplet[0] == ModulationSources.ADSR):
                return ModulationSources.MidiChannel
            elif(modulationIdTuplet[0] == ModulationSources.Value):
                return ModulationSources.MidiChannel

    def getModulationImageCount(self):
        return len(self._modulationSorces.getChoices())

    def getModulationImageBitmap(self, index):
        if(index == ModulationSources.NoModulation):
            return self._blankModBitmap
        elif(index == ModulationSources.MidiChannel):
            return self._modBitmatController
        elif(index == ModulationSources.MidiNote):
            return self._modBitmatNote
        elif(index == ModulationSources.LFO):
            return self._modBitmatLfo
        elif(index == ModulationSources.ADSR):
            return self._modBitmatAdsr
        elif(index == ModulationSources.Value):
            return self._modBitmatValue

    def getBigModulationImageBitmap(self, index):
        if(index == ModulationSources.NoModulation):
            return self._modBitmatBlankBig
        elif(index == ModulationSources.MidiChannel):
            return self._modBitmatControllerBig
        elif(index == ModulationSources.MidiNote):
            return self._modBitmatNoteBig
        elif(index == ModulationSources.LFO):
            return self._modBitmatLfoBig
        elif(index == ModulationSources.ADSR):
            return self._modBitmatAdsrBig
        elif(index == ModulationSources.Value):
            return self._modBitmatValueBig

    def updateModulationGuiButton(self, modulationString, widget):
        imageId = self.getModulationImageId(modulationString)
        bitmap = self.getModulationImageBitmap(imageId)
        widget.setBitmaps(bitmap, bitmap)
       
    def updateGui(self, modulationString, widget, closeCallback):
        self._updateWidget = widget
        self._closeCallback = closeCallback
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
                    calcValue = int(160.0 * subModId[1] / 32.0)
                    self._lfoLengthSlider.SetValue(calcValue)
                    self._lfoLengthLabel.SetLabel("%.1f" % (subModId[1]))
                if(len(subModId) > 2):
                    calcValue = int(160.0 * subModId[2] / 32.0)
                    self._lfoPhaseSlider.SetValue(calcValue)
                    self._lfoPhaseLabel.SetLabel("%.1f" % (subModId[2]))
                if(len(subModId) > 3):
                    calcValue = int(101.0 * subModId[3])
                    self._lfoMinValueSlider.SetValue(calcValue)
                    self._lfoMinValueLabel.SetLabel("%.2f" % (subModId[3]))
                if(len(subModId) > 4):
                    calcValue = int(101.0 * subModId[4])
                    self._lfoMaxValueSlider.SetValue(calcValue)
                    self._lfoMaxValueLabel.SetLabel("%.2f" % (subModId[4]))
                self._updateLfoGraph(subModName, subModId[1], subModId[2], subModId[3], subModId[4])
            elif(modulationIdTuplet[0] == ModulationSources.ADSR):
                subModId = modulationIdTuplet[1]
                isInt = isinstance(subModId, int)
                if(isInt == True):
                    subModId = [subModId]
                subModName = self._adsrType.getNames(subModId[0])
                self._adsrTypeField.SetValue(subModName)
                if(len(subModId) > 1):
                    calcValue = int(160.0 * subModId[1] / 32.0)
                    self._adsrAttackSlider.SetValue(calcValue)
                    self._adsrAttackLabel.SetLabel("%.1f" % (subModId[1]))
                if(len(subModId) > 2):
                    calcValue = int(160.0 * subModId[2] / 32.0)
                    self._adsrDecaySlider.SetValue(calcValue)
                    self._adsrDecayLabel.SetLabel("%.1f" % (subModId[2]))
                if(len(subModId) > 3):
                    calcValue = int(101.0 * subModId[3])
                    self._adsrSustainSlider.SetValue(calcValue)
                    self._adsrSustainValueLabel.SetLabel("%.2f" % (subModId[3]))
                if(len(subModId) > 4):
                    calcValue = int(160.0 * subModId[4] / 32.0)
                    self._adsrReleaseSlider.SetValue(calcValue)
                    self._adsrReleaseValueLabel.SetLabel("%.2f" % (subModId[4]))
                self._updateAdsrGraph(subModName, subModId[1], subModId[2], subModId[3], subModId[4])
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
            self._lfoLengthSlider.SetValue(20)
            self._lfoLengthLabel.SetLabel("4.0")
            self._lfoPhaseSlider.SetValue(0)
            self._lfoPhaseLabel.SetLabel("0.0")
            self._lfoMinValueSlider.SetValue(0)
            self._lfoMinValueLabel.SetLabel("0.00")
            self._lfoMaxValueSlider.SetValue(101)
            self._lfoMaxValueLabel.SetLabel("1.00")
            self._updateLfoGraph("Triangle", 4.0, 0.0, 0.0, 1.0)
        if(updatedId != "ADSR"):
            self._adsrTypeField.SetValue("ADSR")
            self._adsrAttackSlider.SetValue(0)
            self._adsrAttackLabel.SetLabel("0.0")
            self._adsrDecaySlider.SetValue(0)
            self._adsrDecayLabel.SetLabel("0.0")
            self._adsrSustainSlider.SetValue(101)
            self._adsrSustainValueLabel.SetLabel("1.00")
            self._adsrReleaseSlider.SetValue(0)
            self._adsrReleaseValueLabel.SetLabel("0.0")
            self._updateAdsrGraph("ADSR", 0.0, 0.0, 1.0, 0.0)
        if(updatedId != "Value"):
            self._valueSlider.SetValue(0)
            self._valueValueLabel.SetLabel("0.00")

        self._onModulationSourceChosen(None)

