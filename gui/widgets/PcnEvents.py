'''
Created on Dec 30, 2012

@author: pcn
'''
import  wx.lib.newevent #@UnresolvedImport

DragStartEvent, EVT_DRAG_START_EVENT = wx.lib.newevent.NewEvent() #@UndefinedVariable
DragDoneEvent, EVT_DRAG_DONE_EVENT = wx.lib.newevent.NewEvent() #@UndefinedVariable
DoubleClickEvent, EVT_DOUBLE_CLICK_EVENT = wx.lib.newevent.NewEvent() #@UndefinedVariable
MouseMoveEvent, EVT_MOUSE_MOVE_EVENT = wx.lib.newevent.NewEvent() #@UndefinedVariable
