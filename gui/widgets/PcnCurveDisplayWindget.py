'''
Created on 26. jan. 2012

@author: pcn
'''
import wx
from widgets.PcnEvents import EVT_DOUBLE_CLICK_EVENT

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

    def drawCurve(self, curve):
        baseX, baseY = self._baseBitmap.GetSize()
        
        workBitmap = wx.EmptyBitmap(baseX, baseX) #@UndefinedVariable
        dc = wx.MemoryDC() #@UndefinedVariable
        dc.SelectObject(workBitmap)
        dc.SetBrush(wx.Brush('#AAAAAA')) #@UndefinedVariable
        dc.SetPen(wx.Pen((0,0,0), 1)) #@UndefinedVariable
        dc.DrawRectangle(0, 0, baseX, baseY)

        dc.SetPen(wx.Pen((0,0,0), 1)) #@UndefinedVariable
        lastYPos = None
        for xPos in range(self._drawSize):
            yValue = curve.getValue(float(xPos*256)/self._drawSize)
            yPos = self._drawSize - (int(yValue))
            if(lastYPos == None):
                lastYPos = yPos
            dc.DrawLine(xPos + 1, lastYPos, xPos + 1, yPos)
            lastYPos = yPos

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
        return (xPos, yPos)
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
        if(self.clicked == True):
            print "M",
        else:
            print "m",
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
