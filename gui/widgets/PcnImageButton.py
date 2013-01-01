'''
Created on 26. jan. 2012

@author: pcn
'''
import wx #@UnusedImport
from PIL import Image
from widgets.PcnEvents import EVT_DRAG_START_EVENT, EVT_DRAG_DONE_EVENT,\
    EVT_DOUBLE_CLICK_EVENT

class PcnPopupMenu(wx.Menu): #@UndefinedVariable
    def __init__(self, parent, imageList, nameList, onChosenCallback):
        super(PcnPopupMenu, self).__init__()
        self._onChosenCallback = onChosenCallback

        self._menuIds = []
        for i in range(len(imageList)):
            image = imageList[i]
            name = nameList[i]
            
            itemId = wx.NewId() #@UndefinedVariable
            menuItem = wx.MenuItem(self, itemId, name) #@UndefinedVariable
#            print "DEBUG pcn: adding menu item: " + name + " id: " + str(itemId)
            menuItem.SetBitmap(image) #@UndefinedVariable
            menuItem.SetBackgroundColour((190,190,190))
            self.AppendItem(menuItem)
            self._menuIds.append(menuItem.GetId())
            self.Bind(wx.EVT_MENU, self._onChoice, menuItem) #@UndefinedVariable

    def getIdList(self):
        return self._menuIds

    def _onChoice(self, event):
        menuId = event.GetId()
        foundMenuIndex = None
        for i in range(len(self._menuIds)):
            if(self._menuIds[i] == menuId):
                foundMenuIndex = i
                break
        self._onChosenCallback(foundMenuIndex)


def addKeyboardButtonFrame(bitmap, isPressed, baseBitmap, isBlack):
    oldX, oldY = baseBitmap.GetSize()
    
    framedBitmap = wx.EmptyBitmap(oldX, oldY) #@UndefinedVariable
    dc = wx.MemoryDC() #@UndefinedVariable
    dc.SelectObject(framedBitmap)
    dc.DrawBitmap(baseBitmap, 0, 0, True)
    if(isBlack == True):
        extraY = 2
    else:
        extraY = 0
    dc.DrawBitmap(bitmap, 2, 1 + extraY, True)
    if((isBlack == False) and (isPressed != True)):
        dc.SetPen(wx.Pen((255,255,255), 1)) #@UndefinedVariable
    elif((isBlack == True) and (isPressed == True)):
        dc.SetPen(wx.Pen((255,255,255), 1)) #@UndefinedVariable
    else:
        dc.SetPen(wx.Pen((0,0,0), 1)) #@UndefinedVariable
    dc.DrawLine(4, oldY-2, oldX-4, oldY-2)
    dc.DrawLine(oldX-2, extraY, oldX-2, oldY-4)
    dc.DrawLine(2, extraY, oldX-2, extraY)
    dc.DrawLine(1, extraY, 1, oldY-4)
    dc.SelectObject(wx.NullBitmap) #@UndefinedVariable
    return framedBitmap

def addTrackButtonFrame(bitmap, isPressed, baseBitmap, isBlack):
    oldX, oldY = baseBitmap.GetSize()
    
    framedBitmap = wx.EmptyBitmap(oldX, oldY) #@UndefinedVariable
    dc = wx.MemoryDC() #@UndefinedVariable
    dc.SelectObject(framedBitmap)
    dc.DrawBitmap(baseBitmap, 0, 0, True)
    dc.DrawBitmap(bitmap, 1, 1, True)
    if(isPressed == True):
        dc.SetPen(wx.Pen((255,255,255), 1)) #@UndefinedVariable
    else:
        dc.SetPen(wx.Pen((0,0,0), 1)) #@UndefinedVariable
    dc.DrawLine(1, oldY-1, oldX-1, oldY-1)
    dc.DrawLine(oldX-1, 1, oldX-1, oldY-1)
    dc.DrawLine(0, 0, oldX-1, 0)
    dc.DrawLine(0, 1, 0, oldY-1)
    dc.SelectObject(wx.NullBitmap) #@UndefinedVariable
    return framedBitmap

class PcnKeyboardButton(wx.PyControl): #@UndefinedVariable
    def __init__(self, parent, bitmap, pos, bid = -1, size=(-1,-1), isBlack=False):
        super(PcnKeyboardButton, self).__init__(parent, bid, style=wx.BORDER_NONE, pos=pos, size=size) #@UndefinedVariable
        self._clicked = False
        self._isSelected = False
        self._isBlack = isBlack
        self._baseBitmap = bitmap
        self._normal = self._baseBitmap
        self._pressed = self._baseBitmap
        self._buttonParent = parent
        self._doubleClickEnabled = False
        self._doubleClicked = False
        self._bitmap = None
        self._frameAddingFunction = addKeyboardButtonFrame
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM) #@UndefinedVariable
        self.Bind(wx.EVT_SIZE, self.on_size) #@UndefinedVariable
        self.Bind(wx.EVT_PAINT, self.on_paint) #@UndefinedVariable
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down) #@UndefinedVariable
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_left_dclick) #@UndefinedVariable
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up) #@UndefinedVariable
#        self.Bind(wx.EVT_MOTION, self.on_motion) #@UndefinedVariable
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave_window) #@UndefinedVariable

        self._singleClickTimer = wx.Timer(self, -1) #@UndefinedVariable

    def enableDoubleClick(self):
        self._doubleClickEnabled = True

    def setFrqameAddingFunction(self, function):
        self._frameAddingFunction = function

    def addButtonFrame(self, bitmap, isPressed):
        return self._frameAddingFunction(bitmap, isPressed, self._baseBitmap, self._isBlack)

    def getBitmap(self):
        return self._bitmap

    def setBitmap(self, bitmap):
        self._bitmap = bitmap
        if(self._bitmap != None):
            self._normal = self.addButtonFrame(bitmap, False)
            self._pressed = self.addButtonFrame(bitmap, True)
            self.Refresh()

    def clearBitmap(self):
        if(self._bitmap != None):
            self._bitmap = None
            self._normal = self.addButtonFrame(self._baseBitmap, False)
            self._pressed = self.addButtonFrame(self._baseBitmap, True)
            self.Refresh()

    def clearKeyboardButton(self):
        if(self._bitmap != None):
            self._bitmap = None
            self._normal = self._baseBitmap
            self._pressed = self._baseBitmap
            self.Refresh()

    def setBitmapFile(self, fileName):
        try:
            pilImage = Image.open(fileName)
        except:
            print "Warning: Error reading %s image!" % (fileName)
            return False
        else:
            myWxImage  = wx.EmptyImage(pilImage.size[0],pilImage.size[1]) #@UndefinedVariable
            try:
                myWxImage.SetData(pilImage.convert("RGB").tostring())
            except:
                print "Warning: Error reading %s image!" % (fileName)
                return False
            else:
                bitmap = wx.BitmapFromImage(myWxImage ) #@UndefinedVariable
                self.setBitmap(bitmap)
                return True

    def getBitmapSize(self):
        return self._bitmap.GetSize()

    def setSelected(self):
        if(self._isSelected != True):
            self._isSelected = True
            self.Refresh()

    def unsetSelected(self):
        if(self._isSelected != False):
            self._isSelected = False
            self.Refresh()

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
        depressed = self._clicked
        if(self._isSelected):
            depressed = not self._clicked
        if(depressed):
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
        dragStartEvent = wx.CommandEvent() #@UndefinedVariable
        dragStartEvent.SetEventObject(self)
        dragStartEvent.SetEventType(EVT_DRAG_START_EVENT.typeId) #@UndefinedVariable
        wx.PostEvent(self, dragStartEvent) #@UndefinedVariable
    def on_left_dclick(self, event):
        if(self._singleClickTimer.IsRunning() == True):
            self._singleClickTimer.Stop()
        self._doubleClicked = True
        self.on_left_down(event)
    def on_single_click(self, event):
        self.post_event()
    def on_left_up(self, event):
        if(self._doubleClickEnabled == False):
            if self.clicked:
                self.post_event()
        else:
            if(self._doubleClicked == True):
                doubleEvent = wx.CommandEvent() #@UndefinedVariable
                doubleEvent.SetEventObject(self)
                doubleEvent.SetEventType(EVT_DOUBLE_CLICK_EVENT.typeId) #@UndefinedVariable
                wx.PostEvent(self, doubleEvent) #@UndefinedVariable
            else:
                if self.clicked:
                    self._singleClickTimer.Start(100, oneShot=True)#1/2 sec
                    self.Bind(wx.EVT_TIMER, self.on_single_click) #@UndefinedVariable
        self.clicked = False
        self._doubleClicked = False
        dragDoneEvent = wx.CommandEvent() #@UndefinedVariable
        dragDoneEvent.SetEventObject(self)
        dragDoneEvent.SetEventType(EVT_DRAG_DONE_EVENT.typeId) #@UndefinedVariable
        wx.PostEvent(self, dragDoneEvent) #@UndefinedVariable
        wx.PostEvent(self._buttonParent, event) #@UndefinedVariable
#    def on_motion(self, event):
#        if self.clicked:
#            self.clicked = False
    def on_leave_window(self, event):
        self.clicked = False

class PcnImageButton(wx.PyControl): #@UndefinedVariable
    def __init__(self, parent, bitmapNormal, bitmapPressed, pos=(-1,-1), bid = -1, size=(-1,-1)):
        super(PcnImageButton, self).__init__(parent, bid, style=wx.BORDER_NONE, pos=pos, size=size) #@UndefinedVariable
        self._clicked = False
        self._isSelected = False
        self._normal = bitmapNormal
        self._pressed = bitmapPressed
        self._buttonParent = parent
        self._doubleClickEnabled = False
        self._doubleClicked = False
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM) #@UndefinedVariable
        self.Bind(wx.EVT_SIZE, self.on_size) #@UndefinedVariable
        self.Bind(wx.EVT_PAINT, self.on_paint) #@UndefinedVariable
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down) #@UndefinedVariable
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_left_dclick) #@UndefinedVariable
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up) #@UndefinedVariable
#        self.Bind(wx.EVT_MOTION, self.on_motion) #@UndefinedVariable
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave_window) #@UndefinedVariable

        self._singleClickTimer = wx.Timer(self, -1) #@UndefinedVariable

    def enableDoubleClick(self):
        self._doubleClickEnabled = True

    def setBitmaps(self, bitmapNormal, bitmapPressed):
        self._normal = bitmapNormal
        self._pressed = bitmapPressed
        self.Refresh()

    def setSelected(self):
        if(self._isSelected != True):
            self._isSelected = True
            self.Refresh()

    def unsetSelected(self):
        if(self._isSelected != False):
            self._isSelected = False
            self.Refresh()

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
        depressed = self._clicked
        if(self._isSelected):
            depressed = not self._clicked
        if(depressed):
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
        dragStartEvent = wx.CommandEvent() #@UndefinedVariable
        dragStartEvent.SetEventObject(self)
        dragStartEvent.SetEventType(EVT_DRAG_START_EVENT.typeId) #@UndefinedVariable
        wx.PostEvent(self, dragStartEvent) #@UndefinedVariable
    def on_left_dclick(self, event):
        if(self._singleClickTimer.IsRunning() == True):
            self._singleClickTimer.Stop()
        self._doubleClicked = True
        self.on_left_down(event)
    def on_single_click(self, event):
        self.post_event()
    def on_left_up(self, event):
        if(self._doubleClickEnabled == False):
            if self.clicked:
                self.post_event()
        else:
            if(self._doubleClicked == True):
                doubleEvent = wx.CommandEvent() #@UndefinedVariable
                doubleEvent.SetEventObject(self)
                doubleEvent.SetEventType(EVT_DOUBLE_CLICK_EVENT.typeId) #@UndefinedVariable
                wx.PostEvent(self, doubleEvent) #@UndefinedVariable
            else:
                if self.clicked:
                    self._singleClickTimer.Start(100, oneShot=True)#1/2 sec
                    self.Bind(wx.EVT_TIMER, self.on_single_click) #@UndefinedVariable
        self.clicked = False
        self._doubleClicked = False
        dragDoneEvent = wx.CommandEvent() #@UndefinedVariable
        dragDoneEvent.SetEventObject(self)
        dragDoneEvent.SetEventType(EVT_DRAG_DONE_EVENT.typeId) #@UndefinedVariable
        wx.PostEvent(self, dragDoneEvent) #@UndefinedVariable
        wx.PostEvent(self._buttonParent, event) #@UndefinedVariable
#    def on_motion(self, event):
#        if self.clicked:
#            self.clicked = False
    def on_leave_window(self, event):
        self.clicked = False
