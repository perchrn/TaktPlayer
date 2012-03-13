'''
Created on 14. feb. 2012

@author: pcn
'''
class EffectTypes():
    Zoom, Flip, Scroll, Blur, BlurContrast, Distortion, Edge, Desaturate, Contrast, HueSaturation, Colorize, Invert, Threshold = range(13)

    def getChoices(self):
        return ["None",
                "Zoom",
                "Flip",
                "Scroll",
                "Blur",
                "BlurContrast",
                "Distortion",
                "Edge",
                "Desaturate",
                "Contrast",
                "HueSaturation",
                "Colorize",
                "Invert",
                "Threshold"]
    def getDescriptions(self):
        return ["None",
                "Zoom inn/out and even crop video.",
                "Flip video horizontal/vertical.",
                "Scroll image.",
                "Blur video.",
                "Blur and multiply with self.",
                "Distort image to black or white.",
                "Edge detection effects.",
                "Selective desaturation effects.",
                "Adjust brightness and contrast",
                "Rotate colors and adjust saturation.",
                "Add/subtract/multiply with color.",
                "Invert video.",
                "Threshold video to black and white."]

def getEffectId(name):
    lowername = name.lower()
    if(lowername == "zoom"):
        return EffectTypes.Zoom
    elif(lowername == "flip"):
        return EffectTypes.Flip
    elif(lowername == "scroll"):
        return EffectTypes.Scroll
    elif(lowername == "blur"):
        return EffectTypes.Blur
    elif(lowername == "blurcontrast"):
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
    else:
        return None

def getEffectName(effectId):
    if(effectId == EffectTypes.Zoom):
        return "Zoom"
    elif(effectId == EffectTypes.Flip):
        return "Flip"
    elif(effectId == EffectTypes.Scroll):
        return "Scroll"
    elif(effectId == EffectTypes.Blur):
        return "Blur"
    elif(effectId == EffectTypes.BlurContrast):
        return "BlurContrast"
    elif(effectId == EffectTypes.Distortion):
        return "Distortion"
    elif(effectId == EffectTypes.Edge):
        return "Edge"
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
    elif(effectId == EffectTypes.Threshold):
        return "Threshold"
    else:
        return None

class ZoomModes():
    In, Out, InOut, Full = range(4)

    def getChoices(self):
        return ["In", "Out", "InOut", "Full"]

class ScrollModes():
    NoFlip, Flip, NoRepeat = range(3)

    def getChoices(self):
        return ["NoFlip", "Flip", "NoRepeat"]

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

class ColorizeModes():
    Add, Subtract, SubtractFrom, Multiply = range(4)

    def getChoices(self):
        return ["Add", "Subtract", "SubtractFrom", "Multiply"]

