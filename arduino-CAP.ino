
#include <string.h>
#include <time.h>
#include "Header.h"

#define MAXLENGTH 20


uint8_t seq = 0;
int packetCount;
unsigned long current = 0;
unsigned long receivedData = 0;
int fragment = 5;
int handshake = 0;
int handshakecount = 0;
int packets = 0;
int recvSYN = 0;
int count = 0;
int attempt = 0;


void setup() {


  // put your setup code here, to run once:
  Serial.begin(115200);
  current = 0;
  receivedData = 0;
  handshake = 0;
  seq = 0;
  packetCount = 0;
  recvSYN = 0;


}
void sendData(int timeout) {
  //https://arduino.stackexchange.com/questions/72138/send-structure-through-serial
  //calculate checkSum for the packet

  pack1.seq = seq;
  seq = (seq + 1);
  uint8_t *ptr = (uint8_t*)&pack1;
  uint8_t *endptr = (uint8_t*)&pack1 + MAXLENGTH - 1;
  int checksum = 0;


  pack1.rawX = rand() % 255;
  pack1.rawY= rand() % 255;
  pack1.rawZ = rand() % 255;
  pack1.accX = rand() % 255;
  pack1.accY = rand() % 255;
  pack1.accZ = rand() % 255;



  //calculate checksum by doing XOR operation on all values
  while (endptr > ptr) {
    checksum ^= *ptr;
    ptr++;
  }

  //Retrieve the last 8 bits
  checksum &= 0XFF;
  pack1.checksum = checksum;



  Serial.write((uint8_t *) &pack1, sizeof(pack1));


}

void loop() {
  unsigned long current = millis();
  uint8_t data[20];
  uint8_t temp;
  int index = 0;
  int check = 0;
  size_t len = 0;
  int sensor = 0;
  
  if (Serial.available()) {

    receivedData = millis();

    while (Serial.available()) {

       len = Serial.readBytes(data,20);
    }
  }
   
  
  delay(500);

  
  if (len>0) {


    
    if (data[0] == 170 && data[2] == 1 && data[19] == 171 ) {
      
      Serial.write((uint8_t *) &ACK, sizeof(ACK));
      Serial.flush();
    }
    else if (data[0] == 170 && data[2] == 3 && data[19] == 169) {
      sendData(0);
      Serial.flush();

    }



  }


  //timeout functions
  if (current - receivedData > 60000) {
    setup();

  }
  else if (current - receivedData > 10000) {

    Serial.write((uint8_t *) &timeout, sizeof(timeout));
    index++;
    receivedData = millis();

  }


}
