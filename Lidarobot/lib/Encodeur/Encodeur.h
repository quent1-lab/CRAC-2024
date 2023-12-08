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
    int get_resolution();
    int get_reduction();

    int x_to_step(float x);
    int y_to_step(float y);
    int theta_to_step(float theta);
};

#endif
