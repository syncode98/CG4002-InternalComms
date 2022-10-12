#include <Arduino.h>
#include <IRremote.hpp>

const int switchPin = 2;
int buttonState = 0;
int shoot = 0;
int check = 0;
unsigned long current = 0;
unsigned long start = 0;
unsigned long receivedData = 0;
unsigned long deb = 0;
int debounce = 0;
int firstPacket = 0;
int startGame = 0;
int count = 0;
bool match = false;
bool waiting = false;
uint8_t data[20];
 
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

struct Packet readings = {170, 2,  4,  0,  1,  0,  0,  0,  0,  0, 0,  0, 0};
struct Packet notSent = {0, 0,  0,  0,  0,  0,  0,  0,  0,  0, 0,  0, 0};
struct Packet ACK =   {170, 0,  2,  0,  0,  0,  0,  0,  0,  0, 0,  0, 170 ^ 2};

void setup() {
  Serial.begin(115200);


  IrSender.begin(4);
}

void sendData(uint8_t seq) {
  readings.seq = seq;
  readings.checksum = (readings.header ^ readings.device ^ readings.type ^ readings.seq ^ 1);
  Serial.write((uint8_t *) &readings, sizeof(readings));


}
void resetValues() {
  buttonState = 0;
  shoot = 0;
  check = 0;
  current = 0;
  start = 0;
  receivedData = 0;
  debounce = 0;
  firstPacket = 0;
  startGame = 0;
  count = 0;
  match = false;
}
void loop () {
  uint8_t temp = 0;
  buttonState = digitalRead(switchPin);
  //uint8_t data[20];
  size_t len = 0;
  current = millis();



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
          notSent.header = 170;
          notSent.device = shoot;
          notSent.type = data[1];
          match = false;

        }


      }
      else {
        startGame = 1;
      }

    }
    else {
      notSent.header = 182;
    }
  }
  if (check == 1) {

    if (buttonState == HIGH && millis() - deb > 200)
    {

      deb = millis();
      IrSender.sendNEC(0xFF91, 0x91, 0);
      
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



    }

  }


  //timeout functions
  //Resend packet if ACK is lost or data is lost
  if (current - receivedData > 3000 && receivedData != 0 && match == false && firstPacket == 1 && len == 0)
  {
    int temp = shoot == 1 ? 0 : shoot - 1;
    sendData(temp);
    receivedData = millis();
  }




}
