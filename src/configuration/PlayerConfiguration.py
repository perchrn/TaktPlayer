'''
Created on 16. feb. 2012

@author: pcn
'''

class PlayerConfiguration(object):
    def __init__(self, configHolder):
        self._playerConfigurationTree = configHolder

        self._playerConfigurationTree.addTextParameter("VideoDir", "")
        self._playerConfigurationTree.addTextParameter("StartConfig", "PovRay_1.cfg") #TODO: change this to a default config.

        self._screenConfig = self._playerConfigurationTree.addChildUnique("Screen")
        self._screenConfig.addIntParameter("ResolutionX", 800)
        self._screenConfig.addIntParameter("ResolutionY", 600)
        self._internalResolutionX =  self._screenConfig.getValue("ResolutionX")
        self._internalResolutionY =  self._screenConfig.getValue("ResolutionY")

        self._serverConfig = self._playerConfigurationTree.addChildUnique("Server")
        self._serverConfig.addTextParameter("MidiBindAddress", "0.0.0.0")
        self._serverConfig.addIntParameter("MidiPort", 2020)
        self._serverConfig.addTextParameter("WebBindAddress", "0.0.0.0")
        self._serverConfig.addIntParameter("WebPort", 2021)

    def getResolution(self):
        return (self._internalResolutionX, self._internalResolutionY)

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

