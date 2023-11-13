#ifndef Encodeur_h
#define Encodeur_h

#include <Arduino.h>
#include <ESP32Encoder.h>

class Encodeur {
  private:
    ESP32Encoder encoderD;
    ESP32Encoder encoderG;
    long oldPositionD;
    long oldPositionG;

  public:
    Encodeur(int pinA, int pinB,int pinC, int pinD);
    void init();
    int readEncoderD();
    int readEncoderG();
    void reset();
    void odometrie(float* x, float* y, float* theta);
};

#endif
