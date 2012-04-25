'''
Created on 28. nov. 2011

@author: pcn
'''

#Kivy imports
import os
from configuration.EffectSettings import EffectTemplates, FadeTemplates, EffectImageList
from configuration.GuiServer import GuiServer
import multiprocessing
from multiprocessing import Process, Queue
from configuration.PlayerConfiguration import PlayerConfiguration
from kivy.config import Config
import sys
os.environ['KIVY_CAMERA'] = 'opencv'
import kivy
kivy.require('1.0.9') # replace with your current kivy version !
from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config

#pcn stuff
from pcnKivy.pcnVideoWidget import PcnVideo

from configuration.ConfigurationHolder import ConfigurationHolder

from video.media.MediaMixer import MediaMixer
from video.media.MediaPool import MediaPool

from midi.MidiTiming import MidiTiming
from midi.TcpMidiListner import TcpMidiListner
from midi.MidiStateHolder import MidiStateHolder

from utilities import MultiprocessLogger

#Python standard
import time
import signal
#Log system
import logging
logging.root.setLevel(logging.ERROR)

internalResolutionX = 800
internalResolutionY = 600

class MyKivyApp(App):
    icon = os.path.normpath('graphics/TaktPlayer.png')
    title = 'Takt Player'

    def build(self):
        #Multithreaded logging utility and regular logging:
        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
#        self._log.setLevel(logging.WARNING)
        self._multiprocessLogger = MultiprocessLogger.MultiprocessLogger(self._log)

        self._playerConfiguration = PlayerConfiguration()
        self._internalResolutionX = internalResolutionX
        self._internalResolutionY =  internalResolutionY

        self._configurationTree = ConfigurationHolder("MusicalVideoPlayer")
        self._configurationTree.loadConfig(self._playerConfiguration.getStartConfig())
        self._globalConfig = self._configurationTree.addChildUnique("Global")

        self._pcnVideoWidget = PcnVideo(internalResolution=(self._internalResolutionX, self._internalResolutionY))

        self._midiTiming = MidiTiming()
        self._midiStateHolder = MidiStateHolder()


        self._effectsConfiguration = EffectTemplates(self._globalConfig, self._midiTiming, self._internalResolutionX, self._internalResolutionY)
        self._mediaFadeConfiguration = FadeTemplates(self._globalConfig, self._midiTiming)
        self._effectImagesConfiguration = EffectImageList(self._globalConfig, self._midiTiming, self._playerConfiguration.getVideoDir())

        confChild = self._configurationTree.addChildUnique("MediaMixer")
        self._mediaMixer = MediaMixer(confChild, self._midiStateHolder, self._effectsConfiguration, self._effectImagesConfiguration, self._internalResolutionX, self._internalResolutionY)
        confChild = self._configurationTree.addChildUnique("MediaPool")
        self._mediaPool = MediaPool(self._midiTiming, self._midiStateHolder, self._mediaMixer, self._effectsConfiguration, self._effectImagesConfiguration, self._mediaFadeConfiguration, confChild, self._internalResolutionX, self._internalResolutionY, self._playerConfiguration.getVideoDir())

        self._pcnVideoWidget.setFrameProviderClass(self._mediaMixer)
        self._midiListner = TcpMidiListner(self._midiTiming, self._midiStateHolder, self._multiprocessLogger)
        self._midiListner.startDaemon(self._playerConfiguration.getMidiServerAddress(), self._playerConfiguration.getMidiServerPort(), self._playerConfiguration.getMidiServerUsesBroadcast())

        self._timingThreshold = 2.0/60
        self._lastDelta = -1.0

        self._configCheckEveryNRound = 60 * 5 #Every 5th second
        self._configCheckCounter = 0

        self._guiServer = GuiServer(self._configurationTree, self._mediaPool, self._midiStateHolder)
        self._guiServer.startGuiServerProcess(self._playerConfiguration.getWebServerAddress(), self._playerConfiguration.getWebServerPort(), None)
        startNote = self._playerConfiguration.getStartNoteNumber()
        if((startNote > -1) and (startNote < 128)):
            self._midiStateHolder.noteOn(0, startNote, 0x40, (True, 0.0))
            self._midiStateHolder.noteOff(0, startNote, 0x40, (True, 0.000000001))

        self._guiProcess = None
        self._playerOnlyMode = False
        if(Config.getint("DEFAULT", "playerOnly") == 1):
            self._playerOnlyMode = True
        if(self._playerOnlyMode == False):
            print "*-*-*" * 30
            print "Start GUI process!"
            self._startGUIProcess()
            print "*-*-*" * 30

        print self._configurationTree.getConfigurationXMLString()

        return self._pcnVideoWidget

    def _getConfiguration(self):
        pass

    def checkAndUpdateFromConfiguration(self):
        if(self._configCheckCounter >= self._configCheckEveryNRound):
            if(self._configurationTree.isConfigurationUpdated()):
                print "**********" * 10
                print "config is updated..."
                self._getConfiguration()
                self._effectsConfiguration.checkAndUpdateFromConfiguration()
                self._effectImagesConfiguration.checkAndUpdateFromConfiguration()
                self._mediaFadeConfiguration.checkAndUpdateFromConfiguration()
                self._mediaPool.checkAndUpdateFromConfiguration()
                self._mediaMixer.checkAndUpdateFromConfiguration()
                self._configurationTree.resetConfigurationUpdated()
                #TODO: autosave...
                print "**********" * 10
                print self._configurationTree.getConfigurationXMLString()
                print "**********" * 10
            self._configCheckCounter = 0
        else:
            self._configCheckCounter += 1

    def _startGUIProcess(self):
        self._log.debug("Starting GUI Process")
        from configurationGui.GuiMainWindow import startGui
        self._commandQueue = Queue(10)
        self._statusQueue = Queue(-1)
        self._guiProcess = Process(target=startGui, args=(False, self._commandQueue, self._statusQueue))
        self._guiProcess.name = "guiProcess"
        self._guiProcess.start()

    def _checkStatusQueue(self):
        if(self._guiProcess != None):
            try:
                status = self._statusQueue.get_nowait()
                if(status == "QUIT"):
                    self.stopProcess()
                else:
                    self._log.warning("From GUI: %s" % status)
            except:
                pass
            
    def _requestGuiProcessToStop(self):
        if(self._guiProcess != None):
            self._log.debug("Stopping GUI Process")
            self._commandQueue.put("QUIT")

    def _stopGUIProcess(self):
        if(self._guiProcess != None):
            self._guiProcess.join(20.0)
            if(self._guiProcess.is_alive()):
                print "GUI Process did not respond to quit command. Terminating."
                self._guiProcess.terminate()
            self._guiProcess = None

    def stopProcess(self):
        self._log.info("Caught signal INT")
        self.stop()

    def on_stop(self):
        self._log.info("Close applicaton")
        self._midiListner.requestTcpMidiListnerProcessToStop()
        self._guiServer.requestGuiServerProcessToStop()
        self._requestGuiProcessToStop()
        self._midiListner.stopDaemon()
        self._guiServer.stopGuiServerProcess()
        self._stopGUIProcess()

    def frameReady(self, dt):
        pass

    def getNextFrame(self, dt):
        try:
#            if (dt > self._timingThreshold):
#                self._log.info("Too slow main schedule " + str(dt))
            timeStamp = time.time()
            self._checkStatusQueue()
            self._midiListner.getData(False)
            self._mediaPool.updateVideo(timeStamp)
            self._multiprocessLogger.handleQueuedLoggs()
            self.checkAndUpdateFromConfiguration()
            updateConfig = self._guiServer.processGuiRequests()
            if(updateConfig == True):
                self._configCheckCounter = self._configCheckEveryNRound + 1
#            timeUsed = time.time() - timeStamp
#            if((timeUsed / self._lastDelta) > 0.9):
#                print "PCN time: " + str(timeUsed) + " last delta: " + str(self._lastDelta)
            self._lastDelta = dt
        except:
            self.stopProcess()
            raise

if __name__ in ('__android__', '__main__'):
    multiprocessing.freeze_support()

    playerConfiguration = PlayerConfiguration()
    internalResolutionX, internalResolutionY =  playerConfiguration.getResolution()
    fullscreenMode = playerConfiguration.getFullscreenMode()

    if(sys.platform == "win32"):
        from win32api import GetSystemMetrics #@UnresolvedImport
        currentWidth = GetSystemMetrics (0)
        currentHeight = GetSystemMetrics (1)
    elif(sys.platform == "darwin"):
        import AppKit #@UnresolvedImport
        screen = AppKit.NSScreen.screens()[0]
        currentWidth = screen.frame().size.width
        currentHeight = screen.frame().size.height
    else:
        print "do xrandr | grep '*' and parse to get resolution on linux etc..."
    if(fullscreenMode == "auto"):
        internalResolutionX = currentWidth
        internalResolutionY = currentHeight
        Config.set('graphics', 'fullscreen', "auto")
        print "Startup fullscreen: Width: " + str(currentWidth) + " Height: " + str(currentHeight)
    elif(fullscreenMode == "on"):
        Config.set('graphics', 'width', str(internalResolutionX))
        Config.set('graphics', 'height', str(internalResolutionY))
        Config.set('graphics', 'fullscreen', "auto")
        print "Startup fullscreen: Width: " + str(internalResolutionX) + " Height: " + str(internalResolutionY)
    else:
        windowWidth = min(currentWidth, (internalResolutionX + 100))
        windowHeight = min(currentHeight, (internalResolutionY + 100))
        Config.set('graphics', 'width', str(windowWidth))
        Config.set('graphics', 'height', str(windowHeight))
        Config.set('graphics', 'fullscreen', "0")
        autoMode = playerConfiguration.isAutoPositionEnabled()
        if(autoMode == True):
            Config.set('graphics', 'position', "auto")
        else:
            positionX, postionY = playerConfiguration.getPosition()
            Config.set('graphics', 'position', "custom")
            Config.set('graphics', 'left', str(positionX))
            Config.set('graphics', 'top', str(postionY))
            print "Custom position: Left: " + str(postionY) + " Top: " + str(positionX)
        print "Startup windowed: Width: " + str(windowWidth) + " Height: " + str(windowHeight)
    Config.write()

    try:
        mainApp = MyKivyApp()
        Clock.schedule_interval(mainApp.getNextFrame, 0)
#        Clock.schedule_interval(mainApp.frameReady, -1)
        signal.signal(signal.SIGINT, mainApp.stopProcess)
        mainApp.run()
    except:
        mainApp.stopProcess()
        raise
    print "Exiting MAIN XoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoX"
    mainApp.stopProcess()
