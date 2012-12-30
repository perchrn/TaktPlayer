'''
Created on 26. jan. 2012

@author: pcn
'''
import wx


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
    def post_event(self):
        event = wx.CommandEvent() #@UndefinedVariable
        event.SetEventObject(self)
        event.SetEventType(wx.EVT_BUTTON.typeId) #@UndefinedVariable
        wx.PostEvent(self, event) #@UndefinedVariable
    def on_size(self, event):
        event.Skip()
        self.Refresh()
    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self) #@UndefinedVariable
        dc.SetBackground(wx.Brush(self.GetParent().GetBackgroundColour())) #@UndefinedVariable
        dc.Clear()
        dc.DrawBitmap(self._activeBitmap, 0, 0)
