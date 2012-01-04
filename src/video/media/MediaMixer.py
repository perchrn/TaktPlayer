'''
Created on 21. des. 2011

@author: pcn
'''
import logging

from video.media.MediaFile import imageFromArray, imageToArray, getEmptyImage

class MediaMixer(object):
    def __init__(self):
        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))

        self._currentImage = getEmptyImage(800, 600)
        self._currentImageId = 0
        self._nextImage = self._currentImage
        self._nextImageId = 0

    def getImage(self):
        self._updateWithLatestImageFromQueue()
        return self._currentImage

    def gueueImage(self, image, midiChannel):
        #TODO: store for each channel and mix down on request
        self._testTransfer = imageToArray(image)

    def _updateImage(self):
        if(self._currentImageId != self._nextImageId):
            self._currentImageId = self._nextImageId
            self._currentImage = self._nextImage

    def _updateWithLatestImageFromQueue(self):
        self._nextImage = imageFromArray(self._testTransfer)
        self._nextImageId += 1
        self._updateImage()


