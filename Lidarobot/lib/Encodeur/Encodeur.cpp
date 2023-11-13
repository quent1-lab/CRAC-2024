#include "Encodeur.h"

Encodeur::Encodeur(int pinA, int pinB, int pinC, int pinD) {
    encoderA.attachHalfQuad(pinA, pinB);
    encoderB.attachHalfQuad(pinC, pinD);
    oldPositionA = -999;
    oldPositionB = -999;
}

void Encodeur::init() {
  // Other initialization if needed
}

int Encodeur::readEncoderA() {
  return encoderA.getCount();
}

int Encodeur::readEncoderB() {
  return encoderB.getCount();
}

void Encodeur::reset() {
    encoderA.setCount(0);
    encoderB.setCount(0);
}

void Encodeur::odometrie(float* x, float* y, float* theta) {
  int delta = readEncoder() - oldPosition;
  // Other odometry calculations
  oldPosition = readEncoder();
  // Other operations related to odometry
}
