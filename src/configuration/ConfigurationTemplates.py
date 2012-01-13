'''
Created on 13. jan. 2012

@author: pcn
'''

class TemplateList(object):
    def __init__(self):
        pass

class ConfigurationTemplates(object):
    def __init__(self, configurationTree):
        self._configurationTree = configurationTree

    def _getConfiguration(self):
        self.loadMediaFromConfiguration()

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print "mediaPool config is updated..."
            self._getConfiguration()
            for mediaFile in self._mediaPool:
                if(mediaFile != None):
                    mediaFile.checkAndUpdateFromConfiguration()
            self._configurationTree.resetConfigurationUpdated()


