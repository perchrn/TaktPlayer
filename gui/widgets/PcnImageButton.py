'''
Created on 26. jan. 2012

@author: pcn
'''
import wx

class PcnKeyboardButton(wx.PyControl): #@UndefinedVariable
    def __init__(self, parent, bitmap, pos, bid = -1, size=(-1,-1), isBlack=False):
        super(PcnKeyboardButton, self).__init__(parent, bid, style=wx.BORDER_NONE, pos=pos, size=size) #@UndefinedVariable
        self._clicked = False
        self._isBlack = isBlack
        self._baseBitmap = bitmap
        self._normal = self._baseBitmap
        self._pressed = self._baseBitmap
        self._buttonParent = parent
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM) #@UndefinedVariable
        self.Bind(wx.EVT_SIZE, self.on_size) #@UndefinedVariable
        self.Bind(wx.EVT_PAINT, self.on_paint) #@UndefinedVariable
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down) #@UndefinedVariable
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_left_dclick) #@UndefinedVariable
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up) #@UndefinedVariable
#        self.Bind(wx.EVT_MOTION, self.on_motion) #@UndefinedVariable
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave_window) #@UndefinedVariable

    def addButtonFrame(self, bitmap, isPressed):
        oldX, oldY = self._baseBitmap.GetSize()
        
        framedBitmap = wx.EmptyBitmap(oldX, oldY) #@UndefinedVariable
        dc = wx.MemoryDC() #@UndefinedVariable
        dc.SelectObject(framedBitmap)
        dc.DrawBitmap(self._baseBitmap, 0, 0, True)
        if(self._isBlack == True):
            extraY = 2
        else:
            extraY = 0
        dc.DrawBitmap(bitmap, 2, 1 + extraY, True)
        if((self._isBlack == False) and (isPressed != True)):
            dc.SetPen(wx.Pen((255,255,255), 1)) #@UndefinedVariable
        elif((self._isBlack == True) and (isPressed == True)):
            dc.SetPen(wx.Pen((255,255,255), 1)) #@UndefinedVariable
        else:
            dc.SetPen(wx.Pen((0,0,0), 1)) #@UndefinedVariable
        dc.DrawLine(4, oldY-2, oldX-4, oldY-2)
        dc.DrawLine(oldX-2, extraY, oldX-2, oldY-4)
        dc.DrawLine(2, extraY, oldX-2, extraY)
        dc.DrawLine(1, extraY, 1, oldY-4)
        dc.SelectObject(wx.NullBitmap) #@UndefinedVariable
        return framedBitmap

    def setBitmap(self, bitmap):
        self._bitmap = bitmap
        self._normal = self.addButtonFrame(bitmap, False)
        self._pressed = self.addButtonFrame(bitmap, True)
#        self._buttonParent.Refresh()
        self.Refresh()

    def setBitmapFile(self, fileName):
        try:
            newBitmap = wx.Bitmap(fileName) #@UndefinedVariable
            self.setBitmap(newBitmap)
        except:
            print "Bitmap setting failed... %s" % fileName

    def getBitmapSize(self):
        return self._bitmap.GetSize()

    def DoGetBestSize(self):
        return self._normal.GetSize()
    def Enable(self, *args, **kwargs):
        super(PcnKeyboardButton, self).Enable(*args, **kwargs)
        self.Refresh()
    def Disable(self, *args, **kwargs):
        super(PcnKeyboardButton, self).Disable(*args, **kwargs)
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
        if(self._clicked):
            dc.DrawBitmap(self._pressed, 0, 0)
        else:
            dc.DrawBitmap(self._normal, 0, 0)
    def set_clicked(self, clicked):
        if clicked != self._clicked:
            self._clicked = clicked
            self.Refresh()
    def get_clicked(self):
        return self._clicked
    clicked = property(get_clicked, set_clicked)
    def on_left_down(self, event):
        self.clicked = True
    def on_left_dclick(self, event):
        self.on_left_down(event)
    def on_left_up(self, event):
        if self.clicked:
            self.post_event()
        self.clicked = False
#    def on_motion(self, event):
#        if self.clicked:
#            self.clicked = False
    def on_leave_window(self, event):
        self.clicked = False
