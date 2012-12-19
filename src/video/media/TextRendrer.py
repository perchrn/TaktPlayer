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
    retries = 2
    fontFile = os.path.join(fontPath, font + ".ttf")
    if(os.path.isfile(fontPath) != True):
        fontFile = os.path.join(fontPath, font + ".otf")
    if (os.path.isfile(fontPath) == False):
        print "Could not find font: %s (%s)" % (font, fontPath)
    while(retries > 0):
        try:
            font = ImageFont.truetype(fontFile, fontSize)
            retries = 0
        except:
            if(retries == 2):
                fontFile = os.path.join(fontPath, "Ariel.ttf")
            elif(retries == 1):
                fontFile = "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
            else:
                raise FontError("Unable to load font: " + str(font) + " in " + str(fontPath))
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
    drawArea = ImageDraw.Draw(fontPILImage)
    posY = 0
    for textLines in textSplit:
        textW, textH = font.getsize(textLines)
        posX = int((textWidth - textW) / 2)
        drawArea.text((posX, posY), textLines, font=font, fill=colour)
        posY += textH

    textPILMask = fontPILImage.convert('L')

    return fontPILImage, textPILMask

