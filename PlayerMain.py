'''
Created on 28. nov. 2011

@author: pcn
'''

#Imports
from configuration.EffectSettings import EffectTemplates, FadeTemplates, EffectImageList,\
    TimeModulationTemplates
from configuration.GuiServer import GuiServer
import traceback
import multiprocessing
from multiprocessing import Process, Queue
from configuration.ConfigurationHolder import getDefaultDirectories
from configuration.PlayerConfiguration import PlayerConfiguration
from taktVersion import getVersionNumberString, getVersionDateString,\
    getVersionGitIdString

import wx

#pcn stuff
from configuration.ConfigurationHolder import ConfigurationHolder

from video.media.MediaMixer import MediaMixer
from video.media.MediaPool import MediaPool

#from video.media.MediaFile import createCvWindow, showCvImage, hasCvWindowStoped, addCvMouseCallback

from midi.MidiTiming import MidiTiming
from midi.TcpMidiListner import TcpMidiListner, RenderFileReader
from midi.MidiStateHolder import MidiStateHolder, SpecialModulationHolder

#Python standard
import time
import signal
import sys
import shutil
import os
from dmx.DmxListner import DmxListner

APP_NAME = "TaktPlayer"
launchGUI = True
applicationHolder = None

class PlayerMain(wx.Frame):
    def __init__(self, parent, configDir, configFile, debugMode, eventlogFileName, renderConfig, title):
        super(PlayerMain, self).__init__(parent, title=title, size=(800, 600))
        self._debugModeOn = debugMode
        self._configDirArgument = configDir
        self._baseTitle = title
        self._eventlogFileName = eventlogFileName
        renderModeOn, renderFileName, renderOutputFile, renderFrameRate = renderConfig
        self._renderMode = renderModeOn
        self._renderFileName = renderFileName
        self._renderOutputFile = renderOutputFile
        self._renderFrameRate = renderFrameRate

        if(os.path.isfile("graphics/TaktPlayer.ico")):
            wxIcon = wx.Icon(os.path.normpath("graphics/TaktPlayer.ico"), wx.BITMAP_TYPE_ICO) #@UndefinedVariable
            self.SetIcon(wxIcon)
        elif(os.path.isfile("TaktPlayer.ico")):
            wxIcon = wx.Icon(os.path.normpath("TaktPlayer.ico"), wx.BITMAP_TYPE_ICO) #@UndefinedVariable
            self.SetIcon(wxIcon)

        screenWidth = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
        screenHeight = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
        print "DEBUG screensize: " + str((screenWidth, screenHeight))

        self._playerConfiguration = PlayerConfiguration(configDir)
        if(sys.platform == "darwin"):
            self._wiggleMouse = False
        else:
            self._wiggleMouse = self._playerConfiguration.isAvoidScreensaverEnabled()
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
            if(configFullscreenmode != "auto"):
                if((configPositionX >= 0) and (configPositionY >= 0)):
                    self.SetPosition((configPositionX, configPositionY))
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
        else:
            filePath = os.path.join(self._playerConfiguration.getConfigDir(), self._playerConfiguration.getStartConfig())
        self._configurationTree.loadConfig(filePath)
        self._globalConfig = self._configurationTree.addChildUnique("Global")


        self.SetBackgroundColour((0,0,0)) #@UndefinedVariable
        self._wxImageBuffer = wx.EmptyImage(self._internalResolutionX, self._internalResolutionY)
        self._imagePosX = 0
        self._imagePosY = 0
        self.SetDoubleBuffered(True)
        self._onSize(None)

        self._midiTiming = MidiTiming()
        self._midiStateHolder = MidiStateHolder(self._playerConfiguration.getDmxSettings())
        self._specialModulationHolder = SpecialModulationHolder()


        self._timeModulationConfiguration = TimeModulationTemplates(self._globalConfig, self._midiTiming, self._specialModulationHolder)
        self._effectsConfiguration = EffectTemplates(self._globalConfig, self._midiTiming, self._specialModulationHolder, self._internalResolutionX, self._internalResolutionY)
        self._mediaFadeConfiguration = FadeTemplates(self._globalConfig, self._midiTiming, self._specialModulationHolder)
        self._effectImagesConfiguration = EffectImageList(self._globalConfig, self._midiTiming, self._playerConfiguration.getVideoDir())

        confChild = self._configurationTree.addChildUnique("MediaMixer")
        self._mediaMixer = MediaMixer(confChild, self._midiStateHolder, self._specialModulationHolder,
                                      self._effectsConfiguration, self._effectImagesConfiguration,
                                      self._mediaFadeConfiguration,
                                      self._internalResolutionX, self._internalResolutionY,
                                      self._playerConfiguration.getAppDataDirectory())
        confChild = self._configurationTree.addChildUnique("MediaPool")
        self._mediaPool = MediaPool(self._midiTiming, self._midiStateHolder, self._specialModulationHolder,
                                    self._mediaMixer, self._timeModulationConfiguration,
                                    self._effectsConfiguration, self._effectImagesConfiguration,
                                    self._mediaFadeConfiguration, confChild, self._internalResolutionX,
                                    self._internalResolutionY, self._playerConfiguration.getVideoDir(),
                                    self._playerConfiguration.getAppDataDirectory())

        self._configCheckEveryNRound = 60 * 5 #Every 5th second
        self._configCheckCounter = 0

        self._eventlogFileHandle = None
        self._eventLogSaveQueue = None
        if(self._renderMode == True):
            self._midiListner = RenderFileReader(self._midiTiming, self._midiStateHolder, self._configLoadCallback)
            self._dmxListner = None
            #TODO: add DMX rendrer
        else:
            try:
                filePath = os.path.normpath(self._eventlogFileName)
                self._eventlogFileHandle = open(filePath, 'w')
            except:
                pass
            if(self._eventlogFileHandle != None):
                self._eventLogSaveQueue = Queue(4096)
            self._midiListner = TcpMidiListner(self._midiTiming, self._midiStateHolder, self._configLoadCallback, self._eventLogSaveQueue)
            self._midiListner.startDaemon(self._playerConfiguration.getMidiServerAddress(), self._playerConfiguration.getMidiServerPort(), self._playerConfiguration.getMidiServerUsesBroadcast())
            self._dmxListner = DmxListner(self._midiTiming, self._midiStateHolder, self._configLoadCallback, self._eventLogSaveQueue)
            self._dmxListner.startDaemon(self._playerConfiguration.getDmxSettings())

        self._timingThreshold = 2.0/60
        self._lastDelta = -1.0

        self._guiProcess = None
        self._guiServer =None
        if(self._renderMode == False):
            self._guiServer = GuiServer(self._configurationTree, self._playerConfiguration, self._mediaPool, self._midiStateHolder, self._eventLogSaveQueue)
            self._guiServer.startGuiServerProcess(self._playerConfiguration.getWebServerAddress(), self._playerConfiguration.getWebServerPort(), None)
            startNote = self._playerConfiguration.getStartNoteNumber()
            if((startNote > -1) and (startNote < 128)):
                self._midiStateHolder.noteOn(0, startNote, 0x40, (True, 0.0))
                self._midiStateHolder.noteOff(0, startNote, 0x40, (True, 0.000000001))

            if(launchGUI == True):
                print "*-*-*-" * 30
                print "Start GUI process!"
                self._startGUIProcess()
                print "*-*-*-" * 30

#        print self._configurationTree.getConfigurationXMLString()
        self._updateTimer = wx.Timer(self, -1) #@UndefinedVariable
        self._updateTimer.Start(1000 / 60)#30 times a second
        if(self._renderMode == False):
            self.Bind(wx.EVT_TIMER, self._frameUpdate, id=self._updateTimer.GetId()) #@UndefinedVariable
        else:
            self._renderTime  = None
            self._renderDelta = None
            self.Bind(wx.EVT_TIMER, self._renderFile, id=self._updateTimer.GetId()) #@UndefinedVariable
        self.Bind(wx.EVT_PAINT, self._onPaint) #@UndefinedVariable
        self.Bind(wx.EVT_SIZE, self._onSize) #@UndefinedVariable
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda evt: None)
        self.Bind(wx.EVT_CLOSE, self._onWindowClose) #@UndefinedVariable
        self._cmdDown = False
        self._ctrlDown = False
        self._altDown = False
        self._shiftDown = False
        self.Bind(wx.EVT_KEY_DOWN, self._onKeyPress) #@UndefinedVariable
        self.Bind(wx.EVT_KEY_UP, self._onKeyRelease) #@UndefinedVariable
        self._outOfMemory = False

    def _getConfiguration(self):
        pass

    def _updateTitle(self, message = None):
        if(message == None):
            self.SetTitle(self._baseTitle)
        else:
            self.SetTitle(self._baseTitle + "   *** " + message + " ***")


    def _configLoadCallback(self, programName, configString = None):
        if(configString != None):
            if(configString != ""):
                self._configurationTree.setFromXmlString(configString)
                self._configCheckCounter = self._configCheckEveryNRound + 1
                self.checkAndUpdateFromConfiguration()
        elif(programName != ""):
            activeConfigName = self._configurationTree.getCurrentFileName()
            isConfigNotSaved = self._configurationTree.isConfigNotSaved()
            if(isConfigNotSaved or (activeConfigName != programName)):
                #Find config...
                print "-" * 120
                print "DEBUG pcn: _configLoadCallback loading: " + str(programName)
                print "-" * 120
                filePath = os.path.join(self._playerConfiguration.getConfigDir(), programName)
                self._configurationTree.loadConfig(filePath)
                self._configCheckCounter = self._configCheckEveryNRound + 1
                return self._configurationTree.getLoadedXMLString()

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
                self._timeModulationConfiguration.doPostConfigurations()
                self._effectsConfiguration.doPostConfigurations()
                self._mediaFadeConfiguration.doPostConfigurations()
                self._configurationTree.resetConfigurationUpdated()
            self._configCheckCounter = 0
        else:
            self._configCheckCounter += 1

    def _startGUIProcess(self):
        if(sys.platform != "darwin"):
            print("Starting GUI Process")
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
            print("Stopping GUI Process")
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
        showWindowTitle = True
        if(self.IsTopLevel() == True):
            if(self.IsMaximized() == True):
                print "MAXIMIZED " *12
                showWindowTitle = False
            elif(self.IsFullScreen() == True):
                print "FULLSCREEN " *12
#                showWindowTitle = False
        if(showWindowTitle == True):
            self.SetWindowStyle(wx.DEFAULT_FRAME_STYLE)
        else:
            self.SetWindowStyle(wx.FRAME_NO_TASKBAR)
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
        toggleFullscreen = False
        keyCode = event.GetKeyCode()
        if(keyCode == 396): #Cmd.
            self._cmdDown = True
        elif(keyCode == 308): #Ctrl.
            self._ctrlDown = True
        elif(keyCode == 307): #Alt.
            self._altDown = True
        elif(keyCode == 306): #Shift.
            self._shiftDown = True
        elif(keyCode == 27): #ESC
            print "User has pressed ESC!"
            self._stopPlayer()
        elif((self._altDown == True) and (keyCode == 81)): #alt q
            if(sys.platform != "darwin"):
                print "User has pressed ALT-Q!"
                self._stopPlayer()
        elif((self._ctrlDown == True) and (keyCode == 81)): #ctrl q
            print "User has pressed CTRL-Q!"
            self._stopPlayer()
        elif((self._cmdDown == True) and (keyCode == 81)): #cmd q
            print "User has pressed CMD-Q!"
            self._stopPlayer()
        elif((self._ctrlDown == True) and (keyCode == 67)): #ctrl c
            print "User has pressed CTRL-C!"
            self._stopPlayer()
        elif((self._altDown == True) and (keyCode == 13)): #alt enter
            if(sys.platform != "darwin"):
                print "User has pressed ALT-ENTER!"
                toggleFullscreen = True
        elif((self._altDown == True) and (keyCode == 13)): #alt enter
            if(sys.platform != "darwin"):
                print "User has pressed ALT-ENTER!"
                toggleFullscreen = True
        elif((self._shiftDown == True) and (self._cmdDown == True) and (keyCode == 70)): #shift cmd f
            if(sys.platform == "darwin"):
                print "User has pressed SHIFT-CMD-F!"
                toggleFullscreen = True
        else:
            if(self._cmdDown == True):
                print "DEBUG key pressed: cmd + " + str(keyCode)
            elif(self._ctrlDown == True):
                print "DEBUG key pressed: ctrl + " + str(keyCode)
            elif(self._altDown == True):
                print "DEBUG key pressed: alt + " + str(keyCode)
            elif(self._shiftDown == True):
                print "DEBUG key pressed: shift + " + str(keyCode)
            else:
                print "DEBUG key pressed: " + str(keyCode)
        if(toggleFullscreen == True):
            maximize = True
            fullScreenMode = True
            configFullscreenmode = self._playerConfiguration.getFullscreenMode().lower()
            if(configFullscreenmode == "off"):
                fullScreenMode = False
            if(self.IsTopLevel() == True):
                if(self.IsMaximized() == True):
                    maximize = False
                elif(self.IsFullScreen() == True):
                    maximize = False
            if(fullScreenMode == False):
                if(maximize == True):
                    self.Maximize(True)
                else:
                    self.Restore()
            else:
                if(maximize == True):
                    self.ShowFullScreen(True, style=wx.FULLSCREEN_ALL)
                else:
                    self.ShowFullScreen(False, style=wx.FULLSCREEN_ALL)

    def _onKeyRelease(self, event):
        keyCode = event.GetKeyCode()
        if(keyCode == 396): #Cmd.
            self._cmdDown = False
        elif(keyCode == 308): #Ctrl.
            self._ctrlDown = False
        elif(keyCode == 307): #Alt.
            self._altDown = False
        elif(keyCode == 306): #Shift.
            self._shiftDown = False

    def _onWindowClose(self, event = None):
        print "User has closed window!"
        self._stopPlayer()

    def _stopPlayer(self):
        print "Closeing applicaton"
        if(self._fullscreenMode == True):
            self.ShowFullScreen(False, style=0)

        if(self._renderMode != True):
            self._updateTimer.Stop()

        if(self._eventlogFileHandle != None):
            self._eventlogFileHandle.close()

        try:
            if(self._guiServer != None):
                self._guiServer.requestGuiServerProcessToStop()
            if(self._midiListner != None):
                self._midiListner.requestTcpMidiListnerProcessToStop()
            if(self._dmxListner != None):
                self._dmxListner.requestDmxListnerProcessToStop()
            self._requestGuiProcessToStop()

            self._shutdownTimer = wx.Timer(self, -1) #@UndefinedVariable
            self._shutdownTimer.Start(100)#10 times a second
            self.Bind(wx.EVT_TIMER, self._onShutdownTimer, id=self._shutdownTimer.GetId()) #@UndefinedVariable
            self._shutdownTimerCounter = 0
        except:
            traceback.print_exc()
            self._shutdownTimerCounter = 1000
            self._onShutdownTimer(None)

    def _onShutdownTimer(self, event):
        allDone = False
        if(self._shutdownTimerCounter >= 1000):
            if(self._guiServer != None):
                self._guiServer.forceGuiServerProcessToStop()
            if(self._midiListner != None):
                self._midiListner.forceTcpMidiListnerProcessToStop()
            if(self._dmxListner != None):
                self._dmxListner.forceDmxListnerProcessToStop()
            self.forceGuiProcessProcessToStop()
            allDone = True
        else:
            if((self._guiServer == None) or (self._guiServer.hasGuiServerProcessShutdownNicely())):
                if((self._midiListner == None) or (self._midiListner.hasTcpMidiListnerProcessToShutdownNicely())):
                    if((self._dmxListner == None) or (self._dmxListner.hasDmxListnerProcessToShutdownNicely())):
                        if(self.hasGuiProcessProcessShutdownNicely()):
                            print "All done. (shutdown timer counter: " + str(self._shutdownTimerCounter) + " )"
                            allDone = True
            if(allDone == False):
                self._shutdownTimerCounter += 1
                if(self._shutdownTimerCounter > 200):
                    print "Shutdown timeout!!! Force killing rest..."
                    if((self._guiServer != None) and (self._guiServer.hasGuiServerProcessShutdownNicely() == False)):
                        self._guiServer.forceGuiServerProcessToStop()
                    if((self._midiListner != None) and (self._midiListner.hasTcpMidiListnerProcessToShutdownNicely() == False)):
                        self._midiListner.forceTcpMidiListnerProcessToStop()
                    if((self._dmxListner == None) and (self._dmxListner.hasDmxListnerProcessToShutdownNicely())):
                        self._dmxListner.forceDmxListnerProcessToStop()
                    if(self.hasGuiProcessProcessShutdownNicely() == False):
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

    def _showErrorDialog(self, text, title):
        print text
        dlg = wx.MessageDialog(self, text, title, wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _openRenderFile(self):
        fileOk = False
        if(self._renderFileName != ""):
            testFile = self._renderFileName
            if(os.path.isfile(os.path.normpath(testFile)) == False):
                testFile = os.path.join(self._playerConfiguration.getAppDataDirectory(), os.path.basename(testFile))
            if(os.path.isfile(os.path.normpath(testFile)) == False):
                testFile = os.path.join(self._playerConfiguration.getVideoDir(), os.path.basename(testFile))
            if(os.path.isfile(os.path.normpath(testFile)) == True):
                fileOk = True
            self._renderFileName = testFile
        if(fileOk == False):
            dlg = wx.FileDialog(self, "Choose an eventlog file to render:", self._playerConfiguration.getConfigDir(), "TaktPlayer.eventlog", "*.*", wx.OPEN) #@UndefinedVariable
            if dlg.ShowModal() == wx.ID_OK: #@UndefinedVariable
                self._renderFileName = os.path.normpath(dlg.GetPath())
            else:
                self._stopPlayer()
                return True
            if(os.path.isfile(os.path.normpath(self._renderFileName)) == True):
                fileOk = True
        if(fileOk == True):
            self._midiListner.openFile(self._renderFileName)
            return False
        else:
            errorText = "Error! Could not find input file: " + str(os.path.basename(self._renderFileName)) + "\n"
            self._showErrorDialog(errorText, "Input file error!")
            self._stopPlayer()
            return True

    def _renderFile(self, event):
        if(self._renderTime == None):
            if(self._renderDelta != None):
                self._updateBuffer()
                return
            self._renderDelta = 1.0
            if(self._openRenderFile() == True):
                return
            if(self._midiListner.endIsReached() == True):
                errorText = "Error! Could not find the starting point in input file: " + str(os.path.basename(self._renderFileName)) + "\n"
                errorText += "Please add StartRecording tag in event file.\n"
                errorText += "1358807809.39|StartRecording|Kosmodrom\n"
                self._showErrorDialog(errorText, "Input error!")
                self._stopPlayer()
                return
            startTime = self._midiListner.getStartTime()
            self._renderFrameRate = max(min(self._renderFrameRate, 1000), 1)
            self._renderDelta = 1.0/self._renderFrameRate
            print "DEBUG pcn: framerate: " + str(self._renderFrameRate)
            if(self._renderOutputFile != ""):
                if(os.path.isabs(self._renderOutputFile) == False):
                    videoDir = self._playerConfiguration.getVideoDir()
                    self._renderOutputFile = os.path.normpath(os.path.join(videoDir, self._renderOutputFile))
            else:
                self._renderOutputFile = self._midiListner.getOutputFileName()
                videoDir = self._playerConfiguration.getVideoDir()
                self._renderOutputFile = os.path.normpath(os.path.join(videoDir, self._renderOutputFile))
            if(self._renderOutputFile.endswith(".avi") == False):
                self._renderOutputFile = self._renderOutputFile + ".avi"
            if(os.path.isfile(self._renderOutputFile)):
                print "File \"" + self._renderOutputFile + "\" already exists.\n\nDo you want to overwrite?"
                dlg = wx.MessageDialog(self, "File \"" + self._renderOutputFile + "\" already exists.\n\nDo you want to overwrite?", 'Overwrite?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                dlg.Destroy()
                if(result == True):
                    os.remove(self._renderOutputFile)
                    if(os.path.isfile(self._renderOutputFile)):
                        errorText = "Error! Could not delete old file aborting... Is file: \"" + self._renderOutputFile + "\" in use?"
                        self._showErrorDialog(errorText, "Delete error!")
                        self._stopPlayer()
                        return
                else:
                    errorText = "Rendering aborted by user. Chose a different output name or move: \"" + self._renderOutputFile + "\""
                    self._showErrorDialog(errorText, "Aborted!")
                    self._stopPlayer()
                    return
            self._updateTitle("Rendering: " + str(self._renderOutputFile))
            print "*"*120
            print "Rendering: " + str(self._renderOutputFile)
            print "*"*120
            self._mediaMixer.setupVideoWriter(self._renderOutputFile, self._renderFrameRate)
            self._renderTime = startTime
        sleepCount = 0
        while(self._midiListner.endIsReached() == False):
            self._midiListner.getData(self._renderTime)
            self._mediaPool.updateVideo(self._renderTime)
            mixedImage = self._mediaMixer.getImage(self._outOfMemory)
            self._mediaMixer.writeImage()
            self._wxImageBuffer.SetData(mixedImage.tostring())
            self._updateBuffer()
            self._renderTime += self._renderDelta
            sleepCount += 1
            if(sleepCount > self._renderFrameRate):
                print "S"
                return
        self._renderTime = None
        self._stopPlayer()

    def _frameUpdate(self, event = None):
#            if (dt > self._timingThreshold):
#                print("Too slow main schedule " + str(dt))
        #Prepare frame
        timeStamp = time.time()
        gotMidiNote = self._midiListner.getData(False)
        gotDmxNote = self._dmxListner.getData()
        if((gotMidiNote == True) and (self._wiggleMouse == True)):
#            print "DEBUG pcn: wiggle wiggle"
            mousePos = wx.GetMousePosition()
            screenPos = self.ClientToScreen((0,0))
            self.WarpPointer(mousePos[0] - screenPos[0], mousePos[1] - screenPos[1])
        self._mediaPool.updateVideo(timeStamp)
        self.checkAndUpdateFromConfiguration()
        updateConfig = self._guiServer.processGuiRequests()
        if(updateConfig == True):
            self._configCheckCounter = self._configCheckEveryNRound + 1

        #Show frame:
        mixedImage = self._mediaMixer.getImage(self._outOfMemory)
        try:
            self._wxImageBuffer.SetData(mixedImage.tostring())
            self._updateBuffer()
            if(self._outOfMemory == True):
                self._updateTitle(None)
                self._outOfMemory = False
        except MemoryError:
            self._updateTitle("Out of memory error!")
            self._outOfMemory = True

        if(self._eventLogSaveQueue != None):
            saveLines = ""
            gotNewLines = False
            try:
                while(True):
                    saveLines += self._eventLogSaveQueue.get_nowait()
                    gotNewLines = True
            except:
                pass
            if(gotNewLines == True):
                self._eventlogFileHandle.write(saveLines)

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

    helpMode = False
    launchGUI = True
    debugMode = False
    raisePriority = True
    guiOnlyMode = False
    checkForMoreConfigFileName = False
    checkForMoreConfigDirName = False
    checkForMoreEventFileName = False
    checkForMoreRenderOutputFileName = False
    configDir = ""
    configFile = ""
    renderConfig = [False, "", "", 60]
    for i in range(len(sys.argv) - 1):
        if(sys.argv[i+1].lower() == "--help"):
            if(sys.platform == "darwin"):
                print os.path.basename(sys.argv[0]) + " --help --debug --configDir=DIR_NAME --configFile=FILE_NAME"
                print "\t--help\t\t\t\tPrint this text and exit"
                print "\t--debug\t\t\t\tPrints debug info to console and not to logfile"
                print "\t--configDir=DIR_NAME\t\tSet config file to start with"
                print "\t--configFile=FILE_NAME\t\tSet configuration directory"
                print "\t--renderMode\t\t\tTurns on render mode"
                print "\t--renderFile=FILE_NAME\t\tSet the event file to render if in render mode."
                print "\t--renderOutputFile=FILE_NAME\tName of the output video file in render mode."
                print "\t--renderFrameRate=FPS\t\tSet the number of frames per second in render mode."
            else:
                print os.path.basename(sys.argv[0]) + " --help --debug --normalpriority --nogui --guionly --configDir=DIR_NAME --configFile=FILE_NAME"
                print "\t--help\t\t\t\tPrint this text and exit"
                print "\t--debug\t\t\t\tPrints debug info to console and not to logfile"
                print "\t--normalpriority\t\tDon't raise priority"
                print "\t--nogui\t\t\t\tRun without GUI (always on mac)"
                print "\t--guionly\t\t\tRun without Player (not on mac)"
                print "\t--configDir=DIR_NAME\t\tSet config file to start with"
                print "\t--configFile=FILE_NAME\t\tSet configuration directory"
                print "\t--renderMode\t\t\tTurns on render mode"
                print "\t--renderFile=FILE_NAME\t\tSet the event file to render if in render mode."
                print "\t--renderOutputFile=FILE_NAME\tName of the output video file in render mode."
                print "\t--renderFrameRate=FPS\t\tSet the number of frames per second in render mode."
            print ""
            print "    TaktPlayer version: " + getVersionNumberString()
            print "        Build date:\t" + getVersionDateString()
            print "        Build id:\t" + getVersionGitIdString()
            helpMode = True
            checkForMoreConfigDirName = False
            checkForMoreConfigFileName = False
            checkForMoreEventFileName = False
            checkForMoreRenderOutputFileName = False
        elif(sys.argv[i+1].lower() == "--nogui"):
            launchGUI = False
            checkForMoreConfigDirName = False
            checkForMoreConfigFileName = False
            checkForMoreEventFileName = False
            checkForMoreRenderOutputFileName = False
        elif(sys.argv[i+1].lower() == "--guionly"):
            guiOnlyMode = True
            checkForMoreConfigDirName = False
            checkForMoreConfigFileName = False
            checkForMoreEventFileName = False
            checkForMoreRenderOutputFileName = False
        elif(sys.argv[i+1].lower() == "--debug"):
            debugMode = True
            checkForMoreConfigDirName = False
            checkForMoreConfigFileName = False
            checkForMoreEventFileName = False
            checkForMoreRenderOutputFileName = False
        elif(sys.argv[i+1].lower() == "--normalpriority"):
            raisePriority = False
            checkForMoreConfigDirName = False
            checkForMoreConfigFileName = False
            checkForMoreEventFileName = False
            checkForMoreRenderOutputFileName = False
        elif(sys.argv[i+1].startswith("--configDir=")):
            checkForMoreConfigDirName = True
            checkForMoreConfigFileName = False
            checkForMoreEventFileName = False
            checkForMoreRenderOutputFileName = False
            configDir = sys.argv[i+1][12:]
        elif(sys.argv[i+1].startswith("--configFile=")):
            checkForMoreConfigDirName = False
            checkForMoreConfigFileName = True
            checkForMoreEventFileName = False
            checkForMoreRenderOutputFileName = False
            configFile = sys.argv[i+1][13:]
        elif(sys.argv[i+1].startswith("--renderMode")):
            renderConfig[0] = True
            checkForMoreConfigDirName = False
            checkForMoreConfigFileName = False
            checkForMoreEventFileName = False
            checkForMoreRenderOutputFileName = False
        elif(sys.argv[i+1].startswith("--renderFile=")):
            checkForMoreConfigDirName = False
            checkForMoreConfigFileName = False
            checkForMoreEventFileName = True
            checkForMoreRenderOutputFileName = False
            renderConfig[1] = sys.argv[i+1][13:]
        elif(sys.argv[i+1].startswith("--renderOutputFile=")):
            checkForMoreConfigDirName = False
            checkForMoreConfigFileName = False
            checkForMoreEventFileName = False
            checkForMoreRenderOutputFileName = True
            renderConfig[2] = sys.argv[i+1][19:]
        elif(sys.argv[i+1].startswith("--renderFrameRate=")):
            checkForMoreConfigDirName = False
            checkForMoreConfigFileName = False
            checkForMoreEventFileName = False
            checkForMoreRenderOutputFileName = False
            try:
                renderConfig[3] = int(sys.argv[i+1][18:])
            except:
                renderConfig[3] = 60
        else:
            if(checkForMoreConfigDirName == True):
                configDir += " " + sys.argv[i+1]
            if(checkForMoreConfigFileName == True):
                configFile += " " + sys.argv[i+1]
            if(checkForMoreEventFileName == True):
                renderConfig[1] += " " + sys.argv[i+1]
            if(checkForMoreRenderOutputFileName == True):
                renderConfig[2] += " " + sys.argv[i+1]
    if(raisePriority == True):
        if(sys.platform == "win32"):
            try:
                from win32api import GetCurrentProcessId, OpenProcess #@UnresolvedImport
                import win32process
                import win32con
                #Incerase priority
                pid = GetCurrentProcessId()
                handle = OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
                win32process.SetPriorityClass(handle, win32process.HIGH_PRIORITY_CLASS)
            except:
                pass
#    else:
#        print "do os nice thing???"

    if(helpMode != True):
        appDataDir, _ = getDefaultDirectories()
        logFileName = os.path.normpath(os.path.join(appDataDir, APP_NAME + ".log"))
        eventlogFileName = os.path.normpath(os.path.join(appDataDir, APP_NAME + ".eventlog"))
        if(debugMode == True):
            redirectValue = 0
        else:
            redirectValue = 1
            oldLogFileName = logFileName + ".old"
            if(os.path.isfile(logFileName)):
                try:
                    shutil.move(logFileName, oldLogFileName)
                except:
                    pass
        if(renderConfig[0] == False):
            oldLogFileName = eventlogFileName + ".old"
            if(os.path.isfile(eventlogFileName)):
                try:
                    shutil.move(eventlogFileName, oldLogFileName)
                except:
                    pass
        if(sys.platform == "darwin"):
            os.environ["PATH"] += ":."
            launchGUI = False
            guiOnlyMode = False
        if(guiOnlyMode == True):
            from configurationGui.GuiMainWindow import startGui
            startGui(debugMode, configDir)
        else:
            applicationHolder = wx.App(redirect = redirectValue, filename = logFileName) #@UndefinedVariable
            gui = PlayerMain(None, configDir, configFile, debugMode, eventlogFileName, renderConfig, title="Takt Player")
            try:
                applicationHolder.MainLoop()
            except:
                gui._stopPlayer()
                raise

