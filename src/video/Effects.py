'''
Created on 24. jan. 2012

@author: pcn
'''
from cv2 import cv
        
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

class EffectTypes():
    Zoom, Flip, Blur, BlurContrast, Distortion, Edge, Desaturate, Contrast, HueSaturation, Colorize, Invert, Threshold = range(12)

def getEffectId(name):
    lowername = name.lower()
    if(lowername == "zoom"):
        return EffectTypes.Zoom
    elif(lowername == "flip"):
        return EffectTypes.Flip
    elif(lowername == "blur"):
        return EffectTypes.Blur
    elif(lowername == "blurContrast"):
        return EffectTypes.BlurContrast
    elif(lowername == "distortion"):
        return EffectTypes.Distortion
    elif(lowername == "edge"):
        return EffectTypes.Edge
    elif(lowername == "desaturate"):
        return EffectTypes.Desaturate
    elif(lowername == "contrast"):
        return EffectTypes.Contrast
    elif(lowername == "huesaturation"):
        return EffectTypes.HueSaturation
    elif(lowername == "colorize"):
        return EffectTypes.Colorize
    elif(lowername == "invert"):
        return EffectTypes.Invert
    elif(lowername == "threshold"):
        return EffectTypes.Threshold

def getEffectById(effectType, configurationTree, internalResX, internalResY):
    if(effectType == EffectTypes.Zoom):
        return ZoomEffect(configurationTree, internalResX, internalResY)
    elif(effectType == EffectTypes.Flip):
        return FlipEffect(configurationTree, internalResX, internalResY)
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

    class Modes():
        In, Out, InOut, Full = range(4)

    def findMode(self, value):
        modeSelected = int(value*3.99)
        if(modeSelected == ZoomEffect.Modes.In):
            return ZoomEffect.Modes.In
        elif(modeSelected == ZoomEffect.Modes.Out):
            return ZoomEffect.Modes.Out
        elif(modeSelected == ZoomEffect.Modes.InOut):
            return ZoomEffect.Modes.InOut
        else:
            return ZoomEffect.Modes.Full

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
        if(zoomMode == ZoomEffect.Modes.Full):
            yzoom = 1.0 - amount * (xyrate  * 2)
            xcentr = (xcenter * -2) + 1
            ycentr = (ycenter * 2) - 1
        else:
            yzoom = xzoom
            xcentr = 0.0
            ycentr = 0.0
        minZoomRange = self._minZoomRange
        zoomRange = self._zoomRange
        if(zoomMode == ZoomEffect.Modes.Out):
            if(minZoomRange < 1.0):
                minZoomRange = 1.0
                zoomRange = zoomRange - 1.0 + self._minZoomRange
                xzoom = 1.0 - xzoom
                yzoom = 1.0 - yzoom
        elif(zoomMode == ZoomEffect.Modes.In):
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
#        print "Zoom: " + str(zoomXFraction) + " Y: " + str(zoomYFraction) + " R:(+) " + str(rangeFraction) + " w: " + str(width) + " h: " + str(height) + " l: " + str(left) + " t: " + str(top)
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

class FlipEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._flipMat = createMat(self._internalResolutionX, self._internalResolutionY)

    class Modes():
        NoFlip, Vertical, Horisontal, Both = range(4)

    def findMode(self, value):
        modeSelected = int(value*3.99)
        if(modeSelected == FlipEffect.Modes.NoFlip):
            return FlipEffect.Modes.NoFlip
        elif(modeSelected == FlipEffect.Modes.Vertical):
            return FlipEffect.Modes.Vertical
        elif(modeSelected == FlipEffect.Modes.Horisontal):
            return FlipEffect.Modes.Horisontal
        else:
            return FlipEffect.Modes.Both

    def getName(self):
        return "Flip"

    def findValue(self, mode):
        if(mode == FlipEffect.Modes.NoFlip):
            return None
        elif(mode == FlipEffect.Modes.Vertical):
            return 1
        elif(mode == FlipEffect.Modes.Horisontal):
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

    def applyEffect(self, image, amount, dummy1, dummy2, dummy3, dummy4):
        return self.dilateErode(image, amount)

    def dilateErode(self, image, value):
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

    class Modes():
        CannyOnTop, Canny, Sobel, Laplace = range(4)

    def findMode(self, value):
        modeSelected = int(value*3.99)
        if(modeSelected == EdgeEffect.Modes.CannyOnTop):
            return EdgeEffect.Modes.CannyOnTop
        elif(modeSelected == EdgeEffect.Modes.Canny):
            return EdgeEffect.Modes.Canny
        elif(modeSelected == EdgeEffect.Modes.Sobel):
            return EdgeEffect.Modes.Sobel
        else:
            return EdgeEffect.Modes.Laplace

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
        if((edgeMode == EdgeEffect.Modes.CannyOnTop) or (edgeMode == EdgeEffect.Modes.Canny)):
            hsvSelected = int(hsv*2.99)
        else:
            hsvSelected = 0
        cv.CvtColor(image, self._colorMat, cv.CV_RGB2HSV)
        if(hsvSelected < 1):
            cv.Split(self._colorMat, None, None, self._splitMat, None)
        elif(hsvSelected < 2):
            cv.Split(self._colorMat, None, self._splitMat, None, None)
        else:
            cv.Split(self._colorMat, self._splitMat, None, None, None)
        if((edgeMode == EdgeEffect.Modes.CannyOnTop) or (edgeMode == EdgeEffect.Modes.Canny)):
            threshold = 256 - int(value * 256)
            cv.Canny(self._splitMat, self._maskMat, threshold, threshold * 2, 3)
            if(edgeMode == EdgeEffect.Modes.CannyOnTop):
                storage = cv.CreateMemStorage(0)
                contour = cv.FindContours(self._maskMat, storage,  cv.CV_RETR_TREE, cv.CV_CHAIN_APPROX_SIMPLE, (0,0))
                cv.DrawContours(image, contour, cv.RGB(red, green, blue), cv.RGB(red, green, blue), 3)
                return image
            else: # Canny
                cv.CvtColor(self._maskMat, self._colorMat, cv.CV_GRAY2RGB)
                return self._colorMat
        else:
            if(edgeMode == EdgeEffect.Modes.Sobel):
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

    class Modes():
        Plus, Minus, Mask = range(3)

    def findMode(self, value):
        modeSelected = int(value*2.99)
        if(modeSelected == DesaturateEffect.Modes.Plus):
            return DesaturateEffect.Modes.Plus
        elif(modeSelected == DesaturateEffect.Modes.Minus):
            return DesaturateEffect.Modes.Minus
        else:
            return DesaturateEffect.Modes.Mask

    def getName(self):
        return "Desaturate"

    def applyEffect(self, image, value, valRange, mode, dummy3, dummy4):
        satMode = self.findMode(mode)
        return self.selectiveDesaturate(image, value, valRange, satMode)

    def selectiveDesaturate(self, image, value, valRange, satMode):
        hueValue = (value * 180)
        huePlussMinus = 1 + (valRange * 19)
        hueMin = max(0, hueValue - huePlussMinus)
        hueMax = min(256, hueValue + huePlussMinus)
        cv.CvtColor(image, self._colorMat, cv.CV_RGB2HSV)
        cv.InRangeS(self._colorMat, (hueMin, 160, 32), (hueMax, 255, 255), self._maskMat)
        if(satMode != DesaturateEffect.Modes.Mask):
            cv.Split(self._colorMat, self._hueMat, self._sat1Mat, self._valMat, None)
            if(satMode == DesaturateEffect.Modes.Plus):
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

    def getName(self):
        return "ContrastBrightness"

    def applyEffect(self, image, contrast, brightness, dummy2, dummy3, dummy4):
        return self.contrastBrightness(image, contrast, brightness)

    def contrastBrightness(self, image, contrast, brightness):
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
            cv.ConvertScaleAbs(image, self._scaleMat, contrastVal, brightnessVal)
            return self._scaleMat

class HueSaturationEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._colorMat = createMat(self._internalResolutionX, self._internalResolutionY)

    def getName(self):
        return "HueSaturation"

    def applyEffect(self, image, hueRot, saturation, brightness, dummy3, dummy4):
        return self.hueSaturationBrightness(image, hueRot, saturation, brightness)

    def hueSaturationBrightness(self, image, rotate, saturation, brightness):
        cv.CvtColor(image, self._colorMat, cv.CV_RGB2HSV)
        rotCalc = (rotate * 512) - 256
        satCalc = (saturation * 512) - 256
        brightCalc = (brightness * 512) - 256
        rgbColor = cv.CV_RGB(rotCalc, satCalc, brightCalc)
        cv.SubS(self._colorMat, rgbColor, image)
        cv.CvtColor(image, self._colorMat, cv.CV_HSV2RGB)
        return self._colorMat

class ColorizeEffect(object):
    def __init__(self, configurationTree, internalResX, internalResY):
        self._configurationTree = configurationTree
        self._internalResolutionX = internalResX
        self._internalResolutionY = internalResY
        self._colorMat = createMat(self._internalResolutionX, self._internalResolutionY)

    def getName(self):
        return "Colorize"

    class Modes():
        Add, Subtract, SubtractFrom, Multiply = range(4)

    def findMode(self, val):
        intVal = int(val*3.99)
        if(intVal == ColorizeEffect.Modes.Add):
            return ColorizeEffect.Modes.Add
        elif(intVal == ColorizeEffect.Modes.Subtract):
            return ColorizeEffect.Modes.Subtract
        elif(intVal == ColorizeEffect.Modes.SubtractFrom):
            return ColorizeEffect.Modes.SubtractFrom
        else:
            return ColorizeEffect.Modes.Multiply

    def applyEffect(self, image, amount, red, green, blue, modeVal):
        mode = self.findMode(modeVal)
        return self.colorize(image, amount, red, green, blue, mode)

    def colorize(self, image, amount, red, green, blue, mode):
        if((mode == ColorizeEffect.Modes.Add) or (mode == ColorizeEffect.Modes.Subtract)):
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
    
        if(mode == ColorizeEffect.Modes.Add):
            cv.AddS(image, rgbColor, self._colorMat)
        elif(mode == ColorizeEffect.Modes.Subtract):
            cv.SubS(image, rgbColor, self._colorMat)
        elif(mode == ColorizeEffect.Modes.SubtractFrom):
            cv.SubRS(image, rgbColor, self._colorMat)
        elif(mode == ColorizeEffect.Modes.Multiply):
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
        brightnessVal = -256 * amount
        if((brightnessVal > -0.01) and (brightnessVal < 0.01)):
            return image
        else:
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

#class MirrorEffect(object):
#class StutterEffect(object):
#class RotateEffect(object):