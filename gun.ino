#include <Arduino.h>
#include <IRremote.hpp>

const int switchPin = 2;
int buttonState = 0;
int shoot = 0;
int check = 0;
unsigned long current = 0;
unsigned long start = 0;
unsigned long receivedData = 0;


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

struct Packet readings = {170, 2,  4,  0,  0,  0,  0,  0,  0,  0, 0,  0, 170 ^ 2 ^ 4 ^ 1};
struct Packet ACK =   {170, 0,  2,  0,  0,  0,  0,  0,  0,  0, 0,  0, 170 ^ 0 ^ 2};

void setup() {
  Serial.begin(115200);


  IrSender.begin(4);
}

void loop () {
  uint8_t temp = 0;
  buttonState = digitalRead(switchPin);
  uint8_t data[20];
  size_t len = 0;

  if (Serial.available()) {
    len = Serial.readBytes(data, 20);
    receivedData = millis();
  }
  if (len > 0) {

  
    if (data[0] == 170) {

      Serial.write((uint8_t *) &ACK, sizeof(ACK));
    }
    else if (data[0]== 171) {
      check = 1;
    }
  }

  if (buttonState == HIGH && check == 1) {
    IrSender.sendNEC(0xFF91, 0x91, 0);
    shoot = 1;
    //Serial.println(shoot);
    readings.rawX = 1;
    Serial.write((uint8_t *) &readings, sizeof(readings));
  }

  //timeout functions
  //if (current - receivedData > 3000 && receivedData != 0)
  // Serial.write((uint8_t *) &readings, sizeof(readings));

  // }

}
