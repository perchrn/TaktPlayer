'''
Created on 6. feb. 2012

@author: pcn
'''
from midi.MidiTiming import MidiTiming
from configuration.EffectSettings import EffectTemplates, FadeTemplates
import wx
from wx.lib.agw import ultimatelistctrl #@UnresolvedImport
from midi.MidiModulation import MidiModulation
from midi.MidiController import MidiControllers
from video.media.MediaFileModes import FadeMode
from video.EffectModes import EffectTypes, FlipModes, ZoomModes, DistortionModes,\
    EdgeModes, DesaturateModes, getEffectId, getEffectName, ColorizeModes,\
    EdgeColourModes, ContrastModes, HueSatModes, ScrollModes
from configurationGui.ModulationGui import ModulationGui
import sys

class GlobalConfig(object):
    def __init__(self, configParent, mainConfig):
        self._mainConfig = mainConfig
        self._configurationTree = configParent.addChildUnique("Global")

        self._midiTiming = MidiTiming()

        self._modulationGui = ModulationGui(self._mainConfig, self._midiTiming)

        self._effectsConfiguration = EffectTemplates(self._configurationTree, self._midiTiming, 800, 600)
        self._effectsGui = EffectsGui(self._mainConfig, self._midiTiming, self._modulationGui)
        self._fadeConfiguration = FadeTemplates(self._configurationTree, self._midiTiming)
        self._fadeGui = FadeGui(self._mainConfig, self._midiTiming, self._modulationGui)

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

    def setupEffectsListGui(self, plane, sizer, parentSizer, parentClass):
        self._effectsGui.setupEffectsListGui(plane, sizer, parentSizer, parentClass)

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

    def updateEffectsGui(self, configName, midiNote, effectId):
        template = self._effectsConfiguration.getTemplate(configName)
        if(template != None):
            self._effectsGui.updateGui(template, midiNote, effectId)

    def updateEffectList(self, selectedName):
        self._effectsGui.updateEffectList(self._effectsConfiguration, selectedName)

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

    def makeEffectTemplate(self, saveName, effectName, ammountMod, arg1Mod, arg2Mod, arg3Mod, arg4Mod):
        return self._effectsConfiguration.createTemplate(saveName, effectName, ammountMod, arg1Mod, arg2Mod, arg3Mod, arg4Mod)

    def deleteEffectTemplate(self, configName):
        self._effectsConfiguration.deleteTemplate(configName)

    def duplicateEffectTemplate(self, configName):
        return self._effectsConfiguration.duplicateTemplate(configName)

    def getEffectTemplateNamesList(self):
        return self._effectsConfiguration.getTemplateNamesList()

    def checkIfNameIsDefaultEffectName(self, configName):
        return self._effectsConfiguration.checkIfNameIsDefaultName(configName)

    def updateModulationGui(self, modulationString, widget, closeCallback, saveCallback):
        self._modulationGui.updateGui(modulationString, widget, closeCallback, saveCallback)

    def updateModulationGuiButton(self, modulationString, widget):
        self._modulationGui.updateModulationGuiButton(modulationString, widget)

    def stopModulationGui(self):
        self._modulationGui.stopModulationUpdate()

    def updateFadeGui(self, configName, editField):
        template = self._fadeConfiguration.getTemplate(configName)
        if(template != None):
            self._fadeGui.updateGui(template, editField)

    def updateFadeList(self, selectedName):
        self._fadeGui.updateFadeList(self._fadeConfiguration, selectedName)

    def updateFadeGuiButtons(self, configName, modeWidget, modulationWidget, levelWidget):
        template = self._fadeConfiguration.getTemplate(configName)
        self._fadeGui.updateFadeGuiButtons(template, modeWidget, modulationWidget, levelWidget)

    def getFadeTemplate(self, configName):
        return self._fadeConfiguration.getTemplate(configName)

    def getFadeTemplateByIndex(self, index):
        return self._fadeConfiguration.getTemplateByIndex(index)

    def makeFadeTemplate(self, saveName, fadeMode, fadeMod, levelMod):
        return self._fadeConfiguration.createTemplate(saveName, fadeMode, fadeMod, levelMod)

    def deleteFadeTemplate(self, configName):
        self._fadeConfiguration.deleteTemplate(configName)

    def duplicateFadeTemplate(self, configName):
        return self._fadeConfiguration.duplicateTemplate(configName)

    def getFadeTemplateNamesList(self):
        return self._fadeConfiguration.getTemplateNamesList()

    def checkIfNameIsDefaultFadeName(self, configName):
        return self._fadeConfiguration.checkIfNameIsDefaultName(configName)

class EffectsGui(object):
    def __init__(self, mainConfing, midiTiming, modulationGui):
        self._mainConfig = mainConfing
        self._midiTiming = midiTiming
        self._modulationGui = modulationGui
        self._midiModulation = MidiModulation(None, self._midiTiming)
        self._startConfigName = ""
        self._selectedEditor = self.EditSelection.Unselected
        self._effectListSelectedIndex = -1

        self._blankFxBitmap = wx.Bitmap("graphics/fxEmpty.png") #@UndefinedVariable
        self._fxBitmapBlur = wx.Bitmap("graphics/fxBlur.png") #@UndefinedVariable
        self._fxBitmapBlurMul = wx.Bitmap("graphics/fxBlurMultiply.png") #@UndefinedVariable
        self._fxBitmapColorize = wx.Bitmap("graphics/fxColorize.png") #@UndefinedVariable
        self._fxBitmapContrast = wx.Bitmap("graphics/fxContrast.png") #@UndefinedVariable
        self._fxBitmapDeSat = wx.Bitmap("graphics/fxDeSat.png") #@UndefinedVariable
        self._fxBitmapDist = wx.Bitmap("graphics/fxDist.png") #@UndefinedVariable
        self._fxBitmapEdge = wx.Bitmap("graphics/fxEdge.png") #@UndefinedVariable
        self._fxBitmapFlip = wx.Bitmap("graphics/fxFlip.png") #@UndefinedVariable
        self._fxBitmapHueSat = wx.Bitmap("graphics/fxHueSat.png") #@UndefinedVariable
        self._fxBitmapInverse = wx.Bitmap("graphics/fxInverse.png") #@UndefinedVariable
        self._fxBitmapMirror = wx.Bitmap("graphics/fxMirror.png") #@UndefinedVariable
        self._fxBitmapRotate = wx.Bitmap("graphics/fxRotate.png") #@UndefinedVariable
        self._fxBitmapScroll = wx.Bitmap("graphics/fxScroll.png") #@UndefinedVariable
        self._fxBitmapThreshold = wx.Bitmap("graphics/fxThreshold.png") #@UndefinedVariable
        self._fxBitmapZoom = wx.Bitmap("graphics/fxZoom.png") #@UndefinedVariable

        self._effectListDraggedIndex = -1
        self._midiNote = -1
        self._activeEffectId = None

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
        self._showModulationCallback = parentClass.showModulationGui
        self._hideModulationCallback = parentClass.hideModulationGui
        self._showEffectListCallback = parentClass.showEffectList
        self._setDragCursor = parentClass.setDragCursor

        templateNameSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText1 = wx.StaticText(self._mainEffectsPlane, wx.ID_ANY, "Name:") #@UndefinedVariable
        self._templateNameField = wx.TextCtrl(self._mainEffectsPlane, wx.ID_ANY, "MediaDefault1", size=(200, -1)) #@UndefinedVariable
        self._templateNameField.SetInsertionPoint(0)
        templateNameButton = wx.Button(self._mainEffectsPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        templateNameButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._mainEffectsPlane.Bind(wx.EVT_BUTTON, self._onTemplateNameHelp, id=templateNameButton.GetId()) #@UndefinedVariable
        templateNameSizer.Add(tmpText1, 1, wx.ALL, 5) #@UndefinedVariable
        templateNameSizer.Add(self._templateNameField, 2, wx.ALL, 5) #@UndefinedVariable
        templateNameSizer.Add(templateNameButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(templateNameSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        effectNameSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText2 = wx.StaticText(self._mainEffectsPlane, wx.ID_ANY, "Effect:") #@UndefinedVariable
        self._effectChoices = EffectTypes()
        self._effectNameField = wx.ComboBox(self._mainEffectsPlane, wx.ID_ANY, size=(200, -1), choices=["None"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateChoices(self._effectNameField, self._effectChoices.getChoices, "None", "None")
        effectNameButton = wx.Button(self._mainEffectsPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        effectNameButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
        self._mainEffectsPlane.Bind(wx.EVT_BUTTON, self._onEffectHelp, id=effectNameButton.GetId()) #@UndefinedVariable
        effectNameSizer.Add(tmpText2, 1, wx.ALL, 5) #@UndefinedVariable
        effectNameSizer.Add(self._effectNameField, 2, wx.ALL, 5) #@UndefinedVariable
        effectNameSizer.Add(effectNameButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(effectNameSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._mainEffectsPlane.Bind(wx.EVT_COMBOBOX, self._onEffectChosen, id=self._effectNameField.GetId()) #@UndefinedVariable

        self._ammountSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._amountLabel = wx.StaticText(self._mainEffectsPlane, wx.ID_ANY, "Amount:") #@UndefinedVariable
        self._ammountField = wx.TextCtrl(self._mainEffectsPlane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._ammountField.SetInsertionPoint(0)
        self._ammountButton = wx.Button(self._mainEffectsPlane, wx.ID_ANY, 'Edit', size=(60,-1)) #@UndefinedVariable
        self._ammountButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainEffectsPlane.Bind(wx.EVT_BUTTON, self._onAmmountEdit, id=self._ammountButton.GetId()) #@UndefinedVariable
        self._ammountSizer.Add(self._amountLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._ammountSizer.Add(self._ammountField, 2, wx.ALL, 5) #@UndefinedVariable
        self._ammountSizer.Add(self._ammountButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._ammountSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._arg1Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg1Label = wx.StaticText(self._mainEffectsPlane, wx.ID_ANY, "Argument 1:") #@UndefinedVariable
        self._arg1Field = wx.TextCtrl(self._mainEffectsPlane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._arg1Field.SetInsertionPoint(0)
        self._arg1Button = wx.Button(self._mainEffectsPlane, wx.ID_ANY, 'Edit', size=(60,-1)) #@UndefinedVariable
        self._arg1Button.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainEffectsPlane.Bind(wx.EVT_BUTTON, self._onArg1Edit, id=self._arg1Button.GetId()) #@UndefinedVariable
        self._arg1Sizer.Add(self._arg1Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg1Sizer.Add(self._arg1Field, 2, wx.ALL, 5) #@UndefinedVariable
        self._arg1Sizer.Add(self._arg1Button, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._arg1Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._arg2Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg2Label = wx.StaticText(self._mainEffectsPlane, wx.ID_ANY, "Argument 2:") #@UndefinedVariable
        self._arg2Field = wx.TextCtrl(self._mainEffectsPlane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._arg2Field.SetInsertionPoint(0)
        self._arg2Button = wx.Button(self._mainEffectsPlane, wx.ID_ANY, 'Edit', size=(60,-1)) #@UndefinedVariable
        self._arg2Button.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainEffectsPlane.Bind(wx.EVT_BUTTON, self._onArg2Edit, id=self._arg2Button.GetId()) #@UndefinedVariable
        self._arg2Sizer.Add(self._arg2Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg2Sizer.Add(self._arg2Field, 2, wx.ALL, 5) #@UndefinedVariable
        self._arg2Sizer.Add(self._arg2Button, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._arg2Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._arg3Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg3Label = wx.StaticText(self._mainEffectsPlane, wx.ID_ANY, "Argument 3:") #@UndefinedVariable
        self._arg3Field = wx.TextCtrl(self._mainEffectsPlane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._arg3Field.SetInsertionPoint(0)
        self._arg3Button = wx.Button(self._mainEffectsPlane, wx.ID_ANY, 'Edit', size=(60,-1)) #@UndefinedVariable
        self._arg3Button.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainEffectsPlane.Bind(wx.EVT_BUTTON, self._onArg3Edit, id=self._arg3Button.GetId()) #@UndefinedVariable
        self._arg3Sizer.Add(self._arg3Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg3Sizer.Add(self._arg3Field, 2, wx.ALL, 5) #@UndefinedVariable
        self._arg3Sizer.Add(self._arg3Button, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._arg3Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._arg4Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._arg4Label = wx.StaticText(self._mainEffectsPlane, wx.ID_ANY, "Argument 4:") #@UndefinedVariable
        self._arg4Field = wx.TextCtrl(self._mainEffectsPlane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._arg4Field.SetInsertionPoint(0)
        self._arg4Button = wx.Button(self._mainEffectsPlane, wx.ID_ANY, 'Edit', size=(60,-1)) #@UndefinedVariable
        self._arg4Button.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainEffectsPlane.Bind(wx.EVT_BUTTON, self._onArg4Edit, id=self._arg4Button.GetId()) #@UndefinedVariable
        self._arg4Sizer.Add(self._arg4Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._arg4Sizer.Add(self._arg4Field, 2, wx.ALL, 5) #@UndefinedVariable
        self._arg4Sizer.Add(self._arg4Button, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._arg4Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = wx.Button(self._mainEffectsPlane, wx.ID_ANY, 'Close') #@UndefinedVariable
        closeButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainEffectsPlane.Bind(wx.EVT_BUTTON, self._onCloseButton, id=closeButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 1, wx.ALL, 5) #@UndefinedVariable
        saveButton = wx.Button(self._mainEffectsPlane, wx.ID_ANY, 'Save') #@UndefinedVariable
        saveButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainEffectsPlane.Bind(wx.EVT_BUTTON, self._onSaveButton, id=saveButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(saveButton, 1, wx.ALL, 5) #@UndefinedVariable
        listButton = wx.Button(self._mainEffectsPlane, wx.ID_ANY, 'List') #@UndefinedVariable
        listButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainEffectsPlane.Bind(wx.EVT_BUTTON, self._onListButton, id=listButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(listButton, 1, wx.ALL, 5) #@UndefinedVariable
        slidersButton = wx.Button(self._mainEffectsPlane, wx.ID_ANY, 'Sliders') #@UndefinedVariable
        slidersButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainEffectsPlane.Bind(wx.EVT_BUTTON, self._onSlidersButton, id=slidersButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(slidersButton, 1, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectsGuiSizer.Add(self._buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._flipModes = FlipModes()
        self._zoomModes = ZoomModes()
        self._scrollModes = ScrollModes()
        self._distortionModes = DistortionModes()
        self._edgeModes = EdgeModes()
        self._edgeColourModes = EdgeColourModes()
        self._desaturateModes = DesaturateModes()
        self._contrastModes = ContrastModes()
        self._hueSatModes = HueSatModes()
        self._colorizeModes = ColorizeModes()
        self._midiControllers = MidiControllers()

    def setupEffectsListGui(self, plane, sizer, parentSizer, parentClass):
        self._mainEffectsListPlane = plane
        self._mainEffectsListGuiSizer = sizer
        self._parentSizer = parentSizer
        self._hideEffectsListCallback = parentClass.hideEffectsListGui
#        self._fixEffectGuiLayout = parentClass.fixEffectsGuiLayout
#        self._showSlidersCallback = parentClass.showSlidersGui
#        self._showModulationCallback = parentClass.showModulationGui
#        self._hideModulationCallback = parentClass.hideModulationGui

        self._effectImageList = wx.ImageList(32, 22) #@UndefinedVariable
        self._blankEffectIndex = self._effectImageList.Add(self._blankFxBitmap)
        self._fxIdImageIndex = []
        index = self._effectImageList.Add(self._fxBitmapZoom)
        self._fxIdImageIndex.append(index)
        index = self._effectImageList.Add(self._fxBitmapFlip)
        self._fxIdImageIndex.append(index)
        index = self._effectImageList.Add(self._fxBitmapScroll)
        self._fxIdImageIndex.append(index)
        index = self._effectImageList.Add(self._fxBitmapBlur)
        self._fxIdImageIndex.append(index)
        index = self._effectImageList.Add(self._fxBitmapBlurMul)
        self._fxIdImageIndex.append(index)
        index = self._effectImageList.Add(self._fxBitmapDist)
        self._fxIdImageIndex.append(index)
        index = self._effectImageList.Add(self._fxBitmapEdge)
        self._fxIdImageIndex.append(index)
        index = self._effectImageList.Add(self._fxBitmapDeSat)
        self._fxIdImageIndex.append(index)
        index = self._effectImageList.Add(self._fxBitmapContrast)
        self._fxIdImageIndex.append(index)
        index = self._effectImageList.Add(self._fxBitmapHueSat)
        self._fxIdImageIndex.append(index)
        index = self._effectImageList.Add(self._fxBitmapColorize)
        self._fxIdImageIndex.append(index)
        index = self._effectImageList.Add(self._fxBitmapInverse)
        self._fxIdImageIndex.append(index)
        index = self._effectImageList.Add(self._fxBitmapThreshold)
        self._fxIdImageIndex.append(index)

        self._modIdImageIndex = []
        for i in range(self._modulationGui.getModulationImageCount()):
            bitmap = self._modulationGui.getBigModulationImageBitmap(i)
            index = self._effectImageList.Add(bitmap)
            self._modIdImageIndex.append(index)

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
        closeButton = wx.Button(self._mainEffectsListPlane, wx.ID_ANY, 'Close') #@UndefinedVariable
        closeButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainEffectsListPlane.Bind(wx.EVT_BUTTON, self._onListCloseButton, id=closeButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 1, wx.ALL, 5) #@UndefinedVariable
        duplicateButton = wx.Button(self._mainEffectsListPlane, wx.ID_ANY, 'Duplicate') #@UndefinedVariable
        duplicateButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainEffectsListPlane.Bind(wx.EVT_BUTTON, self._onListDuplicateButton, id=duplicateButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(duplicateButton, 1, wx.ALL, 5) #@UndefinedVariable
        deleteButton = wx.Button(self._mainEffectsListPlane, wx.ID_ANY, 'Delete') #@UndefinedVariable
        deleteButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainEffectsListPlane.Bind(wx.EVT_BUTTON, self._onListDeleteButton, id=deleteButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(deleteButton, 1, wx.ALL, 5) #@UndefinedVariable
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
            if(i == 4):
                extraTab = ""
            elif(i == 7):
                extraTab = ""
            elif(i == 9):
                extraTab = ""
            elif(i == 12):
                extraTab = ""
            text += effectName + ":\t" + extraTab + effectDescription + "\n"
        dlg = wx.MessageDialog(self._mainEffectsPlane, text, 'Effect help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _highlightButton(self, selected):
        if(selected == self.EditSelection.Ammount):
            self._ammountButton.SetBackgroundColour(wx.Colour(180,180,255)) #@UndefinedVariable
        else:
            self._ammountButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        if(selected == self.EditSelection.Arg1):
            self._arg1Button.SetBackgroundColour(wx.Colour(180,180,255)) #@UndefinedVariable
        else:
            self._arg1Button.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        if(selected == self.EditSelection.Arg2):
            self._arg2Button.SetBackgroundColour(wx.Colour(180,180,255)) #@UndefinedVariable
        else:
            self._arg2Button.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        if(selected == self.EditSelection.Arg3):
            self._arg3Button.SetBackgroundColour(wx.Colour(180,180,255)) #@UndefinedVariable
        else:
            self._arg3Button.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        if(selected == self.EditSelection.Arg4):
            self._arg4Button.SetBackgroundColour(wx.Colour(180,180,255)) #@UndefinedVariable
        else:
            self._arg4Button.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable

    def unselectButton(self):
        self._selectedEditor = self.EditSelection.Unselected
        self._highlightButton(self._selectedEditor)

    def _onAmmountEdit(self, event):
        self._showModulationCallback()
        self._fixEffectGuiLayout()
        self._selectedEditor = self.EditSelection.Ammount
        self._highlightButton(self._selectedEditor)
        self._mainConfig.updateModulationGui(self._ammountField.GetValue(), self._ammountField, self.unselectButton, None)

    def _onArg1Edit(self, event):
        self._showModulationCallback()
        self._fixEffectGuiLayout()
        self._selectedEditor = self.EditSelection.Arg1
        self._highlightButton(self._selectedEditor)
        self._mainConfig.updateModulationGui(self._arg1Field.GetValue(), self._arg1Field, self.unselectButton, None)

    def _onArg2Edit(self, event):
        self._showModulationCallback()
        self._fixEffectGuiLayout()
        self._selectedEditor = self.EditSelection.Arg2
        self._highlightButton(self._selectedEditor)
        self._mainConfig.updateModulationGui(self._arg2Field.GetValue(), self._arg2Field, self.unselectButton, None)

    def _onArg3Edit(self, event):
        self._showModulationCallback()
        self._fixEffectGuiLayout()
        self._selectedEditor = self.EditSelection.Arg3
        self._highlightButton(self._selectedEditor)
        self._mainConfig.updateModulationGui(self._arg3Field.GetValue(), self._arg3Field, self.unselectButton, None)

    def _onArg4Edit(self, event):
        self._showModulationCallback()
        self._fixEffectGuiLayout()
        self._selectedEditor = self.EditSelection.Arg4
        self._highlightButton(self._selectedEditor)
        self._mainConfig.updateModulationGui(self._arg4Field.GetValue(), self._arg4Field, self.unselectButton, None)

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
        self._mainConfig.stopModulationGui()

    def _onListDuplicateButton(self, event):
        if(self._effectListSelectedIndex >= 0):
            effectTemplate = self._mainConfig.getEffectTemplateByIndex(self._effectListSelectedIndex)
            if(effectTemplate != None):
                effectName = effectTemplate.getName()
                newName = self._mainConfig.duplicateEffectTemplate(effectName)
                self._mainConfig.updateEffectList(newName)

    def _onListDeleteButton(self, event):
        if(self._effectListSelectedIndex >= 0):
            effectTemplate = self._mainConfig.getEffectTemplateByIndex(self._effectListSelectedIndex)
            if(effectTemplate != None):
                effectName = effectTemplate.getName()
                inUseNumber = self._mainConfig.countNumberOfTimeEffectTemplateUsed(effectName)
                text = "Are you sure you want to delete \"%s\"? (It is used %d times)" % (effectName, inUseNumber)
                dlg = wx.MessageDialog(self._mainEffectsListPlane, text, 'Move?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                dlg.Destroy()
                if(result == True):
                    self._mainConfig.deleteEffectTemplate(effectName)
                    self._mainConfig.verifyEffectTemplateUsed()
                    self._mainConfig.updateEffectList(None)
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
        self._setDragCursor()

    def getDraggedFxIndex(self):
        dragIndex = self._effectListDraggedIndex # Gets updated by state calls
        if(dragIndex > -1):
            self._effectListWidget.SetItemState(dragIndex, 0, ultimatelistctrl.ULC_STATE_SELECTED)
            self._effectListWidget.SetItemState(dragIndex, ultimatelistctrl.ULC_STATE_SELECTED, ultimatelistctrl.ULC_STATE_SELECTED) #@UndefinedVariable
        self._effectListWidget.SetCursor(wx.StockCursor(wx.CURSOR_ARROW)) #@UndefinedVariable
        return dragIndex

    def _onListDoubbleClick(self, event):
        self._effectListDraggedIndex = -1
        effectTemplate = self._mainConfig.getEffectTemplateByIndex(self._effectListSelectedIndex)
        if(effectTemplate != None):
            self.updateGui(effectTemplate, None)
            self._showEffectsCallback()

    def _onListButton(self, event):
        effectConfigName = self._templateNameField.GetValue()
        self._mainConfig.updateEffectList(effectConfigName)
        self._showEffectListCallback()

    def _onSaveButton(self, event):
        saveName = self._templateNameField.GetValue()
        oldTemplate = self._mainConfig.getEffectTemplate(saveName)
        rename = False
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
                    text = "Do you want to move all instances of \"%s\" to the new configuration \"%s\" (%d in all)" % (self._startConfigName, saveName, inUseNumber)
                    dlg = wx.MessageDialog(self._mainEffectsPlane, text, 'Move?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                    result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                    dlg.Destroy()
                    if(result == True):
                        rename = True
            else:
                text = "Do you want to move all instances of \"%s\" to the new configuration \"%s\" (%d in all)" % (self._startConfigName, saveName, inUseNumber)
                dlg = wx.MessageDialog(self._mainEffectsPlane, text, 'Move?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
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
        if(cancel == True):
            self._ammountField.SetValue(ammountMod)
            self._arg1Field.SetValue(arg1Mod)
            self._arg2Field.SetValue(arg2Mod)
            self._arg3Field.SetValue(arg3Mod)
            self._arg4Field.SetValue(arg4Mod)
        else:
            if(oldTemplate == None):
                print "Make new template..."
                savedTemplate = self._mainConfig.makeEffectTemplate(saveName, effectName, ammountMod, arg1Mod, arg2Mod, arg3Mod, arg4Mod)
                if(rename == True):
                    self._mainConfig.renameEffectTemplateUsed(self._startConfigName, saveName)
                self._mainConfig.verifyEffectTemplateUsed()
            else:
                oldTemplate.update(effectName, ammountMod, arg1Mod, arg2Mod, arg3Mod, arg4Mod)
                savedTemplate = oldTemplate
            self.updateGui(savedTemplate, self._midiNote)
            self._mainConfig.updateNoteGui()
            self._mainConfig.updateMixerGui()
            self._mainConfig.updateEffectList(saveName)

    def _onSlidersButton(self, event):
        self._showSlidersCallback()
        self._fixEffectGuiLayout()

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
        baseId = 0
        if((self._activeEffectId == "Effect2") or (self._activeEffectId == "PostEffect")):
            baseId = 5
        isChannelController = False
        if((self._activeEffectId == "PreEffect") or (self._activeEffectId == "PostEffect")):
            isChannelController = True
        if((midiChannel > -1) and (midiChannel < 16)):
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
        self._updateValueLabels()

    def _onEffectChosen(self, event):
        selectedEffectId = self._effectNameField.GetSelection()
        self._setEffect(getEffectName(selectedEffectId-1))

    def sendGuiController(self, isChannelController, channel, note, guiControllerId, value):
        guiControllerId = (guiControllerId & 0x0f)
        if(isChannelController == True):
            command = 0xe0
            note = 0
        else:
            command = 0xf0
        command += guiControllerId
        midiSender = self._mainConfig.getMidiSender()
        print "DEBUG sending GUI controller: " + str(command) + " note: " + str(note) + " value: " + str(value)
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
        self._fixEffectGuiLayout()

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
        self._ammountValueLabels = amount
        self._arg1ValueLabels = arg1
        self._arg2ValueLabels = arg2
        self._arg3ValueLabels = arg3
        self._arg4ValueLabels = arg4

    def _updateLabels(self):            
        if(self._chosenEffectId == EffectTypes.Zoom):
            self._setLabels("Amount:", "XY ratio", "X position", "Y position", "Zoom mode")
            self._setupValueLabels(None, None, None, None, self._zoomModes.getChoices())
        if(self._chosenEffectId == EffectTypes.Scroll):
            self._setLabels("X amount:", "Y amount", "Scroll mode", None, None)
            self._setupValueLabels(None, None, self._scrollModes.getChoices(), None, None)
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
            self._setLabels("Contrast:", "Brightness", "Mode", None, None)
            self._setupValueLabels(None, None, self._contrastModes.getChoices(), None, None)
        elif(self._chosenEffectId == EffectTypes.HueSaturation):
            self._setLabels("Color rotate:", "Saturation", "Brightness", "Mode", None)
            self._setupValueLabels(None, None, None, self._hueSatModes.getChoices(), None)
        elif(self._chosenEffectId == EffectTypes.Colorize):
            self._setLabels("Amount:", "Red", "Green", "Blue", "Mode")
            self._setupValueLabels(None, None, None, None, self._colorizeModes.getChoices())
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
        self._fixEffectGuiLayout()

    def updateEffectList(self, effectConfiguration, selectedName):
        self._effectListWidget.DeleteAllItems()
        selectedIndex = -1
        for effectConfig in effectConfiguration.getList():
            config = effectConfig.getConfigHolder()
            effectName = config.getValue("Effect")
            effectId = getEffectId(effectName)
            if(effectId != None):
                bitmapId = self._fxIdImageIndex[effectId]
            else:
                bitmapId = self._blankEffectIndex
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

    def updateEffectListHeight(self, height):
        pass
#        if((self._oldListHeight != height) and (height >= 100)):
#            self._effectListWidget.SetSize((340, height))
#            self._buttonPlane.SetPosition((0,height + 5))
##            self._mainEffectsListPlane.SetSize((340,height+40))
#            self._oldListHeight = height

    def updateGui(self, effectTemplate, midiNote, effectId):
        self._midiNote = midiNote
        self._activeEffectId = effectId
        config = effectTemplate.getConfigHolder()
        self._startConfigName = config.getValue("Name")
        self._templateNameField.SetValue(self._startConfigName)
        self._setEffect(config.getValue("Effect"))
        self._ammountField.SetValue(config.getValue("Amount"))
        self._arg1Field.SetValue(config.getValue("Arg1"))
        self._arg2Field.SetValue(config.getValue("Arg2"))
        self._arg3Field.SetValue(config.getValue("Arg3"))
        self._arg4Field.SetValue(config.getValue("Arg4"))

class FadeGui(object):
    def __init__(self, mainConfing, midiTiming, modulationGui):
        self._mainConfig = mainConfing
        self._midiTiming = midiTiming
        self._modulationGui = modulationGui
        self._midiModulation = MidiModulation(None, self._midiTiming)
        self._selectedEditor = self.EditSelected.Unselected
        self._fadeModes = FadeMode()
        self._fadeListSelectedIndex = -1

        self._blankFadeBitmap = wx.Bitmap("graphics/modulationBlank.png") #@UndefinedVariable
        self._fadeBlackBitmap = wx.Bitmap("graphics/fadeToBlack.png") #@UndefinedVariable
        self._fadeWhiteBitmap = wx.Bitmap("graphics/fadeToWhite.png") #@UndefinedVariable

        self._fadeModeImages = [self._fadeBlackBitmap, self._fadeWhiteBitmap]
        self._fadeModeLabels = self._fadeModes.getChoices()

    def getFadeModeLists(self):
        return (self._fadeModeImages, self._fadeModeLabels)

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

        templateNameSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText1 = wx.StaticText(self._mainFadeGuiPlane, wx.ID_ANY, "Name:") #@UndefinedVariable
        self._templateNameField = wx.TextCtrl(self._mainFadeGuiPlane, wx.ID_ANY, "Default", size=(200, -1)) #@UndefinedVariable
        self._templateNameField.SetInsertionPoint(0)
        templateNameSizer.Add(tmpText1, 1, wx.ALL, 5) #@UndefinedVariable
        templateNameSizer.Add(self._templateNameField, 2, wx.ALL, 5) #@UndefinedVariable
        self._mainFadeGuiSizer.Add(templateNameSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        fadeModeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText2 = wx.StaticText(self._mainFadeGuiPlane, wx.ID_ANY, "Mode:") #@UndefinedVariable
        self._fadeModesField = wx.ComboBox(self._mainFadeGuiPlane, wx.ID_ANY, size=(200, -1), choices=["Black"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateChoices(self._fadeModesField, self._fadeModes.getChoices, "Black", "Black")
        fadeModeButton = wx.Button(self._mainFadeGuiPlane, wx.ID_ANY, 'Help', size=(60,-1)) #@UndefinedVariable
        fadeModeButton.SetBackgroundColour(wx.Colour(210,240,210)) #@UndefinedVariable
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
        self._fadeModulationButton = wx.Button(self._mainFadeGuiPlane, wx.ID_ANY, 'Edit', size=(60,-1)) #@UndefinedVariable
        self._fadeModulationButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainFadeGuiPlane.Bind(wx.EVT_BUTTON, self._onFadeModulationEdit, id=self._fadeModulationButton.GetId()) #@UndefinedVariable
        fadeModulationSizer.Add(tmpText3, 1, wx.ALL, 5) #@UndefinedVariable
        fadeModulationSizer.Add(self._fadeModulationField, 2, wx.ALL, 5) #@UndefinedVariable
        fadeModulationSizer.Add(self._fadeModulationButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainFadeGuiSizer.Add(fadeModulationSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        levelModulationSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText3 = wx.StaticText(self._mainFadeGuiPlane, wx.ID_ANY, "Level modulation:") #@UndefinedVariable
        self._levelModulationField = wx.TextCtrl(self._mainFadeGuiPlane, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._levelModulationField.SetInsertionPoint(0)
        self._levelModulationButton = wx.Button(self._mainFadeGuiPlane, wx.ID_ANY, 'Edit', size=(60,-1)) #@UndefinedVariable
        self._levelModulationButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainFadeGuiPlane.Bind(wx.EVT_BUTTON, self._onLevelModulationEdit, id=self._levelModulationButton.GetId()) #@UndefinedVariable
        levelModulationSizer.Add(tmpText3, 1, wx.ALL, 5) #@UndefinedVariable
        levelModulationSizer.Add(self._levelModulationField, 2, wx.ALL, 5) #@UndefinedVariable
        levelModulationSizer.Add(self._levelModulationButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainFadeGuiSizer.Add(levelModulationSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable


        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = wx.Button(self._mainFadeGuiPlane, wx.ID_ANY, 'Close') #@UndefinedVariable
        closeButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainFadeGuiPlane.Bind(wx.EVT_BUTTON, self._onCloseButton, id=closeButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 1, wx.ALL, 5) #@UndefinedVariable
        saveButton = wx.Button(self._mainFadeGuiPlane, wx.ID_ANY, 'Save') #@UndefinedVariable
        saveButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainFadeGuiPlane.Bind(wx.EVT_BUTTON, self._onSaveButton, id=saveButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(saveButton, 1, wx.ALL, 5) #@UndefinedVariable
        listButton = wx.Button(self._mainFadeGuiPlane, wx.ID_ANY, 'List') #@UndefinedVariable
        listButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainFadeGuiPlane.Bind(wx.EVT_BUTTON, self._onListButton, id=listButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(listButton, 1, wx.ALL, 5) #@UndefinedVariable
        self._mainFadeGuiSizer.Add(self._buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

    def setupFadeListGui(self, plane, sizer, parentSizer, parentClass):
        self._mainFadeListPlane = plane
        self._mainFadeListGuiSizer = sizer
        self._parentSizer = parentSizer
        self._hideFadeListCallback = parentClass.hideFadeListGui

        self._fadeImageList = wx.ImageList(25, 16) #@UndefinedVariable

        self._modeIdImageIndex = []
        index = self._fadeImageList.Add(self._fadeWhiteBitmap)
        self._modeIdImageIndex.append(index)
        index = self._fadeImageList.Add(self._fadeBlackBitmap)
        self._modeIdImageIndex.append(index)

        self._modIdImageIndex = []
        for i in range(self._modulationGui.getModulationImageCount()):
            bitmap = self._modulationGui.getModulationImageBitmap(i)
            index = self._fadeImageList.Add(bitmap)
            self._modIdImageIndex.append(index)

        self._oldListHeight = 376
        self._fadeListWidget = ultimatelistctrl.UltimateListCtrl(self._mainFadeListPlane, id=wx.ID_ANY, size=(220,self._oldListHeight), agwStyle = wx.LC_REPORT | wx.LC_HRULES | wx.LC_SINGLE_SEL) #@UndefinedVariable
        self._fadeListWidget.SetImageList(self._fadeImageList, wx.IMAGE_LIST_SMALL) #@UndefinedVariable
        self._fadeListWidget.SetBackgroundColour((170,170,170))

        self._fadeListWidget.InsertColumn(0, 'Name', width=150)
        self._fadeListWidget.InsertColumn(1, 'Fade', width=34)
        self._fadeListWidget.InsertColumn(2, 'Level', width=36)

        self._mainFadeListGuiSizer.Add(self._fadeListWidget, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._mainFadeListPlane.Bind(ultimatelistctrl.EVT_LIST_COL_CLICK, self._onListItemMouseDown, self._fadeListWidget)
        self._mainFadeListPlane.Bind(ultimatelistctrl.EVT_LIST_ITEM_SELECTED, self._onListItemSelected, self._fadeListWidget)
        self._mainFadeListPlane.Bind(ultimatelistctrl.EVT_LIST_ITEM_DESELECTED, self._onListItemDeselected, self._fadeListWidget)
        self._mainFadeListPlane.Bind(ultimatelistctrl.EVT_LIST_BEGIN_DRAG, self._onListDragStart, self._fadeListWidget)
        self._fadeListWidget.Bind(wx.EVT_LEFT_DCLICK, self._onListDoubbleClick) #@UndefinedVariable

        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = wx.Button(self._mainFadeListPlane, wx.ID_ANY, 'Close') #@UndefinedVariable
        closeButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainFadeListPlane.Bind(wx.EVT_BUTTON, self._onListCloseButton, id=closeButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 1, wx.ALL, 5) #@UndefinedVariable
        duplicateButton = wx.Button(self._mainFadeListPlane, wx.ID_ANY, 'Duplicate') #@UndefinedVariable
        duplicateButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainFadeListPlane.Bind(wx.EVT_BUTTON, self._onListDuplicateButton, id=duplicateButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(duplicateButton, 1, wx.ALL, 5) #@UndefinedVariable
        deleteButton = wx.Button(self._mainFadeListPlane, wx.ID_ANY, 'Delete') #@UndefinedVariable
        deleteButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainFadeListPlane.Bind(wx.EVT_BUTTON, self._onListDeleteButton, id=deleteButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(deleteButton, 1, wx.ALL, 5) #@UndefinedVariable
        self._mainFadeListGuiSizer.Add(self._buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

    def _onFadeModeChosen(self, event):
        pass

    def _onFadeModeHelp(self, event):
        text = """
Decides if this image fades to black or white.
"""
        dlg = wx.MessageDialog(self._mainFadeGuiPlane, text, 'Fade mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _highlightButton(self, selected):
        if(selected == self.EditSelected.Fade):
            self._fadeModulationButton.SetBackgroundColour(wx.Colour(180,180,255)) #@UndefinedVariable
        else:
            self._fadeModulationButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        if(selected == self.EditSelected.Level):
            self._levelModulationButton.SetBackgroundColour(wx.Colour(180,180,255)) #@UndefinedVariable
        else:
            self._levelModulationButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable

    def unselectButton(self):
        self._selectedEditor = self.EditSelected.Unselected
        self._highlightButton(self._selectedEditor)

    def _onFadeModulationEdit(self, event):
        self._showModulationCallback()
        self._fixEffectGuiLayout()
        self._selectedEditor = self.EditSelected.Fade
        self._highlightButton(self._selectedEditor)
        self._mainConfig.updateModulationGui(self._fadeModulationField.GetValue(), self._fadeModulationField, self.unselectButton, None)

    def _onLevelModulationEdit(self, event):
        self._showModulationCallback()
        self._fixEffectGuiLayout()
        self._selectedEditor = self.EditSelected.Level
        self._highlightButton(self._selectedEditor)
        self._mainConfig.updateModulationGui(self._levelModulationField.GetValue(), self._levelModulationField, self.unselectButton, None)

    def _onCloseButton(self, event):
        self._hideFadeCallback()
        self._hideModulationCallback()
        self._selectedEditor = self.EditSelected.Unselected
        self._highlightButton(self._selectedEditor)
        self._mainConfig.stopModulationGui()

    def _onListCloseButton(self, event):
        self._hideModulationCallback()
        self._hideFadeCallback()
        self._hideFadeListCallback()
        self._selectedEditor = self.EditSelected.Unselected
        self._highlightButton(self._selectedEditor)
        self._mainConfig.stopModulationGui()

    def _onListDuplicateButton(self, event):
        if(self._fadeListSelectedIndex >= 0):
            fadeTemplate = self._mainConfig.getFadeTemplateByIndex(self._fadeListSelectedIndex)
            if(fadeTemplate != None):
                fadeName = fadeTemplate.getName()
                newName = self._mainConfig.duplicateFadeTemplate(fadeName)
                self._mainConfig.updateFadeList(newName)

    def _onListDeleteButton(self, event):
        if(self._fadeListSelectedIndex >= 0):
            fadeTemplate = self._mainConfig.getFadeTemplateByIndex(self._fadeListSelectedIndex)
            if(fadeTemplate != None):
                fadeName = fadeTemplate.getName()
                inUseNumber = self._mainConfig.countNumberOfTimeFadeTemplateUsed(fadeName)
                text = "Are you sure you want to delete \"%s\"? (It is used %d times)" % (fadeName, inUseNumber)
                dlg = wx.MessageDialog(self._mainFadeListPlane, text, 'Move?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                dlg.Destroy()
                if(result == True):
                    self._mainConfig.deleteFadeTemplate(fadeName)
                    self._mainConfig.verifyFadeTemplateUsed()
                    self._mainConfig.updateFadeList(None)
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
        self._setDragCursor()

    def getDraggedFxIndex(self):
        dragIndex = self._fadeListDraggedIndex # Gets updated by state calls
        if(dragIndex > -1):
            self._fadeListWidget.SetItemState(dragIndex, 0, wx.LIST_STATE_SELECTED) #@UndefinedVariable
            self._fadeListWidget.SetItemState(dragIndex, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED) #@UndefinedVariable
        self._fadeListWidget.SetCursor(wx.StockCursor(wx.CURSOR_ARROW)) #@UndefinedVariable
        return dragIndex

    def _onListDoubbleClick(self, event):
        self._fadeListDraggedIndex = -1
        fadeTemplate = self._mainConfig.getFadeTemplateByIndex(self._fadeListSelectedIndex)
        if(fadeTemplate != None):
            self.updateGui(fadeTemplate, None)
            self._showFadeCallback()

    def _onListButton(self, event):
        fadeConfigName = self._templateNameField.GetValue()
        self._mainConfig.updateFadeList(fadeConfigName)
        self._showFadeListCallback()

    def _onSaveButton(self, event):
        saveName = self._templateNameField.GetValue()
        oldTemplate = self._mainConfig.getFadeTemplate(saveName)
        rename = False
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
                    text = "Do you want to move all instances of \"%s\" to the new configuration \"%s\" (%d in all)" % (self._startConfigName, saveName, inUseNumber)
                    dlg = wx.MessageDialog(self._mainFadeGuiPlane, text, 'Move?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                    result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                    dlg.Destroy()
                    if(result == True):
                        rename = True
            else:
                text = "Do you want to move all instances of \"%s\" to the new configuration \"%s\" (%d in all)" % (self._startConfigName, saveName, inUseNumber)
                dlg = wx.MessageDialog(self._mainFadeGuiPlane, text, 'Move?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                dlg.Destroy()
                if(result == True):
                    rename = True
        fadeMode = self._fadeModesField.GetValue()
        fadeMod = self._midiModulation.validateModulationString(self._fadeModulationField.GetValue())
        levelMod = self._midiModulation.validateModulationString(self._levelModulationField.GetValue())
        if(cancel == True):
            self._fadeModesField.SetValue(fadeMode)
            self._fadeModulationField.SetValue(fadeMod)
            self._levelModulationField.SetValue(levelMod)
        else:
            if(oldTemplate == None):
                print "Make new template..."
                savedTemplate = self._mainConfig.makeFadeTemplate(saveName, fadeMode, fadeMod, levelMod)
                if(rename == True):
                    self._mainConfig.renameFadeTemplateUsed(self._startConfigName, saveName)
                self._mainConfig.verifyFadeTemplateUsed()
            else:
                oldTemplate.update(fadeMode, fadeMod, levelMod)
                savedTemplate = oldTemplate
            self.updateGui(savedTemplate, None)
            self._mainConfig.updateNoteGui()
            self._mainConfig.updateMixerGui()
            self._mainConfig.updateFadeList(saveName)

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

    def updateFadeModeThumb(self, widget, fadeMode):
        if(fadeMode == "None"):
            widget.setBitmaps(self._blankFadeBitmap, self._blankFadeBitmap)
        elif(fadeMode == "White"):
            widget.setBitmaps(self._fadeWhiteBitmap, self._fadeWhiteBitmap)
        else:
            widget.setBitmaps(self._fadeBlackBitmap, self._fadeBlackBitmap)

    def updateFadeGuiButtons(self, fadeTemplate, modeWidget, modulationWidget, levelWidget):
        if(fadeTemplate == None):
            self.updateFadeModeThumb(modeWidget, "None")
            self._mainConfig.updateModulationGuiButton(modulationWidget, "None")
            self._mainConfig.updateModulationGuiButton(levelWidget, "None")
        else:
            config = fadeTemplate.getConfigHolder()
            fadeMode = config.getValue("Mode")
            self.updateFadeModeThumb(modeWidget, fadeMode)
            fadeModulation = config.getValue("Modulation")
            self._mainConfig.updateModulationGuiButton(modulationWidget, fadeModulation)
            fadeLevel = config.getValue("Level")
            self._mainConfig.updateModulationGuiButton(levelWidget, fadeLevel)

    def updateFadeList(self, effectConfiguration, selectedName):
        self._fadeListWidget.DeleteAllItems()
        selectedIndex = -1
        for effectConfig in effectConfiguration.getList():
            config = effectConfig.getConfigHolder()
            selectedMode = config.getValue("Mode")
            if(selectedMode.lower() == "white"):
                bitmapId = self._modeIdImageIndex[0]
            else:
                bitmapId = self._modeIdImageIndex[1]
            configName = effectConfig.getName()
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

            if(index % 2):
                self._fadeListWidget.SetItemBackgroundColour(index, wx.Colour(170,170,170)) #@UndefinedVariable
            else:
                self._fadeListWidget.SetItemBackgroundColour(index, wx.Colour(190,190,190)) #@UndefinedVariable
        if(selectedIndex > -1):
            self._fadeListSelectedIndex = selectedIndex
            self._fadeListWidget.Select(selectedIndex)

    def updateGui(self, fadeTemplate, editField):
        config = fadeTemplate.getConfigHolder()
        self._selectedEditor = self.EditSelected.Unselected
        self._highlightButton(self._selectedEditor)
        self._startConfigName = config.getValue("Name")
        self._templateNameField.SetValue(self._startConfigName)
        self._updateChoices(self._fadeModesField, self._fadeModes.getChoices, config.getValue("Mode"), "Black")
        self._fadeModulationField.SetValue(config.getValue("Modulation"))
        self._levelModulationField.SetValue(config.getValue("Level"))
        if(editField == "Modulation"):
            self._selectedEditor = self.EditSelected.Fade
            self._highlightButton(self._selectedEditor)
            self._mainConfig.updateModulationGui(self._fadeModulationField.GetValue(), self._fadeModulationField, self.unselectButton, self._onSaveButton)
        if(editField == "Level"):
            self._selectedEditor = self.EditSelected.Level
            self._highlightButton(self._selectedEditor)
            self._mainConfig.updateModulationGui(self._levelModulationField.GetValue(), self._levelModulationField, self.unselectButton, self._onSaveButton)

