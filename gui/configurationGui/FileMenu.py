'''
Created on 27. juni 2012

@author: pcn
'''
import wx
from configuration.PlayerConfiguration import PlayerConfiguration
from midi.MidiUtilities import noteToNoteString

class ConfigOpenDialog(wx.Dialog): #@UndefinedVariable
    def __init__(self, parent, title, sendOpenCommandCallback, configList, lastSelectedConfig):
        super(ConfigOpenDialog, self).__init__(parent=parent, title=title, size=(300, 150))

        self._sendOpenCommandCallback = sendOpenCommandCallback
        self._configList = configList
        self._lastSelectedConfig = lastSelectedConfig

        dialogSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable
        self.SetBackgroundColour((180,180,180))

        infoText = wx.StaticText(self, wx.ID_ANY, "Please select file to open:") #@UndefinedVariable
        dialogSizer.Add(infoText, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        configListSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        configListLabel = wx.StaticText(self, wx.ID_ANY, "Configuration:") #@UndefinedVariable
        self._configListField = wx.ComboBox(self, wx.ID_ANY, size=(200, -1), choices=[], style=wx.CB_READONLY) #@UndefinedVariable
        self._configListField.Clear()
        valueOk = False
        backupSelection = self._configList[0]
        for choice in self._configList:
            self._configListField.Append(choice)
            if(choice == self._lastSelectedConfig):
                valueOk = True
        if(valueOk == True):
            self._configListField.SetStringSelection(self._lastSelectedConfig)
        else:
            self._configListField.SetStringSelection(backupSelection)
        configListSizer.Add(configListLabel, 1, wx.ALL, 5) #@UndefinedVariable
        configListSizer.Add(self._configListField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(configListSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable


        buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        loadButton = wx.Button(self, wx.ID_ANY, 'Load', size=(60,-1)) #@UndefinedVariable
        loadButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        cancelButton = wx.Button(self, wx.ID_ANY, 'Cancel', size=(60,-1)) #@UndefinedVariable
        cancelButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        buttonsSizer.Add(loadButton, 1, wx.ALL, 5) #@UndefinedVariable
        buttonsSizer.Add(cancelButton, 1, wx.ALL, 5) #@UndefinedVariable
        loadButton.Bind(wx.EVT_BUTTON, self._onLoad) #@UndefinedVariable
        cancelButton.Bind(wx.EVT_BUTTON, self._onCancel) #@UndefinedVariable
        dialogSizer.Add(buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self.SetSizer(dialogSizer)


    def _onLoad(self, event):
        self._sendOpenCommandCallback(self._configListField.GetValue())
        self.Destroy()

    def _onCancel(self, event):
        self.Destroy()

class ConfigNewDialog(wx.Dialog): #@UndefinedVariable
    def __init__(self, parent, title, updateConfigNameCallback, currentConfigName):
        super(ConfigNewDialog, self).__init__(parent=parent, title=title, size=(300, 120))

        self._updateConfigNameCallback = updateConfigNameCallback
        self._currentConfigName = currentConfigName

        dialogSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable
        self.SetBackgroundColour((180,180,180))

        infoText = wx.StaticText(self, wx.ID_ANY, "Please type new name:") #@UndefinedVariable
        dialogSizer.Add(infoText, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        configNameSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        configNameLabel = wx.StaticText(self, wx.ID_ANY, "New name:") #@UndefinedVariable
        self._configNameField = wx.TextCtrl(self, wx.ID_ANY, str(self._currentConfigName), size=(120, -1)) #@UndefinedVariable
        configNameSizer.Add(configNameLabel, 1, wx.ALL, 5) #@UndefinedVariable
        configNameSizer.Add(self._configNameField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(configNameSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable


        buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        newButton = wx.Button(self, wx.ID_ANY, 'New', size=(60,-1)) #@UndefinedVariable
        newButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        cancelButton = wx.Button(self, wx.ID_ANY, 'Cancel', size=(60,-1)) #@UndefinedVariable
        cancelButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        buttonsSizer.Add(newButton, 1, wx.ALL, 5) #@UndefinedVariable
        buttonsSizer.Add(cancelButton, 1, wx.ALL, 5) #@UndefinedVariable
        newButton.Bind(wx.EVT_BUTTON, self._onOk) #@UndefinedVariable
        cancelButton.Bind(wx.EVT_BUTTON, self._onCancel) #@UndefinedVariable
        dialogSizer.Add(buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self.SetSizer(dialogSizer)


    def _onOk(self, event):
        self._updateConfigNameCallback(self._configNameField.GetValue())
        self.Destroy()

    def _onCancel(self, event):
        self.Destroy()

class ConfigGuiDialog(wx.Dialog): #@UndefinedVariable
    def __init__(self, parent, title, configurationClass):
        super(ConfigGuiDialog, self).__init__(parent=parent, title=title, size=(440, 520))

        self._configurationClass = configurationClass

        dialogSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable
        self.SetBackgroundColour((180,180,180))

        infoText = wx.StaticText(self, wx.ID_ANY, "Player:") #@UndefinedVariable
        boldFont = infoText.GetFont()
        boldFont.SetWeight(wx.BOLD) #@UndefinedVariable
        infoText.SetFont(boldFont)
        dialogSizer.Add(infoText, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        playerHostName, playerWebPort = self._configurationClass.getWebConfig()

        isMidiOn = self._configurationClass.isMidiEnabled()
        playerMidiOnSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        playerMidiOnLabel = wx.StaticText(self, wx.ID_ANY, "MIDI:") #@UndefinedVariable
        self._playerMidiOnField = wx.CheckBox(self, wx.ID_ANY, "Send MIDI notes from GUI to player.") #@UndefinedVariable
        self._playerMidiOnField.SetValue(isMidiOn)
        playerMidiOnSizer.Add(playerMidiOnLabel, 1, wx.ALL, 5) #@UndefinedVariable
        playerMidiOnSizer.Add(self._playerMidiOnField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(playerMidiOnSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        playerHostNameSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        playerHostNameLabel = wx.StaticText(self, wx.ID_ANY, "Host address:") #@UndefinedVariable
        self._playerHostNameField = wx.TextCtrl(self, wx.ID_ANY, str(playerHostName), size=(120, -1)) #@UndefinedVariable
        playerHostNameSizer.Add(playerHostNameLabel, 1, wx.ALL, 5) #@UndefinedVariable
        playerHostNameSizer.Add(self._playerHostNameField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(playerHostNameSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        playerHostName, playerMidiPort = self._configurationClass.getMidiConfig()
        playerMidiPortSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        playerMidiPortLabel = wx.StaticText(self, wx.ID_ANY, "MIDI port:") #@UndefinedVariable
        self._playerMidiPortField = wx.SpinCtrl(self, value=str(playerMidiPort), pos=(-1, -1), size=(60, -1)) #@UndefinedVariable
        self._playerMidiPortField.SetRange(1024, 9999)
        playerMidiPortSizer.Add(playerMidiPortLabel, 1, wx.ALL, 5) #@UndefinedVariable
        playerMidiPortSizer.Add(self._playerMidiPortField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(playerMidiPortSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        playerWebPortSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        playerWebPortLabel = wx.StaticText(self, wx.ID_ANY, "Web port:") #@UndefinedVariable
        self._playerWebPortField = wx.SpinCtrl(self, value=str(playerWebPort), pos=(-1, -1), size=(60, -1)) #@UndefinedVariable
        self._playerWebPortField.SetRange(1024, 9999)
        playerWebPortSizer.Add(playerWebPortLabel, 1, wx.ALL, 5) #@UndefinedVariable
        playerWebPortSizer.Add(self._playerWebPortField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(playerWebPortSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        infoText = wx.StaticText(self, wx.ID_ANY, "GUI:") #@UndefinedVariable
        infoText.SetFont(boldFont)
        dialogSizer.Add(infoText, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        isAutosendOn = self._configurationClass.isAutoSendEnabled()
        autoSendOnSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        autoSendOnLabel = wx.StaticText(self, wx.ID_ANY, "Autosend:") #@UndefinedVariable
        self._autoSendOnField = wx.CheckBox(self, wx.ID_ANY, "Send all configuration changes to Player.") #@UndefinedVariable
        self._autoSendOnField.SetValue(isAutosendOn)
        autoSendOnSizer.Add(autoSendOnLabel, 1, wx.ALL, 5) #@UndefinedVariable
        autoSendOnSizer.Add(self._autoSendOnField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(autoSendOnSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        guiMidiBindBroadcast, guiMidiBindAddress, guiMidiBindPort = self._configurationClass.getMidiListenConfig()
        guiMidiBindAddressSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        guiMidiBindAddressLabel = wx.StaticText(self, wx.ID_ANY, "Input address:") #@UndefinedVariable
        self._guiMidiBindAddressField = wx.TextCtrl(self, wx.ID_ANY, str(guiMidiBindAddress), size=(120, -1)) #@UndefinedVariable
        guiMidiBindAddressSizer.Add(guiMidiBindAddressLabel, 1, wx.ALL, 5) #@UndefinedVariable
        guiMidiBindAddressSizer.Add(self._guiMidiBindAddressField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(guiMidiBindAddressSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        guiMidiPortSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        guiMidiPortLabel = wx.StaticText(self, wx.ID_ANY, "Input port:") #@UndefinedVariable
        self._guiMidiPortField = wx.SpinCtrl(self, value=str(guiMidiBindPort), pos=(-1, -1), size=(60, -1)) #@UndefinedVariable
        self._guiMidiPortField.SetRange(1024, 9999)
        guiMidiPortSizer.Add(guiMidiPortLabel, 1, wx.ALL, 5) #@UndefinedVariable
        guiMidiPortSizer.Add(self._guiMidiPortField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(guiMidiPortSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        guiMidiBroadcastSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        guiMidiBroadcastLabel = wx.StaticText(self, wx.ID_ANY, "Broadcast:") #@UndefinedVariable
        self._guiMidiBroadcastField = wx.CheckBox(self, wx.ID_ANY, "Receive broadcast packets.") #@UndefinedVariable
        self._guiMidiBroadcastField.SetValue(guiMidiBindBroadcast)
        guiMidiBroadcastSizer.Add(guiMidiBroadcastLabel, 1, wx.ALL, 5) #@UndefinedVariable
        guiMidiBroadcastSizer.Add(self._guiMidiBroadcastField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(guiMidiBroadcastSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        sizeX, sizeY = self._configurationClass.getWindowSize()
        windowSizeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        windowSizeLabel = wx.StaticText(self, wx.ID_ANY, "Input address:") #@UndefinedVariable
        self._windowSizeField = wx.TextCtrl(self, wx.ID_ANY, str(sizeX) + "," + str(sizeY), size=(120, -1)) #@UndefinedVariable
        windowSizeSizer.Add(windowSizeLabel, 1, wx.ALL, 5) #@UndefinedVariable
        windowSizeSizer.Add(self._windowSizeField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(windowSizeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        posX, posY = self._configurationClass.getWindowPosition()
        windowPosSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        windowPosLabel = wx.StaticText(self, wx.ID_ANY, "Input address:") #@UndefinedVariable
        self._windowPosField = wx.TextCtrl(self, wx.ID_ANY, str(posX) + "," + str(posY), size=(120, -1)) #@UndefinedVariable
        windowPosSizer.Add(windowPosLabel, 1, wx.ALL, 5) #@UndefinedVariable
        windowPosSizer.Add(self._windowPosField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(windowPosSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable



        infoText = wx.StaticText(self, wx.ID_ANY, "Convertion:") #@UndefinedVariable
        infoText.SetFont(boldFont)
        dialogSizer.Add(infoText, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        ffmpegBinary = self._configurationClass.getFfmpegBinary()
        ffmpegBinarySizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        ffmpegBinaryLabel = wx.StaticText(self, wx.ID_ANY, "ffmpeg binary:") #@UndefinedVariable
        self._ffmpegBinaryField = wx.TextCtrl(self, wx.ID_ANY, str(ffmpegBinary), size=(120, -1)) #@UndefinedVariable
        ffmpegBinarySizer.Add(ffmpegBinaryLabel, 1, wx.ALL, 5) #@UndefinedVariable
        ffmpegBinarySizer.Add(self._ffmpegBinaryField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(ffmpegBinarySizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        scaleX = self._configurationClass.getVideoScaleX()
        scaleXSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        scaleXLabel = wx.StaticText(self, wx.ID_ANY, "Default X scale size:") #@UndefinedVariable
        self._scaleXField = wx.SpinCtrl(self, value=str(scaleX), pos=(-1, -1), size=(60, -1)) #@UndefinedVariable
        self._scaleXField.SetRange(-1, 8000)
        scaleXSizer.Add(scaleXLabel, 1, wx.ALL, 5) #@UndefinedVariable
        scaleXSizer.Add(self._scaleXField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(scaleXSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        scaleY = self._configurationClass.getVideoScaleY()
        scaleYSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        scaleYLabel = wx.StaticText(self, wx.ID_ANY, "Default Y scale size:") #@UndefinedVariable
        self._scaleYField = wx.SpinCtrl(self, value=str(scaleY), pos=(-1, -1), size=(60, -1)) #@UndefinedVariable
        self._scaleYField.SetRange(-1, 6000)
        scaleYSizer.Add(scaleYLabel, 1, wx.ALL, 5) #@UndefinedVariable
        scaleYSizer.Add(self._scaleYField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(scaleYSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        videoDirectory = self._configurationClass.getGuiVideoDir()
        videoDirectorySizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        videoDirectoryLabel = wx.StaticText(self, wx.ID_ANY, "Video directory:") #@UndefinedVariable
        self._videoDirectoryField = wx.TextCtrl(self, wx.ID_ANY, str(videoDirectory), size=(120, -1)) #@UndefinedVariable
        videoDirectorySizer.Add(videoDirectoryLabel, 1, wx.ALL, 5) #@UndefinedVariable
        videoDirectorySizer.Add(self._videoDirectoryField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(videoDirectorySizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        newButton = wx.Button(self, wx.ID_ANY, 'Save', size=(60,-1)) #@UndefinedVariable
        newButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        cancelButton = wx.Button(self, wx.ID_ANY, 'Cancel', size=(60,-1)) #@UndefinedVariable
        cancelButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        buttonsSizer.Add(newButton, 1, wx.ALL, 5) #@UndefinedVariable
        buttonsSizer.Add(cancelButton, 1, wx.ALL, 5) #@UndefinedVariable
        newButton.Bind(wx.EVT_BUTTON, self._onOk) #@UndefinedVariable
        cancelButton.Bind(wx.EVT_BUTTON, self._onCancel) #@UndefinedVariable
        dialogSizer.Add(buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self.SetSizer(dialogSizer)


    def _onOk(self, event):
        playerHost = self._playerHostNameField.GetValue()
        midiPort = self._playerMidiPortField.GetValue()
        webPort = self._playerWebPortField.GetValue()
        midiOn = self._playerMidiOnField.GetValue()
        self._configurationClass.setPlayerConfig(playerHost, midiPort, webPort, midiOn)

        videoDir = self._videoDirectoryField.GetValue()
        ffmpegBinary = self._ffmpegBinaryField.GetValue()
        scaleX = self._scaleXField.GetValue()
        scaleY = self._scaleYField.GetValue()
        self._configurationClass.setVideoConfig(videoDir, ffmpegBinary, scaleX, scaleY)

        autoSend = self._autoSendOnField.GetValue()
        midiBcast = self._guiMidiBroadcastField.GetValue()
        midiBindAddress = self._guiMidiBindAddressField.GetValue()
        midiPort2 = self._guiMidiPortField.GetValue()
        winSize = self._windowSizeField.GetValue()
        winPos = self._windowPosField.GetValue()
        self._configurationClass.setGuiConfig(autoSend, midiBcast, midiBindAddress, midiPort2, winSize, winPos)

        self._configurationClass.saveConfig()
        wx.MessageBox('You must restart GUI to make sure all changes to take effect!', 'Info', wx.OK | wx.ICON_INFORMATION) #@UndefinedVariable
        self.Destroy()

    def _onCancel(self, event):
        self.Destroy()

class ConfigPlayerDialog(wx.Dialog): #@UndefinedVariable
    def __init__(self, parent, title, sendConfigCallback, configurationXmlString):
        super(ConfigPlayerDialog, self).__init__(parent=parent, title=title, size=(440, 540))

        self._sendConfigCallback = sendConfigCallback
        self._configurationClass = PlayerConfiguration("", False)
        self._configurationClass.setFromXmlString(configurationXmlString)

        dialogSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable
        self.SetBackgroundColour((180,180,180))

        infoText = wx.StaticText(self, wx.ID_ANY, "Network:") #@UndefinedVariable
        boldFont = infoText.GetFont()
        boldFont.SetWeight(wx.BOLD) #@UndefinedVariable
        infoText.SetFont(boldFont)
        dialogSizer.Add(infoText, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        playerBindName = self._configurationClass.getMidiServerAddress()
        playerBindNameSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        playerBindNameLabel = wx.StaticText(self, wx.ID_ANY, "MIDI bind address:") #@UndefinedVariable
        self._playerBindNameField = wx.TextCtrl(self, wx.ID_ANY, str(playerBindName), size=(120, -1)) #@UndefinedVariable
        playerBindNameSizer.Add(playerBindNameLabel, 1, wx.ALL, 5) #@UndefinedVariable
        playerBindNameSizer.Add(self._playerBindNameField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(playerBindNameSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        playerMidiPort = self._configurationClass.getMidiServerPort()
        playerMidiPortSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        playerMidiPortLabel = wx.StaticText(self, wx.ID_ANY, "MIDI port:") #@UndefinedVariable
        self._playerMidiPortField = wx.SpinCtrl(self, value=str(playerMidiPort), pos=(-1, -1), size=(60, -1)) #@UndefinedVariable
        self._playerMidiPortField.SetRange(1024, 9999)
        playerMidiPortSizer.Add(playerMidiPortLabel, 1, wx.ALL, 5) #@UndefinedVariable
        playerMidiPortSizer.Add(self._playerMidiPortField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(playerMidiPortSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        useBroadcast = self._configurationClass.getMidiServerUsesBroadcast()
        playerMidiBcastOnSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        playerMidiBcastOnLabel = wx.StaticText(self, wx.ID_ANY, "Broadcast:") #@UndefinedVariable
        self._playerMidiBcastOnField = wx.CheckBox(self, wx.ID_ANY, "Listen for MIDI broadcast packets.") #@UndefinedVariable
        self._playerMidiBcastOnField.SetValue(useBroadcast)
        playerMidiBcastOnSizer.Add(playerMidiBcastOnLabel, 1, wx.ALL, 5) #@UndefinedVariable
        playerMidiBcastOnSizer.Add(self._playerMidiBcastOnField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(playerMidiBcastOnSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        playerWebBindName = self._configurationClass.getWebServerAddress()
        playerWebBindNameSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        playerWebBindNameLabel = wx.StaticText(self, wx.ID_ANY, "Web bind address:") #@UndefinedVariable
        self._playerWebBindNameField = wx.TextCtrl(self, wx.ID_ANY, str(playerWebBindName), size=(120, -1)) #@UndefinedVariable
        playerWebBindNameSizer.Add(playerWebBindNameLabel, 1, wx.ALL, 5) #@UndefinedVariable
        playerWebBindNameSizer.Add(self._playerWebBindNameField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(playerWebBindNameSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        playerWebPort = self._configurationClass.getWebServerPort()
        playerWebPortSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        playerWebPortLabel = wx.StaticText(self, wx.ID_ANY, "Web port:") #@UndefinedVariable
        self._playerWebPortField = wx.SpinCtrl(self, value=str(playerWebPort), pos=(-1, -1), size=(60, -1)) #@UndefinedVariable
        self._playerWebPortField.SetRange(1024, 9999)
        playerWebPortSizer.Add(playerWebPortLabel, 1, wx.ALL, 5) #@UndefinedVariable
        playerWebPortSizer.Add(self._playerWebPortField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(playerWebPortSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        infoText = wx.StaticText(self, wx.ID_ANY, "Window:") #@UndefinedVariable
        infoText.SetFont(boldFont)
        dialogSizer.Add(infoText, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        fullscreenMode = self._configurationClass.getFullscreenMode()
        fullscreenSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        fullscreenLabel = wx.StaticText(self, wx.ID_ANY, "Fullscreen:") #@UndefinedVariable
        self._fullscreenField = wx.ComboBox(self, wx.ID_ANY, size=(200, -1), choices=["off", "on", "auto"], style=wx.CB_READONLY) #@UndefinedVariable
        self._fullscreenField.SetStringSelection(fullscreenMode)
        fullscreenSizer.Add(fullscreenLabel, 1, wx.ALL, 5) #@UndefinedVariable
        fullscreenSizer.Add(self._fullscreenField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(fullscreenSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        resolutionX, resolutionY = self._configurationClass.getResolution()
        resolutionXSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        resolutionXLabel = wx.StaticText(self, wx.ID_ANY, "X resolution:") #@UndefinedVariable
        self._resolutionXField = wx.SpinCtrl(self, value=str(resolutionX), pos=(-1, -1), size=(60, -1)) #@UndefinedVariable
        self._resolutionXField.SetRange(400, 4000)
        resolutionXSizer.Add(resolutionXLabel, 1, wx.ALL, 5) #@UndefinedVariable
        resolutionXSizer.Add(self._resolutionXField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(resolutionXSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        resolutionYSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        resolutionYLabel = wx.StaticText(self, wx.ID_ANY, "Y resolution:") #@UndefinedVariable
        self._resolutionYField = wx.SpinCtrl(self, value=str(resolutionY), pos=(-1, -1), size=(60, -1)) #@UndefinedVariable
        self._resolutionYField.SetRange(300, 3000)
        resolutionYSizer.Add(resolutionYLabel, 1, wx.ALL, 5) #@UndefinedVariable
        resolutionYSizer.Add(self._resolutionYField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(resolutionYSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        autoPosition = self._configurationClass.getMidiServerUsesBroadcast()
        autopositionSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        autopositionLabel = wx.StaticText(self, wx.ID_ANY, "Autoposition:") #@UndefinedVariable
        self._autopositionField = wx.CheckBox(self, wx.ID_ANY, "Let OS position window.") #@UndefinedVariable
        self._autopositionField.SetValue(autoPosition)
        autopositionSizer.Add(autopositionLabel, 1, wx.ALL, 5) #@UndefinedVariable
        autopositionSizer.Add(self._autopositionField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(autopositionSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        positionX, positionY = self._configurationClass.getPosition()
        positionXSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        positionXLabel = wx.StaticText(self, wx.ID_ANY, "X position:") #@UndefinedVariable
        self._positionXField = wx.SpinCtrl(self, value=str(positionX), pos=(-1, -1), size=(60, -1)) #@UndefinedVariable
        self._positionXField.SetRange(-1, 8000)
        positionXSizer.Add(positionXLabel, 1, wx.ALL, 5) #@UndefinedVariable
        positionXSizer.Add(self._positionXField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(positionXSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        positionYSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        positionYLabel = wx.StaticText(self, wx.ID_ANY, "Y position:") #@UndefinedVariable
        self._positionYField = wx.SpinCtrl(self, value=str(positionY), pos=(-1, -1), size=(60, -1)) #@UndefinedVariable
        self._positionYField.SetRange(-1, 6000)
        positionYSizer.Add(positionYLabel, 1, wx.ALL, 5) #@UndefinedVariable
        positionYSizer.Add(self._positionYField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(positionYSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        infoText = wx.StaticText(self, wx.ID_ANY, "Startup:") #@UndefinedVariable
        infoText.SetFont(boldFont)
        dialogSizer.Add(infoText, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        startConfig = self._configurationClass.getStartConfig()
        startConfigSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        startConfigLabel = wx.StaticText(self, wx.ID_ANY, "Start configuration:") #@UndefinedVariable
        self._startConfigField = wx.TextCtrl(self, wx.ID_ANY, str(startConfig), size=(120, -1)) #@UndefinedVariable
        startConfigSizer.Add(startConfigLabel, 1, wx.ALL, 5) #@UndefinedVariable
        startConfigSizer.Add(self._startConfigField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(startConfigSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        startNote = self._configurationClass.getStartNoteNumber()
        startNoteSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        startNoteLabel = wx.StaticText(self, wx.ID_ANY, "Start note:") #@UndefinedVariable
        self._startNoteField = wx.SpinCtrl(self, value=str(startNote), pos=(-1, -1), size=(60, -1)) #@UndefinedVariable
        self._startNoteField.SetRange(-1, 127)
        startNoteSizer.Add(startNoteLabel, 1, wx.ALL, 5) #@UndefinedVariable
        startNoteSizer.Add(self._startNoteField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(startNoteSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        videoDir = self._configurationClass.getVideoDir()
        videoDirSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        videoDirLabel = wx.StaticText(self, wx.ID_ANY, "Video directory:") #@UndefinedVariable
        self._videoDirField = wx.TextCtrl(self, wx.ID_ANY, str(videoDir), size=(120, -1)) #@UndefinedVariable
        videoDirSizer.Add(videoDirLabel, 1, wx.ALL, 5) #@UndefinedVariable
        videoDirSizer.Add(self._videoDirField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(videoDirSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        configDir = self._configurationClass.getConfigDir()
        configDirSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        configDirLabel = wx.StaticText(self, wx.ID_ANY, "Configuration directory:") #@UndefinedVariable
        self._configDirField = wx.TextCtrl(self, wx.ID_ANY, str(configDir), size=(120, -1)) #@UndefinedVariable
        configDirSizer.Add(configDirLabel, 1, wx.ALL, 5) #@UndefinedVariable
        configDirSizer.Add(self._configDirField, 2, wx.ALL, 5) #@UndefinedVariable
        dialogSizer.Add(configDirSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable


        buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        newButton = wx.Button(self, wx.ID_ANY, 'Save', size=(60,-1)) #@UndefinedVariable
        newButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        cancelButton = wx.Button(self, wx.ID_ANY, 'Cancel', size=(60,-1)) #@UndefinedVariable
        cancelButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        buttonsSizer.Add(newButton, 1, wx.ALL, 5) #@UndefinedVariable
        buttonsSizer.Add(cancelButton, 1, wx.ALL, 5) #@UndefinedVariable
        newButton.Bind(wx.EVT_BUTTON, self._onOk) #@UndefinedVariable
        cancelButton.Bind(wx.EVT_BUTTON, self._onCancel) #@UndefinedVariable
        dialogSizer.Add(buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self.SetSizer(dialogSizer)


    def _onOk(self, event):
        startConfig = self._startConfigField.GetValue()
        startNote = noteToNoteString(self._startNoteField.GetValue())
        videoDir = self._videoDirField.GetValue()
        configDir = self._configDirField.GetValue()
        self._configurationClass.setStartupConfig(startConfig, startNote, videoDir, configDir)

        resX = self._resolutionXField.GetValue()
        resY = self._resolutionYField.GetValue()
        fullscreenMode = self._fullscreenField.GetValue()
        isAutoPos = self._autopositionField.GetValue()
        posX = self._positionXField.GetValue()
        posY = self._positionYField.GetValue()
        self._configurationClass.setScreenConfig(resX, resY, fullscreenMode, isAutoPos, posX, posY)


        midiBcast = self._playerMidiBcastOnField.GetValue()
        midiAddress = self._playerBindNameField.GetValue()
        midiPort = self._playerMidiPortField.GetValue()
        webAddress = self._playerWebBindNameField.GetValue()
        webPort = self._playerWebPortField.GetValue()
        self._configurationClass.setServerConfig(midiBcast, midiAddress, midiPort, webAddress, webPort)
        xmlString = self._configurationClass.getXmlString()
        self._sendConfigCallback(xmlString)
        wx.MessageBox('You must restart Player to make sure all changes to take effect!', 'Info', wx.OK | wx.ICON_INFORMATION) #@UndefinedVariable
        self.Destroy()

    def _onCancel(self, event):
        self.Destroy()
