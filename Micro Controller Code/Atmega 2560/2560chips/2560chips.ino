#include <Servo.h>

//pins
const int IN1 = 6;
const int IN2 = 7;
const int ENA = 5;
const int SERVO = 8;

Servo SteeringServo;

const int SteeringAngle = 27; // degrees

int CurrentAngle = 90;

void setup() {
  Serial.begin(9600);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENA, OUTPUT);
  SteeringServo.attach(SERVO);
}

void loop() {
  static const int maxLen = 64;
  static byte buffer[maxLen];
  static int index = 0;
  static bool started = false;
  static int packetLength = 0;

  while (Serial.available()) {
    byte incoming = Serial.read();

    if (!started) {
      if (incoming == 0xFF) {
        started = true;
        index = 0;
        packetLength = 0;
      }
      continue;
    }

    if (packetLength == 0) {
      packetLength = incoming; // next byte after start byte is length
      continue;
    }

    if (incoming == '\n') {
      // End of packet, process data
      if (index == packetLength) {
        for (int i = 0; i < index; i += 2) {
          byte id = buffer[i];
          byte val = buffer[i + 1];
          doStuff(id, val);
        }
      }
      // Reset for next packet
      started = false;
      index = 0;
      packetLength = 0;
    } else {
      if (index < maxLen) {
        buffer[index++] = incoming;
      } else {
        // buffer overflow, reset
        started = false;
        index = 0;
        packetLength = 0;
      }
    }
  }
}

void doStuff(byte id, byte val) {
  if (id == 1) { // Throttle control
    int speed = constrain(val, 0, 255);
    analogWrite(ENA, speed);
  }

  if (id == 2) { // Direction control
    if (val == 0) {
      digitalWrite(IN1, LOW);
      digitalWrite(IN2, HIGH);  // Reverse
    } else {
      digitalWrite(IN1, HIGH);
      digitalWrite(IN2, LOW);   // Forward
    }
  }

  if (id == 3) { // Steering
    CurrentAngle = map(val, 0, 255, 90 - SteeringAngle, 90 + SteeringAngle);
    SteeringServo.write(CurrentAngle);
  }
}
