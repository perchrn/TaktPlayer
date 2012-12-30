'''
Created on 27. dec. 2012

@author: pcn
'''

import wx
from widgets.PcnImageButton import PcnImageButton
from widgets.PcnCurveDisplayWindget import PcnCurveDisplayWidget

class Curve(object):
    Off, Linear, Array = range(3)

    def __init__(self):
        self._mode = self.Linear
        self._points = [(0,0), (255,255)]

    def getValue(self, xPos):
        if(self._mode == self.Linear):
            firstPoint = self._points[0]
            lastPoint = self._points[len(self._points)-1]
            if(xPos < firstPoint[0]):
                return firstPoint[1]
            elif(xPos > lastPoint[0]):
                return lastPoint[1]
            else:
                beforePoint = firstPoint
                afterPoint = lastPoint
                numPoints = len(self._points)
                if(numPoints > 2):
                    beforePoint = firstPoint
                    afterPoint = firstPoint
                    for i in range(len(self._points)-1):
                        nextI = i + 1
                        nextPoint = self._points[nextI]
                        beforePoint = afterPoint
                        afterPoint = nextPoint
                        if(nextPoint[0] < xPos):
                            pass
                        else:
                            print "DEBUG pcn: xPos: " + str(xPos) + " i: " + str(i) + " afterPoint = " + str(nextPoint),
                            break
                print "DEBUG pcn: beforePoint " + str(beforePoint) + " afterPoint " + str(afterPoint)
                subPos = xPos - beforePoint[0]
                subCalc = beforePoint[1] + ((afterPoint[1] - beforePoint[1]) * (float(subPos) / (afterPoint[0] - beforePoint[0])))
                return subCalc
        if(self._mode == self.Array):
            i = min(max(int(xPos), 255), 0)
            return self._points[i]
        if(self._mode == self.Off):
            return xPos

    def getArray(self):
        if(self._mode == self.Off):
            return None
        returnArray = []
        for xPos in range(256):
            returnArray.append(int(self.getValue(xPos)))
        return returnArray

    def setString(self, newString):
        print "DEBUG pcn: setString! " + newString
        bigSplit = newString.split('|', 1)
        if(len(bigSplit) > 1):
            if(bigSplit[0] == "Linear"):
                print "DEBUG pcn: Linear!"
                print "DEBUG pcn: bigSplit len: " + str(len(bigSplit))
                print "DEBUG pcn: bigSplit[1]: " + str(bigSplit[1])
                self._mode = self.Linear
                pointsSplit = bigSplit[1].split('|')
                self._points = []
                for pointString in pointsSplit:
                    print "DEBUG pcn: pointString: " + pointString
                    coordinateSplit = pointString.split(',')
                    if(len(coordinateSplit) == 2):
                        try:
                            print "DEBUG pcn: coordinateSplit: " + str(coordinateSplit[0]) + " " + str(coordinateSplit[1])
                            xPos = min(max(int(coordinateSplit[0]), 0), 255)
                            yPos = min(max(int(coordinateSplit[1]), 0), 255)
                            self._points.append((xPos, yPos))
                            print "DEBUG pcn: adding point: " + str((xPos,yPos))
                        except:
                            pass
                if(len(self._points) < 1):
                    self._points.append((0,0))
                if(len(self._points) < 2):
                    self._points.append((255,255))
                return
            elif(bigSplit[0] == "Array"):
                print "DEBUG pcn: Linear!"
                self._mode = self.Array
                return
        self._mode = self.Off

    def getString(self):
        if(self._mode == self.Linear):
            returnString = "Linear"
            for point in self._points:
                returnString += "|" + str(point[0]) + "," + str(point[1])
            return returnString
        if(self._mode == self.Array):
            returnString = "Array|"
            first = True
            for point in self._points:
                if(first == False):
                    returnString += ','
                first = False
                returnString += str(point)
            return returnString
        return "Off"

class CurveGui(object):
    def __init__(self, mainConfing):
        self._mainConfig = mainConfing
        self._updateWidget = None
        self._closeCallback = None
        self._saveCallback = None
        self._saveArgument = None

        self._curveConfig = Curve()

        self._helpBitmap = wx.Bitmap("graphics/helpButton.png") #@UndefinedVariable
        self._helpPressedBitmap = wx.Bitmap("graphics/helpButtonPressed.png") #@UndefinedVariable

        self._closeButtonBitmap = wx.Bitmap("graphics/closeButton.png") #@UndefinedVariable
        self._closeButtonPressedBitmap = wx.Bitmap("graphics/closeButtonPressed.png") #@UndefinedVariable
        self._updateButtonBitmap = wx.Bitmap("graphics/updateButton.png") #@UndefinedVariable
        self._updateButtonPressedBitmap = wx.Bitmap("graphics/updateButtonPressed.png") #@UndefinedVariable
        self._updateRedButtonBitmap = wx.Bitmap("graphics/updateButtonRed.png") #@UndefinedVariable
        self._updateRedButtonPressedBitmap = wx.Bitmap("graphics/updateButtonRedPressed.png") #@UndefinedVariable
        self._saveBigBitmap = wx.Bitmap("graphics/saveButtonBig.png") #@UndefinedVariable
        self._saveBigPressedBitmap = wx.Bitmap("graphics/saveButtonBigPressed.png") #@UndefinedVariable
        self._saveBigGreyBitmap = wx.Bitmap("graphics/saveButtonBigGrey.png") #@UndefinedVariable

    def setupCurveGui(self, plane, sizer, parentSizer, parentClass):
        print "DEBUG pcn: setupCurveGui()"
        self._mainCurveGuiPlane = plane
        self._mainCurveGuiSizer = sizer
        self._parentSizer = parentSizer
        self._hideCurveCallback = parentClass.hideCurveGui
        self._fixCurveGuiLayout = parentClass.fixCurveGuiLayout

        headerLabel = wx.StaticText(self._mainCurveGuiPlane, wx.ID_ANY, "Curve editor:") #@UndefinedVariable
        headerFont = headerLabel.GetFont()
        headerFont.SetWeight(wx.BOLD) #@UndefinedVariable
        headerLabel.SetFont(headerFont)
        self._mainCurveGuiSizer.Add(headerLabel, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        self._curveGraphicsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._curveGraphicsLabel = wx.StaticText(self._mainCurveGuiPlane, wx.ID_ANY, "Curve graph:") #@UndefinedVariable
        self._curveGraphicsDisplay = PcnCurveDisplayWidget(self._mainCurveGuiPlane)
        curveGraphicsValueButton = PcnImageButton(self._mainCurveGuiPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        curveGraphicsValueButton.Bind(wx.EVT_BUTTON, self._onCurveGraphicsHelp) #@UndefinedVariable
        self._curveGraphicsSizer.Add(self._curveGraphicsLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._curveGraphicsSizer.Add(self._curveGraphicsDisplay, 2, wx.ALL, 5) #@UndefinedVariable
        self._curveGraphicsSizer.Add(curveGraphicsValueButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainCurveGuiSizer.Add(self._curveGraphicsSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._curveGraphicsId = self._curveGraphicsDisplay.GetId()


        """Buttons"""

        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = PcnImageButton(self._mainCurveGuiPlane, self._closeButtonBitmap, self._closeButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(55, 17)) #@UndefinedVariable
        closeButton.Bind(wx.EVT_BUTTON, self._onCloseButton) #@UndefinedVariable
        self._saveButton = PcnImageButton(self._mainCurveGuiPlane, self._updateButtonBitmap, self._updateButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(67, 17)) #@UndefinedVariable
        self._saveButton.Bind(wx.EVT_BUTTON, self._onSaveButton) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(self._saveButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainCurveGuiSizer.Add(self._buttonsSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

    def _onCurveGraphicsHelp(self, event):
        text = """
Shows the curve.
"""
        dlg = wx.MessageDialog(self._mainCurveGuiPlane, text, 'Curve display help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()


    def _updateCurveGraph(self):
        self._curveGraphicsDisplay.drawCurve(self._curveConfig)

    def _onCloseButton(self, event):
        if(self._closeCallback != None):
            self._closeCallback()
        self._hideCurveCallback()


    def _onSaveButton(self, event):
        modeString = self._getModeString()
        if(self._updateWidget != None):
            self._updateWidget.SetValue(modeString)
        if(self._saveCallback):
            if(self._saveArgument != None):
                self._saveCallback(self._saveArgument, modeString)
            else:
                self._saveCallback(None)
        self._lastSavedCurveString = modeString
        self._checkForUpdates()

    def _checkForUpdates(self, event = None):
        newCurveString = self._curveConfig.getString()
        if(self._lastSavedCurveString != newCurveString):
            if(self._saveArgument == None):
                self._saveButton.setBitmaps(self._updateRedButtonBitmap, self._updateRedButtonPressedBitmap)
            else:
                self._saveButton.setBitmaps(self._saveBigBitmap, self._saveBigPressedBitmap)
        else:
            if(self._saveArgument == None):
                self._saveButton.setBitmaps(self._updateButtonBitmap, self._updateButtonPressedBitmap)
            else:
                self._saveButton.setBitmaps(self._saveBigGreyBitmap, self._saveBigGreyBitmap)

    def updateGui(self, curveConfigString, widget, closeCallback, saveCallback, saveArgument):
        self._updateWidget = widget
        self._closeCallback = closeCallback
        self._saveCallback = saveCallback
        self._saveArgument = saveArgument
        self._lastSavedCurveString = curveConfigString
        self._curveConfig.setString(curveConfigString)
        self._updateCurveGraph()
        self._checkForUpdates()

