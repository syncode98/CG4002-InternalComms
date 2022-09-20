

//20 bytes worth of Data
//https://stackoverflow.com/questions/2692383/convert-struct-into-bytes
int sensor = 0;


typedef struct Packet {
  uint8_t header; 
  uint8_t device ;
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

struct Packet pack1 = {170, 5,  1,  0,  0,  0,  0,  0,  0,  0, 0,  0, 0};
struct Packet timeout = {170, 0,  4,  0,  0,  0,  0,  0,  0,  0, 0,  0, 170 ^ 4};
struct Packet ACK =   {170, 0,  2,  0,  0,  0,  0,  0,  0,  0, 0,  0, 170 ^ 2};

//This will simulate both the IMU sensor readings
//and the data from the IR sensors
int detectSensor(int* arr) {
  sensor = rand() %2;

  return sensor;


}
