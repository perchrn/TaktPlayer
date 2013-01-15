'''
Created on 10. des. 2012

@author: pcn
'''

from cv2 import cv #@UnresolvedImport
from video.media.MediaFileModes import WipeMode, MixMode
from video.Effects import getNoizeMask, createMask, rotatePoint

class ImageMixer(object):
    def __init__(self, internalResolutionX, internalResolutionY):
        self._internalResolutionX =  internalResolutionX
        self._internalResolutionY =  internalResolutionY
        self._halfResolutionX = self._internalResolutionX / 2
        self._halfResolutionY = self._internalResolutionY / 2

        self._mixMixMask1 = createMask(self._internalResolutionX, self._internalResolutionY)
        self._mixMixMask2 = createMask(self._internalResolutionX, self._internalResolutionY)
        self._mixImageMask = createMask(self._internalResolutionX, self._internalResolutionY)

    def _wipeMix(self, wipeMode, wipeConfig, level, image1, image2, mixMat):
        if((wipeMode == WipeMode.Push)):
            wipeDirection = wipeConfig
            if(wipeDirection < 0.25):
                wipePosX = int(self._internalResolutionX * level)
                sourceLeft = self._internalResolutionX-wipePosX
                sourceTop = 0
                sourceWidth = wipePosX
                sourceHeight = self._internalResolutionY
                destLeft = 0
                destTop = 0
            elif(wipeDirection < 0.5):
                wipePosX = self._internalResolutionX - int(self._internalResolutionX * level)
                sourceLeft = 0
                sourceTop = 0
                sourceWidth = self._internalResolutionX-wipePosX
                sourceHeight = self._internalResolutionY
                destLeft = self._internalResolutionX-(self._internalResolutionX-wipePosX)
                destTop = 0
            elif(wipeDirection < 0.75):
                wipePosY = int(self._internalResolutionY * level)
                sourceLeft = 0
                sourceTop = self._internalResolutionY-wipePosY
                sourceWidth = self._internalResolutionX
                sourceHeight = wipePosY
                destLeft = 0
                destTop = 0
            else:
                wipePosY = self._internalResolutionY - int(self._internalResolutionY * level)
                sourceLeft = 0
                sourceTop = 0
                sourceWidth = self._internalResolutionX
                sourceHeight = self._internalResolutionY-wipePosY
                destLeft = 0
                destTop = self._internalResolutionY-(self._internalResolutionY-wipePosY)
            destWidth = sourceWidth
            destHeight = sourceHeight
            src_region = cv.GetSubRect(image2, (sourceLeft, sourceTop, sourceWidth, sourceHeight))
            if(image1 == None):
                cv.SetZero(mixMat)
                dst_region = cv.GetSubRect(mixMat, (destLeft, destTop, destWidth, destHeight))
                return mixMat
            else:
                dst_region = cv.GetSubRect(mixMat, (destLeft, destTop, destWidth, destHeight))
            cv.Copy(src_region, dst_region)
            if(wipeDirection < 0.25):
                wipePosX = int(self._internalResolutionX * level)
                sourceLeft = wipePosX
                sourceTop = 0
                sourceWidth = self._internalResolutionX-wipePosX
                sourceHeight = self._internalResolutionY
                destLeft = wipePosX
                destTop = 0
            elif(wipeDirection < 0.5):
                wipePosX = self._internalResolutionX - int(self._internalResolutionX * level)
                sourceLeft = 0
                sourceTop = 0
                sourceWidth = wipePosX
                sourceHeight = self._internalResolutionY
                destLeft = 0
                destTop = 0
            elif(wipeDirection < 0.75):
                wipePosY = int(self._internalResolutionY * level)
                sourceLeft = 0
                sourceTop = wipePosY
                sourceWidth = self._internalResolutionX
                sourceHeight = self._internalResolutionY-wipePosY
                destLeft = 0
                destTop = wipePosY
            else:
                wipePosY = self._internalResolutionY - int(self._internalResolutionY * level)
                sourceLeft = 0
                sourceTop = 0
                sourceWidth = self._internalResolutionX
                sourceHeight = wipePosY
                destLeft = 0
                destTop = 0
            destWidth = sourceWidth
            destHeight = sourceHeight
            src_region = cv.GetSubRect(image1, (sourceLeft, sourceTop, sourceWidth, sourceHeight))
            dst_region = cv.GetSubRect(mixMat, (destLeft, destTop, destWidth, destHeight))
            cv.Copy(src_region, dst_region)
            return mixMat
        if(wipeMode == WipeMode.Noize):
            scaleArg = wipeConfig
            noizeMask = getNoizeMask(level, self._internalResolutionX, self._internalResolutionY, 1.0 + (19.0 * scaleArg))
            if(image1 == None):
                cv.SetZero(mixMat)
                cv.Copy(image2, mixMat, noizeMask)
                return  mixMat
            cv.Copy(image2, image1, noizeMask)
            return image1
        if(wipeMode == WipeMode.Zoom):
            xMove, yMove = wipeConfig
            xSize = int(self._internalResolutionX * level)
            ySize = int(self._internalResolutionY * level)
            xPos = int((self._internalResolutionX - xSize) * xMove)
            yPos = int((self._internalResolutionY - ySize) * (1.0 - yMove))
            cv.SetZero(mixMat)
            dst_region = cv.GetSubRect(mixMat, (xPos, yPos, xSize, ySize))
            cv.Resize(image2, dst_region,cv.CV_INTER_CUBIC)
            if(image1 == None):
                return mixMat
            cv.SetZero(self._mixMixMask1)
            dst_region = cv.GetSubRect(self._mixMixMask1, (xPos, yPos, xSize, ySize))
            cv.Set(dst_region, 256)
            cv.Copy(mixMat, image1, self._mixMixMask1)
            return image1
        if(wipeMode == WipeMode.Flip):
            flipRotation = wipeConfig
            rotation = 1.0 - level
            srcPoints = ((0.0, 0.0),(0.0,self._internalResolutionY),(self._internalResolutionX, 0.0))
            destPoint1 = (0.0, 0.0)
            destPoint2 = (0.0, self._internalResolutionY)
            destPoint3 = (self._internalResolutionX, 0.0)
            if(image1 == None):
                rotation = rotation / 2
            if(rotation < 0.5):
                flipAngle = rotation / 2
            else:
                flipAngle = level / 2
            destPoint1 = rotatePoint(flipRotation, destPoint1[0], destPoint1[1], self._halfResolutionX, self._halfResolutionY, flipAngle)
            destPoint2 = rotatePoint(flipRotation, destPoint2[0], destPoint2[1], self._halfResolutionX, self._halfResolutionY, flipAngle)
            destPoint3 = rotatePoint(flipRotation, destPoint3[0], destPoint3[1], self._halfResolutionX, self._halfResolutionY, flipAngle)
            dstPoints = ((destPoint1[0], destPoint1[1]),(destPoint2[0], destPoint2[1]),(destPoint3[0],destPoint3[1]))
            zoomMatrix = cv.CreateMat(2,3,cv.CV_32F)
#            print "DEBUG pcn: trasform points source: " + str(srcPoints) + " dest: " + str(dstPoints) 
            cv.GetAffineTransform(srcPoints, dstPoints, zoomMatrix)
            if(rotation < 0.5):
                cv.WarpAffine(image2, mixMat, zoomMatrix)
            else:
                cv.WarpAffine(image1, mixMat, zoomMatrix)
            cv.Set(self._mixMixMask2, (255,255,255))
            cv.WarpAffine(self._mixMixMask2, self._mixMixMask1, zoomMatrix)
            return mixMat
        return image2
    
    def _wipeImage(self, wipeMode, wipeConfig, level, image, imageMask, mixMat, whiteMode = False):
        if((wipeMode == WipeMode.Push)):
            wipeDirection = wipeConfig
            if(whiteMode == True):
                cv.Set(mixMat, (255,255,255))
            else:
                cv.SetZero(mixMat)
            if(wipeDirection < 0.25):
                wipePosX = int(self._internalResolutionX * level)
                sourceLeft = self._internalResolutionX-wipePosX
                sourceTop = 0
                sourceWidth = wipePosX
                sourceHeight = self._internalResolutionY
                destLeft = 0
                destTop = 0
            elif(wipeDirection < 0.5):
                wipePosX = self._internalResolutionX - int(self._internalResolutionX * level)
                sourceLeft = 0
                sourceTop = 0
                sourceWidth = self._internalResolutionX-wipePosX
                sourceHeight = self._internalResolutionY
                destLeft = self._internalResolutionX-(self._internalResolutionX-wipePosX)
                destTop = 0
            elif(wipeDirection < 0.75):
                wipePosY = int(self._internalResolutionY * level)
                sourceLeft = 0
                sourceTop = self._internalResolutionY-wipePosY
                sourceWidth = self._internalResolutionX
                sourceHeight = wipePosY
                destLeft = 0
                destTop = 0
            else:
                wipePosY = self._internalResolutionY - int(self._internalResolutionY * level)
                sourceLeft = 0
                sourceTop = 0
                sourceWidth = self._internalResolutionX
                sourceHeight = self._internalResolutionY-wipePosY
                destLeft = 0
                destTop = self._internalResolutionY-(self._internalResolutionY-wipePosY)
            destWidth = sourceWidth
            destHeight = sourceHeight
            src_region = cv.GetSubRect(image, (sourceLeft, sourceTop, sourceWidth, sourceHeight))
            dst_region = cv.GetSubRect(mixMat, (destLeft, destTop, destWidth, destHeight))
            cv.Copy(src_region, dst_region)
            cv.Zero(self._mixMixMask1)
            dst_region = cv.GetSubRect(self._mixMixMask1, (destLeft, destTop, destWidth, destHeight))
            cv.Set(dst_region, 255)
            return mixMat, self._mixMixMask1
        if(wipeMode == WipeMode.Noize):
            scaleArg = wipeConfig
            cv.Copy(image, mixMat)
            noizeMask = getNoizeMask(level, self._internalResolutionX, self._internalResolutionY, 1.0 + (19.0 * scaleArg))
            if(whiteMode == True):
                cv.Set(image, (255,255,255))
            else:
                cv.Set(image, (0,0,0))
            cv.Copy(mixMat, image, noizeMask)
            return image, noizeMask
        if(wipeMode == WipeMode.Zoom):
            xMove, yMove = wipeConfig
            xSize = int(self._internalResolutionX * level)
            ySize = int(self._internalResolutionY * level)
            xPos = int((self._internalResolutionX - xSize) * xMove)
            yPos = int((self._internalResolutionY - ySize) * (1.0 - yMove))
            if(whiteMode == True):
                cv.Set(mixMat, (255,255,255))
            else:
                cv.SetZero(mixMat)
            dst_region = cv.GetSubRect(mixMat, (xPos, yPos, xSize, ySize))
            cv.Resize(image, dst_region,cv.CV_INTER_CUBIC)
            cv.Copy(mixMat, image)
            cv.SetZero(self._mixMixMask1)
            if(imageMask == None):
                dst_region = cv.GetSubRect(self._mixMixMask1, (xPos, yPos, xSize, ySize))
                cv.Set(dst_region, 255)
            else:
                dst_region = cv.GetSubRect(self._mixMixMask1, (xPos, yPos, xSize, ySize))
                cv.Resize(imageMask, dst_region,cv.CV_INTER_CUBIC)
            return image, self._mixMixMask1
        if(wipeMode == WipeMode.Flip):
            flipRotation = wipeConfig
            rotation = 1.0 - level
            srcPoints = ((0.0, 0.0),(0.0,self._internalResolutionY),(self._internalResolutionX, 0.0))
            destPoint1 = (0.0, 0.0)
            destPoint2 = (0.0, self._internalResolutionY)
            destPoint3 = (self._internalResolutionX, 0.0)
            flipAngle = rotation / 4
            destPoint1 = rotatePoint(flipRotation, destPoint1[0], destPoint1[1], self._halfResolutionX, self._halfResolutionY, flipAngle)
            destPoint2 = rotatePoint(flipRotation, destPoint2[0], destPoint2[1], self._halfResolutionX, self._halfResolutionY, flipAngle)
            destPoint3 = rotatePoint(flipRotation, destPoint3[0], destPoint3[1], self._halfResolutionX, self._halfResolutionY, flipAngle)
            dstPoints = ((destPoint1[0], destPoint1[1]),(destPoint2[0], destPoint2[1]),(destPoint3[0],destPoint3[1]))
            zoomMatrix = cv.CreateMat(2,3,cv.CV_32F)
#            print "DEBUG pcn: trasform points source: " + str(srcPoints) + " dest: " + str(dstPoints) 
            cv.GetAffineTransform(srcPoints, dstPoints, zoomMatrix)
            cv.WarpAffine(image, mixMat, zoomMatrix)
            cv.Set(self._mixMixMask2, (255,255,255))
            cv.WarpAffine(self._mixMixMask2, self._mixMixMask1, zoomMatrix)
            return mixMat, self._mixMixMask1
        calcMaskValue = 255 - (255* level)
        cv.Set(self._mixMixMask1, (calcMaskValue, calcMaskValue, calcMaskValue))
        return image, self._mixMixMask1
    
    def _mixImageSelfMask(self, wipeSettings, level, image1, image2, mixMat, whiteMode):
        cv.CvtColor(image2, self._mixImageMask, cv.CV_BGR2GRAY);
        if(whiteMode == True):
            cv.CmpS(self._mixImageMask, 250, self._mixImageMask, cv.CV_CMP_LT)
        else:
            cv.CmpS(self._mixImageMask, 5, self._mixImageMask, cv.CV_CMP_GT)
        return self._mixImageAlphaMask(wipeSettings, level, image1, image2, self._mixImageMask, mixMat)
    
    def _mixImageAlphaMask(self, wipeSettings, level, image1, image2, image2mask, mixMat):
        if(level < 0.99):
            wipeMode, wipePostMix, wipeConfig = wipeSettings
            if((wipeMode == WipeMode.Fade) or (wipeMode == WipeMode.Default)):
                valueCalc = int(256 * (1.0 - level))
                rgbColor = cv.CV_RGB(valueCalc, valueCalc, valueCalc)
                whiteColor = cv.CV_RGB(255, 255, 255)
                cv.Set(mixMat, whiteColor)
                cv.Set(mixMat, rgbColor, image2mask)
                cv.Mul(image1, mixMat, image1, 0.004)
                valueCalc = int(256 * level)
                rgbColor = cv.CV_RGB(valueCalc, valueCalc, valueCalc)
                cv.Zero(mixMat)
                cv.Set(mixMat, rgbColor, image2mask)
                cv.Mul(image2, mixMat, image2, 0.004)
                cv.Add(image1, image2, image1)
                return image1
            else:
                if(wipePostMix == False):
                    image2, image2mask = self._wipeImage(wipeMode, wipeConfig, level, image2, image2mask, mixMat, False)
                    cv.Copy(image2, image1, image2mask)
                    return image1
                else:
                    cv.Copy(image1, mixMat)
                    cv.Copy(image2, mixMat, image2mask)
                    return self._wipeMix(wipeMode, wipeConfig, level, image1, mixMat, image2)
        cv.Copy(image2, image1, image2mask)
        return image1
    
    def _mixImageAdd(self, wipeSettings, level, image1, image2, mixMat):
        if(level < 0.99):
            wipeMode, wipePostMix, wipeConfig = wipeSettings
            if((wipeMode == WipeMode.Fade) or (wipeMode == WipeMode.Default)):
                cv.ConvertScaleAbs(image2, image2, level, 0.0)
                cv.Add(image1, image2, mixMat)
                return mixMat
            else:
                if(wipePostMix == False):
                    image2, _ = self._wipeImage(wipeMode, wipeConfig, level, image2, None, mixMat, False)
                    cv.Add(image1, image2, mixMat)
                    return mixMat
                else:
                    cv.Add(image1, image2, mixMat)
                    return self._wipeMix(wipeMode, wipeConfig, level, image1, mixMat, image2)
        cv.Add(image1, image2, mixMat)
        return mixMat
    
    def _mixImageSubtract(self, wipeSettings, level, image1, image2, mixMat):
        if(level < 0.99):
            wipeMode, wipePostMix, wipeConfig = wipeSettings
#            print "DEBUG pcn: mixImageSubtract: wipeSettings: " + str(wipeSettings)
            if((wipeMode == WipeMode.Fade) or (wipeMode == WipeMode.Default)):
                cv.ConvertScaleAbs(image2, image2, level, 0.0)
                cv.Sub(image1, image2, mixMat)
                return mixMat
            else:
                if(wipePostMix == False):
                    image2, _ = self._wipeImage(wipeMode, wipeConfig, level, image2, None, mixMat, False)
                    cv.Sub(image1, image2, mixMat)
                    return mixMat
                else:
                    cv.Sub(image1, image2, mixMat)
                    return self._wipeMix(wipeMode, wipeConfig, level, image1, mixMat, image2)
        cv.Sub(image1, image2, mixMat)
        return mixMat
    
    def _mixImageReplace(self, wipeSettings, level, image1, image2, mixMat):
        if(level < 0.99):
            wipeMode, wipePostMix, wipeConfig = wipeSettings
            if((wipeMode == WipeMode.Fade) or (wipeMode == WipeMode.Default)):
                if(image1 != None):
                    cv.ConvertScaleAbs(image2, image2, level, 0.0)
                    cv.ConvertScaleAbs(image1, image1, 1.0 - level, 0.0)
                    cv.Add(image1, image2, mixMat)
                    return mixMat
                else:
                    cv.ConvertScaleAbs(image2, mixMat, level, 0.0)
                    return mixMat
            else:
                if(wipePostMix == False):
                    image2, mixMask = self._wipeImage(wipeMode, wipeConfig, level, image2, None, mixMat, False)
                    if(image1 == None):
                        return image2
                    cv.Copy(image2, image1, mixMask)
                    return image1
                else:
                    return self._wipeMix(wipeMode, wipeConfig, level, image1, image2, mixMat)
        return image2
    
    def _mixImageMultiply(self, wipeSettings, level, image1, image2, mixMat):
        if(level < 0.99):
            wipeMode, wipePostMix, wipeConfig = wipeSettings
            if((wipeMode == WipeMode.Fade) or (wipeMode == WipeMode.Default)):
                cv.ConvertScaleAbs(image2, mixMat, 1.0, 256*(1.0-level))
                cv.Mul(image1, mixMat, mixMat, 0.004)
                return mixMat
            else:
                if(wipePostMix == False):
                    image2, _ = self._wipeImage(wipeMode, wipeConfig, level, image2, None, mixMat, True)
                    cv.Mul(image1, image2, mixMat, 0.004)
                    return mixMat
                else:
                    cv.Mul(image1, image2, mixMat, 0.004)
                    return self._wipeMix(wipeMode, wipeConfig, level, image1, mixMat, image2)
        cv.Mul(image1, image2, mixMat, 0.004)
        return mixMat

    def mixImages(self, mode, wipeSettings, level, image1, image2, image2mask, mixMat):
        if(level < 0.01):
            return image1
        if(mode == MixMode.Multiply):
            return self._mixImageMultiply(wipeSettings, level, image1, image2, mixMat)
        elif(mode == MixMode.Subtract):
            return self._mixImageSubtract(wipeSettings, level, image1, image2, mixMat)
        elif(mode == MixMode.LumaKey):
            return self._mixImageSelfMask(wipeSettings, level, image1, image2, mixMat, False)
        elif(mode == MixMode.WhiteLumaKey):
            return self._mixImageSelfMask(wipeSettings, level, image1, image2, mixMat, True)
        elif(mode == MixMode.AlphaMask):
            if(image2mask != None):
                return self._mixImageAlphaMask(wipeSettings, level, image1, image2, image2mask, mixMat)
            #Will fall back to Add mode if there is no mask.
        elif(mode == MixMode.Replace):
            return self._mixImageReplace(wipeSettings, level, image1, image2, mixMat)
        #Default is Add!
        return self._mixImageAdd(wipeSettings, level, image1, image2, mixMat)
