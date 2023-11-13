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
    int x;
    int y;
    int theta;
    float rayon;

  public:
    Encodeur(int pinA, int pinB,int pinC, int pinD);
    void init();
    void init(int x, int y, int theta);
    void change_position(int x, int y, int theta);
    int readEncoderD();
    int readEncoderG();
    void reset();
    void odometrie(float* x, float* y, float* theta);
    void print();
};

#endif
