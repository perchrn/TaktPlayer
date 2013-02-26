'''
Created on 28. nov. 2011

@author: pcn
'''

#Imports
import traceback
import multiprocessing
from multiprocessing import Process, Queue

import wx

#pcn stuff
from configuration.ConfigurationHolder import ConfigurationHolder, \
    getDefaultDirectories
from taktVersion import getVersionNumberString, getVersionDateString,\
    getVersionGitIdString

from configuration.CameraServerConfiguration import CameraConfiguration
from configuration.CameraWebServer import CameraWebServer

from video.media.MediaFile import RawCamera
from video.Effects import MediaError

#Python standard
import time
import signal
import sys
import shutil
import os
from video.media.ImageMixer import CameraDisplayMixer

APP_NAME = "TaktCameraServer"
applicationHolder = None

class CameraMain(wx.Frame):
    def __init__(self, parent, configDir, configFile, debugMode, title):
        super(CameraMain, self).__init__(parent, title=title, size=(800, 600))
        self._debugModeOn = debugMode
        self._configDirArgument = configDir
        self._baseTitle = title

        if(os.path.isfile("graphics/TaktPlayer.ico")):
            wxIcon = wx.Icon(os.path.normpath("graphics/TaktPlayer.ico"), wx.BITMAP_TYPE_ICO) #@UndefinedVariable
            self.SetIcon(wxIcon)
        elif(os.path.isfile("TaktPlayer.ico")):
            wxIcon = wx.Icon(os.path.normpath("TaktPlayer.ico"), wx.BITMAP_TYPE_ICO) #@UndefinedVariable
            self.SetIcon(wxIcon)

        screenWidth = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
        screenHeight = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
        print "DEBUG screensize: " + str((screenWidth, screenHeight))

        self._cameraConfiguration = CameraConfiguration(configDir)
        if(sys.platform == "darwin"):
            self._wiggleMouse = False
        else:
            self._wiggleMouse = self._cameraConfiguration.isAvoidScreensaverEnabled()
        configFullscreenmode = self._cameraConfiguration.getFullscreenMode().lower()
        configResolution = self._cameraConfiguration.getResolution()
        configPositionX, configPositionY = self._cameraConfiguration.getPosition()
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


        self.SetBackgroundColour((0,0,0)) #@UndefinedVariable
        self._wxImageBuffer = wx.EmptyImage(self._internalResolutionX, self._internalResolutionY)
        self._imagePosX = 0
        self._imagePosY = 0
        self.SetDoubleBuffered(True)
        self._onSize(None)

        self._cameraServer = CameraWebServer(self._cameraConfiguration)
        self._cameraServer.startCameraWebServerProcess()

        self._cameraList = []
        self._imageList = []
        stop = False
        cameraId = 0
        maxCameras = self._cameraConfiguration.getMaxCameras()
        while(stop == False):
            try:
                cameraMedia = RawCamera(cameraId)
                cameraMedia.openFile()
                self._cameraList.append(cameraMedia)
                self._imageList.append(None)
            except MediaError, mediaError:
                print "Error opening camera: %d Message: %s" % (cameraId, str(mediaError))
                print "Stopping after %d cameras." % (cameraId)
                stop = True
            cameraId += 1
            if(cameraId > maxCameras):
                stop = True
        self._numCameras = cameraId
        self._cameraDisplayMixer = CameraDisplayMixer(self._internalResolutionX, self._internalResolutionY, self._numCameras, self._cameraConfiguration)

        self._updateTimer = wx.Timer(self, -1) #@UndefinedVariable
        self._updateTimer.Start(1000 / 60)#30 times a second
        self.Bind(wx.EVT_TIMER, self._frameUpdate, id=self._updateTimer.GetId()) #@UndefinedVariable
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
        self.Bind(wx.EVT_LEFT_UP, self._onMouseButton) #@UndefinedVariable

    def _getConfiguration(self):
        pass

    def _updateTitle(self, message = None):
        if(message == None):
            self.SetTitle(self._baseTitle)
        else:
            self.SetTitle(self._baseTitle + "   *** " + message + " ***")

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

    def _onMouseButton(self, event):
        xPos, yPos = event.GetPosition()
        xPos = xPos - self._imagePosX
        yPos = yPos - self._imagePosY
        self._cameraDisplayMixer.selectSmallImage(xPos, yPos)

    def _onWindowClose(self, event = None):
        print "User has closed window!"
        self._stopPlayer()

    def _stopPlayer(self):
        print "Closeing applicaton"
        if(self._fullscreenMode == True):
            self.ShowFullScreen(False, style=0)

        self._updateTimer.Stop()

        try:
            if(self._cameraServer != None):
                self._cameraServer.requestCameraWebServerProcessToStop()

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
            if(self._cameraServer != None):
                self._cameraServer.forceCameraWebServerProcessToStop()
            allDone = True
        else:
            if((self._cameraServer == None) or (self._cameraServer.hasCameraWebServerProcessShutdownNicely())):
                print "All done. (shutdown timer counter: " + str(self._shutdownTimerCounter) + " )"
                allDone = True
            if(allDone == False):
                self._shutdownTimerCounter += 1
                if(self._shutdownTimerCounter > 200):
                    print "Shutdown timeout!!! Force killing rest..."
                    if((self._cameraServer != None) and (self._cameraServer.hasCameraWebServerProcessShutdownNicely() == False)):
                        self._cameraServer.forceCameraWebServerProcessToStop()
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


    def _frameUpdate(self, event = None):
#            if (dt > self._timingThreshold):
#                print("Too slow main schedule " + str(dt))
        #Prepare frame
        timeStamp = time.time()
        for i in range(self._numCameras - 1):
            cameraMedia = self._cameraList[i]
            self._imageList[i] = cameraMedia.getFrames(timeStamp)

        #Save images:
        fileNameList = self._cameraDisplayMixer.saveImages(self._imageList, timeStamp)

        #Update web server:
        self._cameraServer.processCameraWebServerMessages()
        self._cameraServer.processCameraWebServerMessages()
        self._cameraServer.updateFileNameList(fileNameList)

        #Show frame:
        mixedImage = self._cameraDisplayMixer.placeImages(self._imageList)
        self._wxImageBuffer.SetData(mixedImage.tostring())
        self._updateBuffer()

#            timeUsed = time.time() - timeStamp
#            if((timeUsed / self._lastDelta) > 0.9):
#                print "PCN time: " + str(timeUsed) + " last delta: " + str(self._lastDelta)
#            self._lastDelta = dt

if __name__ in ('__android__', '__main__'):
    multiprocessing.freeze_support()

    helpMode = False
    debugMode = False
    checkForMoreConfigFileName = False
    checkForMoreConfigDirName = False
    configDir = ""
    configFile = ""
    for i in range(len(sys.argv) - 1):
        if(sys.argv[i+1].lower() == "--help"):
            print os.path.basename(sys.argv[0]) + " --help --debug --configDir=DIR_NAME --configFile=FILE_NAME"
            print "\t--help\t\t\t\tPrint this text and exit"
            print "\t--debug\t\t\t\tPrints debug info to console and not to logfile"
            print "\t--configDir=DIR_NAME\t\tSet config file to start with"
            print "\t--configFile=FILE_NAME\t\tSet configuration directory"
            print ""
            print "    TaktPlayer version: " + getVersionNumberString()
            print "        Build date:\t" + getVersionDateString()
            print "        Build id:\t" + getVersionGitIdString()
            helpMode = True
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

    if(helpMode != True):
        appDataDir, _ = getDefaultDirectories()
        logFileName = os.path.normpath(os.path.join(appDataDir, APP_NAME + ".log"))
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
        if(sys.platform == "darwin"):
            os.environ["PATH"] += ":."
            launchGUI = False
        applicationHolder = wx.App(redirect = redirectValue, filename = logFileName) #@UndefinedVariable
        gui = CameraMain(None, configDir, configFile, debugMode, title="Takt Camera Server")
        try:
            applicationHolder.MainLoop()
        except:
            gui._stopPlayer()
            raise

