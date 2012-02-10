'''
Created on 28. nov. 2011

@author: pcn
'''

#Kivy imports
import os
from configuration.EffectSettings import EffectTemplates, FadeTemplates
from configuration.GuiServer import GuiServer
os.environ['KIVY_CAMERA'] = 'opencv'
import kivy
kivy.require('1.0.9') # replace with your current kivy version !
from kivy.app import App
from kivy.clock import Clock

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

class MyKivyApp(App):
#    icon = 'custom-kivy-icon.png'
    title = 'Musical Video Player'

    def build(self):
        #Multithreaded logging utility and regular logging:
        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
#        self._log.setLevel(logging.WARNING)
        self._multiprocessLogger = MultiprocessLogger.MultiprocessLogger(self._log)

        self._configurationTree = ConfigurationHolder("MusicalVideoPlayer")
#        self._configurationTree.loadConfig("DefaultConfig.cfg")
#        self._configurationTree.loadConfig("NerverIEnBunt_1.cfg")
#        self._configurationTree.loadConfig("HongKong_1.cfg")
#        self._configurationTree.loadConfig("Baertur_1.cfg")
        self._configurationTree.loadConfig("PovRay_1.cfg")
        self._globalConfig = self._configurationTree.addChildUnique("Global")
        self._globalConfig.addIntParameter("ResolutionX", 800)
        self._globalConfig.addIntParameter("ResolutionY", 600)

        self._internalResolutionX =  self._configurationTree.getValueFromPath("Global.ResolutionX")
        self._internalResolutionY =  self._configurationTree.getValueFromPath("Global.ResolutionY")

        self._pcnVideoWidget = PcnVideo(resolution=(self._internalResolutionX, self._internalResolutionY))

        self._midiTiming = MidiTiming()
        self._midiStateHolder = MidiStateHolder()
#        self._midiStateHolder.noteOn(0, 0x18, 0x40, (True, 0.0))

        self._effectsConfiguration = EffectTemplates(self._globalConfig, self._midiTiming, self._internalResolutionX, self._internalResolutionY)
        self._mediaFadeConfiguration = FadeTemplates(self._globalConfig, self._midiTiming)

        confChild = self._configurationTree.addChildUnique("MediaMixer")
        self._mediaMixer = MediaMixer(confChild, self._midiStateHolder, self._effectsConfiguration)
        confChild = self._configurationTree.addChildUnique("MediaPool")
        self._mediaPool = MediaPool(self._midiTiming, self._midiStateHolder, self._mediaMixer, self._effectsConfiguration, self._mediaFadeConfiguration, confChild, self._multiprocessLogger)

        self._pcnVideoWidget.setFrameProviderClass(self._mediaMixer)
        self._midiListner = TcpMidiListner(self._midiTiming, self._midiStateHolder, self._multiprocessLogger)
        self._timingThreshold = 2.0/60
        self._lastDelta = -1.0

        self._configCheckEveryNRound = 60 * 5 #Every 5th second
        self._configCheckCounter = 0

        self._guiServer = GuiServer(self._configurationTree, self._mediaPool, self._midiStateHolder)
        self._guiServer.startGuiServerProcess("0.0.0.0", 2021, None)
        print self._configurationTree.getConfigurationXMLString()

        return self._pcnVideoWidget

    def _getConfiguration(self):
        self._internalResolutionX =  self._configurationTree.getValueFromPath("Global.ResolutionX")
        self._internalResolutionY =  self._configurationTree.getValueFromPath("Global.ResolutionY")

    def checkAndUpdateFromConfiguration(self):
        if(self._configCheckCounter >= self._configCheckEveryNRound):
            if(self._configurationTree.isConfigurationUpdated()):
                #TODO: Fix config updated indicator...
#                print "config is updated..."
                self._getConfiguration()
                self._mediaPool.checkAndUpdateFromConfiguration()
                self._configurationTree.resetConfigurationUpdated()
                self._globalConfig.resetConfigurationUpdated()
                #TODO: autosave...
            self._configCheckCounter = 0
        else:
            self._configCheckCounter += 1

    def stopProcess(self):
        self._log.info("Caught signal INT")
        self.stop()

    def on_stop(self):
        self._log.info("Close applicaton")
        self._midiListner.stopDaemon()
        self._guiServer.stopGuiServerProcess()

    def frameReady(self, dt):
        pass

    def getNextFrame(self, dt):
        try:
#            if (dt > self._timingThreshold):
#                self._log.info("Too slow main schedule " + str(dt))
            timeStamp = time.time()
            self._midiListner.getData()
            self._mediaPool.updateVideo(timeStamp)
            self._multiprocessLogger.handleQueuedLoggs()
            self.checkAndUpdateFromConfiguration()
            self._guiServer.processGuiRequests()
#            timeUsed = time.time() - timeStamp
#            if((timeUsed / self._lastDelta) > 0.9):
#                print "PCN time: " + str(timeUsed) + " last delta: " + str(self._lastDelta)
            self._lastDelta = dt
        except:
            self.stopProcess()
            raise

if __name__ in ('__android__', '__main__'):
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
