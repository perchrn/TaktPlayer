'''
Created on 22. mars 2012

@author: pcn
'''

import wx
import os

class VideoConverterDialog(wx.Dialog): #@UndefinedVariable
    
    def __init__(self, parent, title, valuesSaveCallback, ffmpegPath, lastDirName, configVideoDir, inputFile, cropValue, scaleModeValue, scaleXValue, scaleYValue):
        super(VideoConverterDialog, self).__init__(parent=parent, title=title, size=(400, 280))

        self._valuesSaveCallback = valuesSaveCallback
        self._videoDirectory = configVideoDir
        self._ffmpegPath = ffmpegPath
        self._dirName = lastDirName
        self._inputFile = inputFile
        self._cropMode = cropValue
        self._scaleMode = scaleModeValue
        self._scaleXValue = scaleXValue
        self._scaleYValue = scaleYValue

        dialogSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable
        self.SetBackgroundColour((180,180,180))

        dirSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        dirNameLabel = wx.StaticText(self, wx.ID_ANY, "Dir name:") #@UndefinedVariable
        self._dirNameField = wx.TextCtrl(self, wx.ID_ANY, self._dirName, size=(200, -1)) #@UndefinedVariable
        self._dirNameField.SetEditable(False)
        self._dirNameField.SetBackgroundColour((222,222,222))
        dirOpenButton = wx.Button(self, wx.ID_ANY, 'Select', size=(60,-1)) #@UndefinedVariable
        dirOpenButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self.Bind(wx.EVT_BUTTON, self._onOpenDir, id=dirOpenButton.GetId()) #@UndefinedVariable
        dirSizer.Add(dirNameLabel, 1, wx.ALL, 5) #@UndefinedVariable
        dirSizer.Add(self._dirNameField, 2, wx.ALL, 5) #@UndefinedVariable
        dirSizer.Add(dirOpenButton, 0, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(dirSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        cropSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        cropLabel = wx.StaticText(self, wx.ID_ANY, "Crop:") #@UndefinedVariable
        self._cropModeField = wx.ComboBox(self, wx.ID_ANY, size=(200, -1), choices=[], style=wx.CB_READONLY) #@UndefinedVariable
        self._cropModeField.Clear()
        valueOk = False
        for choice in ["No crop", "16:9->4:3", "4.3->16:9"]:
            self._cropModeField.Append(choice)
            if(choice == self._cropMode):
                valueOk = True
        if(valueOk == True):
            self._cropModeField.SetStringSelection(self._cropMode)
        else:
            self._cropModeField.SetStringSelection("No crop")
        cropSizer.Add(cropLabel, 1, wx.ALL, 5) #@UndefinedVariable
        cropSizer.Add(self._cropModeField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(cropSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        scaleModeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        scaleModeLabel = wx.StaticText(self, wx.ID_ANY, "Scale mode:") #@UndefinedVariable
        self._scaleModeField = wx.ComboBox(self, wx.ID_ANY, size=(200, -1), choices=[], style=wx.CB_READONLY) #@UndefinedVariable
        self._scaleModeField.Clear()
        valueOk = False
        for choice in ["No scale", "800x600", "1024x768", "720x480", "1280x720", "1920x1080", "Custom"]:
            self._scaleModeField.Append(choice)
            if(choice == self._scaleMode):
                valueOk = True
        if(valueOk == True):
            self._scaleModeField.SetStringSelection(self._scaleMode)
        else:
            self._scaleModeField.SetStringSelection("No scale")
        self.Bind(wx.EVT_COMBOBOX, self._onScaleModeChosen, id=self._scaleModeField.GetId()) #@UndefinedVariable
        scaleModeSizer.Add(scaleModeLabel, 1, wx.ALL, 5) #@UndefinedVariable
        scaleModeSizer.Add(self._scaleModeField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(scaleModeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        scaleSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        scaleLabel = wx.StaticText(self, wx.ID_ANY, "Custom scale:") #@UndefinedVariable
        self._scaleXField = wx.TextCtrl(self, wx.ID_ANY, str(self._scaleXValue), size=(120, -1)) #@UndefinedVariable
        self._scaleYField = wx.TextCtrl(self, wx.ID_ANY, str(self._scaleYValue), size=(120, -1)) #@UndefinedVariable
        scaleSizer.Add(scaleLabel, 1, wx.ALL, 5) #@UndefinedVariable
        scaleSizer.Add(self._scaleXField, 1, wx.ALL, 5) #@UndefinedVariable
        scaleSizer.Add(self._scaleYField, 1, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(scaleSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable


        buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        convertButton = wx.Button(self, wx.ID_ANY, 'Convert', size=(60,-1)) #@UndefinedVariable
        convertButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        cancelButton = wx.Button(self, wx.ID_ANY, 'Cancel', size=(60,-1)) #@UndefinedVariable
        cancelButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        buttonsSizer.Add(convertButton, 0, wx.ALL, 5) #@UndefinedVariable
        buttonsSizer.Add(cancelButton, 0, wx.ALL, 5) #@UndefinedVariable
        convertButton.Bind(wx.EVT_BUTTON, self._onConvert) #@UndefinedVariable
        cancelButton.Bind(wx.EVT_BUTTON, self._onCancel) #@UndefinedVariable
        dialogSizer.Add(buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self.SetSizer(dialogSizer)
        self._onScaleModeChosen(None)


    def _onScaleModeChosen(self, event):
        scaleMode = self._scaleModeField.GetValue()
        if(scaleMode == "Custom"):
            self._scaleXField.SetEditable(True)
            self._scaleYField.SetEditable(True)
            self._scaleXField.SetBackgroundColour((255,255,255))
            self._scaleYField.SetBackgroundColour((255,255,255))
        else:
            self._scaleXField.SetEditable(False)
            self._scaleYField.SetEditable(False)
            self._scaleXField.SetBackgroundColour((222,222,222))
            self._scaleYField.SetBackgroundColour((222,222,222))
            if(scaleMode == "800x600"):
                self._scaleXField.SetValue("800")
                self._scaleYField.SetValue("600")
            if(scaleMode == "1024x768"):
                self._scaleXField.SetValue("1024")
                self._scaleYField.SetValue("768")
            if(scaleMode == "720x480"):
                self._scaleXField.SetValue("720")
                self._scaleYField.SetValue("480")
            if(scaleMode == "1280x720"):
                self._scaleXField.SetValue("1280")
                self._scaleYField.SetValue("720")
            if(scaleMode == "1920x1080"):
                self._scaleXField.SetValue("1920")
                self._scaleYField.SetValue("1080")

    def _onOpenDir(self, event):
        dlg = wx.DirDialog (self, "Choose a directory", os.path.join(self._videoDirectory, self._dirName), style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON) #@UndefinedVariable
        if dlg.ShowModal() == wx.ID_OK: #@UndefinedVariable
            self._dirName = os.path.relpath(dlg.GetPath(), self._videoDirectory)
            self._dirNameField.SetValue(self._dirName)
        dlg.Destroy()

    def _onConvert(self, event):
        baseName = os.path.basename(self._inputFile)
        if(baseName.endswith("_mjpeg.avi")):
            newName = baseName
        else:
            newName = os.path.splitext(baseName)[0] + "_mjpeg.avi"
        outputFileName = os.path.join(self._videoDirectory, self._dirName, newName)
        convertFile = True
        if(os.path.isfile(outputFileName)):
            convertFile = False
            dlg = wx.MessageDialog(self, "File \"" + outputFileName + "\" already exists.\n\nDo you want to overwrite?", 'Overwrite?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
            result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
            dlg.Destroy()
            if(result == True):
                convertFile = True
        if(os.path.isdir(outputFileName)):
            convertFile = False
            dlg = wx.MessageDialog(self._mediaFileGuiPanel, "Cannot convert file: \"" + outputFileName + "\" because this is a directory!", 'Output error!', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
            dlg.ShowModal()
            dlg.Destroy()

        cropMode = self._cropModeField.GetValue()
        cropOptions = ""
        if(cropMode == "16:9->4:3"):
            cropOptions = "-vf crop=3/4*in_w:in_h"
        elif(cropMode == "4.3->16:9"):
            cropOptions = "-vf crop=in_w:3/4*in_h"
        scaleMode = self._scaleModeField.GetValue()
        scaleOptions = ""
        if(scaleMode != "No scale"):
            xscale = int(self._scaleXField.GetValue())
            yscale = int(self._scaleYField.GetValue())
            scaleOptions = "-vf scale=%d:%d" % (xscale, yscale)

        if(convertFile == True):
            print "Open converter dialog..."
            print "Show ffmpeg output realtime etc."
            print "%s -i %s %s %s -vcodec mjpeg -qscale 1 -an -y %s" % (self._ffmpegPath, self._inputFile, cropOptions, scaleOptions, outputFileName)
            self._valuesSaveCallback(self._dirName, cropMode, scaleMode, int(self._scaleXField.GetValue()), int(self._scaleYField.GetValue()))
            self.Destroy()

    def _onCancel(self, event):
        self.Destroy()


