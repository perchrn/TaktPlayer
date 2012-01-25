'''
Created on 21. des. 2011

@author: pcn
'''
import logging
from video.Effects import getEmptyImage, createMask, createMat
from video.media.MediaFile import MixMode


class MediaMixer(object):
    def __init__(self, configurationTree, midiStateHolder):
        self._configurationTree = configurationTree
        self._midiStateHolder = midiStateHolder
        #Logging etc.
        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))

        self._internalResolutionX =  self._configurationTree.getValueFromPath("Global.ResolutionX")
        self._internalResolutionY =  self._configurationTree.getValueFromPath("Global.ResolutionY")

        self._mixMat1 = createMat(self._internalResolutionX, self._internalResolutionY)
        self._mixMat2 = createMat(self._internalResolutionX, self._internalResolutionY)
        self._mixMat3 = createMat(self._internalResolutionX, self._internalResolutionY)
        self._mixMask = createMask(self._internalResolutionX, self._internalResolutionY)

        self._blankImage = getEmptyImage(self._internalResolutionX, self._internalResolutionY)
        self._currentImage = self._blankImage
        self._currentImageId = 0
        self._nextImage = self._currentImage
        self._nextImageId = 0

        self._mediaTracks = []
        for i in range(16): #@UnusedVariable
            self._mediaTracks.append(None)
        self._mediaTracksMixMode = []
        for i in range(16): #@UnusedVariable
            self._mediaTracksMixMode.append(MixMode.Default)
        self._mediaTracksEffects = []
        for i in range(16): #@UnusedVariable
            self._mediaTracksEffects.append(None)

    def getImage(self):
        return self._currentImage

    def gueueImage(self, media, midiChannel):
        self._mediaTracks[midiChannel] = media

    def _updateImage(self):
        if(self._currentImageId != self._nextImageId):
            self._currentImageId = self._nextImageId
            self._currentImage = self._nextImage

    def mixImages(self, midiTime):
        imageMix = None
        for midiChannel in range(16):
            currenMedia = self._mediaTracks[midiChannel]
            mixMode = self._mediaTracksMixMode[midiChannel]
            effects = self._mediaTracksEffects[midiChannel]
#TODO:            if(effects != None):
#                midiChannelState = self._midiStateHolder.getMidiChannelState(midiChannel)
#                midiNoteState = midiChannelState.getActiveNote(midiTime)
#                getEffectModulationValues(midiTime, midiChannelState)
            if(currenMedia != None):
                if(imageMix == None):
                    imageMix = currenMedia.getImage()
                else:
                    if(imageMix == self._mixMat1):
                        imageMix = currenMedia.mixWithImage(imageMix, mixMode, effects, self._mixMat1, self._mixMat2, self._mixMask)
                    else:
                        imageMix = currenMedia.mixWithImage(imageMix, mixMode, effects, self._mixMat2, self._mixMat3, self._mixMask)
        if(imageMix == None):
            imageMix = self._blankImage
        self._nextImage = imageMix
        self._nextImageId += 1
        self._updateImage()


