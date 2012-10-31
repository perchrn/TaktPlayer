'''
Created on 26. jan. 2012

@author: pcn
'''
import os
import logging
import wx
from wx.lib.scrolledpanel import ScrolledPanel #@UnresolvedImport
from widgets.PcnImageButton import PcnKeyboardButton, PcnImageButton, addTrackButtonFrame, EVT_DRAG_DONE_EVENT, EVT_DRAG_START_EVENT,\
    PcnPopupMenu, EVT_DOUBLE_CLICK_EVENT

from network.GuiClient import GuiClient
from midi.MidiUtilities import noteToNoteString
import time
from configurationGui.Configuration import Configuration
from configurationGui.MediaPoolConfig import MediaFileGui
from configuration.ConfigurationHolder import xmlToPrettyString
import subprocess
from utilities.MultiprocessLogger import MultiprocessLogger
from configurationGui.MediaMixerConfig import MediaTrackGui
from media.VideoConvert import VideoConverterDialog, VideoCopyDialog
from midi.TcpMidiListner import TcpMidiListner
from midi.MidiTiming import MidiTiming
from midi.MidiStateHolder import DummyMidiStateHolder
import shutil
import sys
from configurationGui.FileMenu import ConfigOpenDialog, ConfigNewDialog,\
    ConfigGuiDialog, ConfigPlayerDialog
from video.media.MediaFileModes import forceUnixPath

APP_NAME = "TaktPlayerGui"

class TaskHolder(object):
    class States():
        Init, Sendt, Received, Done = range(4)

    class RequestTypes():
        ActiveNotes, Note, File, Track, ConfigState, EffectState, Configuration, SendConfig, PlayerConfiguration, LatestControllers, ConfigFileList, Preview = range(12)

    def __init__(self, description, taskType, widget, uniqueId = None):
        self._desc = description
        self._type = taskType
        self._widget = widget
        self._uniqueueId = uniqueId
        self._extraData = None
        self._state = self.States.Init
        self._stateTime = time.time()
        self._startTime = self._stateTime
        self._timeout = 20.0
        if((self._type == self.RequestTypes.Track) or (self._type == self.RequestTypes.Preview) or (self._type == self.RequestTypes.EffectState)):
            self._timeout = 5.0

    def getDescription(self):
        return self._desc

    def getType(self):
        return self._type

    def getUniqueId(self):
        return self._uniqueueId

    def getWidget(self):
        return self._widget

    def setExtraData(self, data):
        self._extraData = data

    def getExtraData(self):
        return self._extraData

    def isStale(self, currentTime):
        if((currentTime - self._stateTime) > self._timeout):
            return True
        else:
            return False

    def setState(self, state):
        self._state = state
        self._stateTime = time.time()

    def taskDone(self):
        self.setState(self.States.Done)
#        print self._desc + " task done in " + str(self._stateTime - self._startTime) + " secs."

class FileDrop(wx.FileDropTarget): #@UndefinedVariable
    def __init__(self, widgetId, callbackFunction):
        wx.FileDropTarget.__init__(self) #@UndefinedVariable
        self._widgetId = widgetId
        self._callbackFunction = callbackFunction

    def OnDropFiles(self, x, y, filenames):
        nameId = 0
        for name in filenames:
            self._callbackFunction(self._widgetId, name, nameId)
            nameId += 1


class TrackOverviewSettings(object):
    def __init__(self, panel, midiChannel, parent, cursorWidgetList):
        self._midiChannel = midiChannel
        extraSpace = ""
        if(self._midiChannel < 9):
            extraSpace = " "
        wx.StaticText(panel, wx.ID_ANY, extraSpace + str(self._midiChannel + 1), pos=(2, 4+36*self._midiChannel)) #@UndefinedVariable
        self._trackButton = PcnKeyboardButton(panel, parent._trackThumbnailBitmap, (16, 4+36*self._midiChannel), wx.ID_ANY, size=(42, 32), isBlack=False) #@UndefinedVariable
        cursorWidgetList.append(self._trackButton)
        self._trackButton.setFrqameAddingFunction(addTrackButtonFrame)
        self._trackButton.setBitmap(parent._emptyBitMap)
        self._trackPlayButton = PcnImageButton(panel, parent._trackPlayBitmap, parent._trackPlayPressedBitmap, (60, 4+36*self._midiChannel), wx.ID_ANY, size=(15, 11)) #@UndefinedVariable
        self._trackEditButton = PcnImageButton(panel, parent._trackEditBitmap, parent._trackEditPressedBitmap, (60, 15+36*self._midiChannel), wx.ID_ANY, size=(15, 11)) #@UndefinedVariable
        self._trackStopButton = PcnImageButton(panel, parent._trackStopBitmap, parent._trackStopPressedBitmap, (60, 26+36*self._midiChannel), wx.ID_ANY, size=(15, 11)) #@UndefinedVariable
        cursorWidgetList.append(self._trackPlayButton)
        cursorWidgetList.append(self._trackEditButton)
        cursorWidgetList.append(self._trackStopButton)
        self._activeTrackNote = -1
        self._trackButtonWidgetId = self._trackButton.GetId()
        self._trackStopWidgetsId = self._trackStopButton.GetId()
        self._trackEditWidgetsId = self._trackEditButton.GetId()
        self._trackPlayWidgetsId = self._trackPlayButton.GetId()
        self._trackButton.Bind(wx.EVT_BUTTON, parent._onTrackButton) #@UndefinedVariable
        self._trackButton.enableDoubleClick()
        self._trackButton.Bind(EVT_DOUBLE_CLICK_EVENT, parent._onTrackButtonDouble) #@UndefinedVariable
        self._trackPlayButton.Bind(wx.EVT_BUTTON, parent._onTrackPlayButton) #@UndefinedVariable
        self._trackEditButton.Bind(wx.EVT_BUTTON, parent._onTrackEditButton) #@UndefinedVariable
        self._trackStopButton.Bind(wx.EVT_BUTTON, parent._onTrackStopButton) #@UndefinedVariable

    def hasTrackWidgetId(self, widgetId):
        return self._trackButtonWidgetId == widgetId

    def hasPlayWidgetId(self, widgetId):
        return self._trackPlayWidgetsId == widgetId

    def hasEditWidgetId(self, widgetId):
        return self._trackEditWidgetsId == widgetId

    def hasStopWidgetId(self, widgetId):
        return self._trackStopWidgetsId == widgetId

    def setPreFxWidget(self, widget):
        self._trackPreFxWidget = widget
        self._trackPreFxWidgetId = widget.GetId()

    def hasPreFxWidgetId(self, widgetId):
        return self._trackPreFxWidgetId == widgetId

    def getPreFxWidget(self):
        return self._trackPreFxWidget

    def setMixWidget(self, widget):
        self._trackMixWidget = widget
        self._trackMixWidgetId = widget.GetId()

    def hasMixWidgetId(self, widgetId):
        return self._trackMixWidgetId == widgetId

    def getMixWidget(self):
        return self._trackMixWidget

    def setLvlWidget(self, widget):
        self._trackLvlWidget = widget
        self._trackLvlWidgetId = widget.GetId()

    def hasLvlWidgetId(self, widgetId):
        return self._trackLvlWidgetId == widgetId

    def getLvlWidget(self):
        return self._trackLvlWidget

    def setPostFxWidget(self, widget):
        self._trackPostFxWidget = widget
        self._trackPostFxWidgetId = widget.GetId()

    def hasPostFxWidgetId(self, widgetId):
        return self._trackPostFxWidgetId == widgetId

    def getPostFxWidget(self):
        return self._trackPostFxWidget

    def setSelected(self, isMidiEnabled):
        self._trackButton.setSelected()
        if(isMidiEnabled == True):
            self._trackPlayButton.setSelected()

    def unsetSelected(self):
        self._trackButton.unsetSelected()
        self._trackPlayButton.unsetSelected()

    def clearThumb(self):
        self._trackButton.clearBitmap()

    def setThumb(self, bitmap):
        self._trackButton.setBitmap(bitmap)

    def setActiveNoteId(self, note):
        self._activeTrackNote = note

    def getActiveNoteId(self):
        return self._activeTrackNote

class TaktPlayerGui(wx.Frame): #@UndefinedVariable
    def __init__(self, parent, configDir, debugMode, title):
        super(TaktPlayerGui, self).__init__(parent, title=title, size=(800, 600))
        self._debugModeOn = debugMode
        self._baseTitle = title
        self._activeConfig = ""
        self._serverConfigIsSaved = False
        self._updateTitle(self._activeConfig)

        wxIcon = wx.Icon(os.path.normpath("graphics/TaktGui.ico"), wx.BITMAP_TYPE_ICO) #@UndefinedVariable
        self.SetIcon(wxIcon)

        self._configuration = Configuration(configDir)
        self._configuration.setLatestMidiControllerRequestCallback(self.getLatestControllers)

        windowSizeX, windowSizeY = self._configuration.getWindowSize()
        configPositionX, configPositionY = self._configuration.getWindowPosition()
        if((windowSizeX >= 500) and (windowSizeX >= 400)):
            self.SetSize((windowSizeX, windowSizeY))
        if((configPositionX >= 0) and (configPositionY >= 0)):
#            print "DEBUG pcn: cfgPos!!!!!!!!!!!!!!!!!!!!!!"
            self.SetPosition((configPositionX, configPositionY))

        self._videoDirectory = self._configuration.getGuiVideoDir()
        self._videoSaveSubDir = ""
        self._videoScaleX = self._configuration.getVideoScaleX()
        if(self._videoScaleX == None):
            self._videoScaleX = -1
        self._videoScaleY = self._configuration.getVideoScaleY()
        if(self._videoScaleY == None):
            self._videoScaleY = -1
        if((self._videoScaleX == -1) or (self._videoScaleY == -1)):
            self._videoScaleMode = "No scale"
        else:
            self._videoScaleMode = "Custom"
        self._videoCropMode = "No crop"
        self._convertionWentOk = False
        self._convertionOutputFileName = ""
        self._playerConfigString = None
        self._oldServerConfigurationString = ""
        self._oldGuiConfigurationString = ""
        self._oldServerConfigList = ""
        self._configurationFilesList = ["N/A"]
        self._oldServerActiveConfig = ""

        self.SetBackgroundColour((120,120,120))
        self._subPanelsList = []
        self._subWidgetList = []
        self._fxWidgetsList = [] #For destination cursor type on fx drag
#        self._fadeWidgetsList = [] #For destination cursor type on fade drag
#        self._timeWidgetsList = [] #For destination cursor type on time modulation drag

        self._mainSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._menuSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        menuSeperatorSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._trackAndEditAreaSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        editAreaSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        trackAndPreviewSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        midiTrackSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        keyboardSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---

        self._menuPanel =  wx.Panel(self, wx.ID_ANY, size=(3000,29)) #@UndefinedVariable
        self._subPanelsList.append(self._menuPanel)
        self._menuPanel.SetBackgroundColour(wx.Colour(200,200,200)) #@UndefinedVariable
        self._menuPanel.SetSizer(self._menuSizer) #@UndefinedVariable
        menuSeperatorPannel = wx.Panel(self, wx.ID_ANY, size=(3000,2)) #@UndefinedVariable
        menuSeperatorPannel.SetBackgroundColour(wx.Colour(200,200,200)) #@UndefinedVariable
        menuSeperatorPannel.SetSizer(menuSeperatorSizer) #@UndefinedVariable

        self._scrollingKeyboardPannel = ScrolledPanel(parent=self, id=wx.ID_ANY, size=(-1,87)) #@UndefinedVariable
        self._subPanelsList.append(self._scrollingKeyboardPannel)
        self._scrollingKeyboardPannel.SetupScrolling(True, False)
        self._scrollingKeyboardPannel.SetSizer(keyboardSizer)
        self._keyboardPanel = wx.Panel(self._scrollingKeyboardPannel, wx.ID_ANY, size=(3082,60)) #@UndefinedVariable
        self._scrollingKeyboardPannel.SetBackgroundColour(wx.Colour(0,0,0)) #@UndefinedVariable
        keyboardSizer.Add(self._keyboardPanel, wx.EXPAND, 0) #@UndefinedVariable

        self._scrollingMidiTrackPanel = wx.lib.scrolledpanel.ScrolledPanel(parent=self, id=wx.ID_ANY, size=(220,-1)) #@UndefinedVariable
        self._subPanelsList.append(self._scrollingMidiTrackPanel)
        self._scrollingMidiTrackPanel.SetupScrolling(False, True)
        self._scrollingMidiTrackPanel.SetSizer(midiTrackSizer)
        self._midiTrackPanel = wx.Panel(self._scrollingMidiTrackPanel, wx.ID_ANY, size=(98,1200)) #@UndefinedVariable
        self._subPanelsList.append(self._midiTrackPanel)
        self._scrollingMidiTrackPanel.SetBackgroundColour(wx.Colour(170,170,170)) #@UndefinedVariable
        midiTrackSizer.Add(self._midiTrackPanel, wx.EXPAND, 0) #@UndefinedVariable

        self._trackGui = MediaTrackGui(self._configuration)
        self._previewPanel = wx.Panel(self, wx.ID_ANY, size=(250,120)) #@UndefinedVariable
        self._subPanelsList.append(self._previewPanel)
        self._previewPanel.SetBackgroundColour(wx.Colour(200,200,200)) #@UndefinedVariable
        self._trackGui.setupPreviewGui(self._previewPanel, self._subWidgetList)

        self._scrollingEditAreaPanel = wx.lib.scrolledpanel.ScrolledPanel(parent=self, id=wx.ID_ANY, size=(-1,-1)) #@UndefinedVariable
        self._scrollingEditAreaPanel.SetupScrolling(True, True)
        self._scrollingEditAreaPanel.SetSizer(editAreaSizer)
        self._scrollingEditAreaPanel.SetBackgroundColour((100,100,100))

        self._configuration.setGetActiveNoteForTrackConfigCallback(self.getNoteConfig)
        self._configuration.setMixerGui(self._trackGui)
        self._noteGui = MediaFileGui(self._scrollingEditAreaPanel, self._configuration, self._trackGui, self._requestNote, self, self._subWidgetList, self._fxWidgetsList)
        self._configuration.setNoteGui(self._noteGui)
        trackAndPreviewSizer.Add(self._scrollingMidiTrackPanel, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        trackAndPreviewSizer.Add(self._previewPanel, proportion=0, flag=wx.EXPAND) #@UndefinedVariable        
        self._trackAndEditAreaSizer.Add(trackAndPreviewSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._trackAndEditAreaSizer.Add(self._scrollingEditAreaPanel, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._mainSizer.Add(self._menuSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._mainSizer.Add(menuSeperatorSizer, proportion=0) #@UndefinedVariable
        self._mainSizer.Add(self._trackAndEditAreaSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._mainSizer.Add(self._scrollingKeyboardPannel, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        self._fileMenuBitmap = wx.Bitmap("graphics/fileButton.png") #@UndefinedVariable
        self._fileMenuPressedBitmap = wx.Bitmap("graphics/fileButtonPressed.png") #@UndefinedVariable

        self._fileMenuOpen = wx.Bitmap("graphics/menuButtonFile.png") #@UndefinedVariable
        self._fileMenuNew = wx.Bitmap("graphics/menuButtonFilePluss.png") #@UndefinedVariable
        self._fileMenuSave = wx.Bitmap("graphics/menuButtonDisk.png") #@UndefinedVariable
        self._fileMenuConfig = wx.Bitmap("graphics/menuButtonConfig.png") #@UndefinedVariable
        self._fileMenuExit = wx.Bitmap("graphics/menuButtonExit.png") #@UndefinedVariable

        self._fileImages = [self._fileMenuOpen, self._fileMenuNew, self._fileMenuSave, self._fileMenuConfig, self._fileMenuConfig, self._fileMenuExit]
        self._fileLabels = ["Open", "New", "Save", "Player Config", "GUI Config", "Exit"]

        self._sendConfigBitmap = wx.Bitmap("graphics/sendConfigButton.png") #@UndefinedVariable
        self._sendConfigPressedBitmap = wx.Bitmap("graphics/sendConfigButtonPressed.png") #@UndefinedVariable
        self._sendConfigNoContactBitmap = wx.Bitmap("graphics/sendConfigButtonNoContact.png") #@UndefinedVariable
        self._sendConfigNoContactRedBitmap = wx.Bitmap("graphics/sendConfigButtonNoContactRed.png") #@UndefinedVariable
        self._sendConfigNoNewConfigBitmap = wx.Bitmap("graphics/sendConfigButtonNoNewConfig.png") #@UndefinedVariable
        self._sendConfigSendingBitmap = wx.Bitmap("graphics/sendConfigButtonSending.png") #@UndefinedVariable

        self._midiOnBitmap = wx.Bitmap("graphics/midiOnButton.png") #@UndefinedVariable
        self._midiOnPressedBitmap = wx.Bitmap("graphics/midiOnButtonPressed.png") #@UndefinedVariable
        self._midiOffBitmap = wx.Bitmap("graphics/midiOnButtonOff.png") #@UndefinedVariable
        self._midiOffPressedBitmap = wx.Bitmap("graphics/midiOnButtonOffPressed.png") #@UndefinedVariable
        self._midiNoContactBitmap = wx.Bitmap("graphics/midiOnButtonNoContact.png") #@UndefinedVariable

        self._inputGreenBitmap = wx.Bitmap("graphics/inputIndicatorGreen.png") #@UndefinedVariable
        self._inputGrayBitmap = wx.Bitmap("graphics/inputIndicatorGray.png") #@UndefinedVariable

        self._fileButton = PcnImageButton(self._menuPanel, self._fileMenuBitmap, self._fileMenuPressedBitmap, (-1, -1), wx.ID_ANY, size=(46, 17)) #@UndefinedVariable
        self._fileButtonPopup = PcnPopupMenu(self, self._fileImages, self._fileLabels, self._onFileMenuItemChosen)
        self._fileButton.Bind(wx.EVT_BUTTON, self._onFileButton) #@UndefinedVariable
        self._sendButton = PcnImageButton(self._menuPanel, self._sendConfigNoNewConfigBitmap, self._sendConfigNoNewConfigBitmap, (-1, -1), wx.ID_ANY, size=(93, 17)) #@UndefinedVariable
        self._sendButton.Bind(wx.EVT_BUTTON, self._onSendButton) #@UndefinedVariable
        self._midiButton = PcnImageButton(self._menuPanel, self._sendConfigNoNewConfigBitmap, self._sendConfigNoNewConfigBitmap, (-1, -1), wx.ID_ANY, size=(108, 17)) #@UndefinedVariable
        self._midiButton.Bind(wx.EVT_BUTTON, self._midiToggle) #@UndefinedVariable
        self._timingField = wx.TextCtrl(self._menuPanel, wx.ID_ANY, "N/A", size=(70, -1)) #@UndefinedVariable
        self._bpmField = wx.TextCtrl(self._menuPanel, wx.ID_ANY, "N/A", size=(50, -1)) #@UndefinedVariable
        self._inputButton = PcnImageButton(self._menuPanel, self._inputGrayBitmap, self._inputGrayBitmap, (-1, -1), wx.ID_ANY, size=(34, 17)) #@UndefinedVariable
        self._menuSizer.Add(self._fileButton, 0, wx.EXPAND|wx.ALL, 3) #@UndefinedVariable
        self._menuSizer.Add(self._sendButton, 0, wx.EXPAND|wx.ALL, 3) #@UndefinedVariable
        self._menuSizer.Add(self._midiButton, 0, wx.EXPAND|wx.ALL, 3) #@UndefinedVariable
        self._menuSizer.Add(self._timingField, 0, wx.EXPAND|wx.ALL, 3) #@UndefinedVariable
        self._menuSizer.Add(self._bpmField, 0, wx.EXPAND|wx.ALL, 3) #@UndefinedVariable
        self._menuSizer.Add(self._inputButton, 0, wx.EXPAND|wx.ALL, 3) #@UndefinedVariable

        self._whiteNoteBitmap = wx.Bitmap("graphics/whiteNote.png") #@UndefinedVariable
        self._blackNoteBitmapLeft = wx.Bitmap("graphics/blackNoteLeft.png") #@UndefinedVariable
        self._blackNoteBitmapLeft__2 = wx.Bitmap("graphics/blackNoteLeft_-2.png") #@UndefinedVariable
        self._blackNoteBitmapLeft__1 = wx.Bitmap("graphics/blackNoteLeft_-1.png") #@UndefinedVariable
        self._blackNoteBitmapLeft_0 = wx.Bitmap("graphics/blackNoteLeft_0.png") #@UndefinedVariable
        self._blackNoteBitmapLeft_1 = wx.Bitmap("graphics/blackNoteLeft_1.png") #@UndefinedVariable
        self._blackNoteBitmapLeft_2 = wx.Bitmap("graphics/blackNoteLeft_2.png") #@UndefinedVariable
        self._blackNoteBitmapLeft_3 = wx.Bitmap("graphics/blackNoteLeft_3.png") #@UndefinedVariable
        self._blackNoteBitmapLeft_4 = wx.Bitmap("graphics/blackNoteLeft_4.png") #@UndefinedVariable
        self._blackNoteBitmapLeft_5 = wx.Bitmap("graphics/blackNoteLeft_5.png") #@UndefinedVariable
        self._blackNoteBitmapLeft_6 = wx.Bitmap("graphics/blackNoteLeft_6.png") #@UndefinedVariable
        self._blackNoteBitmapLeft_7 = wx.Bitmap("graphics/blackNoteLeft_7.png") #@UndefinedVariable
        self._blackNoteBitmapLeft_8 = wx.Bitmap("graphics/blackNoteLeft_8.png") #@UndefinedVariable
        self._blackNoteBitmapRight = wx.Bitmap("graphics/blackNoteRight.png") #@UndefinedVariable
        self._blackNoteBitmap = wx.Bitmap("graphics/blackNote.png") #@UndefinedVariable
        self._newNoteBitmap = wx.Bitmap("graphics/newNote.png") #@UndefinedVariable
        self._emptyBitMap = wx.EmptyBitmap (40, 30, depth=3) #@UndefinedVariable

        self._noteWidgets = []
        self._noteWidgetIds = []
        for note in range(128):
            octav = int(note / 12)
            octavNote = note % 12
            baseX = 1 + 308 * octav
            keyboardButton = self.createNoteWidget(octavNote, octav-2, baseX, (note==127))
            self._noteWidgets.append(keyboardButton)
            self._noteWidgetIds.append(keyboardButton.GetId())
            keyboardButton.Bind(wx.EVT_BUTTON, self._onKeyboardButton) #@UndefinedVariable
            keyboardButton.Bind(EVT_DRAG_START_EVENT, self._onDragStart)
            keyboardButton.Bind(EVT_DRAG_DONE_EVENT, self._onDragDone)
            dropTarget = FileDrop(keyboardButton.GetId(), self.fileDropped)
            keyboardButton.SetDropTarget(dropTarget)

        self._activeNoteId = 24
        self._configuration.setSelectedMidiChannel(0)
        self._configuration.setNoteNewThumbCallback(self.setNewImageOnNote)
        self._configuration.clearNoteNewThumbCallback(self.clearImageOnNote)
        self._noteGui.updateOverviewClipBitmap(self._emptyBitMap)
        self._noteGui.clearGui(self._activeNoteId)
        self._selectKeyboardKey(self._activeNoteId)

        self._trackThumbnailBitmap = wx.Bitmap("graphics/blackClip.png") #@UndefinedVariable
        self._trackEditBitmap = wx.Bitmap("graphics/editButton.png") #@UndefinedVariable
        self._trackEditPressedBitmap = wx.Bitmap("graphics/editButtonPressed.png") #@UndefinedVariable
        self._trackPlayBitmap = wx.Bitmap("graphics/playButton.png") #@UndefinedVariable
        self._trackPlayPressedBitmap = wx.Bitmap("graphics/playButtonPressed.png") #@UndefinedVariable
        self._trackEditBitmap = wx.Bitmap("graphics/editButtonSquare.png") #@UndefinedVariable
        self._trackEditPressedBitmap = wx.Bitmap("graphics/editButtonSquarePressed.png") #@UndefinedVariable
        self._trackStopBitmap = wx.Bitmap("graphics/stopButton.png") #@UndefinedVariable
        self._trackStopPressedBitmap = wx.Bitmap("graphics/stopButtonPressed.png") #@UndefinedVariable
        self._trackGuiSettings = []
        for track in range(16):
            self._trackGuiSettings.append(TrackOverviewSettings(self._midiTrackPanel, track, self, self._subWidgetList))
            settings = self._trackGuiSettings[track]
            self._trackGui.setupTrackOverviewGui(self._midiTrackPanel, self._noteGui, track, settings, self._trackGuiSettings, self._subWidgetList, self._fxWidgetsList)

        self._selectedMidiChannel = 0
        self._activeTrackId = -1
        self._selectTrack(self._selectedMidiChannel)

        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        logging.basicConfig()
        self._multiprocessLogger = MultiprocessLogger(self._log)
        self._midiTiming = MidiTiming()
        self._midiStateHolder = DummyMidiStateHolder()
        self._midiListner = None
        self.setupMidiListner()

        self._updateTimer = wx.Timer(self, -1) #@UndefinedVariable
        self._updateTimer.Start(1000 / 30)#30 times a second
        self.Bind(wx.EVT_TIMER, self._timedUpdate, id=self._updateTimer.GetId()) #@UndefinedVariable
        self.Bind(wx.EVT_LEFT_DOWN, self._onMouseClick) #@UndefinedVariable
        self.Bind(wx.EVT_CLOSE, self._onClose) #@UndefinedVariable

        self._dragTimer = wx.Timer(self, -1) #@UndefinedVariable

        self.SetSizer(self._mainSizer)

        for panels in self._subPanelsList:
            panels.Bind(wx.EVT_LEFT_UP, self._onMouseRelease) #@UndefinedVariable

        self.Show()

        self._taskQueue = []
        self._skippedTrackStateRequests = 99
        self._skippedPreviewRequests = 99
        self._skippedConfigStateRequests = 99
        self._skippedConfigListRequests = 99
        self._skippedLatestControllersRequests = 0
        self._skippedCheckConfigState = 0
        self._stoppingWebRequests = True
        self._sendingConfig = False
        self._lastConfigState = -1
        self._configUpdatedRequestIsOpen = False
        self._latestControllersRequestResult = None
        self._dragSource = None
        self.setupClientProcess()
        self._oldGuiConfigurationString = self._configuration.getXmlString()
        self._oldServerConfigurationString = self._oldGuiConfigurationString
        self._commandQueue = None
        self._statusQueue = None
        self._timedUpdate(None)

    def createNoteWidget(self, noteId, octav, baseX, lastNote=False):
        buttonPos = None
        bitmap = None
        if(noteId == 0):
            buttonPos = ( 0+baseX, 36)
            bitmap = self._whiteNoteBitmap
            cornerBitmap = self._blackNoteBitmapLeft_8
            if(octav == -2):
                cornerBitmap = self._blackNoteBitmapLeft__2
            if(octav == -1):
                cornerBitmap = self._blackNoteBitmapLeft__1
            if(octav == 0):
                cornerBitmap = self._blackNoteBitmapLeft_0
            if(octav == 1):
                cornerBitmap = self._blackNoteBitmapLeft_1
            if(octav == 2):
                cornerBitmap = self._blackNoteBitmapLeft_2
            if(octav == 3):
                cornerBitmap = self._blackNoteBitmapLeft_3
            if(octav == 4):
                cornerBitmap = self._blackNoteBitmapLeft_4
            if(octav == 5):
                cornerBitmap = self._blackNoteBitmapLeft_5
            if(octav == 6):
                cornerBitmap = self._blackNoteBitmapLeft_6
            if(octav == 7):
                cornerBitmap = self._blackNoteBitmapLeft_7
            widget = wx.StaticBitmap(self._keyboardPanel, pos=(buttonPos[0], 1), bitmap=cornerBitmap, id=wx.ID_ANY) #@UndefinedVariable
            self._subWidgetList.append(widget)
        elif(noteId == 1):
            buttonPos = (22+baseX,  1)
            bitmap = self._blackNoteBitmap
        elif(noteId == 2):
            buttonPos = (44+baseX, 36)
            bitmap = self._whiteNoteBitmap
        elif(noteId == 3):
            buttonPos = (66+baseX,  1)
            bitmap = self._blackNoteBitmap
        elif(noteId == 4):
            buttonPos = (88+baseX, 36)
            bitmap = self._whiteNoteBitmap
            widget = wx.StaticBitmap(self._keyboardPanel, pos=(buttonPos[0]+22, 1), bitmap=self._blackNoteBitmapRight, id=wx.ID_ANY) #@UndefinedVariable
            self._subWidgetList.append(widget)
        elif(noteId == 5):
            buttonPos = (132+baseX, 36)
            bitmap = self._whiteNoteBitmap
            widget = wx.StaticBitmap(self._keyboardPanel, pos=(buttonPos[0], 1), bitmap=self._blackNoteBitmapLeft, id=wx.ID_ANY) #@UndefinedVariable
            self._subWidgetList.append(widget)
        elif(noteId == 6):
            buttonPos = (154+baseX,  1)
            bitmap = self._blackNoteBitmap
        elif(noteId == 7):
            buttonPos = (176+baseX, 36)
            bitmap = self._whiteNoteBitmap
            if(lastNote == True):
                widget = wx.StaticBitmap(self._keyboardPanel, pos=(buttonPos[0]+22, 1), bitmap=self._blackNoteBitmapRight, id=wx.ID_ANY) #@UndefinedVariable
                self._subWidgetList.append(widget)
        elif(noteId == 8):
            buttonPos = (198+baseX,  1)
            bitmap = self._blackNoteBitmap
        elif(noteId == 9):
            buttonPos = (220+baseX, 36)
            bitmap = self._whiteNoteBitmap
        elif(noteId == 10):
            buttonPos = (242+baseX,  1)
            bitmap = self._blackNoteBitmap
        elif(noteId == 11):
            buttonPos = (264+baseX, 36)
            bitmap = self._whiteNoteBitmap
            widget = wx.StaticBitmap(self._keyboardPanel, pos=(buttonPos[0]+22, 1), bitmap=self._blackNoteBitmapRight, id=wx.ID_ANY) #@UndefinedVariable
            self._subWidgetList.append(widget)
        else:
            return None
        keyboardButton = PcnKeyboardButton(self._keyboardPanel, bitmap, buttonPos, wx.ID_ANY, size=(44, 35), isBlack=(buttonPos[1]==1)) #@UndefinedVariable
        return keyboardButton

    def setupProcessQueues(self, commandQueue, statusQueue):
        self._commandQueue = commandQueue
        self._statusQueue = statusQueue

    def setupClientProcess(self):
        self._guiClient = GuiClient()
        self._configuration.setEffectStateRequestCallback(self.requestEffectState)
        host, port = self._configuration.getWebConfig()
        self._guiClient.startGuiClientProcess(host, port, None)

    def setupMidiListner(self):        
        self._midiListner = TcpMidiListner(self._midiTiming, self._midiStateHolder, self._multiprocessLogger)
        bcast, host, port = self._configuration.getMidiListenConfig()
        self._midiListner.startDaemon(host, port, bcast)

    def updateKeyboardImages(self):
        activeNotesTask = TaskHolder("Active notes request", TaskHolder.RequestTypes.ActiveNotes, None)
        self._taskQueue.append(activeNotesTask)
        self._guiClient.requestActiveNoteList()
        activeNotesTask.setState(TaskHolder.States.Sendt)

    def _findQueuedTask(self, taskType, uniqueId = None, deleteDuplicates = True):
        foundTask = None
        for task in self._taskQueue:
            if(task.getType() == taskType):
                if((uniqueId == None) or (task.getUniqueId() == uniqueId)):
                    if(foundTask != None):
                        if(deleteDuplicates == True):
                            self._taskQueue.remove(task)
                    else:
                        foundTask = task
        return foundTask

    def _timedUpdate(self, event):
        self._checkForProcessCommands()
        self._checkServerResponse()
        self._checkForStaleTasks()
        self._requestConfigState()
        self._requestTrackState()
        self._requestPreview()
        self._requestConfigList()
        self._requestLatestControllers()
        self._midiListner.getData(False)
        self._updateTimingDisplay()
        self._checkConfigState()
        self._multiprocessLogger.handleQueuedLoggs()

    def _checkForProcessCommands(self):
        if(self._commandQueue != None):
            try:
                command = self._commandQueue.get_nowait()
                if(command == "QUIT"):
                    self._onClose(None)
            except:
                pass

    def _checkServerResponse(self):
        result = self._guiClient.getServerResponse()
        if(result[0] != None):
            if(result[0] == GuiClient.ResponseTypes.FileDownload):
#                print "GuiClient.ResponseTypes.FileDownload"
                if(result[1] != None):
                    fileName, playerFileName = result[1]
                    if(playerFileName == "thumbs/preview.jpg"):
#                        print "DEBUG Got preview!!!"
                        foundTask = self._findQueuedTask(TaskHolder.RequestTypes.Preview, None)
                        osFileName = os.path.normpath(fileName)
                        self._trackGui.updatePreviewImage(osFileName)
                        if(foundTask != None):
                            foundTask.taskDone()
                            self._taskQueue.remove(foundTask)
                    else:
                        foundTask = self._findQueuedTask(TaskHolder.RequestTypes.File, playerFileName, False)
                        if(foundTask == None):
                            print "Could not find task that belongs to this answer: " + playerFileName
                        else:
                            fileSetOk = False
                            osFileName = os.path.normpath(fileName)
                            if(os.path.isfile(osFileName)):
                                if(foundTask.getWidget().setBitmapFile(osFileName) == True):
                                    fileSetOk = True
                                    if((self._activeNoteId >= 0) and (self._activeNoteId < 128)):
                                        noteWidget = self._noteWidgets[self._activeNoteId]
                                        noteBitmap = noteWidget.getBitmap()
                                        self._noteGui.updateOverviewClipBitmap(noteBitmap)
                            if(fileSetOk == True):
                                self._taskQueue.remove(foundTask)
            if(result[0] == GuiClient.ResponseTypes.ThumbRequest):
#                print "GuiClient.ResponseTypes.ThumbRequest"
                if(result[1] != None):
                    noteTxt, noteTime, fileName = result[1] #@UnusedVariable
                    noteId = max(min(int(noteTxt), 127), 0)
                    foundTask = self._findQueuedTask(TaskHolder.RequestTypes.Note, noteId)
                    forceUpdate = foundTask.getExtraData()
                    if(foundTask == None):
                        print "Could not find task that belongs to this answer: " + noteTxt + ":" + noteTime + " -> " + fileName
                    else:
                        if(fileName.startswith("thumbs")):
                            namePart = fileName[6:]
                            guiFileName = "guiThumbs" + namePart
                            osFileName = os.path.normpath(guiFileName)
                            needFile = True
                            if(os.path.isfile(osFileName)):
                                if(self._noteWidgets[noteId].setBitmapFile(osFileName) == True):
                                    needFile = False
                                    if((self._activeNoteId >= 0) and (self._activeNoteId < 128) and(noteId == self._activeNoteId)):
                                        noteWidget = self._noteWidgets[self._activeNoteId]
                                        noteBitmap = noteWidget.getBitmap()
                                        self._noteGui.updateOverviewClipBitmap(noteBitmap)
                            if((needFile == True) or (forceUpdate == True)):
                                fileRequestTask = TaskHolder("File request for note %d" %(foundTask.getUniqueId()), TaskHolder.RequestTypes.File, foundTask.getWidget(), fileName)
                                self._taskQueue.append(fileRequestTask)
                                self._guiClient.requestImageFile(fileName)
                                fileRequestTask.setState(TaskHolder.States.Sendt)
                        foundTask.taskDone()
                        self._taskQueue.remove(foundTask)
            if(result[0] == GuiClient.ResponseTypes.NoteList):
#                print "GuiClient.ResponseTypes.NoteList"
                foundTask = self._findQueuedTask(TaskHolder.RequestTypes.ActiveNotes, None)
                if(result[1] != None):
                    noteList = result[1]
                    for i in range(128):
                        found = False
                        for listEntryTxt in noteList:
                            if(listEntryTxt == ""):
                                listEntryTxt = -1
                            if(int(listEntryTxt) == i):
#                                print "requesting i= " + str(i)
                                self._requestNote(i, 0.0)
                                found = True
                        if(found == False):
                            widget = self._noteWidgets[i]
                            widget.clearKeyboardButton()
                    if(foundTask != None):
                        foundTask.taskDone()
                        self._taskQueue.remove(foundTask)
            if(result[0] == GuiClient.ResponseTypes.TrackStateError):
                foundTask = self._findQueuedTask(TaskHolder.RequestTypes.Track, None)
                if((result[1] == "timeout") or (result[1] == "connectionRefused") or (result[1] == "resolvError")):
                    if(foundTask != None):
                        foundTask.taskDone()
                        self._taskQueue.remove(foundTask)
                        self._skippedTrackStateRequests = 99
            if(result[0] == GuiClient.ResponseTypes.TrackState):
#                print "GuiClient.ResponseTypes.TrackState"
                foundTask = self._findQueuedTask(TaskHolder.RequestTypes.Track, None)
                if(result[1] != None):
                    if(self._stoppingWebRequests == True):
                        self._updateTitle("Connecting to server...")
                    self._stoppingWebRequests = False
                    noteList = result[1]
                    for i in range(16):
                        note = int(noteList[i])
                        trackConfig = self._configuration.getTrackConfiguration(i)
                        settings = self._trackGuiSettings[i]
                        if((note < 0) or (note > 127)):
                            settings.clearThumb()
                            if((settings.getActiveNoteId() == -1)):
                                self._trackGui.updateTrackMixModeThumb(i, trackConfig, "None")
                                self._trackGui.updateTrackLvlModThumb(i, trackConfig)
                                self._trackGui.updateTrackEffectsThumb(i, trackConfig)
                            settings.setActiveNoteId(-1)
                        else:
                            noteWidget = self._noteWidgets[note]
                            noteBitmap = noteWidget.getBitmap()
                            if(noteBitmap != None):
                                settings.setThumb(noteBitmap)
                            else:
                                settings.clearThumb()
                            activeNoteConfig = self._configuration.getNoteConfiguration(note)
                            if(activeNoteConfig == None):
                                self._trackGui.updateTrackMixModeThumb(i, trackConfig, "None")
                                self._trackGui.updateTrackLvlModThumb(i, trackConfig)
                                self._trackGui.updateTrackEffectsThumb(i, trackConfig)
                            else:
                                self._trackGui.updateTrackMixModeThumb(i, trackConfig, activeNoteConfig.getMixMode())
                                self._trackGui.updateTrackLvlModThumb(i, trackConfig)
                                self._trackGui.updateTrackEffectsThumb(i, trackConfig)
                            settings.setActiveNoteId(note)
                    if(foundTask != None):
                        foundTask.taskDone()
                        self._taskQueue.remove(foundTask)
            if(result[0] == GuiClient.ResponseTypes.EffectState):
#                print "GuiClient.ResponseTypes.EffectState"
                foundTask = self._findQueuedTask(TaskHolder.RequestTypes.EffectState, None)
                if(result[1] != None):
                    valuesString = result[1][0]
                    guiString = result[1][1]
                    self._configuration.updateEffectsSliders(valuesString, guiString)
#                    print "DEBUG values: %s gui: %s" %(valuesString, guiString)
                if(foundTask != None):
                    foundTask.taskDone()
                    self._taskQueue.remove(foundTask)
            if(result[0] == GuiClient.ResponseTypes.ConfigState):
#                print "GuiClient.ResponseTypes.ConfigState"
                foundTask = self._findQueuedTask(TaskHolder.RequestTypes.ConfigState, None)
                if(result[1] != None):
                    configId = result[1]
                    if(configId != self._lastConfigState):
                        print "Config is updated on server.... ID: " + str(self._lastConfigState) + " != " + str(configId)
                        configRequestTask = TaskHolder("Configuration request", TaskHolder.RequestTypes.Configuration, None, None)
                        self._taskQueue.append(configRequestTask)
                        self._guiClient.requestConfiguration()
                        configRequestTask.setState(TaskHolder.States.Sendt)
                        playerConfigRequestTask = TaskHolder("Player configuration request", TaskHolder.RequestTypes.PlayerConfiguration, None, None)
                        self._taskQueue.append(playerConfigRequestTask)
                        self._guiClient.requestPlayerConfiguration()
                        playerConfigRequestTask.setState(TaskHolder.States.Sendt)
                    self._lastConfigState = configId
                    if(foundTask != None):
                        foundTask.taskDone()
                        self._taskQueue.remove(foundTask)
            if(result[0] == GuiClient.ResponseTypes.Configuration):
#                print "GuiClient.ResponseTypes.Configuration"
                foundTask = self._findQueuedTask(TaskHolder.RequestTypes.Configuration, None)
                if(result[1] != None):
                    newConfigXml = result[1]
                    newConfigString = xmlToPrettyString(newConfigXml)
                    if(self._oldServerConfigurationString != newConfigString):
                        currentGuiConfigString = self._configuration.getXmlString()
                        loadConfig = True
                        if(newConfigString == currentGuiConfigString):
                            loadConfig = False
                        if(currentGuiConfigString != self._oldGuiConfigurationString):
                            self._oldGuiConfigurationString = currentGuiConfigString
                            if(newConfigString != currentGuiConfigString):
                                if(self._configUpdatedRequestIsOpen == False):
                                    self._configUpdatedRequestIsOpen = True
                                    print "Both configs are updated! " * 5
                                    print "GUI " * 50
                                    print currentGuiConfigString
                                    print "SRVR " * 50
                                    print newConfigString
                                    print "XXX " * 50
                                    text = "Both the configuration on the sever and in the GUI has been updated. Would you like to discard local configuration and load server version?"
                                    dlg = wx.MessageDialog(self, text, 'Load server configuration?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                                    dialogResult = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                                    dlg.Destroy()
                                    if(dialogResult == False):
                                        loadConfig = False
                                        self._oldServerConfigurationString = newConfigString
                                    self._configUpdatedRequestIsOpen = False
                        if(loadConfig == True):
                            print "DEBUG pcn loadConfig == True"
                            self._configuration.setFromXml(newConfigXml)
                            self._oldGuiConfigurationString = self._configuration.getXmlString()
                            noteConfig = self._configuration.getNoteConfiguration(self._activeNoteId)
                            if(noteConfig == None):
                                self._noteGui.updateOverviewClipBitmap(self._emptyBitMap)
                                self._noteGui.clearGui(self._activeNoteId)
                            else:
                                noteWidget = self._noteWidgets[self._activeNoteId]
                                noteBitmap = noteWidget.getBitmap()
                                self._noteGui.updateOverviewClipBitmap(noteBitmap)
                                self._noteGui.updateGui(noteConfig, self._activeNoteId)
                            self._selectTrack(self._selectedMidiChannel)
                            self._configuration.updateEffectList(None)
                            self._configuration.updateFadeList(None)
                            self._configuration.updateEffectImageList()
#                            print "#" * 150
#                            self._configuration.printConfiguration()
#                            print "#" * 150
                        self.updateKeyboardImages()
                        self._oldServerConfigurationString = newConfigString
                    if(foundTask != None):
                        foundTask.taskDone()
                        try:
                            self._taskQueue.remove(foundTask)
                        except:
                            pass
                    foundTask = self._findQueuedTask(TaskHolder.RequestTypes.SendConfig, None)
                    if(foundTask != None):
                        foundTask.taskDone()
                        try:
                            self._taskQueue.remove(foundTask)
                        except:
                            pass
            if(result[0] == GuiClient.ResponseTypes.ConfigFileTransfer):
#                print "GuiClient.ResponseTypes.ConfigFileTransfer"
                foundTask = self._findQueuedTask(TaskHolder.RequestTypes.SendConfig, None)
                self._skippedConfigStateRequests = 99
                self._requestConfigState()
                if(foundTask != None):
                    foundTask.taskDone()
                    self._taskQueue.remove(foundTask)
            if(result[0] == GuiClient.ResponseTypes.PlayerConfiguration):
#                print "GuiClient.ResponseTypes.PlayerConfiguration"
                foundTask = self._findQueuedTask(TaskHolder.RequestTypes.PlayerConfiguration, None)
                if(result[1] != None):
                    newConfigXmlString = result[1]
                    self._playerConfigString = newConfigXmlString
                    if(foundTask != None):
                        foundTask.taskDone()
                        self._taskQueue.remove(foundTask)
            if(result[0] == GuiClient.ResponseTypes.LatestControllers):
#                print "GuiClient.ResponseTypes.LatestControllers"
                foundTask = self._findQueuedTask(TaskHolder.RequestTypes.LatestControllers, None)
                if(result[1] != None):
                    self._latestControllersRequestResult = result[1]
                    if(foundTask != None):
                        foundTask.taskDone()
                        self._taskQueue.remove(foundTask)
            if(result[0] == GuiClient.ResponseTypes.ConfigFileList):
#                print "GuiClient.ResponseTypes.ConfigFileList"
                foundTask = self._findQueuedTask(TaskHolder.RequestTypes.ConfigFileList, None)
                if(result[1] != None):
                    configurationFileListString, activeConfig, isConfigSaved = result[1]
                    self._serverConfigIsSaved = isConfigSaved
                    if((self._oldServerConfigList != configurationFileListString) or (self._oldServerActiveConfig != activeConfig)):
                        self._configurationFilesList = configurationFileListString.split(';', 128)
                        self._oldServerActiveConfig = activeConfig
                        if(activeConfig == ""):
                            self._updateTitle("No configuration loaded.")
                        else:
                            self._updateTitle(activeConfig)
                    else:
                        self._updateTitle(activeConfig)
                    self._oldServerConfigList = configurationFileListString
                    if(foundTask != None):
                        foundTask.taskDone()
                        self._taskQueue.remove(foundTask)

    def _updateTitle(self, activeConfig):
        if(activeConfig == ""):
            self.SetTitle(self._baseTitle + "   *** No contact with player! ***")
        elif(activeConfig == "Connecting to server..."):
            self.SetTitle(self._baseTitle + "   * Connecting to server... *")
        else:
            if(self._serverConfigIsSaved):
                self.SetTitle(self._baseTitle + "   [" + activeConfig + "]")
            else:
                self.SetTitle(self._baseTitle + "   [" + activeConfig + "] *Not saved!*")
        self._activeConfig = activeConfig

    def _checkForStaleTasks(self):
        checkTime = time.time()
        for task in self._taskQueue:
            if(task.isStale(checkTime)):
                if(self._stoppingWebRequests == True):
                    if(task.getType() != TaskHolder.RequestTypes.Track):
                        task.taskDone()
                        self._taskQueue.remove(task)
                        return
                if(task.getType() == TaskHolder.RequestTypes.ActiveNotes):
                    self._guiClient.requestActiveNoteList()
                    task.setState(TaskHolder.States.Sendt)
                elif(task.getType() == TaskHolder.RequestTypes.Track):
                    self._guiClient.requestTrackState()
                    task.setState(TaskHolder.States.Sendt)
                    self._stoppingWebRequests = True
                    self._updateTitle("")
                elif(task.getType() == TaskHolder.RequestTypes.Preview):
                    self._guiClient.requestPreview()
                    task.setState(TaskHolder.States.Sendt)
                elif(task.getType() == TaskHolder.RequestTypes.ConfigState):
                    self._guiClient.requestConfigState(self._lastConfigState)
                    task.setState(TaskHolder.States.Sendt)
                elif(task.getType() == TaskHolder.RequestTypes.Note):
                    self._guiClient.requestImage(task.getUniqueId(), 0.0)
                    task.setState(TaskHolder.States.Sendt)
                elif(task.getType() == TaskHolder.RequestTypes.LatestControllers):
                    self._guiClient.requestLatestControllers()
                    task.setState(TaskHolder.States.Sendt)
                elif(task.getType() == TaskHolder.RequestTypes.ConfigFileList):
                    self._guiClient.requestConfigList()
                    task.setState(TaskHolder.States.Sendt)
                elif(task.getType() == TaskHolder.RequestTypes.SendConfig):
                    xmlString = task.getExtraData()
                    self._guiClient.sendConfiguration(xmlString)
                    task.setState(TaskHolder.States.Sendt)
                elif(task.getType() == TaskHolder.RequestTypes.Configuration):
                    if(self._configUpdatedRequestIsOpen == False):
                        self._guiClient.requestConfiguration()
                        task.setState(TaskHolder.States.Sendt)
                    else:
                        print "Waiting for user response..."
                else:
                    self._taskQueue.remove(task)

    def _requestTrackState(self):
        if(self._skippedTrackStateRequests > 5):
            self._skippedTrackStateRequests = 0
            foundTask = self._findQueuedTask(TaskHolder.RequestTypes.Track, None)
            if(foundTask == None):
                trackRequestTask = TaskHolder("Track state request", TaskHolder.RequestTypes.Track, None, None)
                self._taskQueue.append(trackRequestTask)
                self._guiClient.requestTrackState()
                trackRequestTask.setState(TaskHolder.States.Sendt)
        else:
            self._skippedTrackStateRequests += 1

    def _requestNote(self, noteId, noteTime, forceUpdate = False):
        imageRequestTask = TaskHolder("Note request for note %d:%.2f" %(noteId, noteTime), TaskHolder.RequestTypes.Note, self._noteWidgets[noteId], noteId)
        imageRequestTask.setExtraData(forceUpdate)
        self._taskQueue.append(imageRequestTask)
        self._guiClient.requestImage(noteId, noteTime, forceUpdate)
        imageRequestTask.setState(TaskHolder.States.Sendt)

    def requestEffectState(self, channel, note):
        foundTask = self._findQueuedTask(TaskHolder.RequestTypes.EffectState, None)
        if(foundTask == None):
            effectStateRequestTask = TaskHolder("Effect state request for " + str(note) + " or " + str(channel), TaskHolder.RequestTypes.EffectState, None, None)
            self._taskQueue.append(effectStateRequestTask)
            self._guiClient.requestEffectState(channel, note)
            effectStateRequestTask.setState(TaskHolder.States.Sendt)

    def _requestPreview(self):
        if(self._skippedPreviewRequests > 5):
            if(self._stoppingWebRequests == False):
                self._skippedPreviewRequests = 0
                foundTask = self._findQueuedTask(TaskHolder.RequestTypes.Preview, None)
                if(foundTask == None):
                    previewRequestTask = TaskHolder("Track state request", TaskHolder.RequestTypes.Preview, None, None)
                    self._taskQueue.append(previewRequestTask)
                    self._guiClient.requestPreview()
                    previewRequestTask.setState(TaskHolder.States.Sendt)
        else:
            self._skippedPreviewRequests += 1

    def _requestConfigState(self):
        if(self._skippedConfigStateRequests > 30):
            if(self._stoppingWebRequests == False):
                self._skippedConfigStateRequests = 0
                foundTask = self._findQueuedTask(TaskHolder.RequestTypes.ConfigState, None)
                if(foundTask == None):
                    configStateRequestTask = TaskHolder("Config state request", TaskHolder.RequestTypes.ConfigState, None, None)
                    self._taskQueue.append(configStateRequestTask)
                    self._guiClient.requestConfigState(self._lastConfigState)
                    configStateRequestTask.setState(TaskHolder.States.Sendt)
        else:
            self._skippedConfigStateRequests += 1

    def _requestConfigList(self):
        if(self._skippedConfigListRequests > 60):
            if(self._stoppingWebRequests == False):
                self._skippedConfigListRequests = 0
                foundTask = self._findQueuedTask(TaskHolder.RequestTypes.ConfigFileList, None)
                if(foundTask == None):
                    configStateRequestTask = TaskHolder("Config list request", TaskHolder.RequestTypes.ConfigFileList, None, None)
                    self._taskQueue.append(configStateRequestTask)
                    self._guiClient.requestConfigList()
                    configStateRequestTask.setState(TaskHolder.States.Sendt)
        else:
            self._skippedConfigListRequests += 1

    def _requestLatestControllers(self):
        if(self._skippedLatestControllersRequests > 20):
            if(self._stoppingWebRequests == False):
                self._skippedLatestControllersRequests = 0
                foundTask = self._findQueuedTask(TaskHolder.RequestTypes.LatestControllers, None)
                if(foundTask == None):
                    controllersRequestTask = TaskHolder("Latest MIDI controllers request", TaskHolder.RequestTypes.LatestControllers, None, None)
                    self._taskQueue.append(controllersRequestTask)
                    self._guiClient.requestLatestControllers()
                    controllersRequestTask.setState(TaskHolder.States.Sendt)
        else:
            self._skippedLatestControllersRequests += 1

    def _updateTimingDisplay(self):
        timeStamp = self._midiTiming.getTime()
        midiSync, bar, beat, subbeat, subBeatFraction = self._midiTiming.getMidiPosition(timeStamp) #@UnusedVariable
        if(midiSync != True):
            bar = ((bar - 1) % 8) + 1
            self._timingField.SetBackgroundColour((220, 220, 220))
        else:
            self._timingField.SetBackgroundColour((220, 255, 220))
        positionText = "%5d:%d.%02d" %(bar, beat, subbeat)
        self._timingField.SetValue(positionText)
        bpm = int(self._midiTiming.getBpm() + 0.5)
        self._bpmField.SetValue(str(bpm))

        currentTime = time.time()
        midiSateTime = self._midiStateHolder.getLastMidiEventTime()
        lastEventAge = currentTime - midiSateTime
        if(lastEventAge < 1):
            self._inputButton.setBitmaps(self._inputGreenBitmap, self._inputGreenBitmap)
        else:
            self._inputButton.setBitmaps(self._inputGrayBitmap, self._inputGrayBitmap)

#TODO: Better refresh...
#        self._scrollingEditAreaPanel.Layout()
#        self._noteGui.refreshLayout()
#        self._scrollingKeyboardPannel.Layout()
#        self._scrollingMidiTrackPanel.Layout()
#        self._scrollingEditAreaPanel.SendSizeEvent()
#        self._scrollingKeyboardPannel.SendSizeEvent()
#        self._scrollingMidiTrackPanel.SendSizeEvent()


    def _checkConfigState(self):
        if(self._skippedCheckConfigState > 3):
            self._skippedCheckConfigState = 0
            self._updateMidiButtonColor(self._configuration.isMidiEnabled())
            currentGuiConfigString = self._configuration.getXmlString()
            if(self._oldGuiConfigurationString != currentGuiConfigString):
                self._configuration.setupSpecialModulations()
                if(self._stoppingWebRequests == True):
                    self._sendButton.setBitmaps(self._sendConfigNoContactRedBitmap, self._sendConfigNoContactRedBitmap)
                else:
                    foundTask = self._findQueuedTask(TaskHolder.RequestTypes.SendConfig, None)
                    if(foundTask == None):
                        if(self._configuration.isAutoSendEnabled() == True):
                            self._sendButton.setBitmaps(self._sendConfigSendingBitmap, self._sendConfigSendingBitmap)
                            self._onSendButton(None)
                        else:
                            self._sendButton.setBitmaps(self._sendConfigBitmap, self._sendConfigPressedBitmap)
                    else:
                        self._sendButton.setBitmaps(self._sendConfigSendingBitmap, self._sendConfigSendingBitmap)
            else:
                self._sendingConfig = False
                if(self._stoppingWebRequests == True):
                    self._sendButton.setBitmaps(self._sendConfigNoContactBitmap, self._sendConfigNoContactBitmap)
                else:
                    self._sendButton.setBitmaps(self._sendConfigNoNewConfigBitmap, self._sendConfigNoNewConfigBitmap)
        else:
            self._skippedCheckConfigState += 1

    def getLatestControllers(self):
        return self._latestControllersRequestResult

    def _onFileButton(self, event):
        self._menuPanel.PopupMenu(self._fileButtonPopup, (3,19))

    def _onFileMenuItemChosen(self, index):
        if(index < 0):
            return
        if(index > len(self._fileLabels)):
            return
        menuString = self._fileLabels[index]
        if(menuString == "Open"):
            dlg = ConfigOpenDialog(self, 'Load config.', self._guiClient.requestConfigChange, self._configurationFilesList, self._activeConfig)
            dlg.ShowModal()
            try:
                dlg.Destroy()
            except wx._core.PyDeadObjectError: #@UndefinedVariable
                pass
        elif(menuString == "New"):
            dlg = ConfigNewDialog(self, 'New config.', self._updateConfigName, self._activeConfig)
            dlg.ShowModal()
            try:
                dlg.Destroy()
            except wx._core.PyDeadObjectError: #@UndefinedVariable
                pass
            self._updateTitle(self._activeConfig)
            self._guiClient.requestConfigNew(self._activeConfig)
        elif(menuString == "Save"):
            if(self._stoppingWebRequests == True):
                print "Warning! Cannot save program when we have connection troubles!"
                wx.MessageBox('Cannot save program when we have connection troubles!', 'Warning', wx.OK | wx.ICON_INFORMATION) #@UndefinedVariable
            else:
                selectedConfig = self._activeConfig
                print "SAVE: " + str(selectedConfig)
                self._guiClient.requestConfigSave(selectedConfig)
        elif(menuString == "Player Config"):
            if(self._playerConfigString != None):
                dlg = ConfigPlayerDialog(self, 'Player config.', self._updatePlayerConfiguration, self._playerConfigString)
                dlg.ShowModal()
                try:
                    dlg.Destroy()
                except wx._core.PyDeadObjectError: #@UndefinedVariable
                    pass
            else:
                print "Warning! Cannot edit Player config without network contact!"
                wx.MessageBox('Cannot edit Player config without network contact!', 'Warning', wx.OK | wx.ICON_INFORMATION) #@UndefinedVariable
        elif(menuString == "GUI Config"):
            dlg = ConfigGuiDialog(self, 'GUI config.', self._configuration)
            dlg.ShowModal()
            try:
                dlg.Destroy()
            except wx._core.PyDeadObjectError: #@UndefinedVariable
                pass
        elif(menuString == "Exit"):
            self._onClose(None)

    def _updateConfigName(self, newConfigName):
        self._serverConfigIsSaved = False
        self._activeConfig = newConfigName

    def _updatePlayerConfiguration(self, xmlString):
        self._playerConfigString = xmlString
        self._guiClient.sendPlayerConfiguration(xmlString)

    def _onSendButton(self, event):
        if(self._configUpdatedRequestIsOpen == False):
            print "DEBUG pcn: _onSendButton()"
            xmlString = self._configuration.getXmlString()
            foundTask = self._findQueuedTask(TaskHolder.RequestTypes.SendConfig, None)
            if(foundTask != None):
                foundTask.taskDone()
                try:
                    self._taskQueue.remove(foundTask)
                except:
                    pass
            trackRequestTask = TaskHolder("Track state request", TaskHolder.RequestTypes.SendConfig, None, None)
            trackRequestTask.setExtraData(xmlString)
            self._oldGuiConfigurationString = xmlString
            self._taskQueue.append(trackRequestTask)
            self._guiClient.sendConfiguration(xmlString)
            trackRequestTask.setState(TaskHolder.States.Sendt)
            self._sendButton.setBitmaps(self._sendConfigSendingBitmap, self._sendConfigSendingBitmap)
            self._sendingConfig = True

    def _updateMidiButtonColor(self, midiOn):
        if(self._stoppingWebRequests):
            self._midiButton.setBitmaps(self._midiNoContactBitmap, self._midiNoContactBitmap)
        else:
            if(midiOn == True):
                self._midiButton.setBitmaps(self._midiOnBitmap, self._midiOnPressedBitmap)
            else:
                self._midiButton.setBitmaps(self._midiOffBitmap, self._midiOffPressedBitmap)

    def _midiToggle(self, event):
        midiOn = self._configuration.isMidiEnabled()
        if(midiOn == True):
            midiOn = False
            self._configuration.setMidiEnable(midiOn)
            self._selectedMidiChannel = -1
            for i in range(16):
                settings = self._trackGuiSettings[i]
                settings.unsetSelected()
        else:
            midiOn = True
            self._configuration.setMidiEnable(midiOn)
        self._updateMidiButtonColor(midiOn)

    def _selectKeyboardKey(self, keyId):
        if((keyId >= 0) and (keyId < 128)):
            self._noteWidgets[keyId].setSelected()
        for i in range(128):
            widget = self._noteWidgets[i]
            if(i != keyId):
                widget.unsetSelected()

    def _selectTrack(self, trackId):
        if((trackId >= 0) and (trackId < 16)):
            self._trackGuiSettings[trackId].setSelected(self._configuration.isMidiEnabled())
        for i in range(16):
            settings = self._trackGuiSettings[i]
            if(i != trackId):
                settings.unsetSelected()

    def _onKeyboardButton(self, event):
        buttonId = event.GetEventObject().GetId()
        foundNoteId = None
        for i in range(128):
            if(self._noteWidgetIds[i] == buttonId):
                foundNoteId = i
                break

        if(foundNoteId != None):
            self._activeNoteId = foundNoteId
            self._selectKeyboardKey(self._activeNoteId)
            if(self._selectedMidiChannel > -1):
                self._configuration.getMidiSender().sendNoteOnOff(self._selectedMidiChannel, self._activeNoteId)
            noteConfig = self._configuration.getNoteConfiguration(self._activeNoteId)
            if(noteConfig == None):
                self._noteGui.updateOverviewClipBitmap(self._emptyBitMap)
                self._noteGui.clearGui(self._activeNoteId)
            else:
                noteWidget = self._noteWidgets[self._activeNoteId]
                noteBitmap = noteWidget.getBitmap()
                self._noteGui.updateOverviewClipBitmap(noteBitmap)
                self._noteGui.updateGui(noteConfig, self._activeNoteId)
        self._dragSource = None
        self.clearDragCursor()

    def clearDragCursor(self):
        if(self._dragTimer.IsRunning() == True):
            self._dragTimer.Stop()
        cursor = wx.StockCursor(wx.CURSOR_ARROW) #@UndefinedVariable
        self._noteGui.clearDragCursor(cursor)
        self._updateCursor(cursor, "None")

    def setDragCursor(self, dragType, bitmap=None):
        noteMode = False
        fxMode = False
        if(dragType == "Note"):
            noteMode = True
        elif(dragType == "FX"):
            fxMode = True
        dragBitmap = None
        if(noteMode == True):
            for i in range(128):
                if(self._noteWidgetIds[i] == self._dragSource):
                    sourceConfig = self._configuration.getNoteConfiguration(i)
                    if(sourceConfig != None):
                        dragBitmap = self._noteWidgets[i].getBitmap()
                    break
            if(dragBitmap == None):
                self._dragSource = None
                self.clearDragCursor()
                return
            cursorImage = wx.ImageFromBitmap(dragBitmap) #@UndefinedVariable
            cursor = wx.CursorFromImage(cursorImage) #@UndefinedVariable
        elif(fxMode == True):
            if(bitmap == None):
                self._dragSource = None
                self.clearDragCursor()
                return
            cursorImage = wx.ImageFromBitmap(bitmap) #@UndefinedVariable
            cursor = wx.CursorFromImage(cursorImage) #@UndefinedVariable
        else:
            self._dragSource = None
            self.clearDragCursor()
            return
        self._noteGui.setDragCursor(cursor)
        self._updateCursor(cursor, dragType)

    def _updateCursor(self, cursor, dragType):
        for i in range(128):
            widget = self._noteWidgets[i]
            widget.SetCursor(cursor)
        for panels in self._subPanelsList:
            panels.SetCursor(cursor)
        for panels in self._subWidgetList:
            panels.SetCursor(cursor)
        for i in range(len(self._fxWidgetsList)):
            widget = self._fxWidgetsList[i]
            widget.SetCursor(cursor)

    def _onMouseRelease(self, event):
        self.clearDragCursor()
        self._dragSource = None

    def _onDragStart(self, event):
        self._dragSource = event.GetEventObject().GetId()
        self._dragTimer.Start(100, oneShot=True)#1/2 sec
        self.Bind(wx.EVT_TIMER, self._onDragTimeout, id=self._dragTimer.GetId()) #@UndefinedVariable

    def _onDragTimeout(self, event):
        self.setDragCursor("Note")

    def _onDragDone(self, event):
        self.clearDragCursor()
        if(self._dragSource != None):
            sourceNoteId = None
            for i in range(128):
                if(self._noteWidgetIds[i] == self._dragSource):
                    sourceNoteId = i
                    break
            if(sourceNoteId != None):
                buttonId =  event.GetEventObject().GetId()
                destNoteId = None
                for i in range(128):
                    if(self._noteWidgetIds[i] == buttonId):
                        destNoteId = i
                        break
                if(destNoteId != None):
                    if(destNoteId != sourceNoteId):
                        print "Drag and drop from noteId %d to %d" % (sourceNoteId, destNoteId)
                        sourceConfig = self._configuration.getNoteConfiguration(sourceNoteId)
                        if(sourceConfig != None):
                            destinationConfig = self._configuration.getNoteConfiguration(destNoteId)
                            if(destinationConfig == None):
                                destinationConfig = self._configuration.makeNoteConfig("", noteToNoteString(destNoteId), destNoteId)
                            if(destinationConfig != None):
                                destinationConfig.updateFrom(sourceConfig, True)
                                self._noteGui.updateGui(destinationConfig, destNoteId)
                                noteBitmap = self._noteWidgets[sourceNoteId].getBitmap()
                                self._noteWidgets[destNoteId].setBitmap(noteBitmap)
                                self._activeNoteId = destNoteId
                                self._selectKeyboardKey(self._activeNoteId)
                                self._noteGui.updateOverviewClipBitmap(noteBitmap)
        self.clearDragCursor()
        self._dragSource = None

    def _onMouseClick(self, event):
        self._dragSource = None
        self.clearDragCursor()

    def _call_command(self, command, option, fileName):
        outputString = ""
        try:
            process = subprocess.Popen((command, option, fileName), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except:
            text = "Unable to execute ffmpeg command: \"" + command + "\"\n"
            text += " from directory: \"" + os.getcwd() + "\"\n"
            text += "\nPlease check your path or update GUI config under file menu.\n"
            dlg = wx.MessageDialog(self, text, 'ffmpeg error!', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
            dlg.ShowModal()
            dlg.Destroy()
        else:
            while True:
                out = process.stdout.read(1)
                if out == '' and process.poll() != None:
                    break
                if out != '':
                    outputString += out
            outputString += process.communicate()[0]
            return outputString
        return None

    def setNewImageOnNote(self, noteId):
        if((noteId >= 0) and (noteId < 128)):
            self._noteWidgets[noteId].setBitmap(self._newNoteBitmap)
            self._noteGui.updateOverviewClipBitmap(self._newNoteBitmap)

    def clearImageOnNote(self, noteId):
        if((noteId >= 0) and (noteId < 128)):
            self._noteWidgets[noteId].clearKeyboardButton()
            self._noteGui.updateOverviewClipBitmap(self._emptyBitMap)

    def fileDropped(self, widgetId, fileName, fileNameIndex):
        destNoteId = None
        for i in range(128):
            if(self._noteWidgetIds[i] == widgetId):
                destNoteId = i
                break
        destNoteId += fileNameIndex
        ffmpegPath = os.path.normpath(self._configuration.getFfmpegBinary())
        if(destNoteId != None):
            if(destNoteId >= 128):
                return
            ffmpegString = self._call_command(ffmpegPath, "-i", fileName)
            if(ffmpegString == None):
                return
            inputCount = 0
            streamcount = 0
            inputIsVideo = True
            inputIsAvi = False
            inputOk = False
            tryConvert = False
            for ffmpegLine in ffmpegString.split('\n'):
                if(ffmpegLine.startswith("Input") == True):
                    print "Input: " + ffmpegLine
                    if(", image2," in ffmpegLine):
                        print "image!!!"
                        inputIsVideo = False
                    if(", avi," in ffmpegLine):
                        print "video!!!"
                        inputIsAvi = True
                    inputCount += 1
                if(inputCount == 1):
                    if(ffmpegLine.startswith("Input") == False):
                        if("Stream " in ffmpegLine):
                            streamcount += 1
                            if(inputIsVideo == True):
                                if("MJPG" in ffmpegLine):
                                    if("0x47504A4D" in ffmpegLine):
                                        print "MJPG " * 20
                                        if(inputIsAvi == True):
                                            inputOk = True
                                elif(" mjpeg," in ffmpegLine):
                                    if(" yuvj420p," in ffmpegLine):
                                        print "MJPG " * 20
                                        if(inputIsAvi == True):
                                            inputOk = True
                                else:
                                    tryConvert = True
                            else:
                                if(" mjpeg," in ffmpegLine):
                                    print "Jpeg " * 10
                                    inputOk = True
                                elif(" gif," in ffmpegLine):
                                    print "GIF " * 10
                                    inputOk = True
                                elif(" png," in ffmpegLine):
                                    print "PNG " * 10
                                    inputOk = True
                                else:
                                    print ffmpegLine
            if(inputCount > 0):
                convertBeforeImport = True
                if((inputCount == 1) and (streamcount == 1) and (inputOk == True)):
                    convertBeforeImport = False
                if(convertBeforeImport == True):
                    if(tryConvert == True):
                        self._convertionWentOk = False
                        dlg = VideoConverterDialog(self, 'Convert file...', self._updateValuesFromConvertDialogCallback,
                                                   ffmpegPath, self._videoSaveSubDir, self._videoDirectory, fileName, 
                                                   self._videoCropMode, self._videoScaleMode, self._videoScaleX, self._videoScaleY)
                        dlg.ShowModal()
                        try:
                            dlg.Destroy()
                        except wx._core.PyDeadObjectError: #@UndefinedVariable
                            pass
                        if(self._convertionWentOk == True):
                            fileName = self._convertionOutputFileName
                            inputOk = True
                if(inputOk == True):
                    needsCopy = False
                    try:
                        relativeFileName = os.path.relpath(fileName, self._videoDirectory)
                    except:
                        needsCopy = True
                    else:
                        if(relativeFileName.startswith("..") == True):
                            needsCopy = True
                    if(needsCopy == True):
                        self._copyWentOk = False
                        dlg = VideoCopyDialog(self, 'Copy file...', self._updateValuesFromCopyDialogCallback,
                                                   self._videoSaveSubDir, self._videoDirectory, fileName)
                        dlg.ShowModal()
                        try:
                            dlg.Destroy()
                        except:
                            pass
                        if(self._copyWentOk == True):
                            relativeFileName = self._copyOutputFileName
                        else:
                            print "Error copying file!!!"
                            return
                    relativeFileName = forceUnixPath(relativeFileName)
                    print "Setting %d (%s) to fileName: %s" % (destNoteId, noteToNoteString(destNoteId), relativeFileName)
                    destinationConfig = self._configuration.getNoteConfiguration(destNoteId)
                    if(destinationConfig == None):
                        destinationConfig = self._configuration.makeNoteConfig(relativeFileName, noteToNoteString(destNoteId), destNoteId)
                    if(destinationConfig != None):
                        destinationConfig.updateFileName(relativeFileName, inputIsVideo)
                        if(fileNameIndex == 0):
                            self._noteWidgets[destNoteId].setBitmap(self._newNoteBitmap)
                            self._noteGui.updateGui(destinationConfig, destNoteId)
                            self._activeNoteId = destNoteId
                            self._selectKeyboardKey(self._activeNoteId)
                            self._noteGui.updateOverviewClipBitmap(self._newNoteBitmap)
                    return
            text = "Unknown file type: \"" + fileName + "\"\n"
            text += "\n"
            text += "We support jpg, png and gif images,\n"
            text += "and video files detected by ffmpeg.\n"
            text += "\n"
            text += "You can manually convert using ffmpeg with\n"
            text += "output options: \"-vcodec mjpeg -qscale 1 -an\"\n"
            dlg = wx.MessageDialog(self, text, 'File error!', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
            dlg.ShowModal()
            dlg.Destroy()

    def _updateValuesFromConvertDialogCallback(self, videoSaveSubDir, videoCropMode, videoScaleMode, scaleX, scaleY, convertionWentOk, convertionOutputFileName):
        self._videoSaveSubDir = videoSaveSubDir
        self._videoCropMode = videoCropMode
        self._videoScaleMode = videoScaleMode
        self._videoScaleX = scaleX
        self._videoScaleY = scaleY
        self._convertionWentOk = convertionWentOk
        self._convertionOutputFileName = convertionOutputFileName

    def _updateValuesFromCopyDialogCallback(self, fileOk, copyOutputFileName = None, videoSaveSubDir = None):
        self._copyWentOk = fileOk
        if(copyOutputFileName != None):
            self._copyOutputFileName = copyOutputFileName
        if(videoSaveSubDir != None):
            self._videoSaveSubDir = videoSaveSubDir

    def getNoteConfig(self, trackId):
        settings = self._trackGuiSettings[trackId]
        activeNoteId = settings.getActiveNoteId()
        activeNoteMixMode = "Default"
        if((activeNoteId >= 0) and (activeNoteId < 128)):
            activeNoteConfig = self._configuration.getNoteConfiguration(activeNoteId)
            if(activeNoteConfig != None):
                activeNoteMixMode = activeNoteConfig.getMixMode()
        else:
            activeNoteMixMode = "None"
        return (activeNoteId, activeNoteMixMode)

    def setActiveTrackId(self, trackId):
        self._activeTrackId = trackId
        self._selectTrack(trackId)

    def _onTrackEditButton(self, event):
        buttonId = event.GetEventObject().GetId()
        foundTrackId = None
        for i in range(16):
            if(self._trackGuiSettings[i].hasEditWidgetId(buttonId)):
                foundTrackId = i
                break
        if(foundTrackId != None):
            if((self._activeTrackId == foundTrackId) and self._noteGui.isTrackEditorOpen()):
                self._activeTrackId = -1
                self._noteGui.hideTrackGui()
            else:
                self._activeTrackId = foundTrackId
                destinationConfig = self._configuration.getTrackConfiguration(self._activeTrackId)
                if(destinationConfig != None):
                    activeNoteId, activeNoteMixMode = self.getNoteConfig(self._activeTrackId)
                    self._trackGui.updateGui(destinationConfig, foundTrackId, activeNoteId, activeNoteMixMode)
                    self._noteGui.showTrackGui()
        else:
            self._activeTrackId = -1
            self._noteGui.hideTrackGui()

    def _onTrackButton(self, event):
        buttonId = event.GetEventObject().GetId()
        foundTrackId = None
        for i in range(16):
            if(self._trackGuiSettings[i].hasTrackWidgetId(buttonId)):
                foundTrackId = i
                break
        if(foundTrackId != None):
            self._activeTrackId = foundTrackId
            self._selectTrack(foundTrackId)
            if(self._configuration.isMidiEnabled()):
                self._selectedMidiChannel = foundTrackId
            else:
                self._selectedMidiChannel = -1
            self._configuration.setSelectedMidiChannel(self._selectedMidiChannel)
            destinationConfig = self._configuration.getTrackConfiguration(foundTrackId)
            if(destinationConfig != None):
                settings = self._trackGuiSettings[foundTrackId]
                activeNoteId = settings.getActiveNoteId()
                noteMixMode = "Default"
                if((activeNoteId >= 0) and (activeNoteId < 128)):
                    activeNoteConfig = self._configuration.getNoteConfiguration(activeNoteId)
                    if(activeNoteConfig != None):
                        noteMixMode = activeNoteConfig.getMixMode()
                else:
                    noteMixMode = "None"
                self._trackGui.updateGui(destinationConfig, foundTrackId, activeNoteId, noteMixMode)

    def _onTrackButtonDouble(self, event):
        buttonId = event.GetEventObject().GetId()
        foundTrackId = None
        for i in range(16):
            if(self._trackGuiSettings[i].hasTrackWidgetId(buttonId)):
                foundTrackId = i
                break
        if(foundTrackId != None):
            destinationConfig = self._configuration.getTrackConfiguration(foundTrackId)
            if(destinationConfig != None):
                settings = self._trackGuiSettings[foundTrackId]
                activeNoteId = settings.getActiveNoteId()
                if((activeNoteId >= 0) and (activeNoteId < 128)):
                    self._activeNoteId = activeNoteId
                    self._selectKeyboardKey(self._activeNoteId)
                    noteConfig = self._configuration.getNoteConfiguration(self._activeNoteId)
                    if(noteConfig == None):
                        self._noteGui.updateOverviewClipBitmap(self._emptyBitMap)
                        self._noteGui.clearGui(self._activeNoteId)
                    else:
                        noteWidget = self._noteWidgets[self._activeNoteId]
                        noteBitmap = noteWidget.getBitmap()
                        self._noteGui.updateOverviewClipBitmap(noteBitmap)
                        self._noteGui.updateGui(noteConfig, self._activeNoteId)
                    self._noteGui.showNoteGui()
            self._dragSource = None
            self.clearDragCursor()

    def _onTrackPlayButton(self, event):
        buttonId = event.GetEventObject().GetId()
        foundTrackId = None
        for i in range(16):
            if(self._trackGuiSettings[i].hasPlayWidgetId(buttonId)):
                foundTrackId = i
                break
        if(foundTrackId != None):
            self._activeTrackId = foundTrackId
            if(self._selectedMidiChannel == foundTrackId):
                self._selectedMidiChannel = -1
                self._selectTrack(-1)
            else:
                if(self._configuration.isMidiEnabled()):
                    self._selectedMidiChannel = foundTrackId
            self._selectTrack(foundTrackId)
            destinationConfig = self._configuration.getTrackConfiguration(foundTrackId)
            if(destinationConfig != None):
                settings = self._trackGuiSettings[foundTrackId]
                activeNoteId = settings.getActiveNoteId()
                noteMixMode = "Default"
                if((activeNoteId >= 0) and (activeNoteId < 128)):
                    activeNoteConfig = self._configuration.getNoteConfiguration(activeNoteId)
                    if(activeNoteConfig != None):
                        noteMixMode = activeNoteConfig.getMixMode()
                else:
                    noteMixMode = "None"
                self._trackGui.updateGui(destinationConfig, self._activeTrackId, activeNoteId, noteMixMode)
            self._configuration.setSelectedMidiChannel(self._selectedMidiChannel)

    def _onTrackStopButton(self, event):
        buttonId = event.GetEventObject().GetId()
        foundTrackId = None
        for i in range(16):
            if(self._trackGuiSettings[i].hasStopWidgetId(buttonId)):
                foundTrackId = i
                break
        if(foundTrackId != None):
            self._configuration.getMidiSender().sendGuiClearChannelNotes(foundTrackId)

    def _onClose(self, event):
        self._guiClient.requestGuiClientProcessToStop()
        self._midiListner.requestTcpMidiListnerProcessToStop()
        if(self._statusQueue != None):
            self._log.debug("Telling player process that we are quitting.")
            self._statusQueue.put("QUIT")
        self._shutdownTimer = wx.Timer(self, -1) #@UndefinedVariable
        self._shutdownTimer.Start(100)#10 times a second
        self.Bind(wx.EVT_TIMER, self._onShutdownTimer, id=self._shutdownTimer.GetId()) #@UndefinedVariable
        self._shutdownTimerCounter = 0
        self._mainSizer.Hide(self._menuSizer)
        self._mainSizer.Hide(self._trackAndEditAreaSizer)
        self._mainSizer.Hide(self._scrollingKeyboardPannel)

    def _onShutdownTimer(self, event):
        if(self._guiClient.hasGuiClientProcessToShutdownNicely() and self._midiListner.hasTcpMidiListnerProcessToShutdownNicely()):
            print "All done."
            if(sys.platform != "darwin"):
                self.Destroy()
            wx.Exit() #@UndefinedVariable
        else:
            self._shutdownTimerCounter += 1
            if(self._shutdownTimerCounter > 200):
                if(self._guiClient.hasGuiClientProcessToShutdownNicely() != False):
                    self._guiClient.forceGuiClientProcessToStop()
                if(self._midiListner.hasTcpMidiListnerProcessToShutdownNicely() != False):
                    self._midiListner.forceTcpMidiListnerProcessToStop()
                if(sys.platform != "darwin"):
                    self.Destroy()
                wx.Exit() #@UndefinedVariable


def startGui(debugMode, configDir, commandQueue = None, statusQueue = None):
    logFileName = APP_NAME + ".log"
    if(debugMode == True):
        redirectValue = 0
        oldLogFileName = logFileName + ".old"
        if(os.path.isfile(logFileName)):
            try:
                shutil.move(logFileName, oldLogFileName)
            except:
                pass
    else:
        redirectValue = 1
    if(sys.platform == "darwin"):
        os.environ["PATH"] += ":."
    app = wx.App(redirect = redirectValue, filename = logFileName) #@UndefinedVariable
    gui = TaktPlayerGui(None, configDir, debugMode, title="Takt Player GUI")
    if(commandQueue != None and statusQueue != None):
        gui.setupProcessQueues(commandQueue, statusQueue)
    app.MainLoop()

