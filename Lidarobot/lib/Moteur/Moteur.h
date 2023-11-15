#ifndef Moteur_h
#define Moteur_h

#include <Arduino.h>

class Moteur {
  private:
    int pinSens;
    int pinPWM;
    int ledc_channel;
    bool sens_actuel;
    int vitesse_actuelle;
    int vitesse_consigne;
    unsigned long temps_mot;

  public:
    Moteur(int pinSens, int pinPWM, int ledc_channel);
    void init();
    void setVitesse(int vitesse);
    void setSens(bool sens);
    void smoothMoteur();
    void moteur();
};

#endif
