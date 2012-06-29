'''
Created on 16. feb. 2012

@author: pcn
'''
from midi.MidiUtilities import noteStringToNoteNumber
from configuration.ConfigurationHolder import ConfigurationHolder

class PlayerConfiguration(object):
    def __init__(self, loadAndSave = True):
        self._playerConfigurationTree = ConfigurationHolder("TaktPlayer")
        self._playerConfigurationTree.setSelfclosingTags(['startup', 'screen', 'server'])
        if(loadAndSave == True):
            self._playerConfigurationTree.loadConfig("PlayerConfig.cfg")

        self._startupConfig = self._playerConfigurationTree.addChildUnique("Startup")
        self._startupConfig.addTextParameter("VideoDir", "video")
        self._startupConfig.addTextParameter("StartConfig", "Default.cfg")
        self._startupConfig.addTextParameter("StartNote", "0C") #"" "-1D", "0C", "2H" etc.

        self._screenConfig = self._playerConfigurationTree.addChildUnique("Screen")
        self._screenConfig.addIntParameter("ResolutionX", 800)
        self._screenConfig.addIntParameter("ResolutionY", 600)
        self._screenConfig.addTextParameter("FullscreenMode", "off") #on, off, auto
        self._internalResolutionX =  self._screenConfig.getValue("ResolutionX")
        self._internalResolutionY =  self._screenConfig.getValue("ResolutionY")
        self._fullscreenMode =  self._screenConfig.getValue("FullscreenMode")

        self._screenConfig.addTextParameter("Position", "auto") #auto, xpos,ypos, 0,0 etc.
        self._positionAutoMode = True
        self._positionTuplet = (-1, -1)
        positionString = self._screenConfig.getValue("Position")
        if(positionString.lower != "auto"):
            positionList = positionString.split(',')
            if(len(positionList) < 2):
                positionList = positionString.split('.')
            if(len(positionList) < 2):
                positionList = positionString.split(':')
            if(len(positionList) < 2):
                positionList = positionString.split('x')
            if(len(positionList) < 2):
                positionList = positionString.split('X')
            if(len(positionList) == 2):
                self._positionTuplet = (int(positionList[0]), int(positionList[1]))
                self._positionAutoMode = False

        self._serverConfig = self._playerConfigurationTree.addChildUnique("Server")
        self._serverConfig.addBoolParameter("MidiBroadcast", True)
        self._serverConfig.addTextParameter("MidiBindAddress", "0.0.0.0")
        self._serverConfig.addIntParameter("MidiPort", 2020)
        self._serverConfig.addTextParameter("WebBindAddress", "0.0.0.0")
        self._serverConfig.addIntParameter("WebPort", 2021)

        if(loadAndSave == True):
            self._playerConfigurationTree.saveConfigFile("PlayerConfig.cfg")

    def setFromXmlString(self, xmlString):
        self._playerConfigurationTree.setFromXmlString(xmlString)

    def saveConfig(self):
        self._playerConfigurationTree.saveConfigFile("PlayerConfig.cfg")

    def getXmlString(self):
        return self._playerConfigurationTree.getConfigurationXMLString()

    def setStartupConfig(self, startConfig, startNote, videoDir):
        self._startupConfig.setValue("StartConfig", startConfig)
        self._startupConfig.setValue("StartNote", startNote)
        self._startupConfig.setValue("VideoDir", videoDir)

    def setScreenConfig(self, resX, resY, fullscreenMode, isAutoPos, posX, posY):
        self._screenConfig.setValue("ResolutionX", resX)
        self._screenConfig.setValue("ResolutionY", resY)
        self._screenConfig.setValue("FullscreenMode", fullscreenMode)
        if(isAutoPos == True):
            self._screenConfig.setValue("Position", "auto")
        else:
            self._screenConfig.setValue("Position", str(posX) + "," + str(posY))
 
    def setServerConfig(self, midiBcast, midiAddress, midiPort, webAddress, webPort):
        self._serverConfig.setValue("MidiBroadcast", midiBcast)
        self._serverConfig.setValue("MidiBindAddress", midiAddress)
        self._serverConfig.setValue("MidiPort", midiPort)
        self._serverConfig.setValue("WebBindAddress", webAddress)
        self._serverConfig.setValue("WebPort", webPort)

    def getResolution(self):
        return (self._internalResolutionX, self._internalResolutionY)

    def getFullscreenMode(self):
        return self._fullscreenMode

    def isAutoPositionEnabled(self):
        return self._positionAutoMode

    def getPosition(self):
        return self._positionTuplet

    def getMidiServerUsesBroadcast(self):
#        print "UseBcast: " + str(self._serverConfig.getValue("MidiBroadcast"))
        return self._serverConfig.getValue("MidiBroadcast")

    def getMidiServerAddress(self):
#        print "MidiAdr: " + str(self._serverConfig.getValue("MidiBindAddress"))
        return self._serverConfig.getValue("MidiBindAddress")

    def getMidiServerPort(self):
#        print "MidiPort: " + str(self._serverConfig.getValue("MidiPort"))
        return self._serverConfig.getValue("MidiPort")

    def getWebServerAddress(self):
#        print "WebAdr: " + str(self._serverConfig.getValue("WebBindAddress"))
        return self._serverConfig.getValue("WebBindAddress")

    def getWebServerPort(self):
#        print "WebPort: " + str(self._serverConfig.getValue("WebPort"))
        return self._serverConfig.getValue("WebPort")

    def getVideoDir(self):
        return self._startupConfig.getValue("VideoDir")

    def getStartConfig(self):
        return self._startupConfig.getValue("StartConfig")

    def getStartNoteNumber(self):
        noteString = self._startupConfig.getValue("StartNote")
        if(noteString == None):
            return -1
        else:
            return noteStringToNoteNumber(noteString)
