import array
import sys
from ola.ClientWrapper import ClientWrapper

def DmxCallback(state):
	wrapper.Stop()

data = array.array('B')
dataInputOk = False
for i in range(len(sys.argv) - 1):
    try:
        value = max(min(int(sys.argv[i+1]), 255), 0)
        data.append(value)
        dataInputOk = True
    except:
        pass
if(dataInputOk == False):
    data.append(24)
    data.append(255)
    data.append(0)
    data.append(255)
wrapper = ClientWrapper()
client = wrapper.Client()
client.SendDmx(1,data,DmxCallback)
wrapper.Run()
