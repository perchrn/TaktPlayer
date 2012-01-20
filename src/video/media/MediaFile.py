'''
Created on 12. okt. 2011

@author: pcn
'''
import os.path
import logging
from cv2 import cv
import numpy
from midi.MidiModulation import MidiModulation

def getEmptyImage(x, y):
    resizeMat = crateMat(x,y)
    return resizeImage(cv.CreateImage((x,y), cv.IPL_DEPTH_8U, 3), resizeMat)

def crateMat(width, heigth):
    return cv.CreateMat(heigth, width, cv.CV_8UC3)

def crateMask(width, heigth):
    return cv.CreateMat(heigth, width, cv.CV_8UC1)

def copyImage(image):
    return cv.CloneImage(image)

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

def blurImage(image, value, tmpMat):
    if(value < 0.01):
        return image
    xSize = 2 + int(value * 8)
    ySize = 2 + int(value * 6)
    cv.Smooth(image, tmpMat, cv.CV_BLUR, xSize, ySize)
    return tmpMat

def blurMultiply(image, value, tmpMat1, tmpMat2):
    if(value < 0.01):
        return image
    xSize = 2 + int(value * 8)
    ySize = 2 + int(value * 6)
    cv.Smooth(image, tmpMat1, cv.CV_BLUR, xSize, ySize)
    cv.Mul(image, tmpMat1, tmpMat2, 0.006)
    return tmpMat2

class FadeMode():
    Black, White = range(2)

def fadeImage(image, value, mode, tmpMat):
    if(mode == FadeMode.White):
        cv.ConvertScaleAbs(image, tmpMat, value, (1.0-value) * 256)
    else: #FadeMode.Black
        cv.ConvertScaleAbs(image, tmpMat, value, 0.0)
    return tmpMat

def contrastBrightness(image, contrast, brightness, tmpMat):
    contrast = (2 * contrast) -1.0
    brightnessVal = 256 * brightness
    if(contrast < 0.0):
        contrastVal = 1.0 + contrast
    elif(contrast > 0.0):
        contrastVal = 1.0 + (9 * contrast)
    else:
        contrastVal = 1.0
    if((contrast > -0.01) and (contrast < 0.01) and (brightness < 0.1) and (brightness > -0.1)):
        return image
    else:
        cv.ConvertScaleAbs(image, tmpMat, contrastVal, brightnessVal)
        return tmpMat

def hueSaturationBrightness(image, rotate, saturation, brightness, tmpMat):
    cv.CvtColor(image, tmpMat, cv.CV_RGB2HSV)
    rotCalc = (rotate * 512) - 256
    satCalc = (saturation * 512) - 256
    brightCalc = (brightness * 512) - 256
    rgbColor = cv.CV_RGB(rotCalc, satCalc, brightCalc)
    cv.SubS(tmpMat, rgbColor, image)
    cv.CvtColor(image, tmpMat, cv.CV_HSV2RGB)
    return tmpMat

class ColorizeMode():
    Add, Subtract, SubtractFrom, Multiply = range(4)

def colorize(image, red, green, blue, mode, amount, tmpMat):
    if((mode == ColorizeMode.Add) or (mode == ColorizeMode.Subtract)):
        redCalc = 256 * (red * amount)
        greenCalc = 256 * (green * amount)
        blueCalc = 256 * (blue * amount)
    else:
        amount = 1.0 - amount
        redCalc = 256 * (red + ((1.0 - red) * amount))
        greenCalc = 256 * (green  + ((1.0 - green) * amount))
        blueCalc = 256 * (blue  + ((1.0 - blue) * amount))
    rgbColor = cv.CV_RGB(redCalc, greenCalc, blueCalc)
#    print "DEBUG color: " + str((red, green, blue)) + " amount: " + str(amount)

    if(mode == ColorizeMode.Add):
        cv.AddS(image, rgbColor, tmpMat)
    elif(mode == ColorizeMode.Subtract):
        cv.SubS(image, rgbColor, tmpMat)
    elif(mode == ColorizeMode.SubtractFrom):
        cv.SubRS(image, rgbColor, tmpMat)
    elif(mode == ColorizeMode.Multiply):
        cv.Set(tmpMat, rgbColor)
        cv.Mul(image, tmpMat, tmpMat, 0.003)
    else:
        cv.AddS(image, rgbColor, tmpMat)
    return tmpMat

def invert(image, amount, tmpMat):
    brightnessVal = -256 * amount
    if((brightnessVal > -0.01) and (brightnessVal < 0.01)):
        return image
    else:
        cv.ConvertScaleAbs(image, tmpMat, 1.0, brightnessVal)
        return tmpMat

def blackAndWhite(image1, threshold, mixMask, mixMat):
    threshold = 256 * threshold
    cv.CvtColor(image1, mixMask, cv.CV_BGR2GRAY);
    cv.CmpS(mixMask, threshold, mixMask, cv.CV_CMP_GT)
    cv.Merge(mixMask, mixMask, mixMask, None, mixMat)
    return mixMat

def mixImageSelfMask(image1, image2, mixMask, mixMat):
    imageCopy = crateMat(800, 600)
    cv.Copy(image2, imageCopy)
    cv.CvtColor(image2, mixMask, cv.CV_BGR2GRAY);
    cv.CmpS(mixMask, 10, mixMask, cv.CV_CMP_GT)
#    cv.Copy(imageCopy, image1, mixMask)
#    return imageCopy
    cv.Merge(mixMask, mixMask, mixMask, None, mixMat)
    cv.Sub(image1, mixMat, mixMat)
    cv.Add(mixMat, imageCopy, image2)
    return image2

def mixImagesAdd(image1, image2, mixMat):
    cv.Add(image1, image2, mixMat)
    return mixMat

def mixImagesMultiply(image1, image2, mixMat):
    cv.Mul(image1, image2, mixMat, 0.003)
    return mixMat

class MixMode:
    (Add, Multiply, LumaKey, Replace) = range(4)

def mixImages(mode, image1, image2, mixMat, mixMask):
    if(mode == MixMode.Add):
        return mixImagesAdd(image1, image2, mixMat)
    if(mode == MixMode.Multiply):
        return mixImagesMultiply(image1, image2, mixMat)
    if(mode == MixMode.LumaKey):
        return mixImageSelfMask(image1, image2, mixMask, mixMat)
    if(mode == MixMode.Replace):
        return image2

def imageToArray(image):
    return numpy.asarray(image)

def imageFromArray(array):
    return cv.fromarray(array)

class MediaFile(object):
    def __init__(self, fileName, midiTimingClass, configurationTree):
        self._configurationTree = configurationTree
        self.setFileName(fileName)
        self._midiTiming = midiTimingClass
        self._internalResolutionX =  self._configurationTree.getValueFromPath("Global.ResolutionX")
        self._internalResolutionY =  self._configurationTree.getValueFromPath("Global.ResolutionY")
        self._tmpMat1 = crateMat(self._internalResolutionX, self._internalResolutionY)
        self._tmpMat2 = crateMat(self._internalResolutionX, self._internalResolutionY)
        self._tmpMask = crateMask(self._internalResolutionX, self._internalResolutionY)
        self._fileOk = False
        self._image = None
        self._captureImage = None
        self._firstImage = None
        self._secondImage = None
        self._bufferedImageList = None
        self._numberOfFrames = 0
        self._originalFrameRate = 25
        self._originalTime = 0.0
        self._currentFrame = 0;
        self._startSongPosition = 0.0

        self._minZoomPercent = 0.25
        self._maxZoomPercent = 4.0

        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._log.setLevel(logging.WARNING)

        self._configurationTree.addTextParameterStatic("Type", self.getType())
        self._configurationTree.addTextParameterStatic("FileName", self._filename)
        self._midiModulation = MidiModulation(self._configurationTree.addChildUnique("Modulation"), self._midiTiming)
        self._setupConfiguration()
        self._getConfiguration()

    def _setupConfiguration(self):
        self._midiModulation.setModulationReceiver("PlayBack", "None")
        self._midiModulation.setModulationReceiver("FadeInOut", "None")
        self._midiModulation.setModulationReceiver("Level", "None")
        self._midiModulation.setModulationReceiver("EffectX", "None")
        self._midiModulation.setModulationReceiver("EffectY", "None")
        self._midiModulation.setModulationReceiver("EffectAmount", "MidiChannel.Controller.ModWheel")
        self._midiModulation.setModulationReceiver("EffectArgument1", "None")
        self._midiModulation.setModulationReceiver("EffectArgument2", "None")
        self._playbackModulationId = -1
        self._fadeModulationId = -1
        self._levelModulationId = -1
        self._effectXModulationId = -1
        self._effectYModulationId = -1
        self._effectAmountModulationId = -1
        self._effectArgument1ModulationId = -1
        self._effectArgument2ModulationId = -1

        self._configurationTree.addFloatParameter("SyncLength", 4.0) #Default one bar (re calculated on load)
        self._configurationTree.addFloatParameter("QuantizeLength", 4.0)#Default one bar
        self._configurationTree.addTextParameter("MixMode", "Add")#Default Add
        self._configurationTree.addTextParameter("FadeMode", "Black")#Default Add
        self._syncLength = -1.0
        self._quantizeLength = -1.0
        self._mixMode = MixMode.Add
        self._fadeMode = FadeMode.Black

    def getFadeModulation(self, songPosition, midiChannelStateHolder, midiNoteStateHolder):
        return self._midiModulation.getModlulationValue(self._fadeModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)

    def getLevelModulation(self, songPosition, midiChannelStateHolder, midiNoteStateHolder):
        return self._midiModulation.getModlulationValue(self._levelModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)

    def getEffectModulations(self, songPosition, midiChannelStateHolder, midiNoteStateHolder):
        amount =  self._midiModulation.getModlulationValue(self._effectAmountModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        arg1 =  self._midiModulation.getModlulationValue(self._effectArgument1ModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        arg2 =  self._midiModulation.getModlulationValue(self._effectArgument2ModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        xval =  self._midiModulation.getModlulationValue(self._effectXModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        yval =  self._midiModulation.getModlulationValue(self._effectYModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        return (amount, arg1, arg2, xval, yval)

    def _getConfiguration(self):
        self._playbackModulationId = self._midiModulation.connectModulation("PlayBack")
        self._fadeModulationId = self._midiModulation.connectModulation("FadeInOut")
        self._levelModulationId = self._midiModulation.connectModulation("Level")
        self._effectXModulationId = self._midiModulation.connectModulation("EffectX")
        self._effectYModulationId = self._midiModulation.connectModulation("EffectY")
        self._effectAmountModulationId = self._midiModulation.connectModulation("EffectAmount")
        self._effectArgument1ModulationId = self._midiModulation.connectModulation("EffectArgument1")
        self._effectArgument2ModulationId = self._midiModulation.connectModulation("EffectArgument2")

        self.setMidiLengthInBeats(self._configurationTree.getValue("SyncLength"))
        self.setQuantizeInBeats(self._configurationTree.getValue("QuantizeLength"))

        mixMode = self._configurationTree.getValue("MixMode")
        if(mixMode == "Add"):
            self._mixMode = MixMode.Add
        elif(mixMode == "Multiply"):
            self._mixMode = MixMode.Multiply
        elif(mixMode == "LumaKey"):
            self._mixMode = MixMode.LumaKey
        elif(mixMode == "Replace"):
            self._mixMode = MixMode.Replace
        else:
            self._mixMode = MixMode.Add #Defaults to add

        fadeMode = self._configurationTree.getValue("FadeMode")
        if(fadeMode == "Black"):
            self._fadeMode = FadeMode.Black
        elif(fadeMode == "White"):
            self._fadeMode = FadeMode.White
        else:
            self._fadeMode = FadeMode.Black #Defaults to add

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print "mediaFile config is updated..."
            self._getConfiguration()
            self._midiModulation.checkAndUpdateFromConfiguration()
            self._configurationTree.resetConfigurationUpdated()

    def close(self):
        pass

    def getType(self):
        return "Unknown"

    def equalFileName(self, fileName):
        return self._filename == os.path.normcase(fileName)

    def getFileName(self):
        return self._filename

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

    def setMidiLengthInBeats(self, midiLength):
        syncLength = midiLength * self._midiTiming.getTicksPerQuarteNote()
        roundLength = round(syncLength)
        if(abs(syncLength - roundLength) < 0.01):
            syncLength = roundLength
        self._syncLength = syncLength

    def getQuantize(self):
        return self._quantizeLength

    def setQuantizeInBeats(self, midiLength):
        quantizeLength = midiLength * self._midiTiming.getTicksPerQuarteNote()
        roundLength = round(quantizeLength)
        if(abs(quantizeLength - roundLength) < 0.01):
            quantizeLength = roundLength
        self._quantizeLength = quantizeLength

    def setStartPosition(self, startSpp):
        self._startSongPosition = startSpp

    def restartSequence(self):
        pass

    def getCurrentFramePos(self):
        return self._currentFrame

    def zoomImage(self, image, xcenter, ycenter, xzoom, yzoom, tmpMat):
        return zoomImage(image, xcenter, ycenter, xzoom, yzoom, self._minZoomPercent, self._maxZoomPercent, tmpMat)

    def _getFadeValue(self, currentSongPosition, midiNoteState, midiChannelState):
        fadeValue = self.getFadeModulation(currentSongPosition, midiChannelState, midiNoteState)
        levelValue = self.getLevelModulation(currentSongPosition, midiChannelState, midiNoteState)
        fadeValue = (1.0 - fadeValue) * (1.0 - levelValue)
        return fadeValue

    def _aplyEffects(self, currentSongPosition, midiChannelState, midiNoteState, fadeValue):
        if((self._fadeMode == FadeMode.Black) and (fadeValue < 0.01)):
            self._image = None
        else:

            effectAmount, effectArg1, effectArg2, effectX, effectY = self.getEffectModulations(currentSongPosition, midiChannelState, midiNoteState) #@UnusedVariable

#            zoom = abs((2 * float(self._currentFrame) / self._numberOfFrames) -1.0)
#            self._image = self.zoomImage(self._captureImage, -0.25, -0.25, zoom, zoom, self._tmpMat1)
            self._image = resizeImage(self._captureImage, self._tmpMat1)
#            self._image = blurImage(self._image, effectAmount, self._tmpMat2)
            self._image = blurMultiply(self._image, effectAmount, self._tmpMat2, self._tmpMat1)
#            self._image = hueSaturationBrightness(self._image, effectArg1, effectArg2, effectX, self._tmpMat2)
#            self._image = colorize(self._image, effectArg1, effectArg2, effectX, ColorizeMode.Add, effectAmount, self._tmpMat2)
#            self._image = contrastBrightness(self._image, effectAmount, effectArg1, self._tmpMat1)
#            self._image = invert(self._image, effectAmount, self._tmpMat1)
#            self._image = blackAndWhite(self._image, effectAmount, self._tmpMask, self._tmpMat1)
    
            if(fadeValue < 0.99):
                self._image = fadeImage(self._image, fadeValue, self._fadeMode, self._tmpMat1)
        

    def skipFrames(self, currentSongPosition, midiNoteState, midiChannelState):
        pass

    def openVideoFile(self, midiLength):
        if (os.path.isfile(self._filename) == False):
            self._log.warning("Could not find file: %s in directory: %s", self._filename, os.getcwd())
            raise MediaError("File does not exist!")
        self._videoFile = cv.CaptureFromFile(self._filename)
        try:
            self._captureImage = cv.QueryFrame(self._videoFile)
            self._firstImage = copyImage(self._captureImage)
            self._captureImage = cv.QueryFrame(self._videoFile)
            self._secondImage = copyImage(self._captureImage)
            self._captureImage = self._firstImage
        except:
            self._log.warning("Exception while reading: %s", os.path.basename(self._filename))
            print "Exception while reading: " + os.path.basename(self._filename)
            raise MediaError("File caused exception!")
        if (self._captureImage == None):
            self._log.warning("Could not read frames from: %s", os.path.basename(self._filename))
            print "Could not read frames from: " + os.path.basename(self._filename)
            raise MediaError("File could not be read!")
        try:
            self._numberOfFrames = int(cv.GetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_FRAME_COUNT))
            self._originalFrameRate = int(cv.GetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_FPS))
        except:
            self._log.warning("Exception while getting number of frames from: %s", os.path.basename(self._filename))
            raise MediaError("File caused exception!")
        if(self._numberOfFrames < 20):
            try:
                self._bufferedImageList = []
                self._bufferedImageList.append(self._firstImage)
                self._bufferedImageList.append(self._secondImage)
                for i in range(self._numberOfFrames - 2): #@UnusedVariable
                    self._captureImage = cv.QueryFrame(self._videoFile)
                    self._bufferedImageList.append(copyImage(self._captureImage))
            except:
                self._log.warning("Exception while reading: %s", os.path.basename(self._filename))
                print "Exception while reading: " + os.path.basename(self._filename)
                raise MediaError("File caused exception!")
        self._captureImage = self._firstImage
        self._originalTime = float(self._numberOfFrames) / self._originalFrameRate
        if(midiLength != None): # Else we get length from configuration or default.
            if(midiLength <= 0.0):
                midiLength = self._midiTiming.guessMidiLength(self._originalTime)
            self.setMidiLengthInBeats(midiLength)
        self._log.warning("Read file %s with %d frames, framerate %d and length %f guessed MIDI length %f", os.path.basename(self._filename), self._numberOfFrames, self._originalFrameRate, self._originalTime, self._syncLength)
        self._fileOk = True

    def openFile(self, midiLength):
        pass

    def mixWithImage(self, image):
        if(self._image == None):
            return image
        else:
            return mixImages(self._mixMode, image, self._image, self._tmpMat1, self._tmpMask)
    
class ImageFile(MediaFile):
    def __init__(self, fileName, midiTimingClass, configurationTree):
        MediaFile.__init__(self, fileName, midiTimingClass, configurationTree)

    def getType(self):
        return "Image"

    def close(self):
        pass

    def skipFrames(self, currentSongPosition, midiNoteState, midiChannelState):
        fadeValue = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState)
        if(fadeValue < 0.01):
            self._image = None
            return
        self._aplyEffects(currentSongPosition, midiChannelState, midiNoteState, fadeValue)

    def openFile(self, midiLength):
        if (os.path.isfile(self._filename) == False):
            self._log.warning("Could not find file: %s in directory: %s", self._filename, os.getcwd())
            raise MediaError("File does not exist!")
        try:
            self._captureImage = cv.LoadImage(self._filename)
        except:
            self._log.warning("Exception while reading: %s", os.path.basename(self._filename))
            print "Exception while reading: " + os.path.basename(self._filename)
            raise MediaError("File caused exception!")
        if (self._captureImage == None):
            self._log.warning("Could not read frames from: %s", os.path.basename(self._filename))
            print "Could not read frames from: " + os.path.basename(self._filename)
            raise MediaError("File could not be read!")
        self._firstImage = self._captureImage
        self._originalTime = 1.0
        self._log.warning("Read image file %s", os.path.basename(self._filename))
        self._fileOk = True

class ImageSequenceFile(MediaFile):
    class Mode:
        Time, ReTrigger, Controller = range(3)

    def __init__(self, fileName, midiTimingClass, configurationTree):
        MediaFile.__init__(self, fileName, midiTimingClass, configurationTree)
        self._triggerCounter = 0
        self._firstTrigger = True
        self._sequenceMode = ImageSequenceFile.Mode.Time
        self._configurationTree.addTextParameter("SequenceMode", "Time")

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
        seqMode = self._configurationTree.getValue("SequenceMode")
        if(seqMode == "ReTrigger"):
            self._sequenceMode = ImageSequenceFile.Mode.ReTrigger
        elif(seqMode == "Controller"):
            self._sequenceMode = ImageSequenceFile.Mode.Controller
        else:
            self._sequenceMode = ImageSequenceFile.Mode.Time #Defaults to time

    def close(self):
        pass

    def getType(self):
        return "ImageSequence"

    def restartSequence(self):
        self._firstTrigger = True
        self._startSongPosition = 0.0
        self._triggerCounter = 0

    def setStartPosition(self, startSpp):
        lastSpp = self._startSongPosition
        if(startSpp != lastSpp):
            print "Trigger "
            if(self._firstTrigger == True):
                self._firstTrigger = False
            else:
                self._triggerCounter += 1
            print "TriggerCount: " + str(self._triggerCounter) + " startSPP: " + str(startSpp)
        self._startSongPosition = startSpp

    def getPlaybackModulation(self, songPosition, midiChannelStateHolder, midiNoteStateHolder):
        return self._midiModulation.getModlulationValue(self._playbackModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)

    def skipFrames(self, currentSongPosition, midiNoteState, midiChannelState):
        fadeValue = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState)
        if((self._fadeMode == FadeMode.Black) and (fadeValue < 0.01)):
            self._image = None
            return

        lastFrame = self._currentFrame
        
        if(self._sequenceMode == ImageSequenceFile.Mode.Time):
            self._currentFrame = (int((currentSongPosition - self._startSongPosition) / self._syncLength) % self._numberOfFrames)
        elif(self._sequenceMode == ImageSequenceFile.Mode.ReTrigger):
            self._currentFrame =  (self._triggerCounter % self._numberOfFrames)
        elif(self._sequenceMode == ImageSequenceFile.Mode.Controller):
            self._currentFrame = int(self.getPlaybackModulation(currentSongPosition, midiChannelState, midiNoteState) * self._numberOfFrames)

        if(lastFrame != self._currentFrame):
            if(self._bufferedImageList != None):
                self._captureImage = self._bufferedImageList[self._currentFrame]
                print "Buffered image!!!"
            else:
                cv.SetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_POS_FRAMES, self._currentFrame)
                if(self._currentFrame == 0):
                    self._captureImage = self._firstImage
                    self._log.debug("Setting firstframe %d", self._currentFrame)
                elif(self._currentFrame == 1):
                    self._captureImage = self._secondImage
                    self._log.debug("Setting secondframe %d", self._currentFrame)
                else:
                    self._captureImage = cv.QueryFrame(self._videoFile)
                    if(self._captureImage == None):
                        self._captureImage = self._firstImage
            self._aplyEffects(currentSongPosition, midiChannelState, midiNoteState, fadeValue)
            return True
        else:
            self._log.debug("Same frame %d currentSongPosition %f", self._currentFrame, currentSongPosition)
            self._aplyEffects(currentSongPosition, midiChannelState, midiNoteState, fadeValue)
            return False

    def openFile(self, midiLength):
        self.openVideoFile(midiLength)

class VideoLoopFile(MediaFile):
    class Mode:
        Normal, Reverse, PingPong, PingPongReverse, DontLoop, DontLoopReverse = range(6)

    def __init__(self, fileName, midiTimingClass, configurationTree):
        MediaFile.__init__(self, fileName, midiTimingClass, configurationTree)
        self._loopMode = VideoLoopFile.Mode.Normal
        self._configurationTree.addTextParameter("LoopMode", "Normal")

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
        loopMode = self._configurationTree.getValue("LoopMode")
        if(loopMode == "Normal"):
            self._loopMode = VideoLoopFile.Mode.Normal
        elif(loopMode == "Reverse"):
            self._loopMode = VideoLoopFile.Mode.Reverse
        elif(loopMode == "PingPong"):
            self._loopMode = VideoLoopFile.Mode.PingPong
        elif(loopMode == "PingPongReverse"):
            self._loopMode = VideoLoopFile.Mode.PingPongReverse
        elif(loopMode == "DontLoop"):
            self._loopMode = VideoLoopFile.Mode.DontLoop
        elif(loopMode == "DontLoopReverse"):
            self._loopMode = VideoLoopFile.Mode.DontLoopReverse
        else:
            self._loopMode = VideoLoopFile.Mode.Normal #Defaults to normal

    def close(self):
        pass

    def getType(self):
        return "VideoLoop"

    def skipFrames(self, currentSongPosition, midiNoteState, midiChannelState):
        fadeValue = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState)
        if((self._fadeMode == FadeMode.Black) and (fadeValue < 0.01)):
            self._image = None
            return
        lastFrame = self._currentFrame

        framePos = int(((currentSongPosition - self._startSongPosition) / self._syncLength) * self._numberOfFrames)
        if(self._loopMode == VideoLoopFile.Mode.Normal):
            self._currentFrame = framePos % self._numberOfFrames
        elif(self._loopMode == VideoLoopFile.Mode.Reverse):
            self._currentFrame = -framePos % self._numberOfFrames
        elif(self._loopMode == VideoLoopFile.Mode.PingPong):
            self._currentFrame = abs(((framePos + self._numberOfFrames) % (2 * self._numberOfFrames)) - self._numberOfFrames)
        elif(self._loopMode == VideoLoopFile.Mode.PingPongReverse):
            self._currentFrame = abs((framePos % (2 * self._numberOfFrames)) - self._numberOfFrames)
        elif(self._loopMode == VideoLoopFile.Mode.DontLoop):
            if(framePos < self._numberOfFrames):
                self._currentFrame = framePos
            else:
                self._image = None
        elif(self._loopMode == VideoLoopFile.Mode.DontLoopReverse):
            if(framePos < self._numberOfFrames):
                self._currentFrame = self._numberOfFrames - 1 - framePos
            else:
                self._image = None
        else: #Normal
            self._currentFrame = framePos % self._numberOfFrames

        if(lastFrame != self._currentFrame):
            cv.SetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_POS_FRAMES, self._currentFrame)
            if(self._currentFrame == 0):
                self._captureImage = self._firstImage
#                cv.SetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_POS_FRAMES, -1)
                self._log.debug("Setting firstframe %d", self._currentFrame)
            elif(self._currentFrame == 1):
                self._captureImage = self._secondImage
                self._log.debug("Setting secondframe %d", self._currentFrame)
            else:
                self._captureImage = cv.QueryFrame(self._videoFile)
                if(self._captureImage == None):
                    self._captureImage = self._firstImage
            self._aplyEffects(currentSongPosition, midiChannelState, midiNoteState, fadeValue)
            return True
        else:
            self._log.debug("Same frame %d currentSongPosition %f", self._currentFrame, currentSongPosition)
            self._aplyEffects(currentSongPosition, midiChannelState, midiNoteState, fadeValue)
            return False

    def openFile(self, midiLength):
        self.openVideoFile(midiLength)

class MediaError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)