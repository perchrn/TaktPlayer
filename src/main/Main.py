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

from video.media.MediaMixer import MediaMixer
from video.media.MediaPool import MediaPool
from midi.MidiTiming import MidiTiming
import midi.TcpMidiListner

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

        self._pcnVideoWidget = PcnVideo(resolution=(800, 600))
        self._midiTiming = MidiTiming()
        self._mediaMixer = MediaMixer(self._multiprocessLogger)
        self._mediaPool = MediaPool(self._midiTiming, self._mediaMixer, self._multiprocessLogger, (800, 600))
        self._mediaPool.addMedia("", "0C", 1.0) #Blank media
        self._mediaPool.addMedia("../../testFiles/basicVideo/testAnim_4-4_text_mjpeg.png.avi", "1C", 4.0)
        self._mediaPool.addMedia("../../testFiles/basicVideo/testAnim_4-4_text_mjpeg.png.avi", "1C#", 8.0)
        self._mediaPool.addMedia("../../testFiles/basicVideo/testAnim_4-4_text_mjpeg.png.avi", "1D", 16.0)
        self._mediaPool.addMedia("../../testFiles/basicVideo/Gutta_FlyingCombined_mjpeg.avi", "1E", 16.0)
        self._mediaPool.addMedia("../../testFiles/basicVideo/Gutta_FlyingCombined_mjpeg.avi", "1F", 32.0)

        self._pcnVideoWidget.setFrameProviderClass(self._mediaMixer)
        self._midiListner = midi.TcpMidiListner.TcpMidiListner(self._midiTiming, self._multiprocessLogger)
        return self._pcnVideoWidget

    def stopProcess(self):
        self._log.info("Caught signal INT")
        self.stop()

    def on_stop(self):
        self._log.info("Close applicaton")
        self._midiListner.stopDaemon()
        self._mediaMixer.stopMixerProcess()

    def getNextFrame(self, dt):
        try:
            if (dt > 0.02):
                self._log.info("Too slow main schedule " + str(dt))
            timeStamp = time.time()
            self._midiListner.getData()
            self._mediaPool.updateVideo(timeStamp)
            self._multiprocessLogger.handleQueuedLoggs()
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
