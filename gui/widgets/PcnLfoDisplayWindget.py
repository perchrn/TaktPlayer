'''
Created on 26. jan. 2012

@author: pcn
'''
import wx


class PcnLfoDisplayWidget(wx.PyControl): #@UndefinedVariable
    def __init__(self, parent, bitmap, pos=(-1,-1), bid = -1, size=(-1,-1), isBlack=False):
        super(PcnLfoDisplayWidget, self).__init__(parent, bid, style=wx.BORDER_NONE, pos=pos, size=size) #@UndefinedVariable
        self._baseBitmap = bitmap
        self._activeBitmap = bitmap
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM) #@UndefinedVariable
        self.Bind(wx.EVT_SIZE, self.on_size) #@UndefinedVariable
        self.Bind(wx.EVT_PAINT, self.on_paint) #@UndefinedVariable

    def drawLfo(self, lfo):
        baseX, baseY = self._baseBitmap.GetSize()
        lfoMax = baseY - 3

        lfoGraphLength = lfo.calculateLength(32.0)
        lfoStep = float(lfoGraphLength) / baseX
        
        workBitmap = wx.EmptyBitmap(baseX, baseX) #@UndefinedVariable
        dc = wx.MemoryDC() #@UndefinedVariable
        dc.SelectObject(workBitmap)
        dc.SetBrush(wx.Brush('#AAAAAA')) #@UndefinedVariable
        dc.SetPen(wx.Pen((0,0,0), 1)) #@UndefinedVariable
        dc.DrawRectangle(0, 0, baseX, baseY)

        lastYpos = None
        for xpos in range(baseX):
            ypos = 1 + int((1.0 - lfo.getValue(xpos*lfoStep, None)) * lfoMax)
            if(lastYpos == None):
                dc.DrawPoint(xpos, ypos)
            else:
                if(abs(lastYpos - ypos) < 2):
                    dc.DrawPoint(xpos, ypos)
                else:
                    dc.DrawLine(xpos, lastYpos, xpos, ypos)
            lastYpos = ypos
        dc.SelectObject(wx.NullBitmap) #@UndefinedVariable
        self._activeBitmap = workBitmap
        self.Refresh()

    def getBitmapSize(self):
        return self._baseBitmap.GetSize()

    def DoGetBestSize(self):
        return self._baseBitmap.GetSize()

    def Enable(self, *args, **kwargs):
        super(PcnLfoDisplayWidget, self).Enable(*args, **kwargs)
        self.Refresh()
    def Disable(self, *args, **kwargs):
        super(PcnLfoDisplayWidget, self).Disable(*args, **kwargs)
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
