'''
Created on 21. des. 2011

@author: pcn
'''
import logging

from video.media.MediaFile import getEmptyImage

class MediaMixer(object):
    def __init__(self):
        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))

        self._blankImage = getEmptyImage(800, 600)
        self._currentImage = self._blankImage
        self._currentImageId = 0
        self._nextImage = self._currentImage
        self._nextImageId = 0

        self._mediaTracks = []
        for i in range(16): #@UnusedVariable
            self._mediaTracks.append(None)

    def getImage(self):
        return self._currentImage

    def gueueImage(self, media, midiChannel):
        self._mediaTracks[midiChannel] = media

    def _updateImage(self):
        if(self._currentImageId != self._nextImageId):
            self._currentImageId = self._nextImageId
            self._currentImage = self._nextImage

    def mixImages(self):
        imageMix = None
        for midiChannel in range(16):
            currenMedia = self._mediaTracks[midiChannel]
            if(currenMedia != None):
                if(imageMix == None):
                    imageMix = currenMedia.getImage()
                else:
                    imageMix = currenMedia.mixWithImage(imageMix)
        if(imageMix == None):
            imageMix = self._blankImage
        self._nextImage = imageMix
        self._nextImageId += 1
        self._updateImage()


