void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);

}

void loop() {
  // put your main code here, to run repeatedly:

  char data[20];
  if(Serial.available()){
    /*This code reads data sent from laptop
     * /
     * 
      */
      size_t lengthOfData = Serial.readBytes(data,20);
      Serial.println();
      Serial.print(lengthOfData);
      Serial.println();
      for (int i=0;i<lengthOfData;i++){
        Serial.print(data[i]); 
      
      }
      int count = 0;
      count++;
      Serial.println();
      int remaining = 20 - lengthOfData;
      for (int i=lengthOfData;i<20;i++){
        data[i]='0';
      }
      Serial.print(data);
 
      
    }
  
}
