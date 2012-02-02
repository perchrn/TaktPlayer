'''
Created on 26. jan. 2012

@author: pcn
'''
import os
import sys
import wx
from widgets.PcnImageButton import PcnImageButton

from network.GuiClient import GuiClient

APP_NAME = "MusicalVideoPlayer"



class MusicalVideoPlayerGui(wx.Frame): #@UndefinedVariable
    def __init__(self, parent, title):
        super(MusicalVideoPlayerGui, self).__init__(parent, title=title, 
            size=(350, 210))
        self.SetBackgroundColour((120,120,120))

        panel = wx.Panel(self, -1) #@UndefinedVariable
        testText = wx.StaticText(panel, -1, "Input:") #@UndefinedVariable
        emptyBitMap = wx.EmptyBitmap (40, 30, depth=3) #@UndefinedVariable
        self._testButton = PcnImageButton(panel, emptyBitMap, -1) #@UndefinedVariable
        self._testButton.Bind(wx.EVT_BUTTON, self._onButton) #@UndefinedVariable

        sizer = wx.FlexGridSizer(cols=2, hgap=12, vgap=12) #@UndefinedVariable
        sizer.AddMany([testText, self._testButton])
        border = wx.BoxSizer() #@UndefinedVariable
        border.Add(sizer, 0, wx.ALL, 10) #@UndefinedVariable
        panel.SetSizerAndFit(border)


        self._updateTimer = wx.Timer(self, -1) #@UndefinedVariable
        self._updateTimer.Start(50)#20 times a second
        self.Bind(wx.EVT_TIMER, self._timedUpdate) #@UndefinedVariable

        self.Bind(wx.EVT_CLOSE, self._onClose) #@UndefinedVariable

        self.Show()

        self.setupClientProcess()

    def setupClientProcess(self):
        self._guiClient = GuiClient()
        self._guiClient.startGuiClientProcess("127.0.0.1", 2021, None)

    def _timedUpdate(self, event):
        result = self._guiClient.getServerResponse()
        if(result != None):
            if(os.path.isfile(result)):
                self._testButton.setBitmapFile(result)

    def _onButton(self, event):
        self._guiClient.requestImage("0C", 0.0)

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
