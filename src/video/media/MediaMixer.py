'''
Created on 21. des. 2011

@author: pcn
'''
from multiprocessing import Process, Queue
from Queue import Empty
import logging
import time

from utilities import MultiprocessLogger
from video.media.MediaFile import imageFromArray, imageToArray, getEmptyImage

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
                queueImageString, queueMidiChannel = inputQueue.get_nowait()
                processLogger.debug("got something ch: " + str(queueMidiChannel))
                if(queueMidiChannel == -1):
                    processLogger.debug("got command QUIT")
                    run = False
                else:
                    gotOne = True
                    image = queueImageString
                    processLogger.warning("got something 2")
            except Empty:
                queueEmpty = True

class MediaMixer(object):
    def __init__(self, multiprocessLogger):
        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._multiprocessLogger = multiprocessLogger
        self._inputQueue = Queue(32)
        self._outputQueue = Queue(4)
        self._mixerProcess = None
#        self.startMixerProcess()

        self._currentImage = getEmptyImage(800, 600)
        self._currentImageId = 0
        self._nextImage = self._currentImage
        self._nextImageId = 0

    def startMixerProcess(self):
        self._log.debug("Starting Mixer Process")
        self._mixerProcess = Process(target=mixerProcess, args=(self._inputQueue, self._outputQueue, self._multiprocessLogger.getLogQueue()))
        self._mixerProcess.name = "mixerProcess"
#        self._mixerProcess.daemon = True
        self._mixerProcess.start()

    def stopMixerProcess(self):
        if(self._mixerProcess != None):
            self._log.debug("Stopping Mixer Process")
            self._inputQueue.put((None, -1))
            self._mixerProcess.join(10.0)

    def getImage(self):
        self._updateWithLatestImageFromQueue()
        return self._currentImage

    def gueueImage(self, image, midiChannel):
#        print "gueueImage ch: " + str(midiChannel)
#        try:
#            self._inputQueue.put_nowait((imageToArray(image), midiChannel))
#        except:
#            pass
        self._testTransfer = imageToArray(image)

    def _updateImage(self):
        if(self._currentImageId != self._nextImageId):
            self._currentImageId = self._nextImageId
            self._currentImage = self._nextImage

    def _updateWithLatestImageFromQueue(self):
        self._nextImage = imageFromArray(self._testTransfer)
        self._nextImageId += 1
        self._updateImage()
#        gotOne = False
#        queueEmpty = False
#        while(queueEmpty == False):
#            try:
#                imageArray = self._outputQueue.get_nowait()
#                print "_updateWithLatestImageFromQueue got one"
#                gotOne = True
#            except Empty:
#                queueEmpty = True
#        if(gotOne):
#            self._nextImage = imageFromArray(imageArray)
#            self._nextImageId += 1
#            self._updateImage()



