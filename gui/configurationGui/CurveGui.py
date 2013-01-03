'''
Created on 27. dec. 2012

@author: pcn
'''

import wx
from widgets.PcnImageButton import PcnImageButton
from widgets.PcnCurveDisplayWindget import PcnCurveDisplayWidget
from widgets.PcnEvents import EVT_DOUBLE_CLICK_EVENT, EVT_MOUSE_MOVE_EVENT
import math
from configurationGui.UtilityDialogs import updateChoices
import numpy

import warnings
warnings.simplefilter('ignore', numpy.RankWarning)

class Curve(object):
    Linear, Curve, Array, Off = range(4)

    def getChoices(self):
        return ["Linear", "Curve", "Array", "Off"]

    def __init__(self):
        self._mode = self.Linear
        self._points = [(0,0), (255,255)]
        self._curveCoefficients = []

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
                        if(nextPoint[0] >= xPos):
#                            print "DEBUG pcn: xPos: " + str(xPos) + " i: " + str(i) + " afterPoint = " + str(nextPoint),
                            break
#                print "DEBUG pcn: beforePoint " + str(beforePoint) + " afterPoint " + str(afterPoint)
                subPos = xPos - beforePoint[0]
                if(afterPoint[0] == beforePoint[0]):
                    subCalc = afterPoint[1]
                else:
                    subCalc = beforePoint[1] + ((afterPoint[1] - beforePoint[1]) * (float(subPos) / (afterPoint[0] - beforePoint[0])))
                return subCalc
        if(self._mode == self.Curve):
            numPoints = len(self._curveCoefficients)
            if(numPoints < 1):
                return xPos
            ySum = 0
            for i in range(numPoints):
                coefficient = self._curveCoefficients[i]
                ySum += coefficient * math.pow(xPos, numPoints-1-i)
            yValue = min(max(int(ySum), 0.0), 255.99)
            return yValue
        if(self._mode == self.Array):
            i = min(max(int(xPos), 0), 255)
            return self._points[i]
        if(self._mode == self.Off):
            return xPos

    def changeModeString(self, modeString):
        if(modeString.lower() == "array"):
            self.changeMode(self.Array)
        if(modeString.lower() == "curve"):
            self.changeMode(self.Curve)
        elif(modeString.lower() == "off"):
            self.changeMode(self.Off)
        else:
            self.changeMode(self.Linear)

    def changeMode(self, newMode):
        if(self._mode != newMode):
            if(newMode == self.Linear):
                self._mode = self.Linear
                self._points = [(0,0), (255,255)]
            elif(newMode == self.Curve):
                if(self._mode == self.Linear):
                    pass
                elif(self._mode == self.Array):
                    self._points = [(0,0), (255,255)]
                elif(self._mode == self.Off):
                    self._points = [(0,0), (255,255)]
                self._calculateCoefficients()
                self._mode = self.Curve
            elif(newMode == self.Array):
                if(self._mode == self.Linear):
                    newArray = self.getArray()
                    self._points = newArray
                if(self._mode == self.Curve):
                    newArray = self.getArray()
                    self._points = newArray
                if(self._mode == self.Off):
                    self._mode = self.Linear
                    self._points = [(0,0), (255,255)]
                    newArray = self.getArray()
                    self._points = newArray
                self._mode = self.Array
            elif(newMode == self.Off):
                self._mode = self.Off
                self._points = []

    def _calculateCoefficients(self):
        numPoints = len(self._points)
        if(numPoints < 1):
            self._curveCoefficients = []
        else:
            xArr = []
            yArr = []
            for point in self._points:
                xArr.append(point[0])
                yArr.append(point[1])
            self._curveCoefficients = numpy.polyfit(xArr, yArr, numPoints)

    def getPoints(self):
        if(self._mode == self.Linear):
            return self._points
        if(self._mode == self.Curve):
            return self._points
        return []

    def findNearestPoint(self, xPos, yPos):
        if((self._mode == self.Linear) or (self._mode == self.Curve)):
            closePoints = []
            for point in self._points:
                if(abs(point[0] - xPos) < 5):
                    if(abs(point[1] - yPos) < 5):
                        closePoints.append(point)
            if(len(closePoints) > 1):
                leastDistance = 100
                returnPoint = None
                for point in closePoints:
                    pointDistance = math.sqrt(float(math.pow(xPos-point[0], 2) + math.pow(yPos-point[1], 2)))
                    if(pointDistance < leastDistance):
                        leastDistance = pointDistance
                        returnPoint = point
                return returnPoint
            elif(len(closePoints) == 1):
                return closePoints[0]
            return None
        return None

    def movePoint(self, oldPoint, newPoint):
        if((self._mode == self.Linear) or (self._mode == self.Curve)):
            if(oldPoint != newPoint):
                numPoints = len(self._points)
                for i in range(numPoints):
                    if(self._points[i] == oldPoint):
                        done = False
                        if(i > 0):
                            if(self._points[i-1][0] > newPoint[0]):
                                self._points[i] = self._points[i-1]
                                self._points[i-1] = newPoint
                                done = True
                        if(i < (numPoints-2)):
                            if(self._points[i+1][0] < newPoint[0]):
                                self._points[i] = self._points[i+1]
                                self._points[i+1] = newPoint
                                done = True
                        if(done == False):
                            self._points[i] = newPoint
            if(self._mode == self.Curve):
                self._calculateCoefficients()

    def drawingDone(self):
        if((self._mode == self.Linear) or (self._mode == self.Curve)):
            self._movePoint = None

    def addPoint(self, newPoint):
        if((self._mode == self.Linear) or (self._mode == self.Curve)):
            self._movePoint = None
            added = False
            updated = False
            nextPoint = None
            for i in range(len(self._points)):
                oldPoint = self._points[i]
                if(added == True):
                    tmpPoint = self._points[i]
                    self._points[i] = nextPoint
                    nextPoint = tmpPoint
                else:
                    if(oldPoint[0] == newPoint[0]):
                        self._points[i] = newPoint
                        updated = True
                        break
                    elif(oldPoint[0] > newPoint[0]):
                        nextPoint = self._points[i]
                        self._points[i] = newPoint
                        added = True
            if(added == True):
                self._points.append(nextPoint)
            else:
                if(updated == False):
                    self._points.append(newPoint)
            if(self._mode == self.Curve):
                self._calculateCoefficients()

    def drawPoint(self, point):
        if((self._mode == self.Linear) or (self._mode == self.Curve)):
            if(self._movePoint == None):
                self._movePoint = self.findNearestPoint(point[0], point[1])
            if(self._movePoint != None):
                self.movePoint(self._movePoint, point)
                self._movePoint = point
        if(self._mode == self.Array):
            i = min(max(int(point[0]), 0), 255)
            self._points[i] = point[1]

    def getArray(self):
        if(self._mode == self.Off):
            return None
        returnArray = []
        for xPos in range(256):
            returnArray.append(int(self.getValue(xPos)))
        return returnArray

    def setString(self, newString):
#        print "DEBUG pcn: setString! " + newString
        bigSplit = newString.split('|', 1)
        if(len(bigSplit) > 1):
            if(bigSplit[0] == "Linear"):
                self._mode = self.Linear
            if(bigSplit[0] == "Curve"):
                self._mode = self.Curve
            if((bigSplit[0] == "Linear") or (bigSplit[0] == "Curve")):
                pointsSplit = bigSplit[1].split('|')
                self._points = []
                for pointString in pointsSplit:
                    coordinateSplit = pointString.split(',')
                    if(len(coordinateSplit) == 2):
                        try:
                            xPos = min(max(int(coordinateSplit[0]), 0), 255)
                            yPos = min(max(int(coordinateSplit[1]), 0), 255)
                            self._points.append((xPos, yPos))
#                            print "DEBUG pcn: adding point: " + str((xPos,yPos))
                        except:
                            pass
                if(len(self._points) < 1):
                    self._points.append((0,0))
                if(len(self._points) < 2):
                    self._points.append((255,255))
                if(bigSplit[0] == "Curve"):
                    self._calculateCoefficients()
                return
            elif(bigSplit[0] == "Array"):
                self._mode = self.Array
                return
        self._mode = self.Off

    def getString(self):
        if(self._mode == self.Linear):
            returnString = "Linear"
            for point in self._points:
                returnString += "|" + str(point[0]) + "," + str(point[1])
            return returnString
        if(self._mode == self.Curve):
            returnString = "Curve"
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

    def getMode(self):
        return self._mode

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

        curveModeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText1 = wx.StaticText(self._mainCurveGuiPlane, wx.ID_ANY, "Curve mode:") #@UndefinedVariable
        self._curveModeField = wx.ComboBox(self._mainCurveGuiPlane, wx.ID_ANY, size=(200, -1), choices=["Linear"], style=wx.CB_READONLY) #@UndefinedVariable
        updateChoices(self._curveModeField, self._curveConfig.getChoices, "Linear", "Linear")
        curveModeButton = PcnImageButton(self._mainCurveGuiPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        curveModeButton.Bind(wx.EVT_BUTTON, self._onCurveModeHelp) #@UndefinedVariable
        curveModeSizer.Add(tmpText1, 1, wx.ALL, 5) #@UndefinedVariable
        curveModeSizer.Add(self._curveModeField, 2, wx.ALL, 5) #@UndefinedVariable
        curveModeSizer.Add(curveModeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainCurveGuiSizer.Add(curveModeSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._mainCurveGuiPlane.Bind(wx.EVT_COMBOBOX, self._onCurveModeChosen, id=self._curveModeField.GetId()) #@UndefinedVariable

        self._curveGraphicsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._curveGraphicsLabel = wx.StaticText(self._mainCurveGuiPlane, wx.ID_ANY, "Curve graph:") #@UndefinedVariable
        self._curveGraphicsDisplay = PcnCurveDisplayWidget(self._mainCurveGuiPlane)
        curveGraphicsValueButton = PcnImageButton(self._mainCurveGuiPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        curveGraphicsValueButton.Bind(wx.EVT_BUTTON, self._onCurveGraphicsHelp) #@UndefinedVariable
        self._curveGraphicsDisplay.Bind(wx.EVT_BUTTON, self._onCurveSingleClick) #@UndefinedVariable
        self._curveGraphicsDisplay.Bind(EVT_DOUBLE_CLICK_EVENT, self._onCurveDoubleClick) #@UndefinedVariable
        self._curveGraphicsDisplay.Bind(EVT_MOUSE_MOVE_EVENT, self._onMouseMove) #@UndefinedVariable
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

    def _onCurveModeHelp(self, event):
        text = """
Selects how we edit the curve.

Linear:\tAdd points to define curve.
Curve:\tAdd points to define bendt curve.
Array:\tDraw the curve pixel by pixel.
Off:\tStraight line from 0,0 to 255,255.
"""
        dlg = wx.MessageDialog(self._mainCurveGuiPlane, text, 'Curve mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onCurveModeChosen(self, event):
        updateChoices(self._curveModeField, self._curveConfig.getChoices, self._curveModeField.GetValue(), "Linear")
        self._curveConfig.changeModeString(self._curveModeField.GetValue())
        self._updateCurveGraph()

    def _onCurveGraphicsHelp(self, event):
        if(self._curveConfig.getMode() == Curve.Linear):
            text = "Shows the curve\n"
            text += "\n"
            text += "Add points by doubble clicking.\n"
            text += "Select and drag points with left button."
        if(self._curveConfig.getMode() == Curve.Curve):
            text = "Shows the curve\n"
            text += "\n"
            text += "Add points by doubble clicking.\n"
            text += "Select and drag points with left button."
        if(self._curveConfig.getMode() == Curve.Array):
            text = "Shows the curve\n"
            text += "\n"
            text += "Set point(s) with left button."
        else:
            text = "Shows the curve."
        dlg = wx.MessageDialog(self._mainCurveGuiPlane, text, 'Curve display help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onCurveSingleClick(self, event):
        self._curveConfig.drawingDone()
        self._updateCurveGraph()

    def _onCurveDoubleClick(self, event):
        self._curveConfig.addPoint(self._curveGraphicsDisplay.getLastPos())
        self._updateCurveGraph()

    def _onMouseMove(self, event):
        if(event.mousePressed == True):
            self._curveConfig.drawPoint(event.mousePosition)
        else:
            self._curveConfig.drawingDone()
        self._updateCurveGraph()

    def _updateCurveGraph(self):
        self._curveGraphicsDisplay.drawCurve(self._curveConfig)
        self._checkForUpdates()

    def _onCloseButton(self, event):
        if(self._closeCallback != None):
            self._closeCallback()
        self._hideCurveCallback()


    def _onSaveButton(self, event):
        curveString = self._curveConfig.getString()
        if(self._updateWidget != None):
            self._updateWidget.SetValue(curveString)
        if(self._saveCallback):
            if(self._saveArgument != None):
                self._saveCallback(self._saveArgument, curveString)
            else:
                self._saveCallback(None)
        self._lastSavedCurveString = curveString
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

