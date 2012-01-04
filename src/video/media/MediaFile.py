'''
Created on 12. okt. 2011

@author: pcn
'''
import os.path
import logging
from cv2 import cv
import numpy

def getEmptyImage(x, y):
    resizeMat = crateMat(x,y)
    return resizeImage(cv.CreateImage((x,y), cv.IPL_DEPTH_8U, 3), resizeMat)

def crateMat(width, heigth):
    return cv.CreateMat(heigth, width, cv.CV_8UC3)

def resizeImage(image, resizeMat):
    cv.Resize(image, resizeMat)
    return resizeMat

def zoomImage(image, xcenter, ycenter, zoomX, zoomY, minRange, maxRange, resizeMat):
    originalWidth, originalHeight = cv.GetSize(image)
    rangeFraction = maxRange - minRange
    zoomXFraction = minRange + (rangeFraction * zoomX)
    zoomYFraction = minRange + (rangeFraction * zoomY)
    width = int(float(originalWidth) * zoomXFraction)
    height = int(float(originalHeight) * zoomYFraction)
    left = int((originalWidth / 2) + (originalWidth * xcenter / 2) - (width / 2))
    top = int((originalHeight / 2) + (originalHeight * ycenter / 2) - (height / 2))
    right = left + width
    bottom = top + height
    outputRect = False
    outPutLeft = 0
    outPutWidth = -1
    outPutTop = 0
    outPutHeight = -1
    if(left < 0):
        outPutLeft = -int(float(left) / zoomXFraction)
        width = width + left
        left = 0
        outputRect = True
    if(right > originalWidth):
        outPutWidth = originalWidth+int(float(originalWidth - right) / zoomXFraction) - outPutLeft
        width = originalWidth - left
        outputRect = True
    if(top < 0):
        outPutTop = -int(float(top) / zoomYFraction)
        height = height + top
        top = 0
        outputRect = True
    if(bottom > originalHeight):
        outPutHeight = originalHeight+int(float(originalHeight - bottom) / zoomYFraction) - outPutTop
        height = originalHeight - top
        outputRect = True
#    print "Zoom: " + str(zoomX) + " M: " + str(minRange) + " R:(+) " + str(rangeFraction) + " w: " + str(width) + " h: " + str(height) + " l: " + str(left) + " t: " + str(top)
    src_region = cv.GetSubRect(image, (left, top, width, height) )
    if(outputRect):
        if(outPutWidth < 0):
            outPutWidth = originalWidth - outPutLeft
        if(outPutHeight < 0):
            outPutHeight = originalHeight - outPutTop
#        print "Zoom OUT: " + str(outPutWidth) + " h: " + str(outPutHeight) + " l: " + str(outPutLeft) + " t: " + str(outPutTop)
        tmpMat = crateMat(outPutWidth, outPutHeight)
        resized = resizeImage(src_region, tmpMat)
        cv.SetZero(resizeMat)
        dst_region = cv.GetSubRect(resizeMat, (outPutLeft, outPutTop, outPutWidth, outPutHeight) )
        cv.Copy(resized, dst_region)
        return resizeMat
    return resizeImage(src_region, resizeMat)

def imageToArray(image):
    return numpy.asarray(image)

def imageFromArray(array):
    return cv.fromarray(array)

class MediaFile:
    def __init__(self, fileName, midiTimingClass, windowSize):
        self.setFileName(fileName)
        self._midiTiming = midiTimingClass
        self._currentWindowWidth, self._currentWindowHeight = windowSize
        self._tmpResizeMat = crateMat(self._currentWindowWidth, self._currentWindowHeight)
        self._fileOk = False
        self._image = None
        self._firstImage = None
        self._numberOfFrames = 0
        self._originalFrameRate = 25
        self._originalTime = 0.0
        self._currentFrame = 0;
        self._startSongPosition = 0.0
        self._syncLength = self._midiTiming.getTicksPerQuarteNote() * 4

        self._minZoomPercent = 0.25
        self._maxZoomPercent = 4.0

        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._log.setLevel(logging.WARNING)

    def setFileName(self, fileName):
        self._filename = os.path.normcase(fileName)

    def isFileOk(self):
        return self._fileOk
    
    def getImage(self):
        return self._image

    def getFirstImage(self):
        return self._firstImage
    
    def getNumberOfFrames(self):
        return self._numberOfFrames
    
    def getOriginalFps(self):
        return self._originalFrameRate

    def setMidiLength(self, midiLength):
        self._syncLength = midiLength * self._midiTiming.getTicksPerQuarteNote()
    
    def getCurrentFramePos(self):
        return self._currentFrame

    def resizeImage(self, image):
        return resizeImage(image, self._tmpResizeMat)

    def zoomImage(self, image, xcenter, ycenter, xzoom, yzoom):
        return zoomImage(image, xcenter, ycenter, xzoom, yzoom, self._minZoomPercent, self._maxZoomPercent, self._tmpResizeMat)

    def skipFrames(self, currentSongPosition):
        lastFrame = self._currentFrame;
        self._currentFrame = int((((currentSongPosition - self._startSongPosition) / self._syncLength) * self._numberOfFrames) % self._numberOfFrames)

        if(lastFrame != self._currentFrame):
            if(self._currentFrame == 0):
                self._image = self._firstImage
                self._log.debug("Setting firstframe %d", self._currentFrame)
            else:
                cv.SetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_POS_FRAMES, self._currentFrame)
                self._image = cv.QueryFrame(self._videoFile)
                zoom = abs((2 * float(self._currentFrame) / self._numberOfFrames) -1.0)
#                self._image = self.zoomImage(self._image, -0.25, -0.25, zoom, zoom)
                self._image = self.resizeImage(self._image)
            return True
        else:
            self._log.debug("Same frame %d currentSongPosition %f", self._currentFrame, currentSongPosition)
            return False

    def openFile(self):
        if (os.path.isfile(self._filename) == False):
            self._log.warning("Could not find file: %s in directory: %s", self._filename, os.getcwd())
            raise MediaError("File does not exist!")
        self._videoFile = cv.CaptureFromFile(self._filename)
        try:
            self._image = cv.QueryFrame(self._videoFile)
        except:
            self._log.warning("Exception while reading: %s", os.path.basename(self._filename))
            print "Exception while reading: " + os.path.basename(self._filename)
            raise MediaError("File caused exception!")
        if (self._image == None):
            self._log.warning("Could not read frames from: %s", os.path.basename(self._filename))
            print "Could not read frames from: " + os.path.basename(self._filename)
            raise MediaError("File could not be read!")
        try:
            self._image = self.resizeImage(self._image)
            self._firstImage = self._image
            self._numberOfFrames = int(cv.GetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_FRAME_COUNT))
            self._originalFrameRate = int(cv.GetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_FPS))
        except:
            self._log.warning("Exception while getting number of frames from: %s", os.path.basename(self._filename))
            raise MediaError("File caused exception!")
        self._originalTime = float(self._numberOfFrames) / self._originalFrameRate
        self._syncLength = self._midiTiming.guessMidiLength(self._originalTime)
        self._log.warning("Read file %s with %d frames, framerate %d and length %f guessed MIDI length %f", os.path.basename(self._filename), self._numberOfFrames, self._originalFrameRate, self._originalTime, self._syncLength)
        self._fileOk = True

class MediaError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)