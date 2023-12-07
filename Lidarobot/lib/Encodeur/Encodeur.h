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
    float x;
    float y;
    float theta;
    float rayon;
    int reduction;
    int resolution;

  public:
    Encodeur(int pinD_A, int pinD_B,int pinG_A, int pinG_B);
    void init();
    void init(float x, float y, float theta, float rayon);
    void init(float x, float y, float theta, float rayon, int reduction, int resolution);
    void change_position(float x, float y, float theta);
    int readEncoderD();
    int readEncoderG();
    void reset();
    void odometrie();
    void print(int countD,int countG);
    float get_x();
    float get_y();
    float get_theta();
    float get_theta_deg();
    void go_to(float x, float y, float theta);
    void go_to(float x, float y);
    void turn_to(float theta);
};

#endif
