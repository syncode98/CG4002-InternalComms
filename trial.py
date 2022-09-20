from bluepy import btle
from struct import *
import threading
import logging
import time
from struct import *
from multiprocessing import Pool,Lock,Process
from concurrent.futures import ProcessPoolExecutor,wait
#'d0:39:72:bf:c8:ff',
#'c4:be:84:20:19:1a',
#0xD03972BFC389

Addresses=['d0:39:72:bf:c8:ff','c4:be:84:20:19:1a','d0:39:72:bf:c3:89']
threads=[]
connected =[]

#The values to be sent as SYN and SYNACK packets are stored in a list
#before being converted to bytes
SYN_values = [170,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,171]          
SYN = bytes(SYN_values)
SYNACK_values = [170,0,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,169]
SYNACK = bytes(SYNACK_values)

class Device():
    def __init__(self,ADDRESS,peripheral,service,characteristic):
      
        self.connect = 0
        self.disconnect = 0
        self.ADDRESS = ADDRESS
        self.characteristic = characteristic
        self.peripheral = peripheral
        self.play = True
        self.service = service
        self.name = "device" + str(Addresses.index(ADDRESS))+":"
        self.start = 0
        self.count = 0

    def handShakeWithBeetle(self): 
            #Send the SYN PACKET and wait for 5 seconds to receive response
            print(self.name+":begin handshaking")
            print()             
            self.characteristic.write(SYN)
            
            while self.peripheral.waitForNotifications(5.0) == False:
                print(self.name + "Waiting for ACK")
                print()
                

            #If the self.start variable will change to 1 when the ACK packet is recevied
            #If it does, the SYNACK packet can be send to complete the handshaking
            if self.start == 0:
                print(self.name + "Unsuccesful")
                print()
            else:
                print(self.name + "Received ACK")
                print()
                self.characteristic.write(SYNACK)
    
        
    def searchForDevice(self):
        
        #while the device is disconnected, try to connect with it
        #Once its connected, change the value of self.disconnect to break out of the loop
        try:
            self.peripheral.connect(self.ADDRESS)
            self.disconnect = 0
        except Exception as e:
            print(e)

    #override the run function to be used for threads
    def run(self):
        
        while self.play == True:   
            try:
                if(self.disconnect == 1):
                    self.searchForDevice()
                        
                else:    
                    if(self.start == 0):                       
                        self.handShake()                        
                    else:                        
                        self.peripheral.waitForNotifications(1.0)

                    
            except Exception as e:
                print(repr(e))
                print(self.name +": disconnected")
                self.disconnect = 1
                self.start = 0          
                    

class MyDelegate(btle.DefaultDelegate):


        def __init__(self,beetle):
            btle.DefaultDelegate.__init__(self)
            self.beetle=beetle
            self.buffer = []
            self.sequence = 0
            self.missedNumbers = []
            self.startTime = 0
            self.track = 0
            self.play = True
            self.count = 0
            self.correct = 0
            self.start = 0
        def verifyData(self,recv):

            data = list(recv)
            try:
                if len(data) <20:
                    return False
                result = 0

                #calcualte the checksum for the data by doing XOR operation
                for x in data[:19]:
                    result^=x
                return (result == data[19])
            except Exception as e:
                print(e)
            return False

        def handleNotification(self,cHandle,data):

                try:

                    #print(self.beetle.name+ ": "+ str(data))
                    #self.beetle.characteristic.write(SYNACK)

                    
                    self.count +=1
                    if(self.beetle.start == 0):
                        try:
                            if(self.verifyData(data) == 1 and data[0]==170 and data[2]==2 and data[19]==170^2): 
                                self.beetle.start = 1
                                self.start = time.time()


                        except Exception as e:
                            print(self.beetle.name + str(e))
                        

                    
                    else:

                        self.beetle.characteristic.write(SYNACK)
                        now = time.time()
                        if(len(data)==20):
                            recv = unpack('HHHHHH',data[4:16])

                        if(self.verifyData(data) == True):
                            self.correct +=1
                            recv = unpack('HHHHHH',data[4:16])
                            print(self.beetle.name + str(recv))
                        else:
                            print(self.beetle.name + "fragmented")
                            self.buffer.extend(list(data))
                            #print(self.buffer)
                            newIndex = 0
                            try:
                                newIndex = self.buffer.index(170)
                            except:
                                pass
                            required = newIndex + 20
                            newbuffer = []
                            
                            #This checks if there are lost packets in the buffer
                            if newIndex >0 and required>=20:
                                newbuffer = self.buffer[:required].copy()
                                self.buffer = self.buffer[newIndex:] 
                                #print(newbuffer)
                                #print(self.buffer)
                            

                            if len(self.buffer) > 50:
                                self.buffer =[]
                                print("exceeded")

                        print(self.beetle.name + "accuracy = "+ str(self.correct/self.count))
                        dataRate = (self.count * 20 / 1000 ) / ((now-self.start)/60)
                        print(self.beetle.name +"Data Rate=" + str(dataRate) )
                        print()
                        print()
                except Exception as e:
                    print(e)       

                
                    
                     
            


       
        
            
                
                  

def communicate(addr):
    
    connect =0
    attempts = 5

    while(attempts>0 and connect == 0):
        print("Trying to connect")
        try:
            currentBeetle=btle.Peripheral()
            currentBeetle.connect(addr)


            print("Device Connected")
            connect = 1
        except Exception as e:
            print(e)
            attempts-=1

    
    #acquiring the services and characteristics of the beetle
    try:
        service = currentBeetle.getServiceByUUID('dfb0')	
        characteristic = service.getCharacteristics()[0]
        beetle= Device(addr,currentBeetle,service,characteristic)
        currentBeetle.withDelegate(MyDelegate(beetle))
    except Exception as e:
        print(e)
      
       
    play = True
    while play == True:
        try:    
                if beetle.disconnect == 1:
                    try:
                        currentBeetle.connect(addr)
                        beetle.disconnect = 0
                        end = time.time()
                        print(beetle.name + str(end - start))
                    except Exception as e:
                        print(e)
                        

                else:
                    
                    while beetle.start == 0:
                        beetle.handShakeWithBeetle()
                            
                    
                        
                        
                    currentBeetle.waitForNotifications(1.0)
        except Exception as e:
            print(e)
            print(beetle.name + ":disconnected")
            beetle.disconnect = 1
            beetle.start = 0
            start = time.time()

            

       
    print("End of transmission")
    currentBeetle.disconnect()        


        
    

def main():

    try:
        with ProcessPoolExecutor(8) as ex:
            ex.map(communicate,Addresses)
        
        print("Finished communicating")
    except Exception as e:
        print("Failed")



#Protect the entry of the process
if __name__ == "__main__":
    main()


        