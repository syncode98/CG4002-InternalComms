
from bluepy import btle
from struct import *
import logging
import time
from struct import *
from multiprocessing import Pool, Lock, Process, Queue, Manager
from concurrent.futures import ProcessPoolExecutor, wait, ThreadPoolExecutor
import sys
import socket
import base64
import threading
import sshtunnel
import time
import sys
import json
from enum import Enum
import os
import paho.mqtt.client as mqtt

# #The values to be sent as SYN and SYNACK packets are stored in a list
# #before being converted to bytes
SYN_values = [170, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
SYN = bytes(SYN_values)
SYNACK_values = [171, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
SYNACK = bytes(SYNACK_values)
RESETACK = bytes(
    [172, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

Player = 1

shoot = True
count = 0
# create a queue to be passed to the relevant beetles
man = Manager()
queue = man.Queue()
mqttQueue = man.Queue()

Addresses = {
    #Player 1
    #'vest' :'c4:be:84:20:19:1a',
    #"gun": 'd0:39:72:bf:bf:9c',
    #'imu': 'd0:39:72:bf:c3:89'


    #Player2
    #'imu':'d0:39:72:bf:c8:e0',
    #'gun' : 'd0:39:72:bf:c8:ff',
    #'vest' : 'd0:39:72:bf:c3:b0'


}

devices = []
disconnected = []
handshaked = []

recv = list()
json_format_IMU = {"P": 1, "D": "IMU", "V": recv}
json_format_GUN = json.dumps({"P": 1, "D": "GUN", "V": 1})
json_format_SHIELD = json.dumps({"P": 1, "D": "VEST", "V": 1})


class Device():

    def __init__(self, ADDRESS, peripheral, service, characteristic, queue,
                 name,mqtt):

        self.disconnect = 0
        self.ADDRESS = ADDRESS
        self.characteristic = characteristic
        self.peripheral = peripheral
        self.play = True
        self.service = service
        self.name = name
        self.start = 0
        self.count = 0
        self.queue = queue
        self.sendCount = 1
        self.flag = False
        self.mqtt = mqtt
 

    def sendDataToClient(self, recv):
        #print(recv)
        if ('imu' in self.name):
            toSend = {'P': 1, 'D': 'IMU', "V":  recv}
            jsonFormat = json.dumps(toSend)
            #print(jsonFormat)
            self.queue.put(jsonFormat)

        elif ('gun' in self.name):
            #print('GUN:' + str(self.sendCount))
            #print(json_format_GUN)
            self.queue.put(json_format_GUN)

        else:
            #print('VEST:' + str(self.sendCount))
            #print(json_format_SHIELD)
            self.queue.put(json_format_SHIELD)
        self.sendCount+=1
    def reconnect(self):
        while self.disconnect == 1:
            try:
                self.peripheral.connect(self.ADDRESS)
                self.disconnect = 0

                print("Reconnected")
            except Exception as e:
                print(e)
                self.count += 1
                time.sleep(1)

    def handShakeWithBeetle(self):
        # Send the SYN PACKET and wait for 5 seconds to receive response
        print(self.name + ":begin handshaking")
        print()

        count = 0
        
        while (count < 5 and self.start == 0 and self.disconnect == 0):
            try:
                self.characteristic.write(SYN)
                self.peripheral.waitForNotifications(3.0)

                count += 1
                if (self.start == 0):
                    print(self.name + ":Unsuccesful Handshake")
                else:
                    print(self.name + ":Successful handshake")
                
                    
                    
            except Exception as e:
                print(e)
                count = 5
                
                

        while (count > 0 and self.start == 0):
            try:
                self.peripheral.disconnect()
                self.disconnect = 1
                count -= 1
                time.sleep(1)
            except Exception as e:
                count = 0


class MyDelegate(btle.DefaultDelegate):

    def __init__(self, beetle):
        btle.DefaultDelegate.__init__(self)
        self.beetle = beetle
        self.buffer = []
        self.track = 0
        self.play = True
        self.countPacket = 0
        self.start = 1
        self.timer = 1
        self.fragmented = []
        self.header = 170
        self.type = 0
        self.retrPacket = 0
        self.seq = []
        self.sendData = []
        self.count = 0
        self.increase = False
        

    def verifyData(self, recv):

        data = recv
        try:
            if len(data) < 20:
                return False
            result = 0

            # calcualte the checksum for the data by doing XOR operation
            for x in data[:19]:
                result ^= x
            return (result == data[19] and data[0] == 170)

        except Exception as e:
            print(e)
        return False

    def sendACK(self, count):
        if ('gun' in self.beetle.name or 'vest' in self.beetle.name):
            SYNACK_values[1] = count
            
            #print(self.beetle.name + " Sending ACK NO:" + str(SYNACK_values[1]))
            self.beetle.characteristic.write(bytes(SYNACK_values))

    def shiftBuffer(self, newIndex):
        # clear the buffers and shift the data in self.buffer to ensure
        # that the next packet is positioned at the front of the buffer
        #print("Clearing buffers")

        remainingBuffer = self.buffer[newIndex:].copy()
        self.buffer.clear()
        self.buffer = remainingBuffer.copy()
        remainingBuffer.clear()


    def processData(self, data):
        print(data)
        recv = unpack('HHHHHH', data[3:15])
        packetNo = recv[0]
        print(packetNo)
        print(self.countPacket)
        if('imu' in self.beetle.name):
            print(recv)
            self.beetle.sendDataToClient(recv)
        
        #elif ((data[3] == self.countPacket and ('vest' or 'gun' in self.beetle.name))):
        #    if(data[3] not in self.sendData):
        #        self.sendData.append(data[3])
        elif ((packetNo == self.countPacket and ('vest' or 'gun' in self.beetle.name))):
            if(packetNo not in self.sendData):
                self.sendData.append(packetNo)        
                print(recv)
                self.beetle.sendDataToClient(recv)
                global shoot
                global count
                if('gun' in self.beetle.name):
                    shoot = True
                    #print(self.beetle.name+":Correct transmission:" + str(data[3]))
                    
                elif('vest' in self.beetle.name):
                    shoot = True
                    #print(self.beetle.name+":Correct transmission:" + str(data[3]))
                    # if(shoot ==True):
                    #     count+=1
                    #     shoot = False
                    #     print(self.beetle.name+":Correct transmission:" + str(count))
                    # else:
                    #     print("double")
                        
                        
                # if (self.count == 1):
                #     self.count = 0

                #     print("Retransmission successful")
                #     self.countPacket += 1
                #     self.sendACK(self.countPacket)

                #elif (self.countPacket % 10 != 0 and self.count == 0 or self.countPacket == 0):
                
                self.seq.append(self.countPacket)
                self.countPacket += 1
                #print(self.countPacket)
                self.sendACK(self.countPacket)
                if(self.countPacket == 255):
                    self.seq.clear()
                    self.countPacket = 0
                    self.sendData.clear()
            #else:
                #print(self.beetle.name +":" + str(data[3]) +":exists")
                #self.sendACK(data[3])
            #print(self.countPacket)
            #print(data[3])

            # else:
            #     print(self.countPacket)
            #     print(self.count)
            #     print(self.countPacket % 5)
            #     self.sendACK(self.countPacket-1)
            #     self.count = 1
            #     print("sending wrong synack")
                # self.countPacket+=1
                # self.seq.append(self.countPacket)
                # print(self.countPacket)
        else:
            if (packetNo in self.seq):
                #print(self.beetle.name+":Have already received the packet" + str(data[3]))
                self.sendACK(packetNo+1)
                #print(self.beetle.name+":Resending ACK packet" + str(data[3]))
        #     else:
        #         print("Missing:" + str(self.countPacket))

    def handleNotification(self, cHandle, data):

        try:
            #print(
            #    "------------------------------------------------------------------------------")
            #print(self.beetle.name)
            #print(data)
            # To handshake with the beetle
            if (self.beetle.start == 0):
                try:
                    self.countPacket = 0
                    SYNACK_values[1] = 0
                    global count
                    count = 0
                    self.sendData = []
                    #print(self.countPacket)
                    if (self.verifyData(data) == 1):
                        self.beetle.start = 1
                        self.start = time.time()
                        self.beetle.characteristic.write(SYNACK)
                        self.type = data[1]
                        self.retrPacket += 1
                except Exception as e:
                    print(self.beetle.name + str(e))

            else:
                
                #print(self.beetle.name + ":" + str(data))
                self.flag = True
                if (self.verifyData(list(data)) == True):
                    self.processData(data)
                    self.retrPacket += 1

                else:
                    print(self.beetle.name+":"+str(data))
                    # print(data[0])
                    # print(data[1])
                    # print(len(data))
                    if (len(self.buffer) == 0):
                        self.buffer.extend(data)
                        #print(self.buffer)
                        if (self.header in self.buffer):
                            #print(self.buffer)
                            # Find the header and shift it to the front of the buffer
                            while (self.buffer[0] != self.header):
                                #print("shifting")
                                self.buffer.pop(0)

                            if (self.retrPacket > 0):
                                # The previous packet is being discarded since its not retrievable
                                self.retrPacket -= 1
                            #print(self.buffer)
                            # print("------------------------------------------------------------------------------")
                        # Do not append any bytes if the header is not present

                    else:
                        self.buffer.extend(list(data))
                        #print("Extended Buffer:"+str(self.buffer))
                        if (len(self.buffer) >= 20):
                            # Start byte of the next packet
                            if (self.header in self.buffer[1:]):
                                # Find the index of the next packet
                                newIndex = self.buffer[1:].index(
                                    self.header) + 1
                            else:
                                newIndex = 20
                            # Obtain the fragmented data
                            fragmented = self.buffer[:newIndex].copy()
                            #print("Fragmented Data" + str(fragmented))

                            # Extract the data if it satisfies the checksum criteria
                            if (self.verifyData(fragmented)):
                                self.processData(bytes(fragmented))
                                recv = unpack(
                                        'HHHHHH', bytes(fragmented)[3:15])
                                # if ('imu' in self.beetle.name):
                                #     #recv = unpack(
                                #      #   'HHHHHH', bytes(fragmented)[3:15])
                                #     print(recv)
                                #     #self.beetle.sendDataToClient(recv)
                                # else:
                                #     #self.seq.append(fragmented[3])

                                #     #self.beetle.sendDataToClient(fragmented)
                                #     if (fragmented[3] == self.countPacket):
                                #         self.countPacket += 1
                                #         self.sendACK(self.countPacket)
                                #     #else:
                                #         #print(self.countPacket)
                                #         #print(fragmented[3])

                                self.retrPacket += 1
                            else:
                                self.retrPacket -= 1

                            fragmented.clear()
                            self.shiftBuffer(newIndex)

                        if (len(self.buffer) > 50):
                            #print("Length of Buffer is too large")
                            # print(self.buffer)
                            self.buffer.clear()

        except Exception as e:
            print(self.beetle.name + str(e))


def connect(name,mqtt):

    addr = Addresses[name]
    print(addr)
    print("start")
    connect = 0
    attempts = 5
    while (connect == 0):
        print(name + ":Trying to connect")
        try:
            currentBeetle = btle.Peripheral(addr)
            #currentBeetle.connect(addr)

            print("Device Connected")
            connect = 1
        except Exception as e:

            time.sleep(2)
            attempts -= 1

    # acquiring the services and characteristics of the beetle
    initialise = 0

    while (connect == 1 and initialise == 0):
        try:

            service = currentBeetle.getServiceByUUID('dfb0')
            characteristic = service.getCharacteristics()[0]
            beetle = Device(addr, currentBeetle, service, characteristic,
                            queue, name,mqtt)
            currentBeetle.withDelegate(MyDelegate(beetle))
            initialise = 1
            print("initialised")

        except Exception as e:
            print(e)
            initialise = 0
    devices.append(beetle)


def start(beetle):

    play = True
    count = 0
    print("start")
    while play == True:
        try:
            if beetle.disconnect == 1:
                try:
                    print("connecting")
                    beetle.peripheral.connect(beetle.ADDRESS)
                    beetle.disconnect = 0

                    print("Reconnected")
                    beetle.mqtt.publish(beetle.name,"RC")
                except Exception as e:
                    print(e)
                    # print("disconnected")
                    count += 1
                    time.sleep(1)

            else:

                while beetle.start == 0:
                    beetle.characteristic.write(SYN)
                    #beetle.handShakeWithBeetle()
                    if(beetle.peripheral.waitForNotifications(4.0)==True and beetle.start == 1):
                        print("Successful")
                    
                    else:
                        #print(beetle.characteristic.read())
                        print("Unsuccessful")
                        # beetle.start = 1
                        # beetle.characteristic.write(SYNACK)
                        # while True:
                        #     #beetle.peripheral.waitForNotifications(1.0)
                        #     print(beetle.characteristic.read())
                        

                if(beetle.peripheral.waitForNotifications(1.0) == False and 'imu' in beetle.name):
                    beetle.mqtt.publish(beetle.name,"DC")
                    #beetle.mqttQueue.put(beetle.name)              
                    # if('IMU' in beetle.name):
                    #      print("Loss")
                    #      count = 5



        except btle.BTLEDisconnectError as c:
            
            
            beetle.mqtt.publish(beetle.name,"DC")
            #beetle.mqttQueue.put(beetle.name)
            
            print(beetle.name + ":disconnected")
            beetle.disconnect = 1
            beetle.start = 0

        except Exception as e:
            
            print(e)

    print("End of transmission")
    beetle.peripheral.disconnect()


def firstHandShake(beetle):


    while beetle.start == 0:
        try:
            if beetle.disconnect == 1:
                try:
                    beetle.peripheral.connect(beetle.ADDRESS)
                    beetle.disconnect = 0

                    print("Reconnected")
                except Exception as e:
                    print(e)

                    time.sleep(1)

            else:

                while beetle.start == 0 and beetle.disconnect == 0:
                    beetle.characteristic.write(SYN)
                    #beetle.handShakeWithBeetle()
                    if(beetle.peripheral.waitForNotifications(4.0)==True and beetle.start == 1):
                        print("Successful")
                    
                    else:
                        print("Unsuccessful")


              

        except btle.BTLEDisconnectError as c:
            print(beetle.name + ":disconnected")
            beetle.disconnect = 1
            beetle.start = 0

        except Exception as e:
           
            print(e)
            time.sleep(2)

 
  

# connecting to ultra96
class UltraClient(threading.Thread):
    def __init__(self, user, passw,port,queue):
        self.ip_addr = '192.168.95.244'
        self.buff_size = 256
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.user = user
        self.passw = passw
        self.is_start = threading.Event()
        self.queue = queue
        self.port = port
        self.value='ULTRA96'

    # sshtunneling into sunfire
    def start_tunnel(self):
        # open tunnel to sunfire
        tunnel1 = sshtunnel.open_tunnel(
            # host for sunfire at port 22
            ('stu.comp.nus.edu.sg', 22),
            # ultra96 address
            remote_bind_address = ('192.168.95.244', 22),
            ssh_username = self.user,
            ssh_password = self.passw,
            block_on_close = False
            )
        tunnel1.start()
        
        print('[Tunnel Opened] Tunnel into Sunfire: ' + str(tunnel1.local_bind_port))

        # sshtunneling into ultra96
        tunnel2 = sshtunnel.open_tunnel(
            # ssh to ultra96
            ssh_address_or_host = ('localhost', tunnel1.local_bind_port),
            # local host
            remote_bind_address=('127.0.0.1', self.port),
            ssh_username = 'xilinx',
            ssh_password = 'xilinx',
            local_bind_address = ('127.0.0.1', self.port), #localhost to bind it to
            block_on_close = False
            )
        tunnel2.start()
        print('[Tunnel Opened] Tunnel into Xilinx')

        return tunnel2.local_bind_address

    # sending dummy data to ultra96
    def send(self, data):

        try:
            
            data_to_send = str(len(data)) + '_'+ data
            print(data_to_send)
            self.client.sendall(data_to_send.encode("utf8"))
        except Exception as e:
            pass
            #print(e)


def connectClient(ultra96):
    try:
        add = ultra96.start_tunnel()
        ultra96.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ultra96.client.connect(add)
    except Exception as e:
        print(e)
    print(f"[ULTRA96 CONNECTED] Connected to Ultra96")
    count = 0


def runClients(client):
    print("Send to Client")
    if(client.value == 'MQTT'):
        client.client.loop_start()
    else:
        while True:
            try:

                data = client.queue.get()
                #print(data)
                client.send(data)

                
            except ConnectionRefusedError:
                print("connection refused")
                client.is_start.clear()
            except IOError as e:
                print(str(e))
                # break
            except Exception as e:
                print(e)
                break

    #ultra96.client.close()
    print(client.value +":[CLOSED]")

class MQTTClient():
    def __init__(self, topic, client_name,queue):
        self.topic = topic 
        self.queue = queue
        self.client = mqtt.Client(client_name,clean_session=False)
        self.client.on_publish = on_publish
        self.client.connect('test.mosquitto.org')
        self.client.subscribe(self.topic)
        self.value = 'MQTT'
        


    def stop(self):
        self.client.unsubscribe()
        self.client.loop_stop()
        self.client.disconnect()


    def publish(self,device,status):
        MQTT_DATA = {
        "p1": {"imu": "","gun": "","vest": ""},
        "p2": {"imu": "","gun": "","vest": "" }
        }
        currentKey = 'p'+str(Player)
        if(status == 'DC'):
            MQTT_DATA[currentKey][device] = "No"
        
        message = json.dumps(MQTT_DATA)
        print(message)
        res,num = self.client.publish(self.topic, message, qos = 1)

#TESTING
def on_publish(client,userdata, msg ):
    print("Received Message: " + str(msg))  # Print a received msg
    pass
        
#def on_connect(client, userdata, flags, rc):
 #   print("Succesfully connected "+str(rc))
 #   topic = 'visualizer17'
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
  #  client.subscribe(topic)
    #client.publish(topic,"hello",qos = 1)

def main():

    if len(sys.argv) != 4:
        print("input sunfire username and password, port")
        sys.exit()

    user = sys.argv[1]
    passw = sys.argv[2]
    port = int(sys.argv[3])

    ultra96 = UltraClient(user, passw, port,queue)
 
    
    connectClient(ultra96)
    mqtt = MQTTClient("visualizer17","test",mqttQueue)

    for x in Addresses.keys():
        connect(x,mqtt)


    for device in devices:
       firstHandShake(device)



    clients = [ultra96,mqtt]
    try:


        with ThreadPoolExecutor(8) as ex:
            results = ex.map(start, devices)
            #res1 = ex.submit(sendDataClient(ultra96))
            res2 = ex.map(runClients,clients)
            #res = ex.submit(mqtt.client.loop_start())
    except Exception as e:
        print(repr(e))


if __name__ == '__main__':
    main()

# commands to find port sudo lsof -i -P -n | grep 8086
# sudo kill -i <pid>
