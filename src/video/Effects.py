'''
Created on 24. jan. 2012

@author: pcn
'''
import cv2
from cv2 import cv
import numpy
from video.EffectModes import EffectTypes, ZoomModes, FlipModes, DistortionModes,\
    EdgeModes, DesaturateModes, ColorizeModes, EdgeColourModes, getEffectId,\
    ScrollModes, ContrastModes, HueSatModes, ValueToHueModes, BlobDetectModes
import math
import os
import time
import sys

effectImageList = []
effectImageFileNameList = []

class MediaError(Exception):
    def __init__(self, value):
        self.value = value.encode("utf-8")

    def __str__(self):
        return repr(self.value)

def getEmptyImage(x, y):
    try:
        resizeMat = createMat(x,y)
        return resizeImage(cv.CreateImage((x,y), cv.IPL_DEPTH_8U, 3), resizeMat)
    except cv2.error:
        raise MediaError("getEmptyImage() Out of memory! Message: " + sys.exc_info()[1].message)

def createMat(width, heigth):
    try:
        return cv.CreateMat(heigth, width, cv.CV_8UC3)
    except cv2.error:
        raise MediaError("createMat() Out of memory! Message: " + sys.exc_info()[1].message)

def createMask(width, heigth):
    try:
        return cv.CreateMat(heigth, width, cv.CV_8UC1)
    except cv2.error:
        raise MediaError("createMask() Out of memory! Message: " + sys.exc_info()[1].message)

def create16bitMat(width, heigth):
    try:
        return cv.CreateMat(heigth, width, cv.CV_16SC1)
    except cv2.error:
        raise MediaError("create16bitMat() Out of memory! Message: " + sys.exc_info()[1].message)

def createNoizeMatAndMask(width, heigth):
    try:
        randomState = numpy.random.RandomState(int(time.time()))
        noizeMat = createMat(width, heigth)
        randomArray = randomState.randint(0, 255, size=(heigth, width)).astype(numpy.uint8)
        tmpNoizeMask = cv.fromarray(randomArray)
        cv.Merge(tmpNoizeMask, tmpNoizeMask, tmpNoizeMask, None, noizeMat)
        randomArray = randomState.randint(0, 255, size=(heigth, width)).astype(numpy.uint8)
        noizeMask = cv.fromarray(randomArray)
        return noizeMat, noizeMask
    except cv2.error:
        raise MediaError("createNoizeMatAndMask() Out of memory! Message: " + sys.exc_info()[1].message)

def copyOrResizeImage(image, destination):
    imageSize = cv.GetSize(image)
    destSize = cv.GetSize(destination)
    if((imageSize[0] == destSize[0]) and (imageSize[1] == destSize[1])):
        cv.Copy(image, destination)
    else:
        cv.Resize(image, destination)

def copyImage(image):
    try:
        if(type(image) is cv.cvmat):
            return cv.CloneMat(image)
        return cv.CloneImage(image)
    except cv2.error:
        raise MediaError("copyImage() Out of memory! Message: " + sys.exc_info()[1].message)

def pilToCvImage(pilImage):
    try:
        cvImage = cv.CreateImageHeader(pilImage.size, cv.IPL_DEPTH_8U, 3)
        cv.SetData(cvImage, pilImage.tostring())
#        resizeMat = createMat(self._internalResolutionX, self._internalResolutionY)
#        cv.Resize(cvImage, resizeMat)
        return cvImage
    except cv2.error:
        raise MediaError("pilToCvImage() Out of memory! Message: " + sys.exc_info()[1].message)

def pilToCvMask(pilImage, maskThreshold = -1):
    try:
        pilSize = pilImage.size
        cvMask = cv.CreateImageHeader(pilSize, cv.IPL_DEPTH_8U, 1)
        cv.SetData(cvMask, pilImage.tostring())
        if(maskThreshold > 0):
            filterMask = createMask(pilSize[0], pilSize[1])
            cv.CmpS(cvMask, maskThreshold, filterMask, cv.CV_CMP_GE)
            return filterMask
        else:
            return cvMask
    except cv2.error:
        raise MediaError("pilToCvMask() Out of memory! Message: " + sys.exc_info()[1].message)

def resizeImage(image, resizeMat):
    cv.Resize(image, resizeMat)
    return resizeMat

def getHueColor(hue):
    phase = int(hue * 5.99)
    subPhase = (hue * 5.99) % 1.0
    if(phase == 0):
        red = 256
        green = 256.0 * subPhase
        blue = 0
    elif(phase == 1):
        red = 256.0 * (1.0 - subPhase)
        green = 256
        blue = 0
    elif(phase == 2):
        red = 0
        green = 256
        blue = 256.0 * subPhase
    elif(phase == 3):
        red = 0
        green = 256.0 * (1.0 - subPhase)
        blue = 256
    elif(phase == 4):
        red = 256.0 * subPhase
        green = 0
        blue = 256
    else:
        red = 256
        green = 0
        blue = 256.0 * (1.0 - subPhase)
    return (int(red), int(green), int(blue))

def modifyHue(rgb, sat):
    red, green, blue = rgb
    if(sat < 0.5):
        red = int(red + ((256-red) * (1.0 - (2.0*sat))))
        green = int(green + ((256-green) * (1.0 - (2.0*sat))))
        blue = int(blue + ((256-blue) * (1.0 - (2.0*sat))))
    elif(sat > 0.5):
        red = int(red * (1.0 - (2.0*(sat - 0.5))))
        blue = int(blue * (1.0 - (2.0*(sat - 0.5))))
        green = int(green * (1.0 - (2.0*(sat - 0.5))))
    return (red, green, blue)

def getEffectById(effectType, templateName, configurationTree, effectImagesConfiguration, specialModulationHolder, internalResX, internalResY):
    if(effectType == EffectTypes.Zoom):
        return ZoomEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.Flip):
        return FlipEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.Mirror):
        return MirrorEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.Rotate):
        return RotateEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.Scroll):
        return ScrollEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.Blur):
        return BlurEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.BlurContrast):
        return BluredContrastEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.Feedback):
        return FeedbackEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.Delay):
        return DelayEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.SelfDifference):
        return SelfDifferenceEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.Distortion):
        return DistortionEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.Pixelate):
        return PixelateEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.TVNoize):
        return TVNoizeEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.Edge):
        return EdgeEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.BlobDetect):
        return BlobDetectEffect(configurationTree, specialModulationHolder, templateName, internalResX, internalResY)
    elif(effectType == EffectTypes.Desaturate):
        return DesaturateEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.Contrast):
        return ContrastBrightnessEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.HueSaturation):
        return HueSaturationEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.Colorize):
        return ColorizeEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.Invert):
        return InvertEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.ValueToHue):
        return ValueToHueEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.Threshold):
        return ThresholdEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.ImageAdd):
        return ImageAddEffect(configurationTree, effectImagesConfiguration, internalResX, internalResY)
    else:
        return None

def getEffectByName(name, templateName, configurationTree, effectImagesConfiguration, specialModulationHolder, internalResX, internalResY):
    fxid = getEffectId(name)
    return getEffectById(fxid, templateName, configurationTree, effectImagesConfiguration, specialModulationHolder, internalResX, internalResY)

effectMat1 = None
effectMat2 = None
effectMask1 = None
effectMask2 = None
effectMask3 = None
effectMask4 = None
effectMask5 = None
effect16bitMask = None
bigNoizeMat = None
bigNoizeMask = None

def setupEffectMemory(width, heigth):
    global effectMat1
    global effectMat2
    global effectMask1
    global effectMask2
    global effectMask3
    global effectMask4
    global effectMask5
    global effect16bitMask
    global bigNoizeMat
    global bigNoizeMask
    if(effectMat1 == None):
        effectMat1 = createMat(width, heigth)
        effectMat2 = createMat(width, heigth)
        effectMask1 = createMask(width, heigth)
        effectMask2 = createMask(width, heigth)
        effectMask3 = createMask(width, heigth)
        effectMask4 = createMask(width, heigth)
        effectMask5 = createMask(width, heigth)
        effect16bitMask = create16bitMat(width, heigth)
        bigNoizeMat, bigNoizeMask = createNoizeMatAndMask(width*2, heigth*2)

class ZoomEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)

        self._setZoomRange(0.25, 4.0)

        self._zoomMat = effectMat1

    def findMode(self, value):
        modeSelected = int(value*3.99)
        if(modeSelected == ZoomModes.In):
            return ZoomModes.In
        elif(modeSelected == ZoomModes.Out):
            return ZoomModes.Out
        elif(modeSelected == ZoomModes.InOut):
            return ZoomModes.InOut
        else:
            return ZoomModes.Full

    def _setZoomRange(self, minZoom, maxZoom):
        self._minZoomRange = 1 / maxZoom
        self._maxZoomRange = 1 / minZoom
        self._zoomRange = self._maxZoomRange - self._minZoomRange
        zoomMiddle = (self._minZoomRange + self._maxZoomRange) / 2
        self._minMoveRange = zoomMiddle - (self._zoomRange / 2)
        self._moveRange = self._zoomRange

    def getName(self):
        return "Zoom"

    def reset(self):
        pass

    def applyEffect(self, image, amount, xyrate, xcenter, ycenter, mode, minZoomRange = None, zoomRange = None):
        zoomMode = self.findMode(mode)
        xzoom = 1.0 - amount
        if(zoomMode == ZoomModes.Full):
            yzoom = 1.0 - amount * (xyrate  * 2)
            xcentr = (xcenter * -2) + 1
            ycentr = (ycenter * 2) - 1
        else:
            yzoom = xzoom
            xcentr = 0.0
            ycentr = 0.0
        if(minZoomRange == None):
            minZoomRange = self._minZoomRange
        if(zoomRange == None):
            zoomRange = self._zoomRange
        if(zoomMode == ZoomModes.Out):
            if(minZoomRange < 1.0):
                minZoomRange = 1.0
                zoomRange = zoomRange - 1.0 + self._minZoomRange
                xzoom = 1.0 - xzoom
                yzoom = 1.0 - yzoom
        elif(zoomMode == ZoomModes.In):
            if((minZoomRange + zoomRange) > 1.0):
                zoomRange = 1.0 - minZoomRange
        if(zoomRange <= 0):
            return image
        return self.zoomImage(image, xcentr, ycentr, xzoom, yzoom, minZoomRange, zoomRange)

    def zoomImage(self, image, xcenter, ycenter, zoomX, zoomY, minZoomRange, zoomRange):
        originalW, originalH = cv.GetSize(image)
        originalWidth = float(originalW)
        originalHeight = float(originalH)
        zoomXFraction = minZoomRange + (zoomRange * zoomX)
        zoomYFraction = minZoomRange + (zoomRange * zoomY)
        if(zoomYFraction < minZoomRange):
            zoomYFraction = minZoomRange
        elif(zoomYFraction > self._maxZoomRange):
            zoomYFraction = self._maxZoomRange
        width = int(originalWidth * zoomXFraction)
        height = int(originalHeight * zoomYFraction)
        moveXFraction = (self._minMoveRange + (self._moveRange * zoomX / 2))
        moveYFraction = (self._minMoveRange + (self._moveRange * zoomY / 2))
        left = int((originalWidth / 2) + (originalWidth * xcenter * moveXFraction) - (width / 2))
        top = int((originalHeight / 2) + (originalHeight * ycenter * moveYFraction) - (height / 2))
#        print "X: " + str(moveXFraction) + " Y: " + str(moveYFraction) + " Left: " + str(left) + " top: " + str(top) + " xc: " + str(originalWidth * xcenter) + " yc: " + str(originalHeight * ycenter)
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
            outPutWidth = int(originalWidth + ((originalWidth - right) / zoomXFraction)) - outPutLeft
            width = int(originalWidth - left)
            outputRect = True
        if(top < 0):
            outPutTop = -int(float(top) / zoomYFraction)
            height = height + top
            top = 0
            outputRect = True
        if(bottom > originalHeight):
            outPutHeight = int(originalHeight + float(originalHeight - bottom) / zoomYFraction) - outPutTop
            height = int(originalHeight - top)
            outputRect = True
        if((height < 1) or (width < 1)):
            cv.SetZero(image)
            return image
#        print "Zoom src: " + str(zoomXFraction) + " Y: " + str(zoomYFraction) + " w: " + str(width) + " h: " + str(height) + " l: " + str(left) + " t: " + str(top)
        src_region = cv.GetSubRect(image, (left, top, width, height) )
        if(outputRect):
            if(outPutWidth < 0):
                outPutWidth = int(originalWidth - outPutLeft)
                if(outPutWidth < 0):
                    cv.SetZero(image)
                    return image
            if(outPutHeight < 0):
                outPutHeight = int(originalHeight - outPutTop)
                if(outPutHeight < 0):
                    cv.SetZero(image)
                    return image
#            print "Zoom OUT: " + str(outPutWidth) + " h: " + str(outPutHeight) + " l: " + str(outPutLeft) + " t: " + str(outPutTop)
            tmpMat = createMat(outPutWidth, outPutHeight)
            cv.Resize(src_region, tmpMat)
            cv.SetZero(image)
            dst_region = cv.GetSubRect(image, (outPutLeft, outPutTop, outPutWidth, outPutHeight) )
            cv.Copy(tmpMat, dst_region)
            return image
        cv.Resize(src_region, self._zoomMat)
        cv.Copy(self._zoomMat, image)
        return image

class MirrorEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)

        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._halfResX = int(self._internalResolutionX / 2)
        self._halfResY = int(self._internalResolutionY / 2)
        self._radians360 = math.radians(360)

        self._mirrorMat = effectMat1

    def getName(self):
        return "Mirror"

    def reset(self):
        pass

    def applyEffect(self, image, mode, rotate, move, direction, unused1):
        return self.mirrorImage(image, mode, rotate, move, direction)

    def mirrorImage(self, image, mode, rotate, move, direction):
        rotateMatrix1 = cv.CreateMat(2,3,cv.CV_32F)

        if(rotate >= 0.01):
            xCenter = self._halfResX
            yCenter = self._halfResY
            if(move > 0.02):
                xCenter -= self._halfResX * move * math.cos(self._radians360 * -direction)
                yCenter += self._halfResY * move * math.sin(self._radians360 * -direction)
            angle = rotate * 360
    #        print "DEBUG pcn: angle: " + str(angle) + " center: " + str((xCenter, yCenter))
            cv.GetRotationMatrix2D( (xCenter, yCenter), angle, 1.0, rotateMatrix1)
            cv.SetZero(self._mirrorMat)
            cv.WarpAffine(image, self._mirrorMat, rotateMatrix1)
            cv.Copy(self._mirrorMat, image)
            if(mode < 0.5):
                cv.Flip(self._mirrorMat, self._mirrorMat, 1)
            else:
                cv.Flip(self._mirrorMat, self._mirrorMat, 0)
        else:
            if(mode < 0.5):
                cv.Flip(image, self._mirrorMat, 1)
            else:
                cv.Flip(image, self._mirrorMat, 0)
        if(mode < 0.5):
            src_region = cv.GetSubRect(self._mirrorMat, (self._halfResX, 0, self._halfResX, self._internalResolutionY))
            dst_region = cv.GetSubRect(image, (self._halfResX, 0, self._halfResX, self._internalResolutionY))
        else:
            src_region = cv.GetSubRect(self._mirrorMat, (0, self._halfResY, self._internalResolutionX, self._halfResY))
            dst_region = cv.GetSubRect(image, (0, self._halfResY, self._internalResolutionX, self._halfResY))
        cv.Copy(src_region, dst_region)

        return image

class RotateEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)

        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._radians360 = math.radians(360)

        self._rotateMat = effectMat1

    def getName(self):
        return "Rotate"

    def reset(self):
        pass

    def applyEffect(self, image, amount, move, direction, zoom, unused1):
        return self.rotateImage(image, amount, move, direction, zoom)

    def rotateImage(self, image, amount, move, direction, zoom):
        if((amount < 0.02) or (amount > 0.99)):
            if(zoom < 0.02):
                return image
            else:
                cv.Copy(image, self._rotateMat)
        else:
            xCenter = int(self._internalResolutionX / 2)
            yCenter = int(self._internalResolutionY / 2)
            if(move > 0.02):
                xCenter -= self._internalResolutionX *  0.5 * move * math.cos(self._radians360 * -direction)
                yCenter -= self._internalResolutionY * -0.5 * move * math.sin(self._radians360 * -direction)
            angle = amount * 360
#            print "DEBUG pcn: angle: " + str(angle) + " center: " + str((xCenter, yCenter))
            rotateMatrix = cv.CreateMat(2,3,cv.CV_32F)
            cv.GetRotationMatrix2D( (xCenter, yCenter), angle, 1.0, rotateMatrix)
            cv.SetZero(self._rotateMat)
            cv.WarpAffine(image, self._rotateMat, rotateMatrix)
        if(zoom < 0.02):
            cv.Copy(self._rotateMat, image)
        else:
            zoomMultiplier = 0.60 + ((1.0 - zoom) * 0.4)
            xSize = int(self._internalResolutionX * zoomMultiplier)
            ySize = int(self._internalResolutionY * zoomMultiplier)
            xPos = int((self._internalResolutionX - xSize) / 2)
            yPos = int((self._internalResolutionY - ySize) / 2)
            src_region = cv.GetSubRect(self._rotateMat, (xPos, yPos, xSize, ySize))
            cv.Resize(src_region, image)
        return image

class BlobDetectEffect(object):
    def __init__(self, configurationTree, specialModulationHolder, templateName, internalResX, internalResY):
        self._configurationTree = configurationTree
        self._specialModulationHolder = specialModulationHolder
        self._effectTemplateName = templateName
        setupEffectMemory(internalResX, internalResY)
        self._effectModulationHolder = None
        if(self._specialModulationHolder != None):
            self._effectModulationHolder = self._specialModulationHolder.getSubHolder("Effect")

        self._xValModulationIds = []
        self._yValModulationIds = []
        self._zValModulationIds = []
        if(self._effectModulationHolder != None):
            for i in range(10):
                descX = "BlobDetect;" + self._effectTemplateName + ";" + str(i+1) + ";X"
                descY = "BlobDetect;" + self._effectTemplateName + ";" + str(i+1) + ";Y"
                descZ = "BlobDetect;" + self._effectTemplateName + ";" + str(i+1) + ";Size"
                self._xValModulationIds.append(self._effectModulationHolder.addModulation(descX))
                self._yValModulationIds.append(self._effectModulationHolder.addModulation(descY))
                self._zValModulationIds.append(self._effectModulationHolder.addModulation(descZ))

        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY

        self._maxSizeRoot = math.sqrt(self._internalResolutionX * self._internalResolutionY)
        self._thresholdRootSize = math.sqrt((self._internalResolutionX * self._internalResolutionY) / 2)

        self._colorMat = effectMat1
        self._splitMask = effectMask1
        self._thersholdMask = effectMask2

    def getName(self):
        return "BlobDetect"

    def reset(self):
        pass

    def _findMode(self, value):
        modeSelected = int(value*5.99)
        if(modeSelected == BlobDetectModes.CircleAdd):
            return BlobDetectModes.CircleAdd
        elif(modeSelected == BlobDetectModes.CircleOnly):
            return BlobDetectModes.CircleOnly
        elif(modeSelected == BlobDetectModes.RectangleAdd):
            return BlobDetectModes.RectangleAdd
        elif(modeSelected == BlobDetectModes.RectangleOnly):
            return BlobDetectModes.RectangleOnly
        elif(modeSelected == BlobDetectModes.NoAdd):
            return BlobDetectModes.NoAdd
        else:
            return BlobDetectModes.Blank

    def applyEffect(self, image, blobFilter, mode, lineHue, lineSat, lineWeight):
        blobMode = self._findMode(mode)
        return self.detectBlobsImage(image, blobFilter, blobMode, lineHue, lineSat, lineWeight)

    def detectBlobsImage(self, image, blobFilter, blobMode, lineHue, lineSat, lineWeight):
        if(blobFilter < 0.01):
            if(self._effectModulationHolder != None):
                for i in range(10):
                    self._effectModulationHolder.setValue(self._xValModulationIds[i], 0.0)
                    self._effectModulationHolder.setValue(self._yValModulationIds[i], 0.0)
                    self._effectModulationHolder.setValue(self._zValModulationIds[i], 0.0)
            return image
        threshold = int(10 + pow((self._thresholdRootSize * (1.0 - blobFilter)), 2))
        cv.CvtColor(image, self._colorMat, cv.CV_RGB2HSV)
        cv.Split(self._colorMat, None, None, self._splitMask, None)
        cv.CmpS(self._splitMask, 127, self._thersholdMask, cv.CV_CMP_GT)
        storage = cv.CreateMemStorage(0)
        contours = cv.FindContours(self._thersholdMask, storage,  cv.CV_RETR_LIST, cv.CV_CHAIN_APPROX_SIMPLE, (0,0))
        detectedBlobs = []
        while contours:
            blobSize = cv.ContourArea(contours)
            if(blobSize > threshold):
                result = cv.ApproxPoly(contours, storage, cv.CV_POLY_APPROX_DP)
                if((blobMode == BlobDetectModes.RectangleAdd) or (blobMode == BlobDetectModes.RectangleOnly)):
                    blobBox = cv.MinAreaRect2(result)
                    xAmount = blobBox[0][0] / self._internalResolutionX
                    yAmount = blobBox[0][1] / self._internalResolutionY
                    detectedBlobs.append((xAmount, yAmount, blobSize, blobBox))
                else:
                    _, center, radius = cv.MinEnclosingCircle(result)
                    xAmount = center[0] / self._internalResolutionX
                    yAmount = center[1] / self._internalResolutionY
                    detectedBlobs.append((xAmount, yAmount, blobSize, radius))
            contours = contours.h_next()
        sortedBlobs = sorted(detectedBlobs, key=lambda blobInfo: blobInfo[2], reverse=True)
        if((blobMode == BlobDetectModes.CircleOnly) or (blobMode == BlobDetectModes.RectangleOnly) or (blobMode == BlobDetectModes.Blank)):
            cv.SetZero(image)
        red, green, blue = modifyHue(getHueColor(lineHue), lineSat)
        lineWidth = 1 + int(5.99 * lineWeight)
        maxI = -1
        for i in range(min(len(sortedBlobs), 32)):
            maxI = i
            blob = sortedBlobs[i]
            if((blobMode == BlobDetectModes.CircleAdd) or (blobMode == BlobDetectModes.CircleOnly)):
                intX = int(blob[0] * self._internalResolutionX)
                intY = int(blob[1] * self._internalResolutionY)
                intRad = int(blob[3])
                cv.Circle(image, (intX, intY), intRad, (blue,green,red), thickness=lineWidth, lineType=8, shift=0)
            elif((blobMode == BlobDetectModes.RectangleAdd) or (blobMode == BlobDetectModes.RectangleOnly)):
                intX = int(blob[0] * self._internalResolutionX)
                intY = int(blob[1] * self._internalResolutionY)
                boxVectors = [(int(point[0]), int(point[1])) for point in cv.BoxPoints(blob[3])]
                cv.PolyLine(image, [boxVectors], 1, (blue,green,red), thickness=lineWidth, lineType=8, shift=0)
            #TODO: set modulation values...
            if(self._effectModulationHolder != None):
                if(i < 10):
                    self._effectModulationHolder.setValue(self._xValModulationIds[i], blob[0])
                    self._effectModulationHolder.setValue(self._yValModulationIds[i], blob[1])
                    sizeVal = min(1.0, math.sqrt(blob[2]) / self._thresholdRootSize)
                    self._effectModulationHolder.setValue(self._zValModulationIds[i], sizeVal)
#                    print "DEBUG pcn: xID: " + str(self._xValModulationIds[i])
#                    print "DEBUG pcn: yID: " + str(self._yValModulationIds[i])
#            print "DEBUG pcn: Fond blob: " + str((blob[0],blob[1])) + " size: " + str(blob[2])
        if(maxI < 10):
            for i in range(maxI + 1, 10):
                self._effectModulationHolder.setValue(self._xValModulationIds[i], 0.0)
                self._effectModulationHolder.setValue(self._yValModulationIds[i], 0.0)
                self._effectModulationHolder.setValue(self._zValModulationIds[i], 0.0)
        return image

class TVNoizeEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)

        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._randomState = numpy.random.RandomState(int(time.time()))

        self._bigNoizeMask = bigNoizeMask
        self._bigNoizeMat = bigNoizeMat
        self._resizeMat = effectMat2
        self._noizeMask = effectMask1

    def getName(self):
        return "TVNoize"

    def reset(self):
        pass

    def applyEffect(self, image, amount, scale, mode, unused1, unused2):
        return self.noizeifyImage(image, amount, scale, mode)

    def noizeifyImage(self, image, amount, scale, mode):
        if(amount < 0.02):
            return image
        srcWidth = self._internalResolutionX
        srcHeight = self._internalResolutionY
        useResize = False
        if(scale > 0.75):
            useResize = True
            srcWidth = int(srcWidth / 4)
            srcHeight = int(srcHeight / 4)
        elif(scale > 0.50):
            useResize = True
            srcWidth = int(srcWidth / 3)
            srcHeight = int(srcHeight / 3)
        elif(scale > 0.25):
            useResize = True
            srcWidth = int(srcWidth / 2)
            srcHeight = int(srcHeight / 2)
        posX = self._randomState.randint(0, self._internalResolutionX)
        posY = self._randomState.randint(0, self._internalResolutionY)
        src_region = cv.GetSubRect(self._bigNoizeMask, (posX, posY, srcWidth, srcHeight))
        if(useResize == True):
            if(mode < 0.33):
                upScaler = cv.CV_INTER_NN #Clean
            elif(mode < 0.66):
                upScaler = cv.CV_INTER_CUBIC #Blobby roundish
            else:
                upScaler = cv.CV_INTER_LINEAR #Blobby star
            cv.Resize(src_region, self._noizeMask, upScaler)
        else:
            cv.Copy(src_region, self._noizeMask)
        threshold = int(255 * amount)
        cv.CmpS(self._noizeMask, threshold, self._noizeMask, cv.CV_CMP_LT)
        posX = self._randomState.randint(0, self._internalResolutionX)
        posY = self._randomState.randint(0, self._internalResolutionY)
        src_region = cv.GetSubRect(self._bigNoizeMat, (posX, posY, srcWidth, srcHeight))
        if(useResize == True):
            cv.Resize(src_region, self._resizeMat, upScaler)
            cv.Copy(self._resizeMat, image, self._noizeMask)
        else:
            cv.Copy(src_region, image, self._noizeMask)
        return image

class PixelateEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)

        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY

        self._blockRange = math.sqrt(self._internalResolutionX) / 2.0

        self._oldAmount = -1.0

        self._blockMat = effectMat1

    def getName(self):
        return "Pixelate"

    def reset(self):
        pass

    def applyEffect(self, image, amount, mode, unused1, unused2, unused3):
        return self.blockifyImage(image, amount, mode)

    def blockifyImage(self, image, amount, mode):
        if(amount < 0.02):
            return image
        if(self._oldAmount != amount):
            sizeScale = 1.0 / (math.pow((self._blockRange * amount), 2))
            miniImageSizeX = int(self._internalResolutionX * sizeScale)
            miniImageSizeY = int(self._internalResolutionY * sizeScale)
            miniImageSizeX = min(max(1, miniImageSizeX), self._internalResolutionX)
            miniImageSizeY = min(max(1, miniImageSizeY), self._internalResolutionY)
#            print "DEBUG pcn: amount: " + str(amount) + " range: " + str(self._blockRange) + " scale: " + str(sizeScale) + " X: " + str(miniImageSizeX) + " Y: " + str(miniImageSizeY)
            self._blockMat = createMat(miniImageSizeX, miniImageSizeY)
        downScaler = cv.CV_INTER_CUBIC
        if(mode < 0.33):
            upScaler = cv.CV_INTER_NN #Clean
        elif(mode < 0.66):
            upScaler = cv.CV_INTER_CUBIC #Blobby roundish
        else:
            upScaler = cv.CV_INTER_LINEAR #Blobby star
        cv.Resize(image, self._blockMat, downScaler)
        cv.Resize(self._blockMat, image, upScaler)
        return image

class ScrollEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)

        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._scrollMat = effectMat1
        self._flipMat = None

    def findMode(self, value):
        modeSelected = int(value*1.99)
        if(modeSelected == ScrollModes.NoFlip):
            return ScrollModes.NoFlip
        elif(modeSelected == ScrollModes.Flip):
            return ScrollModes.Flip
        else:
            return ScrollModes.NoFlip

    def getName(self):
        return "Scroll"

    def reset(self):
        pass

    def applyEffect(self, image, xcenter, ycenter, mode, dummy3, dummy4):
        flipMode = self.findMode(mode)
        return self.scrollImage(image, xcenter, ycenter, flipMode, False)

    def scrollImage(self, image, xcenter, ycenter, flipMode, isNotRepeat):
        originalW, originalH = cv.GetSize(image)
        originalWidth = float(originalW)
        originalHeight = float(originalH)
        width = self._internalResolutionX
        height = self._internalResolutionY
        if(isNotRepeat == True):
#            print "NO REPEAT! " * 20
            left = int((originalWidth - width) * xcenter * 2.0)
            top = int((originalHeight - height) * ycenter * 2.0)
        elif(flipMode == ScrollModes.Flip):
            left = int(originalWidth * xcenter * 2.0)
            top = int(originalHeight * ycenter * 2.0)
            doubbleH = (originalH * 2)
            doubbleW = (originalW * 2)
        else:
            left = int(originalWidth * xcenter)
            top = int(originalHeight * ycenter)
        right = left + width
        bottom = top + height
        #print "Left: " + str(left) + " top: " + str(top) + " width: " + str(width) + " height: " + str(height)
        if(flipMode == ScrollModes.Flip):
            if(self._flipMat == None):
                self._flipMat = createMat(originalW, originalH)
            else:
                oldFlipW, oldFlipH = cv.GetSize(self._flipMat)
                if((oldFlipW != originalW) or (oldFlipH != originalH)):
                    self._flipMat = createMat(originalW, originalH)
        if(left < originalW):
            if(top < originalH):
                originalRight = right
                originalBottom = bottom
                if(right > originalW):
                    originalRight = originalW
                if(bottom > originalH):
                    originalBottom = originalH
                #print "1: Left: " + str(left) + " top: " + str(top) + " 'right: " + str(originalRight-left) + " 'bottom: " + str(originalBottom-top)
                src_region = cv.GetSubRect(image, (left, top, originalRight-left, originalBottom-top) )
                dst_region = cv.GetSubRect(self._scrollMat, (0, 0, originalRight-left, originalBottom-top) )
                cv.Copy(src_region, dst_region)
        if(right > originalW):
            if(flipMode == ScrollModes.Flip):
                if(left < doubbleW):
                    newWidth = right - originalW
                    newBottom = bottom
                    if(bottom > originalH):
                        newBottom = originalH
                    startLeft = 0
                    dstLeft = originalW - left
                    if(newWidth > originalW):
                        startLeft = left - originalW
                        newWidth = originalW - startLeft
                        dstLeft = 0
                    if((newBottom-top > 0) and (newWidth > 0)):
                        #print "2 1: dstLeft: " + str(dstLeft) + " top: " + str(top) + " 'newWidth: " + str(newWidth) + " 'newBottom-top: " + str(newBottom-top)
                        cv.Flip(image, self._flipMat, 1)
                        src_region = cv.GetSubRect(self._flipMat, (startLeft, top, newWidth, newBottom-top) )
                        dst_region = cv.GetSubRect(self._scrollMat, (dstLeft, 0, newWidth, newBottom-top) )
                        cv.Copy(src_region, dst_region)
                if(right > doubbleW):
                    newWidth = right - doubbleW
                    newBottom = bottom
                    if(bottom > originalH):
                        newBottom = originalH
                    if((newBottom-top > 0) and (newWidth > 0)):
                        #print "2 2: doubbleW-left: " + str(doubbleW-left) + " top: " + str(top) + " 'newWidth: " + str(newWidth) + " 'newBottom-top: " + str(newBottom-top)
                        src_region = cv.GetSubRect(image, (0, top, newWidth, newBottom-top) )
                        dst_region = cv.GetSubRect(self._scrollMat, (doubbleW-left, 0, newWidth, newBottom-top) )
                        cv.Copy(src_region, dst_region)
            elif(flipMode == ScrollModes.NoFlip):
                newWidth = right - originalW
                newBottom = bottom
                if(bottom > originalH):
                    newBottom = originalH
                if((newBottom-top > 0) and (newWidth > 0)):
                    #print "2: originalW-left: " + str(originalW-left) + " top: " + str(top) + " 'newWidth: " + str(newWidth) + " 'newBottom-top: " + str(newBottom-top)
                    src_region = cv.GetSubRect(image, (0, top, newWidth, newBottom-top) )
                    dst_region = cv.GetSubRect(self._scrollMat, (originalW-left, 0, newWidth, newBottom-top) )
                    cv.Copy(src_region, dst_region)
        if(bottom > originalH):
            if(flipMode == ScrollModes.Flip):
                if(top < doubbleH):
                    newHeight = bottom - originalH
                    newRight = right
                    if(right > originalW):
                        newRight = originalW
                    startTop = 0
                    destTop = originalH - top
                    if(newHeight > originalH):
                        startTop = top - originalH
                        newHeight = originalH - startTop
                        destTop = 0
                    if((newRight-left > 0) and (newHeight > 0)):
                        #print "3 1: destTop: " + str(destTop) + " top: " + str(top) + " 'newRight-left: " + str(newRight-left) + " 'newHeight: " + str(newHeight)
                        cv.Flip(image, self._flipMat, 0)
                        src_region = cv.GetSubRect(self._flipMat, (left, startTop, newRight-left, newHeight) )
                        dst_region = cv.GetSubRect(self._scrollMat, (0, destTop, newRight-left, newHeight) )
                        cv.Copy(src_region, dst_region)
                if(bottom > doubbleH):
                    newHeight = bottom - doubbleH
                    newRight = right
                    if(right > originalW):
                        newRight = originalW
                    if((newRight-left > 0) and (newHeight > 0)):
                        #print "3 2: left: " + str(left) + " doubbleH-top: " + str(doubbleH-top) + " 'newHeight: " + str(newHeight) + " 'newRight-left: " + str(newRight-left)
                        src_region = cv.GetSubRect(image, (left, 0, newRight-left, newHeight) )
                        dst_region = cv.GetSubRect(self._scrollMat, (0, doubbleH-top, newRight-left, newHeight) )
                        cv.Copy(src_region, dst_region)
            elif(flipMode == ScrollModes.NoFlip):
                newHeight = bottom - originalH
                newRight = right
                if(right > originalW):
                    newRight = originalW
                if((newRight-left > 0) and (newHeight > 0)):
                    #print "3: left: " + str(left) + " originalH-top: " + str(originalH-top) + " 'newHeight: " + str(newHeight) + " 'newRight-left: " + str(newRight-left)
                    src_region = cv.GetSubRect(image, (left, 0, newRight-left, newHeight) )
                    dst_region = cv.GetSubRect(self._scrollMat, (0, originalH-top, newRight-left, newHeight) )
                    cv.Copy(src_region, dst_region)
        if(bottom > originalH):
            if(right > originalW):
                if(flipMode == ScrollModes.Flip):
                    if( (top < doubbleH) and (left < doubbleW)):
                        newBottom = bottom
                        newRight = right
                        if(bottom >= doubbleH):
                            newBottom = doubbleH - 1
                        if(right >= doubbleW):
                            newRight = doubbleW - 1
                        newHeight = bottom - originalH
                        newWidth = right - originalW
                        newTop = originalH-top
                        newLeft = originalW-left
                        sourceLeft = 0
                        sourceTop = 0
                        if(newTop < 0):
                            sourceTop =  -newTop
                            newHeight += (newTop * 2)
                            newTop = 0
                        if(newLeft < 0):
                            sourceLeft =  -newLeft
                            newWidth += (newLeft * 2)
                            newLeft = 0
                        #print "4 1: newLeft: " + str(newLeft) + " newTop: " + str(newTop) + " 'newWidth: " + str(newWidth) + " 'newHeight: " + str(newHeight)
                        cv.Flip(image, self._flipMat, -1)
                        src_region = cv.GetSubRect(self._flipMat, (sourceLeft, sourceTop, newWidth, newHeight) )
                        dst_region = cv.GetSubRect(self._scrollMat, (newLeft, newTop, newWidth, newHeight) )
                        cv.Copy(src_region, dst_region)
                    if((right > doubbleW) and (top < doubbleH)):
                        newHeight = bottom - originalH
                        newWidth = right - doubbleW
                        newTop = originalH-top
                        sourceTop = 0
                        if(newTop < 0):
                            sourceTop =  -newTop
                            newHeight += (newTop * 2)
                            newTop = 0
                        #print "4 2: doubbleW-left: " + str(doubbleW-left) + " newTop: " + str(newTop) + " 'newWidth: " + str(newWidth) + " 'newHeight: " + str(newHeight)
                        cv.Flip(image, self._flipMat, 0)
                        src_region = cv.GetSubRect(self._flipMat, (0, sourceTop, newWidth, newHeight) )
                        dst_region = cv.GetSubRect(self._scrollMat, (doubbleW-left, newTop, newWidth, newHeight) )
                        cv.Copy(src_region, dst_region)
                    if((bottom > doubbleH) and (left < doubbleW)):
                        newWidth = right - originalW
                        newHeight = bottom - doubbleH
                        newLeft = originalW-left
                        sourceLeft = 0
                        if(newLeft < 0):
                            sourceLeft =  -newLeft
                            newWidth += (newLeft * 2)
                            newLeft = 0
                        #print "4 3: newLeft: " + str(newLeft) + " doubbleH-top: " + str(doubbleH-top) + " 'newWidth: " + str(newWidth) + " 'newHeight: " + str(newHeight)
                        cv.Flip(image, self._flipMat, 1)
                        src_region = cv.GetSubRect(self._flipMat, (sourceLeft, 0, newWidth, newHeight) )
                        dst_region = cv.GetSubRect(self._scrollMat, (newLeft, doubbleH-top, newWidth, newHeight) )
                        cv.Copy(src_region, dst_region)
                    if( (bottom > doubbleH) and (right > doubbleW)):
                        newHeight = bottom - doubbleH
                        newWidth = right - doubbleW
                        #print "4 4: doubbleW-left: " + str(doubbleW-left) + " doubbleH-top: " + str(doubbleH-top) + " 'newWidth: " + str(newWidth) + " 'newHeight: " + str(newHeight)
                        src_region = cv.GetSubRect(image, (0, 0, newWidth, newHeight) )
                        dst_region = cv.GetSubRect(self._scrollMat, (doubbleW-left, doubbleH-top, newWidth, newHeight) )
                        cv.Copy(src_region, dst_region)
                elif(flipMode == ScrollModes.NoFlip):
                    newHeight = bottom - originalH
                    newWidth = right - originalW
                    #print "4: originalW-left: " + str(originalW-left) + " originalH-top: " + str(originalH-top) + " 'newWidth: " + str(newWidth) + " 'newHeight: " + str(newHeight)
                    src_region = cv.GetSubRect(image, (0, 0, newWidth, newHeight) )
                    dst_region = cv.GetSubRect(self._scrollMat, (originalW-left, originalH-top, newWidth, newHeight) )
                    cv.Copy(src_region, dst_region)
        cv.Copy(self._scrollMat, image)
        return image

class FlipEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)

    def findMode(self, value):
        modeSelected = int(value*3.99)
        if(modeSelected == FlipModes.NoFlip):
            return FlipModes.NoFlip
        elif(modeSelected == FlipModes.Vertical):
            return FlipModes.Vertical
        elif(modeSelected == FlipModes.Horizontal):
            return FlipModes.Horizontal
        else:
            return FlipModes.Both

    def getName(self):
        return "Flip"

    def findValue(self, mode):
        if(mode == FlipModes.NoFlip):
            return None
        elif(mode == FlipModes.Vertical):
            return 1
        elif(mode == FlipModes.Horizontal):
            return 0
        else:
            return -1

    def reset(self):
        pass

    def applyEffect(self, image, amount, dummy1, dummy2, dummy3, dummy4):
        mode = self.findMode(amount)
        flipValue = self.findValue(mode)
        if(flipValue == None):
            return image
        else:
            return self.flipImage(image, flipValue)

    def flipImage(self, image, flipMode):
        cv.Flip(image, image, flipMode)
        return image

class BlurEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)

        self._blurMat = effectMat1

    def getName(self):
        return "Blur"

    def reset(self):
        pass

    def applyEffect(self, image, amount, mode, dummy2, dummy3, dummy4):
        return self.blurImage(image, amount, mode)

    def blurImage(self, image, value, mode):
        if(value < 0.01):
            return image
        xSize = 2 + int(value * 8)
        ySize = 2 + int(value * 6)
        if(mode < 0.5):
            smoothMode = cv.CV_BLUR
        else:
            smoothMode = cv.CV_BILATERAL
        cv.Smooth(image, self._blurMat, smoothMode, xSize, ySize)
        cv.Copy(self._blurMat, image)
        return image

class BluredContrastEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)

        self._blurMat1 = effectMat1

    def getName(self):
        return "BluredContrast"

    def reset(self):
        pass

    def applyEffect(self, image, amount, dummy1, dummy2, dummy3, dummy4):
        return self.blurMultiply(image, amount)

    def blurMultiply(self, image, value):
        if(value < 0.01):
            return image
        xSize = 2 + int(value * 8)
        ySize = 2 + int(value * 6)
        cv.Smooth(image, self._blurMat1, cv.CV_BLUR, xSize, ySize)
        cv.Mul(image, self._blurMat1, image, 0.005)
        return image

class FeedbackEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)

        self._radians360 = math.radians(360)
        self._gotMemory = False
        self._memoryMat = createMat(internalResX, internalResY)
        cv.SetZero(self._memoryMat)
        self._tmpMat = effectMat1
        self._replaceMask = effectMask1
        self._zoomEffect = ZoomEffect(configurationTree, internalResX, internalResY)

    def getName(self):
        return "Feedback"

    def reset(self):
        cv.SetZero(self._memoryMat)

    def applyEffect(self, image, amount, arg1, arg2, arg3, arg4):
        return self.addFeedbackImage(image, amount, arg1, arg2, arg3, arg4)

    def addFeedbackImage(self, image, value, invert, move, direction, zoom):
        if(value < 0.01):
            if(self._gotMemory == True):
                cv.SetZero(self._memoryMat)
            return image
        self._gotMemory = True
        #Fade
        calcValue = math.log10(10.0 + (90.0 * value)) - 1.0
        invertVal = -256 * invert
        cv.ConvertScaleAbs(self._memoryMat, self._tmpMat, calcValue, invertVal)
        addImage = self._tmpMat
        if((zoom > 0.003) or (move > 0.003)):
            zoom = 1.0 - zoom
            xcenter = 0.125 * move * math.cos(self._radians360 * -direction)
            ycenter =-0.125 * move * math.sin(self._radians360 * -direction)
            addImage = self._zoomEffect.zoomImage(addImage, xcenter, ycenter, zoom, zoom, 0.90, 0.10)
        cv.Add(image, addImage, self._memoryMat)
        cv.Copy(self._memoryMat, image)
        return image

class DelayEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)

        self._radians360 = math.radians(360)
        self._gotMemory = False
        self._memoryMat = createMat(internalResX, internalResY)
        cv.SetZero(self._memoryMat)
        self._tmpMat = effectMat1
        self._replaceMask = effectMask1
        self._zoomEffect = ZoomEffect(configurationTree, internalResX, internalResY)

    def getName(self):
        return "Delay"

    def reset(self):
        cv.SetZero(self._memoryMat)

    def applyEffect(self, image, amount, arg1, arg2, arg3, arg4):
        return self.addDelayImage(image, amount, arg1, arg2, arg3, arg4)

    def addDelayImage(self, image, value, lumaKey, move, direction, zoom):
        if(value < 0.01):
            if(self._gotMemory == True):
                cv.SetZero(self._memoryMat)
            return image
        self._gotMemory = True
        #Fade
        cv.ConvertScaleAbs(self._memoryMat, self._tmpMat, value, 0)
        tmpImage = self._tmpMat
        if((zoom > 0.003) or (move > 0.003)):
            zoom = 1.0 - zoom
            xcenter = 0.125 * move * math.cos(self._radians360 * -direction)
            ycenter =-0.125 * move * math.sin(self._radians360 * -direction)
            tmpImage = self._zoomEffect.zoomImage(self._tmpMat, xcenter, ycenter, zoom, zoom, 0.90, 0.30) #TODO: Fix the zoom range... Config?
        cv.Copy(tmpImage, self._memoryMat)
        cv.CvtColor(image, self._replaceMask, cv.CV_BGR2GRAY);
        if(lumaKey < 0.5):
            lumaThreshold = int(506 * lumaKey) + 3
            cv.CmpS(self._replaceMask, lumaThreshold, self._replaceMask, cv.CV_CMP_GT)
            cv.Copy(image, self._memoryMat, self._replaceMask)
        elif(lumaKey > 0.5):
            lumaThreshold = int(512 * (lumaKey - 0.5))
            cv.CmpS(self._replaceMask, lumaThreshold, self._replaceMask, cv.CV_CMP_LT)
            cv.Copy(image, self._memoryMat, self._replaceMask)
        cv.Copy(self._memoryMat, image)
        return image

class SelfDifferenceEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)

        self._currentPos = 0
        self._memoryLength = 10
        self._memoryArray = []
        for _ in range(self._memoryLength):
            self._memoryArray.append(getEmptyImage(internalResX, internalResY))
        self._diffMat = effectMat1

    def getName(self):
        return "SelfDifference"

    def reset(self):
        for i in range(self._memoryLength):
            cv.SetZero(self._memoryArray[i])

    def applyEffect(self, image, amount, contrast, invert, smooth, dummy4):
        return self.diffImage(image, amount, contrast, invert, smooth)

    def diffImage(self, image, delay, contrast, invert, smooth):
        delayFrames = int((delay * self._memoryLength) + 0.5)
        if(delayFrames <= 0):
            if(smooth > 0.02):
                xSize = 2 + int(smooth * 8)
                ySize = 2 + int(smooth * 6)
                cv.Smooth(image, self._memoryArray[self._currentPos], cv.CV_BLUR, xSize, ySize)
            else:
                copyOrResizeImage(image, self._memoryArray[self._currentPos])
            return image
        self._currentPos = (self._currentPos + 1) % self._memoryLength
        delayPos = (self._currentPos - delayFrames) % self._memoryLength
        cv.Sub(image, self._memoryArray[delayPos], self._diffMat)
        if(smooth > 0.02):
            xSize = 2 + int(smooth * 8)
            ySize = 2 + int(smooth * 6)
            cv.Smooth(image, self._memoryArray[self._currentPos], cv.CV_BLUR, xSize, ySize)
        else:
            copyOrResizeImage(image, self._memoryArray[self._currentPos])
#        print "DEBUG diffImage: currPos: " + str(self._currentPos) + " delayPos: " + str(delayPos) + " delayLength: " + str(delayFrames)
        if((contrast > 0.02) or (invert > 0.02)):
            contrastVal = 1.0 + (9.0 * contrast)
            invertVal = int(-256.0 * invert)
            cv.ConvertScaleAbs(self._diffMat, image, contrastVal, invertVal)
        else:
            cv.Copy(self._diffMat, image)
        return image

class DistortionEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)

        self._distortMat = effectMat1

    def getName(self):
        return "Distortion"

    def reset(self):
        pass

    def applyEffect(self, image, amount, mode, dummy2, dummy3, dummy4):
        return self.dilateErode(image, amount, mode)

    def findMode(self, value):
        modeSelected = int(value*2.99)
        if(modeSelected == DistortionModes.Black):
            return DistortionModes.Black
        elif(modeSelected == DistortionModes.White):
            return DistortionModes.White
        else:
            return DistortionModes.Both

    def dilateErode(self, image, value, mode):
        modeSelected = self.findMode(mode)
        if(modeSelected == DistortionModes.White):
            itterations = int(value * 64)
        elif(modeSelected == DistortionModes.Black):
            itterations = -int(value * 64)
        else:
            itterations = int(value * 128) - 64
        if(itterations == 0):
            return image
        if(itterations < 0):
            cv.Erode(image, self._distortMat, None, -itterations)
        else:
            cv.Dilate(image, self._distortMat, None, itterations)
        cv.Copy(self._distortMat, image)
        return image

class EdgeEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)

        self._colorMat = effectMat1
        self._maskMat = effectMask1
        self._splitMat = effectMask2
        self._edgeMat = effect16bitMask


    def getName(self):
        return "Distortion"

    def findMode(self, value):
        modeSelected = int(value*3.99)
        if(modeSelected == EdgeModes.CannyOnTop):
            return EdgeModes.CannyOnTop
        elif(modeSelected == EdgeModes.Canny):
            return EdgeModes.Canny
        elif(modeSelected == EdgeModes.Sobel):
            return EdgeModes.Sobel
        else:
            return EdgeModes.Laplace

    def findColorMode(self, value):
        modeSelected = int(value*2.99)
        if(modeSelected == EdgeColourModes.Value):
            return EdgeColourModes.Value
        elif(modeSelected == EdgeColourModes.Saturation):
            return EdgeColourModes.Saturation
        else:
            return EdgeColourModes.Hue


    def reset(self):
        pass

    def applyEffect(self, image, amount, mode, hsv, lineHue, lineSat):
        red, green, blue = modifyHue(getHueColor(lineHue), lineSat)
        edgeMode = self.findMode(mode)
        return self.drawEdges(image, amount, edgeMode, hsv, red, green, blue)

    def drawEdges(self, image, value, edgeMode, hsv, red, green, blue):
#        print "mode: " + str(mode) + " int: " + str(modeSelected) + " hsv: " + str(hsv) + " red: " + str(red) + " green: " + str(green) + " blue: " + str(blue)
        if((edgeMode == EdgeModes.CannyOnTop) or (edgeMode == EdgeModes.Canny)):
            hsvSelected = self.findColorMode(hsv)
        else:
            hsvSelected = EdgeColourModes.Value
        cv.CvtColor(image, self._colorMat, cv.CV_RGB2HSV)
        if(hsvSelected == EdgeColourModes.Value):
            cv.Split(self._colorMat, None, None, self._splitMat, None)
        elif(hsvSelected == EdgeColourModes.Saturation):
            cv.Split(self._colorMat, None, self._splitMat, None, None)
        else:
            cv.Split(self._colorMat, self._splitMat, None, None, None)
        if((edgeMode == EdgeModes.CannyOnTop) or (edgeMode == EdgeModes.Canny)):
            if((value < 0.01) and (edgeMode == EdgeModes.CannyOnTop)):
                return image
            threshold = 256 - int(value * 256)
            cv.Canny(self._splitMat, self._maskMat, threshold, threshold * 2, 3)
#            if(edgeMode == EdgeModes.CannyOnTop):
            storage = cv.CreateMemStorage(0)
            if(edgeMode == EdgeModes.Canny):
                cv.SetZero(image)
            contour = cv.FindContours(self._maskMat, storage,  cv.CV_RETR_TREE, cv.CV_CHAIN_APPROX_SIMPLE, (0,0))
            cv.DrawContours(image, contour, cv.RGB(red, green, blue), cv.RGB(red, green, blue), 20, thickness=2)
            return image
#            else: # Canny
#                cv.CvtColor(self._maskMat, self._colorMat, cv.CV_GRAY2RGB)
#                return self._colorMat
        else:
            if(edgeMode == EdgeModes.Sobel):
                mode = int(value * 3.99)
                if(mode == 0):
                    (sobelX, sobelY) = (1, 0)
                    order = 5
                elif(mode == 1):
                    (sobelX, sobelY) = (1, 0)
                    order = 3
                elif(mode == 2):
                    (sobelX, sobelY) = (0, 1)
                    order = 3
                else:
                    (sobelX, sobelY) = (0, 1)
                    order = 5
                cv.Sobel(self._splitMat, self._edgeMat, sobelX, sobelY, order)
            else: # Laplace
                aparture = 1 + (2 * int(value * 5.99))
                cv.Laplace(self._splitMat, self._edgeMat, aparture)                
            cv.ConvertScale(self._edgeMat, self._maskMat, 0.5)
            cv.CvtColor(self._maskMat, image, cv.CV_GRAY2RGB)
            return image

class DesaturateEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)

        self._colorMat = effectMat1
        self._maskMat = effectMask1
        self._hueMat = effectMask2
        self._sat1Mat = effectMask3
        self._sat2Mat = effectMask4
        self._valMat = effectMask5

    def findMode(self, value):
        modeSelected = int(value*2.99)
        if(modeSelected == DesaturateModes.Plus):
            return DesaturateModes.Plus
        elif(modeSelected == DesaturateModes.Minus):
            return DesaturateModes.Minus
        else:
            return DesaturateModes.Mask

    def getName(self):
        return "Desaturate"

    def reset(self):
        pass

    def applyEffect(self, image, value, valRange, mode, dummy3, dummy4):
        satMode = self.findMode(mode)
        return self.selectiveDesaturate(image, value, valRange, satMode)

    def selectiveDesaturate(self, image, value, valRange, satMode):
        hueValue = (value * 180)
        huePlussMinus = 1 + (valRange * 39)
        satMin = int(160 - (100 * valRange))
        hueMin = int(max(0, hueValue - huePlussMinus))
        hueMax = int(min(256, hueValue + huePlussMinus))
        cv.CvtColor(image, self._colorMat, cv.CV_RGB2HSV)
        cv.InRangeS(self._colorMat, (hueMin, satMin, 32), (hueMax, 255, 255), self._maskMat)
        if(satMode != DesaturateModes.Mask):
            cv.Split(self._colorMat, self._hueMat, self._sat1Mat, self._valMat, None)
            if(satMode == DesaturateModes.Plus):
                cv.Mul(self._sat1Mat, self._maskMat, self._sat2Mat, 0.004)
            else: # Minus
                cv.Sub(self._sat1Mat, self._maskMat, self._sat2Mat)
            cv.Smooth(self._sat2Mat, self._sat1Mat, cv.CV_BLUR, 8, 6)
            cv.Merge(self._hueMat, self._sat1Mat, self._valMat, None, self._colorMat)
            cv.CvtColor(self._colorMat, image, cv.CV_HSV2RGB)
        else:
            cv.CvtColor(self._maskMat, image, cv.CV_GRAY2RGB)
        return image

class ContrastBrightnessEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)

    def findMode(self, value):
        modeSelected = int(value*3.99)
        if(modeSelected == ContrastModes.Increase):
            return ContrastModes.Increase
        elif(modeSelected == ContrastModes.IncDec):
            return ContrastModes.IncDec
        elif(modeSelected == ContrastModes.Decrease):
            return ContrastModes.Decrease
        else:
            return ContrastModes.Full

    def getName(self):
        return "ContrastBrightness"

    def reset(self):
        pass

    def applyEffect(self, image, contrast, brightness, mode, dummy3, dummy4):
        return self.contrastBrightness(image, contrast, brightness, self.findMode(mode))

    def contrastBrightness(self, image, contrast, brightness, mode):
        if(mode == ContrastModes.Full):
            contrast = (2 * contrast) -1.0
            brightnessVal = (512 * brightness) - 256 #TODO: Fix negative brightness
        if(mode == ContrastModes.Increase):
            contrastVal = contrast
            brightnessVal = 256 * brightness
        if(mode == ContrastModes.IncDec):
            contrastVal = contrast
            brightnessVal = -256 * brightness #TODO: Fix negative brightness
        if(mode == ContrastModes.Decrease):
            contrastVal = 1.0 - contrast
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
            cv.ConvertScaleAbs(image, image, contrastVal, brightnessVal)
            return image

class HueSaturationEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)

        self._colorMat = effectMat1

    def findMode(self, value):
        modeSelected = int(value*2.99)
        if(modeSelected == HueSatModes.Increase):
            return HueSatModes.Increase
        elif(modeSelected == HueSatModes.Decrease):
            return HueSatModes.Decrease
        else:
            return HueSatModes.Full

    def getName(self):
        return "HueSaturation"

    def reset(self):
        pass

    def applyEffect(self, image, hueRot, saturation, brightness, mode, dummy4):
        return self.hueSaturationBrightness(image, hueRot, saturation, brightness, self.findMode(mode))

    def hueSaturationBrightness(self, image, rotate, saturation, brightness, mode):
        cv.CvtColor(image, self._colorMat, cv.CV_RGB2HSV)
        rotCalc = (((rotate * 512) + 256) % 512) - 256
        if(mode == HueSatModes.Increase):
            satCalc = int(saturation * -256)
            brightCalc = int(brightness * -256)
        elif(mode == HueSatModes.Decrease):
            satCalc = int(saturation * 256)
            brightCalc = int(brightness * 256)
        else: #(mode == HueSatModes.Full):
            satCalc = int(saturation * -512) + 256
            brightCalc = int(brightness * -512) + 256
        darkCalc = None
        if(brightCalc < 0):
            darkCalc = float(256 - brightCalc) / 256.0
            brightCalc = 0
#        print "DEBUG hueSat: rot: " + str(rotCalc) + " sat: " + str(satCalc) + " bright: " + str((brightness, brightCalc)) + " dark: " + str(darkCalc)
        rgbColor = cv.CV_RGB(brightCalc, satCalc, rotCalc)
        cv.SubS(self._colorMat, rgbColor, self._colorMat)
        cv.CvtColor(self._colorMat, image, cv.CV_HSV2RGB)
        if(darkCalc != None):
            cv.ConvertScaleAbs(image, image, darkCalc, 0)
        return image


class ColorizeEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)

        self._colorMat = effectMat1

    def getName(self):
        return "Colorize"

    def findMode(self, val):
        intVal = int(val*3.99)
        if(intVal == ColorizeModes.Add):
            return ColorizeModes.Add
        elif(intVal == ColorizeModes.Subtract):
            return ColorizeModes.Subtract
        elif(intVal == ColorizeModes.SubtractFrom):
            return ColorizeModes.SubtractFrom
        else:
            return ColorizeModes.Multiply

    def reset(self):
        pass

    def applyEffect(self, image, amount, red, green, blue, modeVal):
        mode = self.findMode(modeVal)
        return self.colorize(image, amount, red, green, blue, mode)

    def colorize(self, image, amount, red, green, blue, mode):
        if((mode == ColorizeModes.Add) or (mode == ColorizeModes.Subtract)):
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
    
        if(mode == ColorizeModes.Add):
            cv.AddS(image, rgbColor, image)
        elif(mode == ColorizeModes.Subtract):
            cv.SubS(image, rgbColor, image)
        elif(mode == ColorizeModes.SubtractFrom):
            cv.SubRS(image, rgbColor, image)
        elif(mode == ColorizeModes.Multiply):
            cv.Set(self._colorMat, rgbColor)
            cv.Mul(image, self._colorMat, image, 0.004)
        else:
            cv.AddS(image, rgbColor, image)
        return image

class InvertEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)

    def getName(self):
        return "Invert"

    def reset(self):
        pass

    def applyEffect(self, image, amount, dummy1, dummy2, dummy3, dummy4):
        return self.invert(image, amount)

    def invert(self, image, amount):
        brightnessVal = -255 * amount
        if((brightnessVal > -1) and (brightnessVal < 1)):
#            print "DEBUG no invert brightnessVal: " + str(brightnessVal) + " amount: " + str(amount)
            return image
        else:
#            print "DEBUG invert brightnessVal: " + str(brightnessVal) + " amount: " + str(amount)
            cv.ConvertScaleAbs(image, image, 1.0, brightnessVal)
            return image

class ValueToHueEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)
        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._colourMat = effectMat1
        self._hueMat = effectMask1
        self._satMat = effectMask2
        self._valMat = effectMask3

    def getName(self):
        return "ValueToHue"

    def reset(self):
        pass

    def _findMode(self, modeVal):
        modeSelected = int(3.99 * modeVal)
        if(modeSelected == ValueToHueModes.Off):
            return ValueToHueModes.Off
        elif(modeSelected == ValueToHueModes.Value):
            return ValueToHueModes.Value
        elif(modeSelected == ValueToHueModes.Saturation):
            return ValueToHueModes.Saturation
        else:
            return ValueToHueModes.Hue

    def applyEffect(self, image, modeVal, rotate, saturate, dummy3, dummy4):
        mode = self._findMode(modeVal)
        return self.processImage(image, mode, rotate, saturate)

    def processImage(self, image, mode, rotate, saturate):
        if(mode == ValueToHueModes.Off):
            return image
        cv.CvtColor(image, self._colourMat, cv.CV_RGB2HSV)
        if(mode == ValueToHueModes.Value):
            cv.Split(self._colourMat, None, None, self._valMat, None)
        elif(mode == ValueToHueModes.Saturation):
            cv.Split(self._colourMat, None, self._valMat, None, None)
        else:
            cv.Split(self._colourMat, self._valMat, None, None, None)
        if(rotate > 0.02):
            rotateVal = int(256.0 * rotate)
            cv.SubS(self._valMat, rotateVal, self._hueMat)
            hueMat = self._hueMat
        else:
            hueMat = self._valMat
        if(saturate > 0.02):
            contrastVal = 1 + (9.0 * saturate)
            cv.ConvertScaleAbs(self._valMat, self._satMat, contrastVal, 0)
            satMat = self._satMat
        else:
            satMat = self._valMat
        cv.Merge(hueMat, satMat, self._valMat, None, self._colourMat)
        cv.CvtColor(self._colourMat, image, cv.CV_HSV2RGB)
        return image

class ThresholdEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)

        self._thersholdMask = effectMask1

    def getName(self):
        return "Threshold"

    def reset(self):
        pass

    def applyEffect(self, image, amount, dummy1, dummy2, dummy3, dummy4):
        return self.threshold(image, amount)

    def threshold(self, image, threshold):
        threshold = 256 - (256 * threshold)
        cv.CvtColor(image, self._thersholdMask, cv.CV_BGR2GRAY);
        cv.CmpS(self._thersholdMask, threshold, self._thersholdMask, cv.CV_CMP_GT)
        cv.Merge(self._thersholdMask, self._thersholdMask, self._thersholdMask, None, image)
        return image

class ImageAddEffect(object):
    def __init__(self, configurationTree, effectImagesConfiguration, internalResX, internalResY):
        self._configurationTree = configurationTree
        self._imageConfiguration = effectImagesConfiguration
        self._videoDirectory = self._imageConfiguration.getVideoDir()
        if(self._videoDirectory == None):
            self._videoDirectory = ""
        setupEffectMemory(internalResX, internalResY)
        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._maskId = 0
        self._maskImage = None
        self._addId = 0
        self._addImage = None

    def loadImage(self, fileName):
        image = None
        imageFileName = os.path.normpath(fileName)
        fullFilePath = os.path.join(os.path.normpath(self._videoDirectory), imageFileName)
        packageFilePath = os.path.join(os.getcwd(), "testFiles", imageFileName)
        if(os.path.isfile(fullFilePath) == False):
            fullFilePath = packageFilePath
        try:
            image = cv.LoadImage(fullFilePath)
            imageSize = cv.GetSize(image)
            if((imageSize[0] != self._internalResolutionX) or (imageSize[1] != self._internalResolutionY)):
                scaleMat = createMat(self._internalResolutionX, self._internalResolutionY)
                cv.Resize(image, scaleMat)
                image =  scaleMat
        except:
            print "Exception while reading effect image: " + fileName
        return image

    def getImage(self, imageId):
        imageList  = self._imageConfiguration.getChoices()
        numImages = len(imageList)
        if(numImages < 1):
            return None
        if(imageId >= numImages):
            imageId = numImages -1
        if(len(effectImageList) < numImages):
            for i in range(len(effectImageList), numImages):
                fileName = imageList[i]
                image = self.loadImage(fileName)
                effectImageList.append(image)
                effectImageFileNameList.append(fileName)
        imageFileName = imageList[imageId]
        oldImageName = effectImageFileNameList[imageId]
        if(imageFileName != oldImageName):
            newImage = self.loadImage(imageFileName)
            effectImageList [imageId] = newImage
            effectImageFileNameList[imageId] = imageFileName
        return effectImageList[imageId]

    def _updateMask(self, maskId):
        if(self._maskId != maskId):
            self._maskId = maskId
            if(maskId < 1):
                self._maskImage = None
            else:
                self._maskImage = self.getImage(maskId - 1)

    def _updateAddImage(self, addId):
        if(self._addId != addId):
            self._addId = addId
            if(addId < 1):
                self._addImage = None
            else:
                self._addImage = self.getImage(addId - 1)
            
    def getName(self):
        return "ImageAdd"

    def reset(self):
        pass

    def applyEffect(self, image, maskId, imageId, mode, dummy3, dummy4):
        return self.mask(image, maskId, imageId, mode)

    def mask(self, image, maskId, imageId, mode):
        maskId = int(maskId * 63)
        self._updateMask(maskId)
        if(self._maskImage != None):
            cv.Mul(image, self._maskImage, image, 0.004)
        imageId = int(imageId * 63)
        self._updateAddImage(imageId)
        if(self._addImage != None):
            cv.Add(image, self._addImage, image)
        return image

#TODO: add effects
#class SliceEffect(object):

#class StutterEffect(object):
#class FreezeFx(object):

#class BaerturEffect(object): #Sigle frame feedback ish ;-)

#class EchoEffect2(object):

#class CurveEffect(object):
#class CromaKeyGeneratorEffect(object):

#??? TODO ???
#get coordinates from image blob (I want better tracking (or sorting if you like))
#Redo clip overview (use more space)
#Showoff DEMO
#make ModulationValueMode available and Move ModulationValueMode to EffectConfig.
#Dont reload all thumbs on config update (only for changed media.) Optemizing ;-)

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!! Embedd licence information !!!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

#ADSR add A AHoldR HoldR modes
#DMX512
#Tap tempo
#Playback GUI
#UDP -> multicast
#Improve thumb requests (bulk thumb requests?)

#install gimp on mac

#Lage teaser video
#Make default config more showoffy/complete (TaktDemo ;-) )

#Debugging.
#Check in blip on verse on RulleIGlassskaar, Effects related?
#FFull path bug: could be when importing multipple files (DnD)
#Redo baertur with time modulation (started)
#Make Rygg I Rand project (started)
#Make Elg project (started)


#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!      Full HD Demo/test        !!!
#!!! More complete startup program !!!
#!!!          Fancy demo           !!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

#Media:
#Video with alpha channel
#Sprite size / zoom (Text media also)
#TextMedia font directory config.
#Recording / resampler.
#Bypass media or (FX media.)
#    Send to locked midi channel?
#Complex looping (rollin, rollout, keep last?) (Under time modulation?)

