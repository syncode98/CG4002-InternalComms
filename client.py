from asyncio import as_completed
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
from keyboard import send
import sshtunnel
import time
import sys
import json
from enum import Enum
import os

# #The values to be sent as SYN and SYNACK packets are stored in a list
# #before being converted to bytes
SYN_values = [170, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
SYN = bytes(SYN_values)
SYNACK_values = [171, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
SYNACK = bytes(SYNACK_values)
RESETACK = bytes(
    [172, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

#create a queue to be passed to the relevant beetles
man = Manager()
queue = man.Queue()

#Addresses of the beetles, along with the queues
Addresses = {
    'IMU1': ('d0:39:72:bf:c3:89', queue),
    "GUN": ('d0:39:72:bf:bf:9c', queue),
    'SHIELD': ('d0:39:72:bf:c3:b0', queue),
    'IMU2':('d0:39:72:bf:c8:e0',queue)

}

disconnected = []

class PlayerStat():

    def __init__(self, name):
        self.name = name
        self.hp = 100
        self.bullets = 100
        self.action = "NA"
        self.bullet_hit = "No"
        self.grenades = 1
        self.shield_health = 10
        self.shield_timer = 10
        self.shield_broke = "No"
        self.num_kills = 0
        self.num_shield = 0
        self.kills = 0
        self.killed = 0

    def reset(self):
        self.hp = 100
        self.bullets = 6
        self.action = "NA"
        self.bullet_hit = "No"
        self.grenades = 1
        self.shield_health = 10
        self.shield_timer = 10
        self.shield_broke = "No"
        self.num_kills = 0
        self.num_shield = 0


player1 = PlayerStat("player1")

recv = list()
json_format_IMU = {"Player":1,"IMU":recv,"bullet_hit":0,"shield_hit":0}
json_format_GUN = json.dumps({"Player":1,"IMU":recv,"bullet_hit":1,"shield_hit":0})
json_format_SHIELD  = json.dumps({"Player":1,"IMU":recv,"bullet_hit":0,"shield_hit":1})

class Device():

    def __init__(self, ADDRESS, peripheral, service, characteristic, queue,
                 name):

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

    def handShakeWithBeetle(self):
        #Send the SYN PACKET and wait for 5 seconds to receive response
        print(self.name + ":begin handshaking")
        print()

        count = 0

        while (count < 5 and self.start == 0):
            self.characteristic.write(SYN)
            self.peripheral.waitForNotifications(3.0)

            count += 1
            if (self.start == 0):
                print(self.name + ":Unsuccesful Handshake")
            else:
                print(self.name + ":Successful handshake")

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
        self.count = 0
        self.start = 0
        self.timer = 1

    def verifyData(self, recv):

        data = recv
        try:
            if len(data) < 20:
                return False
            result = 0

            #calcualte the checksum for the data by doing XOR operation
            for x in data[:19]:
                result ^= x
            return (result == data[19] and data[0] == 170)

        except Exception as e:
            print(e)
        return False

    def handleNotification(self, cHandle, data):

        try:

            self.count += 1

            #To handshake with the beetle
            if (self.beetle.start == 0):
                try:
                    if (self.verifyData(data) == 1 and data[0] == 170
                            and data[2] == 2 and data[19] == 170 ^ 2):
                        self.beetle.start = 1
                        self.start = time.time()
                        self.beetle.characteristic.write(SYNACK)

                except Exception as e:
                    print(self.beetle.name + str(e))
            
            else:
                if (self.beetle.name == 'GUN' or self.beetle.name == 'VEST'  ):
                    SYNACK_values[1] += 1


                    
                self.beetle.characteristic.write(bytes(SYNACK_values))

                if (self.verifyData(list(data)) == True):

                    recv = unpack('HHHHHH', data[4:16])
                    #print(recv)
                    if (self.beetle.name == 'IMU2' or self.beetle.name == 'IMU'):
                        #include all 6 points

                        #data_JSON = json.dumps()
                        #send = ["IMU"]
                        toSend = {'Player':1,'IMU':recv,'Player':1,"bullet_hit":0,"shield_hit":0}
                        jsonFormat = json.dumps(toSend)
                        
                        self.beetle.queue.put(jsonFormat)
                        #self.beetle.queue.put(
                        #    str(self.beetle.name) + ":" + str(recv))
                            
                    elif (self.beetle.name == 'GUN'):
                        #self.beetle.queue.put(str(self.beetle.name) + ":1")
                        self.beetle.queue.put(json_format_GUN)
                        
                        if (player1.hp > 0 and player1.bullets > 0):
                            player1.bullet_hit = "no"
                            player1.bullets -= 1
                            #data_JSON = json.dumps({self.beetle.name: 1,PlayerStat)
                            #self.beetle.queue.put(json.dumps(player1.__dict__))
                    else:
                        #only include the value
                        self.beetle.queue.put(json_format_SHIELD)
                        #self.beetle.queue.put(str(self.beetle.name) + ":1")
                        player1.hp -= 10
                        if (player1.hp > 0):
                            player1.bullet_hit = "yes"
                            #data_JSON = json.dumps({self.beetle.name: 1,'Bullets'})
                            #self.beetle.queue.put(json.dumps(player1.__dict__))
                        else:
                            player1.killed += 1
                            player1.reset()
                            #self.beetle.queue.put(json.dumps(player1.__dict__))

                else:
                    print(self.buffer)
                    print(data)
                    self.buffer.extend(list(data))
                    newIndex = 0
                    try:
                        newIndex = self.buffer.index(170)
                    except:
                        pass

                    if newIndex > -1:
                       
                        required = newIndex + 20
                        
                    else:
                        required = 0
                    
                    newbuffer = []
                    currentLength = len(self.buffer)

                    if currentLength >= required and required >= 19:
                        while(self.buffer[0]!= 170):
                            self.buffer.pop(0)
                        #print(self.buffer)
                        newbuffer.append(self.buffer.pop(0))
                        while(self.buffer[0]!= 170):
                            newbuffer.append(self.buffer.pop(0))
                        print("Remaining buffer" + str(self.buffer))
                        print("Retrieved" + str(newbuffer))
                    #     if (self.verifyData(newBuffer)):
                    #         recv = unpack('HHHHHH', bytes(newBuffer[4:16]))
                    #         print(recv)
                    #         print(self.buffer)
                    #         #self.beetle.queue.put({self.beetle.name: recv})
                    #         #print(self.beetle.name + ":" str(recv))


        except Exception as e:
            print(self.beetle.name + str(e))


def connect(name):

    addr = Addresses[name][0]

    print("start")
    connect = 0
    attempts = 5
    while (connect == 0):
        print(name +":Trying to connect")
        try:
            currentBeetle = btle.Peripheral()
            currentBeetle.connect(addr)

            #print("Device Connected")
            connect = 1
        except Exception as e:
            #print(e)
            time.sleep(3)
            attempts -= 1

    #acquiring the services and characteristics of the beetle
    initialise = 0

    while (connect == 1 and initialise == 0):
        try:

            service = currentBeetle.getServiceByUUID('dfb0')
            characteristic = service.getCharacteristics()[0]
            beetle = Device(addr, currentBeetle, service, characteristic,
                            queue, name)
            currentBeetle.withDelegate(MyDelegate(beetle))
            initialise = 1
        except Exception as e:
            #print(e)
            initialise = 0
    if (connect == 1 and initialise == 1):
        play = True
        count = 0
        while play == True:
            try:
                if beetle.disconnect == 1:
                    try:
                        currentBeetle.connect(addr)
                        beetle.disconnect = 0

                        print("Reconnected")
                    except Exception as e:
                        print("disconnected")
                        count+=1
                        time.sleep(1)

                else:

                    while beetle.start == 0 and beetle.disconnect == 0:
                        beetle.handShakeWithBeetle()

                    currentBeetle.waitForNotifications(1.0)

            except btle.BTLEDisconnectError as c:
                print(beetle.name + ":disconnected")
                beetle.disconnect = 1
                beetle.start = 0

            except Exception as e:
                print(1)
                print(e)

        print("End of transmission")
        currentBeetle.disconnect()


# connecting to ultra96
class UltraClient():

    def __init__(self, user, passw, queue):
        self.ip_addr = '192.168.95.244'
        self.buff_size = 256
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.user = user
        self.passw = passw
        #self.is_start = threading.Event()
        self.queue = queue

    # sshtunneling into sunfire
    def start_tunnel(self):
        # open tunnel to sunfire
        tunnel1 = sshtunnel.open_tunnel(
            # host for sunfire at port 22
            ('stu.comp.nus.edu.sg', 22),
            # ultra96 address
            remote_bind_address=('192.168.95.244', 22),
            ssh_username=self.user,
            ssh_password=self.passw,
            block_on_close=False)
        tunnel1.start()

        print('[Tunnel Opened] Tunnel into Sunfire: ' +
              str(tunnel1.local_bind_port))

        # sshtunneling into ultra96
        tunnel2 = sshtunnel.open_tunnel(
            # ssh to ultra96
            ssh_address_or_host=('localhost', tunnel1.local_bind_port),
            # local host
            remote_bind_address=('127.0.0.1', 8086),
            ssh_username='xilinx',
            ssh_password='xilinx',
            local_bind_address=('127.0.0.1', 8086),  #localhost to bind it to
            block_on_close=False)
        tunnel2.start()
        print('[Tunnel Opened] Tunnel into Xilinx')

        return tunnel2.local_bind_address

    # sending dummy data to ultra96
    def send(self, data):
        self.client.sendall(data)
        #self.client.sendall(data.encode("utf8"))


def connectClient(ultra96):
    try:
        add = ultra96.start_tunnel()
        ultra96.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ultra96.client.connect(add)
    except Exception as e:
        print(e)
    print(f"[ULTRA96 CONNECTED] Connected to Ultra96")
    count = 0


def sendDataClient(ultra96):
    print("Send to Client")
    while True:
        try:

            data = ultra96.queue.get()
            #print(data)
            result = json.loads(data)
            #print(result)
            #print(result['bullet_hit'])
            #ultra96.send(data)

            #time.sleep(5)
        except ConnectionRefusedError:
            ultra96.is_start.clear()
            print("connection refused")
        except Exception as e:
            print(e)
            break

    ultra96.client.close()
    print("[CLOSED]")


def main():

    # if len(sys.argv) != 3:
    #     print("input sunfire username and password")
    #     sys.exit()
    
    # user = sys.argv[1]
    # passw = sys.argv[2]

    # ultra96 = UltraClient(user, passw,queue)
    # connectClient(ultra96)
    #connect('IMU2')
    # try:
    #     add = ultra96.start_tunnel()
    #     ultra96.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     ultra96.client.connect(add)
    # except Exception as e:
    #     print(e)
    
    try:
        client = UltraClient("trial", "trial", queue)

        with ThreadPoolExecutor() as ex:
            results = ex.map(connect, Addresses.keys())
            res = ex.submit(sendDataClient, client)

            # results = [
            #     ex.submit(connect, device) for device in Addresses.keys()
            # ]
            # res = ex.submit(connectClient, client)
            # for fut in as_completed(results):
            #     task = fut.result()

        print("Finished communicating")
        
    except Exception as e:
        print(repr(e))


if __name__ == '__main__':
    main()
