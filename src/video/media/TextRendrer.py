'''
Created on Oct 7, 2012

@author: pcn
'''
import sys
import os
from PIL import ImageFont, ImageDraw, Image

class FontError(Exception):
    def __init__(self, value):
        self.value = value.encode("utf-8")

    def __str__(self):
        return repr(self.value)

def findOsFontPath():
    if(sys.platform == "darwin"):
        return "/Library/Fonts"
    elif(sys.platform == "win32"):
        winDir = os.getenv('WINDIR')
        return os.path.join(winDir, "fonts")
    else:
        return "/usr/share/fonts/"

def generateTextImageAndMask(text, font, fontPath, fontSize, red, green, blue):
    colour = (blue, green, red) #BGR (to skip transforming later.)
    retries = 4
    if (os.path.isdir(fontPath) == False):
        print "Could not find fontpath: (%s)" % (fontPath)
        raise FontError("Bad font path: " + str(fontPath))
        return
    fontFile = os.path.join(fontPath, font + ".ttf")
    if(os.path.isfile(fontFile) != True):
        print "Could not find font: %s.ttf trying %s.otf" % (font, font)
        fontFile = os.path.join(fontPath, font + ".otf")
    while(retries > 0):
        try:
#            print "DEBUG pcn: opening font: " + str(fontFile)
            font = ImageFont.truetype(fontFile, fontSize)
            retries = -1
        except:
            if(retries == 4):
                fontFile = os.path.join(fontPath, "Ariel.ttf")
            elif(retries == 3):
                fontFile = os.path.join(fontPath, "Ariel.otf")
            elif(retries == 2):
                fontFile = "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
            else:
                raise FontError("Unable to load font: " + str(font) + " in " + str(fontPath))
                return
            retries -= 1
    textSplit = text.split("\\n")
    textHeight = 0
    textWidth = 0
    for textLines in textSplit:
        textW, textH = font.getsize(textLines)
        textHeight += textH
        textWidth = max(textWidth, textW)
    #print "DEBUG pcn: textSize " + str(textSize) + " for: " + text 
    fontPILImage = Image.new('RGB', (textWidth, textHeight), (0, 0, 0))
    fontPILMaskImage = Image.new('RGB', (textWidth, textHeight), (0, 0, 0))
    drawArea = ImageDraw.Draw(fontPILImage)
    maskArea = ImageDraw.Draw(fontPILMaskImage)
    posY = 0
    for textLines in textSplit:
        textW, textH = font.getsize(textLines)
        posX = int((textWidth - textW) / 2)
        drawArea.text((posX, posY), textLines, font=font, fill=colour)
        maskArea.text((posX, posY), textLines, font=font, fill=(255,255,255))
        posY += textH

    textPILMask = fontPILMaskImage.convert('L')

    return fontPILImage, textPILMask

