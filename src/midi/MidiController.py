'''
Created on 9. jan. 2012

@author: pcn
'''

class Controllers():
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

def getLowControllerName(controllerId):
    if(controllerId == Controllers.BankSelect):
        return "BankSelect"
    elif(controllerId == Controllers.ModWheel):
        return "ModWheel"
    elif(controllerId == Controllers.BreathController):
        return "BreathController"
    elif(controllerId == Controllers.FootController):
        return "FootController"
    elif(controllerId == Controllers.PortamentoTime):
        return "PortamentoTime"
    elif(controllerId == Controllers.DataEntryMSB):
        return "DataEntryMSB"
    elif(controllerId == Controllers.Volume):
        return "Volume"
    elif(controllerId == Controllers.Balance):
        return "Balance"
    elif(controllerId == Controllers.Controller8):
        return "Controller9"
    elif(controllerId == Controllers.Pan):
        return "Pan"
    elif(controllerId == Controllers.ExpressionController):
        return "ExpressionController"
    elif(controllerId == Controllers.Controller11):
        return "Controller11"
    elif(controllerId == Controllers.Controller12):
        return "Controller12"
    elif(controllerId == Controllers.Controller13):
        return "Controller13"
    elif(controllerId == Controllers.Controller14):
        return "Controller14"
    elif(controllerId == Controllers.GeneralPurpose1):
        return "GeneralPurpose1"
    elif(controllerId == Controllers.GeneralPurpose2):
        return "GeneralPurpose2"
    elif(controllerId == Controllers.GeneralPurpose3):
        return "GeneralPurpose3"
    elif(controllerId == Controllers.GeneralPurpose4):
        return "GeneralPurpose4"
    elif(controllerId == Controllers.Controller19):
        return "Controller19"
    elif(controllerId == Controllers.Controller20):
        return "Controller20"
    elif(controllerId == Controllers.Controller21):
        return "Controller21"
    elif(controllerId == Controllers.Controller22):
        return "Controller22"
    elif(controllerId == Controllers.Controller23):
        return "Controller23"
    elif(controllerId == Controllers.Controller24):
        return "Controller24"
    elif(controllerId == Controllers.Controller25):
        return "Controller25"
    elif(controllerId == Controllers.Controller26):
        return "Controller26"
    elif(controllerId == Controllers.Controller27):
        return "Controller27"
    elif(controllerId == Controllers.Controller28):
        return "Controller28"
    elif(controllerId == Controllers.Controller29):
        return "Controller29"
    elif(controllerId == Controllers.Controller30):
        return "Controller30"
    elif(controllerId == Controllers.Controller31):
        return "Controller31"
    return None

def getHighControllerName(controllerId):
    if(controllerId == Controllers.Sustain):
        return "Sustain"
    elif(controllerId == Controllers.Portamento):
        return "Portamento"
    elif(controllerId == Controllers.Sustenuto):
        return "Sustenuto"
    elif(controllerId == Controllers.SoftPedal):
        return "SoftPedal"
    elif(controllerId == Controllers.Controller68):
        return "Controller68"
    elif(controllerId == Controllers.Hold2):
        return "Hold2"
    elif(controllerId == Controllers.Controller70):
        return "Controller70"
    elif(controllerId == Controllers.Controller71):
        return "Controller71"
    elif(controllerId == Controllers.Controller72):
        return "Controller72"
    elif(controllerId == Controllers.Controller73):
        return "Controller73"
    elif(controllerId == Controllers.Controller74):
        return "Controller74"
    elif(controllerId == Controllers.Controller75):
        return "Controller75"
    elif(controllerId == Controllers.Controller76):
        return "Controller76"
    elif(controllerId == Controllers.Controller77):
        return "Controller77"
    elif(controllerId == Controllers.Controller78):
        return "Controller78"
    elif(controllerId == Controllers.Controller79):
        return "Controller79"
    elif(controllerId == Controllers.GeneralPurpose5):
        return "GeneralPurpose5"
    elif(controllerId == Controllers.TempChange):
        return "TempChange"
    elif(controllerId == Controllers.GeneralPurpose7):
        return "XXXGeneralPurpose7"
    elif(controllerId == Controllers.GeneralPurpose8):
        return "GeneralPurpose8"
    elif(controllerId == Controllers.Controller84):
        return "Controller84"
    elif(controllerId == Controllers.Controller85):
        return "Controller85"
    elif(controllerId == Controllers.Controller86):
        return "Controller86"
    elif(controllerId == Controllers.Controller87):
        return "Controller87"
    elif(controllerId == Controllers.Controller88):
        return "Controller88"
    elif(controllerId == Controllers.Controller89):
        return "Controller89"
    elif(controllerId == Controllers.Controller90):
        return "Controller90"
    elif(controllerId == Controllers.ExtEffectsDepth):
        return "ExtEffectsDepth"
    elif(controllerId == Controllers.TremeloDepth):
        return "TremeloDepth"
    elif(controllerId == Controllers.ChorusDepth):
        return "ChorusDepth"
    elif(controllerId == Controllers.DetuneDepth):
        return "DetuneDepth"
    elif(controllerId == Controllers.PhaserDepth):
        return "PhaserDepth"
    elif(controllerId == Controllers.DataIncrement):
        return "DataIncrement"
    elif(controllerId == Controllers.DataDecrement):
        return "DataDecrement"
    elif(controllerId == Controllers.NonRegisteredParamLSB):
        return "NonRegisteredParamLSB"
    elif(controllerId == Controllers.NonRegisteredParamMSB):
        return "NonRegisteredParamMSB"
    elif(controllerId == Controllers.RegisteredParamLSB):
        return "RegisteredParamLSB"
    elif(controllerId == Controllers.RegisteredParamMSB):
        return "RegisteredParamMSB"
    elif(controllerId == Controllers.Controller102):
        return "Controller102"
    elif(controllerId == Controllers.Controller103):
        return "Controller103"
    elif(controllerId == Controllers.Controller104):
        return "Controller104"
    elif(controllerId == Controllers.Controller105):
        return "Controller105"
    elif(controllerId == Controllers.Controller106):
        return "Controller106"
    elif(controllerId == Controllers.Controller107):
        return "Controller107"
    elif(controllerId == Controllers.Controller108):
        return "Controller108"
    elif(controllerId == Controllers.Controller109):
        return "Controller109"
    elif(controllerId == Controllers.Controller110):
        return "Controller110"
    elif(controllerId == Controllers.Controller111):
        return "Controller111"
    elif(controllerId == Controllers.Controller112):
        return "Controller112"
    elif(controllerId == Controllers.Controller113):
        return "Controller113"
    elif(controllerId == Controllers.Controller114):
        return "Controller114"
    elif(controllerId == Controllers.Controller115):
        return "Controller115"
    elif(controllerId == Controllers.Controller116):
        return "Controller116"
    elif(controllerId == Controllers.Controller117):
        return "Controller117"
    elif(controllerId == Controllers.Controller118):
        return "Controller118"
    elif(controllerId == Controllers.Controller119):
        return "Controller119"
    elif(controllerId == Controllers.Controller120):
        return "Controller120"
    elif(controllerId == Controllers.ResetAllControllers):
        return "ResetAllControllers"
    elif(controllerId == Controllers.LocalControl):
        return "LocalControl"
    elif(controllerId == Controllers.AllNotesOff):
        return "AllNotesOff"
    elif(controllerId == Controllers.OmniModeOff):
        return "OmniModeOff"
    elif(controllerId == Controllers.OmniModeOn):
        return "OmniModeOn"
    elif(controllerId == Controllers.MonoModeOn):
        return "MonoModeOn"
    elif(controllerId == Controllers.PolyModeOn):
        return "PolyModeOn"
    return None

def getLowControllerId(controllerName):
    if(controllerName == "BankSelect"):
        return Controllers.BankSelect
    elif(controllerName == "ModWheel"):
        return Controllers.ModWheel
    elif(controllerName == "BreathController"):
        return Controllers.BreathController
    elif(controllerName == "FootController"):
        return Controllers.FootController
    elif(controllerName == "PortamentoTime"):
        return Controllers.PortamentoTime
    elif(controllerName == "DataEntryMSB"):
        return Controllers.DataEntryMSB
    elif(controllerName == "Volume"):
        return Controllers.Volume
    elif(controllerName == "Balance"):
        return Controllers.Balance
    elif(controllerName == "Controller8"):
        return Controllers.Controller9
    elif(controllerName == "Pan"):
        return Controllers.Pan
    elif(controllerName == "ExpressionController"):
        return Controllers.ExpressionController
    elif(controllerName == "Controller11"):
        return Controllers.Controller11
    elif(controllerName == "Controller12"):
        return Controllers.Controller12
    elif(controllerName == "Controller13"):
        return Controllers.Controller13
    elif(controllerName == "Controller14"):
        return Controllers.Controller14
    elif(controllerName == "GeneralPurpose1"):
        return Controllers.GeneralPurpose1
    elif(controllerName == "GeneralPurpose2"):
        return Controllers.GeneralPurpose2
    elif(controllerName == "GeneralPurpose3"):
        return Controllers.GeneralPurpose3
    elif(controllerName == "GeneralPurpose4"):
        return Controllers.GeneralPurpose4
    elif(controllerName == "Controller19"):
        return Controllers.Controller19
    elif(controllerName == "Controller20"):
        return Controllers.Controller20
    elif(controllerName == "Controller21"):
        return Controllers.Controller21
    elif(controllerName == "Controller22"):
        return Controllers.Controller22
    elif(controllerName == "Controller23"):
        return Controllers.Controller23
    elif(controllerName == "Controller24"):
        return Controllers.Controller24
    elif(controllerName == "Controller25"):
        return Controllers.Controller25
    elif(controllerName == "Controller26"):
        return Controllers.Controller26
    elif(controllerName == "Controller27"):
        return Controllers.Controller27
    elif(controllerName == "Controller28"):
        return Controllers.Controller28
    elif(controllerName == "Controller29"):
        return Controllers.Controller29
    elif(controllerName == "Controller30"):
        return Controllers.Controller30
    elif(controllerName == "Controller31"):
        return Controllers.Controller31
    elif(controllerName == "BankSelectLSB"):
        return Controllers.BankSelect
    elif(controllerName == "ModWheelLSB"):
        return Controllers.ModWheel
    elif(controllerName == "BreathControllerLSB"):
        return Controllers.BreathController
    elif(controllerName == "FootControllerLSB"):
        return Controllers.FootController
    elif(controllerName == "PortamentoTimeLSB"):
        return Controllers.PortamentoTime
    elif(controllerName == "DataEntryLSB"):
        return Controllers.DataEntryMSB
    elif(controllerName == "VolumeLSB"):
        return Controllers.Volume
    elif(controllerName == "BalanceLSB"):
        return Controllers.Balance
    elif(controllerName == "Controller8LSB"):
        return Controllers.Controller9
    elif(controllerName == "PanLSB"):
        return Controllers.Pan
    elif(controllerName == "ExpressionControllerLSB"):
        return Controllers.ExpressionController
    elif(controllerName == "Controller11LSB"):
        return Controllers.Controller12
    elif(controllerName == "Controller12LSB"):
        return Controllers.Controller13
    elif(controllerName == "Controller13LSB"):
        return Controllers.Controller14
    elif(controllerName == "Controller14LSB"):
        return Controllers.Controller15
    elif(controllerName == "GeneralPurpose1LSB"):
        return Controllers.GeneralPurpose1
    elif(controllerName == "GeneralPurpose2LSB"):
        return Controllers.GeneralPurpose2
    elif(controllerName == "GeneralPurpose3LSB"):
        return Controllers.GeneralPurpose3
    elif(controllerName == "GeneralPurpose4LSB"):
        return Controllers.GeneralPurpose4
    elif(controllerName == "Controller19LSB"):
        return Controllers.Controller19
    elif(controllerName == "Controller20LSB"):
        return Controllers.Controller20
    elif(controllerName == "Controller21LSB"):
        return Controllers.Controller21
    elif(controllerName == "Controller22LSB"):
        return Controllers.Controller22
    elif(controllerName == "Controller23LSB"):
        return Controllers.Controller23
    elif(controllerName == "Controller24LSB"):
        return Controllers.Controller24
    elif(controllerName == "Controller25LSB"):
        return Controllers.Controller25
    elif(controllerName == "Controller26LSB"):
        return Controllers.Controller26
    elif(controllerName == "Controller27LSB"):
        return Controllers.Controller27
    elif(controllerName == "Controller28LSB"):
        return Controllers.Controller28
    elif(controllerName == "Controller29LSB"):
        return Controllers.Controller29
    elif(controllerName == "Controller30LSB"):
        return Controllers.Controller30
    elif(controllerName == "Controller31LSB"):
        return Controllers.Controller31
    return None

def getHighControllerId(controllerName):
    if(controllerName == "Sustain"):
        return Controllers.Sustain
    elif(controllerName == "Portamento"):
        return Controllers.Portamento
    elif(controllerName == "Sustenuto"):
        return Controllers.Sustenuto
    elif(controllerName == "SoftPedal"):
        return Controllers.SoftPedal
    elif(controllerName == "Controller68"):
        return Controllers.Controller68
    elif(controllerName == "Hold2"):
        return Controllers.Hold2
    elif(controllerName == "Controller70"):
        return Controllers.Controller70
    elif(controllerName == "Controller71"):
        return Controllers.Controller71
    elif(controllerName == "Controller72"):
        return Controllers.Controller72
    elif(controllerName == "Controller73"):
        return Controllers.Controller73
    elif(controllerName == "Controller74"):
        return Controllers.Controller74
    elif(controllerName == "Controller75"):
        return Controllers.Controller75
    elif(controllerName == "Controller76"):
        return Controllers.Controller76
    elif(controllerName == "Controller77"):
        return Controllers.Controller77
    elif(controllerName == "Controller78"):
        return Controllers.Controller78
    elif(controllerName == "Controller79"):
        return Controllers.Controller79
    elif(controllerName == "GeneralPurpose5"):
        return Controllers.GeneralPurpose5
    elif(controllerName == "TempChange"):
        return Controllers.TempChange
    elif(controllerName == "GeneralPurpose7"):
        return Controllers.XXXGeneralPurpose7
    elif(controllerName == "GeneralPurpose8"):
        return Controllers.GeneralPurpose8
    elif(controllerName == "Controller84"):
        return Controllers.Controller84
    elif(controllerName == "Controller85"):
        return Controllers.Controller85
    elif(controllerName == "Controller86"):
        return Controllers.Controller86
    elif(controllerName == "Controller87"):
        return Controllers.Controller87
    elif(controllerName == "Controller88"):
        return Controllers.Controller88
    elif(controllerName == "Controller89"):
        return Controllers.Controller89
    elif(controllerName == "Controller90"):
        return Controllers.Controller90
    elif(controllerName == "ExtEffectsDepth"):
        return Controllers.ExtEffectsDepth
    elif(controllerName == "TremeloDepth"):
        return Controllers.TremeloDepth
    elif(controllerName == "ChorusDepth"):
        return Controllers.ChorusDepth
    elif(controllerName == "DetuneDepth"):
        return Controllers.DetuneDepth
    elif(controllerName == "PhaserDepth"):
        return Controllers.PhaserDepth
    elif(controllerName == "DataIncrement"):
        return Controllers.DataIncrement
    elif(controllerName == "DataDecrement"):
        return Controllers.DataDecrement
    elif(controllerName == "NonRegisteredParamLSB"):
        return Controllers.NonRegisteredParamLSB
    elif(controllerName == "NonRegisteredParamMSB"):
        return Controllers.NonRegisteredParamMSB
    elif(controllerName == "RegisteredParamLSB"):
        return Controllers.RegisteredParamLSB
    elif(controllerName == "RegisteredParamMSB"):
        return Controllers.RegisteredParamMSB
    elif(controllerName == "Controller102"):
        return Controllers.Controller102
    elif(controllerName == "Controller103"):
        return Controllers.Controller103
    elif(controllerName == "Controller104"):
        return Controllers.Controller104
    elif(controllerName == "Controller105"):
        return Controllers.Controller105
    elif(controllerName == "Controller106"):
        return Controllers.Controller106
    elif(controllerName == "Controller107"):
        return Controllers.Controller107
    elif(controllerName == "Controller108"):
        return Controllers.Controller108
    elif(controllerName == "Controller109"):
        return Controllers.Controller109
    elif(controllerName == "Controller110"):
        return Controllers.Controller110
    elif(controllerName == "Controller111"):
        return Controllers.Controller111
    elif(controllerName == "Controller112"):
        return Controllers.Controller112
    elif(controllerName == "Controller113"):
        return Controllers.Controller113
    elif(controllerName == "Controller114"):
        return Controllers.Controller114
    elif(controllerName == "Controller115"):
        return Controllers.Controller115
    elif(controllerName == "Controller116"):
        return Controllers.Controller116
    elif(controllerName == "Controller117"):
        return Controllers.Controller117
    elif(controllerName == "Controller118"):
        return Controllers.Controller118
    elif(controllerName == "Controller119"):
        return Controllers.Controller119
    elif(controllerName == "Controller120"):
        return Controllers.Controller120
    elif(controllerName == "ResetAllControllers"):
        return Controllers.ResetAllControllers
    elif(controllerName == "LocalControl"):
        return Controllers.LocalControl
    elif(controllerName == "AllNotesOff"):
        return Controllers.AllNotesOff
    elif(controllerName == "OmniModeOff"):
        return Controllers.OmniModeOff
    elif(controllerName == "OmniModeOn"):
        return Controllers.OmniModeOn
    elif(controllerName == "MonoModeOn"):
        return Controllers.MonoModeOn
    elif(controllerName == "PolyModeOn"):
        return Controllers.PolyModeOn
    return None

def getControllerName(controllerId):
    retVal = getLowControllerName(controllerId)
    if(retVal == None):
        retVal = getLowControllerName(controllerId - 32)
        if(retVal != None):
            if((controllerId - 32) == Controllers.DataEntryMSB):
                retVal = "DataEntryLSB"
            else:
                retVal = retVal + "LSB"
        else:
            retVal = getHighControllerName(controllerId)
    if(retVal == None):
        return "Unknown id: " + str(controllerId)
    else:
        return retVal

def getControllerId(controllerName):
    retVal = getLowControllerId(controllerName)
    if(retVal == None):
        retVal = getHighControllerId(controllerName)
    if(retVal == None):
        return -1
    else:
        return retVal

