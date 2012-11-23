'''
Created on 23. nov. 2012

@author: pcn
'''
import wx

class ThreeChoiceMessageDialog(wx.Dialog): #@UndefinedVariable
    def __init__(self, parent, title, buttonPressedCallback, text, firstChoice, secondChoice, thirdChoice):
        super(ThreeChoiceMessageDialog, self).__init__(parent=parent, title=title, size=(420, 140))

        self._buttonPressedCallback = buttonPressedCallback

        dialogSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable
        self.SetBackgroundColour((180,180,180))

        textSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        infoText = wx.StaticText(self, wx.ID_ANY, text + "\n") #@UndefinedVariable
        textSizer.Add(infoText, 1, wx.ALL, 20) #@UndefinedVariable
        dialogSizer.Add(textSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable
        firstButton = wx.Button(self, wx.ID_ANY, firstChoice, size=(60,-1)) #@UndefinedVariable
        firstButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        secondButton = wx.Button(self, wx.ID_ANY, secondChoice, size=(60,-1)) #@UndefinedVariable
        secondButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        thirdButton = wx.Button(self, wx.ID_ANY, thirdChoice, size=(60,-1)) #@UndefinedVariable
        thirdButton.SetBackgroundColour(wx.Colour(210,210,210)) #@UndefinedVariable
        buttonsSizer.Add(firstButton, 1, wx.ALL, 5) #@UndefinedVariable
        buttonsSizer.Add(secondButton, 1, wx.ALL, 5) #@UndefinedVariable
        buttonsSizer.Add(thirdButton, 1, wx.ALL, 5) #@UndefinedVariable
        firstButton.Bind(wx.EVT_BUTTON, self._onFirst) #@UndefinedVariable
        secondButton.Bind(wx.EVT_BUTTON, self._onSecond) #@UndefinedVariable
        thirdButton.Bind(wx.EVT_BUTTON, self._onThird) #@UndefinedVariable
        dialogSizer.Add(buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self.SetSizer(dialogSizer)


    def _onFirst(self, event):
        self._buttonPressedCallback(1)
        self.Destroy()

    def _onSecond(self, event):
        self._buttonPressedCallback(2)
        self.Destroy()

    def _onThird(self, event):
        self._buttonPressedCallback(3)
        self.Destroy()

