from ola.ClientWrapper import ClientWrapper

def DmxReceiveCallback(data):
	print data

wrapper = ClientWrapper()
client = wrapper.Client()
client.RegisterUniverse(1, client.REGISTER, DmxReceiveCallback)
wrapper.Run()

