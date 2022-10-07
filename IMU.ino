#include "Wire.h"
#include "MPU6050.h"
#include "I2Cdev.h"

#define MAXLENGTH 20

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

struct Packet readings = {170, 4,  4,  0,  0,  0,  0,  0,  0,  0, 0,  0, 0};
struct Packet ACK =   {170, 0,  2,  0,  0,  0,  0,  0,  0,  0, 0,  0, 170 ^ 0 ^ 2};

uint8_t seq = 0;
int packetCount;
unsigned long current = 0;
unsigned long start = 0;
unsigned long receivedData = 0;
int establishConnection = 0;
int check = 0;

MPU6050 mpu;
int ax, ay, az;
int gx, gy, gz;
int rawax, raway, rawaz;
int rawgx, rawgy, rawgz;


void setup()
{
  Serial.begin(115200);
  Wire.begin();
  mpu.initialize();
  start = millis();
  receivedData = 0;

}

void readData() {
  int i;
  rawax = 0;
  raway = 0;
  rawaz = 0;
  rawgx = 0;
  rawgy = 0;
  rawgz = 0;
  for (i = 0; i < 10; i++)
  {
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
    ax = map(ax, -35000, 35000, 0, 255 ); // X axis data
    ay = map(ay, -35000, 35000, 0, 255); // Y axis data
    az = map(az, -35000, 35000, 0, 255);  // Z axis data
    gx = map(gx, -35000, 35000, 0, 255); // X gero data
    gy = map(gy, -35000, 35000, 0, 255); // Y gero data
    gz = map(gz, -35000, 35000, 0, 255);  // Z gero data
    rawax += ax;
    raway += ay;
    rawaz += az;
    rawgx += gx;
    rawgy += gy;
    rawgz += gz;
  }
  readings.seq = seq;
  seq = (seq + 1);
  uint8_t *ptr = (uint8_t*)&readings;
  uint8_t *endptr = (uint8_t*)&readings + 19;
  int checksum = 0;

  readings.rawX = rawax / 10;
  readings.rawY = raway / 10;
  readings.rawZ = rawaz / 10;
  readings.accX = rawgx / 10;
  readings.accY = rawgy / 10;
  readings.accZ = rawgz / 10;



  //calculate checksum by doing XOR operation on all values
  while (endptr > ptr) {
    checksum ^= *ptr;
    ptr++;
  }

  //Retrieve the last 8 bits
  checksum &= 0XFF;
  readings.checksum = checksum;


}


void (*restart)(void) = 0;

void clearBuffer() {
  uint8_t temp;
  while (Serial.available()) {
    temp = Serial.read();

  }

}



void loop() {
  unsigned long current = millis();
  uint8_t temp;
  uint8_t data[20];
  size_t len = 0;


    if (Serial.available()) {

      receivedData = millis();
      len = Serial.readBytes(data, 20);
    }

    if (len > 0) {
      if (data[0] == 170) {
        clearBuffer();
        Serial.write((uint8_t *) &ACK, sizeof(ACK));
        Serial.flush();
        //If device disconnects and is not reset
        establishConnection = 0;

      }
      else if (data[0] == 171) {
        clearBuffer();
        check = 1;
        establishConnection = 1;
      }
      else if (data[0] == 172) {
        restart();
      }


    }

  
  if (establishConnection == 1) {
    
    readData();
    Serial.write((uint8_t *) &readings, sizeof(readings));
    Serial.flush();

  }






}
