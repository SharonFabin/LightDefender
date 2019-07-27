#include<Servo.h>

Servo serX;
Servo serY;
int xpos,ypos;

String tempModify;

void setup() {

  serX.attach(11);
  serY.attach(10);
  Serial.begin(9600);
  Serial.setTimeout(10);
  xpos=90;
  ypos=90;

  pinMode(12,OUTPUT);
  digitalWrite(12,HIGH);
}

void loop() {
  if(Serial.available()>0){
    tempModify = Serial.readString();
    serX.write(parseDataX(tempModify));
    serY.write(parseDataY(tempModify));
  }
}

int parseDataX(String data){
  data.remove(data.indexOf(":"));
  return data.toInt();
}

int parseDataY(String data){
  data.remove(0,data.indexOf(":") + 1);
  return data.toInt();

}