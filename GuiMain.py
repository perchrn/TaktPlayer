'''
Created on 26. jan. 2012

@author: pcn
'''
import os
import sys
import wx
from wx.lib.scrolledpanel import ScrolledPanel #@UnresolvedImport
from widgets.PcnImageButton import PcnKeyboardButton, PcnImageButton, addTrackButtonFrame, EVT_DRAG_DONE_EVENT, EVT_DRAG_START_EVENT

from network.GuiClient import GuiClient
from midi.MidiUtilities import noteToNoteString
import time
from configurationGui.Configuration import Configuration
from configurationGui.MediaPoolConfig import MediaFileGui
from configuration.ConfigurationHolder import xmlToPrettyString
import subprocess
import multiprocessing
from utilities.UrlSignature import UrlSignature
from configurationGui.MediaMixerConfig import MediaTrackGui
from media.VideoConvert import VideoConverterDialog

APP_NAME = "TaktPlayerGui"

class TaskHolder(object):
    class States():
        Init, Sendt, Received, Done = range(4)

    class RequestTypes():
        ActiveNotes, Note, File, Track, ConfigState, Configuration, LatestControllers, ConfigFileList, Preview = range(9)

    def __init__(self, description, taskType, widget, uniqueId = None):
        self._desc = description
        self._type = taskType
        self._widget = widget
        self._uniqueueId = uniqueId
        self._state = self.States.Init
        self._stateTime = time.time()
        self._startTime = self._stateTime
        self._timeout = 20.0
        if((self._type == self.RequestTypes.Track) or (self._type == self.RequestTypes.Preview)):
            self._timeout = 5.0

    def getDescription(self):
        return self._desc

    def getType(self):
        return self._type

    def getUniqueId(self):
        return self._uniqueueId

    def getWidget(self):
        return self._widget

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
        for name in filenames:
            self._callbackFunction(self._widgetId, name)
            break

class MusicalVideoPlayerGui(wx.Frame): #@UndefinedVariable
    def __init__(self, parent, title):
        super(MusicalVideoPlayerGui, self).__init__(parent, title=title, 
            size=(800, 600))

        wxIcon = wx.Icon(os.path.normpath("graphics/TaktGui.ico"), wx.BITMAP_TYPE_ICO)
        self.SetIcon(wxIcon)

        self._configuration = Configuration()
        self._configuration.setLatestMidiControllerRequestCallback(self.getLatestControllers)
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
        self._oldServerConfigurationString = ""
        self._oldServerConfigList = ""
        self._oldServerActiveConfig = ""

        self.SetBackgroundColour((120,120,120))

        self._mainSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._menuSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        menuSeperatorSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._trackAndEditAreaSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        editAreaSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        midiTrackSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        keyboardSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---

        menuPannel =  wx.Panel(self, wx.ID_ANY, size=(3000,29)) #@UndefinedVariable
        menuPannel.SetBackgroundColour(wx.Colour(200,200,200)) #@UndefinedVariable
        menuPannel.SetSizer(self._menuSizer) #@UndefinedVariable
        menuSeperatorPannel =  wx.Panel(self, wx.ID_ANY, size=(3000,2)) #@UndefinedVariable
        menuSeperatorPannel.SetBackgroundColour(wx.Colour(200,200,200)) #@UndefinedVariable
        menuSeperatorPannel.SetSizer(menuSeperatorSizer) #@UndefinedVariable

        self._scrollingKeyboardPannel = ScrolledPanel(parent=self, id=wx.ID_ANY, size=(-1,87)) #@UndefinedVariable
        self._scrollingKeyboardPannel.SetupScrolling(True, False)
        self._scrollingKeyboardPannel.SetSizer(keyboardSizer)
        self._keyboardPanel = wx.Panel(self._scrollingKeyboardPannel, wx.ID_ANY, size=(3082,60)) #@UndefinedVariable
        self._scrollingKeyboardPannel.SetBackgroundColour(wx.Colour(0,0,0)) #@UndefinedVariable
        keyboardSizer.Add(self._keyboardPanel, wx.EXPAND, 0) #@UndefinedVariable

        scrollingMidiTrackPanel = wx.lib.scrolledpanel.ScrolledPanel(parent=self, id=wx.ID_ANY, size=(98,-1)) #@UndefinedVariable
        scrollingMidiTrackPanel.SetupScrolling(False, True)
        scrollingMidiTrackPanel.SetSizer(midiTrackSizer)
        self._midiTrackPanel = wx.Panel(scrollingMidiTrackPanel, wx.ID_ANY, size=(98,1200)) #@UndefinedVariable
        scrollingMidiTrackPanel.SetBackgroundColour(wx.Colour(170,170,170)) #@UndefinedVariable
        midiTrackSizer.Add(self._midiTrackPanel, wx.EXPAND, 0) #@UndefinedVariable

        scrollingEditAreaPanel = wx.lib.scrolledpanel.ScrolledPanel(parent=self, id=wx.ID_ANY, size=(-1,-1)) #@UndefinedVariable
        scrollingEditAreaPanel.SetupScrolling(True, True)
        scrollingEditAreaPanel.SetSizer(editAreaSizer)

        self._trackGui = MediaTrackGui(self._configuration)
        self._configuration.setMixerGui(self._trackGui)
        self._noteGui = MediaFileGui(scrollingEditAreaPanel, self._configuration, self._trackGui)
        self._configuration.setNoteGui(self._noteGui)
        self._trackAndEditAreaSizer.Add(scrollingMidiTrackPanel, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._trackAndEditAreaSizer.Add(scrollingEditAreaPanel, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._mainSizer.Add(self._menuSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._mainSizer.Add(menuSeperatorSizer, proportion=0) #@UndefinedVariable
        self._mainSizer.Add(self._trackAndEditAreaSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._mainSizer.Add(self._scrollingKeyboardPannel, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        self._sendButton = wx.Button(menuPannel, wx.ID_ANY, 'Send') #@UndefinedVariable
        self._sendButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._midiButton = wx.Button(menuPannel, wx.ID_ANY, 'MIDI on') #@UndefinedVariable
        self._updateMidiButtonColor(self._configuration.isMidiEnabled())
        self._configNameField = wx.TextCtrl(menuPannel, wx.ID_ANY, "N/A", size=(120, -1)) #@UndefinedVariable
        self._configFileSelector = wx.ComboBox(menuPannel, wx.ID_ANY, size=(160, -1), choices=["N/A"], style=wx.CB_READONLY) #@UndefinedVariable
        self._configFileSelector.SetStringSelection("N/A")
        self._loadButton = wx.Button(menuPannel, wx.ID_ANY, 'Load') #@UndefinedVariable
        self._loadButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._saveButton = wx.Button(menuPannel, wx.ID_ANY, 'Save') #@UndefinedVariable
        self._saveButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._menuSizer.Add(self._sendButton, 0, wx.EXPAND|wx.ALL, 3) #@UndefinedVariable
        self._menuSizer.Add(self._midiButton, 0, wx.EXPAND|wx.ALL, 3) #@UndefinedVariable
        self._menuSizer.Add(self._configNameField, 0, wx.EXPAND|wx.ALL, 3) #@UndefinedVariable
        self._menuSizer.Add(self._configFileSelector, 0, wx.EXPAND|wx.ALL, 3) #@UndefinedVariable
        self._menuSizer.Add(self._loadButton, 0, wx.EXPAND|wx.ALL, 3) #@UndefinedVariable
        self._menuSizer.Add(self._saveButton, 0, wx.EXPAND|wx.ALL, 3) #@UndefinedVariable
        menuPannel.Bind(wx.EVT_BUTTON, self._onSendButton, id=self._sendButton.GetId()) #@UndefinedVariable
        menuPannel.Bind(wx.EVT_BUTTON, self._midiToggle, id=self._midiButton.GetId()) #@UndefinedVariable
        menuPannel.Bind(wx.EVT_BUTTON, self._onLoadButton, id=self._loadButton.GetId()) #@UndefinedVariable
        menuPannel.Bind(wx.EVT_BUTTON, self._onSaveButton, id=self._saveButton.GetId()) #@UndefinedVariable

        self._whiteNoteBitmap = wx.Bitmap("graphics/whiteNote.png") #@UndefinedVariable
        self._blackNoteBitmapLeft = wx.Bitmap("graphics/blackNoteLeft.png") #@UndefinedVariable
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
            keyboardButton = self.createNoteWidget(octavNote, baseX, (note==127))
            self._noteWidgets.append(keyboardButton)
            self._noteWidgetIds.append(keyboardButton.GetId())
            keyboardButton.Bind(wx.EVT_BUTTON, self._onKeyboardButton) #@UndefinedVariable
            keyboardButton.Bind(EVT_DRAG_START_EVENT, self._onDragStart)
            keyboardButton.Bind(EVT_DRAG_DONE_EVENT, self._onDragDone)
            dropTarget = FileDrop(keyboardButton.GetId(), self.fileDropped)
            keyboardButton.SetDropTarget(dropTarget)

        self._activeNoteId = 24
        self._noteGui.updateOverviewClipBitmap(self._emptyBitMap)
        self._noteGui.clearGui(self._activeNoteId)
        self._selectKeyboardKey(self._activeNoteId)

        self._trackThumbnailBitmap = wx.Bitmap("graphics/blackClip.png") #@UndefinedVariable
        self._trackEditBitmap = wx.Bitmap("graphics/editButton.png") #@UndefinedVariable
        self._trackEditPressedBitmap = wx.Bitmap("graphics/editButtonPressed.png") #@UndefinedVariable
        self._trackPlayBitmap = wx.Bitmap("graphics/playButton.png") #@UndefinedVariable
        self._trackPlayPressedBitmap = wx.Bitmap("graphics/playButtonPressed.png") #@UndefinedVariable
        self._trackWidgets = []
        self._activeTrackNotes = []
        self._activeTrackId = -1
        self._trackWidgetIds = []
        self._trackEditWidgetsIds = []
        self._trackPlayWidgets = []
        self._trackPlayWidgetsIds = []
        for track in range(16):
            extraSpace = ""
            if(track < 9):
                extraSpace = " "
            wx.StaticText(self._midiTrackPanel, wx.ID_ANY, extraSpace + str(track + 1), pos=(2, 4+36*track)) #@UndefinedVariable
            trackButton = PcnKeyboardButton(self._midiTrackPanel, self._trackThumbnailBitmap, (16, 4+36*track), wx.ID_ANY, size=(42, 32), isBlack=False) #@UndefinedVariable
            trackButton.setFrqameAddingFunction(addTrackButtonFrame)
            trackButton.setBitmap(self._emptyBitMap)
            trackPlayButton = PcnImageButton(self._midiTrackPanel, self._trackPlayBitmap, self._trackPlayPressedBitmap, (60, 21+36*track), wx.ID_ANY, size=(15, 15)) #@UndefinedVariable
            self._trackWidgets.append(trackButton)
            self._activeTrackNotes.append(-1)
            self._trackPlayWidgets.append(trackPlayButton)
            self._trackWidgetIds.append(trackButton.GetId())
            self._trackPlayWidgetsIds.append(trackPlayButton.GetId())
            trackButton.Bind(wx.EVT_BUTTON, self._onTrackButton) #@UndefinedVariable
            trackPlayButton.Bind(wx.EVT_BUTTON, self._onTrackPlayButton) #@UndefinedVariable

        self._selectedMidiChannel = 0
        self._selectTrackKey(self._selectedMidiChannel)
        self._trackSelected(self._selectedMidiChannel)

        self._updateTimer = wx.Timer(self, -1) #@UndefinedVariable
        self._updateTimer.Start(50)#20 times a second
        self.Bind(wx.EVT_TIMER, self._timedUpdate, id=self._updateTimer.GetId()) #@UndefinedVariable
        self.Bind(wx.EVT_LEFT_DOWN, self._onMouseClick) #@UndefinedVariable
        self.Bind(wx.EVT_CLOSE, self._onClose) #@UndefinedVariable

        self.SetSizer(self._mainSizer)

        self.Show()

        self._taskQueue = []
        self._skippedTrackStateRequests = 99
        self._skippedPreviewRequests = 99
        self._skippedConfigStateRequests = 99
        self._skippedConfigListRequests = 99
        self._skippedLatestControllersRequests = 0
        self._stoppingWebRequests = True
        self._lastConfigState = -1
        self._latestControllersRequestResult = None
        self._dragSource = None
        self.setupClientProcess()
        self._oldServerConfigurationString = self._configuration.getXmlString()
        self._timedUpdate(None)

    def createNoteWidget(self, noteId, baseX, lastNote=False):
        buttonPos = None
        bitmap = None
        if(noteId == 0):
            buttonPos = ( 0+baseX, 36)
            bitmap = self._whiteNoteBitmap
            wx.StaticBitmap(self._keyboardPanel, pos=(buttonPos[0], 1), bitmap=self._blackNoteBitmapLeft, id=wx.ID_ANY) #@UndefinedVariable
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
            wx.StaticBitmap(self._keyboardPanel, pos=(buttonPos[0]+22, 1), bitmap=self._blackNoteBitmapRight, id=wx.ID_ANY) #@UndefinedVariable
        elif(noteId == 5):
            buttonPos = (132+baseX, 36)
            bitmap = self._whiteNoteBitmap
            wx.StaticBitmap(self._keyboardPanel, pos=(buttonPos[0], 1), bitmap=self._blackNoteBitmapLeft, id=wx.ID_ANY) #@UndefinedVariable
        elif(noteId == 6):
            buttonPos = (154+baseX,  1)
            bitmap = self._blackNoteBitmap
        elif(noteId == 7):
            buttonPos = (176+baseX, 36)
            bitmap = self._whiteNoteBitmap
            if(lastNote == True):
                wx.StaticBitmap(self._keyboardPanel, pos=(buttonPos[0]+22, 1), bitmap=self._blackNoteBitmapRight, id=wx.ID_ANY) #@UndefinedVariable
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
            wx.StaticBitmap(self._keyboardPanel, pos=(buttonPos[0]+22, 1), bitmap=self._blackNoteBitmapRight, id=wx.ID_ANY) #@UndefinedVariable
        else:
            return None
        keyboardButton = PcnKeyboardButton(self._keyboardPanel, bitmap, buttonPos, wx.ID_ANY, size=(44, 35), isBlack=(buttonPos[1]==1)) #@UndefinedVariable
        keyboardButton.setBitmap(self._emptyBitMap)
        return keyboardButton

    def setupClientProcess(self):
        self._guiClient = GuiClient()
        host, port = self._configuration.getWebConfig()
        self._guiClient.startGuiClientProcess(host, port, None)

    def updateKeyboardImages(self):
        activeNotesTask = TaskHolder("Active notes request", TaskHolder.RequestTypes.ActiveNotes, None)
        self._taskQueue.append(activeNotesTask)
        self._guiClient.requestActiveNoteList()
        activeNotesTask.setState(TaskHolder.States.Sendt)

    def _findQueuedTask(self, taskType, uniqueId = None):
        foundTask = None
        for task in self._taskQueue:
            if(task.getType() == taskType):
                if((uniqueId == None) or (task.getUniqueId() == uniqueId)):
                    if(foundTask != None):
                        self._taskQueue.remove(task)
                    else:
                        foundTask = task
        return foundTask

    def _timedUpdate(self, event):
        self._checkServerResponse()
        self._checkForStaleTasks()
        self._requestConfigState()
        self._requestTrackState()
        self._requestPreview()
        self._requestConfigList()
        self._requestLatestControllers()

    def _checkServerResponse(self):
        result = self._guiClient.getServerResponse()
        if(result[0] != None):
            if(result[0] == GuiClient.ResponseTypes.FileDownload):
#                print "GuiClient.ResponseTypes.FileDownload"
                if(result[1] != None):
                    fileName, playerFileName = result[1]
                    if(playerFileName == os.path.normpath("thumbs/preview.jpg")):
#                        print "DEBUG Got preview!!!"
                        foundTask = self._findQueuedTask(TaskHolder.RequestTypes.Preview, None)
                        osFileName = os.path.normpath(fileName)
                        self._trackGui.updatePreviewImage(osFileName)
                        if(foundTask != None):
                            foundTask.taskDone()
                            self._taskQueue.remove(foundTask)
                    else:
                        foundTask = self._findQueuedTask(TaskHolder.RequestTypes.File, playerFileName)
                        if(foundTask == None):
                            print "Could not find task that belongs to this answer: " + fileName
                        else:
                            osFileName = os.path.normpath(fileName)
                            if(os.path.isfile(osFileName)):
                                foundTask.getWidget().setBitmapFile(osFileName)
                            if((self._activeNoteId >= 0) and (self._activeNoteId < 128)):
                                noteWidget = self._noteWidgets[self._activeNoteId]
                                noteBitmap = noteWidget.getBitmap()
                                self._noteGui.updateOverviewClipBitmap(noteBitmap)
            if(result[0] == GuiClient.ResponseTypes.ThumbRequest):
#                print "GuiClient.ResponseTypes.ThumbRequest"
                if(result[1] != None):
                    noteTxt, noteTime, fileName = result[1] #@UnusedVariable
                    noteId = max(min(int(noteTxt), 127), 0)
                    foundTask = self._findQueuedTask(TaskHolder.RequestTypes.Note, noteId)
                    if(foundTask == None):
                        print "Could not find task that belongs to this answer: " + noteTxt + ":" + noteTime + " -> " + fileName
                    else:
                        osFileName = os.path.normpath(fileName)
                        if(os.path.isfile(osFileName)):
                            self._noteWidgets[noteId].setBitmapFile(osFileName)
                            if((self._activeNoteId >= 0) and (self._activeNoteId < 128)):
                                noteWidget = self._noteWidgets[self._activeNoteId]
                                noteBitmap = noteWidget.getBitmap()
                                self._noteGui.updateOverviewClipBitmap(noteBitmap)
                        else:
                            fileRequestTask = TaskHolder("File request for note %d" %(foundTask.getUniqueId()), TaskHolder.RequestTypes.File, foundTask.getWidget(), fileName)
                            self._taskQueue.append(fileRequestTask)
                            self._guiClient.requestImageFile(fileName)
                            fileRequestTask.setState(TaskHolder.States.Sendt)
                        foundTask.taskDone()
                        self._taskQueue.remove(foundTask)
            if(result[0] == GuiClient.ResponseTypes.NoteList):
                print "GuiClient.ResponseTypes.NoteList"
                foundTask = self._findQueuedTask(TaskHolder.RequestTypes.ActiveNotes, None)
                if(result[1] != None):
                    noteList = result[1]
                    for i in range(128):
                        found = False
                        for listEntryTxt in noteList:
                            if(int(listEntryTxt) == i):
#                                print "requesting i= " + str(i)
                                imageRequestTask = TaskHolder("Note request for note %d:%.2f" %(i, 0.0), TaskHolder.RequestTypes.Note, self._noteWidgets[i], i)
                                self._taskQueue.append(imageRequestTask)
                                self._guiClient.requestImage(i, 0.0)
                                imageRequestTask.setState(TaskHolder.States.Sendt)
                                found = True
                        if(found == False):
                            widget = self._noteWidgets[i]
                            widget.setBitmap(self._emptyBitMap)
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
                    self._stoppingWebRequests = False
                    noteList = result[1]
                    for i in range(16):
                        note = int(noteList[i])
                        widget = self._trackWidgets[i]
                        if((note < 0) or (note > 127)):
                            widget.setBitmap(self._emptyBitMap)
                            if((i == self._activeTrackId) and (self._activeTrackNotes[i] != -1)):
                                self._noteGui.clearTrackOverviewGui()
                                self._trackGui.updateMixModeOverviewThumb("None")
                            self._activeTrackNotes[i] = -1
                        else:
                            noteWidget = self._noteWidgets[note]
                            noteBitmap = noteWidget.getBitmap()
                            widget.setBitmap(noteBitmap)
                            if(i == self._activeTrackId):
                                self._noteGui.updateTrackOverviewClipBitmap(noteBitmap)
                                activeNoteConfig = self._configuration.getNoteConfiguration(note)
                                if(activeNoteConfig == None):
                                    self._noteGui.clearTrackOverviewGui()
                                    self._trackGui.updateMixModeOverviewThumb("None")
                                else:
                                    self._noteGui.updateTrackOverviewGui(activeNoteConfig, note)
                                    self._trackGui.updateMixModeOverviewThumb(activeNoteConfig.getMixMode())
                            self._activeTrackNotes[i] = note
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
                        if(currentGuiConfigString != self._oldServerConfigurationString):
                            if(newConfigString == currentGuiConfigString):
                                loadConfig = False
                            else:
                                print "Both configs are updated! " * 5
                                print "GUI " * 50
                                print currentGuiConfigString
                                print "NEW " * 50
                                print newConfigString
                                print "XXX " * 50
                                text = "Both the configuration on the sever and in the GUI has been updated. Would you like to discard local configuration and load server version?"
                                dlg = wx.MessageDialog(self, text, 'Load server configuration?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                                dialogResult = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                                dlg.Destroy()
                                if(dialogResult == False):
                                    loadConfig = False
                        if(loadConfig == True):
                            self._configuration.setFromXml(newConfigXml)
                            noteConfig = self._configuration.getNoteConfiguration(self._activeNoteId)
                            if(noteConfig == None):
                                self._noteGui.updateOverviewClipBitmap(self._emptyBitMap)
                                self._noteGui.clearGui(self._activeNoteId)
                            else:
                                noteWidget = self._noteWidgets[self._activeNoteId]
                                noteBitmap = noteWidget.getBitmap()
                                self._noteGui.updateOverviewClipBitmap(noteBitmap)
                                self._noteGui.updateGui(noteConfig, self._activeNoteId)
                            self._selectTrackKey(self._selectedMidiChannel)
                            self._configuration.updateEffectList(None)
                            self._configuration.updateFadeList(None)
                            print "#" * 150
                            self._configuration.printConfiguration()
                            print "#" * 150
                        self.updateKeyboardImages()
                    self._oldServerConfigurationString = newConfigString
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
                    configurationFileListString, activeConfig = result[1]
                    if((self._oldServerConfigList != configurationFileListString) or (self._oldServerActiveConfig != activeConfig)):
                        configurationFileLists = configurationFileListString.split(';', 128)
                        if(self._oldServerActiveConfig != activeConfig):
                            selectedValue = activeConfig
                            self._oldServerActiveConfig = activeConfig
                        else:
                            selectedValue = self._configFileSelector.GetValue()
                        self._configFileSelector.Clear()
                        valueOk = False
                        self._configFileSelector.Append("active configuration")
                        for choice in configurationFileLists:
                            self._configFileSelector.Append(choice)
                            if(choice == selectedValue):
                                valueOk = True
                        if(valueOk == True):
                            self._configFileSelector.SetStringSelection(selectedValue)
                        else:
                            self._configFileSelector.SetStringSelection("active configuration")
                        self._configNameField.SetValue(activeConfig)
                    self._oldServerConfigList = configurationFileListString
                    if(foundTask != None):
                        foundTask.taskDone()
                        self._taskQueue.remove(foundTask)

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

    def getLatestControllers(self):
        return self._latestControllersRequestResult

    def _onSendButton(self, event):
        xmlString = self._configuration.getXmlString()
        urlTest = UrlSignature()
        urlTest.getSigantureFieldsForFile("configuration", "temp.cfg", xmlString)
        self._guiClient.sendConfiguration(xmlString)

    def _updateMidiButtonColor(self, midiOn):
        if(midiOn == True):
            self._midiButton.SetBackgroundColour(wx.Colour(200,255,200)) #@UndefinedVariable
        else:
            self._midiButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable

    def _midiToggle(self, event):
        midiOn = self._configuration.isMidiEnabled()
        if(midiOn == True):
            self._configuration.setMidiEnable(False)
        else:
            self._configuration.setMidiEnable(True)
        self._updateMidiButtonColor(midiOn)

    def _onLoadButton(self, event):
        selectedConfig = self._configFileSelector.GetValue()
        print "LOAD: " + str(selectedConfig)
        self._guiClient.requestConfigChange(selectedConfig)

    def _onSaveButton(self, event):
        selectedConfig = self._configNameField.GetValue()
        print "SAVE: " + str(selectedConfig)
        self._guiClient.requestConfigSave(selectedConfig)

    def _onNewButton(self):
        pass

    def _selectKeyboardKey(self, keyId):
        if((keyId >= 0) and (keyId < 128)):
            self._noteWidgets[keyId].setSelected()
        for i in range(128):
            widget = self._noteWidgets[i]
            if(i != keyId):
                widget.unsetSelected()

    def _selectTrackKey(self, trackId):
        if((trackId >= 0) and (trackId < 16)):
            self._trackWidgets[trackId].setSelected()
        for i in range(16):
            widget = self._trackWidgets[i]
            if(i != trackId):
                widget.unsetSelected()

    def _selectTrackPlayer(self, trackId):
        if((trackId >= 0) and (trackId < 16)):
            self._trackPlayWidgets[trackId].setSelected()
        for i in range(16):
            widget = self._trackPlayWidgets[i]
            if(i != trackId):
                widget.unsetSelected()

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

    def _onDragStart(self, event):
        self._dragSource = event.GetEventObject().GetId()
        self._noteGui.setDragCursor()

    def _onDragDone(self, event):
        self._noteGui.clearDragCursor()
        if(self._dragSource == None):
            print "DEBUG drag done..."
        else:
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
                                self._noteWidgets[destNoteId].setBitmap(self._noteWidgets[sourceNoteId].getBitmap())
        self._dragSource = None

    def _onMouseClick(self, event):
        self._dragSource = None
        self._noteGui.clearDragCursor()

    def _call_command(self, command):
        outputString = ""
        try:
            process = subprocess.Popen(command.split(' '), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except:
            text = "Unable to execute ffmpeg command: \"" + command + "\"\n"
            text += " from directory: \"" + os.getcwd() + "\"\n"
            text += "\nPlease check your path or update GuiMain.bat.\n"
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

    def fileDropped(self, widgetId, fileName):
        destNoteId = None
        for i in range(128):
            if(self._noteWidgetIds[i] == widgetId):
                destNoteId = i
                break
        ffmpegPath = os.path.normpath(self._configuration.getFfmpegBinary())
        if(destNoteId != None):
            ffmpegString = self._call_command(ffmpegPath + " -i " + fileName)
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
                                if(("MJPG" in ffmpegLine) and ("0x47504A4D" in ffmpegLine)):
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
                        text = "Convert file: " + fileName
                        self._convertionWentOk = False
                        dlg = VideoConverterDialog(self, 'Convert file...', self._updateValuesFromConvertDialogCallback,
                                                   ffmpegPath, self._videoSaveSubDir, self._videoDirectory, fileName, 
                                                   self._videoCropMode, self._videoScaleMode, self._videoScaleX, self._videoScaleY)
                        dlg.ShowModal()
                        dlg.Destroy()
                        if(self._convertionWentOk == True):
                            fileName = self._convertionOutputFileName
                            inputOk = True
                #TODO: Check and ask if we should "move" file...
                if(inputOk == True):
                    relativeFileName = os.path.relpath(fileName, self._videoDirectory)
                    print "Setting %d (%s) to fileName: %s" % (destNoteId, noteToNoteString(destNoteId), relativeFileName)
                    destinationConfig = self._configuration.getNoteConfiguration(destNoteId)
                    if(destinationConfig == None):
                        destinationConfig = self._configuration.makeNoteConfig(relativeFileName, noteToNoteString(destNoteId), destNoteId)
                    if(destinationConfig != None):
                        destinationConfig.updateFileName(relativeFileName, inputIsVideo)
                        self._noteWidgets[destNoteId].setBitmap(self._newNoteBitmap)
                        self._noteGui.updateGui(destinationConfig, destNoteId)
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

    def _onTrackButton(self, event):
        buttonId = event.GetEventObject().GetId()
        foundTrackId = None
        for i in range(16):
            if(self._trackWidgetIds[i] == buttonId):
                foundTrackId = i
                break
        if(foundTrackId != None):
            self._selectTrackKey(foundTrackId)
            self._trackSelected(foundTrackId)

    def _trackSelected(self, selectedTrackId):
        self._activeTrackId = selectedTrackId
        destinationConfig = self._configuration.getTrackConfiguration(self._activeTrackId)
        if(destinationConfig != None):
            activeNoteId = self._activeTrackNotes[self._activeTrackId]
            noteMixMode = "Default"
            if((activeNoteId >= 0) and (activeNoteId < 128)):
                activeNoteConfig = self._configuration.getNoteConfiguration(activeNoteId)
                if(activeNoteConfig != None):
                    noteWidget = self._noteWidgets[activeNoteId]
                    noteBitmap = noteWidget.getBitmap()
                    noteMixMode = activeNoteConfig.getMixMode()
                    self._noteGui.updateTrackOverviewClipBitmap(noteBitmap)
                    self._noteGui.updateTrackOverviewGui(activeNoteConfig, activeNoteId)
                else:
                    self._noteGui.clearTrackOverviewGui()
            else:
                noteMixMode = "None"
                self._noteGui.clearTrackOverviewGui()
            self._trackGui.updateGui(destinationConfig, self._activeTrackId, activeNoteId, noteMixMode)

    def _onTrackPlayButton(self, event):
        buttonId = event.GetEventObject().GetId()
        foundTrackId = None
        for i in range(16):
            if(self._trackPlayWidgetsIds[i] == buttonId):
                foundTrackId = i
                break
        if(foundTrackId != None):
            if(self._selectedMidiChannel == foundTrackId):
                self._selectedMidiChannel = -1
                self._selectTrackPlayer(-1)
            else:
                self._selectedMidiChannel = foundTrackId
                self._selectTrackPlayer(foundTrackId)
            self._configuration.setSelectedMidiChannel(self._selectedMidiChannel)

    def _onClose(self, event):
        self._guiClient.requestGuiClientProcessToStop()
        self._shutdownTimer = wx.Timer(self, -1) #@UndefinedVariable
        self._shutdownTimer.Start(100)#10 times a second
        self.Bind(wx.EVT_TIMER, self._onShutdownTimer, id=self._shutdownTimer.GetId()) #@UndefinedVariable
        self._shutdownTimerCounter = 0
        self._mainSizer.Hide(self._menuSizer)
        self._mainSizer.Hide(self._trackAndEditAreaSizer)
        self._mainSizer.Hide(self._scrollingKeyboardPannel)

    def _onShutdownTimer(self, event):
        if(self._guiClient.hasGuiClientProcessToShutdownNicely()):
            print "All done."
            self.Destroy()
            wx.Exit()
        else:
            self._shutdownTimerCounter += 1
            if(self._shutdownTimerCounter > 200):
                self._guiClient.forceGuiClientProcessToStop()
                self.Destroy()
                wx.Exit()
      
if __name__ == '__main__':
    multiprocessing.freeze_support()
    dirOk = True
    scriptDir = os.path.dirname(sys.argv[0])
    if((scriptDir != "") and (scriptDir != os.getcwd())):
        os.chdir(scriptDir)
        if(scriptDir != os.getcwd()):
            print "Could not go to correct directory: " + scriptDir + " we are in " + os.getcwd()
            dirOk = False
#    print "CWD: %s" % os.getcwd()
    if(dirOk):
#        print "Starting wx"
        app = wx.App(redirect = 0, filename = APP_NAME + ".log") #@UndefinedVariable
        MusicalVideoPlayerGui(None, title="Takt Player GUI")
        app.MainLoop()
#        print "wx Done"
    else:
        print "Exiting..."
