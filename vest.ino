#include <Arduino.h>
#include <IRremote.hpp>
unsigned long current = 0;
unsigned long start = 0;
unsigned long receivedData = 0;
int check = 0;
int connection = 0;
int shot = 0;

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

struct Packet readings = {170, 3,  4,  1,  1,  0,  0,  0,  0,  0, 0,  0, 170^3^4^1^1};
struct Packet ACK =   {170, 0,  2,  0,  0,  0,  0,  0,  0,  0, 0,  0, 170 ^ 0 ^ 2};

const int RECV_PIN = 3;
//const int LED_PIN = 7;

//IRrecv irrecv(RECV_PIN);

//decode_results results;

bool isLedOn = false;

const unsigned long expectedHex = 0xFEA888;

void setup() {
  Serial.begin(115200);
  IrReceiver.begin(RECV_PIN);
  //  irrecv.enableIRIn();
  //  pinMode(LED_PIN, OUTPUT);
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

      Serial.write((uint8_t *) &ACK, sizeof(ACK));
    }
    else if (data[0] == 171) {

      if (connection == 0)
        connection = 1;

    }
  }

  if (IrReceiver.decode() && connection == 1) {
    Serial.write((uint8_t *) &readings, sizeof(readings));
   
  } IrReceiver.resume();

}
