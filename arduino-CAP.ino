#include <string.h>


void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);

}

bool checkSum(char* data){
  
}

void loop() {
  // put your main code here, to run repeatedly:

  char data[10];
  int input[6];
  char recv[20];
  char inverted[16];
  if(Serial.available()){
    /*This code reads data sent from laptop
     * /
     * 
      */
      size_t lengthOfData = Serial.readBytes(data,10);
      for (int i=0;i<lengthOfData;i++){
        //Serial.println(data[i]);
      }
      Serial.print(data);

      
    }
  
}
