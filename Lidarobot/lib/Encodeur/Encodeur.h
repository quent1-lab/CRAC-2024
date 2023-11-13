#ifndef Encodeur_h
#define Encodeur_h

#include <Arduino.h>
#include <ESP32Encoder.h>

class Encodeur {
  private:
    ESP32Encoder encoderA;
    ESP32Encoder encoderB;
    long oldPositionA;
    long oldPositionB;

  public:
    Encodeur(int pinA, int pinB,int pinC, int pinD);
    void init();
    int readEncoderA();
    int readEncoderB();
    void reset();
    void odometrie(float* x, float* y, float* theta);
};

#endif
