'''
Created on 14. feb. 2012

@author: pcn
'''
class EffectTypes():
    Zoom, Flip, Mirror, Rotate, Scroll, Blur, BlurContrast, Feedback, Delay, Rays, SelfDifference, Distortion, Pixelate, TVNoize, Edge, BlobDetect, Desaturate, Contrast, HueSaturation, Colorize, Invert, ValueToHue, Threshold, ImageAdd = range(24)

    def getChoices(self):
        return ["None",
                "Zoom",
                "Flip",
                "Mirror",
                "Rotate",
                "Scroll",
                "Blur",
                "BlurContrast",
                "Feedback",
                "Delay",
                "Rays",
                "SelfDifference",
                "Distortion",
                "Pixelate",
                "TVNoize",
                "Edge",
                "BlobDetect",
                "Desaturate",
                "Contrast",
                "HueSaturation",
                "Colorize",
                "Invert",
                "ValueToHue",
                "Threshold",
                "ImageAdd"]
    def getDescriptions(self):
        return ["None",
                "Zoom inn/out and even crop video.",
                "Flip video horizontal/vertical.",
                "Mirror effect.",
                "Rotate image around a poit.",
                "Scroll image.",
                "Blur video.",
                "Blur and multiply with self.",
                "Video feedback effect.",
                "Video delay effect.",
                "Ray effect.",
                "Delaying video and subtracting it with self.",
                "Distort image to black or white.",
                "Pixelate image",
                "TVNoize adder.",
                "Edge detection effects.",
                "Blob detection effects.",
                "Selective desaturation effects.",
                "Adjust brightness and contrast",
                "Rotate colors and adjust saturation.",
                "Add/subtract/multiply with color.",
                "Invert video.",
                "Turns BW images into a rainbow of colours.",
                "Threshold video to black and white.",
                "Can mask and add image to video."]

def getEffectId(name):
    lowername = name.lower()
    if(lowername == "zoom"):
        return EffectTypes.Zoom
    elif(lowername == "flip"):
        return EffectTypes.Flip
    elif(lowername == "mirror"):
        return EffectTypes.Mirror
    elif(lowername == "rotate"):
        return EffectTypes.Rotate
    elif(lowername == "scroll"):
        return EffectTypes.Scroll
    elif(lowername == "blur"):
        return EffectTypes.Blur
    elif(lowername == "blurcontrast"):
        return EffectTypes.BlurContrast
    elif(lowername == "feedback"):
        return EffectTypes.Feedback
    elif(lowername == "delay"):
        return EffectTypes.Delay
    elif(lowername == "rays"):
        return EffectTypes.Rays
    elif(lowername == "selfdifference"):
        return EffectTypes.SelfDifference
    elif(lowername == "distortion"):
        return EffectTypes.Distortion
    elif(lowername == "pixelate"):
        return EffectTypes.Pixelate
    elif(lowername == "tvnoize"):
        return EffectTypes.TVNoize
    elif(lowername == "edge"):
        return EffectTypes.Edge
    elif(lowername == "blobdetect"):
        return EffectTypes.BlobDetect
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
    elif(lowername == "valuetohue"):
        return EffectTypes.ValueToHue
    elif(lowername == "threshold"):
        return EffectTypes.Threshold
    elif(lowername == "imageadd"):
        return EffectTypes.ImageAdd
    else:
        return None

def getEffectName(effectId):
    if(effectId == EffectTypes.Zoom):
        return "Zoom"
    elif(effectId == EffectTypes.Flip):
        return "Flip"
    elif(effectId == EffectTypes.Mirror):
        return "Mirror"
    elif(effectId == EffectTypes.Rotate):
        return "Rotate"
    elif(effectId == EffectTypes.Scroll):
        return "Scroll"
    elif(effectId == EffectTypes.Blur):
        return "Blur"
    elif(effectId == EffectTypes.BlurContrast):
        return "BlurContrast"
    elif(effectId == EffectTypes.Feedback):
        return "Feedback"
    elif(effectId == EffectTypes.Delay):
        return "Delay"
    elif(effectId == EffectTypes.Rays):
        return "Rays"
    elif(effectId == EffectTypes.SelfDifference):
        return "SelfDifference"
    elif(effectId == EffectTypes.Distortion):
        return "Distortion"
    elif(effectId == EffectTypes.Pixelate):
        return "Pixelate"
    elif(effectId == EffectTypes.TVNoize):
        return "TVNoize"
    elif(effectId == EffectTypes.Edge):
        return "Edge"
    elif(effectId == EffectTypes.BlobDetect):
        return "BlobDetect"
    elif(effectId == EffectTypes.Desaturate):
        return "Desaturate"
    elif(effectId == EffectTypes.Contrast):
        return "Contrast"
    elif(effectId == EffectTypes.HueSaturation):
        return "HueSaturation"
    elif(effectId == EffectTypes.Colorize):
        return "Colorize"
    elif(effectId == EffectTypes.Invert):
        return "Invert"
    elif(effectId == EffectTypes.ValueToHue):
        return "ValueToHue"
    elif(effectId == EffectTypes.Threshold):
        return "Threshold"
    elif(effectId == EffectTypes.ImageAdd):
        return "ImageAdd"
    else:
        return None

class ZoomModes():
    In, Out, InOut, Full = range(4)

    def getChoices(self):
        return ["In", "Out", "InOut", "Full"]

class ScrollModes():
    NoFlip, Flip = range(2)

    def getChoices(self):
        return ["NoFlip", "Flip"]

class FlipModes():
    NoFlip, Vertical, Horizontal, Both = range(4)

    def getChoices(self):
        return ["NoFlip", "Vertical", "Horizontal", "Both"]

class DistortionModes():
    Black, White, Both = range(3)

    def getChoices(self):
        return ["Black", "White", "Both"]

class EdgeModes():
    CannyOnTop, Canny, Sobel, Laplace = range(4)

    def getChoices(self):
        return ["CannyOnTop", "Canny", "Sobel", "Laplace"]

class EdgeColourModes():
    Value, Saturation, Hue = range(3)

    def getChoices(self):
        return ["Value", "Saturation", "Hue"]

class DesaturateModes():
    Plus, Minus, Mask = range(3)

    def getChoices(self):
        return ["Plus", "Minus", "Mask"]

class ContrastModes():
    Increase, IncDec, Decrease, Full = range(4)

    def getChoices(self):
        return ["Increase", "IncDec", "Decrease", "Full"]

class HueSatModes():
    Increase, Decrease, Full = range(3)

    def getChoices(self):
        return ["Increase", "Decrease", "Full"]

class ColorizeModes():
    Add, Subtract, SubtractFrom, Multiply = range(4)

    def getChoices(self):
        return ["Add", "Subtract", "SubFrom", "Multiply"]

class ValueToHueModes():
    Off, Value, Saturation, Hue = range(4)

    def getChoices(self):
        return ["Off", "Value", "Saturation", "Hue"]

class MirrorModes():
    Vertical, Horisontal = range(2)

    def getChoices(self):
        return ["Vertical", "Horisontal"]

class BlobDetectModes():
    CircleAdd, CircleOnly, RectangleAdd, RectangleOnly, NoAdd, Blank = range(6)

    def getChoices(self):
        return ["CircleAdd", "CircleOnly", "RectangleAdd", "RectangleOnly", "NoAdd", "Blank"]

class PixelateModes():
    Clean, Round, Star = range(3)

    def getChoices(self):
        return ["Clean", "Round", "Star"]

class TVNoizeModes():
    Star, Round, Clean = range(3)

    def getChoices(self):
        return ["Clean", "Round", "Star"]

class BlurModes():
    Blur, Bilateral = range(2)

    def getChoices(self):
        return ["Blur", "Bilateral"]

class RayModes():
    Lower, Upper, Both, Mirror = range(4)

    def getChoices(self):
        return ["Lower", "Upper", "Both", "Mirror"]

