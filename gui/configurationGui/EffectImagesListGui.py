'''
Created on 20. apr. 2012

@author: pcn
'''

import wx
from wx.lib.agw import ultimatelistctrl #@UnresolvedImport
import sys
import os
from video.media.MediaFileModes import forceUnixPath
from widgets.PcnImageButton import PcnImageButton

class EffectImagesListGui(object):
    def __init__(self, mainConfig, effectImagesConfig, globalConfig):
        self._mainConfig = mainConfig
        self._globalConfig = globalConfig
        self._videoDirectory = self._mainConfig.getGuiVideoDir()
        self._lastDialogDir = self._videoDirectory
        self._effectImagesConfig = effectImagesConfig
        self._effectImageListSelectedIndex = -1

        self._closeButtonBitmap = wx.Bitmap("graphics/closeButton.png") #@UndefinedVariable
        self._closeButtonPressedBitmap = wx.Bitmap("graphics/closeButtonPressed.png") #@UndefinedVariable
        self._newButtonBitmap = wx.Bitmap("graphics/newButton.png") #@UndefinedVariable
        self._newButtonPressedBitmap = wx.Bitmap("graphics/newButtonPressed.png") #@UndefinedVariable
        self._deleteButtonBitmap = wx.Bitmap("graphics/deleteButton.png") #@UndefinedVariable
        self._deleteButtonPressedBitmap = wx.Bitmap("graphics/deleteButtonPressed.png") #@UndefinedVariable

    def setupEffectImageListGui(self, plane, sizer, parentSizer, parentClass):
        self._mainEffectImagesListPlane = plane
        self._mainEffectImagesListGuiSizer = sizer
        self._parentSizer = parentSizer
        self._hideEffectImagesListCallback = parentClass.hideEffectImageListGui

        headerLabel = wx.StaticText(self._mainEffectImagesListPlane, wx.ID_ANY, "Image list:") #@UndefinedVariable
        headerFont = headerLabel.GetFont()
        headerFont.SetWeight(wx.BOLD) #@UndefinedVariable
        headerLabel.SetFont(headerFont)
        self._mainEffectImagesListGuiSizer.Add(headerLabel, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

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
        closeButton = PcnImageButton(self._mainEffectImagesListPlane, self._closeButtonBitmap, self._closeButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(55, 17)) #@UndefinedVariable
        closeButton.Bind(wx.EVT_BUTTON, self._onListCloseButton) #@UndefinedVariable
        newButton = PcnImageButton(self._mainEffectImagesListPlane, self._newButtonBitmap, self._newButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(79, 17)) #@UndefinedVariable
        newButton.Bind(wx.EVT_BUTTON, self._onListNewButton) #@UndefinedVariable
        deleteButton = PcnImageButton(self._mainEffectImagesListPlane, self._deleteButtonBitmap, self._deleteButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(62, 17)) #@UndefinedVariable
        deleteButton.Bind(wx.EVT_BUTTON, self._onListDeleteButton) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(newButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(deleteButton, 0, wx.ALL, 5) #@UndefinedVariable
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
        dlg = wx.FileDialog(self._mainEffectImagesListPlane, "Choose a file", self._lastDialogDir, "", "*.*", wx.OPEN) #@UndefinedVariable
        if dlg.ShowModal() == wx.ID_OK: #@UndefinedVariable
            selectedFileName = dlg.GetPath()
            self._lastDialogDir = os.path.dirname(selectedFileName)
            fileName = forceUnixPath(selectedFileName)
            if((self._videoDirectory != "") and (fileName != "")):
                if(os.path.isabs(fileName)):
                    try:
                        noteFileName = forceUnixPath(os.path.relpath(fileName, self._videoDirectory))
                    except:
                        noteFileName = fileName
                    else:
                        if(noteFileName.startswith("..") == True):
                            noteFileName = fileName
                    fileName = noteFileName
            oldImage = self._globalConfig.getEffectImage(fileName)
            if(oldImage == None):
                self._globalConfig.makeNewEffectImage(fileName)
                self.updateEffectImageList()
            else:
                print "Warning: We already got this image! Ignoring."
        dlg.Destroy()

    def _onListDeleteButton(self, event):
        if(self._effectImageListSelectedIndex >= 0):
            effectImage = self._globalConfig.getEffectImageByIndex(self._effectImageListSelectedIndex)
            if(effectImage != None):
                effectImageFileName = effectImage.getFileName()
                text = "Are you sure you want to delete \"%s\"?" % (effectImageFileName)
                dlg = wx.MessageDialog(self._mainEffectImagesListPlane, text, 'Delete?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                dlg.Destroy()
                if(result == True):
                    self._globalConfig.deleteEffectImage(effectImageFileName)
                    self.updateEffectImageList()

    def _onListItemSelected(self, event):
        self._effectImageListSelectedIndex = event.m_itemIndex

    def _onListItemDeselected(self, event):
        self._effectImageListSelectedIndex = -1

    def _onListDoubbleClick(self, event):
        effectImage = self._globalConfig.getEffectImageByIndex(self._effectImageListSelectedIndex)
        if(effectImage != None):
            print "Show image editor!!!" * 10
#            self.updateGui(effectImage, None, self._activeEffectId)
#            self._showEffectsCallback()

