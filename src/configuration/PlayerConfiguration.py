'''
Created on 16. feb. 2012

@author: pcn
'''

class PlayerConfiguration(object):
    def __init__(self, configHolder):
        self._playerConfigurationTree = configHolder

        self._playerConfigurationTree.addTextParameter("VideoDir", "C:\Users\pcn\Video") #TODO: change this
        self._playerConfigurationTree.addTextParameter("StartConfig", "PovRay_1.cfg") #TODO: change this to a default config.

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

    def getResolution(self):
        return (self._internalResolutionX, self._internalResolutionY)

    def getFullscreenMode(self):
        return self._fullscreenMode

    def isAutoPositionEnabled(self):
        return self._positionAutoMode

    def getPosition(self):
        return self._positionTuplet

    def getMidiServerUsesBroadcast(self):
        print "UseBcast: " + str(self._serverConfig.getValue("MidiBroadcast"))
        return self._serverConfig.getValue("MidiBroadcast")

    def getMidiServerAddress(self):
        print "MidiAdr: " + str(self._serverConfig.getValue("MidiBindAddress"))
        return self._serverConfig.getValue("MidiBindAddress")

    def getMidiServerPort(self):
        print "MidiPort: " + str(self._serverConfig.getValue("MidiPort"))
        return self._serverConfig.getValue("MidiPort")

    def getWebServerAddress(self):
        print "WebAdr: " + str(self._serverConfig.getValue("WebBindAddress"))
        return self._serverConfig.getValue("WebBindAddress")

    def getWebServerPort(self):
        print "WebPort: " + str(self._serverConfig.getValue("WebPort"))
        return self._serverConfig.getValue("WebPort")

    def getVideoDir(self):
        return self._playerConfigurationTree.getValue("VideoDir")

    def getStartConfig(self):
        return self._playerConfigurationTree.getValue("StartConfig")

