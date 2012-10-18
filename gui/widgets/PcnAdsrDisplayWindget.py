'''
Created on 26. jan. 2012

@author: pcn
'''
import wx


class PcnAdsrDisplayWidget(wx.PyControl): #@UndefinedVariable
    def __init__(self, parent, bitmap, pos=(-1,-1), bid = -1, size=(-1,-1), isBlack=False):
        super(PcnAdsrDisplayWidget, self).__init__(parent, bid, style=wx.BORDER_NONE, pos=pos, size=size) #@UndefinedVariable
        self._baseBitmap = bitmap
        self._activeBitmap = bitmap
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM) #@UndefinedVariable
        self.Bind(wx.EVT_SIZE, self.on_size) #@UndefinedVariable
        self.Bind(wx.EVT_PAINT, self.on_paint) #@UndefinedVariable

    def drawAdsr(self, adsr):
        baseX, baseY = self._baseBitmap.GetSize()
        adsrMax = baseY - 3

        attackLength = adsr.getAttackLength()
        decayLength = adsr.getDecayLength()
        holdLength = adsr.calculateHoldLength(1.0)
        releaseLength = adsr.getReleaseLength()
        endLength = adsr.calculateHoldLength(1.0)
        adsrLength = attackLength + decayLength + holdLength + releaseLength + endLength
        adsrStep = float(adsrLength) / baseX
        attackPos = int(float(attackLength) / adsrStep)
        decayPos = int(float(attackLength + decayLength) / adsrStep)
        sustainPos = int(float(attackLength + decayLength + holdLength) / adsrStep)
        releasePos = int(float(attackLength + decayLength + holdLength + releaseLength) / adsrStep)
        adsrNoteOnLength = float(attackLength + decayLength + holdLength)
        noteOffPos = int(float(adsrNoteOnLength) / adsrStep)
        
        workBitmap = wx.EmptyBitmap(baseX, baseX) #@UndefinedVariable
        dc = wx.MemoryDC() #@UndefinedVariable
        dc.SelectObject(workBitmap)
        dc.SetBrush(wx.Brush('#AAAAAA')) #@UndefinedVariable
        dc.SetPen(wx.Pen((0,0,0), 1)) #@UndefinedVariable
        dc.DrawRectangle(0, 0, baseX, baseY)
        lastYpos = None
        for xpos in range(baseX):
            if(xpos < noteOffPos):
                offSPP = 0.0
                noteLength = 0.0
            else:
                offSPP = adsrNoteOnLength
                noteLength = adsrNoteOnLength
            ypos = 1 + int(adsr.getValue(xpos*adsrStep, (0.0, offSPP, noteLength)) * adsrMax)
            if(lastYpos == None):
                dc.DrawPoint(xpos, ypos)
            else:
                if(abs(lastYpos - ypos) < 2):
                    dc.DrawPoint(xpos, ypos)
                else:
                    dc.DrawLine(xpos, lastYpos, xpos, ypos)
            lastYpos = ypos
            if(xpos in [attackPos, decayPos, sustainPos, releasePos]):
                dc.DrawLine(xpos, 1, xpos, adsrMax)
        dc.SelectObject(wx.NullBitmap) #@UndefinedVariable
        self._activeBitmap = workBitmap
        self.Refresh()

    def getBitmapSize(self):
        return self._baseBitmap.GetSize()

    def DoGetBestSize(self):
        return self._baseBitmap.GetSize()

    def Enable(self, *args, **kwargs):
        super(PcnAdsrDisplayWidget, self).Enable(*args, **kwargs)
        self.Refresh()
    def Disable(self, *args, **kwargs):
        super(PcnAdsrDisplayWidget, self).Disable(*args, **kwargs)
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
