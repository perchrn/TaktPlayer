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

import video.media.MediaFile
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
        self._pcnVideoWidget = PcnVideo(resolution=(800, 600))
        self._midiTiming = MidiTiming()

        self._mediaFile = video.media.MediaFile.MediaFile("../../testFiles/basicVideo/testAnim_4-4_text_mjpeg.png.avi", self._midiTiming)
#        self._mediaFile = video.media.MediaFile.MediaFile("../../testFiles/basicVideo/Gutta_FlyingCombined_mjpeg.avi")
#        self._mediaFile = video.media.MediaFile.MediaFile("Gutta_FlyingCombined_mjpeg.avi")
        self._mediaFile.openFile()
        self._mediaFile.setMidiLength(8.0)
#        originalBaars120BPM = int((self._originalTime / 2) + 0.5)
        self._pcnVideoWidget.setFrameProviderClass(self._mediaFile)
        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._multiprocessLogger = MultiprocessLogger.MultiprocessLogger(self._log)
        self._midiListner = midi.TcpMidiListner.TcpMidiListner(self._midiTiming, self._multiprocessLogger)
#        self._log.setLevel(logging.WARNING)
        return self._pcnVideoWidget

    def stopProcess(self):
        self._log.info("Caught signal INT")
        self.stop()

    def on_stop(self):
        self._log.info("Close applicaton")
        self._midiListner.stopDaemon()

    def getNextFrame(self, dt):
        if (dt > 0.02):
            self._log.info("Too slow main schedule " + str(dt))
        timeStamp = time.time()
        midiSync, midiTime = self._midiTiming.getSongPosition(timeStamp) #@UnusedVariable
        self._mediaFile.skipFrames(midiTime)
        self._midiListner.getData()
        self._multiprocessLogger.handleQueuedLoggs()

if __name__ in ('__android__', '__main__'):
    
    mainApp = MyKivyApp()
    Clock.schedule_interval(mainApp.getNextFrame, 0)
#    Clock.schedule_interval(mainApp.frameReady, -1)
    signal.signal(signal.SIGINT, mainApp.stopProcess)
    mainApp.run()

