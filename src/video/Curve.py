'''
Created on 5. jan. 2013

@author: pcn
'''

import math
import numpy

import warnings
warnings.simplefilter('ignore', numpy.RankWarning)

class Curve(object):
    Off, All, Threshold, RGB, HSV = range(5)
    Linear, Thresh, Curve, Array = range(4)

    def getChoices(self):
        return ["Off", "All", "Threshold", "RGB", "HSV"]
    def getSubChoices(self):
        return ["Linear", "Curve", "Array"]

    def __init__(self):
        self._curves = []
        self._curves.append(CurveChannel())
        self._curves.append(CurveChannel())
        self._curves.append(CurveChannel())
        self._mode = Curve.Off
        self._currentCurveString = "Off"
        self._thresholdsSettingsList = []

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
        if(self._mode == Curve.Threshold):
            if(modeString.lower() != "threshold"):
                self.setString("Off")
        if(modeString.lower() == "all"):
            self._mode = Curve.All
        elif(modeString.lower() == "threshold"):
            if(self._mode != Curve.Threshold):
                self.setString("Threshold;000000|ffffff")
            self._mode = Curve.Threshold
        elif(modeString.lower() == "rgb"):
            self._mode = Curve.RGB
        elif(modeString.lower() == "hsv"):
            self._mode = Curve.HSV
        else:
            if(self._mode != Curve.Off):
                self.setString("Off")
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

    def getThresholdsSettings(self):
        if(self._mode == Curve.Threshold):
            return self._thresholdsSettingsList
        return None

    def updateFromThresholdsSettings(self):
        configString = self._generateThresholdConfigString()
        self.setString(configString)

    def movePoint(self, oldPoint, newPoint, subId = -1):
        if(self._mode == Curve.Off):
            pass
        elif(self._mode == Curve.Threshold):
            pass
        elif(self._mode == Curve.All):
            self._curves[0].movePoint(oldPoint, newPoint)
            self._curves[1].movePoint(oldPoint, newPoint)
            self._curves[2].movePoint(oldPoint, newPoint)
        else:
            if((subId >= 0) and (subId < 3)):
                self._curves[subId].movePoint(oldPoint, newPoint)

    def drawingDone(self, subId):
        self._curves[0].drawingDone(subId == 0)
        self._curves[1].drawingDone(subId == 1)
        self._curves[2].drawingDone(subId == 2)

    def addPoint(self, newPoint, subId = -1):
        if(self._mode == Curve.Off):
            pass
        elif(self._mode == Curve.Threshold):
            settingsLen = len(self._thresholdsSettingsList)
            for i in range(settingsLen):
                setting = self._thresholdsSettingsList[i]
                if(setting[1] == newPoint[0]):
                    return i
                elif(setting[1] > newPoint[0]):
                    if((i-1) >= 0):
                        newRed = (((setting[0] & 0xff0000) + (self._thresholdsSettingsList[i-1][0] & 0xff0000)) / 2) & 0xff0000
                        newGreen = (((setting[0] & 0x00ff00) + (self._thresholdsSettingsList[i-1][0] & 0x00ff00)) / 2) & 0x00ff00
                        newBlue = ((setting[0] & 0x0000ff) + (self._thresholdsSettingsList[i-1][0] & 0x0000ff)) / 2
                        newValue = newRed + newGreen + newBlue
                    else:
                        newValue = setting[0]
                    self._thresholdsSettingsList.insert(i, (newValue, newPoint[0]))
                    return i
            self._thresholdsSettingsList.append((0xffffff, newPoint[0]))
            return settingsLen
        elif(self._mode == Curve.All):
            self._curves[0].addPoint(newPoint)
            self._curves[1].addPoint(newPoint)
            self._curves[2].addPoint(newPoint)
        else:
            if((subId >= 0) and (subId < 3)):
                self._curves[subId].addPoint(newPoint)

    def getActivePointId(self, subId = -1):
        if(self._mode == Curve.Off):
            return None
        elif(self._mode == Curve.Threshold):
            return None
        elif(self._mode == Curve.All):
            return self._curves[0].getActivePointId()
        else:
            if((subId >= 0) and (subId < 3)):
                return self._curves[subId].getActivePointId()

    def findActivePointId(self, subId, point):
        if(self._mode == Curve.Off):
            return None
        elif(self._mode == Curve.Threshold):
            return None
        elif(self._mode == Curve.All):
            return self._curves[0].findActivePointId(point)
        else:
            if((subId >= 0) and (subId < 3)):
                return self._curves[subId].findActivePointId(point)

    def drawPoint(self, point, subId = -1):
        if(self._mode == Curve.Off):
            pass
        elif(self._mode == Curve.Threshold):
            pass
        elif(self._mode == Curve.All):
            self._curves[0].drawPoint(point)
            self._curves[1].drawPoint(point)
            self._curves[2].drawPoint(point)
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

    def _updateThersholdListPos(self, updateList, pos, addListPos):
        lastPos = 0
        lastListPos = 0
        for i in range(len(updateList)):
            valPos = updateList[i]
            if(i == 0):
                if(updateList[i][1] == None):
#                    print "DEBUG pcn: _updateThersholdListPos None: " + str((updateList[i][0], 0))
                    updateList[i] = (updateList[i][0], 0)
            else:
                if(valPos[1] == None):
                    posDiff = pos - lastPos
                    newPos = lastPos + (posDiff / max((1 + addListPos - lastListPos), 2))
#                    print "DEBUG pcn: _updateThersholdListPos: " + str((updateList[i][0], newPos)) + "  " + str((pos, lastPos, posDiff, addListPos, lastListPos, (posDiff / max((1 + addListPos - lastListPos), 2))))
                    updateList[i] = (updateList[i][0], newPos)
            lastPos = updateList[i][1]
            lastListPos += 1
                    

    def _thresholdString2curveString(self, string):
        coloursSplit = string.split('|')
        settingsList = []
        addPos = None
        addColour = None
        addListPos = 0
        for part in coloursSplit:
            if(len(part) == 6):
                addColour = int(part,16)
            elif(len(part) == 7):
                addColour = int(part[1:],16)
            else:
                addPos = int(part)
            if(addColour != None):
                settingsList.append((addColour, addPos))
                if(addPos != None):
                    self._updateThersholdListPos(settingsList, addPos, addListPos)
                addPos = None
                addColour = None
                addListPos += 1
#        print "DEBUG pcn: preFix: " + str(settingsList)
        self._updateThersholdListPos(settingsList, 255, len(settingsList))
        if(len(settingsList) < 1):
            return "Linear|0,0|255,255", "Linear|0,0|255,255", "Linear|0,0|255,255"
        elif(len(settingsList) == 1):
            if(settingsList[0][1] <= 0):
                if((addPos == None) or (addPos > 0)):
                    settingsList[0] = (settingsList[0][0], 127)
                else:
                    settingsList[0] = (settingsList[0][0], addPos)
                settingsList.insert(0, (0x000000, 0))
        else:
            if(settingsList[0][1] > 0):
                settingsList.insert(0, (settingsList[0][0], 0))
        settingsListLen = len(settingsList)
        if(settingsList[settingsListLen-1][1] < 255):
            settingsList.append((settingsList[settingsListLen-1][0], 255))
#        print "DEBUG pcn: postFix: " + str(settingsList)
        curve1 = "Thresh"
        curve2 = "Thresh"
        curve3 = "Thresh"
        lastValue1 = None
        lastValue2 = None
        lastValue3 = None
        configLastValue = None
        self._thresholdsSettingsList = []
        for setting in settingsList:
            if(setting[1] == 0):
                self._thresholdsSettingsList.append(setting)
            elif((setting[1] == 255) and (configLastValue == setting[0])):
                pass
            else:
                self._thresholdsSettingsList.append(setting)
            configLastValue = setting[0]
            value1 = (setting[0]&0xff0000) / 0x010000
            value2 = (setting[0]&0x00ff00) / 0x000100
            value3 = (setting[0]&0x0000ff)
            if(lastValue1 == None):
                curve1 += "|" + str(setting[1]) + ","+ str(value1)
            elif(lastValue1 != value1):
                curve1 += "|" + str(setting[1]-1) + ","+ str(lastValue1)
                curve1 += "|" + str(setting[1]) + ","+ str(value1)
            lastValue1 = value1
            if(lastValue2 == None):
                curve2 += "|" + str(setting[1]) + ","+ str(value2)
            elif(lastValue2 != value2):
                curve2 += "|" + str(setting[1]-1) + ","+ str(lastValue2)
                curve2 += "|" + str(setting[1]) + ","+ str(value2)
            lastValue2 = value2
            if(lastValue3 == None):
                curve3 += "|" + str(setting[1]) + ","+ str(value3)
            elif(lastValue3 != value3):
                curve3 += "|" + str(setting[1]-1) + ","+ str(lastValue3)
                curve3 += "|" + str(setting[1]) + ","+ str(value3)
            lastValue3 = value3
        self._currentCurveString = self._generateThresholdConfigString()
        return curve1, curve2, curve3

    def _generateThresholdConfigString(self):
        configString = ""
        for setting in self._thresholdsSettingsList:
            if(setting[1] == 0):
                if(configString != ""):
                    configString += "|"
                configString += "%06x" %(setting[0])
            else:
                if(configString != ""):
                    configString += "|"
                configString += "%d|%06x" %(setting[1], setting[0])
        return "Threshold;" + configString

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
                self._curves[1].setString(curvesSplit[1])
                self._curves[2].setString(curvesSplit[1])
            if(curvesSplit[0] == "Threshold"):
                self._mode = Curve.Threshold
                curve1, curve2, curve3 = self._thresholdString2curveString(curvesSplit[1])
                self._curves[0].setString(curve1)
                self._curves[1].setString(curve2)
                self._curves[2].setString(curve3)
#                arr0, arr1, arr2 = self.getArray()
#                print "R: " + str((arr0[0],arr0[1],arr0[126],arr0[127],arr0[254],arr0[255])),
#                print " G: " + str((arr1[0],arr1[1],arr1[126],arr1[127],arr1[254],arr1[255])),
#                print " B: " + str((arr2[0],arr2[1],arr2[126],arr2[127],arr2[254],arr2[255]))
            else:
                if(curvesSplit[0] == "RGB"):
                    self._mode = Curve.RGB
                if(curvesSplit[0] == "HSV"):
                    self._mode = Curve.HSV
                self._curves[0].setString(curvesSplit[1])
                if(len(curvesSplit) > 2):
                    self._curves[1].setString(curvesSplit[2])
                    if(len(curvesSplit) > 3):
                        self._curves[2].setString(curvesSplit[3])
                    else:
                        self._curves[2].setString(curvesSplit[2])
                else:
                    self._curves[1].setString(curvesSplit[1])
                    self._curves[2].setString(curvesSplit[1])
        self._currentCurveString = self.getString()

    def getString(self):
        if(self._mode == Curve.Off):
            return "Off"
        elif(self._mode == Curve.All):
            returnString = "All;"
            returnString += self._curves[0].getString()
            return returnString
        elif(self._mode == Curve.Threshold):
            return self._currentCurveString
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
        self._movePoint = None
        self._movePointId = None
        self._lastPoint = None

    def getValue(self, xPos):
        if((self._mode == Curve.Linear) or (self._mode == Curve.Thresh)):
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
        elif(modeString.lower() == "thresh"):
            self.changeMode(Curve.Thresh)
        else:
            self.changeMode(Curve.Linear)

    def changeMode(self, newMode):
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
                if(abs(point[0] - xPos) < 10):
                    if(abs(point[1] - yPos) < 10):
                        closePoints.append(point)
            if(len(closePoints) > 1):
                leastDistance = 100
                returnPoint = None
                for point in closePoints:
                    pointDistance = math.sqrt(float(math.pow(xPos-point[0], 2) + math.pow(yPos-point[1], 2)))
                    if(pointDistance < leastDistance):
                        leastDistance = pointDistance
                        returnPoint = point
                self._movePointId = self._points.index(returnPoint)
                return returnPoint
            elif(len(closePoints) == 1):
                self._movePointId = self._points.index(closePoints[0])
                return closePoints[0]
        self._movePointId = None
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

    def drawingDone(self, dontClearId):
        self._movePoint = None
        if(dontClearId == False):
            self._movePointId = None
        self._lastPoint = None

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
            self._findNearestPoint(newPoint[0], newPoint[1])

    def getActivePointId(self):
        return self._movePointId

    def findActivePointId(self, point):
        self._findNearestPoint(point[0], point[1])

    def drawPoint(self, point):
        if((self._mode == Curve.Linear) or (self._mode == Curve.Curve)):
            if(self._movePoint == None):
                self._movePoint = self._findNearestPoint(point[0], point[1])
            if(self._movePoint != None):
                self.movePoint(self._movePoint, point)
                self._movePoint = point
        if(self._mode == Curve.Array):
            i = min(max(int(point[0]), 0), 255)
            if(self._lastPoint != None):
                xJump = self._lastPoint[0]-i
                if(abs(xJump) > 1):
                    yDiff = self._lastPoint[1] - point[1]
                    for j in range(abs(xJump)):
                        if(xJump < 0):
                            self._points[i-j] = point[1] + int(yDiff * (float(j) / abs(xJump)))
                        else:
                            self._points[i+j] = point[1] + int(yDiff * (float(j) / abs(xJump)))
            self._points[i] = point[1]
            self._lastPoint = (i, point[1])

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
            if(bigSplit[0] == "Thresh"):
                self._mode = Curve.Thresh
            if(bigSplit[0] == "Curve"):
                self._mode = Curve.Curve
            if((bigSplit[0] == "Linear") or (bigSplit[0] == "Thresh") or (bigSplit[0] == "Curve")):
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
                if(bigSplit[0] == "Curve"):
                    self._calculateCoefficients()
                return
            elif(bigSplit[0] == "Array"):
                self._mode = Curve.Array
                newArray = []
                lastValue = 0
                arrayString = bigSplit[1].split(',')
                for valString in arrayString:
                    try:
                        newValue = int(valString)
                    except:
                        newValue = lastValue
                    newArray.append(newValue)
                    lastValue = newValue
                while(len(newArray) < 256):
                    newArray.append(lastValue)
                self._points = newArray
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

