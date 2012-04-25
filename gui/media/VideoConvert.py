'''
Created on 22. mars 2012

@author: pcn
'''

import wx
import os
import subprocess
from multiprocessing import Process, Queue
from Queue import Empty
import sys
import time
import shutil

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
        self._convertionWentOk = False

        dialogSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable
        self.SetBackgroundColour((180,180,180))

        infoText = wx.StaticText(self, wx.ID_ANY, "This file needs to be converted. Please select yout options here:") #@UndefinedVariable
        dialogSizer.Add(infoText, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

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
        buttonsSizer.Add(convertButton, 1, wx.ALL, 5) #@UndefinedVariable
        buttonsSizer.Add(cancelButton, 1, wx.ALL, 5) #@UndefinedVariable
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
            cropOptions = " -vf crop=3/4*in_w:in_h"
        elif(cropMode == "4.3->16:9"):
            cropOptions = " -vf crop=in_w:3/4*in_h"
        scaleMode = self._scaleModeField.GetValue()
        scaleOptions = ""
        if(scaleMode != "No scale"):
            xscale = int(self._scaleXField.GetValue())
            yscale = int(self._scaleYField.GetValue())
            scaleOptions = " -vf scale=%d:%d" % (xscale, yscale)

        if(convertFile == True):
            print "Open converter dialog..."
            print "Show ffmpeg output realtime etc."
            ffmpegCommand = "%s -i %s%s%s -vcodec mjpeg -qscale 1 -an -y %s" % (self._ffmpegPath, self._inputFile, cropOptions, scaleOptions, outputFileName)
            dlg = VideoConverterStatusDialog(self, 'Converting file...', ffmpegCommand, self._okConvertionCallback)
            dlg.ShowModal()
            dlg.Destroy()
            self._valuesSaveCallback(self._dirName, cropMode, scaleMode, int(self._scaleXField.GetValue()), int(self._scaleYField.GetValue()), self._convertionWentOk, outputFileName)
            self.Destroy()

    def _okConvertionCallback(self):
        self._convertionWentOk = True

    def _onCancel(self, event):
        self.Destroy()

class VideoCopyDialog(wx.Dialog): #@UndefinedVariable
    
    def __init__(self, parent, title, valuesSaveCallback, lastDirName, configVideoDir, inputFile):
        super(VideoCopyDialog, self).__init__(parent=parent, title=title, size=(400, 180))

        self._valuesSaveCallback = valuesSaveCallback
        self._videoDirectory = configVideoDir
        self._dirName = lastDirName
        self._inputFile = inputFile

        dialogSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable
        self.SetBackgroundColour((180,180,180))

        infoText = wx.StaticText(self, wx.ID_ANY, "This file should be copied since it is not in your video directory: \"%s\" is not within \"%s\"" % (inputFile, configVideoDir)) #@UndefinedVariable
        dialogSizer.Add(infoText, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

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


        buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        copyButton = wx.Button(self, wx.ID_ANY, 'Copy', size=(60,-1)) #@UndefinedVariable
        copyButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        keepButton = wx.Button(self, wx.ID_ANY, 'Keep path', size=(60,-1)) #@UndefinedVariable
        keepButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        cancelButton = wx.Button(self, wx.ID_ANY, 'Cancel', size=(60,-1)) #@UndefinedVariable
        cancelButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        buttonsSizer.Add(copyButton, 1, wx.ALL, 5) #@UndefinedVariable
        buttonsSizer.Add(keepButton, 1, wx.ALL, 5) #@UndefinedVariable
        buttonsSizer.Add(cancelButton, 1, wx.ALL, 5) #@UndefinedVariable
        copyButton.Bind(wx.EVT_BUTTON, self._onCopy) #@UndefinedVariable
        keepButton.Bind(wx.EVT_BUTTON, self._onKeep) #@UndefinedVariable
        cancelButton.Bind(wx.EVT_BUTTON, self._onCancel) #@UndefinedVariable
        dialogSizer.Add(buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self.SetSizer(dialogSizer)


    def _onOpenDir(self, event):
        dlg = wx.DirDialog (self, "Choose a directory", os.path.join(self._videoDirectory, self._dirName), style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON) #@UndefinedVariable
        if dlg.ShowModal() == wx.ID_OK: #@UndefinedVariable
            self._dirName = os.path.relpath(dlg.GetPath(), self._videoDirectory)
            self._dirNameField.SetValue(self._dirName)
        dlg.Destroy()

    def _onCopy(self, event):
        baseName = os.path.basename(self._inputFile)
        outputFileName = os.path.join(self._videoDirectory, self._dirName, baseName)
        copyFile = True
        if(os.path.isfile(outputFileName)):
            copyFile = False
            dlg = wx.MessageDialog(self, "File \"" + outputFileName + "\" already exists.\n\nDo you want to overwrite?", 'Overwrite?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
            result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
            dlg.Destroy()
            if(result == True):
                copyFile = True
        if(os.path.isdir(outputFileName)):
            copyFile = False
            dlg = wx.MessageDialog(self._mediaFileGuiPanel, "Cannot copy file: \"" + outputFileName + "\" because this is a directory!", 'Output error!', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
            dlg.ShowModal()
            dlg.Destroy()

        if(copyFile == True):
            shutil.copy(self._inputFile, outputFileName)
            self._valuesSaveCallback(True, outputFileName, self._dirName)
            self.Destroy()

    def _onKeep(self, event):
        self._valuesSaveCallback(True, self._inputFile)
        self.Destroy()

    def _onCancel(self, event):
        self._valuesSaveCallback(False)
        self.Destroy()

class VideoConverterStatusDialog(wx.Dialog): #@UndefinedVariable
    
    def __init__(self, parent, title, ffmpegCommand, okConvertionCallback):
        super(VideoConverterStatusDialog, self).__init__(parent=parent, title=title, size=(800, 320))

        self._okConvertionCallback = okConvertionCallback

        dialogSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable
        self.SetBackgroundColour((180,180,180))

        commandSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        commandLabel = wx.StaticText(self, wx.ID_ANY, "Running:") #@UndefinedVariable
        commandField = wx.TextCtrl(self, wx.ID_ANY, ffmpegCommand) #@UndefinedVariable
        commandField.SetEditable(False)
        commandField.SetBackgroundColour((222,222,222))
        commandSizer.Add(commandLabel, 0, wx.ALL, 5) #@UndefinedVariable
        commandSizer.Add(commandField, 1, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(commandSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        ffmpegOutputSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        self._ffmpegOutputArea = wx.TextCtrl(self, style=wx.TE_MULTILINE, size=(-1,200)) #@UndefinedVariable
        self._ffmpegOutputArea.SetEditable(False)
        self._ffmpegOutputArea.SetBackgroundColour((232,232,232))
        ffmpegOutputSizer.Add(self._ffmpegOutputArea, 1, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(ffmpegOutputSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        self._doneButton = wx.Button(self, wx.ID_ANY, 'Done', size=(60,-1)) #@UndefinedVariable
        self._doneButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._backgroundButton = wx.Button(self, wx.ID_ANY, 'Background', size=(60,-1)) #@UndefinedVariable
        self._backgroundButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._cancelButton = wx.Button(self, wx.ID_ANY, 'Cancel', size=(60,-1)) #@UndefinedVariable
        self._cancelButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        self._buttonsSizer.Add(self._doneButton, 1, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Hide(self._doneButton)
        self._buttonsSizer.Add(self._backgroundButton, 1, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(self._cancelButton, 1, wx.ALL, 5) #@UndefinedVariable
        self._doneButton.Bind(wx.EVT_BUTTON, self._onCancel) #@UndefinedVariable
        self._backgroundButton.Bind(wx.EVT_BUTTON, self._onBackground) #@UndefinedVariable
        self._cancelButton.Bind(wx.EVT_BUTTON, self._onCancel) #@UndefinedVariable
        dialogSizer.Add(self._buttonsSizer, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        self.SetSizer(dialogSizer)

        self._commandProcess = None
        self._startConvertion(ffmpegCommand)

        self._printTimer = wx.Timer(self, -1) #@UndefinedVariable
        self._printTimer.Start(50)#20 times a second
        self.Bind(wx.EVT_TIMER, self._onGetOutputTimer) #@UndefinedVariable

    def _startConvertion(self, command):
        self._commandPrintQueue = Queue(0)
        self._returnValueQueue = Queue(1)
        self._commandQueue = Queue(1)
        self._commandProcess = Process(target=callCommandProcess, args=(command, self._commandQueue, self._commandPrintQueue, self._returnValueQueue))
        self._commandProcess.name = "convertionCommandProcess"
        self._commandProcess.start()

    def _stopConvertion(self, kill = False):
        if(self._commandProcess != None):
            if(self._commandProcess.is_alive()):
                if(kill == True):
                    print "Killing command."
                    self._commandQueue.put(True)
                    time.sleep(1)
                    self._onGetOutputTimer(None)
        if(self._commandProcess != None):
            if(self._commandProcess.is_alive()):
                print "Terminating command process."
                self._commandProcess.terminate()
        self._commandProcess = None
        self._printTimer.Stop()

    def _onGetOutputTimer(self, event):
        outputText = ""
        skippedCount = 0
        try:
            while(True):
                outputText += self._commandPrintQueue.get_nowait()
                if(skippedCount < 25):
                    skippedCount += 1
                else:
                    self._ffmpegOutputArea.AppendText(outputText)
                    sys.stdout.write(outputText)
                    outputText = ""
                    skippedCount = 0
        except Empty:
            if(outputText != ""):
                self._ffmpegOutputArea.AppendText(outputText)
                sys.stdout.write(outputText)
        if(self._commandProcess.is_alive() == False):
            self._stopConvertion()
            try:
                returnValue = self._returnValueQueue.get_nowait()
                if(returnValue == 0):
                    returnedOk = True
                else:
                    returnedOk = False
            except Empty:
                returnedOk = False
            if(returnedOk == True):
                self._buttonsSizer.Show(self._doneButton)
                self._buttonsSizer.Hide(self._cancelButton)
                self._okConvertionCallback()
            self._buttonsSizer.Hide(self._backgroundButton)
            self.Layout()

    def _onBackground(self, event):
        self._stopConvertion(False)
        self.Destroy()

    def _onCancel(self, event):
        self._stopConvertion(True)
        self.Destroy()

def callCommandProcess(command, commandQueue, printQueue, returnValueQueue):
    process = subprocess.Popen(command.split(' '), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    printQueue.put("Running: " + command + "\n")
    while True:
        out = process.stdout.read(1)
        if out == '' and process.poll() != None:
            break
        if out != '':
            printQueue.put(out)
        try:
            stop = commandQueue.get_nowait()
            if(stop == True):
                printQueue.put("\n\nTerminated by user!\n")
                process.terminate()
                break
        except Empty:
            pass
    printQueue.put(process.communicate()[0])
    printQueue.put("Done.")
    returnValueQueue.put(process.returncode)
