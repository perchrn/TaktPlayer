'''
Created on 26. jan. 2012

@author: pcn
'''
import os
import sys
import wx
from wx.lib.scrolledpanel import ScrolledPanel #@UnresolvedImport
from widgets.PcnImageButton import PcnKeyboardButton

from network.GuiClient import GuiClient
from midi.MidiUtilities import noteToNoteString, noteStringToNoteNumber
from network.SendMidiOverNet import SendMidiOverNet

APP_NAME = "MusicalVideoPlayer"



class MusicalVideoPlayerGui(wx.Frame): #@UndefinedVariable
    def __init__(self, parent, title):
        super(MusicalVideoPlayerGui, self).__init__(parent, title=title, 
            size=(1400, 600))
        self.SetBackgroundColour((120,120,120))

        mainSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        notKeyboardSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        midiTrackSizer=wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        keyboardSizer=wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---

        scrollingKeyboardPannel = ScrolledPanel(parent=self, id=wx.ID_ANY, size=(-1,87)) #@UndefinedVariable
        scrollingKeyboardPannel.SetBackgroundColour(wx.Colour(0,0,0)) #@UndefinedVariable
        scrollingKeyboardPannel.SetupScrolling()
        scrollingKeyboardPannel.SetSizer(keyboardSizer)
        self._keyboardPanel = wx.Panel(scrollingKeyboardPannel, wx.ID_ANY, size=(3082,70)) #@UndefinedVariable
        scrollingKeyboardPannel.SetBackgroundColour(wx.Colour(0,0,0)) #@UndefinedVariable
        keyboardSizer.Add(self._keyboardPanel, wx.EXPAND, 0) #@UndefinedVariable

        midiTrackPanel = wx.lib.scrolledpanel.ScrolledPanel(parent=self, id=wx.ID_ANY, size=(100,-1)) #@UndefinedVariable
        midiTrackPanel.SetBackgroundColour(wx.Colour(255,255,233)) #@UndefinedVariable
        midiTrackPanel.SetupScrolling()
        midiTrackPanel.SetSizer(midiTrackSizer)
        midiTrackText = "0\n1\n2\n3\n4\n5\n6\n7\n8\n9\nA\nB\nC\nD\nE\nF\n" * 3
        midiTrackThing=wx.StaticText(midiTrackPanel, -1, midiTrackText) #@UndefinedVariable
        midiTrackSizer.Add(midiTrackThing, wx.EXPAND, 0) #@UndefinedVariable

        restPanel = wx.Panel(self, wx.ID_ANY) #@UndefinedVariable
        restPanel.SetBackgroundColour(wx.Colour(255,255,0)) #@UndefinedVariable
        notKeyboardSizer.Add(midiTrackPanel, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        notKeyboardSizer.Add(restPanel, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

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

        self._updateTimer = wx.Timer(self, -1) #@UndefinedVariable
        self._updateTimer.Start(50)#20 times a second
        self.Bind(wx.EVT_TIMER, self._timedUpdate) #@UndefinedVariable

        self.Bind(wx.EVT_CLOSE, self._onClose) #@UndefinedVariable

        self.SetSizer(mainSizer)

        self.Show()

        self._midiSender = SendMidiOverNet("127.0.0.1", 2020)
        self.setupClientProcess()
        self.updateKeyboardImages()

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
        self._guiClient.requestActiveNoteList()
#        self._guiClient.requestImage(24, 0.0)

    def _timedUpdate(self, event):
        result = self._guiClient.getServerResponse()
        if(result[0] != None):
            if(result[0] == GuiClient.ResponseTypes.FileDownload):
                print "GuiClient.ResponseTypes.FileDownload"
                if(result[1] != None):
                    if(os.path.isfile(result[1])):
                        pass
        #TODO: find widgets an update...                for witingFile in self._waitFiles:
        #                    pass
            if(result[0] == GuiClient.ResponseTypes.ThumbRequest):
                print "GuiClient.ResponseTypes.ThumbRequest"
                if(result[1] != None):
                    noteTxt, noteTime, fileName = result[1] #@UnusedVariable
                    if(os.path.isfile(fileName)):
                        noteId = max(min(int(noteTxt), 127), 0)
                        self._noteWidgets[noteId].setBitmapFile(fileName)
                    else:
                        self._guiClient.requestImageFile(fileName)
                        #TODO: Queue in waiting files etc...
            if(result[0] == GuiClient.ResponseTypes.NoteList):
                print "GuiClient.ResponseTypes.NoteList"
                if(result[1] != None):
                    noteList = result[1]
                    for i in range(128):
                        found = False
                        for listEntryTxt in noteList:
                            if(int(listEntryTxt) == i):
                                print "requesting i= " + str(i)
                                self._guiClient.requestImage(i, 0.0)
                        if(found == False):
                            widget = self._noteWidgets[i]
                            widget.setBitmap(self._emptyBitMap)

    def _onKeyboardButton(self, event):
        buttonId = event.GetEventObject().GetId()
        foundNoteId = None
        for i in range(128):
            if(self._noteWidgetIds[i] == buttonId):
                foundNoteId = i
                break
        if(foundNoteId != None):
            noteString = noteToNoteString(foundNoteId)
            print "found note: " + str(foundNoteId) + " -> " + noteString
            self._midiSender.sendNoteOnOff(0, foundNoteId)

    def _onClose(self, event):
        self._guiClient.stopGuiClientProcess()
        self.Destroy()

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
