#Utilise multiprocessing to communicate with servers
from bluepy import btle
from struct import *
from multiprocessing import Process, Queue, Manager
import sys
import socket
import threading
import sshtunnel
import sys
import json
import paho.mqtt.client as mqtt

# #The values to be sent as SYN and SYNACK packets are stored in a list
# #before being converted to bytes

SYN_values = [170, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
SYN = bytes(SYN_values)
ACK_values = [171, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
SYNACK  = bytes(ACK_values)
ACK = bytes(ACK_values)
RESETACK = bytes(
    [172, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

Player = 1
shoot = True
count = 0
# create a queue to be passed to the relevant beetles
man = Manager()
queue = Queue()
mqttQueue = Queue()
mqttQueueP = Queue()
# mqttQueue = man.Queue()

if Player == 1:
    Addresses = {
        #Player 1
        
        'vest' :'c4:be:84:20:19:1a',
        "gun": 'd0:39:72:bf:bf:9c',
        'imu': 'd0:39:72:bf:c3:89'
        
    }

else:

    Addresses = {
        #Player2
        'imu':'d0:39:72:bf:c8:e0',
        'gun' : 'd0:39:72:bf:c8:ff',
        'vest' : 'd0:39:72:bf:c3:b0'
    }
devices = []
disconnectDevices = []

recv = list()
json_format_IMU = {"P": Player, "D": "IMU", "V": recv}
json_format_GUN = json.dumps({"P": Player, "D": "GUN", "V": 1})
json_format_SHIELD = json.dumps({"P": Player, "D": "VEST", "V": 1})


class Device(Process):

    def __init__(self, ADDRESS,queue,
                 name):
        super().__init__()
        self.disconnect = 0
        self.ADDRESS = ADDRESS
        self.characteristic = None
        self.peripheral = None
        self.service = None
        self.name = name
        self.started = 0
        self.count = 0
        self.sendCount = 1
        self.flag = False
       

    def initialise(self):

        addr = self.ADDRESS
        print("start")
        connect = 0

        initialise = 0
        while initialise == 0:
            while (connect == 0):
                print("\r{} :Trying to Connect".format(self.name), end="")
                try:
                    currentBeetle = btle.Peripheral(addr)
                    self.peripheral = currentBeetle
                    print("Device Connected")
                    connect = 1
                except Exception as e:
                    pass

            # acquiring the services and characteristics of the beetle
            initialise = 0
            err = 1
            while (connect == 1 and initialise == 0):
                try:
                    self.service = currentBeetle.getServiceByUUID('dfb0')
                    self.characteristic = self.service.getCharacteristics()[0]
                    currentBeetle.withDelegate(MyDelegate(self))
                    initialise = 1
                    print("initialised")

                except btle.BTLEDisconnectError as c:
                    print("Disconnected before intialisations")
                    connect = 0
                except Exception as e:
                    print(e)                
                    initialise = 0
                       



    def sendDataToClient(self, recv):
        #print(recv)
        if ('imu' in self.name):
            toSend = {'P': Player, 'D': 'IMU', "V":  recv}
            jsonFormat = json.dumps(toSend)
            queue.put(jsonFormat)

        elif ('gun' in self.name):
            queue.put(json_format_GUN)

        else:
            queue.put(json_format_SHIELD)
        self.sendCount+=1

    def run(self):
     print("start")
     self.initialise()
     reset = 0
    
     while True:
        try:
            if self.disconnect == 1:
                try:

                    self.peripheral.connect(self.ADDRESS)
                    self.disconnect = 0


                    message = (self.name,"RC")
                    mqttQueue.put(message)  
                except Exception as e:
                    pass

            else:

                while self.started == 0:
                    self.characteristic.write(SYN)
                    if(self.peripheral.waitForNotifications(4.0)==True and self.started == 1):
                        print("Successful")                  
                    else:
                        print("Unsuccessful")
                if(self.peripheral.waitForNotifications(1.0) == False and 'imu' in self.name):
                    if(reset == 0):
                        message = (self.name,"DC")           
                        mqttQueue.put(message)  
                        reset = 1               
                    
        except btle.BTLEDisconnectError as c:
            
            self.started = 0
            message = (self.name,"DC")           
            mqttQueue.put(message)  
            print(self.name + ":disconnected")
            self.disconnect = 1
            reset = 0

        except Exception as e:
            if(reset == 0):
                print(e)
                reset = 1

    print("End of transmission")

class MyDelegate(btle.DefaultDelegate):

    def __init__(self, beetle):
        btle.DefaultDelegate.__init__(self)
        self.beetle = beetle
        self.buffer = []
        self.track = 0
        self.play = True
        self.countPacket = 0
        self.started = 1
        self.timer = 1
        self.fragmented = []
        self.header = 170
        self.type = 0
        self.retrPacket = 0
        self.seq = []
        self.sendData = []
        self.count = 0
        self.prev = 0
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
            ACK_values[1] = count
            
            print(self.beetle.name + " Sending ACK NO:" + str(ACK_values[1]))
            self.beetle.characteristic.write(bytes(ACK_values))




    def shiftBuffer(self, newIndex):
        # clear the buffers and shift the data in self.buffer to ensure
        # that the next packet is positioned at the front of the buffer
        #print("Clearing buffers")

        remainingBuffer = self.buffer[newIndex:].copy()
        self.buffer.clear()
        self.buffer = remainingBuffer.copy()
        remainingBuffer.clear()


    def processData(self, data):
        recv = unpack('HHHHHH', data[3:15])
        packetNo = recv[0]
        print("process Data")
        print(self.sendData)
        if('imu' in self.beetle.name):
            self.beetle.sendDataToClient(recv)
        
        elif ((packetNo == self.countPacket and ('vest' or 'gun' in self.beetle.name))):
            if(packetNo not in self.sendData):
                self.sendData.append(packetNo)        
                print(recv)
                self.beetle.sendDataToClient(recv)
                self.seq.append(self.countPacket)
                self.countPacket += 1

                self.sendACK(self.countPacket)
                if(self.countPacket >= 255):
                    self.seq.clear()
                    self.countPacket = 0
                    self.sendData.clear()
            else:
                print("Nope")
        else:
            if (packetNo in self.seq):
                print(self.beetle.name+":Have already received the packet" + str(data[3]))
                self.sendACK(packetNo+1)


    def handleNotification(self, cHandle, data):

        try:
            print(data)
            if('vest' in self.beetle.name or 'gun' in self.beetle.name):
                print(self.beetle.name)
                print(data)

            if (self.verifyData(list(data)) == True):

                if(self.beetle.started == 0):
                    self.beetle.started = 1
                    self.seq.clear()
                    self.sendData.clear()
                    self.countPacket = 0
                    print("Send synack")
                    self.beetle.characteristic.write(SYNACK)
                    self.fragmented.clear()
                else:

                    self.processData(data)
                    self.retrPacket += 1

            else:

                if (len(self.buffer) == 0):
                    self.buffer.extend(data)
                    if (self.header in self.buffer):

                        # Find the header and shift it to the front of the buffer
                        while (self.buffer[0] != self.header):
                            #print("shifting")
                            self.buffer.pop(0)

                        if (self.retrPacket > 0):

                            self.retrPacket -= 1

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
                            
                            if(self.beetle.started == 0):
                                print("Recovered Handshake")
                                self.beetle.started = 1
                                self.beetle.characteristic.write(SYNACK)
                                self.fragmented.clear()
                            else:

                                self.processData(bytes(fragmented))
                                recv = unpack(
                                        'HHHHHH', bytes(fragmented)[3:15])

                                self.retrPacket += 1
                        else:
                            self.retrPacket -= 1

                        fragmented.clear()
                        self.shiftBuffer(newIndex)

                    if (len(self.buffer) > 50):
                        self.buffer.clear()

        except Exception as e:
            print(self.beetle.name + str(e))




# connecting to ultra96
class UltraClient(Process):
    def __init__(self, user, passw,port,queue):
        super().__init__()
        self.ip_addr = '192.168.95.244'
        self.buff_size = 256
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.user = user
        self.passw = passw
        self.is_start = threading.Event()
        # self.queue = queue
        self.port = port
        self.value='ULTRA96'
        self.count = 0
    # sshtunneling into sunfire
    def start_tunnel(self):
        # open tunnel to sunfire
        tunnel1 = sshtunnel.open_tunnel(
            # host for sunfire at port 22
            ('sunfire.comp.nus.edu.sg', 22),
            #('stu.comp.nus.edu.sg', 22),
            # ultra96 address
            remote_bind_address = ('192.168.95.244', 22),
            ssh_username = self.user,
            ssh_password = self.passw,
            block_on_close = False
            )
        print("Tunnel initialised")
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
        tunnel2.start()
        print('[Tunnel Opened] Tunnel into Xilinx')

        return tunnel2.local_bind_address

      

    # sending dummy data to ultra96
    def send(self, data):

        try:
            
            data_to_send = str(len(data)) + '_'+ data
            self.client.sendall(data_to_send.encode("utf8"))

        except Exception as e:
            pass
           

    def run(self):

        self.connectClient()
        mqtt_p = MQTTClient("visualizer17","test")   
        mqtt_p.client.loop_start()

        
        print("Start server")
        while True:
            try:
                if mqttQueue.qsize() > 0:
                    msg = mqttQueue.get()
                    print("Should pulish: {}".format(msg))
                    mqttQueueP.put(msg)
                    mqtt_p.publish()
            except Exception as e:
                print("\033[31mProblem with MQTT at CLIENT: {}\033[0m".format(e))
            try:

                # data = self.queue.get()
                if queue.qsize() > 0:
                    data = queue.get()
                    self.send(data)

                
            except ConnectionRefusedError:
                print("connection refused")
                self.is_start.clear()
            except IOError as e:
                print(str(e))
                # break
            except Exception as e:
                print(e)
                break

    def connectClient(self):
        try:
            print("Starting Tunnel")
            add = self.start_tunnel()
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect(add)
        except Exception as e:
            print(e)
        print(f"[ULTRA96 CONNECTED] Connected to Ultra96")
        count = 0


class MQTTClient():
    def __init__(self, topic, client_name):
        self.topic = topic 
        self.client = mqtt.Client(client_name,clean_session=False)
        self.client.connect('test.mosquitto.org')
        self.client.subscribe(self.topic)
        self.value = 'MQTT'

    def stop(self):
        self.client.unsubscribe()
        self.client.loop_stop()
        self.client.disconnect()


    def publish(self):
        try:
            if mqttQueueP.qsize() > 0:
                device, status = mqttQueueP.get()
                print(device)
                print(status)
                currentKey = 'p'+str(Player)
                MQTT_DATA = {
                currentKey: {"imu": "","gun": "","vest": ""},
                }
                print(status)
                print("Send")
                if(status == 'DC'):
                    if(device not in disconnectDevices):
                        disconnectDevices.append(device)

                else:
                    disconnectDevices.remove(device)
                print(disconnectDevices)
                for dev in disconnectDevices:
                    MQTT_DATA[currentKey][dev] = 'no'
                        
                
                message = json.dumps(MQTT_DATA)
                print("\033[33m PUBLISHED TO MQTT: {}\033[0m".format(message))
                res,num = self.client.publish(self.topic, message, qos = 1)
                print(res)
        except Exception as e:
            print("mqtt error")
            print(e)

if __name__ == '__main__':

    if len(sys.argv) != 4:
        print("input sunfire username and password, port")
        sys.exit()

    user = sys.argv[1]
    passw = sys.argv[2]
    port = int(sys.argv[3])
    
    ultra96 = UltraClient(user, passw, port,queue)

    for dev in Addresses:
        device = Device(Addresses[dev],queue,dev)
        devices.append(device)
    print("Initialised Devices")

    
    try:
        
        for device in devices:
            print(device)
            device.start()
        ultra96.start()

    except Exception as e:
        print(repr(e))


