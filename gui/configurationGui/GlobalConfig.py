'''
Created on 6. feb. 2012

@author: pcn
'''
from midi.MidiTiming import MidiTiming
from configuration.EffectSettings import EffectTemplates, FadeTemplates,\
    EffectImageList, TimeModulationTemplates, FadeSettings
import wx
from wx.lib.agw import ultimatelistctrl #@UnresolvedImport
from midi.MidiModulation import MidiModulation
from midi.MidiController import MidiControllers
from video.media.MediaFileModes import TimeModulationMode, WipeMode
from video.EffectModes import EffectTypes, FlipModes, ZoomModes, DistortionModes,\
    EdgeModes, DesaturateModes, getEffectId, getEffectName, ColorizeModes,\
    EdgeColourModes, ContrastModes, HueSatModes, ScrollModes, ValueToHueModes,\
    MirrorModes, BlobDetectModes, PixelateModes, TVNoizeModes, BlurModes,\
    RayModes, SlitDirections, StrobeModes
from configurationGui.ModulationGui import ModulationGui
import sys
from configurationGui.EffectImagesListGui import EffectImagesListGui
from widgets.PcnImageButton import PcnImageButton
from midi.MidiUtilities import noteToNoteString
import re
from configurationGui.UtilityDialogs import ThreeChoiceMessageDialog,\
    updateChoices
from configurationGui.CurveGui import CurveGui

class GlobalConfig(object):
    def __init__(self, configParent, mainConfig, specialModulationHolder, effectsModulation):
        self._mainConfig = mainConfig
        self._configurationTree = configParent.addChildUnique("Global")
        self._specialModulationHolder = specialModulationHolder
        self._effectsModulation = effectsModulation

        self._midiTiming = MidiTiming()

        self._modulationGui = ModulationGui(self._mainConfig, self._midiTiming, self._specialModulationHolder, self)
        self._curveGui = CurveGui(self._mainConfig)

        self._timeModulationConfiguration = TimeModulationTemplates(self._configurationTree, self._midiTiming, self._specialModulationHolder)
        self._timeModulationGui = TimeModulationGui(self._mainConfig, self._midiTiming, self._modulationGui, self._specialModulationHolder, self)

        self._effectsConfiguration = EffectTemplates(self._configurationTree, self._midiTiming, self._specialModulationHolder, 800, 600)
        self._effectsGui = EffectsGui(self._mainConfig, self._midiTiming, self._modulationGui, self._specialModulationHolder, self)
        self._fadeConfiguration = FadeTemplates(self._configurationTree, self._midiTiming, self._specialModulationHolder)
        self._fadeGui = FadeGui(self._mainConfig, self._midiTiming, self._modulationGui, self._specialModulationHolder, self)
        self._effectImagesConfiguration = EffectImageList(self._configurationTree, self._midiTiming)
        self._effectImagesGui = EffectImagesListGui(self._mainConfig, self._effectImagesConfiguration, self)

    def getSpecialModulationHolder(self):
        return self._specialModulationHolder

    def getCurveGui(self):
        return self._curveGui

    def _getConfiguration(self):
        self._timeModulationConfiguration._getConfiguration()
        self._effectsConfiguration._getConfiguration()
        self._effectImagesConfiguration._getConfiguration()
        self._fadeConfiguration._getConfiguration()

    def setupSpecialEffectModulations(self):
        self._effectsConfiguration.setupEffectModulations(self._effectsModulation)

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print "GlobalConfig config is updated..."
            self._getConfiguration()
            self._configurationTree.resetConfigurationUpdated()

    def getEffectConfiguration(self):
        return self._effectsConfiguration

    def getEffectChoices(self):
        return self._effectsConfiguration.getChoices()

    def getFadeChoices(self):
        return self._fadeConfiguration.getChoices()

    def getTimeModulationTemplate(self, configName):
        return self._timeModulationConfiguration.getTemplate(configName)

    def getTimeModulationTemplateByIndex(self, index):
        return self._timeModulationConfiguration.getTemplateByIndex(index)

    def makeTimeModulationTemplate(self, saveName, mode, modulation, rangeVal, rangeQuantize):
        return self._timeModulationConfiguration.createTemplate(saveName, mode, modulation, rangeVal, rangeQuantize)

    def deleteTimeModulationTemplate(self, configName):
        self._timeModulationConfiguration.deleteTemplate(configName)

    def duplicateTimeModulationTemplate(self, configName):
        return self._timeModulationConfiguration.duplicateTemplate(configName)

    def checkIfNameIsDefaultTimeModulationName(self, configName):
        return self._timeModulationConfiguration.checkIfNameIsDefaultName(configName)

    def getTimeModulationTemplateNamesList(self):
        return self._timeModulationConfiguration.getTemplateNamesList()

    def getTimeModulationChoices(self):
        return self._timeModulationConfiguration.getChoices()

    def setupTimeModulationsGui(self, plane, sizer, parentSizer, parentClass):
        self._timeModulationGui.setupTimeModulationGui(plane, sizer, parentSizer, parentClass)

    def setupTimeModulationsListGui(self, plane, sizer, parentSizer, parentClass):
        self._timeModulationGui.setupTimeModulationListGui(plane, sizer, parentSizer, parentClass)

    def updateTimeModulationGui(self, configName, midiNote, editFieldWidget = None):
        template = self._timeModulationConfiguration.getTemplate(configName)
        if(template != None):
            self._timeModulationGui.updateGui(template, midiNote, editFieldWidget)

    def updateTimeModulationList(self, selectedName):
        self._timeModulationGui.updateTimeModulationList(self._timeModulationConfiguration, selectedName)

    def setupEffectsGui(self, plane, sizer, parentSizer, parentClass):
        self._effectsGui.setupEffectsGui(plane, sizer, parentSizer, parentClass)

    def setupEffectsListGui(self, plane, sizer, parentSizer, parentClass):
        self._effectsGui.setupEffectsListGui(plane, sizer, parentSizer, parentClass)

    def setupEffectImageListGui(self, plane, sizer, parentSizer, parentClass):
        self._effectImagesGui.setupEffectImageListGui(plane, sizer, parentSizer, parentClass)

    def getFadeModeLists(self):
        return self._fadeGui.getFadeModeLists()

    def setupFadeGui(self, plane, sizer, parentSizer, parentClass):
        self._fadeGui.setupFadeGui(plane, sizer, parentSizer, parentClass)

    def setupFadeListGui(self, plane, sizer, parentSizer, parentClass):
        self._fadeGui.setupFadeListGui(plane, sizer, parentSizer, parentClass)

    def setupModulationGui(self, plane, sizer, parentSizer, parentClass):
        self._modulationGui.setupModulationGui(plane, sizer, parentSizer, parentClass)

    def setupEffectsSlidersGui(self, plane, sizer, parentSizer, parentClass):
        self._effectsGui.setupEffectsSlidersGui(plane, sizer, parentSizer, parentClass)

    def updateEffectsGui(self, configName, midiNote, editFieldName, editFieldWidget = None):
        template = self._effectsConfiguration.getTemplate(configName)
        if(template != None):
            self._effectsGui.updateGui(template, midiNote, editFieldName, editFieldWidget)

    def updateEffectsSliders(self, valuesString, guiString):
        self._effectsGui.updateEffectsSliders(valuesString, guiString)

    def startSlidersUpdate(self):
        self._effectsGui.startSlidersUpdate()

    def stopSlidersUpdate(self):
        self._effectsGui.stopSlidersUpdate()

    def updateEffectList(self, selectedName):
        self._effectsGui.updateEffectList(self._effectsConfiguration, selectedName)

    def updateEffectImageList(self):
        self._effectImagesGui.updateEffectImageList()

    def showSliderGuiEditButton(self, show = True):
        self._effectsGui.showSliderGuiEditButton(show)

    def updateEffectListHeight(self, height):
        self._effectsGui.updateEffectListHeight(height)

    def getDraggedFxName(self):
        fxIndex = self._effectsGui.getDraggedFxIndex()
        effect = self._effectsConfiguration.getTemplateByIndex(fxIndex)
        if(effect != None):
            return effect.getName()
        else:
            return None

    def getEffectTemplate(self, configName):
        return self._effectsConfiguration.getTemplate(configName)

    def getEffectTemplateByIndex(self, index):
        return self._effectsConfiguration.getTemplateByIndex(index)

    def makeEffectTemplate(self, saveName, effectName, ammountMod, arg1Mod, arg2Mod, arg3Mod, arg4Mod, startValuesString):
        return self._effectsConfiguration.createTemplate(saveName, effectName, ammountMod, arg1Mod, arg2Mod, arg3Mod, arg4Mod, startValuesString)

    def deleteEffectTemplate(self, configName):
        self._effectsConfiguration.deleteTemplate(configName)

    def duplicateEffectTemplate(self, configName):
        return self._effectsConfiguration.duplicateTemplate(configName)

    def getEffectTemplateNamesList(self):
        return self._effectsConfiguration.getTemplateNamesList()

    def checkIfNameIsDefaultEffectName(self, configName):
        return self._effectsConfiguration.checkIfNameIsDefaultName(configName)

    def getEffectImage(self, fileName):
        return self._effectImagesConfiguration.getTemplate(fileName)

    def getEffectImageByIndex(self, index):
        return self._effectImagesConfiguration.getTemplateByIndex(index)

    def deleteEffectImage(self, fileName):
        return self._effectImagesConfiguration.deleteTemplate(fileName)

    def makeNewEffectImage(self, fileName):
        return self._effectImagesConfiguration.createTemplate(fileName)

    def getEffectImageFileListString(self):
        return self._effectImagesConfiguration.getFileListString()

    def updateModulationGui(self, modulationString, widget, closeCallback, saveCallback, saveArgument = None):
        self._modulationGui.updateGui(modulationString, widget, closeCallback, saveCallback, saveArgument)

    def updateModulationGuiButton(self, widget, modulationString):
        self._modulationGui.updateModulationGuiButton(widget, modulationString)

    def stopModulationGui(self):
        self._modulationGui.stopModulationUpdate()

    def updateFadeGui(self, configName, editFieldName, fadeFieldWidget = None, selectedWipeMode = None, selectedWipePrePostString = None):
        template = self._fadeConfiguration.getTemplate(configName)
        if(template != None):
            self._fadeGui.updateGui(template, editFieldName, fadeFieldWidget, selectedWipeMode, selectedWipePrePostString)

    def updateFadeList(self, selectedName):
        self._fadeGui.updateFadeList(self._fadeConfiguration, selectedName)

    def updateFadeGuiButtons(self, configName, noteWipeMode, modeWidget, modulationWidget, levelWidget):
        template = self._fadeConfiguration.getTemplate(configName)
        self._fadeGui.updateFadeGuiButtons(template, noteWipeMode, modeWidget, modulationWidget, levelWidget)

    def getFadeTemplate(self, configName):
        return self._fadeConfiguration.getTemplate(configName)

    def getFadeTemplateByIndex(self, index):
        return self._fadeConfiguration.getTemplateByIndex(index)

    def makeFadeTemplate(self, saveName, wipeMode, wipePostMix, wipeSettings, fadeMod, levelMod):
        return self._fadeConfiguration.createTemplate(saveName, wipeMode, wipePostMix, wipeSettings, fadeMod, levelMod)

    def deleteFadeTemplate(self, configName):
        self._fadeConfiguration.deleteTemplate(configName)

    def duplicateFadeTemplate(self, configName):
        return self._fadeConfiguration.duplicateTemplate(configName)

    def getFadeTemplateNamesList(self):
        return self._fadeConfiguration.getTemplateNamesList()

    def checkIfNameIsDefaultFadeName(self, configName):
        return self._fadeConfiguration.checkIfNameIsDefaultName(configName)

class EffectsGui(object):
    def __init__(self, mainConfing, midiTiming, modulationGui, specialModulationHolder, globalConfig):
        self._mainConfig = mainConfing
        self._globalConfig = globalConfig
        self._midiTiming = midiTiming
        self._modulationGui = modulationGui
        self._specialModulationHolder = specialModulationHolder
        self._midiModulation = MidiModulation(None, self._midiTiming, self._specialModulationHolder)
        self._startConfigName = ""
        self._selectedEditor = self.EditSelection.Unselected
        self._effectListSelectedIndex = -1

        self._blankFxBitmap = wx.Bitmap("graphics/fxEmpty.png") #@UndefinedVariable
        self._fxBitmapBlobDetect = wx.Bitmap("graphics/fxEdge.png") #@UndefinedVariable
        self._fxBitmapBlur = wx.Bitmap("graphics/fxBlur.png") #@UndefinedVariable
        self._fxBitmapBlurMul = wx.Bitmap("graphics/fxBlurMultiply.png") #@UndefinedVariable
        self._fxBitmapFeedback = wx.Bitmap("graphics/fxFeedback.png") #@UndefinedVariable
        self._fxBitmapDelay = wx.Bitmap("graphics/fxDelay.png") #@UndefinedVariable
        self._fxBitmapColorize = wx.Bitmap("graphics/fxColorize.png") #@UndefinedVariable
        self._fxBitmapContrast = wx.Bitmap("graphics/fxContrast.png") #@UndefinedVariable
        self._fxBitmapDeSat = wx.Bitmap("graphics/fxDeSat.png") #@UndefinedVariable
        self._fxBitmapDist = wx.Bitmap("graphics/fxDist.png") #@UndefinedVariable
        self._fxBitmapEdge = wx.Bitmap("graphics/fxEdge.png") #@UndefinedVariable
        self._fxBitmapFlip = wx.Bitmap("graphics/fxFlip.png") #@UndefinedVariable
        self._fxBitmapHueSat = wx.Bitmap("graphics/fxHueSat.png") #@UndefinedVariable
        self._fxBitmapImageAdd = wx.Bitmap("graphics/fxImageAdd.png") #@UndefinedVariable
        self._fxBitmapInverse = wx.Bitmap("graphics/fxInverse.png") #@UndefinedVariable
        self._fxBitmapMirror = wx.Bitmap("graphics/fxMirror.png") #@UndefinedVariable
        self._fxBitmapPixelate = wx.Bitmap("graphics/fxPixelate.png") #@UndefinedVariable
        self._fxBitmapRays = wx.Bitmap("graphics/fxRays.png") #@UndefinedVariable
        self._fxBitmapSlitScan = wx.Bitmap("graphics/fxSlitScan.png") #@UndefinedVariable
        self._fxBitmapRotate = wx.Bitmap("graphics/fxRotate.png") #@UndefinedVariable
        self._fxBitmapScroll = wx.Bitmap("graphics/fxScroll.png") #@UndefinedVariable
        self._fxBitmapSelfDiff = wx.Bitmap("graphics/fxSelfDiff.png") #@UndefinedVariable
        self._fxBitmapStrobe = wx.Bitmap("graphics/fxStrobe.png") #@UndefinedVariable
        self._fxBitmapThreshold = wx.Bitmap("graphics/fxThreshold.png") #@UndefinedVariable
        self._fxBitmapTVNoize = wx.Bitmap("graphics/fxTVNoize.png") #@UndefinedVariable
        self._fxBitmapVal2Hue = wx.Bitmap("graphics/fxVal2Hue.png") #@UndefinedVariable
        self._fxBitmapZoom = wx.Bitmap("graphics/fxZoom.png") #@UndefinedVariable

        self._helpBitmap = wx.Bitmap("graphics/helpButton.png") #@UndefinedVariable
        self._helpPressedBitmap = wx.Bitmap("graphics/helpButtonPressed.png") #@UndefinedVariable
        self._editBitmap = wx.Bitmap("graphics/editButton.png") #@UndefinedVariable
        self._editPressedBitmap = wx.Bitmap("graphics/editButtonPressed.png") #@UndefinedVariable
        self._editSelectedBitmap = wx.Bitmap("graphics/editButtonSelected.png") #@UndefinedVariable
        self._saveBitmap = wx.Bitmap("graphics/saveButton.png") #@UndefinedVariable
        self._savePressedBitmap = wx.Bitmap("graphics/saveButtonPressed.png") #@UndefinedVariable
        self._saveGreyBitmap = wx.Bitmap("graphics/saveButtonGrey.png") #@UndefinedVariable

        self._duplicateButtonBitmap = wx.Bitmap("graphics/duplicateButton.png") #@UndefinedVariable
        self._duplicateButtonPressedBitmap = wx.Bitmap("graphics/duplicateButtonPressed.png") #@UndefinedVariable
        self._deleteButtonBitmap = wx.Bitmap("graphics/deleteButton.png") #@UndefinedVariable
        self._deleteButtonPressedBitmap = wx.Bitmap("graphics/deleteButtonPressed.png") #@UndefinedVariable

        self._editButtonBitmap = wx.Bitmap("graphics/editButtonBig.png") #@UndefinedVariable
        self._editButtonPressedBitmap = wx.Bitmap("graphics/editButtonBigPressed.png") #@UndefinedVariable
        self._resetButtonBitmap = wx.Bitmap("graphics/releaseSlidersButton.png") #@UndefinedVariable
        self._resetButtonPressedBitmap = wx.Bitmap("graphics/releaseSlidersButtonPressed.png") #@UndefinedVariable
        self._updateButtonBitmap = wx.Bitmap("graphics/setStartValuesButton.png") #@UndefinedVariable
        self._updateButtonPressedBitmap = wx.Bitmap("graphics/setStartValuesButtonPressed.png") #@UndefinedVariable

        self._closeButtonBitmap = wx.Bitmap("graphics/closeButton.png") #@UndefinedVariable
        self._closeButtonPressedBitmap = wx.Bitmap("graphics/closeButtonPressed.png") #@UndefinedVariable
        self._listButtonBitmap = wx.Bitmap("graphics/listButton.png") #@UndefinedVariable
        self._listButtonPressedBitmap = wx.Bitmap("graphics/listButtonPressed.png") #@UndefinedVariable
        self._slidersButtonBitmap = wx.Bitmap("graphics/slidersButton.png") #@UndefinedVariable
        self._slidersButtonPressedBitmap = wx.Bitmap("graphics/slidersButtonPressed.png") #@UndefinedVariable
        self._saveBigBitmap = wx.Bitmap("graphics/saveButtonBig.png") #@UndefinedVariable
        self._saveBigPressedBitmap = wx.Bitmap("graphics/saveButtonBigPressed.png") #@UndefinedVariable
        self._saveBigGreyBitmap = wx.Bitmap("graphics/saveButtonBigGrey.png") #@UndefinedVariable

        self._effectListDraggedIndex = -1
        self._midiNote = -1
        self._activeEffectId = None
        self._config = None
        self._editFieldWidget = None

    class EditSelection():
        Unselected, Ammount, Arg1, Arg2, Arg3, Arg4 = range(6)

    def setupEffectsGui(self, plane, sizer, parentSizer, parentClass):
        self._mainEffectsPlane = plane
        self._mainEffectsGuiSizer = sizer
        self._parentSizer = parentSizer
        self._showEffectsCallback = parentClass.showEffectsGui
        self._hideEffectsCallback = parentClass.hideEffectsGui
        self._fixEffectGuiLayout = parentClass.fixEffectsGuiLayout
        self._showSlidersCallback = parentClass.showSlidersGui
        self._showCurveCallback = parentClass.showCurveGui
        self._hideCurveCallback = parentClass.hideCurveGui
        self._showModulationCallback = parentClass.showModulationGui
        self._hideModulationCallback = parentClass.hideModulationGui
        self._showEffectListCallback = parentClass.showEffectList
        self._showEffectImageListCallback = parentClass.showEffectImageListGui
        self._setDragCursor = parentClass.setDragCursorCallback
        self._mediaPoolEffectNameFieldUpdateCallback = parentClass.updateEffectField
        self._trackEffectNameFieldUpdateCallback = parentClass.trackEffectFieldUpdateCallback

        self._curveGui = self._globalConfig.getCurveGui()

        headerLabel = wx.StaticText(self._mainEffectsPlane, wx.ID_ANY, "Effect configuration:") #@UndefinedVariable
        headerFont = headerLabel.GetFont()
        headerFont.SetWeight(wx.BOLD) #@UndefinedVariable
        headerLabel.SetFont(headerFont)
        self._mainEffectsGuiSizer.Add(headerLabel, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        templateNameSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText1 = wx.StaticText(self._mainEffectsPlane, wx.ID_ANY, "Name:") #@UndefinedVariable
        self._templateNameField = wx.TextCtrl(self._mainEffectsPlane, wx.ID_ANY, "MediaDefault1", size=(200, -1)) #@UndefinedVariable
        self._templateNameField.SetInsertionPoint(0)
        self._templateNameField.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        templateNameButton = PcnImageButton(self._mainEffectsPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        templateNameButton.Bind(wx.EVT_BUTTON, self._onTemplateNameHelp) #@UndefinedVariable
        templateNameSizer.Add(tmpText1, 1, wx.ALL, 5) #@UndefinedVariable
        templateNameSizer.Add(self._templateNameField, 2, wx.ALL, 5) #@UndefinedVariable
        templateNameSizer.Add(templateNameButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(templateNameSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        effectNameSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText2 = wx.StaticText(self._mainEffectsPlane, wx.ID_ANY, "Effect:") #@UndefinedVariable
        self._effectChoices = EffectTypes()
        self._effectNameField = wx.ComboBox(self._mainEffectsPlane, wx.ID_ANY, size=(200, -1), choices=["None"], style=wx.CB_READONLY) #@UndefinedVariable
        updateChoices(self._effectNameField, self._effectChoices.getChoices, "None", "None")
        effectNameButton = PcnImageButton(self._mainEffectsPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        effectNameButton.Bind(wx.EVT_BUTTON, self._onEffectHelp) #@UndefinedVariable
        effectNameSizer.Add(tmpText2, 1, wx.ALL, 5) #@UndefinedVariable
        effectNameSizer.Add(self._effectNameField, 2, wx.ALL, 5) #@UndefinedVariable
        effectNameSizer.Add(effectNameButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(effectNameSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._mainEffectsPlane.Bind(wx.EVT_COMBOBOX, self._onEffectChosen, id=self._effectNameField.GetId()) #@UndefinedVariable

        self._imagesSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._imagesLabel = wx.StaticText(self._mainEffectsPlane, wx.ID_ANY, "Image list:") #@UndefinedVariable
        self._imagesField = wx.TextCtrl(self._mainEffectsPlane, wx.ID_ANY, "", size=(200, -1)) #@UndefinedVariable
        self._imagesField.SetEditable(False)
        self._imagesField.SetBackgroundColour((232,232,232))
        self._imagesButton = PcnImageButton(self._mainEffectsPlane, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._imagesButton.Bind(wx.EVT_BUTTON, self._onImagesButton) #@UndefinedVariable
        self._imagesSizer.Add(self._imagesLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._imagesSizer.Add(self._imagesField, 2, wx.ALL, 5) #@UndefinedVariable
        self._imagesSizer.Add(self._imagesButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._imagesSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._curveSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._curveLabel = wx.StaticText(self._mainEffectsPlane, wx.ID_ANY, "Curve:") #@UndefinedVariable
        self._curveField = wx.TextCtrl(self._mainEffectsPlane, wx.ID_ANY, "Linear|0,0|255,255", size=(200, -1)) #@UndefinedVariable
#        self._curveField.SetEditable(False)
        self._curveField.SetBackgroundColour((232,232,232))
        self._curveButton = PcnImageButton(self._mainEffectsPlane, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._curveButton.Bind(wx.EVT_BUTTON, self._onCurveButton) #@UndefinedVariable
        self._curveSizer.Add(self._curveLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._curveSizer.Add(self._curveField, 2, wx.ALL, 5) #@UndefinedVariable
        self._curveSizer.Add(self._curveButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._curveSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._ammountSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._amountLabel = wx.StaticText(self._mainEffectsPlane, wx.ID_ANY, "Amount:") #@UndefinedVariable
        self._ammountField = wx.TextCtrl(self._mainEffectsPlane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._ammountField.SetInsertionPoint(0)
        self._ammountField.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        self._ammountButton = PcnImageButton(self._mainEffectsPlane, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._ammountButton.Bind(wx.EVT_BUTTON, self._onAmmountEdit) #@UndefinedVariable
        self._ammountSizer.Add(self._amountLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._ammountSizer.Add(self._ammountField, 2, wx.ALL, 5) #@UndefinedVariable
        self._ammountSizer.Add(self._ammountButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._ammountSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._arg1Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg1Label = wx.StaticText(self._mainEffectsPlane, wx.ID_ANY, "Argument 1:") #@UndefinedVariable
        self._arg1Field = wx.TextCtrl(self._mainEffectsPlane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._arg1Field.SetInsertionPoint(0)
        self._arg1Field.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        self._arg1Button = PcnImageButton(self._mainEffectsPlane, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._arg1Button.Bind(wx.EVT_BUTTON, self._onArg1Edit) #@UndefinedVariable
        self._arg1Sizer.Add(self._arg1Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg1Sizer.Add(self._arg1Field, 2, wx.ALL, 5) #@UndefinedVariable
        self._arg1Sizer.Add(self._arg1Button, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._arg1Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._arg2Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg2Label = wx.StaticText(self._mainEffectsPlane, wx.ID_ANY, "Argument 2:") #@UndefinedVariable
        self._arg2Field = wx.TextCtrl(self._mainEffectsPlane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._arg2Field.SetInsertionPoint(0)
        self._arg2Field.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        self._arg2Button = PcnImageButton(self._mainEffectsPlane, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._arg2Button.Bind(wx.EVT_BUTTON, self._onArg2Edit) #@UndefinedVariable
        self._arg2Sizer.Add(self._arg2Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg2Sizer.Add(self._arg2Field, 2, wx.ALL, 5) #@UndefinedVariable
        self._arg2Sizer.Add(self._arg2Button, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._arg2Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._arg3Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg3Label = wx.StaticText(self._mainEffectsPlane, wx.ID_ANY, "Argument 3:") #@UndefinedVariable
        self._arg3Field = wx.TextCtrl(self._mainEffectsPlane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._arg3Field.SetInsertionPoint(0)
        self._arg3Field.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        self._arg3Button = PcnImageButton(self._mainEffectsPlane, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._arg3Button.Bind(wx.EVT_BUTTON, self._onArg3Edit) #@UndefinedVariable
        self._arg3Sizer.Add(self._arg3Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg3Sizer.Add(self._arg3Field, 2, wx.ALL, 5) #@UndefinedVariable
        self._arg3Sizer.Add(self._arg3Button, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._arg3Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._arg4Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg4Label = wx.StaticText(self._mainEffectsPlane, wx.ID_ANY, "Argument 4:") #@UndefinedVariable
        self._arg4Field = wx.TextCtrl(self._mainEffectsPlane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._arg4Field.SetInsertionPoint(0)
        self._arg4Field.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        self._arg4Button = PcnImageButton(self._mainEffectsPlane, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._arg4Button.Bind(wx.EVT_BUTTON, self._onArg4Edit) #@UndefinedVariable
        self._arg4Sizer.Add(self._arg4Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg4Sizer.Add(self._arg4Field, 2, wx.ALL, 5) #@UndefinedVariable
        self._arg4Sizer.Add(self._arg4Button, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._arg4Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._conf1Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._conf1Label = wx.StaticText(self._mainEffectsPlane, wx.ID_ANY, "Config choise:") #@UndefinedVariable
        self._conf1Field = wx.ComboBox(self._mainEffectsPlane, wx.ID_ANY, size=(200, -1), choices=["None"], style=wx.CB_READONLY) #@UndefinedVariable
        self._conf1Field.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        self._conf1Button = PcnImageButton(self._mainEffectsPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._conf1HelpText = ""
        self._conf1Button.Bind(wx.EVT_BUTTON, self._onConf1Help) #@UndefinedVariable
        self._conf1Sizer.Add(self._conf1Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._conf1Sizer.Add(self._conf1Field, 2, wx.ALL, 5) #@UndefinedVariable
        self._conf1Sizer.Add(self._conf1Button, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._conf1Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._conf2Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._conf2Label = wx.StaticText(self._mainEffectsPlane, wx.ID_ANY, "Config choise:") #@UndefinedVariable
        self._conf2Field = wx.TextCtrl(self._mainEffectsPlane, wx.ID_ANY, "0.0", size=(200, -1)) #@UndefinedVariable
        self._conf2Field.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        self._conf2Button = PcnImageButton(self._mainEffectsPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._conf2HelpText = ""
        self._conf2Button.Bind(wx.EVT_BUTTON, self._onConf2Help) #@UndefinedVariable
        self._conf2Sizer.Add(self._conf2Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._conf2Sizer.Add(self._conf2Field, 2, wx.ALL, 5) #@UndefinedVariable
        self._conf2Sizer.Add(self._conf2Button, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._conf2Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        startValuesSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        startValuesLabel = wx.StaticText(self._mainEffectsPlane, wx.ID_ANY, "Start values:") #@UndefinedVariable
        self._startValuesField = wx.TextCtrl(self._mainEffectsPlane, wx.ID_ANY, "0.0|0.0|0.0|0.0|0.0", size=(200, -1)) #@UndefinedVariable
        self._startValuesField.SetInsertionPoint(0)
        self._startValuesField.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        startValuesButton = PcnImageButton(self._mainEffectsPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        startValuesButton.Bind(wx.EVT_BUTTON, self._onStartValuesHelp) #@UndefinedVariable
        startValuesSizer.Add(startValuesLabel, 1, wx.ALL, 5) #@UndefinedVariable
        startValuesSizer.Add(self._startValuesField, 2, wx.ALL, 5) #@UndefinedVariable
        startValuesSizer.Add(startValuesButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(startValuesSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = PcnImageButton(self._mainEffectsPlane, self._closeButtonBitmap, self._closeButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(55, 17)) #@UndefinedVariable
        closeButton.Bind(wx.EVT_BUTTON, self._onCloseButton) #@UndefinedVariable
        listButton = PcnImageButton(self._mainEffectsPlane, self._listButtonBitmap, self._listButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(46, 17)) #@UndefinedVariable
        listButton.Bind(wx.EVT_BUTTON, self._onListButton) #@UndefinedVariable
        slidersButton = PcnImageButton(self._mainEffectsPlane, self._slidersButtonBitmap, self._slidersButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(65, 17)) #@UndefinedVariable
        slidersButton.Bind(wx.EVT_BUTTON, self._onSlidersButton) #@UndefinedVariable
        self._saveButton = PcnImageButton(self._mainEffectsPlane, self._saveBigGreyBitmap, self._saveBigGreyBitmap, (-1, -1), wx.ID_ANY, size=(52, 17)) #@UndefinedVariable
        self._saveButton.Bind(wx.EVT_BUTTON, self._onSaveButton) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(listButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(slidersButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(self._saveButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._flipModes = FlipModes()
        self._mirrorModes = MirrorModes()
        self._blurModes = BlurModes()
        self._zoomModes = ZoomModes()
        self._scrollModes = ScrollModes()
        self._rayModes = RayModes()
        self._slitDirs = SlitDirections()
        self._distortionModes = DistortionModes()
        self._pixelateModes = PixelateModes()
        self._tvNoizeModes = TVNoizeModes()
        self._edgeModes = EdgeModes()
        self._edgeColourModes = EdgeColourModes()
        self._blobDetectModes = BlobDetectModes()
        self._desaturateModes = DesaturateModes()
        self._contrastModes = ContrastModes()
        self._hueSatModes = HueSatModes()
        self._colorizeModes = ColorizeModes()
        self._valueToHueModes = ValueToHueModes()
        self._strobeModes = StrobeModes()
        self._midiControllers = MidiControllers()

    def setupEffectsListGui(self, plane, sizer, parentSizer, parentClass):
        self._mainEffectsListPlane = plane
        self._mainEffectsListGuiSizer = sizer
        self._parentSizer = parentSizer
        self._hideEffectsListCallback = parentClass.hideEffectsListGui

        self._listImageIds = []

        self._effectImageList = wx.ImageList(32, 22) #@UndefinedVariable
        self._blankEffectIndex = self._effectImageList.Add(self._blankFxBitmap)
        self._fxIdImageIndex = []
        self._fxBitmapList = []
        index = self._effectImageList.Add(self._fxBitmapZoom)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapZoom)
        index = self._effectImageList.Add(self._fxBitmapFlip)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapFlip)
        index = self._effectImageList.Add(self._fxBitmapMirror)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapMirror)
        index = self._effectImageList.Add(self._fxBitmapRotate)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapRotate)
        index = self._effectImageList.Add(self._fxBitmapScroll)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapScroll)
        index = self._effectImageList.Add(self._fxBitmapBlur)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapBlur)
        index = self._effectImageList.Add(self._fxBitmapBlurMul)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapBlurMul)
        index = self._effectImageList.Add(self._fxBitmapFeedback)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapFeedback)
        index = self._effectImageList.Add(self._fxBitmapDelay)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapDelay)
        index = self._effectImageList.Add(self._fxBitmapRays)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapRays)
        index = self._effectImageList.Add(self._fxBitmapSlitScan)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapSlitScan)
        index = self._effectImageList.Add(self._fxBitmapSelfDiff)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapSelfDiff)
        index = self._effectImageList.Add(self._fxBitmapDist)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapDist)
        index = self._effectImageList.Add(self._fxBitmapPixelate)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapPixelate)
        index = self._effectImageList.Add(self._fxBitmapTVNoize)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapTVNoize)
        index = self._effectImageList.Add(self._fxBitmapEdge)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapEdge)
        index = self._effectImageList.Add(self._fxBitmapBlobDetect)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapBlobDetect)
        index = self._effectImageList.Add(self._fxBitmapDeSat)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapDeSat)
        index = self._effectImageList.Add(self._fxBitmapContrast)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapContrast)
        index = self._effectImageList.Add(self._fxBitmapHueSat)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapHueSat)
        index = self._effectImageList.Add(self._fxBitmapColorize)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapColorize)
        index = self._effectImageList.Add(self._fxBitmapInverse)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapInverse)
        index = self._effectImageList.Add(self._fxBitmapStrobe)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapStrobe)
        index = self._effectImageList.Add(self._fxBitmapVal2Hue)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapVal2Hue)
        index = self._effectImageList.Add(self._fxBitmapThreshold)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapThreshold)
        index = self._effectImageList.Add(self._fxBitmapImageAdd)
        self._fxIdImageIndex.append(index)
        self._fxBitmapList.append(self._fxBitmapImageAdd)

        self._modIdImageIndex = []
        for i in range(self._modulationGui.getModulationImageCount()):
            bitmap = self._modulationGui.getBigModulationImageBitmap(i)
            index = self._effectImageList.Add(bitmap)
            self._modIdImageIndex.append(index)

        headerLabel = wx.StaticText(self._mainEffectsListPlane, wx.ID_ANY, "Effect list:") #@UndefinedVariable
        headerFont = headerLabel.GetFont()
        headerFont.SetWeight(wx.BOLD) #@UndefinedVariable
        headerLabel.SetFont(headerFont)
        self._mainEffectsListGuiSizer.Add(headerLabel, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        self._oldListHeight = 376
        self._effectListWidget = ultimatelistctrl.UltimateListCtrl(self._mainEffectsListPlane, id=wx.ID_ANY, size=(340,self._oldListHeight), agwStyle = wx.LC_REPORT | wx.LC_HRULES | wx.LC_SINGLE_SEL) #@UndefinedVariable
        self._effectListWidget.SetImageList(self._effectImageList, wx.IMAGE_LIST_SMALL) #@UndefinedVariable
        self._effectListWidget.SetBackgroundColour((170,170,170))

        self._effectListWidget.InsertColumn(0, 'Name', width=150)
        self._effectListWidget.InsertColumn(1, 'Mod1', width=34)
        self._effectListWidget.InsertColumn(2, 'Mod2', width=34)
        self._effectListWidget.InsertColumn(3, 'Mod3', width=34)
        self._effectListWidget.InsertColumn(4, 'Mod4', width=34)
        self._effectListWidget.InsertColumn(5, 'Mod5', width=34)

        self._mainEffectsListGuiSizer.Add(self._effectListWidget, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._mainEffectsListPlane.Bind(ultimatelistctrl.EVT_LIST_COL_CLICK, self._onListItemMouseDown, self._effectListWidget)
        self._mainEffectsListPlane.Bind(ultimatelistctrl.EVT_LIST_ITEM_SELECTED, self._onListItemSelected, self._effectListWidget)
        self._mainEffectsListPlane.Bind(ultimatelistctrl.EVT_LIST_ITEM_DESELECTED, self._onListItemDeselected, self._effectListWidget)
        self._mainEffectsListPlane.Bind(ultimatelistctrl.EVT_LIST_BEGIN_DRAG, self._onListDragStart, self._effectListWidget)
        self._effectListWidget.Bind(wx.EVT_LEFT_DCLICK, self._onListDoubbleClick) #@UndefinedVariable

        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = PcnImageButton(self._mainEffectsListPlane, self._closeButtonBitmap, self._closeButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(55, 17)) #@UndefinedVariable
        closeButton.Bind(wx.EVT_BUTTON, self._onListCloseButton) #@UndefinedVariable
        duplicateButton = PcnImageButton(self._mainEffectsListPlane, self._duplicateButtonBitmap, self._duplicateButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(79, 17)) #@UndefinedVariable
        duplicateButton.Bind(wx.EVT_BUTTON, self._onListDuplicateButton) #@UndefinedVariable
        deleteButton = PcnImageButton(self._mainEffectsListPlane, self._deleteButtonBitmap, self._deleteButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(62, 17)) #@UndefinedVariable
        deleteButton.Bind(wx.EVT_BUTTON, self._onListDeleteButton) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(duplicateButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(deleteButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsListGuiSizer.Add(self._buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

    def _onTemplateNameHelp(self, event):
        text = """
The name of this configuration.

You will get a choice to rename or make a new template on save if you change this.
"""
        dlg = wx.MessageDialog(self._mainEffectsPlane, text, 'Template name help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onEffectHelp(self, event):
        text = """
Selects the effect.

"""
        effectChoices = self._effectChoices.getChoices()
        effectDescriptions = self._effectChoices.getDescriptions()
        for i in range(1, len(self._effectChoices.getChoices())):
            effectName = effectChoices[i]
            effectDescription = effectDescriptions[i]
            extraTab = "\t"
            if(sys.platform == "darwin"):
                if(i == 2):
                    extraTab = "\t\t"
                elif(i == 4):
                    extraTab = "\t\t"
                elif(i == 5):
                    extraTab = ""
                elif(i == 8):
                    extraTab = ""
                elif(i == 10):
                    extraTab = ""
                elif(i == 12):
                    extraTab = ""
                elif(i == 15):
                    extraTab = ""
                elif(i == 16):
                    extraTab = ""
            else:
                if(i == 5):
                    extraTab = ""
                elif(i == 10):
                    extraTab = ""
                elif(i == 12):
                    extraTab = ""
                elif(i == 15):
                    extraTab = ""
                elif(i == 16):
                    extraTab = ""
            text += effectName + ":\t" + extraTab + effectDescription + "\n"
        dlg = wx.MessageDialog(self._mainEffectsPlane, text, 'Effect help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _highlightButton(self, selected):
        if(selected == self.EditSelection.Ammount):
            self._ammountButton.setBitmaps(self._editSelectedBitmap, self._editSelectedBitmap)
        else:
            self._ammountButton.setBitmaps(self._editBitmap, self._editPressedBitmap)
        if(selected == self.EditSelection.Arg1):
            self._arg1Button.setBitmaps(self._editSelectedBitmap, self._editSelectedBitmap)
        else:
            self._arg1Button.setBitmaps(self._editBitmap, self._editPressedBitmap)
        if(selected == self.EditSelection.Arg2):
            self._arg2Button.setBitmaps(self._editSelectedBitmap, self._editSelectedBitmap)
        else:
            self._arg2Button.setBitmaps(self._editBitmap, self._editPressedBitmap)
        if(selected == self.EditSelection.Arg3):
            self._arg3Button.setBitmaps(self._editSelectedBitmap, self._editSelectedBitmap)
        else:
            self._arg3Button.setBitmaps(self._editBitmap, self._editPressedBitmap)
        if(selected == self.EditSelection.Arg4):
            self._arg4Button.setBitmaps(self._editSelectedBitmap, self._editSelectedBitmap)
        else:
            self._arg4Button.setBitmaps(self._editBitmap, self._editPressedBitmap)

    def unselectButton(self):
        self._selectedEditor = self.EditSelection.Unselected
        self._highlightButton(self._selectedEditor)

    def _onAmmountEdit(self, event):
        if(self._selectedEditor != self.EditSelection.Ammount):
            self._selectedEditor = self.EditSelection.Ammount
            self._showModulationCallback()
        else:
            self._selectedEditor = self.EditSelection.Unselected
            self._hideModulationCallback()
        self._fixEffectGuiLayout()
        self._globalConfig.updateModulationGui(self._ammountField.GetValue(), self._ammountField, self.unselectButton, None)
        self._highlightButton(self._selectedEditor)

    def _onArg1Edit(self, event):
        if(self._selectedEditor != self.EditSelection.Arg1):
            self._selectedEditor = self.EditSelection.Arg1
            self._showModulationCallback()
        else:
            self._selectedEditor = self.EditSelection.Unselected
            self._hideModulationCallback()
        self._fixEffectGuiLayout()
        self._globalConfig.updateModulationGui(self._arg1Field.GetValue(), self._arg1Field, self.unselectButton, None)
        self._highlightButton(self._selectedEditor)

    def _onArg2Edit(self, event):
        if(self._selectedEditor != self.EditSelection.Arg2):
            self._selectedEditor = self.EditSelection.Arg2
            self._showModulationCallback()
        else:
            self._selectedEditor = self.EditSelection.Unselected
            self._hideModulationCallback()
        self._fixEffectGuiLayout()
        self._globalConfig.updateModulationGui(self._arg2Field.GetValue(), self._arg2Field, self.unselectButton, None)
        self._highlightButton(self._selectedEditor)

    def _onArg3Edit(self, event):
        if(self._selectedEditor != self.EditSelection.Arg3):
            self._selectedEditor = self.EditSelection.Arg3
            self._showModulationCallback()
        else:
            self._selectedEditor = self.EditSelection.Unselected
            self._hideModulationCallback()
        self._fixEffectGuiLayout()
        self._globalConfig.updateModulationGui(self._arg3Field.GetValue(), self._arg3Field, self.unselectButton, None)
        self._highlightButton(self._selectedEditor)

    def _onArg4Edit(self, event):
        if(self._selectedEditor != self.EditSelection.Arg4):
            self._selectedEditor = self.EditSelection.Arg4
            self._showModulationCallback()
        else:
            self._selectedEditor = self.EditSelection.Unselected
            self._hideModulationCallback()
        self._fixEffectGuiLayout()
        self._globalConfig.updateModulationGui(self._arg4Field.GetValue(), self._arg4Field, self.unselectButton, None)
        self._highlightButton(self._selectedEditor)

    def _onConf1Help(self, event):
        dlg = wx.MessageDialog(self._mainEffectsPlane, self._conf1HelpText, 'Config dropdown help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onConf2Help(self, event):
        dlg = wx.MessageDialog(self._mainEffectsPlane, self._conf2HelpText, 'Config field help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onStartValuesHelp(self, event):
        text = """
A list of start values for the effect modulation.
"""
        dlg = wx.MessageDialog(self._mainEffectsPlane, text, 'Template name help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onCloseButton(self, event):
        self._selectedEditor = self.EditSelection.Unselected
        self._highlightButton(self._selectedEditor)
        self._hideSlidersCallback()
        self._hideModulationCallback()
        self._hideEffectsCallback()

    def _onListCloseButton(self, event):
        self._hideSlidersCallback()
        self._hideModulationCallback()
        self._hideEffectsCallback()
        self._hideEffectsListCallback()
        self._selectedEditor = self.EditSelection.Unselected
        self._highlightButton(self._selectedEditor)

    def _onListDuplicateButton(self, event):
        if(self._effectListSelectedIndex >= 0):
            effectTemplate = self._globalConfig.getEffectTemplateByIndex(self._effectListSelectedIndex)
            if(effectTemplate != None):
                effectName = effectTemplate.getName()
                newName = self._globalConfig.duplicateEffectTemplate(effectName)
                self._globalConfig.updateEffectList(newName)
                self._globalConfig.updateEffectsGui(newName, self._midiNote, self._activeEffectId, self._editFieldWidget)

    def _onListDeleteButton(self, event):
        if(self._effectListSelectedIndex >= 0):
            effectTemplate = self._globalConfig.getEffectTemplateByIndex(self._effectListSelectedIndex)
            if(effectTemplate != None):
                effectName = effectTemplate.getName()
                inUseNumber = self._mainConfig.countNumberOfTimeEffectTemplateUsed(effectName)
                text = "Are you sure you want to delete \"%s\"? (It is used %d times)" % (effectName, inUseNumber)
                dlg = wx.MessageDialog(self._mainEffectsListPlane, text, 'Move?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                dlg.Destroy()
                if(result == True):
                    self._globalConfig.deleteEffectTemplate(effectName)
                    self._mainConfig.verifyEffectTemplateUsed()
                    self._globalConfig.updateEffectList(None)
                    self._mainConfig.updateNoteGui()
                    self._mainConfig.updateMixerGui()

    def _onListItemMouseDown(self, event):
        self._effectListSelectedIndex = event.m_itemIndex
        self._effectListDraggedIndex = -1

    def _onListItemSelected(self, event):
        self._effectListSelectedIndex = event.m_itemIndex
        self._effectListDraggedIndex = -1

    def _onListItemDeselected(self, event):
        self._effectListDraggedIndex = -1
        self._effectListSelectedIndex = -1

    def _onListDragStart(self, event):
        self._effectListSelectedIndex = event.m_itemIndex
        self._effectListDraggedIndex = event.m_itemIndex
        bitmap = None
        if((self._effectListDraggedIndex >= 0) and (self._effectListDraggedIndex < len(self._listImageIds))):
            imageIndex = self._listImageIds[self._effectListDraggedIndex]
            if((imageIndex >= 0) and (imageIndex < len(self._fxBitmapList))):
                bitmap = self._fxBitmapList[imageIndex]
        if(bitmap == None):
            bitmap = self._blankFxBitmap
        self._setDragCursor("FX", bitmap)

    def getDraggedFxIndex(self):
        dragIndex = self._effectListDraggedIndex # Gets updated by state calls
        if(dragIndex > -1):
            self._effectListWidget.SetItemState(dragIndex, 0, ultimatelistctrl.ULC_STATE_SELECTED)
            self._effectListWidget.SetItemState(dragIndex, ultimatelistctrl.ULC_STATE_SELECTED, ultimatelistctrl.ULC_STATE_SELECTED) #@UndefinedVariable
        self._effectListWidget.SetCursor(wx.StockCursor(wx.CURSOR_ARROW)) #@UndefinedVariable
        return dragIndex

    def _onListDoubbleClick(self, event):
        self._effectListDraggedIndex = -1
        effectTemplate = self._globalConfig.getEffectTemplateByIndex(self._effectListSelectedIndex)
        if(effectTemplate != None):
            self.updateGui(effectTemplate, None, self._activeEffectId)
            self._showEffectsCallback(0)

    def _onListButton(self, event):
        effectConfigName = self._templateNameField.GetValue()
        self._globalConfig.updateEffectList(effectConfigName)
        self._showEffectListCallback()

    def _onImagesButton(self, event):
        self._globalConfig.updateEffectImageList()
        self._showEffectImageListCallback()

    def _onCurveButton(self, event):
        self._curveGui.updateGui(self._curveField.GetValue(), self._curveField, None, None, None)
        self._showCurveCallback()

    def _dialogResultCallback(self, value):
        self._dialogResult = value

    def _onSaveButton(self, event):
        saveName = self._templateNameField.GetValue()
        oldTemplate = self._globalConfig.getEffectTemplate(saveName)
        rename = False
        move = False
        moveOne = False
        cancel = False
        if(saveName != self._startConfigName):
            inUseNumber = self._mainConfig.countNumberOfTimeEffectTemplateUsed(self._startConfigName)
            
            if(oldTemplate != None):
                text = "\"%s\" already exists!!! Do you want to overwrite?" % (saveName)
                dlg = wx.MessageDialog(self._mainEffectsPlane, text, 'Overwrite?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                dlg.Destroy()
                if(result == False):
                    cancel = True
                else:
                    if(inUseNumber > 0):
                        if(self._editFieldWidget != None):
                            self._dialogResultCallback(-1)
                            text = "Do you want to move one or all instances of \"%s\"\nto the new configuration \"%s\" (%d in all)" % (self._startConfigName, saveName, inUseNumber)
                            dlg = ThreeChoiceMessageDialog(self._mainEffectsPlane, "Move?", self._dialogResultCallback, text, "One", "All", "None")
                            dlg.ShowModal()
                            dlg.Destroy()
                            if(self._dialogResult == 1):
                                moveOne = True
                            elif(self._dialogResult == 2):
                                move = True
                        else:
                            text = "Do you want to move all instances of \"%s\" to the new configuration \"%s\" (%d in all)" % (self._startConfigName, saveName, inUseNumber)
                            dlg = wx.MessageDialog(self._mainEffectsPlane, text, 'Move?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                            result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                            dlg.Destroy()
                            if(result == True):
                                move = True
                    else:
                        text = "Do you want to rename \"%s\" to the new configuration \"%s\" (a copy will be made if you select No)" % (self._startConfigName, saveName)
                        dlg = wx.MessageDialog(self._mainEffectsPlane, text, 'Rename?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                        result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                        dlg.Destroy()
                        if(result == True):
                            rename = True
            else:
                if(inUseNumber > 0):
                    if(self._editFieldWidget != None):
                        self._dialogResultCallback(-1)
                        text = "Do you want to move one or all instances of \"%s\"\nto the new configuration \"%s\" (%d in all)" % (self._startConfigName, saveName, inUseNumber)
                        dlg = ThreeChoiceMessageDialog(self._mainEffectsPlane, "Move?", self._dialogResultCallback, text, "One", "All", "None")
                        dlg.ShowModal()
                        dlg.Destroy()
                        if(self._dialogResult == 1):
                            moveOne = True
                        elif(self._dialogResult == 2):
                            move = True
                    else:
                        text = "Do you want to move all instances of \"%s\" to the new configuration \"%s\" (%d in all)" % (self._startConfigName, saveName, inUseNumber)
                        dlg = wx.MessageDialog(self._mainEffectsPlane, text, 'Move?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                        result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                        dlg.Destroy()
                        if(result == True):
                            move = True
                else:
                    text = "Do you want to rename \"%s\" to the new configuration \"%s\" (a copy will be made if you select No)" % (self._startConfigName, saveName)
                    dlg = wx.MessageDialog(self._mainEffectsPlane, text, 'Rename?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                    result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                    dlg.Destroy()
                    if(result == True):
                        rename = True
        effectName = self._effectNameField.GetValue()
        ammountMod = self._midiModulation.validateModulationString(self._ammountField.GetValue())
        arg1Mod = self._midiModulation.validateModulationString(self._arg1Field.GetValue())
        arg2Mod = self._midiModulation.validateModulationString(self._arg2Field.GetValue())
        arg3Mod = self._midiModulation.validateModulationString(self._arg3Field.GetValue())
        arg4Mod = self._midiModulation.validateModulationString(self._arg4Field.GetValue())
        startValuesString = self._startValuesField.GetValue()
        if(cancel == True):
            self._ammountField.SetValue(ammountMod)
            self._arg1Field.SetValue(arg1Mod)
            self._arg2Field.SetValue(arg2Mod)
            self._arg3Field.SetValue(arg3Mod)
            self._arg4Field.SetValue(arg4Mod)
        else:
            if(rename == True):
                oldTemplate = self._globalConfig.getEffectTemplate(self._startConfigName)
                oldTemplate.setName(saveName)
                if(move == True):
                    self._mainConfig.renameEffectTemplateUsed(self._startConfigName, saveName)
            if(oldTemplate == None):
                savedTemplate = self._globalConfig.makeEffectTemplate(saveName, effectName, ammountMod, arg1Mod, arg2Mod, arg3Mod, arg4Mod, startValuesString)
                if(move == True):
                    self._mainConfig.renameEffectTemplateUsed(self._startConfigName, saveName)
                self._mainConfig.verifyEffectTemplateUsed()
            else:
                oldTemplate.update(effectName, ammountMod, arg1Mod, arg2Mod, arg3Mod, arg4Mod, startValuesString)
                savedTemplate = oldTemplate
            savedTemplate.updateWithExtraValues((self._conf1Field.GetValue(), self._conf2Field.GetValue()))
            self.updateGui(savedTemplate, self._midiNote, self._activeEffectId, self._editFieldWidget)
            if(self._editFieldWidget != None):
                if((self._activeEffectId == "PreEffect") or (self._activeEffectId == "PostEffect")):
                    self._trackEffectNameFieldUpdateCallback(self._editFieldWidget, saveName, moveOne, self._activeEffectId)
                else:
                    self._mediaPoolEffectNameFieldUpdateCallback(self._editFieldWidget, saveName, moveOne, self._activeEffectId)
            self._mainConfig.updateNoteGui()
            self._mainConfig.updateMixerGui()
            self._globalConfig.updateEffectList(saveName)
            self._showOrHideSaveButton()

    def _onSlidersButton(self, event):
        self.showSliderGuiEditButton(False)
        self._showSlidersCallback()
        self._fixEffectGuiLayout()

    def setupEffectsSlidersGui(self, plane, sizer, parentSizer, parentClass):
        self._mainSliderSizer = sizer
        self._parentSizer = parentSizer
        self._hideSlidersCallback = parentClass.hideSlidersGui

        headerLabel = wx.StaticText(plane, wx.ID_ANY, "GUI sliders:") #@UndefinedVariable
        headerFont = headerLabel.GetFont()
        headerFont.SetWeight(wx.BOLD) #@UndefinedVariable
        headerLabel.SetFont(headerFont)
        self._mainSliderSizer.Add(headerLabel, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        self._slidersInfoLabel = wx.StaticText(plane, wx.ID_ANY, "N/A") #@UndefinedVariable
        self._mainSliderSizer.Add(self._slidersInfoLabel, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        self._ammountSliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._amountSliderLabel = wx.StaticText(plane, wx.ID_ANY, "Amount:") #@UndefinedVariable
        self._ammountSlider = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=127, size=(200, -1)) #@UndefinedVariable
        self._amountValueLabel = wx.StaticText(plane, wx.ID_ANY, "0.0", size=(30,-1)) #@UndefinedVariable
        self._ammountSliderSizer.Add(self._amountSliderLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._ammountSliderSizer.Add(self._ammountSlider, 2, wx.ALL, 5) #@UndefinedVariable
        self._ammountSliderSizer.Add(self._amountValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainSliderSizer.Add(self._ammountSliderSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._amountSliderId = self._ammountSlider.GetId()

        self._arg1SliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg1SliderLabel = wx.StaticText(plane, wx.ID_ANY, "Argument 1:") #@UndefinedVariable
        self._arg1Slider = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=127, size=(200, -1)) #@UndefinedVariable
        self._arg1ValueLabel = wx.StaticText(plane, wx.ID_ANY, "0.0", size=(30,-1)) #@UndefinedVariable
        self._arg1SliderSizer.Add(self._arg1SliderLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg1SliderSizer.Add(self._arg1Slider, 2, wx.ALL, 5) #@UndefinedVariable
        self._arg1SliderSizer.Add(self._arg1ValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainSliderSizer.Add(self._arg1SliderSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._arg1SliderId = self._arg1Slider.GetId()

        self._arg2SliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg2SliderLabel = wx.StaticText(plane, wx.ID_ANY, "Argument 2:") #@UndefinedVariable
        self._arg2Slider = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=127, size=(200, -1)) #@UndefinedVariable
        self._arg2ValueLabel = wx.StaticText(plane, wx.ID_ANY, "0.0", size=(30,-1)) #@UndefinedVariable
        self._arg2SliderSizer.Add(self._arg2SliderLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg2SliderSizer.Add(self._arg2Slider, 2, wx.ALL, 5) #@UndefinedVariable
        self._arg2SliderSizer.Add(self._arg2ValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainSliderSizer.Add(self._arg2SliderSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._arg2SliderId = self._arg2Slider.GetId()

        self._arg3SliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg3SliderLabel = wx.StaticText(plane, wx.ID_ANY, "Argument 3:") #@UndefinedVariable
        self._arg3Slider = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=127, size=(200, -1)) #@UndefinedVariable
        self._arg3ValueLabel = wx.StaticText(plane, wx.ID_ANY, "0.0", size=(30,-1)) #@UndefinedVariable
        self._arg3SliderSizer.Add(self._arg3SliderLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg3SliderSizer.Add(self._arg3Slider, 2, wx.ALL, 5) #@UndefinedVariable
        self._arg3SliderSizer.Add(self._arg3ValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainSliderSizer.Add(self._arg3SliderSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._arg3SliderId = self._arg3Slider.GetId()

        self._arg4SliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg4SliderLabel = wx.StaticText(plane, wx.ID_ANY, "Argument 4:") #@UndefinedVariable
        self._arg4Slider = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=127, size=(200, -1)) #@UndefinedVariable
        self._arg4ValueLabel = wx.StaticText(plane, wx.ID_ANY, "0.0", size=(30,-1)) #@UndefinedVariable
        self._arg4SliderSizer.Add(self._arg4SliderLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg4SliderSizer.Add(self._arg4Slider, 2, wx.ALL, 5) #@UndefinedVariable
        self._arg4SliderSizer.Add(self._arg4ValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainSliderSizer.Add(self._arg4SliderSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._arg4SliderId = self._arg4Slider.GetId()

        self._sliderButtonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = PcnImageButton(plane, self._closeButtonBitmap, self._closeButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(55, 17)) #@UndefinedVariable
        closeButton.Bind(wx.EVT_BUTTON, self._onSliderCloseButton) #@UndefinedVariable
        self._editButton = PcnImageButton(plane, self._editButtonBitmap, self._editButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(90, 17)) #@UndefinedVariable
        self._editButton.Bind(wx.EVT_BUTTON, self._onSliderEditButton) #@UndefinedVariable
        self._updateButton = PcnImageButton(plane, self._updateButtonBitmap, self._updateButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(67, 17)) #@UndefinedVariable
        self._updateButton.Bind(wx.EVT_BUTTON, self._onSliderUpdateButton) #@UndefinedVariable
        self._resetButton = PcnImageButton(plane, self._resetButtonBitmap, self._resetButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(67, 17)) #@UndefinedVariable
        self._resetButton.Bind(wx.EVT_BUTTON, self._onResetButton) #@UndefinedVariable
        self._sliderButtonsSizer.Add(closeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._sliderButtonsSizer.Add(self._editButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._sliderButtonsSizer.Hide(self._editButton)
        self._sliderButtonsSizer.Add(self._updateButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._sliderButtonsSizer.Add(self._resetButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainSliderSizer.Add(self._sliderButtonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        plane.Bind(wx.EVT_SLIDER, self._onSlide) #@UndefinedVariable

        self._effectSlidersUpdate = wx.Timer(plane, -1) #@UndefinedVariable
        plane.Bind(wx.EVT_TIMER, self._onEffectSlidersUpdate) #@UndefinedVariable

    def startSlidersUpdate(self):
        if(self._effectSlidersUpdate.IsRunning() == False):
            self._effectSlidersUpdate.Start(100)#10 times a second

    def stopSlidersUpdate(self):
        if(self._effectSlidersUpdate.IsRunning() == True):
            self._effectSlidersUpdate.Stop()

    def _onEffectSlidersUpdate(self, event):
        isChannelController = False
        if((self._activeEffectId == "PreEffect") or (self._activeEffectId == "PostEffect")):
            isChannelController = True
        midiChannel = self._mainConfig.getSelectedMidiChannel()
        if(isChannelController == True):
            if((midiChannel < 0) or (midiChannel >= 16)):
                pass
            else:
                self._mainConfig.getEffectState(midiChannel, None)
        else:
            if((midiChannel < 0) or (midiChannel >= 16)):
                midiChannel = None
            if((self._midiNote == None) or (self._midiNote < 0) or (self._midiNote >= 128)):
                pass
            else:
                self._mainConfig.getEffectState(midiChannel, self._midiNote)
    
    def _onSliderCloseButton(self, event):
        self._hideSlidersCallback()

    def _onSliderEditButton(self, event):
        selectedEditor = 0
        if(self._activeEffectId == "Effect1"):
            selectedEditor = 2
        if(self._activeEffectId == "Effect2"):
            selectedEditor = 3
        self._showEffectsCallback(selectedEditor)
        self._sliderButtonsSizer.Hide(self._editButton)
        self._sliderButtonsSizer.Show(self._updateButton)
        self._sliderButtonsSizer.Layout()

    def _onSliderUpdateButton(self, event):
        valueString = str("%.2f" % (float(self._ammountSlider.GetValue()) / 127.0))
        valueString += "|" + str("%.2f" % (float(self._arg1Slider.GetValue()) / 127.0))
        valueString += "|" + str("%.2f" % (float(self._arg2Slider.GetValue()) / 127.0))
        valueString += "|" + str("%.2f" % (float(self._arg3Slider.GetValue()) / 127.0))
        valueString += "|" + str("%.2f" % (float(self._arg4Slider.GetValue()) / 127.0))
        self._startValuesField.SetValue(valueString)

    def _onResetButton(self, event):
        midiChannel = self._mainConfig.getSelectedMidiChannel()
        baseId = 0
        if((self._activeEffectId == "Effect2") or (self._activeEffectId == "PostEffect")):
            baseId = 5
        isChannelController = False
        if((self._activeEffectId == "PreEffect") or (self._activeEffectId == "PostEffect")):
            isChannelController = True
        if((isChannelController == True) and ((midiChannel < 0) or (midiChannel >= 16))):
            print "No MIDI channel selected for channel controller message!"
        elif((isChannelController == False) and ((self._midiNote == None) or (self._midiNote < 0) or (self._midiNote >= 128))):
            print "No note selected for note controller message!"
        else:
            if(isChannelController == False):
                midiChannel = min(max(0, midiChannel), 15)
            self.sendGuiRelease(isChannelController, midiChannel, self._midiNote, baseId)

    def _onSlide(self, event):
        sliderId = event.GetEventObject().GetId()
        midiChannel = self._mainConfig.getSelectedMidiChannel()
        baseId = 0
        if((self._activeEffectId == "Effect2") or (self._activeEffectId == "PostEffect")):
            baseId = 5
        isChannelController = False
        if((self._activeEffectId == "PreEffect") or (self._activeEffectId == "PostEffect")):
            isChannelController = True
        if((isChannelController == True) and ((midiChannel < 0) or (midiChannel >= 16))):
            print "No MIDI channel selected for channel controller message!"
        elif((isChannelController == False) and ((self._midiNote == None) or (self._midiNote < 0) or (self._midiNote >= 128))):
            print "No note selected for note controller message!"
        else:
            if(isChannelController == False):
                midiChannel = min(max(0, midiChannel), 15)
            if(sliderId == self._amountSliderId):
                self.sendGuiController(isChannelController, midiChannel, self._midiNote, baseId, self._ammountSlider.GetValue())
            elif(sliderId == self._arg1SliderId):
                self.sendGuiController(isChannelController, midiChannel, self._midiNote, baseId+1, self._arg1Slider.GetValue())
            elif(sliderId == self._arg2SliderId):
                self.sendGuiController(isChannelController, midiChannel, self._midiNote, baseId+2, self._arg2Slider.GetValue())
            elif(sliderId == self._arg3SliderId):
                self.sendGuiController(isChannelController, midiChannel, self._midiNote, baseId+3, self._arg3Slider.GetValue())
            elif(sliderId == self._arg4SliderId):
                self.sendGuiController(isChannelController, midiChannel, self._midiNote, baseId+4, self._arg4Slider.GetValue())
        self._updateValueLabels(False)

    def _onEffectChosen(self, event):
        selectedEffectId = self._effectNameField.GetSelection()
        self._setEffect(getEffectName(selectedEffectId-1))
        self._showOrHideSaveButton()

    def sendGuiRelease(self, isChannelController, channel, note, guiControllerId):
        guiControllerId = (guiControllerId & 0x0f)
        if(isChannelController == True):
            command = 0xc0
            note = 0
        else:
            command = 0xd0
        command += guiControllerId
        midiSender = self._mainConfig.getMidiSender()
        midiSender.sendGuiRelease(channel, note, command)

    def sendGuiController(self, isChannelController, channel, note, guiControllerId, value):
        guiControllerId = (guiControllerId & 0x0f)
        if(isChannelController == True):
            command = 0xe0
            note = 0
        else:
            command = 0xf0
        command += guiControllerId
        midiSender = self._mainConfig.getMidiSender()
        midiSender.sendGuiController(channel, note, command, value)

#    def sendMidi(self, channel, controllerDescription, value):
#        midiSender = self._mainConfig.getMidiSender()
#        if(controllerDescription.startswith("MidiChannel.")):
#            descriptionSplit = controllerDescription.split('.', 6)
#            if(len(descriptionSplit) > 1):
#                if(descriptionSplit[1] == "Controller"):
#                    if(len(descriptionSplit) > 2):
#                        controllerId = self._midiControllers.getId(descriptionSplit[2])
#                        midiSender.sendMidiController(channel, controllerId, value)
#                elif(descriptionSplit[1] == "PitchBend"):
#                    midiSender.sendPitchbend(channel, value)
#                elif(descriptionSplit[1] == "Aftertouch"):
#                    midiSender.sendAftertouch(channel, value)
#        if(controllerDescription.startswith("MidiNote.")):
#            descriptionSplit = controllerDescription.split('.', 6)
#            if(len(descriptionSplit) > 1):
#                if((descriptionSplit[1] == "NotePreasure") or (descriptionSplit[1] == "Preasure")):
#                    if(self._midiNote != None):
#                        midiSender.sendPolyPreasure(self._mainConfig.getSelectedMidiChannel(), self._midiNote, value)

    def _setLabels(self, amountLabel, arg1Label, arg2Label, arg3Label, arg4Label, config1config = None, config2config = None):
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
        if(config1config != None):
            configLabel, configChoisesFunction, configvalue, configdefaultChoise, configHelpText = config1config
            self._mainEffectsGuiSizer.Show(self._conf1Sizer)
            self._conf1Label.SetLabel(configLabel)
            updateChoices(self._conf1Field, configChoisesFunction, configvalue, configdefaultChoise)
            self._conf1HelpText = configHelpText
        else:
            self._mainEffectsGuiSizer.Hide(self._conf1Sizer)
        if(config2config != None):
            configLabel, configvalue, configHelpText = config2config
            self._mainEffectsGuiSizer.Show(self._conf2Sizer)
            self._conf2Label.SetLabel(configLabel)
            self._conf2Field.SetValue(configvalue)
            self._conf2HelpText = configHelpText
        else:
            self._mainEffectsGuiSizer.Hide(self._conf2Sizer)
        self._fixEffectGuiLayout()

    def _updateValueLabels(self, updateSliderValues):
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
        if(updateSliderValues == True):
            isChannelController = False
            if((self._activeEffectId == "PreEffect") or (self._activeEffectId == "PostEffect")):
                isChannelController = True
            if(isChannelController == True):
                midiChannel = self._mainConfig.getSelectedMidiChannel()
                if((midiChannel < 0) or (midiChannel >= 16)):
                    self._slidersInfoLabel.SetLabel("No MIDI channel selected for channel controller message!")
                else:
                    self._mainConfig.getEffectState(midiChannel, None)
                    self._slidersInfoLabel.SetLabel(self._activeEffectId + " on channel " + str(midiChannel))
            else:
                if((self._midiNote == None) or (self._midiNote < 0) or (self._midiNote >= 128)):
                    self._slidersInfoLabel.SetLabel("No note selected for note controller message!")
                else:
                    self._mainConfig.getEffectState(None, self._midiNote)
                    self._slidersInfoLabel.SetLabel(self._activeEffectId + " for note " + noteToNoteString(self._midiNote))

    def updateEffectsSliders(self, valuesString, guiString):
        if(valuesString == None or valuesString == "None"):
            values = (0.0, 0.0, 0.0, 0.0, 0.0)
        else:
            valueSplit = valuesString.split(';')
            if((self._activeEffectId == "Effect2") or (self._activeEffectId == "PostEffect")):
                activeValueString = valueSplit[1]
            else:
                activeValueString = valueSplit[0]
            values = tuple(float(v) for v in re.findall("[0-9]+.[0-9]+", activeValueString))
#        print "DEBUG values: " + str(values)
        calcValue = int(127.0 * values[0])
        self._ammountSlider.SetValue(calcValue)
        calcValue = int(127.0 * values[1])
        self._arg1Slider.SetValue(calcValue)
        calcValue = int(127.0 * values[2])
        self._arg2Slider.SetValue(calcValue)
        calcValue = int(127.0 * values[3])
        self._arg3Slider.SetValue(calcValue)
        calcValue = int(127.0 * values[4])
        self._arg4Slider.SetValue(calcValue)
        self._updateValueLabels(False)

    def _setupValueLabels(self, amount=None, arg1=None, arg2=None, arg3=None, arg4=None):
        self._ammountValueLabels = amount
        self._arg1ValueLabels = arg1
        self._arg2ValueLabels = arg2
        self._arg3ValueLabels = arg3
        self._arg4ValueLabels = arg4

    def _tryToGetConfigValue(self, name, defaultValue):
        if(self._config != None):
            value = self._config.getValue(name)
            if(value != None):
                return value
        return defaultValue

    def _updateLabels(self):            
        if(self._chosenEffectId == EffectTypes.Zoom):
            config1helpText = "Selects zoom mode.\n"
            config1helpText += "\n"
            config1helpText += "Full mode enables zoom and movement the rest are just plain zoom modes.\n"
            config1config = "Zoom mode", self._zoomModes.getChoices, self._tryToGetConfigValue("ZoomMode", "In"), "In", config1helpText
            config2helpText = "Sets zoom out and zoom in range.\n"
            config2helpText += "\n"
            config2helpText += "Default is 0.25|4.0\n"
            config2helpText += "\n"
            config2helpText += "0.25 -> zoom out to a quarter of original size.\n"
            config2helpText += "4.00 -> zoom in to four times the original size.\n"
            config2config = "Zoom range", self._tryToGetConfigValue("ZoomRange", "0.25|4.0"), config2helpText
            self._setLabels("Amount:", "X position", "Y position", "Flip", "Flip angle", config1config, config2config)
            self._setupValueLabels(None, None, None, None, None)
        elif(self._chosenEffectId == EffectTypes.Scroll):
            self._setLabels("X amount:", "Y amount", "Scroll mode", None, None)
            self._setupValueLabels(None, None, self._scrollModes.getChoices(), None, None)
        elif(self._chosenEffectId == EffectTypes.Flip):
            self._setLabels("Flip mode:", None, None, None, None)
            self._setupValueLabels(None, None, None, None, None)
        elif(self._chosenEffectId == EffectTypes.Mirror):
            self._setLabels("Mirror mode:", "Angle", "Move center", "Move angle", None)
            self._setupValueLabels(self._mirrorModes.getChoices(), None, None, None, None)
        elif(self._chosenEffectId == EffectTypes.Rotate):
            self._setLabels("Angle", "Move center", "Move angle", "Zoom", None)
            self._setupValueLabels(None, None, None, None, None)
        elif(self._chosenEffectId == EffectTypes.Blur):
            self._setLabels("Amount:", None, None, None, None)
            self._setupValueLabels(None, None, None, None, None)#self._blurModes.getChoices()
        elif(self._chosenEffectId == EffectTypes.BlurContrast):
            self._setLabels("Amount:", None, None, None, None)
            self._setupValueLabels(None, None, None, None, None)
        elif(self._chosenEffectId == EffectTypes.Feedback):
            config2helpText = "Sets up advanced zoom options.\n"
            config2helpText += "\n"
            config2helpText += "Default is 1.0|0.0|0.0|0.0 (Zoom only.)\n"
            config2helpText += "\n"
            config2helpText += "First number is zoom amount.\n"
            config2helpText += "\t1.0 = use full zoom range.\n"
            config2helpText += "Second number is rotation amount.\n"
            config2helpText += "\t1.0 = rotate 360 degrees.\n"
            config2helpText += "Thirt number is flip amount around X-axis.\n"
            config2helpText += "\t1.0 = flip 360 degrees.\n"
            config2helpText += "Forth number rotates the flip axis around Z-axis.\n"
            config2helpText += "\t1.0 = rotate 360 degrees.\n"
            config2config = "Advanced zoom values", self._tryToGetConfigValue("FeedbackAdvancedZoom", "1.0|0.0|0.0|0.0"), config2helpText
            self._setLabels("Feedback:", "Inversion:", "Move:", "Angle:", "Zoom:", None, config2config)
            self._setupValueLabels(None, None, None, None, None)
        elif(self._chosenEffectId == EffectTypes.Delay):
            config2helpText = "Sets up advanced zoom options.\n"
            config2helpText += "\n"
            config2helpText += "Default is 1.0|0.0|0.0|0.0 (Zoom only.)\n"
            config2helpText += "\n"
            config2helpText += "First number is zoom amount.\n"
            config2helpText += "\t1.0 = use full zoom range.\n"
            config2helpText += "Second number is rotation amount.\n"
            config2helpText += "\t1.0 = rotate 360 degrees.\n"
            config2helpText += "Thirt number is flip amount around X-axis.\n"
            config2helpText += "\t1.0 = flip 360 degrees.\n"
            config2helpText += "Forth number rotates the flip axis around Z-axis.\n"
            config2helpText += "\t1.0 = rotate 360 degrees.\n"
            config2config = "Advanced zoom values", self._tryToGetConfigValue("FeedbackAdvancedZoom", "1.0|0.0|0.0|0.0"), config2helpText
            self._setLabels("Feedback:", "LumaKey:", "Move:", "Angle:", "Zoom:", None, config2config)
            self._setupValueLabels(None, None, None, None, None)
        elif(self._chosenEffectId == EffectTypes.Rays):
            self._setLabels("Amount:", "Bend", "Mode:", "Horizontal:", None)
            self._setupValueLabels(None, None, self._rayModes.getChoices(), None, None)
        elif(self._chosenEffectId == EffectTypes.SlitScan):
            self._setLabels("Slit size:", "Draw pos:", "Source pos", "Direction", "Mix")
            self._setupValueLabels(None, None, None, self._slitDirs.getChoices(), None)
        elif(self._chosenEffectId == EffectTypes.SelfDifference):
            self._setLabels("Delay:", "Contrast:", "Invert:", "Smooth:", None)
            self._setupValueLabels(None, None, None, None, None)
        elif(self._chosenEffectId == EffectTypes.Distortion):
            self._setLabels("Distortion amount:", "Distortion mode", None, None, None)
            self._setupValueLabels(None, self._distortionModes.getChoices(), None, None, None)
        elif(self._chosenEffectId == EffectTypes.Pixelate):
            self._setLabels("Pixel size:", "Pixel mode", "Colour reduce", None, None)
            self._setupValueLabels(None, self._pixelateModes.getChoices(), None, None, None)
        elif(self._chosenEffectId == EffectTypes.TVNoize):
            self._setLabels("Noize amount:", "Noize scale", "Scale mode", None, None)
            self._setupValueLabels(None, None, self._tvNoizeModes.getChoices(), None, None)
        elif(self._chosenEffectId == EffectTypes.Edge):
            config1config = "Input mode:", self._edgeColourModes.getChoices, self._tryToGetConfigValue("EdgeChannelMode", "Value"), "Value", "Selects value (B/W), saturation or hue (colour) channel as input to edge detector."
            self._setLabels("Amount:", "Edge mode", "Line color:", "Line saturation", "LineWidth", config1config)
            self._setupValueLabels(None, self._edgeModes.getChoices(), None, None, None)
        elif(self._chosenEffectId == EffectTypes.BlobDetect):
            self._setLabels("Amount:", "Mode", "Line color:", "Line saturation", "LineWeight")
            self._setupValueLabels(None, self._blobDetectModes.getChoices(), None, None, None)
        elif(self._chosenEffectId == EffectTypes.Desaturate):
            self._setLabels("Colour:", "Range", "Mode", None, None)
            self._setupValueLabels(None, None, self._desaturateModes.getChoices(), None, None)
        elif(self._chosenEffectId == EffectTypes.Contrast):
            self._setLabels("Contrast:", "Brightness", "Mode", None, None)
            self._setupValueLabels(None, None, self._contrastModes.getChoices(), None, None)
        elif(self._chosenEffectId == EffectTypes.HueSaturation):
            self._setLabels("Colour rotate:", "Saturation", "Brightness", "Mode", None)
            self._setupValueLabels(None, None, None, self._hueSatModes.getChoices(), None)
        elif(self._chosenEffectId == EffectTypes.Colorize):
            self._setLabels("Amount:", "Red", "Green", "Blue", "Mode")
            self._setupValueLabels(None, None, None, None, self._colorizeModes.getChoices())
        elif(self._chosenEffectId == EffectTypes.Invert):
            self._setLabels("Amount:", None, None, None, None)
            self._setupValueLabels(None, None, None, None, None)
        elif(self._chosenEffectId == EffectTypes.Strobe):
            self._setLabels("Amount:", "Speed:", "Mode:", None, None)
            self._setupValueLabels(None, None, self._strobeModes.getChoices(), None, None)
        elif(self._chosenEffectId == EffectTypes.ValueToHue):
            self._setLabels("Mode:", "Colour rotate:", "Saturation:", None, None)
            self._setupValueLabels(self._valueToHueModes.getChoices(), None, None, None, None)
        elif(self._chosenEffectId == EffectTypes.Threshold):
            self._setLabels("Threshold:", None, None, None, None)
            self._setupValueLabels(None, None, None, None, None)
        elif(self._chosenEffectId == EffectTypes.ImageAdd):
            self._setLabels("MaskId:", "ImageId", "Mode", None, None)
            self._setupValueLabels(None, None, None, None, None)
        else:
            self._setLabels("Amount:", "Argument 1:", "Argument 2:", "Argument 3:", "Argument 4:")
            self._setupValueLabels(None, None, None, None, None)
        if(self._chosenEffectId == EffectTypes.ImageAdd):
            self._mainEffectsGuiSizer.Show(self._imagesSizer)
        else:
            self._mainEffectsGuiSizer.Hide(self._imagesSizer)
        self._updateValueLabels(True)

    def _checkIfUpdated(self):
        if(self._config == None):
            return False
        print "DEBUG pcn: cu 1"
        guiName = self._templateNameField.GetValue()
        configName = self._config.getValue("Name")
        if(guiName != configName):
            print "DEBUG pcn: diff 1"
            return True
        guiEffect = self._effectNameField.GetValue()
        configEffect = self._config.getValue("Effect")
        if(guiEffect != configEffect):
            print "DEBUG pcn: diff 2 " + str((guiEffect, configEffect))
            return True
        else:
            print "DEBUG pcn: eq 2 " + str((guiEffect, configEffect))
        guiArg = self._ammountField.GetValue()
        configArg = self._config.getValue("Amount")
        if(guiArg != configArg):
            print "DEBUG pcn: diff 3 " + str((guiArg, configArg))
            return True
        guiArg = self._arg1Field.GetValue()
        configArg = self._config.getValue("Arg1")
        if(guiArg != configArg):
            print "DEBUG pcn: diff 4"
            return True
        guiArg = self._arg2Field.GetValue()
        configArg = self._config.getValue("Arg2")
        if(guiArg != configArg):
            print "DEBUG pcn: diff 5"
            return True
        guiArg = self._arg3Field.GetValue()
        configArg = self._config.getValue("Arg3")
        if(guiArg != configArg):
            print "DEBUG pcn: diff 6"
            return True
        guiArg = self._arg4Field.GetValue()
        configArg = self._config.getValue("Arg4")
        if(guiArg != configArg):
            print "DEBUG pcn: diff 7"
            return True
        guiStart = self._startValuesField.GetValue()
        configStart = self._config.getValue("StartValues")
        if(guiStart != configStart):
            print "DEBUG pcn: diff 8"
            return True
        if(configEffect == "Zoom"):
            config1Val = self._config.getValue("ZoomMode")
            gui1Val = self._conf1Field.GetValue()
            if(gui1Val != config1Val):
                print "DEBUG pcn: diff z1"
                return True
            config2Val = self._config.getValue("ZoomRange")
            gui2Val = self._conf2Field.GetValue()
            if(gui2Val != config2Val):
                print "DEBUG pcn: diff z2"
                return True
        elif((configEffect == "Feedback") or (configEffect == "Delay")):
            config2Val = self._config.getValue("FeedbackAdvancedZoom")
            gui2Val = self._conf2Field.GetValue()
            if(gui2Val != config2Val):
                print "DEBUG pcn: diff f1"
                return True
        elif(configEffect == "Edge"):
            config1Val = self._config.getValue("EdgeChannelMode")
            gui1Val = self._conf1Field.GetValue()
            if(gui1Val != config1Val):
                print "DEBUG pcn: diff e1"
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

    def _setEffect(self, value):
        if(value == None):
            self._chosenEffectId = -1
            self._chosenEffect = "None"
        else:
            self._chosenEffectId = getEffectId(value)
            self._chosenEffect = getEffectName(self._chosenEffectId)
        updateChoices(self._effectNameField, self._effectChoices.getChoices, self._chosenEffect, "None")
        self._updateLabels()
        self._fixEffectGuiLayout()

    def updateEffectList(self, effectConfiguration, selectedName):
        self._effectListWidget.DeleteAllItems()
        self._listImageIds = []
        selectedIndex = -1
        for effectConfig in effectConfiguration.getList():
            config = effectConfig.getConfigHolder()
            effectName = config.getValue("Effect")
            effectId = getEffectId(effectName)
            if(effectId != None):
                bitmapId = self._fxIdImageIndex[effectId]
            else:
                bitmapId = self._blankEffectIndex
            self._listImageIds.append(effectId)
            configName = effectConfig.getName()
            index = self._effectListWidget.InsertImageStringItem(sys.maxint, configName, bitmapId)
            if(configName == selectedName):
                selectedIndex = index
            modulationString = config.getValue("Amount")
            modBitmapId = self._modulationGui.getModulationImageId(modulationString)
            imageId = self._modIdImageIndex[modBitmapId]
            self._effectListWidget.SetStringItem(index, 1, "", imageId)
            modulationString = config.getValue("Arg1")
            modBitmapId = self._modulationGui.getModulationImageId(modulationString)
            imageId = self._modIdImageIndex[modBitmapId]
            self._effectListWidget.SetStringItem(index, 2, "", imageId)
            modulationString = config.getValue("Arg2")
            modBitmapId = self._modulationGui.getModulationImageId(modulationString)
            imageId = self._modIdImageIndex[modBitmapId]
            self._effectListWidget.SetStringItem(index, 3, "", imageId)
            modulationString = config.getValue("Arg3")
            modBitmapId = self._modulationGui.getModulationImageId(modulationString)
            imageId = self._modIdImageIndex[modBitmapId]
            self._effectListWidget.SetStringItem(index, 4, "", imageId)
            modulationString = config.getValue("Arg4")
            modBitmapId = self._modulationGui.getModulationImageId(modulationString)
            imageId = self._modIdImageIndex[modBitmapId]
            self._effectListWidget.SetStringItem(index, 5, "", imageId)

            if(index % 2):
                self._effectListWidget.SetItemBackgroundColour(index, wx.Colour(170,170,170)) #@UndefinedVariable
            else:
                self._effectListWidget.SetItemBackgroundColour(index, wx.Colour(190,190,190)) #@UndefinedVariable
        if(selectedIndex > -1):
            self._effectListSelectedIndex = selectedIndex
            self._effectListWidget.Focus(selectedIndex)
            self._effectListWidget.Update()
            self._effectListWidget.Select(selectedIndex)

    def showSliderGuiEditButton(self, show):
        if(show == True):
            self._sliderButtonsSizer.Show(self._editButton)
            self._sliderButtonsSizer.Hide(self._updateButton)
        else:
            self._sliderButtonsSizer.Hide(self._editButton)
            self._sliderButtonsSizer.Show(self._updateButton)
        self._sliderButtonsSizer.Layout()

    def updateEffectListHeight(self, height):
        pass
#        if((self._oldListHeight != height) and (height >= 100)):
#            self._effectListWidget.SetSize((340, height))
#            self._buttonPlane.SetPosition((0,height + 5))
##            self._mainEffectsListPlane.SetSize((340,height+40))
#            self._oldListHeight = height

    def updateGui(self, effectTemplate, midiNote, editFieldName, editFieldWidget = None):
#        print "DEBUG pcn: updateGui() template xml:"
#        print effectTemplate.getXmlString()
#        print "x"*120
        self._midiNote = midiNote
        self._activeEffectId = editFieldName
        self._editFieldWidget = editFieldWidget
        self._config = effectTemplate.getConfigHolder()
        self._startConfigName = self._config.getValue("Name")
        self._templateNameField.SetValue(self._startConfigName)
        self._setEffect(self._config.getValue("Effect"))
        self._imagesField.SetValue(self._globalConfig.getEffectImageFileListString())
        self._ammountField.SetValue(self._config.getValue("Amount"))
        self._arg1Field.SetValue(self._config.getValue("Arg1"))
        self._arg2Field.SetValue(self._config.getValue("Arg2"))
        self._arg3Field.SetValue(self._config.getValue("Arg3"))
        self._arg4Field.SetValue(self._config.getValue("Arg4"))
        self._startValuesField.SetValue(self._config.getValue("StartValues"))
        self._sliderButtonsSizer.Hide(self._editButton)
        self._sliderButtonsSizer.Show(self._updateButton)
        self._sliderButtonsSizer.Layout()

class FadeGui(object):
    def __init__(self, mainConfing, midiTiming, modulationGui, specialModulationHolder, globalConfig):
        self._mainConfig = mainConfing
        self._globalConfig = globalConfig
        self._midiTiming = midiTiming
        self._specialModulationHolder = specialModulationHolder
        self._modulationGui = modulationGui
        self._midiModulation = MidiModulation(None, self._midiTiming, self._specialModulationHolder)
        self._startConfigName = ""
        self._selectedEditor = self.EditSelected.Unselected
        self._wipeModesHolder = WipeMode()
        self._fadeListSelectedIndex = -1

        self._blankWipeBitmap = wx.Bitmap("graphics/modeEmpty.png") #@UndefinedVariable
        self._wipeDefaultBitmap = wx.Bitmap("graphics/wipeDefault.png") #@UndefinedVariable
        self._wipeFadeBitmap = wx.Bitmap("graphics/wipeFade.png") #@UndefinedVariable
        self._wipePushBitmap = wx.Bitmap("graphics/wipePush.png") #@UndefinedVariable
        self._wipeNoizeBitmap = wx.Bitmap("graphics/wipeNoize.png") #@UndefinedVariable
        self._wipeZoomBitmap = wx.Bitmap("graphics/wipeZoom.png") #@UndefinedVariable
        self._wipeFlipBitmap = wx.Bitmap("graphics/wipeFlip.png") #@UndefinedVariable

        self._helpBitmap = wx.Bitmap("graphics/helpButton.png") #@UndefinedVariable
        self._helpPressedBitmap = wx.Bitmap("graphics/helpButtonPressed.png") #@UndefinedVariable
        self._editBitmap = wx.Bitmap("graphics/editButton.png") #@UndefinedVariable
        self._editPressedBitmap = wx.Bitmap("graphics/editButtonPressed.png") #@UndefinedVariable
        self._editSelectedBitmap = wx.Bitmap("graphics/editButtonSelected.png") #@UndefinedVariable
        self._saveBitmap = wx.Bitmap("graphics/saveButton.png") #@UndefinedVariable
        self._savePressedBitmap = wx.Bitmap("graphics/saveButtonPressed.png") #@UndefinedVariable
        self._saveGreyBitmap = wx.Bitmap("graphics/saveButtonGrey.png") #@UndefinedVariable

        self._duplicateButtonBitmap = wx.Bitmap("graphics/duplicateButton.png") #@UndefinedVariable
        self._duplicateButtonPressedBitmap = wx.Bitmap("graphics/duplicateButtonPressed.png") #@UndefinedVariable
        self._deleteButtonBitmap = wx.Bitmap("graphics/deleteButton.png") #@UndefinedVariable
        self._deleteButtonPressedBitmap = wx.Bitmap("graphics/deleteButtonPressed.png") #@UndefinedVariable

        self._closeButtonBitmap = wx.Bitmap("graphics/closeButton.png") #@UndefinedVariable
        self._closeButtonPressedBitmap = wx.Bitmap("graphics/closeButtonPressed.png") #@UndefinedVariable
        self._listButtonBitmap = wx.Bitmap("graphics/listButton.png") #@UndefinedVariable
        self._listButtonPressedBitmap = wx.Bitmap("graphics/listButtonPressed.png") #@UndefinedVariable
        self._saveBigBitmap = wx.Bitmap("graphics/saveButtonBig.png") #@UndefinedVariable
        self._saveBigPressedBitmap = wx.Bitmap("graphics/saveButtonBigPressed.png") #@UndefinedVariable
        self._saveBigGreyBitmap = wx.Bitmap("graphics/saveButtonBigGrey.png") #@UndefinedVariable

        self._wipeModeImages = [self._wipeDefaultBitmap, self._wipeFadeBitmap, self._wipePushBitmap, self._wipeNoizeBitmap, self._wipeZoomBitmap, self._wipeFlipBitmap]
        self._wipeModeLabels = self._wipeModesHolder.getChoices()
        self._config = None
        self._fadeFieldWidget = None
        self._fadeFieldName = ""

    def getFadeModeLists(self):
        return (self._wipeModeImages, self._wipeModeLabels)

    class EditSelected():
        Unselected, Fade, Level = range(3)

    def setupFadeGui(self, plane, sizer, parentSizer, parentClass):
        self._mainFadeGuiPlane = plane
        self._mainFadeGuiSizer = sizer
        self._parentSizer = parentSizer
        self._hideFadeCallback = parentClass.hideFadeGui
        self._showFadeCallback = parentClass.showFadeGui
        self._showFadeListCallback = parentClass.showFadeListGui
        self._showModulationCallback = parentClass.showModulationGui
        self._hideModulationCallback = parentClass.hideModulationGui
        self._fixEffectGuiLayout = parentClass.fixEffectsGuiLayout
        self._mediaPoolFadeNameFieldUpdateCallback = parentClass.updateFadeField

        headerLabel = wx.StaticText(self._mainFadeGuiPlane, wx.ID_ANY, "Fade configuration:") #@UndefinedVariable
        headerFont = headerLabel.GetFont()
        headerFont.SetWeight(wx.BOLD) #@UndefinedVariable
        headerLabel.SetFont(headerFont)
        self._mainFadeGuiSizer.Add(headerLabel, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        templateNameSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText1 = wx.StaticText(self._mainFadeGuiPlane, wx.ID_ANY, "Name:") #@UndefinedVariable
        self._templateNameField = wx.TextCtrl(self._mainFadeGuiPlane, wx.ID_ANY, "Default", size=(200, -1)) #@UndefinedVariable
        self._templateNameField.SetInsertionPoint(0)
        self._templateNameField.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        templateNameSizer.Add(tmpText1, 1, wx.ALL, 5) #@UndefinedVariable
        templateNameSizer.Add(self._templateNameField, 2, wx.ALL, 5) #@UndefinedVariable
        self._mainFadeGuiSizer.Add(templateNameSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        fadeModeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText2 = wx.StaticText(self._mainFadeGuiPlane, wx.ID_ANY, "Wipe mode:") #@UndefinedVariable
        self._wipeModesField = wx.ComboBox(self._mainFadeGuiPlane, wx.ID_ANY, size=(200, -1), choices=["Fade"], style=wx.CB_READONLY) #@UndefinedVariable
        updateChoices(self._wipeModesField, self._wipeModesHolder.getChoices, "Fade", "Fade")
        self._wipeModesField.Bind(wx.EVT_COMBOBOX, self._onUpdate) #@UndefinedVariable
        fadeModeButton = PcnImageButton(self._mainFadeGuiPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        fadeModeButton.Bind(wx.EVT_BUTTON, self._onWipeModeHelp) #@UndefinedVariable
        fadeModeSizer.Add(tmpText2, 1, wx.ALL, 5) #@UndefinedVariable
        fadeModeSizer.Add(self._wipeModesField, 2, wx.ALL, 5) #@UndefinedVariable
        fadeModeSizer.Add(fadeModeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainFadeGuiSizer.Add(fadeModeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._mainFadeGuiPlane.Bind(wx.EVT_COMBOBOX, self._onFadeModeChosen, id=self._wipeModesField.GetId()) #@UndefinedVariable

        self._fadeModulationSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText3 = wx.StaticText(self._mainFadeGuiPlane, wx.ID_ANY, "ADSR modulation:") #@UndefinedVariable
        self._fadeModulationField = wx.TextCtrl(self._mainFadeGuiPlane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._fadeModulationField.SetInsertionPoint(0)
        self._fadeModulationField.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        self._fadeModulationButton = PcnImageButton(self._mainFadeGuiPlane, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._fadeModulationButton.Bind(wx.EVT_BUTTON, self._onFadeModulationEdit) #@UndefinedVariable
        self._fadeModulationSizer.Add(tmpText3, 1, wx.ALL, 5) #@UndefinedVariable
        self._fadeModulationSizer.Add(self._fadeModulationField, 2, wx.ALL, 5) #@UndefinedVariable
        self._fadeModulationSizer.Add(self._fadeModulationButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainFadeGuiSizer.Add(self._fadeModulationSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        levelModulationSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText3 = wx.StaticText(self._mainFadeGuiPlane, wx.ID_ANY, "Level modulation:") #@UndefinedVariable
        self._levelModulationField = wx.TextCtrl(self._mainFadeGuiPlane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._levelModulationField.SetInsertionPoint(0)
        self._levelModulationField.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        self._levelModulationButton = PcnImageButton(self._mainFadeGuiPlane, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._levelModulationButton.Bind(wx.EVT_BUTTON, self._onLevelModulationEdit) #@UndefinedVariable
        levelModulationSizer.Add(tmpText3, 1, wx.ALL, 5) #@UndefinedVariable
        levelModulationSizer.Add(self._levelModulationField, 2, wx.ALL, 5) #@UndefinedVariable
        levelModulationSizer.Add(self._levelModulationButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainFadeGuiSizer.Add(levelModulationSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._wipePostMixSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._wipePostMixLabel = wx.StaticText(self._mainFadeGuiPlane, wx.ID_ANY, "Wipe Pre/Post:") #@UndefinedVariable
        self._wipePostMixField = wx.ComboBox(self._mainFadeGuiPlane, wx.ID_ANY, size=(200, -1), choices=["Pre", "Post"], style=wx.CB_READONLY) #@UndefinedVariable
        updateChoices(self._wipePostMixField, self._getWipePostMixChoises, "Pre", "Pre")
        self._wipePostMixField.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        self._wipePostMixButton = PcnImageButton(self._mainFadeGuiPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._wipePostMixHelpText = ""
        self._wipePostMixButton.Bind(wx.EVT_BUTTON, self._onWipePostHelp) #@UndefinedVariable
        self._wipePostMixSizer.Add(self._wipePostMixLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._wipePostMixSizer.Add(self._wipePostMixField, 2, wx.ALL, 5) #@UndefinedVariable
        self._wipePostMixSizer.Add(self._wipePostMixButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainFadeGuiSizer.Add(self._wipePostMixSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._wipeSettingsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._wipeSettingsLabel = wx.StaticText(self._mainFadeGuiPlane, wx.ID_ANY, "Wipe settings:") #@UndefinedVariable
        self._wipeSettingsField = wx.TextCtrl(self._mainFadeGuiPlane, wx.ID_ANY, "0.0", size=(200, -1)) #@UndefinedVariable
        self._wipeSettingsField.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        self._wipeSettingsButton = PcnImageButton(self._mainFadeGuiPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._wipeSettingsHelpText = ""
        self._wipeSettingsButton.Bind(wx.EVT_BUTTON, self._onWipeSettingsHelp) #@UndefinedVariable
        self._wipeSettingsSizer.Add(self._wipeSettingsLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._wipeSettingsSizer.Add(self._wipeSettingsField, 2, wx.ALL, 5) #@UndefinedVariable
        self._wipeSettingsSizer.Add(self._wipeSettingsButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainFadeGuiSizer.Add(self._wipeSettingsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable


        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = PcnImageButton(self._mainFadeGuiPlane, self._closeButtonBitmap, self._closeButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(55, 17)) #@UndefinedVariable
        closeButton.Bind(wx.EVT_BUTTON, self._onCloseButton) #@UndefinedVariable
        listButton = PcnImageButton(self._mainFadeGuiPlane, self._listButtonBitmap, self._listButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(46, 17)) #@UndefinedVariable
        listButton.Bind(wx.EVT_BUTTON, self._onListButton) #@UndefinedVariable
        self._saveButton = PcnImageButton(self._mainFadeGuiPlane, self._saveBigGreyBitmap, self._saveBigGreyBitmap, (-1, -1), wx.ID_ANY, size=(52, 17)) #@UndefinedVariable
        self._saveButton.Bind(wx.EVT_BUTTON, self._onSaveButton) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 1, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(listButton, 1, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(self._saveButton, 1, wx.ALL, 5) #@UndefinedVariable
        self._mainFadeGuiSizer.Add(self._buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

    def _getWipePostMixChoises(self):
        return ["Pre", "Post"]

    def setupFadeListGui(self, plane, sizer, parentSizer, parentClass):
        self._mainFadeListPlane = plane
        self._mainFadeListGuiSizer = sizer
        self._parentSizer = parentSizer
        self._hideFadeListCallback = parentClass.hideFadeListGui

        self._fadeImageList = wx.ImageList(25, 16) #@UndefinedVariable

        self._modeIdImageIndex = []
        index = self._fadeImageList.Add(self._wipeDefaultBitmap)
        self._modeIdImageIndex.append(index)
        index = self._fadeImageList.Add(self._wipeFadeBitmap)
        self._modeIdImageIndex.append(index)
        index = self._fadeImageList.Add(self._wipePushBitmap)
        self._modeIdImageIndex.append(index)
        index = self._fadeImageList.Add(self._wipeNoizeBitmap)
        self._modeIdImageIndex.append(index)
        index = self._fadeImageList.Add(self._wipeZoomBitmap)
        self._modeIdImageIndex.append(index)
        index = self._fadeImageList.Add(self._wipeFlipBitmap)
        self._modeIdImageIndex.append(index)

        self._modIdImageIndex = []
        for i in range(self._modulationGui.getModulationImageCount()):
            bitmap = self._modulationGui.getModulationImageBitmap(i)
            index = self._fadeImageList.Add(bitmap)
            self._modIdImageIndex.append(index)

        headerLabel = wx.StaticText(self._mainFadeListPlane, wx.ID_ANY, "Fade list:") #@UndefinedVariable
        headerFont = headerLabel.GetFont()
        headerFont.SetWeight(wx.BOLD) #@UndefinedVariable
        headerLabel.SetFont(headerFont)
        self._mainFadeListGuiSizer.Add(headerLabel, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

#        self._oldListHeight = 376
        self._fadeListWidget = ultimatelistctrl.UltimateListCtrl(self._mainFadeListPlane, id=wx.ID_ANY, size=(325,376), agwStyle = wx.LC_REPORT | wx.LC_HRULES | wx.LC_SINGLE_SEL) #@UndefinedVariable
        self._fadeListWidget.SetImageList(self._fadeImageList, wx.IMAGE_LIST_SMALL) #@UndefinedVariable
        self._fadeListWidget.SetBackgroundColour((170,170,170))

        self._fadeListWidget.InsertColumn(0, 'Name', width=150)
        self._fadeListWidget.InsertColumn(1, 'Fade', width=34)
        self._fadeListWidget.InsertColumn(2, 'Level', width=36)
        self._fadeListWidget.InsertColumn(3, 'Mix', width=36)
        self._fadeListWidget.InsertColumn(4, 'Settings', width=56)

        self._mainFadeListGuiSizer.Add(self._fadeListWidget, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._mainFadeListPlane.Bind(ultimatelistctrl.EVT_LIST_COL_CLICK, self._onListItemMouseDown, self._fadeListWidget)
        self._mainFadeListPlane.Bind(ultimatelistctrl.EVT_LIST_ITEM_SELECTED, self._onListItemSelected, self._fadeListWidget)
        self._mainFadeListPlane.Bind(ultimatelistctrl.EVT_LIST_ITEM_DESELECTED, self._onListItemDeselected, self._fadeListWidget)
#        self._mainFadeListPlane.Bind(ultimatelistctrl.EVT_LIST_BEGIN_DRAG, self._onListDragStart, self._fadeListWidget)
        self._fadeListWidget.Bind(wx.EVT_LEFT_DCLICK, self._onListDoubbleClick) #@UndefinedVariable

        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = PcnImageButton(self._mainFadeListPlane, self._closeButtonBitmap, self._closeButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(55, 17)) #@UndefinedVariable
        closeButton.Bind(wx.EVT_BUTTON, self._onListCloseButton) #@UndefinedVariable
        duplicateButton = PcnImageButton(self._mainFadeListPlane, self._duplicateButtonBitmap, self._duplicateButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(79, 17)) #@UndefinedVariable
        duplicateButton.Bind(wx.EVT_BUTTON, self._onListDuplicateButton) #@UndefinedVariable
        deleteButton = PcnImageButton(self._mainFadeListPlane, self._deleteButtonBitmap, self._deleteButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(62, 17)) #@UndefinedVariable
        deleteButton.Bind(wx.EVT_BUTTON, self._onListDeleteButton) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(duplicateButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(deleteButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainFadeListGuiSizer.Add(self._buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

    def _onFadeModeChosen(self, event):
        pass

    def _onWipeModeHelp(self, event):
        text = """
Decides how we fade or wipe in this media or track.

Default:\tUse media mode or fade if no other is selected.
Fade:\tCrossfade mode.
Push:\tPush image from one of four sides.
Noize:\tDisolve with TV noize.
Zoom:\tZoom image to infinity.
Flip:\tFlip image around X ot Y axis.
"""
        dlg = wx.MessageDialog(self._mainFadeGuiPlane, text, 'Wipe mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _highlightButton(self, selected):
        if(selected == self.EditSelected.Fade):
            self._fadeModulationButton.setBitmaps(self._editSelectedBitmap, self._editSelectedBitmap)
        else:
            self._fadeModulationButton.setBitmaps(self._editBitmap, self._editPressedBitmap)
        if(selected == self.EditSelected.Level):
            self._levelModulationButton.setBitmaps(self._editSelectedBitmap, self._editSelectedBitmap)
        else:
            self._levelModulationButton.setBitmaps(self._editBitmap, self._editPressedBitmap)

    def unselectButton(self):
        self._selectedEditor = self.EditSelected.Unselected
        self._highlightButton(self._selectedEditor)

    def _onFadeModulationEdit(self, event):
        if(self._selectedEditor != self.EditSelected.Fade):
            self._selectedEditor = self.EditSelected.Fade
            self._showModulationCallback()
        else:
            self._selectedEditor = self.EditSelected.Unselected
            self._hideModulationCallback()
        self._fixEffectGuiLayout()
        self._globalConfig.updateModulationGui(self._fadeModulationField.GetValue(), self._fadeModulationField, self.unselectButton, None)
        self._highlightButton(self._selectedEditor)

    def _onLevelModulationEdit(self, event):
        if(self._selectedEditor != self.EditSelected.Level):
            self._selectedEditor = self.EditSelected.Level
            self._showModulationCallback()
        else:
            self._selectedEditor = self.EditSelected.Unselected
            self._hideModulationCallback()
        self._fixEffectGuiLayout()
        self._globalConfig.updateModulationGui(self._levelModulationField.GetValue(), self._levelModulationField, self.unselectButton, None)
        self._highlightButton(self._selectedEditor)

    def _onWipePostHelp(self, event):
        text = """
Decides if the wipe happend before or after the mixing stage.

It only affects wipes that move the images.
"""
        dlg = wx.MessageDialog(self._mainFadeGuiPlane, text, 'Wipe pre/post help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onWipeSettingsHelp(self, event):
        wipeModeString = self._wipeModesField.GetValue()
        wipeModeId = self._wipeModesHolder.findMode(wipeModeString)
        if(wipeModeId == WipeMode.Push):
            text = """
Sets witch way the image gets pushed.

<0.25 is to the left
<0.50 is to the top
<0.75 is to the right
>0.75 is to the bottom
"""
        elif(wipeModeId == WipeMode.Zoom):
            text = """
Sets x/y position of where the zoom ends.

0.5|0.5 is in the middle of the screen.
0.0|0.0 is in the bottom left corner.
0.0|1.0 is in the top left corner.
1.0|1.0 is in the top right corner.
1.0|0.0 is in the bottom right corner.
"""
        elif(wipeModeId == WipeMode.Noize):
            text = """
Sets the size of the noize particles.
"""
        else:
            text = "Help text is missing for " + str(wipeModeString) + " in _onWipeSettingsHelp()"
        dlg = wx.MessageDialog(self._mainFadeGuiPlane, text, 'Wipe settings help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onCloseButton(self, event):
        self._hideFadeCallback()
        self._hideModulationCallback()
        self._selectedEditor = self.EditSelected.Unselected
        self._highlightButton(self._selectedEditor)

    def _onListCloseButton(self, event):
        self._hideModulationCallback()
        self._hideFadeCallback()
        self._hideFadeListCallback()
        self._selectedEditor = self.EditSelected.Unselected
        self._highlightButton(self._selectedEditor)

    def _onListDuplicateButton(self, event):
        if(self._fadeListSelectedIndex >= 0):
            fadeTemplate = self._globalConfig.getFadeTemplateByIndex(self._fadeListSelectedIndex)
            if(fadeTemplate != None):
                fadeName = fadeTemplate.getName()
                newName = self._globalConfig.duplicateFadeTemplate(fadeName)
                self._globalConfig.updateFadeList(newName)
                self._globalConfig.updateFadeGui(newName, self._fadeFieldName, self._fadeFieldWidget)

    def _onListDeleteButton(self, event):
        if(self._fadeListSelectedIndex >= 0):
            fadeTemplate = self._globalConfig.getFadeTemplateByIndex(self._fadeListSelectedIndex)
            if(fadeTemplate != None):
                fadeName = fadeTemplate.getName()
                inUseNumber = self._mainConfig.countNumberOfTimeFadeTemplateUsed(fadeName)
                text = "Are you sure you want to delete \"%s\"? (It is used %d times)" % (fadeName, inUseNumber)
                dlg = wx.MessageDialog(self._mainFadeListPlane, text, 'Move?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                dlg.Destroy()
                if(result == True):
                    self._globalConfig.deleteFadeTemplate(fadeName)
                    self._mainConfig.verifyFadeTemplateUsed()
                    self._globalConfig.updateFadeList(None)
                    self._mainConfig.updateNoteGui()
                    self._mainConfig.updateMixerGui()

    def _onListItemMouseDown(self, event):
        self._fadeListSelectedIndex = event.m_itemIndex
        self._fadeListDraggedIndex = -1

    def _onListItemSelected(self, event):
        self._fadeListSelectedIndex = event.m_itemIndex
        self._fadeListDraggedIndex = -1

    def _onListItemDeselected(self, event):
        self._fadeListDraggedIndex = -1
        self._fadeListSelectedIndex = -1

    def _onListDragStart(self, event):
        self._fadeListSelectedIndex = event.m_itemIndex
        self._fadeListDraggedIndex = event.m_itemIndex
        self._setDragCursor("Fade")

    def getDraggedFxIndex(self):
        dragIndex = self._fadeListDraggedIndex # Gets updated by state calls
        if(dragIndex > -1):
            self._fadeListWidget.SetItemState(dragIndex, 0, wx.LIST_STATE_SELECTED) #@UndefinedVariable
            self._fadeListWidget.SetItemState(dragIndex, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED) #@UndefinedVariable
        self._fadeListWidget.SetCursor(wx.StockCursor(wx.CURSOR_ARROW)) #@UndefinedVariable
        return dragIndex

    def _onListDoubbleClick(self, event):
        self._fadeListDraggedIndex = -1
        fadeTemplate = self._globalConfig.getFadeTemplateByIndex(self._fadeListSelectedIndex)
        if(fadeTemplate != None):
            self.updateGui(fadeTemplate, None)
            self._showFadeCallback()

    def _onListButton(self, event):
        fadeConfigName = self._templateNameField.GetValue()
        self._globalConfig.updateFadeList(fadeConfigName)
        self._showFadeListCallback()

    def _dialogResultCallback(self, value):
        self._dialogResult = value

    def _onSaveButton(self, event):
        saveName = self._templateNameField.GetValue()
        oldTemplate = self._globalConfig.getFadeTemplate(saveName)
        rename = False
        renameOne = False
        cancel = False
        if(saveName != self._startConfigName):
            inUseNumber = self._mainConfig.countNumberOfTimeFadeTemplateUsed(self._startConfigName)
            
            if(oldTemplate != None):
                text = "\"%s\" already exists!!! Do you want to overwrite?" % (saveName)
                dlg = wx.MessageDialog(self._mainFadeGuiPlane, text, 'Overwrite?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                dlg.Destroy()
                if(result == False):
                    cancel = True
                else:
                    if(self._fadeFieldWidget != None):
                        self._dialogResultCallback(-1)
                        text = "Do you want to move one or all instances of \"%s\"\nto the new configuration \"%s\" (%d in all)" % (self._startConfigName, saveName, inUseNumber)
                        dlg = ThreeChoiceMessageDialog(self._mainFadeGuiPlane, "Move?", self._dialogResultCallback, text, "One", "All", "None")
                        dlg.ShowModal()
                        dlg.Destroy()
                        if(self._dialogResult == 1):
                            renameOne = True
                        elif(self._dialogResult == 2):
                            rename = True
                    else:
                        text = "Do you want to move all instances of \"%s\" to the new configuration \"%s\" (%d in all)" % (self._startConfigName, saveName, inUseNumber)
                        dlg = wx.MessageDialog(self._mainFadeGuiPlane, text, 'Move?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                        result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                        dlg.Destroy()
                        if(result == True):
                            rename = True
            else:
                if(self._fadeFieldWidget != None):
                    self._dialogResultCallback(-1)
                    text = "Do you want to move one or all instances of \"%s\"\nto the new configuration \"%s\" (%d in all)" % (self._startConfigName, saveName, inUseNumber)
                    dlg = ThreeChoiceMessageDialog(self._mainFadeGuiPlane, "Move?", self._dialogResultCallback, text, "One", "All", "None")
                    dlg.ShowModal()
                    dlg.Destroy()
                    if(self._dialogResult == 1):
                        renameOne = True
                    elif(self._dialogResult == 2):
                        rename = True
                else:
                    text = "Do you want to move all instances of \"%s\" to the new configuration \"%s\" (%d in all)" % (self._startConfigName, saveName, inUseNumber)
                    dlg = wx.MessageDialog(self._mainFadeGuiPlane, text, 'Move?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                    result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                    dlg.Destroy()
                    if(result == True):
                        rename = True
        wipeModeString = self._wipeModesField.GetValue()
        fadeMod = self._midiModulation.validateModulationString(self._fadeModulationField.GetValue())
        levelMod = self._midiModulation.validateModulationString(self._levelModulationField.GetValue())
        wipePostMixString = self._wipePostMixField.GetValue()
        if(wipePostMixString == "Post"):
            wipePostMix = True
        else:
            wipePostMix = False
        wipeSettingsString = self._wipeSettingsField.GetValue()
        if(cancel == True):
            self._wipeModesField.SetValue(wipeModeString)
            self._fadeModulationField.SetValue(fadeMod)
            self._levelModulationField.SetValue(levelMod)
        else:
            wipeModeId = self._wipeModesHolder.findMode(wipeModeString)
            wipeSettings = FadeSettings.getVerifiedWipeSettingsFromString(wipeSettingsString, wipeModeId)
            if(oldTemplate == None):
                savedTemplate = self._globalConfig.makeFadeTemplate(saveName, wipeModeId, wipePostMix, wipeSettings, fadeMod, levelMod)
                if(rename == True):
                    self._mainConfig.renameFadeTemplateUsed(self._startConfigName, saveName)
                self._mainConfig.verifyFadeTemplateUsed()
            else:
                oldTemplate.update(wipeModeId, wipePostMix, wipeSettings, fadeMod, levelMod)
                savedTemplate = oldTemplate
            self.updateGui(savedTemplate, self._fadeFieldName, self._fadeFieldWidget)
            if(self._fadeFieldWidget != None):
                if((self._fadeFieldName == "Track")):
                    self._trackFadeNameFieldUpdateCallback(self._fadeFieldWidget, saveName, renameOne)
                else:
                    self._mediaPoolFadeNameFieldUpdateCallback(self._fadeFieldWidget, saveName, renameOne)
            if(self._fadeFieldWidget != None):
                self._mediaPoolFadeNameFieldUpdateCallback(self._fadeFieldWidget, saveName, renameOne)
            self._mainConfig.updateNoteGui()
            self._mainConfig.updateMixerGui()
            self._globalConfig.updateFadeList(saveName)

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

    def _checkIfUpdated(self):
        if(self._config == None):
            return False
        guiName = self._templateNameField.GetValue()
        configName = self._config.getValue("Name")
        if(guiName != configName):
            return True
        guiMode = self._wipeModesField.GetValue()
        configMode = self._config.getValue("WipeMode")
        if(guiMode != configMode):
            return True
        guiModulation = self._fadeModulationField.GetValue()
        configModulation = self._config.getValue("Modulation")
        if(guiModulation != configModulation):
            return True
        guiLevel = self._levelModulationField.GetValue()
        configLevel = self._config.getValue("Level")
        if(guiLevel != configLevel):
            return True
        guiWipePostMixString = self._wipePostMixField.GetValue()
        if(guiWipePostMixString == "Post"):
            guiWipePostMix = True
        else:
            guiWipePostMix = False
        configWipePostMix = self._config.getValue("WipePostMix")
        if(guiWipePostMix != configWipePostMix):
            return True
        guiWipeSettings = self._wipeSettingsField.GetValue()
        configWipeSettings = self._config.getValue("WipeSettings")
        if(guiWipeSettings != configWipeSettings):
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

    def updateWipeModeThumb(self, widget, wipeMode):
        if(wipeMode == None):
            widget.setBitmaps(self._blankWipeBitmap, self._blankWipeBitmap)
        elif(wipeMode == WipeMode.Default):
            widget.setBitmaps(self._wipeDefaultBitmap, self._wipeDefaultBitmap)
        elif(wipeMode == WipeMode.Fade):
            widget.setBitmaps(self._wipeFadeBitmap, self._wipeFadeBitmap)
        elif(wipeMode == WipeMode.Push):
            widget.setBitmaps(self._wipePushBitmap, self._wipePushBitmap)
        elif(wipeMode == WipeMode.Noize):
            widget.setBitmaps(self._wipeNoizeBitmap, self._wipeNoizeBitmap)
        elif(wipeMode == WipeMode.Zoom):
            widget.setBitmaps(self._wipeZoomBitmap, self._wipeZoomBitmap)
        elif(wipeMode == WipeMode.Flip):
            widget.setBitmaps(self._wipeFlipBitmap, self._wipeFlipBitmap)
        else:
            widget.setBitmaps(self._wipeDefaultBitmap, self._wipeDefaultBitmap)

    def updateFadeGuiButtons(self, fadeTemplate, noteWipeMode, modeWidget, modulationWidget = None, levelWidget = None):
        if(fadeTemplate == None):
            self.updateWipeModeThumb(modeWidget, None)
            if(modulationWidget != None):
                self._globalConfig.updateModulationGuiButton(modulationWidget, "None")
            if(levelWidget != None):
                self._globalConfig.updateModulationGuiButton(levelWidget, "None")
        else:
            config = fadeTemplate.getConfigHolder()
            wipeMode, wipePostMix, _ = fadeTemplate.getWipeConfigValues(False)
            if(noteWipeMode != None):
                if(wipeMode == WipeMode.Default):
                    wipeMode = noteWipeMode
            self.updateWipeModeThumb(modeWidget, wipeMode)
            if(modulationWidget != None):
                fadeModulation = config.getValue("Modulation")
                self._globalConfig.updateModulationGuiButton(modulationWidget, fadeModulation)
            if(levelWidget != None):
                fadeLevel = config.getValue("Level")
                self._globalConfig.updateModulationGuiButton(levelWidget, fadeLevel)

    def updateFadeList(self, fadeConfiguration, selectedName):
        self._fadeListWidget.DeleteAllItems()
        selectedIndex = -1
        for fadeConfig in fadeConfiguration.getList():
            wipeModeId, wipePostMix, wipeSettings = fadeConfig.getWipeConfigValues(True)
            config = fadeConfig.getConfigHolder()
            bitmapId = self._modeIdImageIndex[wipeModeId]
            configName = fadeConfig.getName()
            index = self._fadeListWidget.InsertImageStringItem(sys.maxint, configName, bitmapId)
            if(configName == selectedName):
                selectedIndex = index
            modulationString = config.getValue("Modulation")
            modBitmapId = self._modulationGui.getModulationImageId(modulationString)
            imageId = self._modIdImageIndex[modBitmapId]
            self._fadeListWidget.SetStringItem(index, 1, "", imageId)
            modulationString = config.getValue("Level")
            modBitmapId = self._modulationGui.getModulationImageId(modulationString)
            imageId = self._modIdImageIndex[modBitmapId]
            self._fadeListWidget.SetStringItem(index, 2, "", imageId)
            if(wipePostMix == True):
                self._fadeListWidget.SetStringItem(index, 3, "Post")
            else:
                self._fadeListWidget.SetStringItem(index, 3, "Pre")
            self._fadeListWidget.SetStringItem(index, 4, wipeSettings)

            if(index % 2):
                self._fadeListWidget.SetItemBackgroundColour(index, wx.Colour(170,170,170)) #@UndefinedVariable
            else:
                self._fadeListWidget.SetItemBackgroundColour(index, wx.Colour(190,190,190)) #@UndefinedVariable
        if(selectedIndex > -1):
            self._fadeListSelectedIndex = selectedIndex
            self._fadeListWidget.Select(selectedIndex)

    def updateGui(self, fadeTemplate, fadeFieldName, fadeFieldWidget = None, selectedWipeMode = None, selectedWipePrePostString = None):
        self._config = fadeTemplate.getConfigHolder()
        self._selectedEditor = self.EditSelected.Unselected
        self._fadeFieldName = fadeFieldName
        self._fadeFieldWidget = fadeFieldWidget
        self._highlightButton(self._selectedEditor)
        self._startConfigName = self._config.getValue("Name")
        self._templateNameField.SetValue(self._startConfigName)
        self._fadeModulationField.SetValue(self._config.getValue("Modulation"))
        if(fadeFieldName == "Track"):
            self._mainFadeGuiSizer.Hide(self._fadeModulationSizer)
        else:
            self._mainFadeGuiSizer.Show(self._fadeModulationSizer)
        self._mainFadeGuiSizer.Layout()
        self._levelModulationField.SetValue(self._config.getValue("Level"))
        wipeMode, wipePostMix, wipeSettings = fadeTemplate.getWipeConfigValues(True)
        if(selectedWipeMode != None):
            wipeModeString = selectedWipeMode
        else:
            wipeModeString = self._wipeModesHolder.getNames(wipeMode)
        updateChoices(self._wipeModesField, self._wipeModesHolder.getChoices, wipeModeString, "Default")
        if(selectedWipePrePostString != None):
            wipePostMixString = selectedWipePrePostString
        else:
            if(wipePostMix == True):
                wipePostMixString = "Post"
            else:
                wipePostMixString = "Pre"
        updateChoices(self._wipePostMixField, self._getWipePostMixChoises, wipePostMixString, "Pre")
        self._wipeSettingsField.SetValue(wipeSettings)
        if(self._fadeFieldName == "Modulation"):
            self._selectedEditor = self.EditSelected.Fade
            self._highlightButton(self._selectedEditor)
            self._globalConfig.updateModulationGui(self._fadeModulationField.GetValue(), self._fadeModulationField, self.unselectButton, self._onSaveButton)
        if(self._fadeFieldName == "Level"):
            self._selectedEditor = self.EditSelected.Level
            self._highlightButton(self._selectedEditor)
            self._globalConfig.updateModulationGui(self._levelModulationField.GetValue(), self._levelModulationField, self.unselectButton, self._onSaveButton)

        self._showOrHideSaveButton()

class TimeModulationGui(object):
    def __init__(self, mainConfing, midiTiming, modulationGui, specialModulationHolder, globalConfig):
        self._mainConfig = mainConfing
        self._globalConfig = globalConfig
        self._midiTiming = midiTiming
        self._specialModulationHolder = specialModulationHolder
        self._modulationGui = modulationGui
        self._midiModulation = MidiModulation(None, self._midiTiming, self._specialModulationHolder)
        self._startConfigName = ""
        self._selectedEditor = self.EditSelected.Unselected
        self._timeModes = TimeModulationMode()
        self._timeModListSelectedIndex = -1

        self._timeOffBitmap = wx.Bitmap("graphics/modulationBlank.png") #@UndefinedVariable
        self._timeSpeedBitmap = wx.Bitmap("graphics/timeModSpeed.png") #@UndefinedVariable
        self._timeJumpBitmap = wx.Bitmap("graphics/timeModJump.png") #@UndefinedVariable
        self._timeLoopBitmap = wx.Bitmap("graphics/timeModLoop.png") #@UndefinedVariable

        self._helpBitmap = wx.Bitmap("graphics/helpButton.png") #@UndefinedVariable
        self._helpPressedBitmap = wx.Bitmap("graphics/helpButtonPressed.png") #@UndefinedVariable
        self._editBitmap = wx.Bitmap("graphics/editButton.png") #@UndefinedVariable
        self._editPressedBitmap = wx.Bitmap("graphics/editButtonPressed.png") #@UndefinedVariable
        self._editSelectedBitmap = wx.Bitmap("graphics/editButtonSelected.png") #@UndefinedVariable
        self._saveBitmap = wx.Bitmap("graphics/saveButton.png") #@UndefinedVariable
        self._savePressedBitmap = wx.Bitmap("graphics/saveButtonPressed.png") #@UndefinedVariable
        self._saveGreyBitmap = wx.Bitmap("graphics/saveButtonGrey.png") #@UndefinedVariable

        self._duplicateButtonBitmap = wx.Bitmap("graphics/duplicateButton.png") #@UndefinedVariable
        self._duplicateButtonPressedBitmap = wx.Bitmap("graphics/duplicateButtonPressed.png") #@UndefinedVariable
        self._deleteButtonBitmap = wx.Bitmap("graphics/deleteButton.png") #@UndefinedVariable
        self._deleteButtonPressedBitmap = wx.Bitmap("graphics/deleteButtonPressed.png") #@UndefinedVariable

        self._closeButtonBitmap = wx.Bitmap("graphics/closeButton.png") #@UndefinedVariable
        self._closeButtonPressedBitmap = wx.Bitmap("graphics/closeButtonPressed.png") #@UndefinedVariable
        self._listButtonBitmap = wx.Bitmap("graphics/listButton.png") #@UndefinedVariable
        self._listButtonPressedBitmap = wx.Bitmap("graphics/listButtonPressed.png") #@UndefinedVariable
        self._saveBigBitmap = wx.Bitmap("graphics/saveButtonBig.png") #@UndefinedVariable
        self._saveBigPressedBitmap = wx.Bitmap("graphics/saveButtonBigPressed.png") #@UndefinedVariable
        self._saveBigGreyBitmap = wx.Bitmap("graphics/saveButtonBigGrey.png") #@UndefinedVariable

        self._modeImages = [self._timeOffBitmap, self._timeSpeedBitmap, self._timeJumpBitmap, self._timeLoopBitmap]
        self._modeLabels = self._timeModes.getChoices()
        self._config = None
        self._midiNote = -1
        self._editFieldWidget = None

    def getModeLists(self):
        return (self._modeImages, self._modeLabels)

    class EditSelected():
        Unselected, Mode = range(2)

    def setupTimeModulationGui(self, plane, sizer, parentSizer, parentClass):
        self._mainTimeModulationGuiPlane = plane
        self._mainTimeModulationGuiSizer = sizer
        self._parentSizer = parentSizer
        self._hideTimeModulationCallback = parentClass.hideTimeModulationGui
        self._showTimeModulationCallback = parentClass.showTimeModulationGui
        self._fixEffectGuiLayout = parentClass.fixEffectsGuiLayout
        self._showTimeModulationListCallback = parentClass.showTimeModulationListGui
        self._showModulationCallback = parentClass.showModulationGui
        self._hideModulationCallback = parentClass.hideModulationGui
        self._fixTimeModulationGuiLayout = parentClass.fixTimeModulationGuiLayout
        self._timeModulationNameFieldUpdateCallback = parentClass.updateTimeModulationField

        headerLabel = wx.StaticText(self._mainTimeModulationGuiPlane, wx.ID_ANY, "Time Modulation configuration:") #@UndefinedVariable
        headerFont = headerLabel.GetFont()
        headerFont.SetWeight(wx.BOLD) #@UndefinedVariable
        headerLabel.SetFont(headerFont)
        self._mainTimeModulationGuiSizer.Add(headerLabel, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        templateNameSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText1 = wx.StaticText(self._mainTimeModulationGuiPlane, wx.ID_ANY, "Name:") #@UndefinedVariable
        self._templateNameField = wx.TextCtrl(self._mainTimeModulationGuiPlane, wx.ID_ANY, "Default", size=(200, -1)) #@UndefinedVariable
        self._templateNameField.SetInsertionPoint(0)
        self._templateNameField.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        templateNameSizer.Add(tmpText1, 1, wx.ALL, 5) #@UndefinedVariable
        templateNameSizer.Add(self._templateNameField, 2, wx.ALL, 5) #@UndefinedVariable
        self._mainTimeModulationGuiSizer.Add(templateNameSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        timeModulationModeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText2 = wx.StaticText(self._mainTimeModulationGuiPlane, wx.ID_ANY, "Mode:") #@UndefinedVariable
        self._timeModulationModesField = wx.ComboBox(self._mainTimeModulationGuiPlane, wx.ID_ANY, size=(200, -1), choices=["SpeedModulation"], style=wx.CB_READONLY) #@UndefinedVariable
        updateChoices(self._timeModulationModesField, self._timeModes.getChoices, "SpeedModulation", "SpeedModulation")
        self._timeModulationModesField.Bind(wx.EVT_COMBOBOX, self._onTimeModulationModeChosen) #@UndefinedVariable
        timeModulationModeButton = PcnImageButton(self._mainTimeModulationGuiPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        timeModulationModeButton.Bind(wx.EVT_BUTTON, self._onTimeModulationModeHelp) #@UndefinedVariable
        timeModulationModeSizer.Add(tmpText2, 1, wx.ALL, 5) #@UndefinedVariable
        timeModulationModeSizer.Add(self._timeModulationModesField, 2, wx.ALL, 5) #@UndefinedVariable
        timeModulationModeSizer.Add(timeModulationModeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainTimeModulationGuiSizer.Add(timeModulationModeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._timeModulationModulationSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText3 = wx.StaticText(self._mainTimeModulationGuiPlane, wx.ID_ANY, "Modulation source:") #@UndefinedVariable
        self._timeModulationModulationField = wx.TextCtrl(self._mainTimeModulationGuiPlane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._timeModulationModulationField.SetInsertionPoint(0)
        self._timeModulationModulationField.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        self._timeModulationModulationButton = PcnImageButton(self._mainTimeModulationGuiPlane, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._timeModulationModulationButton.Bind(wx.EVT_BUTTON, self._onTimeModulationModulationEdit) #@UndefinedVariable
        self._timeModulationModulationSizer.Add(tmpText3, 1, wx.ALL, 5) #@UndefinedVariable
        self._timeModulationModulationSizer.Add(self._timeModulationModulationField, 2, wx.ALL, 5) #@UndefinedVariable
        self._timeModulationModulationSizer.Add(self._timeModulationModulationButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainTimeModulationGuiSizer.Add(self._timeModulationModulationSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._timeModulationModulationTestSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self._mainTimeModulationGuiPlane, wx.ID_ANY, "Modulation test slider:") #@UndefinedVariable
        self._timeModulationModulationTestSlider = wx.Slider(self._mainTimeModulationGuiPlane, wx.ID_ANY, minValue=0, maxValue=127, size=(200, -1)) #@UndefinedVariable
        self._timeModulationModulationTestSlider.SetValue(64)
        self._timeModulationModulationTestLabel = wx.StaticText(self._mainTimeModulationGuiPlane, wx.ID_ANY, "0.5", size=(30,-1)) #@UndefinedVariable
        timeModulationModulationTestButton = PcnImageButton(self._mainTimeModulationGuiPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        timeModulationModulationTestButton.Bind(wx.EVT_BUTTON, self._onTimeModulationModulationTestHelp) #@UndefinedVariable
        self._timeModulationModulationTestSizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        self._timeModulationModulationTestSizer.Add(self._timeModulationModulationTestSlider, 2, wx.ALL, 5) #@UndefinedVariable
        self._timeModulationModulationTestSizer.Add(self._timeModulationModulationTestLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._timeModulationModulationTestSizer.Add(timeModulationModulationTestButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainTimeModulationGuiSizer.Add(self._timeModulationModulationTestSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._timeModulationModulationTestSliderId = self._timeModulationModulationTestSlider.GetId()


        self._timeModulationRangeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText3 = wx.StaticText(self._mainTimeModulationGuiPlane, wx.ID_ANY, "Range:") #@UndefinedVariable
        self._timeModulationRangeField = wx.TextCtrl(self._mainTimeModulationGuiPlane, wx.ID_ANY, "4.0", size=(200, -1)) #@UndefinedVariable
        self._timeModulationRangeField.SetInsertionPoint(0)
        self._timeModulationRangeField.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        self._timeModulationRangeButton = PcnImageButton(self._mainTimeModulationGuiPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._timeModulationRangeButton.Bind(wx.EVT_BUTTON, self._onTimeModulationRangeHelp) #@UndefinedVariable
        self._timeModulationRangeSizer.Add(tmpText3, 1, wx.ALL, 5) #@UndefinedVariable
        self._timeModulationRangeSizer.Add(self._timeModulationRangeField, 2, wx.ALL, 5) #@UndefinedVariable
        self._timeModulationRangeSizer.Add(self._timeModulationRangeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainTimeModulationGuiSizer.Add(self._timeModulationRangeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._timeModulationRangeSliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self._mainTimeModulationGuiPlane, wx.ID_ANY, "Range:") #@UndefinedVariable
        self._timeModulationRangeSlider = wx.Slider(self._mainTimeModulationGuiPlane, wx.ID_ANY, minValue=0, maxValue=160, size=(200, -1)) #@UndefinedVariable
        self._timeModulationRangeLabel = wx.StaticText(self._mainTimeModulationGuiPlane, wx.ID_ANY, "4.0", size=(30,-1)) #@UndefinedVariable
        timeModulationRangeButton = PcnImageButton(self._mainTimeModulationGuiPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        timeModulationRangeButton.Bind(wx.EVT_BUTTON, self._onTimeModulationRangeHelp) #@UndefinedVariable
        self._timeModulationRangeSliderSizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        self._timeModulationRangeSliderSizer.Add(self._timeModulationRangeSlider, 2, wx.ALL, 5) #@UndefinedVariable
        self._timeModulationRangeSliderSizer.Add(self._timeModulationRangeLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._timeModulationRangeSliderSizer.Add(timeModulationRangeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainTimeModulationGuiSizer.Add(self._timeModulationRangeSliderSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._timeModulationRangeSliderId = self._timeModulationRangeSlider.GetId()

        self._timeModulationRangeQuantizeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText3 = wx.StaticText(self._mainTimeModulationGuiPlane, wx.ID_ANY, "Range quantization:") #@UndefinedVariable
        self._timeModulationRangeQuantizeField = wx.TextCtrl(self._mainTimeModulationGuiPlane, wx.ID_ANY, "1.0", size=(200, -1)) #@UndefinedVariable
        self._timeModulationRangeQuantizeField.SetInsertionPoint(0)
        self._timeModulationRangeQuantizeField.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        self._timeModulationRangeQuantizeButton = PcnImageButton(self._mainTimeModulationGuiPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._timeModulationRangeQuantizeButton.Bind(wx.EVT_BUTTON, self._onTimeModulationRangeQuantizeHelp) #@UndefinedVariable
        self._timeModulationRangeQuantizeSizer.Add(tmpText3, 1, wx.ALL, 5) #@UndefinedVariable
        self._timeModulationRangeQuantizeSizer.Add(self._timeModulationRangeQuantizeField, 2, wx.ALL, 5) #@UndefinedVariable
        self._timeModulationRangeQuantizeSizer.Add(self._timeModulationRangeQuantizeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainTimeModulationGuiSizer.Add(self._timeModulationRangeQuantizeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._timeModulationRangeQuantizeSliderSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self._mainTimeModulationGuiPlane, wx.ID_ANY, "Range quantization:") #@UndefinedVariable
        self._timeModulationRangeQuantizeSlider = wx.Slider(self._mainTimeModulationGuiPlane, wx.ID_ANY, minValue=0, maxValue=160, size=(200, -1)) #@UndefinedVariable
        self._timeModulationRangeQuantizeLabel = wx.StaticText(self._mainTimeModulationGuiPlane, wx.ID_ANY, "1.0", size=(30,-1)) #@UndefinedVariable
        timeModulationRangeQuantizeButton = PcnImageButton(self._mainTimeModulationGuiPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        timeModulationRangeQuantizeButton.Bind(wx.EVT_BUTTON, self._onTimeModulationRangeQuantizeHelp) #@UndefinedVariable
        self._timeModulationRangeQuantizeSliderSizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        self._timeModulationRangeQuantizeSliderSizer.Add(self._timeModulationRangeQuantizeSlider, 2, wx.ALL, 5) #@UndefinedVariable
        self._timeModulationRangeQuantizeSliderSizer.Add(self._timeModulationRangeQuantizeLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._timeModulationRangeQuantizeSliderSizer.Add(timeModulationRangeQuantizeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainTimeModulationGuiSizer.Add(self._timeModulationRangeQuantizeSliderSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._timeModulationRangeQuantizeSliderId = self._timeModulationRangeQuantizeSlider.GetId()

        self._mainTimeModulationGuiPlane.Bind(wx.EVT_SLIDER, self._onSlide) #@UndefinedVariable


        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = PcnImageButton(self._mainTimeModulationGuiPlane, self._closeButtonBitmap, self._closeButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(55, 17)) #@UndefinedVariable
        closeButton.Bind(wx.EVT_BUTTON, self._onCloseButton) #@UndefinedVariable
        listButton = PcnImageButton(self._mainTimeModulationGuiPlane, self._listButtonBitmap, self._listButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(46, 17)) #@UndefinedVariable
        listButton.Bind(wx.EVT_BUTTON, self._onListButton) #@UndefinedVariable
        self._saveButton = PcnImageButton(self._mainTimeModulationGuiPlane, self._saveBigGreyBitmap, self._saveBigGreyBitmap, (-1, -1), wx.ID_ANY, size=(52, 17)) #@UndefinedVariable
        self._saveButton.Bind(wx.EVT_BUTTON, self._onSaveButton) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 1, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(listButton, 1, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(self._saveButton, 1, wx.ALL, 5) #@UndefinedVariable
        self._mainTimeModulationGuiSizer.Add(self._buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

    def setupTimeModulationListGui(self, plane, sizer, parentSizer, parentClass):
        self._mainTimeModulationListPlane = plane
        self._mainTimeModulationListGuiSizer = sizer
        self._parentSizer = parentSizer
        self._hideTimeModulationListCallback = parentClass.hideTimeModulationListGui

        self._timeModulationImageList = wx.ImageList(25, 16) #@UndefinedVariable

        self._modeIdImageIndex = []
        index = self._timeModulationImageList.Add(self._timeOffBitmap)
        self._modeIdImageIndex.append(index)
        index = self._timeModulationImageList.Add(self._timeSpeedBitmap)
        self._modeIdImageIndex.append(index)
        index = self._timeModulationImageList.Add(self._timeJumpBitmap)
        self._modeIdImageIndex.append(index)
        index = self._timeModulationImageList.Add(self._timeLoopBitmap)
        self._modeIdImageIndex.append(index)

        self._modIdImageIndex = []
        for i in range(self._modulationGui.getModulationImageCount()):
            bitmap = self._modulationGui.getModulationImageBitmap(i)
            index = self._timeModulationImageList.Add(bitmap)
            self._modIdImageIndex.append(index)

        headerLabel = wx.StaticText(self._mainTimeModulationListPlane, wx.ID_ANY, "TimeModulation list:") #@UndefinedVariable
        headerFont = headerLabel.GetFont()
        headerFont.SetWeight(wx.BOLD) #@UndefinedVariable
        headerLabel.SetFont(headerFont)
        self._mainTimeModulationListGuiSizer.Add(headerLabel, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

#        self._oldListHeight = 376
        self._timeModulationListWidget = ultimatelistctrl.UltimateListCtrl(self._mainTimeModulationListPlane, id=wx.ID_ANY, size=(300,376), agwStyle = wx.LC_REPORT | wx.LC_HRULES | wx.LC_SINGLE_SEL) #@UndefinedVariable
        self._timeModulationListWidget.SetImageList(self._timeModulationImageList, wx.IMAGE_LIST_SMALL) #@UndefinedVariable
        self._timeModulationListWidget.SetBackgroundColour((170,170,170))

        self._timeModulationListWidget.InsertColumn(0, 'Name', width=150)
        self._timeModulationListWidget.InsertColumn(1, 'Mod', width=36)
        self._timeModulationListWidget.InsertColumn(2, 'Range', width=48)
        self._timeModulationListWidget.InsertColumn(3, 'Quantize', width=52)

        self._mainTimeModulationListGuiSizer.Add(self._timeModulationListWidget, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._mainTimeModulationListPlane.Bind(ultimatelistctrl.EVT_LIST_COL_CLICK, self._onListItemMouseDown, self._timeModulationListWidget)
        self._mainTimeModulationListPlane.Bind(ultimatelistctrl.EVT_LIST_ITEM_SELECTED, self._onListItemSelected, self._timeModulationListWidget)
        self._mainTimeModulationListPlane.Bind(ultimatelistctrl.EVT_LIST_ITEM_DESELECTED, self._onListItemDeselected, self._timeModulationListWidget)
#        self._mainTimeModulationListPlane.Bind(ultimatelistctrl.EVT_LIST_BEGIN_DRAG, self._onListDragStart, self._timeModulationListWidget)
        self._timeModulationListWidget.Bind(wx.EVT_LEFT_DCLICK, self._onListDoubbleClick) #@UndefinedVariable

        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = PcnImageButton(self._mainTimeModulationListPlane, self._closeButtonBitmap, self._closeButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(55, 17)) #@UndefinedVariable
        closeButton.Bind(wx.EVT_BUTTON, self._onListCloseButton) #@UndefinedVariable
        duplicateButton = PcnImageButton(self._mainTimeModulationListPlane, self._duplicateButtonBitmap, self._duplicateButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(79, 17)) #@UndefinedVariable
        duplicateButton.Bind(wx.EVT_BUTTON, self._onListDuplicateButton) #@UndefinedVariable
        deleteButton = PcnImageButton(self._mainTimeModulationListPlane, self._deleteButtonBitmap, self._deleteButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(62, 17)) #@UndefinedVariable
        deleteButton.Bind(wx.EVT_BUTTON, self._onListDeleteButton) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(duplicateButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(deleteButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainTimeModulationListGuiSizer.Add(self._buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

    def _onTimeModulationModeChosen(self, event = None):
        currentModeString = self._timeModulationModesField.GetValue()
        if(currentModeString == "Off"):
            self._mainTimeModulationGuiSizer.Hide(self._timeModulationModulationSizer)
            self._mainTimeModulationGuiSizer.Hide(self._timeModulationModulationTestSizer)
            self._mainTimeModulationGuiSizer.Hide(self._timeModulationRangeSizer)
            self._mainTimeModulationGuiSizer.Hide(self._timeModulationRangeSliderSizer)
            self._mainTimeModulationGuiSizer.Hide(self._timeModulationRangeQuantizeSizer)
            self._mainTimeModulationGuiSizer.Hide(self._timeModulationRangeQuantizeSliderSizer)
        else:
            self._mainTimeModulationGuiSizer.Show(self._timeModulationModulationSizer)
            self._mainTimeModulationGuiSizer.Show(self._timeModulationModulationTestSizer)
            self._mainTimeModulationGuiSizer.Show(self._timeModulationRangeSizer)
            self._mainTimeModulationGuiSizer.Show(self._timeModulationRangeSliderSizer)
            self._mainTimeModulationGuiSizer.Show(self._timeModulationRangeQuantizeSizer)
            self._mainTimeModulationGuiSizer.Show(self._timeModulationRangeQuantizeSliderSizer)
        self._mainTimeModulationGuiSizer.Layout()
        self._fixTimeModulationGuiLayout()
        self._onUpdate()

    def _onTimeModulationModeHelp(self, event):
        text = """
Decides what kind of time modulation this clip will use.

SpeedModulation:\tUse modulation to change playback speed.
TriggerdJump:\tRepress note to make a jump.
\t\t Jump length is set by modulation.
\t\t Modulation < 0.5 -> backward jump.
\t\t Modulation > 0.5 -> forward jump.
TriggeredJump:\tRepress note and hold it to loop clip.
\t\t Loop length is set by modulation.
\t\t This needs MIDI input to work.

OBS! Group type can only use SpeedModulation.
"""
        dlg = wx.MessageDialog(self._mainTimeModulationGuiPlane, text, 'Time Modulation mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _highlightButton(self, selected):
        if(selected == self.EditSelected.Mode):
            self._timeModulationModulationButton.setBitmaps(self._editSelectedBitmap, self._editSelectedBitmap)
        else:
            self._timeModulationModulationButton.setBitmaps(self._editBitmap, self._editPressedBitmap)

    def unselectButton(self):
        self._selectedEditor = self.EditSelected.Unselected
        self._highlightButton(self._selectedEditor)

    def _onTimeModulationModulationEdit(self, event):
        if(self._selectedEditor != self.EditSelected.Mode):
            self._selectedEditor = self.EditSelected.Mode
            self._showModulationCallback()
        else:
            self._selectedEditor = self.EditSelected.Unselected
            self._hideModulationCallback()
        self._fixEffectGuiLayout()
        self._globalConfig.updateModulationGui(self._timeModulationModulationField.GetValue(), self._timeModulationModulationField, self.unselectButton, None)
        self._highlightButton(self._selectedEditor)

    def _onTimeModulationModulationTestHelp(self, event):
        text = """
A slider that can be used to test modulation values.
"""
        dlg = wx.MessageDialog(self._mainTimeModulationGuiPlane, text, 'Range help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onTimeModulationRangeHelp(self, event):
        modeSelected = self._timeModulationModesField.GetValue()
        if(modeSelected == "SpeedModulation"):
            text = """
Decides how much the modulation changes the speed.

4.0  -> From 0.25 to  4.0 times the speed.
10.0 -> From 0.10 to 10.0 times the speed.
"""
        else:
            text = """
Decides how long we jump or loops in bars.
"""
        dlg = wx.MessageDialog(self._mainTimeModulationGuiPlane, text, 'Range help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onTimeModulationRangeQuantizeHelp(self, event):
        modeSelected = self._timeModulationModesField.GetValue()
        if(modeSelected == "SpeedModulation"):
            text = """
Decides how many steps we get.

Example for range = 4.0
4.0  -> 0.25, 1.0 4.0
1.0  -> 0.25, 0.33, 0.5, 0.66, 1.0, 1.5, 2.0, 3.0 4.0
"""
        else:
            text = """
Decides how we quantize the jump or loop length.

Example for range = 4.0
4.0    -> 0.0, 4.0
1.0    -> 0.0, 1.0, 2.0, 3.0, 4.0
"""
        dlg = wx.MessageDialog(self._mainTimeModulationGuiPlane, text, 'Range quantization help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onSlide(self, event):
        sliderId = event.GetEventObject().GetId()
        baseId = 10
        if(sliderId == self._timeModulationModulationTestSliderId):
            if((self._midiNote == None) or (self._midiNote < 0) or (self._midiNote >= 128)):
                print "No note selected for note controller message!"
            else:
                self.sendGuiController(self._midiNote, baseId+4, self._timeModulationModulationTestSlider.GetValue())
        if(sliderId == self._timeModulationRangeSliderId):
            self._updateValueLabels(True, False)
        elif(sliderId == self._timeModulationRangeQuantizeSliderId):
            self._updateValueLabels(False, True)
        else:
            self._updateValueLabels(False, False)

    def _updateValueLabels(self, updateRangeField = False, updateRangeQuantizeField = False):
        valueString = "%.2f" % (float(self._timeModulationModulationTestSlider.GetValue()) / 127.0)
        self._timeModulationModulationTestLabel.SetLabel(valueString)

        valueString = "%.1f" % (float(self._timeModulationRangeSlider.GetValue()) / 2.0)
        self._timeModulationRangeLabel.SetLabel(valueString)
        if(updateRangeField == True):
            self._timeModulationRangeField.SetValue(valueString)
        valueString = "%.2f" % (float(self._timeModulationRangeQuantizeSlider.GetValue()) / 8.0)
        self._timeModulationRangeQuantizeLabel.SetLabel(valueString)
        if(updateRangeQuantizeField == True):
            self._timeModulationRangeQuantizeField.SetValue(valueString)

    def sendGuiRelease(self, note, guiControllerId):
        if((note == None) or (note < 0) or (note >= 128)):
            print "No note selected for note controller message!"
        else:
            channel = 0
            guiControllerId = (guiControllerId & 0x0f)
            command = 0xd0
            command += guiControllerId
            midiSender = self._mainConfig.getMidiSender()
            midiSender.sendGuiRelease(channel, note, command)

    def sendGuiController(self, note, guiControllerId, value):
        channel = 0
        guiControllerId = (guiControllerId & 0x0f)
        command = 0xf0
        command += guiControllerId
        midiSender = self._mainConfig.getMidiSender()
        midiSender.sendGuiController(channel, note, command, value)

    def _onCloseButton(self, event):
        self._hideTimeModulationCallback()
        self._hideModulationCallback()
        self._selectedEditor = self.EditSelected.Unselected
        self._highlightButton(self._selectedEditor)
        self.sendGuiRelease(self._midiNote, 4)

    def _onListCloseButton(self, event):
        self._hideModulationCallback()
        self._hideTimeModulationCallback()
        self._hideTimeModulationListCallback()
        self._selectedEditor = self.EditSelected.Unselected
        self._highlightButton(self._selectedEditor)

    def _onListDuplicateButton(self, event):
        if(self._timeModListSelectedIndex >= 0):
            timeModulationTemplate = self._globalConfig.getTimeModulationTemplateByIndex(self._timeModListSelectedIndex)
            if(timeModulationTemplate != None):
                timeModulationName = timeModulationTemplate.getName()
                newName = self._globalConfig.duplicateTimeModulationTemplate(timeModulationName)
                self._globalConfig.updateTimeModulationList(newName)
                self._globalConfig.updateTimeModulationGui(newName, self._midiNote, self._editFieldWidget)

    def _onListDeleteButton(self, event):
        if(self._timeModListSelectedIndex >= 0):
            timeModulationTemplate = self._globalConfig.getTimeModulationTemplateByIndex(self._timeModListSelectedIndex)
            if(timeModulationTemplate != None):
                timeModulationName = timeModulationTemplate.getName()
                inUseNumber = self._mainConfig.countNumberOfTimeTimeModulationTemplateUsed(timeModulationName)
                text = "Are you sure you want to delete \"%s\"? (It is used %d times)" % (timeModulationName, inUseNumber)
                dlg = wx.MessageDialog(self._mainTimeModulationListPlane, text, 'Move?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                dlg.Destroy()
                if(result == True):
                    self._globalConfig.deleteTimeModulationTemplate(timeModulationName)
                    self._mainConfig.verifyTimeModulationTemplateUsed()
                    self._globalConfig.updateTimeModulationList(None)
                    self._globalConfig.updateNoteGui()
                    self._globalConfig.updateMixerGui()

    def _onListItemMouseDown(self, event):
        self._timeModListSelectedIndex = event.m_itemIndex
        self._timeModulationListDraggedIndex = -1

    def _onListItemSelected(self, event):
        self._timeModListSelectedIndex = event.m_itemIndex
        self._timeModulationListDraggedIndex = -1

    def _onListItemDeselected(self, event):
        self._timeModulationListDraggedIndex = -1
        self._timeModListSelectedIndex = -1

    def _onListDragStart(self, event):
        self._timeModListSelectedIndex = event.m_itemIndex
        self._timeModulationListDraggedIndex = event.m_itemIndex
        self._setDragCursor("Time")

    def getDraggedFxIndex(self):
        dragIndex = self._timeModulationListDraggedIndex # Gets updated by state calls
        if(dragIndex > -1):
            self._timeModulationListWidget.SetItemState(dragIndex, 0, wx.LIST_STATE_SELECTED) #@UndefinedVariable
            self._timeModulationListWidget.SetItemState(dragIndex, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED) #@UndefinedVariable
        self._timeModulationListWidget.SetCursor(wx.StockCursor(wx.CURSOR_ARROW)) #@UndefinedVariable
        return dragIndex

    def _onListDoubbleClick(self, event):
        self._timeModulationListDraggedIndex = -1
        timeModulationTemplate = self._globalConfig.getTimeModulationTemplateByIndex(self._timeModListSelectedIndex)
        if(timeModulationTemplate != None):
            self.updateGui(timeModulationTemplate, self._midiNote, self._editFieldWidget)
            self._showTimeModulationCallback()

    def _onListButton(self, event):
        timeModulationConfigName = self._templateNameField.GetValue()
        self._globalConfig.updateTimeModulationList(timeModulationConfigName)
        self._showTimeModulationListCallback()

    def _dialogResultCallback(self, value):
        self._dialogResult = value

    def _onSaveButton(self, event):
        saveName = self._templateNameField.GetValue()
        oldTemplate = self._globalConfig.getTimeModulationTemplate(saveName)
        rename = False
        renameOne = True
        cancel = False
        if(saveName != self._startConfigName):
            inUseNumber = self._globalConfig.countNumberOfTimeTimeModulationTemplateUsed(self._startConfigName)
            
            if(oldTemplate != None):
                text = "\"%s\" already exists!!! Do you want to overwrite?" % (saveName)
                dlg = wx.MessageDialog(self._mainTimeModulationGuiPlane, text, 'Overwrite?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                dlg.Destroy()
                if(result == False):
                    cancel = True
                else:
                    if(self._editFieldWidget != None):
                        self._dialogResultCallback(-1)
                        text = "Do you want to move one or all instances of \"%s\"\nto the new configuration \"%s\" (%d in all)" % (self._startConfigName, saveName, inUseNumber)
                        dlg = ThreeChoiceMessageDialog(self._mainTimeModulationGuiPlane, "Move?", self._dialogResultCallback, text, "One", "All", "None")
                        dlg.ShowModal()
                        dlg.Destroy()
                        if(self._dialogResult == 1):
                            renameOne = True
                        elif(self._dialogResult == 2):
                            rename = True
                    else:
                        text = "Do you want to move all instances of \"%s\" to the new configuration \"%s\" (%d in all)" % (self._startConfigName, saveName, inUseNumber)
                        dlg = wx.MessageDialog(self._mainTimeModulationGuiPlane, text, 'Move?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                        result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                        dlg.Destroy()
                        if(result == True):
                            rename = True
            else:
                if(self._editFieldWidget != None):
                    self._dialogResultCallback(-1)
                    text = "Do you want to move one or all instances of \"%s\"\nto the new configuration \"%s\" (%d in all)" % (self._startConfigName, saveName, inUseNumber)
                    dlg = ThreeChoiceMessageDialog(self._mainTimeModulationGuiPlane, "Move?", self._dialogResultCallback, text, "One", "All", "None")
                    dlg.ShowModal()
                    dlg.Destroy()
                    if(self._dialogResult == 1):
                        renameOne = True
                    elif(self._dialogResult == 2):
                        rename = True
                else:
                    text = "Do you want to move all instances of \"%s\" to the new configuration \"%s\" (%d in all)" % (self._startConfigName, saveName, inUseNumber)
                    dlg = wx.MessageDialog(self._mainTimeModulationGuiPlane, text, 'Move?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                    result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                    dlg.Destroy()
                    if(result == True):
                        rename = True
        timeModulationMode = self._timeModulationModesField.GetValue()
        timeModulationMod = self._midiModulation.validateModulationString(self._timeModulationModulationField.GetValue())
        try:
            timeModulationRange = float(self._timeModulationRangeField.GetValue())
        except:
            timeModulationRange = 4.0
        try:
            timeModulationRangeQuantize = float(self._timeModulationRangeQuantizeField.GetValue())
        except:
            timeModulationRangeQuantize = 1.0
        if(cancel == True):
            self._timeModulationModesField.SetValue(timeModulationMode)
            self._timeModulationModulationField.SetValue(timeModulationMod)
        else:
            if(oldTemplate == None):
                savedTemplate = self._globalConfig.makeTimeModulationTemplate(saveName, timeModulationMode, timeModulationMod, timeModulationRange, timeModulationRangeQuantize)
                if(rename == True):
                    self._globalConfig.renameTimeModulationTemplateUsed(self._startConfigName, saveName)
                self._globalConfig.verifyTimeModulationTemplateUsed()
            else:
                oldTemplate.update(timeModulationMode, timeModulationMod, timeModulationRange, timeModulationRangeQuantize)
                savedTemplate = oldTemplate
            self.updateGui(savedTemplate, self._midiNote, self._editFieldWidget)
            if(self._editFieldWidget != None):
                self._timeModulationNameFieldUpdateCallback(self._editFieldWidget, saveName, renameOne)
            self._mainConfig.updateNoteGui()
            self._mainConfig.updateMixerGui()
            self._globalConfig.updateTimeModulationList(saveName)

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

    def _checkIfUpdated(self):
        if(self._config == None):
            return False
        guiName = self._templateNameField.GetValue()
        configName = self._config.getValue("Name")
        if(guiName != configName):
            return True
        guiMode = self._timeModulationModesField.GetValue()
        configMode = self._config.getValue("Mode")
        if(guiMode != configMode):
            return True
        guiModulation = self._timeModulationModulationField.GetValue()
        configModulation = self._config.getValue("Modulation")
        if(guiModulation != configModulation):
            return True
        try:
            guiRange = float(self._timeModulationRangeField.GetValue())
        except:
            guiRange = 4.0
        configRange = self._config.getValue("Range")
        if(guiRange != configRange):
            return True
        try:
            guiRangeQuantize = float(self._timeModulationRangeQuantizeField.GetValue())
        except:
            guiRangeQuantize = 1.0
        configRangeQuantize = self._config.getValue("RangeQuantize")
        if(guiRangeQuantize != configRangeQuantize):
            return True
        return False

    def _onUpdate(self, event = None):
        self._showOrHideSaveButton()

    def _showOrHideSaveButton(self):
        updated = self._checkIfUpdated()
        if(updated == False):
            self._saveButton.setBitmaps(self._saveBigGreyBitmap, self._saveBigGreyBitmap)
        if(updated == True):
            self._saveButton.setBitmaps(self._saveBigBitmap, self._saveBigPressedBitmap)

    def updateTimeModeThumb(self, widget, mode):
        if(mode == "Off"):
            widget.setBitmaps(self._timeOffBitmap, self._timeOffBitmap)
        elif(mode == "SpeedModulation"):
            widget.setBitmaps(self._timeSpeedBitmap, self._timeSpeedBitmap)
        elif(mode == "TriggeredJump"):
            widget.setBitmaps(self._timeJumpBitmap, self._timeJumpBitmap)
        elif(mode == "TriggeredLoop"):
            widget.setBitmaps(self._timeLoopBitmap, self._timeLoopBitmap)
        else:
            widget.setBitmaps(self._timeSpeedBitmap, self._timeSpeedBitmap)

    def updateTimeModulationGuiButtons(self, timeModulationTemplate, modeWidget, modulationWidget, levelWidget):
        if(timeModulationTemplate == None):
            self.updateTimeModeThumb(modeWidget, "SpeedModulation")
            self._globalConfig.updateModulationGuiButton(modulationWidget, "MidiChannel.PitchBend")
        else:
            config = timeModulationTemplate.getConfigHolder()
            mode = config.getValue("Mode")
            self.updateTimeModeThumb(modeWidget, mode)
            modulation = config.getValue("Modulation")
            self._globalConfig.updateModulationGuiButton(modulationWidget, modulation)

    def updateTimeModulationList(self, timeModConfiguration, selectedName):
        self._timeModulationListWidget.DeleteAllItems()
        selectedIndex = -1
        for timeModConfig in timeModConfiguration.getList():
            config = timeModConfig.getConfigHolder()
            selectedMode = config.getValue("Mode")
            selectedModeLower = selectedMode.lower()
            currentMode = TimeModulationMode.SpeedModulation
            if(selectedModeLower == "off"):
                bitmapId = self._modeIdImageIndex[0]
                currentMode = TimeModulationMode.Off
            elif(selectedModeLower == "speedmodulation"):
                bitmapId = self._modeIdImageIndex[1]
                currentMode = TimeModulationMode.SpeedModulation
            elif(selectedModeLower == "triggeredjump"):
                bitmapId = self._modeIdImageIndex[2]
                currentMode = TimeModulationMode.TriggeredJump
            elif(selectedModeLower == "triggeredloop"):
                bitmapId = self._modeIdImageIndex[3]
                currentMode = TimeModulationMode.TriggeredLoop
            else:
                bitmapId = self._modeIdImageIndex[1]
                currentMode = TimeModulationMode.SpeedModulation
            configName = timeModConfig.getName()
            index = self._timeModulationListWidget.InsertImageStringItem(sys.maxint, configName, bitmapId)
            if(configName == selectedName):
                selectedIndex = index
            modulationString = config.getValue("Modulation")
            if(currentMode != TimeModulationMode.Off):
                modBitmapId = self._modulationGui.getModulationImageId(modulationString)
                imageId = self._modIdImageIndex[modBitmapId]
                self._timeModulationListWidget.SetStringItem(index, 1, "", imageId)
            else:
                self._timeModulationListWidget.SetStringItem(index, 1, "", self._modeIdImageIndex[0])
            if((currentMode == TimeModulationMode.SpeedModulation) or (currentMode == TimeModulationMode.TriggeredJump) or (currentMode == TimeModulationMode.TriggeredLoop)):
                rangeString = str(config.getValue("Range"))
                rangeQuantizeString = str(config.getValue("RangeQuantize"))
                self._timeModulationListWidget.SetStringItem(index, 2, rangeString)
                self._timeModulationListWidget.SetStringItem(index, 3, rangeQuantizeString)
            else:
                self._timeModulationListWidget.SetStringItem(index, 2, "")
                self._timeModulationListWidget.SetStringItem(index, 3, "")

            if(index % 2):
                self._timeModulationListWidget.SetItemBackgroundColour(index, wx.Colour(170,170,170)) #@UndefinedVariable
            else:
                self._timeModulationListWidget.SetItemBackgroundColour(index, wx.Colour(190,190,190)) #@UndefinedVariable
        if(selectedIndex > -1):
            self._timeModListSelectedIndex = selectedIndex
            self._timeModulationListWidget.Select(selectedIndex)

    def updateGui(self, timeModulationTemplate, midiNote, editFieldWidget = None):
        self._config = timeModulationTemplate.getConfigHolder()
        self._midiNote = midiNote
        self._selectedEditor = self.EditSelected.Unselected
        self._editFieldWidget = editFieldWidget
        self._highlightButton(self._selectedEditor)
        self._startConfigName = self._config.getValue("Name")
        self._templateNameField.SetValue(self._startConfigName)

        currentModeString = self._config.getValue("Mode")
        updateChoices(self._timeModulationModesField, self._timeModes.getChoices, currentModeString, "SpeedModulation")

        self._timeModulationModulationField.SetValue(self._config.getValue("Modulation"))

        rangeValue = self._config.getValue("Range")
        self._timeModulationRangeField.SetValue(str(rangeValue))
        calcValue = max(min(int(2.0 * rangeValue), 160), 0)
        self._timeModulationRangeSlider.SetValue(calcValue)

        rangeQuantizeValue = self._config.getValue("RangeQuantize")
        self._timeModulationRangeQuantizeField.SetValue(str(rangeQuantizeValue))
        calcValue = max(min(int(8.0 * rangeQuantizeValue), 160), 0)
        self._timeModulationRangeQuantizeSlider.SetValue(calcValue)

        self._updateValueLabels()
        self._onTimeModulationModeChosen()

        self._showOrHideSaveButton()

