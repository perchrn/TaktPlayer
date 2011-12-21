'''
Created on 21. des. 2011

@author: pcn
'''
from multiprocessing import Process, Queue
from Queue import Empty
import logging
import time

from utilities import MultiprocessLogger

def mixerProcess(inputQueue, outputQueue, logQueue):
    #Logging etc.
    processLogger = logging.getLogger('mixerProcess')
    processLogger.setLevel(logging.DEBUG)
    MultiprocessLogger.configureProcessLogger(processLogger, logQueue)

    run = True
    gotOne = False
    image = None
    while(run):
        if(gotOne):
            outputQueue.put_nowait(image)
            gotOne = False
        else:
            time.sleep(0.02)
        queueEmpty = False
        while(queueEmpty == False):
            try:
                image, midichannel = inputQueue.get_nowait()
                if(midichannel == -1):
                    processLogger.debug("got command QUIT")
                    run = False
                else:
                    gotOne = True
            except Empty:
                queueEmpty = True

class MediaMixer(object):
    def __init__(self, multiprocessLogger):
        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._multiprocessLogger = multiprocessLogger
        self._inputQueue = Queue(32)
        self._outputQueue = Queue(4)
        self.startMixerProcess()

        self._currentImage = None
        self._currentImageId = 0
        self._nextImage = None
        self._nextImageId = 0

    def startMixerProcess(self):
        self._log.debug("Starting Mixer Process")
        self._mixerProcess = Process(target=mixerProcess, args=(self._inputQueue, self._outputQueue, self._multiprocessLogger.getLogQueue()))
        self._mixerProcess.name = "mixerProcess"
#        self._mixerProcess.daemon = True
        self._mixerProcess.start()

    def stopMixerProcess(self):
        self._log.debug("Stopping Mixer Process")
        self._inputQueue.put((None, -1))
        self._mixerProcess.join(10.0)

    def getImage(self):
        self._updateWithLatestImageFromQueue()
        return self._currentImage

    def gueueImage(self, image, midiChannel):
        self._inputQueue.put_nowait((image, midiChannel))

    def _setImage(self, newImage):
        self._nextImage = newImage
        self._nextImageId += 1

    def _updateImage(self):
        if(self._currentImageId != self._nextImageId):
            self._currentImageId = self._nextImageId
            self._currentImage = self._nextImage

    def _updateWithLatestImageFromQueue(self):
        gotOne = False
        queueEmpty = False
        while(queueEmpty == False):
            try:
                image = self._outputQueue.get_nowait()
                gotOne = True
            except Empty:
                queueEmpty = True
        if(gotOne):
            self._setImage(image)
            self._updateImage()



