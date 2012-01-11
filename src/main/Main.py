'''
Created on 28. nov. 2011

@author: pcn
'''

#Kivy imports
import os
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
    def build(self):
        #Multithreaded logging utility and regular logging:
        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
#        self._log.setLevel(logging.WARNING)
        self._multiprocessLogger = MultiprocessLogger.MultiprocessLogger(self._log)

        self._configurationTree = ConfigurationHolder("MusicalVideoPlayer")
        self._pcnVideoWidget = PcnVideo(resolution=(800, 600))
        self._midiTiming = MidiTiming()
        self._midiStateHolder = MidiStateHolder()
        self._mediaMixer = MediaMixer()
        confChild = self._configurationTree.addChildUnique("MediaPool")
        self._mediaPool = MediaPool(self._midiTiming, self._midiStateHolder, self._mediaMixer, confChild, self._multiprocessLogger, (800, 600))
        self._mediaPool.addMedia("", "0C", 1.0) #Blank media
        self._mediaPool.addMedia("../../testFiles/basicVideo/testAnim_4-4_text_mjpeg.png.avi", "1C", 4.0)
        self._mediaPool.addMedia("../../testFiles/basicVideo/testAnim_4-4_text_mjpeg.png.avi", "1C#", 8.0)
        self._mediaPool.addMedia("../../testFiles/basicVideo/testAnim_4-4_text_mjpeg.png.avi", "1D", 16.0)
        self._mediaPool.addMedia("../../testFiles/basicVideo/Gutta_FlyingCombined_mjpeg.avi", "1E", 12.0)
        self._mediaPool.addMedia("../../testFiles/basicVideo/Gutta_FlyingCombined_mjpeg.avi", "1F", 24.0)
        self._mediaPool.addMedia("../../testFiles/basicVideo/herrang.jpg", "2C", 1.0)
        self._mediaPool.addMedia("../../testFiles/basicVideo/testAnim_8steps_sequence.avi", "0C", 1.0)
        self._mediaPool.addMedia("../../testFiles/basicVideo/testAnim_8steps_sequence.avi", "0C#", 4.0)
        self._mediaPool.addMedia("../../testFiles/basicVideo/testAnim_8steps_mjpeg.avi", "0D", 16.0)
        

        self._pcnVideoWidget.setFrameProviderClass(self._mediaMixer)
        self._midiListner = TcpMidiListner(self._midiTiming, self._midiStateHolder, self._multiprocessLogger)
        self._timingThreshold = 2.0/60
        self._lastDelta = -1.0

        xmlConfTree = self._configurationTree.getConfigurationXMLString()
        print xmlConfTree

        return self._pcnVideoWidget

    def stopProcess(self):
        self._log.info("Caught signal INT")
        self.stop()

    def on_stop(self):
        self._log.info("Close applicaton")
        self._midiListner.stopDaemon()

    def frameReady(self, dt):
        pass

    def getNextFrame(self, dt):
        try:
            if (dt > self._timingThreshold):
                self._log.info("Too slow main schedule " + str(dt))
            timeStamp = time.time()
            self._midiListner.getData()
            self._mediaPool.updateVideo(timeStamp)
            self._multiprocessLogger.handleQueuedLoggs()
            timeUsed = time.time() - timeStamp
            if((timeUsed / self._lastDelta) > 0.9):
                print "PCN time: " + str(timeUsed) + " last delta: " + str(self._lastDelta)
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
