'''
Created on 12. okt. 2011

@author: pcn
'''
import os.path
import logging
from cv2 import cv #@UnresolvedImport
import numpy
from midi.MidiModulation import MidiModulation
from video.Effects import createMat, getEffectByName, getEmptyImage, createMask,\
    copyImage
import hashlib
from video.media.MediaFileModes import MixMode, VideoLoopMode, ImageSequenceMode,\
    FadeMode, getMixModeFromName, ModulationValueMode,\
    getModulationValueModeFromName, KinectMode
import math
from utilities.FloatListText import textToFloatValues
try:
    import freenect
except:
    freenect = None

windowName = "TAKT Player"
def createCvWindow(fullScreenMode, sizeX, sizeY, posX=-1, posY=-1):
    if(fullScreenMode == "off"):
        cv.NamedWindow(windowName, cv.CV_WINDOW_NORMAL)
        cv.ResizeWindow(windowName, sizeX, sizeY)
        if(posX >= 0 and posY >=0):
            cv.MoveWindow(windowName, posX, posY)
    else:
        cv.NamedWindow(windowName, cv.CV_WINDOW_FULLSCREEN)

def showCvImage(image):
    cv.ShowImage(windowName, image)

def hasCvWindowStoped():
    k = cv.WaitKey(1);
    if k == 27: #Escape
        return True
    return False

def resizeImage(image, resizeMat):
    cv.Resize(image, resizeMat)
    return resizeMat

def scaleAndSave(image, osFileName, resizeMat):
    cv.Resize(image, resizeMat)
    cv.SaveImage(osFileName, resizeMat)

def fadeImage(image, value, mode, tmpMat):
    if(mode == FadeMode.White):
        cv.ConvertScaleAbs(image, tmpMat, value, (1.0-value) * 256)
    else: #FadeMode.Black
        cv.ConvertScaleAbs(image, tmpMat, value, 0.0)
    return tmpMat

def mixImageSelfMask(image1, image2, mixMask, mixMat1, whiteMode):
    cv.Copy(image2, mixMat1)
    cv.CvtColor(image2, mixMask, cv.CV_BGR2GRAY);
    if(whiteMode == True):
        cv.CmpS(mixMask, 250, mixMask, cv.CV_CMP_LT)
    else:
        cv.CmpS(mixMask, 5, mixMask, cv.CV_CMP_GT)
    cv.Copy(mixMat1, image1, mixMask)
    return image1

def mixImagesAdd(image1, image2, mixMat):
    cv.Add(image1, image2, mixMat)
    return mixMat

def mixImagesMultiply(image1, image2, mixMat):
    cv.Mul(image1, image2, mixMat, 0.004)
    return mixMat

def mixImages(mode, image1, image2, mixMat1, mixMask):
    if(mode == MixMode.Add):
        return mixImagesAdd(image1, image2, mixMat1)
    elif(mode == MixMode.Multiply):
        return mixImagesMultiply(image1, image2, mixMat1)
    elif(mode == MixMode.LumaKey):
        return mixImageSelfMask(image1, image2, mixMask, mixMat1, False)
    elif(mode == MixMode.WhiteLumaKey):
        return mixImageSelfMask(image1, image2, mixMask, mixMat1, True)
    elif(mode == MixMode.Replace):
        return image2
    else:
        return mixImagesAdd(image1, image2, mixMat1)

def imageToArray(image):
    return numpy.asarray(image)

def imageFromArray(array):
    return cv.fromarray(array)

class MediaFile(object):
    def __init__(self, fileName, midiTimingClass, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        self._configurationTree = configurationTree
        self._effectsConfigurationTemplates = effectsConfiguration
        self._effectImagesConfigurationTemplates = effectImagesConfig
        self._guiCtrlStateHolder = guiCtrlStateHolder
        self._mediaFadeConfigurationTemplates = fadeConfiguration
        self._videoDirectory = videoDir
        self.setFileName(fileName)
        self._midiTiming = midiTimingClass
        self._internalResolutionX =  internalResolutionX
        self._internalResolutionY =  internalResolutionY
        self._resizeMat = createMat(self._internalResolutionX, self._internalResolutionY)
        self._fadeMat = createMat(self._internalResolutionX, self._internalResolutionY)
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

        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._log.setLevel(logging.WARNING)

        self._configurationTree.addTextParameterStatic("Type", self.getType())
        self._configurationTree.addTextParameterStatic("FileName", self._cfgFileName)
        self._midiModulation = None
        self._setupConfiguration()

    def _setupConfiguration(self):
        self._configurationTree.addFloatParameter("SyncLength", 4.0) #Default one bar (re calculated on load)
        self._configurationTree.addFloatParameter("QuantizeLength", 4.0)#Default one bar
        self._configurationTree.addTextParameter("MixMode", "Add")#Default Add
        self._defaultEffect1SettingsName = "MediaDefault1"
        self._configurationTree.addTextParameter("Effect1Config", self._defaultEffect1SettingsName)#Default MediaDefault1
        self._defaultEffect2SettingsName = "MediaDefault2"
        self._configurationTree.addTextParameter("Effect2Config", self._defaultEffect2SettingsName)#Default MediaDefault2
        self._defaultFadeSettingsName = "Default"
        self._configurationTree.addTextParameter("FadeConfig", self._defaultFadeSettingsName)#Default Default
        self._configurationTree.addTextParameter("ModulationValuesMode", "KeepOld")#Default KeepOld
        
        self._syncLength = -1.0
        self._quantizeLength = -1.0
        self._mixMode = MixMode.Add

        self._modulationRestartMode = ModulationValueMode.KeepOld
        self._effect1StartControllerValues = (None, None, None, None, None)
        self._effect2StartControllerValues = (None, None, None, None, None)
        self._effect1StartValues = (0.0, 0.0, 0.0, 0.0, 0.0)
        self._effect2StartValues = (0.0, 0.0, 0.0, 0.0, 0.0)
        self._effect1OldValues = (0.0, 0.0, 0.0, 0.0, 0.0)
        self._effect2OldValues = (0.0, 0.0, 0.0, 0.0, 0.0)
        self._effect1 = None
        self._effect2 = None
        self._effect1Settings = None
        self._effect2Settings = None

    def _getConfiguration(self):
        oldEffect1Name = "None"
        oldEffect1Values = "0.0|0.0|0.0|0.0|0.0"
        if(self._effect1Settings != None):
            oldEffect1Name = self._effect1Settings.getEffectName()
            oldEffect1Values = self._effect1Settings.getStartValuesString()
        self._effect1ModulationTemplate = self._configurationTree.getValue("Effect1Config")
        self._effect1Settings = self._effectsConfigurationTemplates.getTemplate(self._effect1ModulationTemplate)
        if(self._effect1Settings == None):
            self._effect1Settings = self._effectsConfigurationTemplates.getTemplate(self._defaultEffect1SettingsName)
        self._effect1 = getEffectByName(self._effect1Settings.getEffectName(), self._configurationTree, self._effectImagesConfigurationTemplates, self._internalResolutionX, self._internalResolutionY)
        if((oldEffect1Name != self._effect1Settings.getEffectName()) or (oldEffect1Values != self._effect1Settings.getStartValuesString())):
            self._effect1StartValues = self._effect1Settings.getStartValues()
            self._effect1OldValues = self._effect1StartValues

        oldEffect2Name = "None"
        oldEffect2Values = "0.0|0.0|0.0|0.0|0.0"
        if(self._effect2Settings != None):
            oldEffect2Name = self._effect2Settings.getEffectName()
            oldEffect2Values = self._effect2Settings.getStartValuesString()
        self._effect2ModulationTemplate = self._configurationTree.getValue("Effect2Config")
        self._effect2Settings = self._effectsConfigurationTemplates.getTemplate(self._effect2ModulationTemplate)
        if(self._effect2Settings == None):
            self._effect2Settings = self._effectsConfigurationTemplates.getTemplate(self._defaultEffect2SettingsName)
        self._effect2 = getEffectByName(self._effect2Settings.getEffectName(), self._configurationTree, self._effectImagesConfigurationTemplates, self._internalResolutionX, self._internalResolutionY)
        if((oldEffect2Name != self._effect2Settings.getEffectName()) or (oldEffect2Values != self._effect2Settings.getStartValuesString())):
            self._effect2StartValues = self._effect2Settings.getStartValues()
            self._effect2OldValues = self._effect2StartValues

        self._fadeAndLevelTemplate = self._configurationTree.getValue("FadeConfig")
        self._fadeAndLevelSettings = self._mediaFadeConfigurationTemplates.getTemplate(self._fadeAndLevelTemplate)
        if(self._fadeAndLevelSettings == None):
            self._fadeAndLevelSettings = self._mediaFadeConfigurationTemplates.getTemplate(self._defaultFadeSettingsName)

        self.setMidiLengthInBeats(self._configurationTree.getValue("SyncLength"))
        self.setQuantizeInBeats(self._configurationTree.getValue("QuantizeLength"))

        mixMode = self._configurationTree.getValue("MixMode")
        self._mixMode = getMixModeFromName(mixMode)

        modulationRestartMode = self._configurationTree.getValue("ModulationValuesMode")
        self._modulationRestartMode = getModulationValueModeFromName(modulationRestartMode)

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print "mediaFile config is updated..."
            self._getConfiguration()
            if(self._midiModulation != None):
                self._midiModulation.checkAndUpdateFromConfiguration()
            self._configurationTree.resetConfigurationUpdated()

    def close(self):
        pass

    def getType(self):
        return "Unknown"

    def equalFileName(self, fileName):
        return self._cfgFileName.encode("utf-8") == fileName.encode("utf-8")

    def getFileName(self):
        return self._cfgFileName

    def setFileName(self, fileName):
        self._cfgFileName = fileName
        self._fullFilePath = os.path.join(os.path.normpath(self._videoDirectory), os.path.normpath(self._cfgFileName))

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

    def noteJustTriggered(self, songPosition, midiNoteStateHolder, midiChannelStateHolder):
        self._guiCtrlStateHolder.resetState()
        if(self._modulationRestartMode != ModulationValueMode.RawInput):
            self._effect1StartControllerValues = self._effect1Settings.getValues(songPosition, midiChannelStateHolder, midiNoteStateHolder)
            self._effect2StartControllerValues = self._effect2Settings.getValues(songPosition, midiChannelStateHolder, midiNoteStateHolder)
        else:
            self._effect1StartControllerValues = (None, None, None, None, None)
            self._effect2StartControllerValues = (None, None, None, None, None)
        if(self._modulationRestartMode == ModulationValueMode.ResetToDefault):
            self._effect1StartValues = self._effect1Settings.getStartValues()
            self._effect2StartValues = self._effect2Settings.getStartValues()
        else: #KeepOldValues
            self._effect1StartValues = self._effect1OldValues
            self._effect2StartValues = self._effect2OldValues

        if(self._effect1 != None):
            self._effect1.reset()
        if(self._effect2 != None):
            self._effect2.reset()

    def _getFadeValue(self, currentSongPosition, midiNoteState, midiChannelState):
        noteDone = False
        fadeMode, fadeValue, levelValue = self._fadeAndLevelSettings.getValues(currentSongPosition, midiChannelState, midiNoteState)
        if(fadeValue > 0.999999):
            noteDone = True
        fadeValue = (1.0 - fadeValue) * (1.0 - levelValue)
        return fadeMode, fadeValue, noteDone

    def getEffectState(self):
        guiEffectValuesString = str(self._guiCtrlStateHolder.getGuiContollerState(0)) + ";"
        valuesString = str(self._effect1OldValues) + ";"
        guiEffectValuesString += str(self._guiCtrlStateHolder.getGuiContollerState(5))
        valuesString += str(self._effect2OldValues)
        return (valuesString, guiEffectValuesString)

    def _applyOneEffect(self, image, effect, effectSettings, effectStartControllerValues, effectStartValues, songPosition, midiChannelStateHolder, midiNoteStateHolder, guiCtrlStateHolder, guiCtrlStateStartId):
        if(effectSettings != None):
            midiEffectVaules = effectSettings.getValues(songPosition, midiChannelStateHolder, midiNoteStateHolder)
            effectAmount, effectArg1, effectArg2, effectArg3, effectArg4 = guiCtrlStateHolder.updateWithGuiSettings(guiCtrlStateStartId, midiEffectVaules, effectStartValues)
            #print "DEBUG controller values" + str((effectAmount, effectArg1, effectArg2, effectArg3, effectArg4)) + " start" + str(effectStartControllerValues) + " sVals" + str(effectStartValues)
            #TODO: Add mode where values must pass start values?
            effectSCV0 = None
            if(effectAmount == effectStartControllerValues[0]):
                if(effectAmount != effectStartValues[0]):
                    effectAmount = effectStartValues[0]
                    effectSCV0 = effectStartControllerValues[0]
            effectSCV1 = None
            if(effectArg1 == effectStartControllerValues[1]):
                if(effectArg1 != effectStartValues[1]):
                    effectArg1 = effectStartValues[1]
                    effectSCV1 = effectStartControllerValues[1]
            effectSCV2 = None
            if(effectArg2 == effectStartControllerValues[2]):
                if(effectArg2 != effectStartValues[2]):
                    effectArg2 = effectStartValues[2]
                    effectSCV2 = effectStartControllerValues[2]
            effectSCV3 = None
            if(effectArg3 == effectStartControllerValues[3]):
                if(effectArg3 != effectStartValues[3]):
                    effectArg3 = effectStartValues[3]
                    effectSCV3 = effectStartControllerValues[3]
            effectSCV4 = None
            if(effectArg4 == effectStartControllerValues[4]):
                if(effectArg4 != effectStartValues[4]):
                    effectArg4 = effectStartValues[4]
                    effectSCV4 = effectStartControllerValues[4]
            if(effect != None):
                image = effect.applyEffect(image, effectAmount, effectArg1, effectArg2, effectArg3, effectArg4)
#            print "DEBUG modified values" + str((effectAmount, effectArg1, effectArg2, effectArg3, effectArg4))
            return (image, (effectAmount, effectArg1, effectArg2, effectArg3, effectArg4), (effectSCV0, effectSCV1, effectSCV2, effectSCV3, effectSCV4))
        else:
            return (image, (0.0, 0.0, 0.0, 0.0, 0.0), (None, None, None, None, None))

    def _applyEffects(self, currentSongPosition, midiChannelState, midiNoteState, fadeMode, fadeValue):
        imageSize = cv.GetSize(self._captureImage)
        if((imageSize[0] != self._internalResolutionX) or (imageSize[1] != self._internalResolutionY)):
            self._image = resizeImage(self._captureImage, self._resizeMat)
        else:
            self._image = copyImage(self._captureImage)

        (self._image, self._effect1OldValues, self._effect1StartControllerValues) = self._applyOneEffect(self._image, self._effect1, self._effect1Settings, self._effect1StartControllerValues, self._effect1StartValues, currentSongPosition, midiChannelState, midiNoteState, self._guiCtrlStateHolder, 0)
        (self._image, self._effect2OldValues, self._effect2StartControllerValues) = self._applyOneEffect(self._image, self._effect2, self._effect2Settings, self._effect2StartControllerValues, self._effect2StartValues, currentSongPosition, midiChannelState, midiNoteState, self._guiCtrlStateHolder, 5)

        if(fadeValue < 0.99):
            self._image = fadeImage(self._image, fadeValue, fadeMode, self._fadeMat)
        

    def skipFrames(self, currentSongPosition, midiNoteState, midiChannelState):
        pass

    def openVideoFile(self, midiLength):
        if (os.path.isfile(self._fullFilePath) == False):
            self._log.warning("Could not find file: %s in directory: %s", self._cfgFileName, self._videoDirectory)
            raise MediaError("File does not exist!")
        self._videoFile = cv.CaptureFromFile(self._fullFilePath.encode("utf-8"))
        try:
            self._captureImage = cv.QueryFrame(self._videoFile)
            self._firstImage = copyImage(self._captureImage)
            self._captureImage = cv.QueryFrame(self._videoFile)
            self._secondImage = copyImage(self._captureImage)
            self._captureImage = self._firstImage
        except:
            self._log.warning("Exception while reading: %s", os.path.basename(self._cfgFileName))
            print "Exception while reading: " + os.path.basename(self._cfgFileName)
            raise MediaError("File caused exception!")
        if (self._captureImage == None):
            self._log.warning("Could not read frames from: %s", os.path.basename(self._cfgFileName))
            print "Could not read frames from: " + os.path.basename(self._cfgFileName)
            raise MediaError("File could not be read!")
        try:
            self._numberOfFrames = int(cv.GetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_FRAME_COUNT))
            self._originalFrameRate = int(cv.GetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_FPS))
        except:
            self._log.warning("Exception while getting number of frames from: %s", os.path.basename(self._cfgFileName))
            raise MediaError("File caused exception!")
        if(self._numberOfFrames < 20):
            try:
                self._bufferedImageList = []
                self._bufferedImageList.append(self._firstImage)
                self._bufferedImageList.append(self._secondImage)
                for i in range(self._numberOfFrames - 2): #@UnusedVariable
                    self._captureImage = cv.QueryFrame(self._videoFile)
                    self._bufferedImageList.append(copyImage(self._captureImage))
                self._captureImage = self._firstImage
            except:
                self._log.warning("Exception while reading: %s", os.path.basename(self._cfgFileName))
                print "Exception while reading: " + os.path.basename(self._cfgFileName)
                raise MediaError("File caused exception!")
        self._originalTime = float(self._numberOfFrames) / self._originalFrameRate
        if(midiLength != None): # Else we get length from configuration or default.
            if(midiLength <= 0.0):
                midiLength = self._midiTiming.guessMidiLength(self._originalTime)
            self.setMidiLengthInBeats(midiLength)
        self._log.warning("Read file %s with %d frames, framerate %d and length %f guessed MIDI length %f", os.path.basename(self._cfgFileName), self._numberOfFrames, self._originalFrameRate, self._originalTime, self._syncLength)
        self._fileOk = True

    def getThumbnailId(self, videoPosition, forceUpdate):
        image = self._firstImage # Default
        if(videoPosition >= 0.00):
            if(((self.getType() == "VideoLoop") or (self.getType() == "ImageSequence")) and (videoPosition > 0.12)):
                if(videoPosition < 0.28):
                    videoPosition = 0.25
                elif(videoPosition < 0.41):
                    videoPosition = 0.33
                elif(videoPosition < 0.66):
                    videoPosition = 0.50
                elif(videoPosition < 0.87):
                    videoPosition = 0.75
                else:
                    videoPosition = 1.00
                cv.SetCaptureProperty(self._videoFile, cv.CV_CAP_PROP_POS_AVI_RATIO, videoPosition)
                image = cv.QueryFrame(self._videoFile)
        else:
            #Get current image...
            #print "DEBUG Using current image for thumb (pos < 0)"
            image = self._captureImage

        filenameHash = hashlib.sha224(self._cfgFileName.encode("utf-8")).hexdigest()
        if(os.path.exists("thumbs") == False):
            os.makedirs("thumbs")
        if(os.path.isdir("thumbs") == False):
            print "Error!!! thumbs directory is not in: " + os.getcwd()
            return None
        else:
            thumbnailName = "thumbs/%s.jpg" % (filenameHash)
            osFileName = os.path.normpath(thumbnailName)
            if((forceUpdate == True) or (os.path.isfile(osFileName) == False)):
                print "Thumb file does not exist. Generating... " + thumbnailName
                destWidth, destHeight = (40, 30)
                resizeMat = createMat(destWidth, destHeight)
                if(image == None):
                    print "Error! thumbnail image == None for " + self.getType() + "!"
                scaleAndSave(image, osFileName, resizeMat)
            else:
                print "Thumb file already exist. " + thumbnailName
            return thumbnailName

    def openFile(self, midiLength):
        pass

    def mixWithImage(self, image, mixMode, effects, currentSongPosition, midiChannelState, guiCtrlStateHolder, midiNoteState, mixMat1, mixMask):
        if(self._image == None):
            return image
        else:
            if(mixMode == MixMode.Default):
                mixMode = self._mixMode
            if(effects != None):
                preFx, preFxSettings, preFxCtrlVal, preFxStartVal, postFx, postFxSettings, postFxCtrlVal, postFxStartVal = effects
            else:
                preFx, preFxSettings, preFxCtrlVal, preFxStartVal, postFx, postFxSettings, postFxCtrlVal, postFxStartVal = (None, None, (None, None, None, None, None), None, None, None, (None, None, None, None, None), None)
            (self._image, currentPreValues, unusedStarts) = self._applyOneEffect(self._image, preFx, preFxSettings, preFxCtrlVal, preFxStartVal, currentSongPosition, midiChannelState, midiNoteState, guiCtrlStateHolder, 0) #@UnusedVariable
            mixedImage =  mixImages(mixMode, image, self._image, mixMat1, mixMask)
            (mixedImage, currentPostValues, unusedStarts) = self._applyOneEffect(mixedImage, postFx, postFxSettings, postFxCtrlVal, postFxStartVal, currentSongPosition, midiChannelState, midiNoteState, guiCtrlStateHolder, 5) #@UnusedVariable
            return (mixedImage, currentPreValues, currentPostValues)
    
class ImageFile(MediaFile):
    def __init__(self, fileName, midiTimingClass, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
        self._zoomResizeMat = createMat(self._internalResolutionX, self._internalResolutionY)
        self._radians360 = math.radians(360)

        self._configurationTree.addTextParameter("StartValues", "0.0|0.0|0.0")
        self._configurationTree.addTextParameter("EndValues", "0.0|0.0|0.0")
        self._configurationTree.addBoolParameter("CropMode", True)

        self._startZoom, self._startMove, self._startAngle = textToFloatValues("0.0|0.0|0.0", 3)
        self._endZoom, self._endMove, self._endAngle = textToFloatValues("0.0|0.0|0.0", 3)
        self._startX, self._startY = self._angleAndMoveToXY(self._startAngle, self._startMove)
        self._endX, self._endY = self._angleAndMoveToXY(self._endAngle, self._endMove)
        self._cropMode = True

        self.debugCount = 0
        self._oldZoom = -1.0
        self._oldMoveX = -1.0
        self._oldMoveY = -1.0
        self._oldCrop = False
        self._getConfiguration()

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
        startValuesString = self._configurationTree.getValue("StartValues")
        self._startZoom, self._startMove, self._startAngle = textToFloatValues(startValuesString, 3)
        endValuesString = self._configurationTree.getValue("EndValues")
        self._endZoom, self._endMove, self._endAngle = textToFloatValues(endValuesString, 3)
        self._startX, self._startY = self._angleAndMoveToXY(self._startAngle, self._startMove)
        self._endX, self._endY = self._angleAndMoveToXY(self._endAngle, self._endMove)
        self._cropMode = self._configurationTree.getValue("CropMode")

    def getType(self):
        return "Image"

    def close(self):
        pass

    def skipFrames(self, currentSongPosition, midiNoteState, midiChannelState):
        fadeMode, fadeValue, noteDone = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState)
        if((fadeMode == FadeMode.Black) and (fadeValue < 0.00001)):
            self._image = None
            return noteDone
        zoom = self._startZoom
        moveX = self._startX
        moveY = self._startY
        angle = self._startAngle
        move = self._startMove
        guiMove = False
        if((self._startSongPosition + self._syncLength) < currentSongPosition):
            zoom = self._endZoom
            moveX = self._endX
            moveY = self._endY
        elif(self._startSongPosition < currentSongPosition):
#            print "DEBUG middle: currentSPP: " + str(currentSongPosition) + " startSPP: " + str(self._startSongPosition) + " zoomTime: " + str(self._syncLength)
            if(self._endZoom != self._startZoom):
                zoom = self._startZoom + (((self._endZoom - self._startZoom) / self._syncLength) * (currentSongPosition-self._startSongPosition))
            if(self._endX != self._startX):
                moveX = self._startX + (((self._endX - self._startX) / self._syncLength) * (currentSongPosition-self._startSongPosition))
            if(self._endY != self._startY):
                moveY = self._startY + (((self._endY - self._startY) / self._syncLength) * (currentSongPosition-self._startSongPosition))
        guiStates = self._guiCtrlStateHolder.getGuiContollerState(10)
        if(guiStates[0] != None):
            if(guiStates[0] > -0.5):
                zoom = guiStates[0]
        if(guiStates[1] != None):
            if(guiStates[1] > -0.5):
                move = guiStates[1]
                guiMove = True
        if(guiStates[2] != None):
            if(guiStates[2] > -0.5):
                angle = guiStates[2]
                guiMove = True
        if(guiMove == True):
            moveX, moveY = self._angleAndMoveToXY(angle, move)
        if((zoom != self._oldZoom) or (moveX != self._oldMoveX) or (moveY != self._oldMoveY) or (self._cropMode != self._oldCrop)):
            self._oldZoom = zoom
            self._oldMoveX = moveX
            self._oldMoveY = moveY
            self._oldCrop = self._cropMode
            if(zoom <= 0.5):
                multiplicator = 1.0 - zoom
            elif(zoom <= 0.75):
                multiplicator = 0.5 - (0.1666666 * ((zoom - 0.5) * 4))
            else:
                multiplicator = 0.3333333 - (0.08333333 *((zoom - 0.75) *4))
#            print "DEBUG zoom: " + str(zoom) + " multiplicator: " + str(multiplicator)
            if(self._cropMode == True):
                sourceRectangleX = int(self._source100percentCropX * multiplicator)
                sourceRectangleY = int(self._source100percentCropY * multiplicator)
            else:
                sourceRectangleX = int(self._sourceX * multiplicator)
                sourceRectangleY = int(self._sourceY * multiplicator)                
            if(sourceRectangleX < self._sourceX):
                left = int((self._sourceX - sourceRectangleX) / 2)
            else:
                sourceRectangleX = self._sourceX
                left = 0
            maxXmovmentPlussMinus = left
            if(sourceRectangleY < self._sourceY):
                top = int((self._sourceY - sourceRectangleY) / 2)
            else:
                sourceRectangleY = self._sourceY
                top = 0
            maxYmovmentPlussMinus = top
            left = int(moveX * maxXmovmentPlussMinus) + left
            left = int(moveX) + left
            if(left < 0):
                left = 0
            elif((left + sourceRectangleX) > self._sourceX):
                left = self._sourceX - sourceRectangleX
            top = int(moveY * maxYmovmentPlussMinus) + top
            if(top < 0):
                top = 0
            elif((top + sourceRectangleY) > self._sourceY):
                top = self._sourceY - sourceRectangleY
#            print "DEBUG Move X: %d Y: %d" %(moveX, moveY)
#            print "DEBUG source %d:%d dest %d:%d rect: %d:%d:%d:%d" %(self._sourceX, self._sourceY, self._internalResolutionX, self._internalResolutionY, left, top, sourceRectangleX, sourceRectangleY)
            src_region = cv.GetSubRect(self._firstImage, (left, top, sourceRectangleX, sourceRectangleY) )
            cv.Resize(src_region, self._zoomResizeMat)
            self._captureImage = self._zoomResizeMat
        self._applyEffects(currentSongPosition, midiChannelState, midiNoteState, fadeMode, fadeValue)
        return False

    def _angleAndMoveToXY(self, angle, move):
        angle360 = angle * 360
        if(angle360 < 45.0):
            moveX = -move
            moveY = math.tan(self._radians360 * angle) * -move
        elif(angle360 < 135):
            moveX = math.tan(self._radians360 * (angle-0.25)) * move
            moveY = -move
        elif(angle360 < 225):
            moveX = move
            moveY = math.tan(self._radians360 * (angle-0.5)) * move
        elif(angle360 < 315):
            moveX = math.tan(self._radians360 * (angle-0.75)) * -move
            moveY = move
        else:
            moveX = -move
            moveY = math.tan(self._radians360 * angle) * -move
        return moveX, moveY
        
    def openFile(self, midiLength):
        if (os.path.isfile(self._fullFilePath) == False):
            self._log.warning("Could not find file: %s in directory: %s", self._cfgFileName, self._videoDirectory)
            raise MediaError("File does not exist!")
        try:
            self._captureImage = cv.LoadImage(self._fullFilePath)
        except:
            self._log.warning("Exception while reading: %s", os.path.basename(self._cfgFileName))
            print "Exception while reading: " + os.path.basename(self._cfgFileName)
            raise MediaError("File caused exception!")
        if (self._captureImage == None):
            self._log.warning("Could not read frames from: %s", os.path.basename(self._cfgFileName))
            print "Could not read frames from: " + os.path.basename(self._cfgFileName)
            raise MediaError("File could not be read!")
        self._firstImage = self._captureImage
        self._originalTime = 1.0
        self._sourceX, self._sourceY = cv.GetSize(self._firstImage)
        self._sourceAspect = float(self._sourceX) / self._sourceY
        self._destinationAspect = float(self._internalResolutionX) / self._internalResolutionY
        if(self._sourceAspect > self._destinationAspect):
            self._source100percentCropX = int(self._sourceY * self._destinationAspect)
            self._source100percentCropY = self._sourceY
        else:
            self._source100percentCropX = self._sourceX
            self._source100percentCropY = int(self._sourceX / self._destinationAspect)
        self._log.warning("Read image file %s", os.path.basename(self._cfgFileName))
        self._fileOk = True

class VideoCaptureCameras(object):
    def __init__(self):
        self._cameraList = []
        self._cameraTimeStamps = []
        self._bufferdImages = []
        self._internalResolutionX = 800
        self._internalResolutionY = 600

    def openCamera(self, cameraId, internalResolutionX, internalResolutionY):
        self._internalResolutionX = internalResolutionX
        self._internalResolutionY = internalResolutionY
        minNumCamearas = cameraId + 1
        while(minNumCamearas > len(self._cameraList)):
            self._cameraList.append(None)
            self._cameraTimeStamps.append(-1.0)
            blankImage = getEmptyImage(self._internalResolutionX, self._internalResolutionY)
            self._bufferdImages.append(blankImage)
        if(self._cameraList[cameraId] == None):
            import VideoCapture #@UnresolvedImport
            try:
                self._cameraList[cameraId] = VideoCapture.Device(cameraId)
            except:
                return False # Failed to open camera id.
        return True

    def getFirstImage(self, cameraId):
        return self.getCameraImage(cameraId, None)

    def getCameraImage(self, cameraId, timeStamp):
        if(self._cameraList[cameraId] == None):
            return self._bufferdImages[cameraId]
        minNumCamearas = cameraId + 1
        if(minNumCamearas > len(self._cameraList)):
            print "ERROR: Camera with id %d is not initialized! We only got %d number of cameras." %(minNumCamearas, len(self._cameraList))
            return None
        if((timeStamp != None) and (self._cameraTimeStamps[cameraId] != timeStamp)):
            pilImage = self._cameraList[cameraId].getImage()
            if(pilImage != None):
                cvImage = cv.CreateImageHeader(pilImage.size, cv.IPL_DEPTH_8U, 3)
                cv.SetData(cvImage, pilImage.tostring())
                rotatedImage = createMat(pilImage.size[0], pilImage.size[1])
                cv.CvtColor(cvImage, rotatedImage, cv.CV_BGR2RGB)
#                rezizedImage = createMat(self._internalResolutionX, self._internalResolutionY)
                self._bufferdImages[cameraId] = rotatedImage#resizeImage(rotatedImage, rezizedImage)
                self._cameraTimeStamps[cameraId] = timeStamp
#        else:
#            print "DEBUG: using buffered image!!!"
        return self._bufferdImages[cameraId]

class OpenCvCameras(object):
    def __init__(self):
        self._cameraList = []
        self._cameraTimeStamps = []
        self._cameraFrameRates = []
        self._bufferdImages = []
        self._internalResolutionX = 800
        self._internalResolutionY = 600

    def openCamera(self, cameraId, internalResolutionX, internalResolutionY):
        self._internalResolutionX = internalResolutionX
        self._internalResolutionY = internalResolutionY
        minNumCamearas = cameraId + 1
        while(minNumCamearas > len(self._cameraList)):
            self._cameraList.append(None)
            self._cameraTimeStamps.append(-1.0)
            self._cameraFrameRates.append(0.0)
            blankImage = getEmptyImage(self._internalResolutionX, self._internalResolutionY)
            self._bufferdImages.append(blankImage)
        if(self._cameraList[cameraId] == None):
            try:
                self._cameraList[cameraId] = cv.CaptureFromCAM(cameraId)
                self._bufferdImages[cameraId] = cv.QueryFrame(self._cameraList[cameraId])
                self._cameraFrameRates[cameraId] = int(cv.GetCaptureProperty(self._cameraList[cameraId], cv.CV_CAP_PROP_FPS))
            except:
                return False # Failed to open camera id.
        return True

    def getFirstImage(self, cameraId):
        return self.getCameraImage(cameraId, None)

    def getFrameRate(self, cameraId):
        return self._cameraFrameRates[cameraId]

    def getCameraImage(self, cameraId, timeStamp):
        if(self._cameraList[cameraId] == None):
            return self._bufferdImages[cameraId]
        minNumCamearas = cameraId + 1
        if(minNumCamearas > len(self._cameraList)):
            print "ERROR: Camera with id %d is not initialized! We only got %d number of cameras." %(minNumCamearas, len(self._cameraList))
            return None
        if((timeStamp != None) and (self._cameraTimeStamps[cameraId] != timeStamp)):
            self._bufferdImages[cameraId] = cv.QueryFrame(self._cameraList[cameraId])
            self._cameraTimeStamps[cameraId] = timeStamp
#        else:
#            print "DEBUG: using buffered image!!!"
        return self._bufferdImages[cameraId]

videoCaptureCameras = VideoCaptureCameras()
openCvCameras = OpenCvCameras()

class CameraInput(MediaFile):
    def __init__(self, fileName, midiTimingClass, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
        self._cameraId = int(fileName)
        self._getConfiguration()
        self._cameraMode = self.CameraModes.OpenCV
        self._firstTrigger = True

    class CameraModes():
        OpenCV, VideoCapture = range(2)

    def getType(self):
        return "Camera"

    def close(self):
        pass

    def skipFrames(self, currentSongPosition, midiNoteState, midiChannelState):
        fadeMode, fadeValue, noteDone = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState)
        if((fadeMode == FadeMode.Black) and (fadeValue < 0.00001)):
            self._image = None
            return noteDone
        if(self._cameraMode == self.CameraModes.OpenCV):
            self._captureImage = openCvCameras.getCameraImage(self._cameraId, currentSongPosition)
        else:
            self._captureImage = videoCaptureCameras.getCameraImage(self._cameraId, currentSongPosition)
        self._applyEffects(currentSongPosition, midiChannelState, midiNoteState, fadeMode, fadeValue)
        return False

    def openFile(self, midiLength):
        if(self._cameraMode == self.CameraModes.OpenCV):
            if(openCvCameras.openCamera(self._cameraId, self._internalResolutionX, self._internalResolutionY) == False):
                raise MediaError("Could not open OpenCV camera with ID: %d!" %(self._cameraId))
        else:
            if(videoCaptureCameras.openCamera(self._cameraId, self._internalResolutionX, self._internalResolutionY) == False):
                raise MediaError("Could not open VideoCapture camera with ID: %d!" %(self._cameraId))
        try:
            if(self._cameraMode == self.CameraModes.OpenCV):
                self._captureImage = openCvCameras.getFirstImage(self._cameraId)
            else:
                self._captureImage = videoCaptureCameras.getFirstImage(self._cameraId)
        except:
            self._log.warning("Exception while opening camera with ID: %d" % (self._cameraId))
            print "Exception while opening camera with ID: %s" % (self._cameraId)
            raise MediaError("File caused exception!")
        if (self._captureImage == None):
            self._log.warning("Could not read frames from camera with ID: %d" % (self._cameraId))
            print "Could not read frames from camera with ID: %d" % (self._cameraId)
            raise MediaError("Could not open camera with ID: %d!" % (self._cameraId))
        if(self._cameraMode == self.CameraModes.OpenCV):
            self._originalFrameRate = openCvCameras.getFrameRate(self._cameraId)
        self._firstImage = self._captureImage
        self._log.warning("Opened camera %d with framerate %d",self._cameraId, self._originalFrameRate)
        self._fileOk = True

class KinectCameras(object):
    def __init__(self):
        self._depthTimeStamp = -1.0
        self._videoTimeStamp = -1.0
        self._depthMask = None
        self._videoImage = None
        self._irMask = None
        self._internalResolutionX = 800
        self._internalResolutionY = 600

    def openCamera(self, internalResolutionX, internalResolutionY):
        if(freenect == None):
            self._log.warning("Error while importing kinect!")
            print "Error while importing kinect!"
            return False # Failed to open kinect camera.
        self._internalResolutionX = internalResolutionX
        self._internalResolutionY = internalResolutionY
        if((self._depthMask == None) and (self._videoImage == None)):
            self._depthMask = createMask(self._internalResolutionX, self._internalResolutionY)
            self._videoImage = getEmptyImage(self._internalResolutionX, self._internalResolutionY)
            try:
                depthArray, _ = freenect.sync_get_depth()
                depthCapture = cv.fromarray(depthArray.astype(numpy.uint8))
                resizeImage(depthCapture, self._depthMask)
    #            depthArray, _ = freenect.sync_get_video(0, freenect.VIDEO_IR_8BIT)
                rgbImage, _ = freenect.sync_get_video()
                rgbCapture = cv.fromarray(rgbImage.astype(numpy.uint8))
                resizeImage(rgbCapture, self._videoImage)
            except:
                self._log.warning("Exception while opening camera with ID: %d" % (self._cameraId))
                print "Exception while opening camera with ID: %s" % (self._cameraId)
                self._depthMask = None
                self._videoImage = None
                self._irMask = None
                return False
        return True

    class KinectImageTypes():
        Depth, RGB, IR = range(3)

    def getFirstImage(self):
        return self.getCameraImage(self.KinectImageTypes.Depth, None)

    def getCameraImage(self, typeId, timeStamp):
        if((self._depthMask == None) or (self._videoImage == None)):
            return None
        if((typeId == self.KinectImageTypes.RGB) or (typeId == self.KinectImageTypes.IR)):
            if((timeStamp != None) and (self._videoTimeStamp != timeStamp)):
                if(typeId == self.KinectImageTypes.IR):
                    if(self._irMask == None):
                        self._irMask = createMask(self._internalResolutionX, self._internalResolutionY)
                    irArray, _ = freenect.sync_get_video(0, freenect.VIDEO_IR_8BIT)
                    irCapture = cv.fromarray(irArray.astype(numpy.uint8))
                    resizeImage(irCapture, self._irMask)
                    cv.Merge(self._irMask, self._irMask, self._irMask, None, self._videoImage)
                else: #RGB!
                    rgbImage, _ = freenect.sync_get_video()
                    rgbCapture = cv.fromarray(rgbImage.astype(numpy.uint8))
                    resizeImage(rgbCapture, self._videoImage)
                self._videoTimeStamp = timeStamp
            return self._videoImage
        else:
            if((timeStamp != None) and (self._depthTimeStamp != timeStamp)):
                depthArray, _ = freenect.sync_get_depth()
                depthCapture = cv.fromarray(depthArray.astype(numpy.uint8))
                resizeImage(depthCapture, self._depthMask)
                self._depthTimeStamp = timeStamp
            return self._depthMask

kinectCameras = KinectCameras()
    
class KinectCameraInput(MediaFile):
    def __init__(self, fileName, midiTimingClass, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
        self._cameraId = int(fileName)
        self._blackFilterModulationId = -1
        self._diffFilterModulationId = -1
        self._erodeFilterModulationId = -1
        self._midiModulation = MidiModulation(self._configurationTree, self._midiTiming)
        self._midiModulation.setModulationReceiver("DisplayModeModulation", "None")
        self._configurationTree.addTextParameter("FilterValues", "0.0|0.0|0.0")
        self._firstTrigger = True
        self._kinectModesHolder = KinectMode()
        self._getConfiguration()
        self._filterValues = 0.0, 0.0, 0.0

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
        self._modeModulationId = self._midiModulation.connectModulation("DisplayModeModulation")
        filterValuesString = self._configurationTree.getValue("FilterValues")
        self._filterValues = textToFloatValues(filterValuesString, 3)

    def getType(self):
        return "KinectCamera"

    def close(self):
        pass

    def restartSequence(self):
        self._firstTrigger = True

    def findKinectMode(self, currentSongPosition, midiNoteState, midiChannelState):
        value = self._midiModulation.getModlulationValue(self._modeModulationId, midiChannelState, midiNoteState, currentSongPosition, 0.0)
        maxValue = len(self._kinectModesHolder.getChoices()) * 0.99999999
        modeSelected = int(value*maxValue)
        return modeSelected

    def setStartPosition(self, startSpp):
        if(self._firstTrigger == True):
            self._firstTrigger = False
            if(freenect != None):
                pass

    def _getFilterValues(self):
        blackThreshold, diffThreshold, erodeValue = self._filterValues
        guiStates = self._guiCtrlStateHolder.getGuiContollerState(10)
        if(guiStates[0] != None):
            if(guiStates[0] > -0.5):
                blackThreshold = guiStates[0]
        if(guiStates[1] != None):
            if(guiStates[1] > -0.5):
                diffThreshold = guiStates[1]
        if(guiStates[2] != None):
            if(guiStates[2] > -0.5):
                erodeValue = guiStates[2]
        return blackThreshold, diffThreshold, erodeValue

    def skipFrames(self, currentSongPosition, midiNoteState, midiChannelState):
        if(freenect == None):
            self._image = None
            return True
        fadeMode, fadeValue, noteDone = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState)
        if((fadeMode == FadeMode.Black) and (fadeValue < 0.00001)):
            self._image = None
            return noteDone

        kinectMode = self.findKinectMode(currentSongPosition, midiNoteState, midiChannelState)
        if(kinectMode == KinectMode.RGBImage):
            self._captureImage = copyImage(kinectCameras.getCameraImage(kinectCameras.KinectImageTypes.RGB, currentSongPosition))
        elif(kinectMode == KinectMode.IRImage):
            self._captureImage = copyImage(kinectCameras.getCameraImage(kinectCameras.KinectImageTypes.IR, currentSongPosition))
        elif(kinectMode == KinectMode.DepthImage):
            depthImage = kinectCameras.getCameraImage(kinectCameras.KinectImageTypes.Depth, currentSongPosition)
            cv.Merge(depthImage, depthImage, depthImage, None, self._captureImage)
        elif(kinectMode == KinectMode.DepthMask):
            depthImage = kinectCameras.getCameraImage(kinectCameras.KinectImageTypes.Depth, currentSongPosition)
            blackThreshold, diffThreshold, erodeValue = self._getFilterValues()
            cv.CmpS(depthImage, 10 + (50 * blackThreshold), self._tmpMat2, cv.CV_CMP_LE)
            cv.Add(depthImage, self._tmpMat2, self._tmpMat1)
            cv.AddS(self._tmpMat1, 5 + (35 * diffThreshold), self._tmpMat2)
            cv.Cmp(self._tmpMat2, self._startDepthMat, self._tmpMat1, cv.CV_CMP_LT)
            erodeIttrations = int(10 * erodeValue)
            if(erodeIttrations > 0):
                cv.Erode(self._tmpMat1, self._tmpMat2, None, erodeIttrations)
                cv.Merge(self._tmpMat2, self._tmpMat2, self._tmpMat2, None, self._captureImage)
            else:
                cv.Merge(self._tmpMat1, self._tmpMat1, self._tmpMat1, None, self._captureImage)
        elif(kinectMode == KinectMode.DepthThreshold):
            depthImage = kinectCameras.getCameraImage(kinectCameras.KinectImageTypes.Depth, currentSongPosition)
            blackThreshold, diffThreshold, erodeValue = self._getFilterValues()
            darkFilterValue = 256 - int(blackThreshold * 256)
            lightFilterValue = int(diffThreshold * 256)
            cv.CmpS(depthImage, darkFilterValue, self._tmpMat1, cv.CV_CMP_LE)
            cv.CmpS(depthImage, lightFilterValue, self._tmpMat2, cv.CV_CMP_GE)
            cv.Mul(self._tmpMat1, self._tmpMat2, self._tmpMat1)
            cv.Merge(self._tmpMat1, self._tmpMat1, self._tmpMat1, None, self._captureImage)
        else: # (kinectMode == KinectMode.Reset):
            depthImage = kinectCameras.getCameraImage(kinectCameras.KinectImageTypes.Depth, currentSongPosition)
            cv.CmpS(depthImage, 10 + (50 * blackThreshold), self._tmpMat2, cv.CV_CMP_LE)
            cv.Add(depthImage, self._tmpMat2, self._startDepthMat)
            cv.Merge(self._startDepthMat, self._tmpMat1, self._tmpMat2, None, self._captureImage)

        self._applyEffects(currentSongPosition, midiChannelState, midiNoteState, fadeMode, fadeValue)
        return False

    def openFile(self, midiLength):
        openOk = kinectCameras.openCamera(self._internalResolutionX, self._internalResolutionY)
        if(openOk == False):
            self._log.warning("Error while opening kinect camera!")
            print "Error while opening kinect camera!"
            raise MediaError("Kinect not installed correctly?")
        depthMat = kinectCameras.getFirstImage()
        if(depthMat == None):
            self._log.warning("Exception while getting first image from kinnect.")
            print "Exception while getting first image from kinnect."
            raise MediaError("File caused exception!")
        self._tmpMat1 = createMask(self._internalResolutionX, self._internalResolutionY)
        self._tmpMat2 = createMask(self._internalResolutionX, self._internalResolutionY)
        self._tmpRgb = createMat(self._internalResolutionX, self._internalResolutionY)
        self._startDepthMat = cv.CloneMat(depthMat)
        cv.CmpS(depthMat, 20, self._tmpMat2, cv.CV_CMP_LE)
        cv.Add(depthMat, self._tmpMat2, self._startDepthMat)
        self._captureImage = getEmptyImage(self._internalResolutionX, self._internalResolutionY)
        self._firstImage = self._captureImage
        self._log.warning("Opened kinect camera %d with framerate %d",self._cameraId, self._originalFrameRate)
        self._fileOk = True

class ImageSequenceFile(MediaFile):
    def __init__(self, fileName, midiTimingClass, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
        self._triggerCounter = 0
        self._firstTrigger = True
        self._sequenceMode = ImageSequenceMode.Time
        self._midiModulation = MidiModulation(self._configurationTree, self._midiTiming)
        self._configurationTree.addTextParameter("SequenceMode", "Time")
        self._midiModulation.setModulationReceiver("PlaybackModulation", "None")
        self._playbackModulationId = -1
        self._getConfiguration()

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
        self._playbackModulationId = self._midiModulation.connectModulation("PlaybackModulation")
        seqMode = self._configurationTree.getValue("SequenceMode")
        if(seqMode == "ReTrigger"):
            self._sequenceMode = ImageSequenceMode.ReTrigger
        elif(seqMode == "Modulation"):
            self._sequenceMode = ImageSequenceMode.Modulation
        else:
            self._sequenceMode = ImageSequenceMode.Time #Defaults to time

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
            if(self._firstTrigger == True):
                self._firstTrigger = False
            else:
                self._triggerCounter += 1
            print "TriggerCount: " + str(self._triggerCounter) + " startSPP: " + str(startSpp)
        self._startSongPosition = startSpp

    def getPlaybackModulation(self, songPosition, midiChannelStateHolder, midiNoteStateHolder):
        return self._midiModulation.getModlulationValue(self._playbackModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)

    def skipFrames(self, currentSongPosition, midiNoteState, midiChannelState):
        fadeMode, fadeValue, noteDone = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState)
        if((fadeMode == FadeMode.Black) and (fadeValue < 0.00001)):
            self._image = None
            return noteDone

        lastFrame = self._currentFrame
        
        if(self._sequenceMode == ImageSequenceMode.Time):
            self._currentFrame = (int((currentSongPosition - self._startSongPosition) / self._syncLength) % self._numberOfFrames)
        elif(self._sequenceMode == ImageSequenceMode.ReTrigger):
            self._currentFrame =  (self._triggerCounter % self._numberOfFrames)
        elif(self._sequenceMode == ImageSequenceMode.Modulation):
            self._currentFrame = int(self.getPlaybackModulation(currentSongPosition, midiChannelState, midiNoteState) * (self._numberOfFrames - 1))

        if(lastFrame != self._currentFrame):
            if(self._bufferedImageList != None):
                self._captureImage = self._bufferedImageList[self._currentFrame]
#                print "Buffered image!!!"
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
            self._applyEffects(currentSongPosition, midiChannelState, midiNoteState, fadeMode, fadeValue)
            return False
        else:
            self._log.debug("Same frame %d currentSongPosition %f", self._currentFrame, currentSongPosition)
            self._applyEffects(currentSongPosition, midiChannelState, midiNoteState, fadeMode, fadeValue)
            return False

    def openFile(self, midiLength):
        self.openVideoFile(midiLength)


class VideoLoopFile(MediaFile):
    def __init__(self, fileName, midiTimingClass, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        MediaFile.__init__(self, fileName, midiTimingClass, effectsConfiguration, effectImagesConfig, guiCtrlStateHolder, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir)
        self._loopMode = VideoLoopMode.Normal
        self._configurationTree.addTextParameter("LoopMode", "Normal")
        self._getConfiguration()

    def _getConfiguration(self):
        MediaFile._getConfiguration(self)
        loopMode = self._configurationTree.getValue("LoopMode")
        if(loopMode == "Normal"):
            self._loopMode = VideoLoopMode.Normal
        elif(loopMode == "Reverse"):
            self._loopMode = VideoLoopMode.Reverse
        elif(loopMode == "PingPong"):
            self._loopMode = VideoLoopMode.PingPong
        elif(loopMode == "PingPongReverse"):
            self._loopMode = VideoLoopMode.PingPongReverse
        elif(loopMode == "DontLoop"):
            self._loopMode = VideoLoopMode.DontLoop
        elif(loopMode == "DontLoopReverse"):
            self._loopMode = VideoLoopMode.DontLoopReverse
        else:
            self._loopMode = VideoLoopMode.Normal #Defaults to normal

    def close(self):
        pass

    def getType(self):
        return "VideoLoop"

    def skipFrames(self, currentSongPosition, midiNoteState, midiChannelState):
        fadeMode, fadeValue, noteDone = self._getFadeValue(currentSongPosition, midiNoteState, midiChannelState)
        if((fadeMode == FadeMode.Black) and (fadeValue < 0.00001)):
            self._image = None
            return noteDone
        lastFrame = self._currentFrame

        framePos = int(((currentSongPosition - self._startSongPosition) / self._syncLength) * self._numberOfFrames)
        if(self._loopMode == VideoLoopMode.Normal):
            self._currentFrame = framePos % self._numberOfFrames
        elif(self._loopMode == VideoLoopMode.Reverse):
            self._currentFrame = -framePos % self._numberOfFrames
        elif(self._loopMode == VideoLoopMode.PingPong):
            self._currentFrame = abs(((framePos + self._numberOfFrames) % (2 * self._numberOfFrames)) - self._numberOfFrames)
        elif(self._loopMode == VideoLoopMode.PingPongReverse):
            self._currentFrame = abs((framePos % (2 * self._numberOfFrames)) - self._numberOfFrames)
        elif(self._loopMode == VideoLoopMode.DontLoop):
            if(framePos < self._numberOfFrames):
                self._currentFrame = framePos
            else:
                self._image = None
                return False
        elif(self._loopMode == VideoLoopMode.DontLoopReverse):
            if(framePos < self._numberOfFrames):
                self._currentFrame = self._numberOfFrames - 1 - framePos
            else:
                self._image = None
                return False
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
            self._applyEffects(currentSongPosition, midiChannelState, midiNoteState, fadeMode, fadeValue)
            return False
        else:
            self._log.debug("Same frame %d currentSongPosition %f", self._currentFrame, currentSongPosition)
            self._applyEffects(currentSongPosition, midiChannelState, midiNoteState, fadeMode, fadeValue)
            return False

    def openFile(self, midiLength):
        self.openVideoFile(midiLength)

class MediaError(Exception):
    def __init__(self, value):
        self.value = value.encode("utf-8")

    def __str__(self):
        return repr(self.value)