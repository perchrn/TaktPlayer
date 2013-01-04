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
    Off, All, RGB, HSV = range(4)
    Linear, Curve, Array = range(3)

    def getChoices(self):
        return ["Off", "All", "RGB", "HSV"]
    def getSubChoices(self):
        return ["Linear", "Curve", "Array"]

    def __init__(self):
        self._curves = []
        self._curves.append(CurveChannel())
        self._curves.append(CurveChannel())
        self._curves.append(CurveChannel())
        self._mode = Curve.Off

    def getValue(self, xPos, subId = -1):
        if(self._mode == Curve.Off):
            return [xPos]
        elif(self._mode == Curve.All):
            return [self._curves[0].getValue(xPos)]
        else:
            if((subId >= 0) and (subId < 3)):
                return [self._curves[subId].getValue(xPos)]
            else:
                return [self._curves[0].getValue(xPos), self._curves[1].getValue(xPos), self._curves[2].getValue(xPos)]

    def changeModeString(self, modeString):
        print "DEBUG pcn: changeModeString: " + modeString
        if(modeString.lower() == "all"):
            self._mode = Curve.All
        elif(modeString.lower() == "rgb"):
            self._mode = Curve.RGB
        elif(modeString.lower() == "hsv"):
            self._mode = Curve.HSV
        else:
            self._mode = Curve.Off

    def changeSubModeString(self, modeString):
        self._curves[0].changeModeString(modeString)
        self._curves[1].changeModeString(modeString)
        self._curves[2].changeModeString(modeString)

    def getPoints(self, subId = -1):
        if(self._mode == Curve.Off):
            return [[]]
        elif(self._mode == Curve.All):
            return [self._curves[0].getPoints()]
        else:
            if((subId >= 0) and (subId < 3)):
                return [self._curves[subId].getPoints()]
            else:
                return [self._curves[0].getPoints(), self._curves[1].getPoints(), self._curves[2].getPoints()]

    def movePoint(self, oldPoint, newPoint, subId = -1):
        if(self._mode == Curve.Off):
            pass
        elif(self._mode == Curve.All):
            self._curves[0].movePoint(oldPoint, newPoint)
        else:
            if((subId >= 0) and (subId < 3)):
                self._curves[subId].movePoint(oldPoint, newPoint)

    def drawingDone(self):
        self._curves[0].drawingDone()
        self._curves[1].drawingDone()
        self._curves[2].drawingDone()

    def addPoint(self, newPoint, subId = -1):
        if(self._mode == Curve.Off):
            pass
        elif(self._mode == Curve.All):
            self._curves[0].addPoint(newPoint)
        else:
            if((subId >= 0) and (subId < 3)):
                self._curves[subId].addPoint(newPoint)

    def drawPoint(self, point, subId = -1):
        if(self._mode == Curve.Off):
            pass
        elif(self._mode == Curve.All):
            self._curves[0].drawPoint(point)
        else:
            if((subId >= 0) and (subId < 3)):
                self._curves[subId].drawPoint(point)

    def getArray(self, subId = -1):
        if(self._mode == Curve.Off):
            return None
        if(self._mode == Curve.All):
            return self._curves[0].getArray()
        else:
            if((subId >= 0) and (subId < 3)):
                return self._curves[subId].getArray()
            else:
                return (self._curves[0].getArray(), self._curves[1].getArray(), self._curves[2].getArray())

    def setString(self, newString):
        if(newString.lower() == "off"):
            self._mode = Curve.Off
            self._curves[0].setString("Linear|0,0|255,255")
            self._curves[1].setString("Linear|0,0|255,255")
            self._curves[2].setString("Linear|0,0|255,255")
            return
        curvesSplit = newString.split(';')
        if(len(curvesSplit) > 1):
            if(curvesSplit[0] == "All"):
                self._mode = Curve.All
                self._curves[0].setString(curvesSplit[1])
            else:
                if(curvesSplit[0] == "RGB"):
                    self._mode = Curve.RGB
                if(curvesSplit[0] == "HSV"):
                    self._mode = Curve.HSV
                self._curves[0].setString(curvesSplit[1])
                if(len(curvesSplit) > 2):
                    self._curves[1].setString(curvesSplit[2])
                    if(len(curvesSplit) > 2):
                        self._curves[2].setString(curvesSplit[3])
                    else:
                        self._curves[2].setString(curvesSplit[2])
                else:
                    self._curves[1].setString(curvesSplit[1])
                    self._curves[2].setString(curvesSplit[1])

    def getString(self):
        if(self._mode == Curve.Off):
            return "Off"
        elif(self._mode == Curve.All):
            returnString = "All;"
            returnString += self._curves[0].getString()
            return returnString
        elif(self._mode == Curve.RGB):
            returnString = "RGB;"
        elif(self._mode == Curve.HSV):
            returnString = "HSV;"
        returnString += self._curves[0].getString()
        returnString += ";"
        returnString += self._curves[1].getString()
        returnString += ";"
        returnString += self._curves[2].getString()
        return returnString

    def getMode(self):
        return self._mode

    def getSubMode(self):
        return self._curves[0].getMode()

class CurveChannel(object):
    def __init__(self):
        self._mode = Curve.Linear
        self._points = [(0,0), (255,255)]
        self._curveCoefficients = []

    def getValue(self, xPos):
        if(self._mode == Curve.Linear):
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
                            break
                subPos = xPos - beforePoint[0]
                if(afterPoint[0] == beforePoint[0]):
                    subCalc = afterPoint[1]
                else:
                    subCalc = beforePoint[1] + ((afterPoint[1] - beforePoint[1]) * (float(subPos) / (afterPoint[0] - beforePoint[0])))
                return subCalc
        if(self._mode == Curve.Curve):
            numPoints = len(self._curveCoefficients)
            if(numPoints < 1):
                return xPos
            ySum = 0
            for i in range(numPoints):
                coefficient = self._curveCoefficients[i]
                ySum += coefficient * math.pow(xPos, numPoints-1-i)
            yValue = min(max(int(ySum), 0.0), 255.99)
            return yValue
        if(self._mode == Curve.Array):
            i = min(max(int(xPos), 0), 255)
            return self._points[i]

    def changeModeString(self, modeString):
        if(modeString.lower() == "array"):
            self.changeMode(Curve.Array)
        elif(modeString.lower() == "curve"):
            self.changeMode(Curve.Curve)
        else:
            self.changeMode(Curve.Linear)

    def changeMode(self, newMode):
        print "DEBUG pcn: changeMode: " + str(newMode) + " from " + str(self._mode)
        if(self._mode != newMode):
            if(newMode == Curve.Linear):
                if(self._mode == Curve.Linear):
                    pass
                elif(self._mode == Curve.Array):
                    self._points = [(0,0), (255,255)]
                self._mode = Curve.Linear
            elif(newMode == Curve.Curve):
                if(self._mode == Curve.Linear):
                    pass
                elif(self._mode == Curve.Array):
                    self._points = [(0,0), (255,255)]
                self._calculateCoefficients()
                self._mode = Curve.Curve
            elif(newMode == Curve.Array):
                newArray = self.getArray()
                self._points = newArray
                self._mode = Curve.Array

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
        if(self._mode == Curve.Linear):
            return self._points
        if(self._mode == Curve.Curve):
            return self._points
        return []

    def _findNearestPoint(self, xPos, yPos):
        if((self._mode == Curve.Linear) or (self._mode == Curve.Curve)):
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
        if((self._mode == Curve.Linear) or (self._mode == Curve.Curve)):
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
            if(self._mode == Curve.Curve):
                self._calculateCoefficients()

    def drawingDone(self):
        if((self._mode == Curve.Linear) or (self._mode == Curve.Curve)):
            self._movePoint = None

    def addPoint(self, newPoint):
        if((self._mode == Curve.Linear) or (self._mode == Curve.Curve)):
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
            if(self._mode == Curve.Curve):
                self._calculateCoefficients()

    def drawPoint(self, point):
        if((self._mode == Curve.Linear) or (self._mode == Curve.Curve)):
            if(self._movePoint == None):
                self._movePoint = self._findNearestPoint(point[0], point[1])
            if(self._movePoint != None):
                self.movePoint(self._movePoint, point)
                self._movePoint = point
        if(self._mode == Curve.Array):
            i = min(max(int(point[0]), 0), 255)
            self._points[i] = point[1]

    def getArray(self):
        returnArray = []
        for xPos in range(256):
            returnArray.append(int(self.getValue(xPos)))
        return returnArray

    def setString(self, newString):
#        print "DEBUG pcn: setString! " + newString
        bigSplit = newString.split('|', 1)
        if(len(bigSplit) > 1):
            if(bigSplit[0] == "Linear"):
                self._mode = Curve.Linear
            if(bigSplit[0] == "Curve"):
                self._mode = Curve.Curve
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
                self._mode = Curve.Array
                return

    def getString(self):
        if(self._mode == Curve.Linear):
            returnString = "Linear"
            for point in self._points:
                returnString += "|" + str(point[0]) + "," + str(point[1])
            return returnString
        if(self._mode == Curve.Curve):
            returnString = "Curve"
            for point in self._points:
                returnString += "|" + str(point[0]) + "," + str(point[1])
            return returnString
        if(self._mode == Curve.Array):
            returnString = "Array|"
            first = True
            for point in self._points:
                if(first == False):
                    returnString += ','
                first = False
                returnString += str(point)
            return returnString

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
        self._curveModeField = wx.ComboBox(self._mainCurveGuiPlane, wx.ID_ANY, size=(200, -1), choices=["Off"], style=wx.CB_READONLY) #@UndefinedVariable
        updateChoices(self._curveModeField, self._curveConfig.getChoices, "Off", "Off")
        curveModeButton = PcnImageButton(self._mainCurveGuiPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        curveModeButton.Bind(wx.EVT_BUTTON, self._onCurveModeHelp) #@UndefinedVariable
        curveModeSizer.Add(tmpText1, 1, wx.ALL, 5) #@UndefinedVariable
        curveModeSizer.Add(self._curveModeField, 2, wx.ALL, 5) #@UndefinedVariable
        curveModeSizer.Add(curveModeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainCurveGuiSizer.Add(curveModeSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._mainCurveGuiPlane.Bind(wx.EVT_COMBOBOX, self._onCurveModeChosen, id=self._curveModeField.GetId()) #@UndefinedVariable

        curveSubModeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText1 = wx.StaticText(self._mainCurveGuiPlane, wx.ID_ANY, "Curve sub mode:") #@UndefinedVariable
        self._curveSubModeField = wx.ComboBox(self._mainCurveGuiPlane, wx.ID_ANY, size=(200, -1), choices=["Linear"], style=wx.CB_READONLY) #@UndefinedVariable
        updateChoices(self._curveSubModeField, self._curveConfig.getSubChoices, "Linear", "Linear")
        curveSubModeButton = PcnImageButton(self._mainCurveGuiPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        curveSubModeButton.Bind(wx.EVT_BUTTON, self._onCurveSubModeHelp) #@UndefinedVariable
        curveSubModeSizer.Add(tmpText1, 1, wx.ALL, 5) #@UndefinedVariable
        curveSubModeSizer.Add(self._curveSubModeField, 2, wx.ALL, 5) #@UndefinedVariable
        curveSubModeSizer.Add(curveSubModeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainCurveGuiSizer.Add(curveSubModeSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._mainCurveGuiPlane.Bind(wx.EVT_COMBOBOX, self._onCurveSubModeChosen, id=self._curveSubModeField.GetId()) #@UndefinedVariable

        self._curveChannelSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText1 = wx.StaticText(self._mainCurveGuiPlane, wx.ID_ANY, "Edit channel:") #@UndefinedVariable
        self._curveChannelField = wx.ComboBox(self._mainCurveGuiPlane, wx.ID_ANY, size=(200, -1), choices=["Red"], style=wx.CB_READONLY) #@UndefinedVariable
        updateChoices(self._curveChannelField, None, "Red", "Red", ["Red", "Green", "Blue"])
        curveChannelButton = PcnImageButton(self._mainCurveGuiPlane, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        curveChannelButton.Bind(wx.EVT_BUTTON, self._onCurveChannelHelp) #@UndefinedVariable
        self._curveChannelSizer.Add(tmpText1, 1, wx.ALL, 5) #@UndefinedVariable
        self._curveChannelSizer.Add(self._curveChannelField, 2, wx.ALL, 5) #@UndefinedVariable
        self._curveChannelSizer.Add(curveChannelButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainCurveGuiSizer.Add(self._curveChannelSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable
        self._mainCurveGuiPlane.Bind(wx.EVT_COMBOBOX, self._onCurveChannelChosen, id=self._curveChannelField.GetId()) #@UndefinedVariable

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
Selects curve mode.

Off:\tNo curve modifications are done.
All:\tOne curve controlls all channels.
RGB:\tOne curve for each RGB colour.
HSV:\tOne curve for each HSV channel.
"""
        dlg = wx.MessageDialog(self._mainCurveGuiPlane, text, 'Curve mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onCurveModeChosen(self, event):
        updateChoices(self._curveModeField, self._curveConfig.getChoices, self._curveModeField.GetValue(), "Off")
        self._curveConfig.changeModeString(self._curveModeField.GetValue())
        self._onCurveChannelChosen(None)
        self._updateCurveGraph()

    def _onCurveSubModeHelp(self, event):
        text = """
Selects how we edit the curve.

Linear:\tAdd points to define curve.
Curve:\tAdd points to define bendt curve.
Array:\tDraw the curve pixel by pixel.
"""
        dlg = wx.MessageDialog(self._mainCurveGuiPlane, text, 'Curve sub mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onCurveSubModeChosen(self, event):
        updateChoices(self._curveSubModeField, self._curveConfig.getSubChoices, self._curveSubModeField.GetValue(), "Linear")
        self._curveConfig.changeSubModeString(self._curveSubModeField.GetValue())
        self._updateCurveGraph()

    def _onCurveChannelHelp(self, event):
        if(self._curveConfig.getMode() == Curve.HSV):
            text = """
Selects which channel we are editing now.

Hue:\tEdits hue curve. (Colour rotation.)
Saturation:\tEdits saturation curve.
Value:\tEdits value curve.
"""
        else:
            text = """
Selects which channel we are editing now.

Red:\tEdits red colour curve.
Green:\tEdits green colour curve.
Blue:\tEdits blue colour curve.
"""
        dlg = wx.MessageDialog(self._mainCurveGuiPlane, text, 'Curve sub mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onCurveChannelChosen(self, event):
        if(self._curveConfig.getMode() == Curve.HSV):
            self._mainCurveGuiSizer.Show(self._curveChannelSizer)
            updateChoices(self._curveChannelField, None, self._curveChannelField.GetValue(), "Hue", ["Hue", "Saturation", "Value"])
        elif(self._curveConfig.getMode() == Curve.RGB):
            self._mainCurveGuiSizer.Show(self._curveChannelSizer)
            updateChoices(self._curveChannelField, None, self._curveChannelField.GetValue(), "Red", ["Red", "Green", "Blue"])
        else:
            self._mainCurveGuiSizer.Hide(self._curveChannelSizer)
        self._fixCurveGuiLayout()

    def _onCurveGraphicsHelp(self, event):
        if(self._curveConfig.getSubMode() == Curve.Linear):
            text = "Shows the curve\n"
            text += "\n"
            text += "Add points by doubble clicking.\n"
            text += "Select and drag points with left button."
        if(self._curveConfig.getSubMode() == Curve.Curve):
            text = "Shows the curve\n"
            text += "\n"
            text += "Add points by doubble clicking.\n"
            text += "Select and drag points with left button."
        if(self._curveConfig.getSubMode() == Curve.Array):
            text = "Shows the curve\n"
            text += "\n"
            text += "Set point(s) with left button."
        else:
            text = "Shows the curve."
        dlg = wx.MessageDialog(self._mainCurveGuiPlane, text, 'Curve display help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def getSubId(self):
        if(self._curveConfig.getMode() == Curve.Off):
            return -1
        if(self._curveConfig.getMode() == Curve.All):
            return -1
        channelString = self._curveChannelField.GetValue()
        if((channelString == "Red") or (channelString == "Hue")):
            return 0
        if((channelString == "Green") or (channelString == "Saturation")):
            return 1
        if((channelString == "Blue") or (channelString == "Value")):
            return 2

    def _onCurveSingleClick(self, event):
        self._curveConfig.drawingDone()
        self._updateCurveGraph()

    def _onCurveDoubleClick(self, event):
        self._curveConfig.addPoint(self._curveGraphicsDisplay.getLastPos(), self.getSubId())
        self._updateCurveGraph()

    def _onMouseMove(self, event):
        if(event.mousePressed == True):
            self._curveConfig.drawPoint(event.mousePosition, self.getSubId())
            self._updateCurveGraph()
        else:
            self._curveConfig.drawingDone()

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
        updateChoices(self._curveModeField, self._curveConfig.getChoices, self._curveConfig.getChoices()[self._curveConfig.getMode()], "Off")
        updateChoices(self._curveSubModeField, self._curveConfig.getSubChoices, self._curveConfig.getSubChoices()[self._curveConfig.getSubMode()], "Linear")
        self._onCurveChannelChosen(None)
        self._updateCurveGraph()
        self._checkForUpdates()

