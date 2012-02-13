'''
Created on 26. jan. 2012

@author: pcn
'''
import os
import sys
import wx
from wx.lib.scrolledpanel import ScrolledPanel #@UnresolvedImport
from widgets.PcnImageButton import PcnKeyboardButton, addTrackButtonFrame

from network.GuiClient import GuiClient
from midi.MidiUtilities import noteToNoteString
import time
from configurationGui.Configuration import Configuration
from configurationGui.MediaPoolConfig import MediaFileGui
from configuration.ConfigurationHolder import xmlToPrettyString

APP_NAME = "MusicalVideoPlayer"

class TaskHolder(object):
    class States():
        Init, Sendt, Received, Done = range(4)

    class RequestTypes():
        ActiveNotes, Note, File, Track, ConfigState, Configuration, LatestControllers = range(7)

    def __init__(self, description, taskType, widget, uniqueId = None):
        self._desc = description
        self._type = taskType
        self._widget = widget
        self._uniqueueId = uniqueId
        self._state = self.States.Init
        self._stateTime = time.time()
        self._startTime = self._stateTime
        self._timeout = 20.0
        if(self._type == self.RequestTypes.Track):
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

class MusicalVideoPlayerGui(wx.Frame): #@UndefinedVariable
    def __init__(self, parent, title):
        super(MusicalVideoPlayerGui, self).__init__(parent, title=title, 
            size=(1400, 600))
        self._configuration = Configuration()
        self._configuration.setLatestMidiControllerRequestCallback(self.getLatestControllers)

        self.SetBackgroundColour((120,120,120))

        mainSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        notKeyboardSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        midiTrackSizer=wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        keyboardSizer=wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---

        scrollingKeyboardPannel = ScrolledPanel(parent=self, id=wx.ID_ANY, size=(-1,87)) #@UndefinedVariable
        scrollingKeyboardPannel.SetupScrolling()
        scrollingKeyboardPannel.SetSizer(keyboardSizer)
        self._keyboardPanel = wx.Panel(scrollingKeyboardPannel, wx.ID_ANY, size=(3082,60)) #@UndefinedVariable
        scrollingKeyboardPannel.SetBackgroundColour(wx.Colour(0,0,0)) #@UndefinedVariable
        keyboardSizer.Add(self._keyboardPanel, wx.EXPAND, 0) #@UndefinedVariable

        scrollingMidiTrackPanel = wx.lib.scrolledpanel.ScrolledPanel(parent=self, id=wx.ID_ANY, size=(80,-1)) #@UndefinedVariable
        scrollingMidiTrackPanel.SetupScrolling()
        scrollingMidiTrackPanel.SetSizer(midiTrackSizer)
        self._midiTrackPanel = wx.Panel(scrollingMidiTrackPanel, wx.ID_ANY, size=(100,1200)) #@UndefinedVariable
        scrollingMidiTrackPanel.SetBackgroundColour(wx.Colour(132,132,132)) #@UndefinedVariable
        midiTrackSizer.Add(self._midiTrackPanel, wx.EXPAND, 0) #@UndefinedVariable

        self._noteGui = MediaFileGui(self, self._configuration)
        self._configuration.setNoteGui(self._noteGui)
        notKeyboardSizer.Add(scrollingMidiTrackPanel, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        notKeyboardSizer.Add(self._noteGui.getPlane(), proportion=1) #@UndefinedVariable

        mainSizer.Add(notKeyboardSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        mainSizer.Add(scrollingKeyboardPannel, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        self._whiteNoteBitmap = wx.Bitmap("graphics/whiteNote.png") #@UndefinedVariable
        self._blackNoteBitmapLeft = wx.Bitmap("graphics/blackNoteLeft.png") #@UndefinedVariable
        self._blackNoteBitmapRight = wx.Bitmap("graphics/blackNoteRight.png") #@UndefinedVariable
        self._blackNoteBitmap = wx.Bitmap("graphics/blackNote.png") #@UndefinedVariable
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

        self._trackThumbnailBitmap = wx.Bitmap("graphics/trackThumbnail.png") #@UndefinedVariable
        self._trackWidgets = []
        self._trackWidgetIds = []
        for track in range(16):
            trackButton = PcnKeyboardButton(self._midiTrackPanel, self._trackThumbnailBitmap, (2, 4+46*track), wx.ID_ANY, size=(42, 42), isBlack=False) #@UndefinedVariable
            trackButton.setFrqameAddingFunction(addTrackButtonFrame)
            trackButton.setBitmap(self._emptyBitMap)
            self._trackWidgets.append(trackButton)
            self._trackWidgetIds.append(trackButton.GetId())
            trackButton.Bind(wx.EVT_BUTTON, self._onTrackButton) #@UndefinedVariable
        self._selectedMidiChannel = -1

        self._updateTimer = wx.Timer(self, -1) #@UndefinedVariable
        self._updateTimer.Start(50)#20 times a second
        self.Bind(wx.EVT_TIMER, self._timedUpdate) #@UndefinedVariable
        self.Bind(wx.EVT_CLOSE, self._onClose) #@UndefinedVariable

        self.SetSizer(mainSizer)

        self.Show()

        self._taskQueue = []
        self._skippedTrackStateRequests = 99
        self._skippedConfigStateRequests = 99
        self._skippedLatestControllersRequests = 0
        self._lastConfigState = -1
        self._latestControllersRequestResult = None
        self.setupClientProcess()
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
        self._guiClient.startGuiClientProcess("127.0.0.1", 2021, None)

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
        self._requestLatestControllers()

    def _checkServerResponse(self):
        result = self._guiClient.getServerResponse()
        if(result[0] != None):
            if(result[0] == GuiClient.ResponseTypes.FileDownload):
                print "GuiClient.ResponseTypes.FileDownload"
                if(result[1] != None):
                    fileName = result[1]
                    foundTask = self._findQueuedTask(TaskHolder.RequestTypes.File, fileName)
                    if(foundTask == None):
                        print "Could not find task that belongs to this answer: " + fileName
                    else:
                        osFileName = os.path.normcase(fileName)
                        if(os.path.isfile(osFileName)):
                            foundTask.getWidget().setBitmapFile(osFileName)
            if(result[0] == GuiClient.ResponseTypes.ThumbRequest):
#                print "GuiClient.ResponseTypes.ThumbRequest"
                if(result[1] != None):
                    noteTxt, noteTime, fileName = result[1] #@UnusedVariable
                    noteId = max(min(int(noteTxt), 127), 0)
                    foundTask = self._findQueuedTask(TaskHolder.RequestTypes.Note, noteId)
                    if(foundTask == None):
                        print "Could not find task that belongs to this answer: " + noteTxt + ":" + noteTime + " -> " + fileName
                    else:
                        osFileName = os.path.normcase(fileName)
                        if(os.path.isfile(osFileName)):
                            self._noteWidgets[noteId].setBitmapFile(osFileName)
                        else:
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
            if(result[0] == GuiClient.ResponseTypes.TrackState):
#                print "GuiClient.ResponseTypes.TrackState"
                foundTask = self._findQueuedTask(TaskHolder.RequestTypes.Track, None)
                if(result[1] != None):
                    noteList = result[1]
                    for i in range(16):
                        note = int(noteList[i])
                        widget = self._trackWidgets[i]
                        if((note < 0) or (note > 127)):
                            widget.setBitmap(self._emptyBitMap)
                        else:
                            noteWidget = self._noteWidgets[note]
                            widget.setBitmap(noteWidget.getBitmap())
                    if(foundTask != None):
                        foundTask.taskDone()
                        self._taskQueue.remove(foundTask)
            if(result[0] == GuiClient.ResponseTypes.ConfigState):
#                print "GuiClient.ResponseTypes.ConfigState"
                foundTask = self._findQueuedTask(TaskHolder.RequestTypes.ConfigState, None)
                if(result[1] != None):
                    configId = result[1]
                    if(configId != self._lastConfigState):
#                        print "Config is updated on server.... TADA! Please do the right thing man :-P " + str(self._lastConfigState) + " != " + str(configId)
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
                    oldConfigString = self._configuration.getXmlString()
                    if(oldConfigString != newConfigString):
                        self._configuration.setFromXml(newConfigXml)
                        self.updateKeyboardImages()
                        print "#" * 150
                        self._configuration.printConfiguration()
                        print "#" * 150
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

    def _checkForStaleTasks(self):
        checkTime = time.time()
        for task in self._taskQueue:
            if(task.isStale(checkTime)):
                print task.getDescription() + " is stale..."
                if(task.getType() == TaskHolder.RequestTypes.ActiveNotes):
                    self._guiClient.requestActiveNoteList()
                    task.setState(TaskHolder.States.Sendt)
                elif(task.getType() == TaskHolder.RequestTypes.Track):
                    self._guiClient.requestTrackState()
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

    def _requestTrackState(self):
        if(self._skippedTrackStateRequests > 10):
            self._skippedTrackStateRequests = 0
            foundTask = self._findQueuedTask(TaskHolder.RequestTypes.Track, None)
            if(foundTask == None):
                trackRequestTask = TaskHolder("Track state request", TaskHolder.RequestTypes.Track, None, None)
                self._taskQueue.append(trackRequestTask)
                self._guiClient.requestTrackState()
                trackRequestTask.setState(TaskHolder.States.Sendt)
        else:
            self._skippedTrackStateRequests += 1

    def _requestConfigState(self):
        if(self._skippedConfigStateRequests > 30):
            self._skippedConfigStateRequests = 0
            foundTask = self._findQueuedTask(TaskHolder.RequestTypes.ConfigState, None)
            if(foundTask == None):
                configStateRequestTask = TaskHolder("Config state request", TaskHolder.RequestTypes.ConfigState, None, None)
                self._taskQueue.append(configStateRequestTask)
                self._guiClient.requestConfigState(self._lastConfigState)
                configStateRequestTask.setState(TaskHolder.States.Sendt)
        else:
            self._skippedConfigStateRequests += 1

    def _requestLatestControllers(self):
        if(self._skippedLatestControllersRequests > 20):
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

    def _onKeyboardButton(self, event):
        buttonId = event.GetEventObject().GetId()
        foundNoteId = None
        for i in range(128):
            if(self._noteWidgetIds[i] == buttonId):
                foundNoteId = i
                break
        if(foundNoteId != None):
            noteString = noteToNoteString(foundNoteId)
            print "sending note: " + str(foundNoteId) + " -> " + noteString
            self._configuration.getMidiSender().sendNoteOnOff(self._selectedMidiChannel, foundNoteId)
            noteConfig = self._configuration.getNoteConfiguration(foundNoteId)
            if(noteConfig == None):
                self._noteGui.clearGui(foundNoteId)
            else:
                self._noteGui.updateGui(noteConfig, foundNoteId)

    def _onTrackButton(self, event):
        buttonId = event.GetEventObject().GetId()
        foundTrackId = None
        for i in range(128):
            if(self._trackWidgetIds[i] == buttonId):
                foundTrackId = i
                break
        if(foundTrackId != None):
            print "track pressed id: " + str(foundTrackId)
            self._selectedMidiChannel = foundTrackId
            self._configuration.setSelectedMidiChannel(self._selectedMidiChannel)

    def _onClose(self, event):
        self.Destroy()
        self._guiClient.stopGuiClientProcess()

if __name__ == '__main__':
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
        MusicalVideoPlayerGui(None, title=APP_NAME)
        app.MainLoop()
#        print "wx Done"
    else:
        print "Exiting..."
