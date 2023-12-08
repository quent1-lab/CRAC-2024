#ifndef Moteur_h
#define Moteur_h

#include <Arduino.h>

class Moteur {
  private:
    int pinSens, pinPWM, ledc_channel;
    bool sens_actuel;
    int vitesse_actuelle, vitesse_consigne;
    int vitesse_max;
    unsigned long temps_mot;
    float coefficient;


  public:
    Moteur(int pinSens, int pinPWM, int ledc_channel);
    void init();
    void init(int vitesse_max);
    void init(int vitesse_max, float coefficient);
    void setVitesse(int vitesse);
    void setSens(bool sens);
    void smoothMoteur();
    void moteur();
};

#endif
