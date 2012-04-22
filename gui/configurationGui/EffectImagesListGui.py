'''
Created on 20. apr. 2012

@author: pcn
'''

import wx
from wx.lib.agw import ultimatelistctrl #@UnresolvedImport
import sys
import os

class EffectImagesListGui(object):
    def __init__(self, mainConfig, effectImagesConfig):
        self._mainConfig = mainConfig
        self._videoDirectory = self._mainConfig.getGuiVideoDir()
        self._effectImagesConfig = effectImagesConfig
        self._effectImageListSelectedIndex = -1

    def setupEffectImageListGui(self, plane, sizer, parentSizer, parentClass):
        self._mainEffectImagesListPlane = plane
        self._mainEffectImagesListGuiSizer = sizer
        self._parentSizer = parentSizer
        self._hideEffectImagesListCallback = parentClass.hideEffectImageListGui

        self._effectImageList = wx.ImageList(25, 16) #@UndefinedVariable
        self._imageBitmap = wx.Bitmap("graphics/modeImage.png") #@UndefinedVariable
        self._effectImageIndex = self._effectImageList.Add(self._imageBitmap)

        self._effectImageListWidget = ultimatelistctrl.UltimateListCtrl(self._mainEffectImagesListPlane, id=wx.ID_ANY, size=(240,376), agwStyle = wx.LC_REPORT | wx.LC_HRULES | wx.LC_SINGLE_SEL) #@UndefinedVariable
        self._effectImageListWidget.SetImageList(self._effectImageList, wx.IMAGE_LIST_SMALL) #@UndefinedVariable
        self._effectImageListWidget.SetBackgroundColour((170,170,170))

        self._effectImageListWidget.InsertColumn(0, 'Filename', width=230)

        self._mainEffectImagesListGuiSizer.Add(self._effectImageListWidget, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._mainEffectImagesListPlane.Bind(ultimatelistctrl.EVT_LIST_ITEM_SELECTED, self._onListItemSelected, self._effectImageListWidget)
        self._mainEffectImagesListPlane.Bind(ultimatelistctrl.EVT_LIST_ITEM_DESELECTED, self._onListItemDeselected, self._effectImageListWidget)
        self._effectImageListWidget.Bind(wx.EVT_LEFT_DCLICK, self._onListDoubbleClick) #@UndefinedVariable

        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = wx.Button(self._mainEffectImagesListPlane, wx.ID_ANY, 'Close') #@UndefinedVariable
        closeButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainEffectImagesListPlane.Bind(wx.EVT_BUTTON, self._onListCloseButton, id=closeButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 1, wx.ALL, 5) #@UndefinedVariable
        newButton = wx.Button(self._mainEffectImagesListPlane, wx.ID_ANY, 'New') #@UndefinedVariable
        newButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainEffectImagesListPlane.Bind(wx.EVT_BUTTON, self._onListNewButton, id=newButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(newButton, 1, wx.ALL, 5) #@UndefinedVariable
        deleteButton = wx.Button(self._mainEffectImagesListPlane, wx.ID_ANY, 'Delete') #@UndefinedVariable
        deleteButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._mainEffectImagesListPlane.Bind(wx.EVT_BUTTON, self._onListDeleteButton, id=deleteButton.GetId()) #@UndefinedVariable
        self._buttonsSizer.Add(deleteButton, 1, wx.ALL, 5) #@UndefinedVariable
        self._mainEffectImagesListGuiSizer.Add(self._buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

    def updateEffectImageList(self):
        self._effectImageListWidget.DeleteAllItems()
        for effectConfig in self._effectImagesConfig.getList():
            bitmapId = self._effectImageIndex
            fileName = effectConfig.getFileName()
            baseName = os.path.basename(fileName)
            index = self._effectImageListWidget.InsertImageStringItem(sys.maxint, baseName, bitmapId)

            if(index % 2):
                self._effectImageListWidget.SetItemBackgroundColour(index, wx.Colour(170,170,170)) #@UndefinedVariable
            else:
                self._effectImageListWidget.SetItemBackgroundColour(index, wx.Colour(190,190,190)) #@UndefinedVariable

    def _onListCloseButton(self, event):
        self._hideEffectImagesListCallback()

    def _onListNewButton(self, event):
        dlg = wx.FileDialog(self._mainEffectImagesListPlane, "Choose a file", os.getcwd(), "", "*.*", wx.OPEN) #@UndefinedVariable
        if dlg.ShowModal() == wx.ID_OK: #@UndefinedVariable
            fileName = os.path.relpath(dlg.GetPath(), self._videoDirectory)
            oldImage = self._mainConfig.getEffectImage(fileName)
            if(oldImage == None):
                self._mainConfig.makeNewEffectImage(fileName)
                self.updateEffectImageList()
            else:
                print "Warning: We already got this image! Ignoring."
        dlg.Destroy()

    def _onListDeleteButton(self, event):
        if(self._effectImageListSelectedIndex >= 0):
            effectImage = self._mainConfig.getEffectImageByIndex(self._effectImageListSelectedIndex)
            if(effectImage != None):
                effectImageFileName = effectImage.getFileName()
                text = "Are you sure you want to delete \"%s\"?" % (effectImageFileName)
                dlg = wx.MessageDialog(self._mainEffectImagesListPlane, text, 'Delete?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                dlg.Destroy()
                if(result == True):
                    self._mainConfig.deleteEffectImage(effectImageFileName)
                    self.updateEffectImageList()

    def _onListItemSelected(self, event):
        self._effectImageListSelectedIndex = event.m_itemIndex

    def _onListItemDeselected(self, event):
        self._effectImageListSelectedIndex = -1

    def _onListDoubbleClick(self, event):
        effectImage = self._mainConfig.getEffectImageByIndex(self._effectImageListSelectedIndex)
        if(effectImage != None):
            print "Show image editor!!!" * 10
#            self.updateGui(effectImage, None, self._activeEffectId)
#            self._showEffectsCallback()

