'''
Created on 6. feb. 2012

@author: pcn
'''

class MediaMixerConfig(object):
    def __init__(self, configParent):
        self._configurationTree = configParent.addChildUnique("MediaMixer")

    def getConfTree(self):
        return self._configurationTree

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print "MediaMixerConfig config is updated..."
        else:
            print "DEBUG: MediaMixerConfig.checkAndUpdateFromConfiguration NOT updated..."