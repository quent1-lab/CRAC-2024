#include "Moteur.h"

Moteur::Moteur(int pinSens, int pinPWM, int ledc_channel)
{
    this->ledc_channel = ledc_channel;
    this->pinSens = pinSens;
    this->pinPWM = pinPWM;
    this->sens_actuel = false;
    this->vitesse_actuelle = 0;
    this->vitesse_consigne = 0;
    this->temps_mot = 0;
}

void Moteur::init()
{
    pinMode(pinSens, OUTPUT);
    ledcSetup(ledc_channel, 20000, 10);
    ledcAttachPin(pinPWM, ledc_channel);
    ledcWrite(ledc_channel, 0);
    // Other initialization if needed
}

void Moteur::setVitesse(int vitesse)
{
    vitesse_consigne = vitesse;
}

void Moteur::setSens(bool sens)
{
    sens_actuel = sens;
}

void Moteur::smoothMoteur()
{
    if (abs(vitesse_actuelle - vitesse_consigne) > 100)
    {
        if (millis() > temps_mot + 2)
        {
            if (vitesse_actuelle < vitesse_consigne)
            {
                vitesse_actuelle += 2;
            }
            else if (vitesse_actuelle > vitesse_consigne)
            {
                vitesse_actuelle -= 2;
            }
            temps_mot = millis();
        }
    }
    else
    {
        vitesse_actuelle = vitesse_consigne;
    }
}

void Moteur::moteur()
{
    digitalWrite(pinSens, sens_actuel);
    ledcWrite(ledc_channel, vitesse_actuelle);
}
