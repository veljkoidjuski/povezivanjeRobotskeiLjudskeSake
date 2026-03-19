#include<Servo.h>
Servo servo[5];
int angle[5] = { 0 };
int motori[5] = {3, 5, 6, 9, 10};
int c = 0;
String ulaz;
String nizUlaza[5] = { "" };

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(10);
  for (int i = 0; i < 5; i++)
  {
    servo[i].attach(motori[i]);
    servo[i].write(angle[i]);
  }
}

void loop() {
  while (Serial.available()>=16)
  {

    ulaz = Serial.readStringUntil('\n');
    
    for (int i = 0; i < 5; i++)
    {
      nizUlaza[i] = "";
      for (int j = 0; j < 3; j++)
        nizUlaza[i] += ulaz[3 * i + j];
    }

    for(int i = 0; i<5; i++)

    for (int i = 0; i < 5; i++) {
      angle[i] = nizUlaza[i].toInt();
      //Serial.println(angle[i]);
    }

   //while (Serial.available()) Serial.readString();
  }

  for (int i = 0; i < 5; i++)
    servo[i].write(angle[i]);
}
