'''
Created on 26. jan. 2012

@author: pcn
'''
import wx
from widgets.PcnEvents import EVT_DOUBLE_CLICK_EVENT, MouseMoveEvent

class PcnCurveDisplayWidget(wx.PyControl): #@UndefinedVariable
    def __init__(self, parent, pos=(-1,-1), bid = -1, size=(-1,-1), isBig=False):
        if(isBig == True):
            self._drawSize = 512
            emptyCurveBitMap = wx.EmptyBitmap (514, 514, depth=3) #@UndefinedVariable
        else:
            self._drawSize = 256
            emptyCurveBitMap = wx.EmptyBitmap (258, 258, depth=3) #@UndefinedVariable
        super(PcnCurveDisplayWidget, self).__init__(parent, bid, style=wx.BORDER_NONE, pos=pos, size=size) #@UndefinedVariable
        self._baseBitmap = emptyCurveBitMap
        self._activeBitmap = emptyCurveBitMap
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM) #@UndefinedVariable
        self.Bind(wx.EVT_SIZE, self.on_size) #@UndefinedVariable
        self.Bind(wx.EVT_PAINT, self.on_paint) #@UndefinedVariable

        self._clicked = False
        self._buttonParent = parent
        self._doubleClickEnabled = True
        self._doubleClicked = False
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down) #@UndefinedVariable
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_left_dclick) #@UndefinedVariable
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up) #@UndefinedVariable
        self.Bind(wx.EVT_MOTION, self.on_motion) #@UndefinedVariable
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave_window) #@UndefinedVariable

        self._singleClickTimer = wx.Timer(self, -1) #@UndefinedVariable
        self._lastPos = (-1,-1)
        self._lastStartPos = (-1,-1)

    def setPenColour(self, dc, red, green, blue, width):
        if(red == True):
            if(green == True):
                if(blue == True):
                    dc.SetPen(wx.Pen((0,0,0), width)) #@UndefinedVariable
                else:
                    dc.SetPen(wx.Pen((120,60,0), width)) #@UndefinedVariable
            else:
                dc.SetPen(wx.Pen((200,0,0), width)) #@UndefinedVariable
        else:
            if(green == True):
                if(blue == True):
                    dc.SetPen(wx.Pen((0,90,90), width)) #@UndefinedVariable
                else:
                    dc.SetPen(wx.Pen((0,180,0), width)) #@UndefinedVariable
            else:
                dc.SetPen(wx.Pen((0,0,200), width)) #@UndefinedVariable

    def drawCurve(self, curve):
        baseX, baseY = self._baseBitmap.GetSize()

        """ Clear """
        workBitmap = wx.EmptyBitmap(baseX, baseX) #@UndefinedVariable
        dc = wx.MemoryDC() #@UndefinedVariable
        dc.SelectObject(workBitmap)
        dc.SetBrush(wx.Brush('#AAAAAA')) #@UndefinedVariable
        dc.SetPen(wx.Pen((0,0,0), 1)) #@UndefinedVariable
        dc.DrawRectangle(0, 0, baseX, baseY)

        drawFactor = float(self._drawSize) / 256

        """ Points """
        pointListList = curve.getPoints()
        if(len(pointListList) < 2):
            dc.SetPen(wx.Pen((0,0,255), 2)) #@UndefinedVariable
            for point in pointListList[0]:
                yPos = int(drawFactor * self._drawSize - (int(point[1]))) + 1
                dc.DrawCircle(int(point[0] * drawFactor) + 1, yPos, 4)
        else:
            ch0Len = len(pointListList[0])
            ch1Len = len(pointListList[1])
            ch2Len = len(pointListList[2])
            if(ch0Len > 0):
                ch0i = 0
            else:
                ch0i = -1
            if(ch1Len > 0):
                ch1i = 0
            else:
                ch1i = -1
            if(ch2Len > 0):
                ch2i = 0
            else:
                ch2i = -1
            stop = False
            while(stop == False):
                drawPoint = (300,300)
                if(ch0i >= 0):
                    if(pointListList[0][ch0i][0] <= drawPoint[0]):
                        if(pointListList[0][ch0i][1] <= drawPoint[1]):
                            drawPoint = (pointListList[0][ch0i][0], pointListList[0][ch0i][1])
                if(ch1i >= 0):
                    if(pointListList[0][ch1i][0] <= drawPoint[0]):
                        if(pointListList[1][ch1i][1] <= drawPoint[1]):
                            drawPoint = (pointListList[1][ch1i][0], pointListList[1][ch1i][1])
                if(ch2i >= 0):
                    if(pointListList[2][ch2i][0] <= drawPoint[0]):
                        if(pointListList[2][ch2i][1] <= drawPoint[1]):
                            drawPoint = (pointListList[2][ch2i][0], pointListList[2][ch2i][1])
                draw0 = False
                draw1 = False
                draw2 = False
                if(ch0i >= 0):
                    if(pointListList[0][ch0i][0] == drawPoint[0]):
                        if(pointListList[0][ch0i][1] == drawPoint[1]):
                            draw0 = True
                            ch0i += 1
                            if(ch0i >= ch0Len):
                                ch0i = -1
                if(ch1i >= 0):
                    if(pointListList[1][ch1i][0] == drawPoint[0]):
                        if(pointListList[1][ch1i][1] == drawPoint[1]):
                            draw1 = True
                            ch1i += 1
                            if(ch1i >= ch1Len):
                                ch1i = -1
                if(ch2i >= 0):
                    if(pointListList[2][ch2i][0] == drawPoint[0]):
                        if(pointListList[2][ch2i][1] == drawPoint[1]):
                            draw2 = True
                            ch2i += 1
                            if(ch2i >= ch2Len):
                                ch2i = -1
                if((ch0i < 0) and (ch1i < 0) and (ch2i < 0)):
                    stop = True
                self.setPenColour(dc, draw0, draw1, draw2, 2)
                yPos = int(drawFactor * self._drawSize - (int(drawPoint[1]))) + 1
                dc.DrawCircle(int(drawPoint[0] * drawFactor) + 1, yPos, 4)


        """ Curve """
        lastY0Pos = None
        lastY1Pos = None
        lastY2Pos = None
        lastY0Val = None
        lastY1Val = None
        lastY2Val = None
        for xPos in range(self._drawSize):
            yValueList = curve.getValue(float(xPos*256)/self._drawSize)
            if(len(yValueList) < 2):
                dc.SetPen(wx.Pen((0,0,0), 1)) #@UndefinedVariable
                yPos = self._drawSize - (int(yValueList[0] * drawFactor))
                xPos = int(xPos * drawFactor)
                if(lastY0Pos == None):
                    lastY0Pos = yPos
                if(lastY0Pos == yPos):
                    lastY0Pos += 1
                dc.DrawLine(xPos + 1, lastY0Pos - 1, xPos + 1, yPos - 1)
                lastY0Pos = yPos
                lastY0Val = yValueList[0]
            else:
                yPos = self._drawSize - (int(yValueList[2] * drawFactor))
                if((yValueList[0] != yValueList[2]) or (lastY0Val != lastY2Val) or (yValueList[1] != yValueList[2]) or (lastY1Val != lastY2Val)):
                    self.setPenColour(dc, yValueList[0]==yValueList[2], yValueList[1]==yValueList[2], True, 1)
                    xPos = int(xPos * drawFactor)
                    if(lastY2Pos == None):
                        lastY2Pos = yPos
                    if(lastY2Pos == yPos):
                        lastY2Pos += 1
                    dc.DrawLine(xPos + 1, lastY2Pos - 1, xPos + 1, yPos - 1)
                lastY2Pos = yPos
                yPos = self._drawSize - (int(yValueList[1] * drawFactor))
                if((yValueList[0] != yValueList[1]) or (lastY0Val != lastY1Val)):
                    self.setPenColour(dc, yValueList[0]==yValueList[1], True, yValueList[2]==yValueList[1], 1)
                    xPos = int(xPos * drawFactor)
                    if(lastY1Pos == None):
                        lastY1Pos = yPos
                    if(lastY1Pos == yPos):
                        lastY1Pos += 1
                    dc.DrawLine(xPos + 1, lastY1Pos - 1, xPos + 1, yPos - 1)
                lastY1Pos = yPos
                self.setPenColour(dc, True, (yValueList[1]==yValueList[0]) or (lastY1Val == lastY0Val), (yValueList[2]==yValueList[0]) or (lastY2Val == lastY0Val), 1)
                yPos = self._drawSize - (int(yValueList[0] * drawFactor))
                xPos = int(xPos * drawFactor)
                if(lastY0Pos == None):
                    lastY0Pos = yPos
                if(lastY0Pos == yPos):
                    lastY0Pos += 1
                dc.DrawLine(xPos + 1, lastY0Pos - 1, xPos + 1, yPos - 1)
                lastY0Pos = yPos
                lastY0Val = yValueList[0]
                lastY1Val = yValueList[1]
                lastY2Val = yValueList[2]

        dc.SelectObject(wx.NullBitmap) #@UndefinedVariable
        self._activeBitmap = workBitmap
        self.Refresh()

    def getBitmapSize(self):
        return self._baseBitmap.GetSize()

    def DoGetBestSize(self):
        return self._baseBitmap.GetSize()

    def Enable(self, *args, **kwargs):
        super(PcnCurveDisplayWidget, self).Enable(*args, **kwargs)
        self.Refresh()
    def Disable(self, *args, **kwargs):
        super(PcnCurveDisplayWidget, self).Disable(*args, **kwargs)
        self.Refresh()
    def eventPosToCurvePos(self, pos):
        xPos = min(max(int(pos[0] - 2), 0), 255)
        yPos = min(max(int(257 - pos[1]), 0), 255)
        drawFactor = float(self._drawSize) / 256
        return (int(xPos/drawFactor), int(yPos/drawFactor))
    def getLastPos(self):
        return self._lastPos
    def getLastStartPos(self):
        return self._lastStartPos
    def post_event(self):
        event = wx.CommandEvent() #@UndefinedVariable
        event.SetEventObject(self)
        event.SetEventType(wx.EVT_BUTTON.typeId) #@UndefinedVariable
        wx.PostEvent(self, event) #@UndefinedVariable
    def set_clicked(self, clicked):
        if clicked != self._clicked:
            self._clicked = clicked
            self.Refresh()
    def get_clicked(self):
        return self._clicked
    clicked = property(get_clicked, set_clicked)
    def on_left_down(self, event):
        self._lastStartPos = self.eventPosToCurvePos(event.GetPosition())
        self.clicked = True
    def on_left_dclick(self, event):
        if(self._singleClickTimer.IsRunning() == True):
            self._singleClickTimer.Stop()
        self._doubleClicked = True
        self.on_left_down(event)
    def on_single_click(self, event):
        self._doubleClicked = False
        self.post_event()
    def on_left_up(self, event):
        self._lastPos = self.eventPosToCurvePos(event.GetPosition())
        if(self._doubleClickEnabled == False):
            if self.clicked:
                self.post_event()
        else:
            if(self._doubleClicked == True):
                doubleEvent = wx.CommandEvent() #@UndefinedVariable
                doubleEvent.SetEventObject(self)
                doubleEvent.SetEventType(EVT_DOUBLE_CLICK_EVENT.typeId) #@UndefinedVariable
                wx.PostEvent(self, doubleEvent) #@UndefinedVariable
                self._doubleClicked = False
            else:
                if self.clicked:
                    self._singleClickTimer.Start(100, oneShot=True)#1/2 sec
                    self.Bind(wx.EVT_TIMER, self.on_single_click) #@UndefinedVariable
        self.clicked = False
        self._doubleClicked = False
#        wx.PostEvent(self._buttonParent, event) #@UndefinedVariable
    def on_motion(self, event):
        pos = self.eventPosToCurvePos(event.GetPosition())
        mouseEvent = MouseMoveEvent(mousePosition=pos, mousePressed=self._clicked)
        wx.PostEvent(self, mouseEvent) #@UndefinedVariable
    def on_leave_window(self, event):
        self.clicked = False
    def on_size(self, event):
        event.Skip()
        self.Refresh()
    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self) #@UndefinedVariable
        dc.SetBackground(wx.Brush(self.GetParent().GetBackgroundColour())) #@UndefinedVariable
        dc.Clear()
        dc.DrawBitmap(self._activeBitmap, 0, 0)
