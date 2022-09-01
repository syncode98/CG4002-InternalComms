from bluepy import btle
from struct import *

MAC_Addresses=['D0:39:72:BF:C3:89']
devices = []

#preamble = "1010" 
#data
#checksum

#rint(len(preamble.encode("utf8"))) #https://stackoverflow.com/questions/4013230/how-many-bytes-does-a-string-have
#https://inc0x0.com/tcp-ip-packets-introduction/tcp-ip-packets-3-manually-create-and-send-raw-tcp-ip-packets/
#impacket

#Handshake
#disconnect
#setup protocol
#


class MyDelegate(btle.DefaultDelegate):
	def __init__(self):
		btle.DefaultDelegate.__init__(self)
		count = 0
	def handleNotification(self,cHandle,data):
		print(data)
		
		
try:
	first=btle.Peripheral()
	first.connect(MAC_Address)


	print("Device Connected")
except btle.BTLEDisconnectError:
	print("Device Disconnected") 



#https://www.cevinius.com/2016/08/17/serial-communication-with-the-bluno-using-bluetooth-le/
service = first.getServiceByUUID('dfb0')	
characteristic = service.getCharacteristics()[0]
first.withDelegate(MyDelegate())
threeWayHandshake()



data=""
while data!='exit':
	
	data=input("Enter your command:")
	send=data.encode()
	
	
	#send=bytes("Bye",'utf-8')
	characteristic.write(send)
	
	
	
first.disconnect()