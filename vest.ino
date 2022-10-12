#include <Arduino.h>
#include <IRremote.hpp>
int shoot = 0;
int check = 0;
unsigned long current = 0;
unsigned long start = 0;
unsigned long receivedData = 0;

int firstPacket = 0;
int startGame = 0;
int count = 0;
bool match = false;

typedef struct Packet {
  uint8_t header;
  uint8_t device;
  uint8_t type;
  uint8_t seq;
  uint16_t rawX;
  uint16_t rawY;
  uint16_t rawZ;
  uint16_t accX;
  uint16_t accY;
  uint16_t accZ;
  uint16_t pad1;
  uint8_t pad2;
  uint8_t checksum;

} packet;

struct Packet readings = {170, 3,  4,  0,  1,  0,  0,  0,  0,  0, 0,  0, 0};
struct Packet ACK =   {170, 0,  2,  0,  0,  0,  0,  0,  0,  0, 0,  0, 170 ^ 0 ^ 2};

const int RECV_PIN = 3;
//const int LED_PIN = 7;

//IRrecv irrecv(RECV_PIN);

//decode_results results;

bool isLedOn = false;

const unsigned long expectedHex = 0xFEA888;

void sendData(uint8_t seq) {
  readings.seq = seq;
  readings.checksum = (readings.header ^ readings.device ^ readings.type ^ readings.seq ^ 1);
  Serial.write((uint8_t *) &readings, sizeof(readings));


}
void resetValues() {

  shoot = 0;
  check = 0;
  current = 0;
  start = 0;
  receivedData = 0;
  firstPacket = 0;
  startGame = 0;
  count = 0;
  match = false;
}
void setup() {
  Serial.begin(115200);
  IrReceiver.begin(RECV_PIN);
}


void loop() {
  current = millis();
  uint8_t data[20];
  size_t len = 0;

  if (Serial.available()) {
    len = Serial.readBytes(data, 20);
    receivedData = millis();
  }
  if (len > 0) {


    if (data[0] == 170) {
      resetValues();
      Serial.write((uint8_t *) &ACK, sizeof(ACK));
    }

    else if (data[0] == 171) {

      check = 1;

      if (startGame == 1) {

        if (data[1] == shoot) {
          match = true;

        }
        else {
          match = false;

        }


      }
      else {
        startGame = 1;
      }

    }
  }
  
  if (IrReceiver.decode() && check == 1) {

    
    
    if (firstPacket == 0) {

      sendData(count);
      shoot++;
      firstPacket = 1;
    } else {
      if (match) {
        match = false;
        sendData(shoot);
      
        shoot++;
      }

    }  
    delay(100);
  } IrReceiver.resume();


  if (current - receivedData > 5000 && receivedData != 0 && match == false && firstPacket == 1 && len == 0)
  {
    int temp = shoot == 1 ? 0 : shoot - 1;
    sendData(temp);
    receivedData = millis();
  }
}
