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

    def countNumberOfTimeEffectTemplateUsed(self, effectConfigName):
        returnNumer = 0
#        for noteConfig in self._mediaPool:
#            if(noteConfig != None):
#                returnNumer += noteConfig.countNumberOfTimeEffectTemplateUsed(effectConfigName)
        return returnNumer

    def countNumberOfTimeFadeTemplateUsed(self, fadeConfigName):
        returnNumer = 0
#        for noteConfig in self._mediaPool:
#            if(noteConfig != None):
#                returnNumer += noteConfig.countNumberOfTimeFadeTemplateUsed(fadeConfigName)
        return returnNumer

    def renameEffectTemplateUsed(self, oldName, newName):
        pass
#        for noteConfig in self._mediaPool:
#            if(noteConfig != None):
#                noteConfig.renameEffectTemplateUsed(oldName, newName)

    def renameFadeTemplateUsed(self, oldName, newName):
        pass
#        for noteConfig in self._mediaPool:
#            if(noteConfig != None):
#                noteConfig.renameFadeTemplateUsed(oldName, newName)

    def verifyEffectTemplateUsed(self, effectConfigNameList):
        pass
#        for noteConfig in self._mediaPool:
#            if(noteConfig != None):
#                noteConfig.verifyEffectTemplateUsed(effectConfigNameList)

    def verifyFadeTemplateUsed(self, fadeConfigNameList):
        pass
#        for noteConfig in self._mediaPool:
#            if(noteConfig != None):
#                noteConfig.verifyFadeTemplateUsed(fadeConfigNameList)
