'''
Created on 9. jan. 2012

@author: pcn
'''

class MidiControllers():
    (BankSelect,
     ModWheel,
     BreathController,
     FootController,
     PortamentoTime,
     DataEntryMSB,
     Volume,
     Balance,
     Controller8,
     Pan,
     ExpressionController,
     Controller11,
     Controller12,
     Controller13,
     Controller14,
     GeneralPurpose1,
     GeneralPurpose2,
     GeneralPurpose3,
     GeneralPurpose4,
     Controller19,
     Controller20,
     Controller21,
     Controller22,
     Controller23,
     Controller24,
     Controller25,
     Controller26,
     Controller27,
     Controller28,
     Controller29,
     Controller30,
     Controller31,
     BankSelectLSB,
     ModWheelLSB,
     BreathControllerLSB,
     FootControllerLSB,
     PortamentoTimeLSB,
     DataEntryLSB,
     VolumeLSB,
     BalanceLSB,
     Controller8LSB,
     PanLSB,
     ExpressionControllerLSB,
     Controller11LSB,
     Controller12LSB,
     Controller13LSB,
     Controller14LSB,
     GeneralPurpose1LSB,
     GeneralPurpose2LSB,
     GeneralPurpose3LSB,
     GeneralPurpose4LSB,
     Controller19LSB,
     Controller20LSB,
     Controller21LSB,
     Controller22LSB,
     Controller23LSB,
     Controller24LSB,
     Controller25LSB,
     Controller26LSB,
     Controller27LSB,
     Controller28LSB,
     Controller29LSB,
     Controller30LSB,
     Controller31LSB,
     Sustain,
     Portamento,
     Sustenuto,
     SoftPedal,
     Controller68,
     Hold2,
     Controller70,
     Controller71,
     Controller72,
     Controller73,
     Controller74,
     Controller75,
     Controller76,
     Controller77,
     Controller78,
     Controller79,
     GeneralPurpose5,
     TempChange,
     GeneralPurpose7,
     GeneralPurpose8,
     Controller84,
     Controller85,
     Controller86,
     Controller87,
     Controller88,
     Controller89,
     Controller90,
     ExtEffectsDepth,
     TremeloDepth,
     ChorusDepth,
     DetuneDepth,
     PhaserDepth,
     DataIncrement,
     DataDecrement,
     NonRegisteredParamLSB,
     NonRegisteredParamMSB,
     RegisteredParamLSB,
     RegisteredParamMSB,
     Controller102,
     Controller103,
     Controller104,
     Controller105,
     Controller106,
     Controller107,
     Controller108,
     Controller109,
     Controller110,
     Controller111,
     Controller112,
     Controller113,
     Controller114,
     Controller115,
     Controller116,
     Controller117,
     Controller118,
     Controller119,
     Controller120,
     ResetAllControllers,
     LocalControl,
     AllNotesOff,
     OmniModeOff,
     OmniModeOn,
     MonoModeOn,
     PolyModeOn
      ) = range(128)

    def getChoices(self):
        return [ "BankSelect",
                 "ModWheel",
                 "BreathController",
                 "FootController",
                 "PortamentoTime",
                 "DataEntryMSB",
                 "Volume",
                 "Balance",
                 "Controller8",
                 "Pan",
                 "ExpressionController",
                 "Controller11",
                 "Controller12",
                 "Controller13",
                 "Controller14",
                 "GeneralPurpose1",
                 "GeneralPurpose2",
                 "GeneralPurpose3",
                 "GeneralPurpose4",
                 "Controller19",
                 "Controller20",
                 "Controller21",
                 "Controller22",
                 "Controller23",
                 "Controller24",
                 "Controller25",
                 "Controller26",
                 "Controller27",
                 "Controller28",
                 "Controller29",
                 "Controller30",
                 "Controller31",
                 "BankSelectLSB",
                 "ModWheelLSB",
                 "BreathControllerLSB",
                 "FootControllerLSB",
                 "PortamentoTimeLSB",
                 "DataEntryLSB",
                 "VolumeLSB",
                 "BalanceLSB",
                 "Controller8LSB",
                 "PanLSB",
                 "ExpressionControllerLSB",
                 "Controller11LSB",
                 "Controller12LSB",
                 "Controller13LSB",
                 "Controller14LSB",
                 "GeneralPurpose1LSB",
                 "GeneralPurpose2LSB",
                 "GeneralPurpose3LSB",
                 "GeneralPurpose4LSB",
                 "Controller19LSB",
                 "Controller20LSB",
                 "Controller21LSB",
                 "Controller22LSB",
                 "Controller23LSB",
                 "Controller24LSB",
                 "Controller25LSB",
                 "Controller26LSB",
                 "Controller27LSB",
                 "Controller28LSB",
                 "Controller29LSB",
                 "Controller30LSB",
                 "Controller31LSB",
                 "Sustain",
                 "Portamento",
                 "Sustenuto",
                 "SoftPedal",
                 "Controller68",
                 "Hold2",
                 "Controller70",
                 "Controller71",
                 "Controller72",
                 "Controller73",
                 "Controller74",
                 "Controller75",
                 "Controller76",
                 "Controller77",
                 "Controller78",
                 "Controller79",
                 "GeneralPurpose5",
                 "TempChange",
                 "GeneralPurpose7",
                 "GeneralPurpose8",
                 "Controller84",
                 "Controller85",
                 "Controller86",
                 "Controller87",
                 "Controller88",
                 "Controller89",
                 "Controller90",
                 "ExtEffectsDepth",
                 "TremeloDepth",
                 "ChorusDepth",
                 "DetuneDepth",
                 "PhaserDepth",
                 "DataIncrement",
                 "DataDecrement",
                 "NonRegisteredParamLSB",
                 "NonRegisteredParamMSB",
                 "RegisteredParamLSB",
                 "RegisteredParamMSB",
                 "Controller102",
                 "Controller103",
                 "Controller104",
                 "Controller105",
                 "Controller106",
                 "Controller107",
                 "Controller108",
                 "Controller109",
                 "Controller110",
                 "Controller111",
                 "Controller112",
                 "Controller113",
                 "Controller114",
                 "Controller115",
                 "Controller116",
                 "Controller117",
                 "Controller118",
                 "Controller119",
                 "Controller120",
                 "ResetAllControllers",
                 "LocalControl",
                 "AllNotesOff",
                 "OmniModeOff",
                 "OmniModeOn",
                 "MonoModeOn",
                 "PolyModeOn"]

    def getName(self, typeId):
        choices = self.getChoices()
        for i in range(len(choices)):
            if(typeId == i):
                return choices[i]
        return "ModWheel"

    def getId(self, typeName):
        choices = self.getChoices()
        for i in range(len(choices)):
            name = choices[i]
            if(name == typeName):
                return i
        return -1
