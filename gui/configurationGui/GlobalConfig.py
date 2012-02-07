'''
Created on 6. feb. 2012

@author: pcn
'''
from midi.MidiTiming import MidiTiming
from configuration.EffectSettings import EffectTemplates, FadeTemplates

class GlobalConfig(object):
    def __init__(self, configParent):
        self._configurationTree = configParent.addChildUnique("Global")
        self._configurationTree.addIntParameter("ResolutionX", 800)
        self._configurationTree.addIntParameter("ResolutionY", 600)
        self._internalResolutionX =  self._configurationTree.getValueFromPath("Global.ResolutionX")
        self._internalResolutionY =  self._configurationTree.getValueFromPath("Global.ResolutionY")

        self._midiTiming = MidiTiming()

        self._effectsConfiguration = EffectTemplates(self._configurationTree, self._midiTiming, self._internalResolutionX, self._internalResolutionY)
        self._mediaFadeConfiguration = FadeTemplates(self._configurationTree, self._midiTiming)

    def getEffectChoices(self):
        return self._effectsConfiguration.getChoices()

    def getFadeChoices(self):
        return self._mediaFadeConfiguration.getChoices()

