'''
Created on 24. jan. 2012

@author: pcn
'''
import cv2
from cv2 import cv
import numpy
from video.EffectModes import EffectTypes, ZoomModes, FlipModes, DistortionModes,\
    EdgeModes, DesaturateModes, ColorizeModes, EdgeColourModes, getEffectId,\
    ScrollModes, ContrastModes, HueSatModes, ValueToHueModes, BlobDetectModes,\
    SlitDirections
import math
import os
import time
import sys
from utilities.FloatListText import textToFloatValues
from video.Curve import Curve

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

randomStateHolder  = numpy.random.RandomState(int(time.time()))

def createNoizeMatAndMask(width, heigth):
    try:
        noizeMat = createMat(width, heigth)
        randomArray = randomStateHolder.randint(0, 255, size=(heigth, width)).astype(numpy.uint8)
        tmpNoizeMask = cv.fromarray(randomArray)
        cv.Merge(tmpNoizeMask, tmpNoizeMask, tmpNoizeMask, None, noizeMat)
        randomArray = randomStateHolder.randint(0, 255, size=(heigth, width)).astype(numpy.uint8)
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

def showCvImage(image, num = 1):
    cv.ShowImage("TAKT debug " + str(num), image)

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
    elif(effectType == EffectTypes.Rays):
        return RaysEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.SlitScan):
        return SlitEffect(configurationTree, internalResX, internalResY)
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
    elif(effectType == EffectTypes.Curve):
        return CurveEffect(configurationTree, internalResX, internalResY)
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
    elif(effectType == EffectTypes.Strobe):
        return StrobeEffect(configurationTree, internalResX, internalResY)
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
invertMat1 = None
invertMat2 = None
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
    global invertMat1
    global invertMat2
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
        invertMat1 = createMat(heigth, width)
        invertMat2 = createMat(heigth, width)
        bigNoizeMat, bigNoizeMask = createNoizeMatAndMask(width*2, heigth*2)

def getNoizeMask(level, internalRezX, internalRezY, scaleValue):
    if(scaleValue <= 1.05):
        useResize = False
        scaleX = internalRezX
        scaleY = internalRezY
    else:
        useResize = True
        scaleX = int(internalRezX / scaleValue)
        scaleY = int(internalRezY / scaleValue)
    posX = randomStateHolder.randint(0, internalRezX)
    posY = randomStateHolder.randint(0, internalRezY)
    src_region = cv.GetSubRect(bigNoizeMask, (posX, posY, scaleX, scaleY))
    threshold = int(255 * level)
    if(useResize == True):
        cv.Resize(src_region, effectMask1, cv.CV_INTER_NN)
        cv.CmpS(effectMask1, threshold, effectMask1, cv.CV_CMP_LT)
    else:
        cv.CmpS(src_region, threshold, effectMask1, cv.CV_CMP_LT)
    return effectMask1
        
radians360 = math.radians(360)

def angleAndMoveToXY(angle, move):
    angle360 = angle * 360
    if(angle360 < 45.0):
        moveX = -move
        moveY = math.tan(radians360 * angle) * -move
    elif(angle360 < 135):
        moveX = math.tan(radians360 * (angle-0.25)) * move
        moveY = -move
    elif(angle360 < 225):
        moveX = move
        moveY = math.tan(radians360 * (angle-0.5)) * move
    elif(angle360 < 315):
        moveX = math.tan(radians360 * (angle-0.75)) * -move
        moveY = move
    else:
        moveX = -move
        moveY = math.tan(radians360 * angle) * -move
    return moveX, moveY

def rotatePoint(angle, pointX, pointY, orginX, orginY, angle3d = None):
    relativeX = pointX - orginX
    relativeY = pointY - orginY
    if(angle3d != None):
        sinVal = math.sin(-angle*0.5*radians360)
        cosVal = math.cos(-angle*0.5*radians360)
        xrotated = ((relativeX * cosVal) - (relativeY*sinVal)) * math.cos(angle3d* radians360)
        yrotated = (relativeX * sinVal) + (relativeY * cosVal)
        sinVal = math.sin(angle*0.5*radians360)
        cosVal = math.cos(angle*0.5*radians360)
        xfinished = ((xrotated * cosVal) - (yrotated * sinVal))
        yfinished = (xrotated * sinVal) + (yrotated * cosVal)
        return xfinished + orginX, yfinished + orginY
    else:
        sinVal = math.sin(angle*radians360)
        cosVal = math.cos(angle*radians360)
        xrotated = ((relativeX * cosVal) - (relativeY * sinVal))
        yrotated = (relativeX * sinVal) + (relativeY * cosVal)
        return xrotated + orginX, yrotated + orginY

class ZoomEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)
        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._halfResolutionX = internalResX / 2
        self._halfResolutionY = internalResY / 2

        self._zoomModesHolder = ZoomModes()
        self._zoomMode = ZoomModes.In
        self._setZoomRange(0.25, 4.0)

        self._zoomMat = effectMat1
        self._zoomMask = effectMask1

    def setExtraConfig(self, values):
#        print("DEBUG pcn: Zoom::setExtraConfig() " + str(values))
        if(values != None):
            zoomModeString, zoomRangeString = values
            if(zoomModeString == None):
                self._zoomMode = ZoomModes.In
            else:
                self._zoomMode = self._zoomModesHolder.findMode(zoomModeString)
            if(zoomRangeString == None):
                self._setZoomRange(0.25, 4.0)
            else:
                minZoom, maxZoom = textToFloatValues(zoomRangeString, 2)
                self._setZoomRange(minZoom, maxZoom)

    def _setZoomRange(self, minZoom, maxZoom):
        if(minZoom < 0.004):
            maxZoomRange = 256.0
        elif(minZoom > 1.0):
            maxZoomRange = 1.0
        else:
            maxZoomRange = 1.0 / minZoom
        if(maxZoom >= 256.0):
            maxZoom = 256.0
        elif(maxZoom < 1.0):
            maxZoom = 1.0

        self._maxZoomTimes = maxZoomRange
        self._minZoomTimes = maxZoom
        #maxZoom is a bit confusing since it is flipped in this function. It is used here at the zero zoom point.

    def getName(self):
        return "Zoom"

    def reset(self):
        pass

    def calculateZoom(self, zoom, minZoomTimes, maxZoomTimes):
        if(zoom < 0.5):
            zoomCalc = 1.0 / (1.0 + (((0.5-zoom) * 2) * (minZoomTimes-1.0)))
        else:
            zoomCalc = 1.0 + (((zoom - 0.5) * 2) * (maxZoomTimes - 1))
        return zoomCalc

    def applyEffect(self, image, songPosition, amount, xcenter, ycenter, flip, angle, minZoomTimes = None, maxZoomTimes = None):
        zoom = 1.0 - amount

        if(minZoomTimes == None):
            minZoomTimes = self._minZoomTimes
        else:
            self._zoomMode = ZoomModes.Full
        if(maxZoomTimes == None):
            maxZoomTimes = self._maxZoomTimes
        else:
            self._zoomMode = ZoomModes.Full
        if(self._zoomMode != ZoomModes.Full):
            xcenter = 0.5
            ycenter = 0.5
            flip = 0.0
            angle = 0.0
        if(self._zoomMode == ZoomModes.Out):
            zoomCalc = 1.0 + ((maxZoomTimes - 1.0) * (1.0 - zoom))
        elif(self._zoomMode == ZoomModes.In):
            zoomCalc = 1.0 / (1.0 + ((minZoomTimes - 1.0) * (1.0 - zoom)))
        else:
            zoomCalc = self.calculateZoom(zoom, minZoomTimes, maxZoomTimes)

        return self.zoomImageTransform(image, xcenter, ycenter, zoomCalc, angle, flip, 0.0)

    def zoomImageTransform(self, image, xcenter, ycenter, zoom, xAngle, xRotation, zRotation, imageMask = None):
#        print "DEBUG pcn: zoomImageTransform( " + str((xcenter, ycenter, zoom, xAngle, xRotation, zRotation))
        ycenter = 1.0 - ycenter
        originalW, originalH = cv.GetSize(image)
        originalWidth = float(originalW)
        originalHeight = float(originalH)
        width = int(originalWidth * zoom)
        height = int(originalHeight * zoom)
        if((width < 1) or (height < 1)):
            cv.SetZero(image)
            return image
        left = int((originalWidth / 2) - (width / 2))
        top = int((originalHeight / 2) - (height / 2))
        extraMultiplyer = 0.6 + (0.4/zoom)
        xAdd = ((self._internalResolutionX * 2.0 * xcenter) - self._internalResolutionX) * extraMultiplyer
        yAdd = ((self._internalResolutionY * 2.0 * ycenter) - self._internalResolutionY) * extraMultiplyer
#        print "Left: " + str(left) + " top: " + str(top) + " xc: " + str(originalWidth * xcenter) + " yc: " + str(originalHeight * ycenter) + " size: " + str((width, height))
        srcPoints = ((left, top),(left,top+height),(left+width, top))
        destPoint1 = (0.0, 0.0)
        destPoint2 = (0.0, self._internalResolutionY)
        destPoint3 = (self._internalResolutionX, 0.0)
        if(xRotation != 0.0):
            xAngle += 0.5
            destPoint1 = rotatePoint(xAngle, destPoint1[0], destPoint1[1], self._halfResolutionX, self._halfResolutionY, xRotation)
            destPoint2 = rotatePoint(xAngle, destPoint2[0], destPoint2[1], self._halfResolutionX, self._halfResolutionY, xRotation)
            destPoint3 = rotatePoint(xAngle, destPoint3[0], destPoint3[1], self._halfResolutionX, self._halfResolutionY, xRotation)
        if(zRotation != 0.0):
            destPoint1 = rotatePoint(-zRotation, destPoint1[0], destPoint1[1], self._halfResolutionX, self._halfResolutionY)
            destPoint2 = rotatePoint(-zRotation, destPoint2[0], destPoint2[1], self._halfResolutionX, self._halfResolutionY)
            destPoint3 = rotatePoint(-zRotation, destPoint3[0], destPoint3[1], self._halfResolutionX, self._halfResolutionY)
        dstPoints = ((destPoint1[0]+xAdd, destPoint1[1]+yAdd),(destPoint2[0]+xAdd, destPoint2[1]+yAdd),(destPoint3[0]+xAdd,destPoint3[1]+yAdd))
        zoomMatrix = cv.CreateMat(2,3,cv.CV_32F)
#        print "DEBUG pcn: trasform points source: " + str(srcPoints) + " dest: " + str(dstPoints) 
        cv.GetAffineTransform(srcPoints, dstPoints, zoomMatrix)
        cv.WarpAffine(image, self._zoomMat, zoomMatrix)
        if(imageMask != None):
            cv.WarpAffine(imageMask, self._zoomMask, zoomMatrix)
            cv.Copy(self._zoomMask, imageMask)
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

    def applyEffect(self, image, songPosition, mode, rotate, move, direction, unused1):
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

    def applyEffect(self, image, songPosition, amount, move, direction, zoom, unused1):
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

    def applyEffect(self, image, songPosition, blobFilter, mode, lineHue, lineSat, lineWeight):
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

    def applyEffect(self, image, songPosition, amount, scale, mode, unused1, unused2):
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
        posX = randomStateHolder.randint(0, self._internalResolutionX)
        posY = randomStateHolder.randint(0, self._internalResolutionY)
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
        posX = randomStateHolder.randint(0, self._internalResolutionX)
        posY = randomStateHolder.randint(0, self._internalResolutionY)
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
        self._colourTableMat = cv.CreateMat(1, 256, cv.CV_8UC1)
        self._updateTable(16)

    def getName(self):
        return "Pixelate"

    def reset(self):
        pass

    def _updateTable(self, quantize):
        stepSize = 256.0 / quantize
        for i in range(256):
            if(int(i/stepSize) == 0):
                cv.Set1D(self._colourTableMat, i, 0)
            else:
                cv.Set1D(self._colourTableMat, i, int((1+int(i/stepSize))*stepSize))
        self._colourTableLastValue = quantize

    def applyEffect(self, image, songPosition, amount, mode, colours, unused2, unused3):
        return self.blockifyImage(image, amount, mode, colours)

    def blockifyImage(self, image, amount, mode, colours):
        if(amount > 0.01):
            if(self._oldAmount != amount):
                sizeScale = 1.0 / (math.pow((self._blockRange * amount), 2))
                miniImageSizeX = int(self._internalResolutionX * sizeScale)
                miniImageSizeY = int(self._internalResolutionY * sizeScale)
                miniImageSizeX = min(max(1, miniImageSizeX), self._internalResolutionX)
                miniImageSizeY = min(max(1, miniImageSizeY), self._internalResolutionY)
#                print "DEBUG pcn: amount: " + str(amount) + " range: " + str(self._blockRange) + " scale: " + str(sizeScale) + " X: " + str(miniImageSizeX) + " Y: " + str(miniImageSizeY)
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
        if(colours > 0.01):
            colVal = 1.0 - colours
            quantize = 2 + int(colVal * 30)
            if(self._colourTableLastValue != quantize):
                self._updateTable(quantize)
            cv.LUT(image, image, self._colourTableMat)
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

    def applyEffect(self, image, songPosition, xcenter, ycenter, mode, dummy3, dummy4):
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

    def applyEffect(self, image, songPosition, amount, dummy1, dummy2, dummy3, dummy4):
        mode = self.findMode(amount)
        flipValue = self.findValue(mode)
        if(flipValue == None):
            return image
        else:
            return self.flipImage(image, flipValue)

    def flipImage(self, image, flipMode):
        cv.Flip(image, image, flipMode)
        return image

class RaysEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._halfX = int(self._internalResolutionX / 2)
        self._halfY = int(self._internalResolutionY / 2)
        setupEffectMemory(internalResX, internalResY)

        self._mirrorMat = effectMat1
        self._invertImageMat = invertMat1
        self._invertMirrorMat = invertMat2

    def getName(self):
        return "Rays"

    def reset(self):
        pass

    def applyEffect(self, image, songPosition, amount, bend, mode, horizontal, dummy4):
        return self.rayEffect(image, amount, bend, mode, horizontal)

    def rayEffect(self, image, amount, bend, mode, horizontal):
        if(mode < 0.75):
            if(amount < 0.001):
                return image
        scaleCalcX = 0.9 + ((1.0 - amount) * 0.1)
        scaleCalcY = 1.0 - ((1.0 - scaleCalcX) * (1.0 + (3* bend)))
        if(horizontal < 0.5):
            xSize = self._internalResolutionX
            ySize = self._internalResolutionY
            halfY = self._halfY
            workImage = image
            workMirrorMat = self._mirrorMat
        else:
            xSize = self._internalResolutionY
            ySize = self._internalResolutionX
            halfY = self._halfX
            cv.Transpose(image, self._invertImageMat)
            workImage = self._invertImageMat
            workMirrorMat = self._invertMirrorMat
        sourceSizeX = int(xSize * scaleCalcX)
        sourceSizeY = int(ySize * scaleCalcY)
        sourcePosX = int((xSize - sourceSizeX) / 2)
        sourcePosY = int((ySize - sourceSizeY) / 2)
#        print "DEBUG pcn: amount: " + str(amount) + " mode: " + str(mode)
        if(mode < 0.25):
            src_region = cv.GetSubRect(workImage, (sourcePosX, sourcePosY, sourceSizeX, sourceSizeY))
            cv.Resize(src_region, workImage)
        elif(mode < 0.5):
            cv.Flip(workImage, workMirrorMat, 0)
            src_region = cv.GetSubRect(workMirrorMat, (sourcePosX, sourcePosY, sourceSizeX, sourceSizeY))
            cv.Resize(src_region, workMirrorMat)
            cv.Flip(workMirrorMat, workImage, 0)
        elif(mode < 0.75):
            cv.Flip(workImage, workMirrorMat, 0) #Make flip copy for upper rays
            src_region = cv.GetSubRect(workImage, (sourcePosX, sourcePosY, sourceSizeX, sourceSizeY))
            cv.Resize(src_region, workImage)
            src_region = cv.GetSubRect(workMirrorMat, (sourcePosX, sourcePosY, sourceSizeX, sourceSizeY))
            cv.Resize(src_region, workMirrorMat)
            cv.Flip(workMirrorMat, workMirrorMat, 0) #Flip back
            src_region = cv.GetSubRect(workMirrorMat, (0, 0, xSize, halfY))
            dst_region = cv.GetSubRect(workImage, (0, 0 , xSize, halfY))
            cv.Copy(src_region, dst_region)
        else:
            src_region = cv.GetSubRect(workImage, (sourcePosX, sourcePosY, sourceSizeX, sourceSizeY))
            cv.Resize(src_region, workImage)
            cv.Flip(workImage, workMirrorMat, 0)
            src_region = cv.GetSubRect(workMirrorMat, (0, 0, xSize, halfY))
            dst_region = cv.GetSubRect(workImage, (0, 0 , xSize, halfY))
            cv.Copy(src_region, dst_region)
        if(horizontal >= 0.5):
            cv.Transpose(self._invertImageMat, image)
        return image

class SlitEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)
        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._scaleWidthRange = math.sqrt(self._internalResolutionX) / 2
        self._scaleHeightRange = math.sqrt(self._internalResolutionY) / 2
        self._halfWidth = self._internalResolutionX / 2
        self._halfHeight = self._internalResolutionY / 2

        self._slitDirections = SlitDirections()

        self._memoryMat = createMat(internalResX, internalResY)
        self._composeMat = effectMat1

    def setExtraConfig(self, values):
        pass

    def getName(self):
        return "SlitScan"

    def reset(self):
        pass

    def _findDirection(self, value):
        direction = int(3.99 * value)
        return direction
        
    def applyEffect(self, image, songPosition, width, drawPos, sourceXPos, direction, crossFade):
        return self.slitEffect(image, width, drawPos, sourceXPos, self._findDirection(direction), crossFade)

    def slitEffect(self, image, width, drawPos, sourcePos, direction, crossFade):
        if((direction == SlitDirections.Left) or (direction == SlitDirections.Right)):
            sizeScale = int(math.pow((self._scaleWidthRange * (width+0.08)), 2))
            if(sizeScale < 1):
                return image
            pixelWidth = int((self._internalResolutionX / sizeScale) - (2.0*width))
            if(pixelWidth > self._halfWidth):
                return image
#        print "DEBUG pcn: sizeScale: width: " + str(width) + " sizeScale: " + str(sizeScale) + " pixelWidth: " + str(pixelWidth)
            if(direction == SlitDirections.Left):
                src_region = cv.GetSubRect(self._memoryMat, (pixelWidth, 0, self._internalResolutionX-pixelWidth, self._internalResolutionY))
                dst_region = cv.GetSubRect(self._composeMat, (0, 0, self._internalResolutionX-pixelWidth, self._internalResolutionY))
                cv.Copy(src_region, dst_region)
                src_region = cv.GetSubRect(self._memoryMat, (0, 0, pixelWidth, self._internalResolutionY))
                dst_region = cv.GetSubRect(self._composeMat, (self._internalResolutionX-pixelWidth, 0, pixelWidth, self._internalResolutionY))
                cv.Copy(src_region, dst_region)
            else:
                src_region = cv.GetSubRect(self._memoryMat, (0, 0, self._internalResolutionX-pixelWidth, self._internalResolutionY))
                dst_region = cv.GetSubRect(self._composeMat, (pixelWidth, 0, self._internalResolutionX-pixelWidth, self._internalResolutionY))
                cv.Copy(src_region, dst_region)
                src_region = cv.GetSubRect(self._memoryMat, (self._internalResolutionX-pixelWidth, 0, pixelWidth, self._internalResolutionY))
                dst_region = cv.GetSubRect(self._composeMat, (0, 0, pixelWidth, self._internalResolutionY))
                cv.Copy(src_region, dst_region)
            sourcePosPixels = int(sourcePos * (self._internalResolutionX-pixelWidth))
            drawPosPixels = int(drawPos * (self._internalResolutionX-pixelWidth))
            src_region = cv.GetSubRect(image, (sourcePosPixels, 0, pixelWidth, self._internalResolutionY))
            dst_region = cv.GetSubRect(self._composeMat, (drawPosPixels, 0, pixelWidth, self._internalResolutionY))
            cv.Copy(src_region, dst_region)
        else:
            sizeScale = int(math.pow((self._scaleHeightRange * (width+0.08)), 2))
            if(sizeScale < 1):
                return image
            pixelHeight = int((self._internalResolutionY / sizeScale) - (2.0*width))
            if(pixelHeight > self._halfHeight):
                return image
            if(direction == SlitDirections.Up):
                src_region = cv.GetSubRect(self._memoryMat, (0, pixelHeight, self._internalResolutionX, self._internalResolutionY-pixelHeight))
                dst_region = cv.GetSubRect(self._composeMat, (0, 0, self._internalResolutionX, self._internalResolutionY-pixelHeight))
                cv.Copy(src_region, dst_region)
                src_region = cv.GetSubRect(self._memoryMat, (0, 0, self._internalResolutionX, pixelHeight))
                dst_region = cv.GetSubRect(self._composeMat, (0, self._internalResolutionY-pixelHeight, self._internalResolutionX, pixelHeight))
                cv.Copy(src_region, dst_region)
            else:
                src_region = cv.GetSubRect(self._memoryMat, (0, 0, self._internalResolutionX, self._internalResolutionY-pixelHeight))
                dst_region = cv.GetSubRect(self._composeMat, (0, pixelHeight, self._internalResolutionX, self._internalResolutionY-pixelHeight))
                cv.Copy(src_region, dst_region)
                src_region = cv.GetSubRect(self._memoryMat, (0, self._internalResolutionY-pixelHeight, self._internalResolutionX, pixelHeight))
                dst_region = cv.GetSubRect(self._composeMat, (0, 0, self._internalResolutionX, pixelHeight))
                cv.Copy(src_region, dst_region)
            sourcePosPixels = int(sourcePos * (self._internalResolutionY-pixelHeight))
            drawPosPixels = int(drawPos * (self._internalResolutionY-pixelHeight))
            src_region = cv.GetSubRect(image, (0, sourcePosPixels, self._internalResolutionX, pixelHeight))
            dst_region = cv.GetSubRect(self._composeMat, (0, drawPosPixels, self._internalResolutionX, pixelHeight))
            cv.Copy(src_region, dst_region)
        cv.Copy(self._composeMat, self._memoryMat)
        if(crossFade > 0.01):
            if(crossFade > 0.5):
                cv.ConvertScaleAbs(self._composeMat, self._composeMat, 1.0 - ((crossFade-0.5) * 2))
            else:
                cv.ConvertScaleAbs(image, image, crossFade * 2)
            cv.Add(self._composeMat, image, image)
        else:
            cv.Copy(self._composeMat, image)
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

    def applyEffect(self, image, songPosition, amount, mode, dummy2, dummy3, dummy4):
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

    def applyEffect(self, image, songPosition, amount, dummy1, dummy2, dummy3, dummy4):
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
        self._tmpMat = effectMat2
        self._replaceMask = effectMask1
        self._zoomEffect = ZoomEffect(configurationTree, internalResX, internalResY)
        self._zoomMultiplyerValue = 1.0
        self._zRotationValue = 0.0
        self._xFlipValue = 0.0
        self._xFlipAngleValue = 0.0

    def setExtraConfig(self, values):
        print("DEBUG pcn: Feedback::setExtraConfig() " + str(values))
        if(values != None):
            _, advancedZoomString = values
            if(advancedZoomString == None):
                self._zoomMultiplyerValue = 1.0
                self._zRotationValue = 0.0
                self._xFlipValue = 0.0
                self._xFlipAngleValue = 0.0
            else:
                zoomVal, rotZVal, flipXVal, rotFlipVal = textToFloatValues(advancedZoomString, 4)
                if(zoomVal < -1.0):
                    self._zoomMultiplyerValue = -1.0
                elif(zoomVal > 1.0):
                    self._zoomMultiplyerValue = 1.0
                else:
                    self._zoomMultiplyerValue = zoomVal
                self._zRotationValue = rotZVal
                self._xFlipValue = flipXVal
                self._xFlipAngleValue = rotFlipVal

    def getName(self):
        return "Feedback"

    def reset(self):
        cv.SetZero(self._memoryMat)

    def applyEffect(self, image, songPosition, amount, arg1, arg2, arg3, arg4):
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
        if((zoom != 0.5) or (move > 0.003)):
            zoom = 1.0 - zoom
            if(move > 0.003):
                xcenter = (-0.125 * move * math.cos(self._radians360 * -direction)) + 0.5
                ycenter = (-0.125 * move * math.sin(self._radians360 * -direction)) + 0.5
            else:
                xcenter = 0.5
                ycenter = 0.5
            if(zoom != 0.5):
                if(self._zoomMultiplyerValue < 0.0):
                    zoomValue = ((0.5 - zoom) * -self._zoomMultiplyerValue) + 0.5
                    zoomCalc = self._zoomEffect.calculateZoom(zoomValue, 1.5, 1.5)
                elif(self._zoomMultiplyerValue < 0.003):
                    zoomCalc = 1.0
                else:
                    zoomValue = ((zoom - 0.5) * self._zoomMultiplyerValue) + 0.5
                    zoomCalc = self._zoomEffect.calculateZoom(zoomValue, 1.5, 1.5)
                flipX = (zoom - 0.5) * self._xFlipValue
                flipAngle = (zoom - 0.5) * self._xFlipAngleValue
                rotZ = (zoom - 0.5) * self._zRotationValue
            else:
                zoomCalc = 1.0
                flipX = 0.0
                flipAngle = 0.0
                rotZ = 0.0
            self._zoomEffect.zoomImageTransform(self._tmpMat, xcenter, ycenter, zoomCalc, flipAngle, flipX, rotZ)
        cv.Add(image, self._tmpMat, self._memoryMat)
#        cv.Sub(image, self._tmpMat, self._memoryMat)
        cv.Copy(self._memoryMat, image)
        return image

class DelayEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)

        self._radians360 = math.radians(360)
        self._resetMemory = True
        self._memoryMat = createMat(internalResX, internalResY)
        self._memoryMask = createMask(internalResX, internalResY)
        cv.SetZero(self._memoryMat)
        self._zoomMat = effectMat2
        self._zoomMask = effectMask3
        self._bwMask = effectMask1
        self._innerMask = effectMask2
        self.setExtraConfig((None, None))
        self._zoomEffect = ZoomEffect(configurationTree, internalResX, internalResY)

    def setExtraConfig(self, values):
        if(values != None):
            _, advancedZoomString = values
            if(advancedZoomString == None):
                self._zoomMultiplyerValue = 1.0
                self._zRotationValue = 0.0
                self._xFlipValue = 0.0
                self._xFlipAngleValue = 0.0
            else:
                zoomVal, rotZVal, flipXVal, rotFlipVal = textToFloatValues(advancedZoomString, 4)
                if(zoomVal < -1.0):
                    self._zoomMultiplyerValue = -1.0
                elif(zoomVal > 1.0):
                    self._zoomMultiplyerValue = 1.0
                else:
                    self._zoomMultiplyerValue = zoomVal
                self._zRotationValue = rotZVal
                self._xFlipValue = flipXVal
                self._xFlipAngleValue = rotFlipVal

    def getName(self):
        return "Delay"

    def reset(self):
        self._resetMemory = True

    def applyEffect(self, image, songPosition, amount, arg1, arg2, arg3, arg4):
        return self.addDelayImage(image, amount, arg1, arg2, arg3, arg4)

    def addDelayImage(self, image, value, lumaKey, move, direction, zoom):
        if(value < 0.01):
            self._resetMemory = True
            return image
        if(self._resetMemory == True):
            self._resetMemory = False
            cv.Copy(image, self._memoryMat)
            cv.Set(self._memoryMask, (255))
            return image
        #Fade
        cv.ConvertScaleAbs(self._memoryMat, self._zoomMat, value, 0)
        cv.ConvertScaleAbs(self._memoryMask, self._zoomMask, value/(4-(3*value)), 0)
        if((zoom != 0.5) or (move > 0.003)):
            zoom = 1.0 - zoom
            if(move > 0.003):
                xcenter = (-0.125 * move * math.cos(self._radians360 * -direction)) + 0.5
                ycenter = (-0.125 * move * math.sin(self._radians360 * -direction)) + 0.5
            else:
                xcenter = 0.5
                ycenter = 0.5
            if(zoom != 0.5):
                if(self._zoomMultiplyerValue < 0.0):
                    zoomValue = ((0.5 - zoom) * -self._zoomMultiplyerValue) + 0.5
                    zoomCalc = self._zoomEffect.calculateZoom(zoomValue, 1.5, 1.5)
                elif(self._zoomMultiplyerValue < 0.003):
                    zoomCalc = 1.0
                else:
                    zoomValue = ((zoom - 0.5) * self._zoomMultiplyerValue) + 0.5
                    zoomCalc = self._zoomEffect.calculateZoom(zoomValue, 1.5, 1.5)
                flipX = (zoom - 0.5) * self._xFlipValue
                flipAngle = (zoom - 0.5) * self._xFlipAngleValue
                rotZ = (zoom - 0.5) * self._zRotationValue
            else:
                zoomCalc = 1.0
                flipX = 0.0
                flipAngle = 0.0
                rotZ = 0.0
            self._zoomEffect.zoomImageTransform(self._zoomMat, xcenter, ycenter, zoomCalc, flipAngle, flipX, rotZ, self._zoomMask)

        cv.CvtColor(image, self._bwMask, cv.CV_BGR2GRAY);
        if(lumaKey < 0.5):
            lumaThreshold = int(506 * lumaKey) + 3
            cv.CmpS(self._bwMask, lumaThreshold, self._innerMask, cv.CV_CMP_GT)
            cv.Set(self._zoomMask, (0), self._innerMask)
            cv.Copy(self._zoomMat, image, self._zoomMask)
        else:
            lumaThreshold = int(512 * (lumaKey - 0.5))
            cv.CmpS(self._bwMask, lumaThreshold, self._innerMask, cv.CV_CMP_LT)
            cv.Set(self._zoomMask, (0), self._innerMask)
            cv.Copy(self._zoomMat, image, self._zoomMask)
        cv.Copy(image, self._memoryMat)
        cv.Add(self._innerMask, self._zoomMask, self._memoryMask)
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

    def applyEffect(self, image, songPosition, amount, contrast, invert, smooth, dummy4):
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

    def applyEffect(self, image, songPosition, amount, mode, dummy2, dummy3, dummy4):
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

        self._coluorModesHolder = EdgeColourModes()
        self._coluorMode = EdgeColourModes.Value

    def setExtraConfig(self, values):
        if(values != None):
            edgeColourModeString, _ = values
            if(edgeColourModeString == None):
                self._coluorMode = EdgeColourModes.Value
            else:
                self._coluorMode = self._coluorModesHolder.findMode(edgeColourModeString)

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

    def applyEffect(self, image, songPosition, amount, mode, lineHue, lineSat, lineWidth):
        red, green, blue = modifyHue(getHueColor(lineHue), lineSat)
        edgeMode = self.findMode(mode)
        return self.drawEdges(image, amount, edgeMode, self._coluorMode, red, green, blue, lineWidth)

    def drawEdges(self, image, value, edgeMode, hsv, red, green, blue, lineWidth):
#        print "mode: " + str(edgeMode) + " hsv: " + str(hsv) + " red: " + str(red) + " green: " + str(green) + " blue: " + str(blue)
        if((edgeMode == EdgeModes.CannyOnTop) or (edgeMode == EdgeModes.Canny)):
            if(value < 0.01):
                if(edgeMode == EdgeModes.CannyOnTop):
                    return image
                else: #Canny
                    cv.SetZero(image)
                    return image
        cv.CvtColor(image, self._colorMat, cv.CV_RGB2HSV)
        if(hsv == EdgeColourModes.Value):
            cv.Split(self._colorMat, None, None, self._splitMat, None)
        elif(hsv == EdgeColourModes.Saturation):
            cv.Split(self._colorMat, None, self._splitMat, None, None)
        else:
            cv.Split(self._colorMat, self._splitMat, None, None, None)
        if((edgeMode == EdgeModes.CannyOnTop) or (edgeMode == EdgeModes.Canny)):
            threshold = 256 - int(value * 256)
            cv.Canny(self._splitMat, self._maskMat, threshold, threshold * 2, 3)
            storage = cv.CreateMemStorage(0)
            if(edgeMode == EdgeModes.Canny):
                cv.SetZero(image)
            lineWidthInt = int(1.0 + (lineWidth * 9.0))
            contour = cv.FindContours(self._maskMat, storage,  cv.CV_RETR_TREE, cv.CV_CHAIN_APPROX_SIMPLE, (0,0))
            cv.DrawContours(image, contour, cv.RGB(red, green, blue), cv.RGB(red, green, blue), 20, thickness=lineWidthInt)
            return image
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

class CurveEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)

        self._hsvMat = effectMat1
        self._lastAmount = -1.0
        self._curveConfig = Curve()
        self._curveTableMat = cv.CreateMat(1, 256, cv.CV_8UC3)
        self._diffTable = []
        for _ in range(256):
            self._diffTable.append((0,0,0))

    def getName(self):
        return "Curve"

    def reset(self):
        pass

    def setExtraConfig(self, values):
        if(values != None):
            _, curveConfigString = values
            if(curveConfigString == None):
                curveConfigString = "Off"
            if(curveConfigString != self._curveConfig.getString()):
                self._curveConfig.setString(curveConfigString)
                curveValues = self._curveConfig.getArray()
                if(len(curveValues) == 3):
                    if(self._curveConfig.getMode() == Curve.HSV):
                        for i in range(256):
                            self._diffTable[i] = (curveValues[0][i] - i, curveValues[1][i] - i, curveValues[2][i] - i)
                    else:
                        for i in range(256):
                            self._diffTable[i] = (curveValues[2][i] - i, curveValues[1][i] - i, curveValues[0][i] - i)
                else:
                    for i in range(256):
                        diffVal = curveValues[i] - i
                        self._diffTable[i] = (diffVal, diffVal, diffVal)
                self._lastAmount = -1.0

    def _updateTable(self, amount):
        for i in range(256):
            diffValues = self._diffTable[i]
            ch0Val = int(i + (amount * diffValues[0]))
            ch1Val = int(i + (amount * diffValues[1]))
            ch2Val = int(i + (amount * diffValues[2]))
            cv.Set1D(self._curveTableMat, i, (ch0Val, ch1Val, ch2Val))

    def applyEffect(self, image, songPosition, amount, dummy1, dummy2, dummy3, dummy4):
        return self.applyCurve(image, amount)

    def applyCurve(self, image, amount):
        if(amount < 0.01):
            return image
        if(self._curveConfig.getMode() == Curve.Off):
            return image
        if(self._lastAmount != amount):
            self._updateTable(amount)
            self._lastAmount = amount
        if(self._curveConfig.getMode() == Curve.HSV):
            cv.CvtColor(image, self._hsvMat, cv.CV_BGR2HSV)
            cv.LUT(self._hsvMat, self._hsvMat, self._curveTableMat)
            cv.CvtColor(self._hsvMat, image, cv.CV_HSV2BGR)
        else:
            cv.LUT(image, image, self._curveTableMat)
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

    def applyEffect(self, image, songPosition, value, valRange, mode, dummy3, dummy4):
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

    def applyEffect(self, image, songPosition, contrast, brightness, mode, dummy3, dummy4):
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

    def applyEffect(self, image, songPosition, hueRot, saturation, brightness, mode, dummy4):
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

    def applyEffect(self, image, songPosition, amount, red, green, blue, modeVal):
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

    def applyEffect(self, image, songPosition, amount, dummy1, dummy2, dummy3, dummy4):
        return self.invert(image, amount)

    def invert(self, image, amount):
        brightnessVal = -255 * amount
        if((brightnessVal > -1) and (brightnessVal < 1)):
            return image
        else:
            cv.ConvertScaleAbs(image, image, 1.0, brightnessVal)
            return image

class StrobeEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        setupEffectMemory(internalResX, internalResY)
        self._lastValue = -9
        self._lastTime = 0.0
        self.setExtraConfig((1.0, 4))

    def setExtraConfig(self, values):
#        print("DEBUG pcn: Strobe::setExtraConfig() " + str(values))
        if(values != None):
            strobeBaseTime, strobeSpeedupSteps = values
            if(strobeBaseTime < 0.05):
                strobeBaseTime = 0.05
            if(strobeSpeedupSteps < 1):
                strobeSpeedupSteps = 1
            self._strobeBaseTime = float(strobeBaseTime * 24)
            self._strobeSpeedupSteps = float(int(strobeSpeedupSteps)) + 0.5

    def getName(self):
        return "Strobe"

    def reset(self):
        pass

    def applyEffect(self, image, songPosition, amount, speed, mode, dummy3, dummy4):
        return self.blink(image, songPosition, amount, speed, mode)

    def blink(self, image, songPosition, amount, speed, mode):
        powerFactor = (self._strobeSpeedupSteps + 2) * speed
        if(powerFactor > self._strobeSpeedupSteps):
            strobeLength = 3 - int(powerFactor - self._strobeSpeedupSteps)
            if(self._lastValue < 0):
                if(self._lastValue <= -strobeLength):
                    strobeOnOff = True
                    self._lastValue = 1.0
                else:
                    strobeOnOff = False
                    self._lastValue -= 1.0
            else:
                if(self._lastValue >= strobeLength):
                    strobeOnOff = False
                    self._lastValue = -1.0
                else:
                    strobeOnOff = True
                    self._lastValue += 1.0
#            print "DEBUG pcn: strobeEffect length " + str(strobeLength) + " nextVal " + str(self._lastValue) + " divider: " + str(int(powerFactor)) + " on: " + str(strobeOnOff)
        else:
            strobeIntervall = self._strobeBaseTime / math.pow(2, int(powerFactor))
            strobePhase = (songPosition % strobeIntervall) / strobeIntervall
            if(strobePhase < 0.5):
                strobeOnOff = False
            else:
                strobeOnOff = True
#            print "DEBUG pcn: strobeEffect intervall " + str(strobeIntervall) + " phase " + str(strobePhase) + " divider: " + str(int(powerFactor)) + " on: " + str(strobeOnOff)
        if(strobeOnOff == True):
            if(mode < 0.33):
                cv.ConvertScaleAbs(image, image, 1.0-amount)
            elif(mode < 0.66):
                addValue = int(256*amount)
                cv.AddS(image, (addValue, addValue, addValue), image)
            else:
                invertValue = int(-256*amount)
                cv.ConvertScaleAbs(image, image, 1.0, invertValue)
        self._lastTime = songPosition
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

    def applyEffect(self, image, songPosition, modeVal, rotate, saturate, dummy3, dummy4):
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

    def applyEffect(self, image, songPosition, amount, dummy1, dummy2, dummy3, dummy4):
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

    def applyEffect(self, image, songPosition, maskId, imageId, mode, dummy3, dummy4):
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
#class KaleidoscopeEffect(object):

#class CromaKeyGeneratorEffect(object):

#??? TODO ???
#get coordinates from image blob (I want better tracking (or sorting if you like))
#Showoff DEMO
#make ModulationValueMode available and Move ModulationValueMode to EffectConfig.
#Dont reload all thumbs on config update (only for changed media.) Optemizing ;-)

#ADSR add A AHoldR HoldR modes
#DMX512
#Tap tempo
#Playback GUI
#UDP -> multicast
#Improve thumb requests (bulk thumb requests?)

#Debugging.
#Check in blip on verse on RulleIGlassskaar, Effects related?
#Full path bug: could be when importing multipple files (DnD)

#Make Rygg I Rand project (started)

#No screensaver fix

#Keep last image on play once / advanced looping?

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#!!!      Full HD Demo/test        !!!
#!!! More complete startup program !!!
#!!!          Fancy demo           !!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

#Media:
#Video with alpha channel
#TextMedia font directory config.
#URL image media?
#Streaming from on player to another media (cameras etc.)
#Recording / resampler.
#Bypass media or (FX media.)
#    Send to locked midi channel?
#Complex looping (rollin, rollout, keep last?) (Under time modulation?)

#Wipe animations???
#calculate subframes when really slow...
