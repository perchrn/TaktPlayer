'''
Created on 28. nov. 2011

@author: pcn
'''

#Imports
from configuration.EffectSettings import EffectTemplates, FadeTemplates, EffectImageList
from configuration.GuiServer import GuiServer
import multiprocessing
from multiprocessing import Process, Queue
from configuration.PlayerConfiguration import PlayerConfiguration
import sys

#pcn stuff
from configuration.ConfigurationHolder import ConfigurationHolder

from video.media.MediaMixer import MediaMixer
from video.media.MediaPool import MediaPool

from video.media.MediaFile import createCvWindow, showCvImage, hasCvWindowStoped

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
fullscreenMode = "off"
positionX = -1
positionY = -1
launchGUI = True

class PlayerMain(object):
    def __init__(self):
#        pygame.init()

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

#        print "createCvWindow: " + str(fullscreenMode) + " | " + str(self._internalResolutionX) + " | " + str(self._internalResolutionY) + " | " + str(positionX) + " | " + str(positionY)
        createCvWindow(fullscreenMode, self._internalResolutionX, self._internalResolutionY, positionX, positionY)

        self._midiTiming = MidiTiming()
        self._midiStateHolder = MidiStateHolder()


        self._effectsConfiguration = EffectTemplates(self._globalConfig, self._midiTiming, self._internalResolutionX, self._internalResolutionY)
        self._mediaFadeConfiguration = FadeTemplates(self._globalConfig, self._midiTiming)
        self._effectImagesConfiguration = EffectImageList(self._globalConfig, self._midiTiming, self._playerConfiguration.getVideoDir())

        confChild = self._configurationTree.addChildUnique("MediaMixer")
        self._mediaMixer = MediaMixer(confChild, self._midiStateHolder, self._effectsConfiguration, self._effectImagesConfiguration, self._internalResolutionX, self._internalResolutionY)
        confChild = self._configurationTree.addChildUnique("MediaPool")
        self._mediaPool = MediaPool(self._midiTiming, self._midiStateHolder, self._mediaMixer, self._effectsConfiguration, self._effectImagesConfiguration, self._mediaFadeConfiguration, confChild, self._internalResolutionX, self._internalResolutionY, self._playerConfiguration.getVideoDir())

        self._midiListner = TcpMidiListner(self._midiTiming, self._midiStateHolder, self._multiprocessLogger)
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

        print self._configurationTree.getConfigurationXMLString()

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
                return status
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

    def stop(self):
        self._log.info("Close applicaton")
        self._midiListner.requestTcpMidiListnerProcessToStop()
        self._guiServer.requestGuiServerProcessToStop()
        self._requestGuiProcessToStop()
        self._midiListner.stopDaemon()
        self._guiServer.stopGuiServerProcess()
        self._stopGUIProcess()

    def processFrame(self):
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
        showCvImage(mixedImage)
#        print "DEBUG imageArray: " + str(type(imageArray)) + " array: " + str(imageArray)
#        imageArray.transpose(1,0,2)
#        pygame.surfarray.blit_array(self._pygameVideoSurface, imageArray)
#        self._pygameDisplay.blit(self._pygameVideoSurface, self._pygameVideoRectangle)

        #Check for quit conditions...
        guiStatus = self._checkStatusQueue()
        if(guiStatus == "QUIT"):
            raise QuitRequestException("User has closed GUI window.")
        if(hasCvWindowStoped() == True):
            raise QuitRequestException("User has pressed escape.")
#        for event in pygame.event.get():
#            if event.type is pygame.QUIT:
#                raise QuitRequestException("User has closed window.")
#            if event.type is pygame.KEYDOWN:
#                if event.key is pygame.K_ESCAPE:
#                    raise QuitRequestException("User pressed escape.")

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
#    global internalResolutionX
#    global internalResolutionY
#    global fullscreenMode
#    global positionX
#    global positionY
    multiprocessing.freeze_support()

    playerConfiguration = PlayerConfiguration()
    internalResolutionX, internalResolutionY =  playerConfiguration.getResolution()
    fullscreenMode = playerConfiguration.getFullscreenMode()

    launchGUI = True
    for i in range(len(sys.argv) - 1):
        if(sys.argv[i+1].lower() == "--nogui"):
            launchGUI = False
    if(sys.platform == "win32"):
        from win32api import GetSystemMetrics #@UnresolvedImport
        currentWidth = GetSystemMetrics (0)
        currentHeight = GetSystemMetrics (1)
    elif(sys.platform == "darwin"):
        launchGUI = False
        if(fullscreenMode == "auto"):
            fullscreenMode = "on"
#        import AppKit #@UnresolvedImport
#        screen = Appkit.NSScreen.screens()[0]
#        currentWidth = screen.frame().size.width
#        currentHeight = screen.frame().size.height
    else:
        print "do xrandr | grep '*' and parse to get resolution on linux etc..."
    if(fullscreenMode == "auto"):
        internalResolutionX = currentWidth
        internalResolutionY = currentHeight
        print "Startup fullscreen: Width: " + str(currentWidth) + " Height: " + str(currentHeight)
    elif(fullscreenMode == "on"):
        print "Startup fullscreen: Width: " + str(internalResolutionX) + " Height: " + str(internalResolutionY)
    else:
        autoMode = playerConfiguration.isAutoPositionEnabled()
        if(autoMode == True):
            positionX, positionY = (-1, -1)
        else:
            positionX, positionY = playerConfiguration.getPosition()
            print "Custom position: Left: " + str(positionX) + " Top: " + str(positionY)
        print "Startup windowed: Width: " + str(internalResolutionX) + " Height: " + str(internalResolutionX)

    mainApp = PlayerMain()
    try:
        while(True):
            mainApp.processFrame()
    except QuitRequestException, quitRequest:
        print "Stopping player... (" + str(quitRequest) + ")"
        mainApp.stop()
        print "Player stopped! (" + str(quitRequest) + ")"
    except KeyboardInterrupt, keyboardInterrupt:
        print "Stopping player... (Keyboard Interrupt.)"
        mainApp.stop()
        print "Player stopped! (Keyboard Interrupt.)"
    except:
        mainApp.stop()
        raise
