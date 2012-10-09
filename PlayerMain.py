'''
Created on 28. nov. 2011

@author: pcn
'''

#Imports
from configuration.EffectSettings import EffectTemplates, FadeTemplates, EffectImageList,\
    TimeModulationTemplates
from configuration.GuiServer import GuiServer
import multiprocessing
from multiprocessing import Process, Queue
from configuration.PlayerConfiguration import PlayerConfiguration
import sys
import shutil
import os

import wx

#pcn stuff
from configuration.ConfigurationHolder import ConfigurationHolder

from video.media.MediaMixer import MediaMixer
from video.media.MediaPool import MediaPool

#from video.media.MediaFile import createCvWindow, showCvImage, hasCvWindowStoped, addCvMouseCallback

from midi.MidiTiming import MidiTiming
from midi.TcpMidiListner import TcpMidiListner
from midi.MidiStateHolder import MidiStateHolder, SpecialModulationHolder

from utilities import MultiprocessLogger

#Python standard
import time
import signal
#Log system
import logging
logging.root.setLevel(logging.ERROR)

APP_NAME = "TaktPlayer"
launchGUI = True
applicationHolder = None

class PlayerMain(wx.Frame):
    def __init__(self, parent, configDir, configFile, title):
        super(PlayerMain, self).__init__(parent, title=title, size=(800, 600))
        self._configDirArgument = configDir

        if(os.path.isfile("graphics/TaktPlayer.ico")):
            wxIcon = wx.Icon(os.path.normpath("graphics/TaktPlayer.ico"), wx.BITMAP_TYPE_ICO) #@UndefinedVariable
            self.SetIcon(wxIcon)
        elif(os.path.isfile("TaktPlayer.ico")):
            wxIcon = wx.Icon(os.path.normpath("TaktPlayer.ico"), wx.BITMAP_TYPE_ICO) #@UndefinedVariable
            self.SetIcon(wxIcon)

        #Multithreaded logging utility and regular logging:
        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
#        self._log.setLevel(logging.WARNING)
        self._multiprocessLogger = MultiprocessLogger.MultiprocessLogger(self._log)

        screenWidth = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
        screenHeight = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
        print "DEBUG screensize: " + str((screenWidth, screenHeight))

        self._playerConfiguration = PlayerConfiguration(self._configDirArgument)
        configFullscreenmode = self._playerConfiguration.getFullscreenMode().lower()
        configResolution = self._playerConfiguration.getResolution()
        configPositionX, configPositionY = self._playerConfiguration.getPosition()
        if(configFullscreenmode == "auto"):
            self._internalResolutionX = screenWidth
            self._internalResolutionY =  screenHeight
            self._fullscreenMode = True
        elif(configFullscreenmode == "on"):
            self._internalResolutionX = configResolution[0]
            self._internalResolutionY =  configResolution[1]
            self._fullscreenMode = True
        else:
            self._internalResolutionX = configResolution[0]
            self._internalResolutionY =  configResolution[1]
            self._fullscreenMode = False

        self.Show()
        if(self._fullscreenMode == True):
            self.ShowFullScreen(True, style=wx.FULLSCREEN_ALL)
        else:
            startupSizeX, startupSizeY = self.ClientSize
            neededExtraX = 800 - startupSizeX
            neededExtraY = 600 - startupSizeY
            baseWindowSizeX = self._internalResolutionX + neededExtraX
            baseWindowSizeY = self._internalResolutionY + neededExtraY
            borderX = 0
            if((baseWindowSizeX + 40) < screenWidth):
                borderX = 40
            borderY = 0
            if((baseWindowSizeY + 40) < screenHeight):
                borderY = 40
            windowSizeX = baseWindowSizeX + borderX
            windowSizeY = baseWindowSizeY + borderY
#            print "SetSize: " + str(self._fullscreenMode) + " | " + str(windowSizeX) + " | " + str(windowSizeY) + " | " + str(configPositionX) + " | " + str(configPositionY)
            self.SetSize((windowSizeX, windowSizeY))
            if((configPositionX >= 0) and (configPositionY >= 0)):
                self.SetPosition((configPositionX, configPositionY))

        self._configurationTree = ConfigurationHolder("MusicalVideoPlayer")
        if(configFile != ""):
            filePath = os.path.join(self._playerConfiguration.getConfigDir(), configFile)
            if(os.path.isfile(filePath)):
                self._configurationTree.loadConfig(filePath)
            else:
                self._configurationTree.loadConfig(configFile)
        else:
            self._configurationTree.loadConfig(self._playerConfiguration.getStartConfig())
        self._globalConfig = self._configurationTree.addChildUnique("Global")


        self.SetBackgroundColour((0,0,0)) #@UndefinedVariable
        self._wxImageBuffer = wx.EmptyImage(self._internalResolutionX, self._internalResolutionY)
        self._imagePosX = 0
        self._imagePosY = 0
        self.SetDoubleBuffered(True)
        self._onSize(None)

        self._midiTiming = MidiTiming()
        self._midiStateHolder = MidiStateHolder()
        self._specialModulationHolder = SpecialModulationHolder()


        self._timeModulationConfiguration = TimeModulationTemplates(self._globalConfig, self._midiTiming, self._specialModulationHolder)
        self._effectsConfiguration = EffectTemplates(self._globalConfig, self._midiTiming, self._specialModulationHolder, self._internalResolutionX, self._internalResolutionY)
        self._mediaFadeConfiguration = FadeTemplates(self._globalConfig, self._midiTiming, self._specialModulationHolder)
        self._effectImagesConfiguration = EffectImageList(self._globalConfig, self._midiTiming, self._playerConfiguration.getVideoDir())

        confChild = self._configurationTree.addChildUnique("MediaMixer")
        self._mediaMixer = MediaMixer(confChild, self._midiStateHolder, self._specialModulationHolder,
                                      self._effectsConfiguration, self._effectImagesConfiguration,
                                      self._internalResolutionX, self._internalResolutionY)
        confChild = self._configurationTree.addChildUnique("MediaPool")
        self._mediaPool = MediaPool(self._midiTiming, self._midiStateHolder, self._specialModulationHolder,
                                    self._mediaMixer, self._timeModulationConfiguration,
                                    self._effectsConfiguration, self._effectImagesConfiguration,
                                    self._mediaFadeConfiguration, confChild, self._internalResolutionX,
                                    self._internalResolutionY, self._playerConfiguration.getVideoDir())

        self._midiListner = TcpMidiListner(self._midiTiming, self._midiStateHolder, self._multiprocessLogger, self._configLoadCallback)
        self._midiListner.startDaemon(self._playerConfiguration.getMidiServerAddress(), self._playerConfiguration.getMidiServerPort(), self._playerConfiguration.getMidiServerUsesBroadcast())

        self._timingThreshold = 2.0/60
        self._lastDelta = -1.0

        self._configCheckEveryNRound = 60 * 5 #Every 5th second
        self._configCheckCounter = 0

        self._guiServer = GuiServer(self._configurationTree, self._playerConfiguration, self._mediaPool, self._midiStateHolder)
        self._guiServer.startGuiServerProcess(self._playerConfiguration.getWebServerAddress(), self._playerConfiguration.getWebServerPort(), None)
        startNote = self._playerConfiguration.getStartNoteNumber()
        if((startNote > -1) and (startNote < 128)):
            self._midiStateHolder.noteOn(0, startNote, 0x40, (True, 0.0))
            self._midiStateHolder.noteOff(0, startNote, 0x40, (True, 0.000000001))

        self._guiProcess = None
        if(launchGUI == True):
            print "*-*-*-" * 30
            print "Start GUI process!"
            self._startGUIProcess()
            print "*-*-*-" * 30

#        print self._configurationTree.getConfigurationXMLString()
        self._updateTimer = wx.Timer(self, -1) #@UndefinedVariable
        self._updateTimer.Start(1000 / 60)#30 times a second
        self.Bind(wx.EVT_TIMER, self._frameUpdate, id=self._updateTimer.GetId()) #@UndefinedVariable
        self.Bind(wx.EVT_PAINT, self._onPaint) #@UndefinedVariable
        self.Bind(wx.EVT_SIZE, self._onSize) #@UndefinedVariable
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda evt: None)
        self.Bind(wx.EVT_CLOSE, self._onWindowClose) #@UndefinedVariable
        self._ctrlDown = False
        self.Bind(wx.EVT_KEY_DOWN, self._onKeyPress) #@UndefinedVariable
        self.Bind(wx.EVT_KEY_UP, self._onKeyRelease) #@UndefinedVariable

    def _getConfiguration(self):
        pass

    def _configLoadCallback(self, programName):
        if(programName != ""):
            activeConfigName = self._configurationTree.getCurrentFileName()
            if(activeConfigName != programName):
                #Find config...
                print "-" * 120
                print "DEBUG pcn: _configLoadCallback loading: " + str(programName)
                print "-" * 120
                filePath = os.path.join(self._playerConfiguration.getConfigDir(), programName)
                self._configurationTree.loadConfig(filePath)
                self._configCheckCounter = self._configCheckEveryNRound + 1

    def checkAndUpdateFromConfiguration(self):
        if(self._configCheckCounter >= self._configCheckEveryNRound):
            if(self._configurationTree.isConfigurationUpdated()):
                print "*" * 120
                print "config is updated..."
                print "*" * 120
                self._getConfiguration()
                self._timeModulationConfiguration.checkAndUpdateFromConfiguration()
                self._effectsConfiguration.checkAndUpdateFromConfiguration()
                self._effectImagesConfiguration.checkAndUpdateFromConfiguration()
                self._mediaFadeConfiguration.checkAndUpdateFromConfiguration()
                self._mediaPool.checkAndUpdateFromConfiguration()
                self._mediaMixer.checkAndUpdateFromConfiguration()
                self._configurationTree.resetConfigurationUpdated()
                #TODO: autosave...
#                print "**********" * 10
#                print self._configurationTree.getConfigurationXMLString()
#                print "**********" * 10
            self._configCheckCounter = 0
        else:
            self._configCheckCounter += 1

    def _startGUIProcess(self):
        if(sys.platform != "darwin"):
            self._log.debug("Starting GUI Process")
            from configurationGui.GuiMainWindow import startGui
            self._commandQueue = Queue(10)
            self._statusQueue = Queue(-1)
            self._guiProcess = Process(target=startGui, args=(False, self._configDirArgument, self._commandQueue, self._statusQueue))
            self._guiProcess.name = "guiProcess"
            self._guiProcess.start()

    def _checkStatusQueue(self):
        if(self._guiProcess != None):
            try:
                status = self._statusQueue.get_nowait()
                return status
            except:
                pass
            
    def _requestGuiProcessToStop(self):
        if(self._guiProcess != None):
            self._log.debug("Stopping GUI Process")
            self._commandQueue.put("QUIT")

    def hasGuiProcessProcessShutdownNicely(self):
        if(self._guiProcess == None):
            return True
        else:
            if(self._guiProcess.is_alive() == False):
                self._guiProcess = None
                return True
            return False

    def forceGuiProcessProcessToStop(self):
        if(self._guiProcess != None):
            if(self._guiProcess.is_alive()):
                print "GUI Process did not respond to quit command. Terminating."
                self._guiProcess.terminate()
        self._guiProcess = None

    def _onSize(self, event):
        bufferSize  = self.ClientSize
        print "DEBUG bufferSize: " + str(bufferSize)
        bufferSizeX, bufferSizeY = bufferSize
        self._imagePosX = (bufferSizeX - self._internalResolutionX) / 2
        self._imagePosY = (bufferSizeY - self._internalResolutionY) / 2
        self._paintBuffer = wx.EmptyBitmap(*bufferSize)
        self._updateBuffer()

    def _onPaint(self, event):
        dc = wx.BufferedPaintDC(self, self._paintBuffer)

    def _updateBuffer(self):
        drawContext = wx.MemoryDC()
        drawContext.SelectObject(self._paintBuffer)
        self._showFrame(drawContext)
        del drawContext
        self.Refresh()
        self.Update()

    def _showFrame(self, drawContext):
        drawContext.SetBackground(wx.Brush((0,0,0)))
        drawContext.Clear()
        drawContext.DrawBitmap(wx.BitmapFromImage(self._wxImageBuffer), self._imagePosX, self._imagePosY)

    def _onKeyPress(self, event):
        keyCode = event.GetKeyCode()
        if(keyCode == 308): #Ctrl.
            self._ctrlDown = True
        elif(keyCode == 27): #ESC
            print "User has pressed ESC!"
            self._stopPlayer()
        elif((self._ctrlDown == True) and (keyCode == 81)): #ctrl q
            print "User has pressed CTRL-Q!"
            self._stopPlayer()
        elif((self._ctrlDown == True) and (keyCode == 67)): #ctrl c
            print "User has pressed CTRL-C!"
            self._stopPlayer()
        else:
            if(self._ctrlDown == True):
                print "DEBUG key pressed: ctrl + " + str(keyCode)
            else:
                print "DEBUG key pressed: " + str(keyCode)

    def _onKeyRelease(self, event):
        keyCode = event.GetKeyCode()
        if(keyCode == 308): #Ctrl.
            self._ctrlDown = False

    def _onWindowClose(self, event = None):
        print "User has closed window!"
        self._stopPlayer()

    def _stopPlayer(self):
        print "Closeing applicaton"
        if(self._fullscreenMode == True):
            self.ShowFullScreen(False, style=0)
        self._updateTimer.Stop()

        self._guiServer.requestGuiServerProcessToStop()
        self._midiListner.requestTcpMidiListnerProcessToStop()
        self._requestGuiProcessToStop()

        self._shutdownTimer = wx.Timer(self, -1) #@UndefinedVariable
        self._shutdownTimer.Start(100)#10 times a second
        self.Bind(wx.EVT_TIMER, self._onShutdownTimer, id=self._shutdownTimer.GetId()) #@UndefinedVariable
        self._shutdownTimerCounter = 0

    def _onShutdownTimer(self, event):
        allDone = False
        if(self._guiServer.hasGuiServerProcessShutdownNicely()):
            if(self._midiListner.hasTcpMidiListnerProcessToShutdownNicely()):
                if(self.hasGuiProcessProcessShutdownNicely()):
                    print "All done. (shutdown timer counter: " + str(self._shutdownTimerCounter) + " )"
                    allDone = True
        else:
            self._shutdownTimerCounter += 1
            if(self._shutdownTimerCounter > 200):
                print "Shutdown timeout!!! Force killing rest..."
                if(self._guiServer.hasGuiServerProcessShutdownNicely() != False):
                    self._guiServer.forceGuiServerProcessToStop()
                if(self._midiListner.hasTcpMidiListnerProcessToShutdownNicely() != False):
                    self._midiListner.forceTcpMidiListnerProcessToStop()
                if(self.hasGuiProcessProcessShutdownNicely() != False):
                    self.forceGuiProcessProcessToStop()
                allDone = True
        if(allDone == True):
            if(sys.platform != "darwin"):
                self.Destroy()
            wx.Exit() #@UndefinedVariable
            if((self._fullscreenMode == True) and (sys.platform != "darwin")):
                applicationHolder.Exit()
                sys.exit()
            print "Closeing done."

    def _frameUpdate(self, event = None):
#            if (dt > self._timingThreshold):
#                self._log.info("Too slow main schedule " + str(dt))
        #Prepare frame
        timeStamp = time.time()
        self._midiListner.getData(False)
        self._mediaPool.updateVideo(timeStamp)
        self._multiprocessLogger.handleQueuedLoggs()
        self.checkAndUpdateFromConfiguration()
        updateConfig = self._guiServer.processGuiRequests()
        if(updateConfig == True):
            self._configCheckCounter = self._configCheckEveryNRound + 1

        #Show frame:
        mixedImage = self._mediaMixer.getImage()
        self._wxImageBuffer.SetData(mixedImage.tostring())
        self._updateBuffer()
#        self._frameWidget.SetBitmap(wx.BitmapFromImage(self._wxImageBuffer))

        #Check for quit conditions...
        guiStatus = self._checkStatusQueue()
        if(guiStatus == "QUIT"):
            print "User has closed GUI window."
            self._stopPlayer()

        #Sleep until next frame is needed...
#        self._pygameClock.tick(60)

#            timeUsed = time.time() - timeStamp
#            if((timeUsed / self._lastDelta) > 0.9):
#                print "PCN time: " + str(timeUsed) + " last delta: " + str(self._lastDelta)
#            self._lastDelta = dt

class QuitRequestException(Exception):
    def __init__(self, value):
        self.value = value.encode("utf-8")

    def __str__(self):
        return repr(self.value)

if __name__ in ('__android__', '__main__'):
    multiprocessing.freeze_support()

    launchGUI = True
    debugMode = False
    checkForMoreConfigFileName = False
    checkForMoreConfigDirName = False
    configDir = ""
    configFile = ""
    for i in range(len(sys.argv) - 1):
        if(sys.argv[i+1].lower() == "--nogui"):
            launchGUI = False
            checkForMoreConfigDirName = False
            checkForMoreConfigFileName = False
        elif(sys.argv[i+1].lower() == "--debug"):
            debugMode = True
            checkForMoreConfigDirName = False
            checkForMoreConfigFileName = False
        elif(sys.argv[i+1].startswith("--configDir=")):
            checkForMoreConfigDirName = True
            checkForMoreConfigFileName = False
            configDir = sys.argv[i+1][12:]
        elif(sys.argv[i+1].startswith("--configFile=")):
            checkForMoreConfigDirName = False
            checkForMoreConfigFileName = True
            configFile = sys.argv[i+1][13:]
        else:
            if(checkForMoreConfigDirName == True):
                configDir += " " + sys.argv[i+1]
            if(checkForMoreConfigFileName == True):
                configFile += " " + sys.argv[i+1]
    if(sys.platform == "win32"):
        from win32api import GetCurrentProcessId, OpenProcess #@UnresolvedImport
        import win32process
        import win32con
        #Incerase priority
        pid = GetCurrentProcessId()
        handle = OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
        win32process.SetPriorityClass(handle, win32process.HIGH_PRIORITY_CLASS)
#    else:
#        print "do os nice thing???"

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
        launchGUI = False
    applicationHolder = wx.App(redirect = redirectValue, filename = logFileName) #@UndefinedVariable
    gui = PlayerMain(None, configDir, configFile, title="Takt Player")
    try:
        applicationHolder.MainLoop()
#    except QuitRequestException, quitRequest:
#        app.Exit()
    except:
        gui._stopPlayer()
        raise

