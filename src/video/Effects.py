'''
Created on 24. jan. 2012

@author: pcn
'''
from cv2 import cv
import numpy #@UnusedImport
from video.EffectModes import EffectTypes, ZoomModes, FlipModes, DistortionModes,\
    EdgeModes, DesaturateModes, ColorizeModes, EdgeColourModes, getEffectId,\
    ScrollModes, ContrastModes, HueSatModes
        
def getEmptyImage(x, y):
    resizeMat = createMat(x,y)
    return resizeImage(cv.CreateImage((x,y), cv.IPL_DEPTH_8U, 3), resizeMat)

def createMat(width, heigth):
    return cv.CreateMat(heigth, width, cv.CV_8UC3)

def createMask(width, heigth):
    return cv.CreateMat(heigth, width, cv.CV_8UC1)

def copyImage(image):
    return cv.CloneImage(image)

def resizeImage(image, resizeMat):
    cv.Resize(image, resizeMat)
    return resizeMat

def getEffectById(effectType, configurationTree, internalResX, internalResY):
    if(effectType == EffectTypes.Zoom):
        return ZoomEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.Flip):
        return FlipEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.Scroll):
        return ScrollEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.Blur):
        return BlurEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.BlurContrast):
        return BluredContrastEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.Distortion):
        return DistortionEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.Edge):
        return EdgeEffect(configurationTree, internalResX, internalResY)
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
    elif(effectType == EffectTypes.Threshold):
        return ThresholdEffect(configurationTree, internalResX, internalResY)
    else:
        return None

def getEffectByName(name, configurationTree, internalResX, internalResY):
    fxid = getEffectId(name)
    return getEffectById(fxid, configurationTree, internalResX, internalResY)


class ZoomEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree

        self._setZoomRange(0.25, 4.0)

        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._zoomMat = createMat(self._internalResolutionX, self._internalResolutionY)
        self._blankImage = getEmptyImage(self._internalResolutionX, self._internalResolutionY)

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

    def applyEffect(self, image, amount, xyrate, xcenter, ycenter, mode):
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
        minZoomRange = self._minZoomRange
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
            return self._blankImage
#        print "Zoom src: " + str(zoomXFraction) + " Y: " + str(zoomYFraction) + " w: " + str(width) + " h: " + str(height) + " l: " + str(left) + " t: " + str(top)
        src_region = cv.GetSubRect(image, (left, top, width, height) )
        if(outputRect):
            if(outPutWidth < 0):
                outPutWidth = int(originalWidth - outPutLeft)
                if(outPutWidth < 0):
                    return self._blankImage
            if(outPutHeight < 0):
                outPutHeight = int(originalHeight - outPutTop)
                if(outPutHeight < 0):
                    return self._blankImage
#            print "Zoom OUT: " + str(outPutWidth) + " h: " + str(outPutHeight) + " l: " + str(outPutLeft) + " t: " + str(outPutTop)
            tmpMat = createMat(outPutWidth, outPutHeight)
            cv.Resize(src_region, tmpMat)
            cv.SetZero(self._zoomMat)
            dst_region = cv.GetSubRect(self._zoomMat, (outPutLeft, outPutTop, outPutWidth, outPutHeight) )
            cv.Copy(tmpMat, dst_region)
            return self._zoomMat
        cv.Resize(src_region, self._zoomMat)
        return self._zoomMat

class ScrollEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree

        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._scrollMat = createMat(self._internalResolutionX, self._internalResolutionY)
        self._blankImage = getEmptyImage(self._internalResolutionX, self._internalResolutionY)
        self._flipMat = None

    def findMode(self, value):
        modeSelected = int(value*2.99)
        if(modeSelected == ScrollModes.NoFlip):
            return ScrollModes.NoFlip
        elif(modeSelected == ScrollModes.Flip):
            return ScrollModes.NoRepeat
        elif(modeSelected == ScrollModes.NoRepeat):
            return ScrollModes.Flip
        else:
            return ScrollModes.NoFlip

    def getName(self):
        return "Scroll"

    def applyEffect(self, image, xcenter, ycenter, mode, dummy3, dummy4):
        flipMode = self.findMode(mode)
        return self.zoomImage(image, xcenter, ycenter, flipMode)

    def zoomImage(self, image, xcenter, ycenter, flipMode):
        originalW, originalH = cv.GetSize(image)
        originalWidth = float(originalW)
        originalHeight = float(originalH)
        width = self._internalResolutionX
        height = self._internalResolutionY
        if(flipMode == ScrollModes.Flip):
            print "FLIP!"
            left = int(originalWidth * xcenter * 2.0)
            top = int(originalHeight * ycenter * 2.0)
        if(flipMode == ScrollModes.NoRepeat):
            print "NO REPEAT!"
            left = int((originalWidth - width) * xcenter * 2.0)
            top = int((originalHeight - height) * ycenter * 2.0)
        else:
            left = int(originalWidth * xcenter)
            top = int(originalHeight * ycenter)
        right = left + width
        bottom = top + height
        print "Left: " + str(left) + " top: " + str(top) + " width: " + str(width) + " height: " + str(height)
        if(flipMode == ScrollModes.Flip):
            if(self._flipMat == None):
                self._flipMat = createMat(originalW, originalH)
            else:
                oldFlipW, oldFlipH = cv.GetSize(self._flipMat)
                if((oldFlipW != originalW) or (oldFlipH != originalH)):
                    self._flipMat = createMat(originalW, originalH)
        if(left < originalWidth):
            if(top < originalHeight):
                originalRight = right
                originalBottom = bottom
                if(right > originalWidth):
                    originalRight = originalW
                if(bottom > originalHeight):
                    originalBottom = originalH
                print "1: Left: " + str(left) + " top: " + str(top) + " 'right: " + str(originalRight-left) + " 'bottom: " + str(originalBottom-top)
                src_region = cv.GetSubRect(image, (left, top, originalRight-left, originalBottom-top) )
                dst_region = cv.GetSubRect(self._scrollMat, (0, 0, originalRight-left, originalBottom-top) )
                cv.Copy(src_region, dst_region)
        if(right > originalWidth):
            if(top < originalHeight):
                if(flipMode == ScrollModes.Flip):
                    print "FLIP TODO"
                elif(flipMode == ScrollModes.NoFlip):
                    newWidth = right - originalW
                    newBottom = bottom
                    if(bottom > originalHeight):
                        newBottom = originalH
                    print "2: originalW-left: " + str(originalW-left) + " top: " + str(top) + " 'newWidth: " + str(newWidth) + " 'newBottom-top: " + str(newBottom-top)
                    src_region = cv.GetSubRect(image, (0, top, newWidth, newBottom-top) )
                    dst_region = cv.GetSubRect(self._scrollMat, (originalW-left, 0, newWidth, newBottom-top) )
                    cv.Copy(src_region, dst_region)
        if(bottom > originalHeight):
            if(flipMode == ScrollModes.Flip):
                print "FLIP TODO"
            elif(flipMode == ScrollModes.NoFlip):
                newHeight = bottom - originalH
                newRight = right
                if(right > originalWidth):
                    newRight = originalW
                print "3: left: " + str(left) + " originalH-top: " + str(originalH-top) + " 'newHeight: " + str(newHeight) + " 'newRight-left: " + str(newRight-left)
                src_region = cv.GetSubRect(image, (left, 0, newRight-left, newHeight) )
                dst_region = cv.GetSubRect(self._scrollMat, (0, originalH-top, newRight-left, newHeight) )
                cv.Copy(src_region, dst_region)
        if(bottom > originalHeight):
            if(right > originalWidth):
                if(flipMode == ScrollModes.Flip):
                    print "FLIP TODO"
                elif(flipMode == ScrollModes.NoFlip):
                    newHeight = bottom - originalH
                    newWidth = right - originalW
                    print "4: originalW-left: " + str(originalW-left) + " originalH-top: " + str(originalH-top) + " 'newWidth: " + str(newWidth) + " 'newHeight: " + str(newHeight)
                    src_region = cv.GetSubRect(image, (0, 0, newWidth, newHeight) )
                    dst_region = cv.GetSubRect(self._scrollMat, (originalW-left, originalH-top, newWidth, newHeight) )
                    cv.Copy(src_region, dst_region)
        return self._scrollMat

class FlipEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._flipMat = createMat(self._internalResolutionX, self._internalResolutionY)

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

    def applyEffect(self, image, amount, dummy1, dummy2, dummy3, dummy4):
        mode = self.findMode(amount)
        flipValue = self.findValue(mode)
        if(flipValue == None):
            return image
        else:
            return self.flipImage(image, flipValue)

    def flipImage(self, image, flipMode):
        cv.Flip(image, self._flipMat, flipMode)
        return self._flipMat

class BlurEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._blurMat = createMat(self._internalResolutionX, self._internalResolutionY)

    def getName(self):
        return "Blur"

    def applyEffect(self, image, amount, dummy1, dummy2, dummy3, dummy4):
        return self.blurImage(image, amount)

    def blurImage(self, image, value):
        if(value < 0.01):
            return image
        xSize = 2 + int(value * 8)
        ySize = 2 + int(value * 6)
        cv.Smooth(image, self._blurMat, cv.CV_BLUR, xSize, ySize)
        return self._blurMat

class BluredContrastEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._blurMat1 = createMat(self._internalResolutionX, self._internalResolutionY)
        self._blurMat2 = createMat(self._internalResolutionX, self._internalResolutionY)

    def getName(self):
        return "BluredContrast"

    def applyEffect(self, image, amount, dummy1, dummy2, dummy3, dummy4):
        return self.blurMultiply(image, amount)

    def blurMultiply(self, image, value):
        if(value < 0.01):
            return image
        xSize = 2 + int(value * 8)
        ySize = 2 + int(value * 6)
        cv.Smooth(image, self._blurMat1, cv.CV_BLUR, xSize, ySize)
        cv.Mul(image, self._blurMat1, self._blurMat2, 0.006)
        return self._blurMat2

class DistortionEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._distortMat = createMat(self._internalResolutionX, self._internalResolutionY)

    def getName(self):
        return "Distortion"

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
        return self._distortMat

class EdgeEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._colorMat = createMat(self._internalResolutionX, self._internalResolutionY)
        self._maskMat = createMask(self._internalResolutionX, self._internalResolutionY)
        self._splitMat = createMask(self._internalResolutionX, self._internalResolutionY)
        self._edgeMat = cv.CreateMat(self._internalResolutionY, self._internalResolutionX, cv.CV_16SC1)


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

    def getHueColor(self, hue):
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

    def modifyHue(self, rgb, sat):
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

    def applyEffect(self, image, amount, mode, hsv, lineHue, lineSat):
        red, green, blue = self.modifyHue(self.getHueColor(lineHue), lineSat)
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
            threshold = 256 - int(value * 256)
            cv.Canny(self._splitMat, self._maskMat, threshold, threshold * 2, 3)
            if(edgeMode == EdgeModes.CannyOnTop):
                storage = cv.CreateMemStorage(0)
                contour = cv.FindContours(self._maskMat, storage,  cv.CV_RETR_TREE, cv.CV_CHAIN_APPROX_SIMPLE, (0,0))
                cv.DrawContours(image, contour, cv.RGB(red, green, blue), cv.RGB(red, green, blue), 3)
                return image
            else: # Canny
                cv.CvtColor(self._maskMat, self._colorMat, cv.CV_GRAY2RGB)
                return self._colorMat
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
            cv.CvtColor(self._maskMat, self._colorMat, cv.CV_GRAY2RGB)
            return self._colorMat

class DesaturateEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._colorMat = createMat(self._internalResolutionX, self._internalResolutionY)
        self._maskMat = createMask(self._internalResolutionX, self._internalResolutionY)
        self._hueMat = createMask(self._internalResolutionX, self._internalResolutionY)
        self._sat1Mat = createMask(self._internalResolutionX, self._internalResolutionY)
        self._sat2Mat = createMask(self._internalResolutionX, self._internalResolutionY)
        self._valMat = createMask(self._internalResolutionX, self._internalResolutionY)

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
                cv.Mul(self._sat1Mat, self._maskMat, self._sat2Mat, 0.005)
            else: # Minus
                cv.Sub(self._sat1Mat, self._maskMat, self._sat2Mat)
            cv.Smooth(self._sat2Mat, self._sat1Mat, cv.CV_BLUR, 8, 6)
            cv.Merge(self._hueMat, self._sat1Mat, self._valMat, None, image)
            cv.CvtColor(image, self._colorMat, cv.CV_HSV2RGB)
        else:
            cv.CvtColor(self._maskMat, self._colorMat, cv.CV_GRAY2RGB)
        return self._colorMat

class ContrastBrightnessEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._scaleMat = createMat(self._internalResolutionX, self._internalResolutionY)

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
            cv.ConvertScaleAbs(image, self._scaleMat, contrastVal, brightnessVal)
            return self._scaleMat

class HueSaturationEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._colorMat = createMat(self._internalResolutionX, self._internalResolutionY)

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

    def applyEffect(self, image, hueRot, saturation, brightness, mode, dummy4):
        return self.hueSaturationBrightness(image, hueRot, saturation, brightness, self.findMode(mode))

    def hueSaturationBrightness(self, image, rotate, saturation, brightness, mode):
        cv.CvtColor(image, self._colorMat, cv.CV_RGB2HSV)
        rotCalc = (((rotate * 512) + 256) % 512) - 256
        if(mode == HueSatModes.Increase):
            satCalc = saturation * -256
            brightCalc = brightness * -256
        elif(mode == HueSatModes.Decrease):
            satCalc = saturation * 256
            brightCalc = brightness * 256
        else: #(mode == HueSatModes.Full):
            satCalc = (saturation * -512) + 256
            brightCalc = (brightness * -512) + 256
        darkCalc = None
        if(brightCalc < 0):
            darkCalc = float(256 - brightCalc) / 256.0
            brightCalc = 0
#        print "DEBUG hueSat: rot: " + str(rotCalc) + " sat: " + str(satCalc) + " bright: " + str(brightCalc)
        rgbColor = cv.CV_RGB(brightCalc, satCalc, rotCalc)
        cv.SubS(self._colorMat, rgbColor, image)
        cv.CvtColor(image, self._colorMat, cv.CV_HSV2RGB)
        if(darkCalc != None):
            cv.ConvertScaleAbs(self._colorMat, image, darkCalc, 0)
            return image
        return self._colorMat


class ColorizeEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._colorMat = createMat(self._internalResolutionX, self._internalResolutionY)

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
            cv.AddS(image, rgbColor, self._colorMat)
        elif(mode == ColorizeModes.Subtract):
            cv.SubS(image, rgbColor, self._colorMat)
        elif(mode == ColorizeModes.SubtractFrom):
            cv.SubRS(image, rgbColor, self._colorMat)
        elif(mode == ColorizeModes.Multiply):
            cv.Set(self._colorMat, rgbColor)
            cv.Mul(image, self._colorMat, self._colorMat, 0.004)
        else:
            cv.AddS(image, rgbColor, self._colorMat)
        return self._colorMat

class InvertEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._scaleMat = createMat(self._internalResolutionX, self._internalResolutionY)

    def getName(self):
        return "Invert"

    def applyEffect(self, image, amount, dummy1, dummy2, dummy3, dummy4):
        return self.invert(image, amount)

    def invert(self, image, amount):
        brightnessVal = -255 * amount
        if((brightnessVal > -1) and (brightnessVal < 1)):
            print "DEBUG no invert brightnessVal: " + str(brightnessVal) + " amount: " + str(amount)
            return image
        else:
            print "DEBUG invert brightnessVal: " + str(brightnessVal) + " amount: " + str(amount)
            cv.ConvertScaleAbs(image, self._scaleMat, 1.0, brightnessVal)
            return self._scaleMat

class ThresholdEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._thersholdMat = createMat(self._internalResolutionX, self._internalResolutionY)
        self._thersholdMask = createMask(self._internalResolutionX, self._internalResolutionY)

    def getName(self):
        return "Threshold"

    def applyEffect(self, image, amount, dummy1, dummy2, dummy3, dummy4):
        return self.threshold(image, amount)

    def threshold(self, image, threshold):
        threshold = 256 - (256 * threshold)
        cv.CvtColor(image, self._thersholdMask, cv.CV_BGR2GRAY);
        cv.CmpS(self._thersholdMask, threshold, self._thersholdMask, cv.CV_CMP_GT)
        cv.Merge(self._thersholdMask, self._thersholdMask, self._thersholdMask, None, self._thersholdMat)
        return self._thersholdMat

#TODO: add effects
#class MirrorEffect(object):
#class RotateEffect(object):

#class StutterEffect(object):
#class EchoEffect(object):

#class ScrollingImage(MediaFile):
#replaces:
    #class InterferenceEffect(object):
    #class LimboEffectish():
    #class ParalaxScrolling():