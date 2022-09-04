from bluepy import btle
from struct import *
import threading


MAC_Addresses=['D0:39:72:BF:C3:89','D0:39:72:BF:C8:FF']
devices = []
MaxLen = 20
#preamble = "1010" 
#packetType
#packetID
#data
#checksum

#rint(len(preamble.encode("utf8"))) #https://stackoverflow.com/questions/4013230/how-many-bytes-does-a-string-have
#https://inc0x0.com/tcp-ip-packets-introduction/tcp-ip-packets-3-manually-create-and-send-raw-tcp-ip-packets/
#impacket

#Handshake
#disconnect
#setup protocol
#

#Send data from laptop to nodes only during two instances:Handshaking or sending NACK pakets
#Handshaking:10 00 00 00 00 00 00 00 00 00 
#Syn : 10 10 00 00 00 00 00 00 00 00 

#if its IMU, receive two packets at one instant 3 information
# initiate three threads and read data simultaneously
#

class MyDelegate(btle.DefaultDelegate):
	def __init__(self):
		btle.DefaultDelegate.__init__(self)
		count = 0
	def handleNotification(self,cHandle,data):
		print("Data received")
		print(data.decode())
		value = data.decode()
		binary = bin(int(value))
		inverted = ~binary
		print("Data received")
		print(binary)
		print(inverted)


		
		
		
		
try:
	first=btle.Peripheral()
	first.connect(MAC_Addresses[1])


	print("Device Connected")
except btle.BTLEDisconnectError:
	print("Device Disconnected") 



#https://www.cevinius.com/2016/08/17/serial-communication-with-the-bluno-using-bluetooth-le/
service = first.getServiceByUUID('dfb0')	
characteristic = service.getCharacteristics()[0]

first.withDelegate(MyDelegate())



while True:
	inta = input("")
	send=bytes("1010101001",'utf-8')
	#print(send)
	characteristic.write(send)

	
	
first.disconnect()

#Steps :
#1) Receive and send data from laptop tp arduino
#2)Setup SYN-ACK-SYNACK
#3)Setup sliding window
#4)Setup threading