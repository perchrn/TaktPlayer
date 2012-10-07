'''
Created on Sep 28, 2012

@author: pcn
'''
import wx
import os
import sys
import PIL.Image as Image
import PIL.ImageFont as ImageFont
import PIL.ImageDraw as ImageDraw
from video.media.TextRendrer import findOsFontPath

class MediaFontDialog(wx.Dialog): #@UndefinedVariable
    def __init__(self, parent, title, fontWidget, text):
        super(MediaFontDialog, self).__init__(parent=parent, title=title, size=(600, 500))

        if((text == None) or (text == "")):
            self._previewText = "Testing 1 - 2."
        else:
            self._previewText = text
        self._fontWidget = fontWidget
        fontString = self._fontWidget.GetValue()
        fontStringSplit = fontString.split(";")
        startFont = fontStringSplit[0]
        try:
            startSize = int(fontStringSplit[1])
        except:
            startSize = 32
        try:
            startColour = fontStringSplit[2]
        except:
            startColour = "#FFFFFF"
        startPos = 0
        if(startColour.startswith("#")):
            startPos = 1
        startRed = int(startColour[startPos:startPos+2], 16)
        startGreen = int(startColour[startPos+2:startPos+4], 16)
        startBlue = int(startColour[startPos+4:startPos+6], 16)

        dialogSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable
        self.SetBackgroundColour((180,180,180))

        infoText = wx.StaticText(self, wx.ID_ANY, "Please select font:") #@UndefinedVariable
        dialogSizer.Add(infoText, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        fontListSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        fontListLabel = wx.StaticText(self, wx.ID_ANY, "Font:") #@UndefinedVariable
        self._fontListField = wx.ComboBox(self, wx.ID_ANY, size=(200, -1), choices=[], style=wx.CB_READONLY) #@UndefinedVariable
        self._fontListField.Clear()
        valueOk = False
        self._fontDir = findOsFontPath()
        rawFontFileList = os.listdir(self._fontDir)
        backupSelection = None
        for fontFile in rawFontFileList:
            if(fontFile.lower().endswith(".ttf") == True):
                fontName = os.path.splitext(fontFile)[0].decode('utf8')
                self._fontListField.Append(fontName)
                if(backupSelection == None):
                    backupSelection = fontName
                if(startFont == fontName):
                    valueOk = True
        if(valueOk == True):
            self._fontListField.SetStringSelection(startFont)
        else:
            self._fontListField.SetStringSelection(backupSelection)
        self._fontListField.Bind(wx.EVT_COMBOBOX, self._onUpdate) #@UndefinedVariable
        fontListSizer.Add(fontListLabel, 1, wx.ALL, 5) #@UndefinedVariable
        fontListSizer.Add(self._fontListField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(fontListSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        fontSizeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        fontSizeLabel = wx.StaticText(self, wx.ID_ANY, "Size:") #@UndefinedVariable
        self._fontSizeField = wx.SpinCtrl(self, value=str(startSize), pos=(-1, -1), size=(200, -1)) #@UndefinedVariable
        self._fontSizeField.SetRange(8, 1000)
        self._fontSizeField.Bind(wx.EVT_SPINCTRL, self._onUpdate) #@UndefinedVariable
        fontSizeSizer.Add(fontSizeLabel, 1, wx.ALL, 5) #@UndefinedVariable
        fontSizeSizer.Add(self._fontSizeField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(fontSizeSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        colourSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        colourLabel = wx.StaticText(self, wx.ID_ANY, "Colour:") #@UndefinedVariable  
        self._colourField = wx.ColourPickerCtrl(self, col=(startRed,startGreen,startBlue), pos=(-1, -1), size=(200, -1), style=wx.CLRP_SHOW_LABEL) #@UndefinedVariable
        self._colourField.Bind(wx.EVT_COLOURPICKER_CHANGED, self._onUpdate) #@UndefinedVariable
        colourSizer.Add(colourLabel, 1, wx.ALL, 5) #@UndefinedVariable
        colourSizer.Add(self._colourField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(colourSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        emptyBitmap = wx.EmptyBitmap (600, 300, depth=3) #@UndefinedVariable
        self._previewArea = wx.StaticBitmap(self, wx.ID_ANY, emptyBitmap, size=(600,300)) #@UndefinedVariable
        dialogSizer.Add(self._previewArea, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        loadButton = wx.Button(self, wx.ID_ANY, 'Select', size=(60,-1)) #@UndefinedVariable
        loadButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        cancelButton = wx.Button(self, wx.ID_ANY, 'Cancel', size=(60,-1)) #@UndefinedVariable
        cancelButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        buttonsSizer.Add(loadButton, 1, wx.ALL, 5) #@UndefinedVariable
        buttonsSizer.Add(cancelButton, 1, wx.ALL, 5) #@UndefinedVariable
        loadButton.Bind(wx.EVT_BUTTON, self._onOk) #@UndefinedVariable
        cancelButton.Bind(wx.EVT_BUTTON, self._onCancel) #@UndefinedVariable
        dialogSizer.Add(buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self.SetSizer(dialogSizer)
        self._emptyWxImage = wx.EmptyImage(600,300) #@UndefinedVariable
        self._onUpdate(None)

    def _onUpdate(self, event):
        fontName = self._fontListField.GetValue()
        fontPath = os.path.join(self._fontDir, fontName + ".ttf")
        size = self._fontSizeField.GetValue()
        textColour = self._colourField.GetColour()
        font = ImageFont.truetype(fontPath, size)
        textSplit = self._previewText.split("\\n")
        textHeight = 0
        textWidth = 0
        for textLines in textSplit:
            textW, textH = font.getsize(textLines)
            textHeight += textH
            textWidth = max(textWidth, textW)
        fontPILImage = Image.new('RGB', (600,300), (0, 0, 0))
        drawArea = ImageDraw.Draw(fontPILImage)
        startX = int((600 - textWidth) / 2)
        startY = int((300 - textHeight) / 2)
        startX = max(0, startX)
        startY = max(0, startY)
        posY = startY
        for textLines in textSplit:
            textW, textH = font.getsize(textLines)
            posX = startX + int((textWidth - textW) / 2)
            drawArea.text((posX, posY), textLines, font=font, fill=(textColour.Red(),textColour.Green(),textColour.Blue()))
            posY += textH
        self._emptyWxImage.SetData(fontPILImage.convert("RGB").tostring())
        self._previewArea.SetBitmap(wx.BitmapFromImage(self._emptyWxImage)) #@UndefinedVariable

    def _onOk(self, event):
        fontName = self._fontListField.GetValue()
        size = self._fontSizeField.GetValue()
        textColour = self._colourField.GetColour()
        htmlColour = "#%02X%02X%02X" % (textColour.Red(),textColour.Green(),textColour.Blue())
        self._fontWidget.SetValue(fontName + ";" + str(size) + ";" + htmlColour)
        self.Destroy()

    def _onCancel(self, event):
        self.Destroy()

