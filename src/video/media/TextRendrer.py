'''
Created on Oct 7, 2012

@author: pcn
'''
import sys
import os
from PIL import ImageFont, ImageDraw, Image

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
    fontPath = os.path.join(fontPath, font + ".ttf")
    if(os.path.isfile(fontPath) != True):
        fontPath = os.path.join(fontPath, font + ".otf")
    if (os.path.isfile(fontPath) == False):
        print "Could not find font: %s (%s)" % (font, fontPath)
    font = ImageFont.truetype(fontPath, fontSize)
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

