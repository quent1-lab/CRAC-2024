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
    ledcSetup(ledc_channel, 40000, 10);
    ledcAttachPin(pinPWM, ledc_channel);
    ledcWrite(ledc_channel, 0);
    this->vitesse_max = 100;
    this->coefficient = 1;
}

void Moteur::init(int vitesse_max)
{
    pinMode(pinSens, OUTPUT);
    ledcSetup(ledc_channel, 40000, 10);
    ledcAttachPin(pinPWM, ledc_channel);
    ledcWrite(ledc_channel, 0);
    this->vitesse_max = vitesse_max;
    this->coefficient = 1;
}

void Moteur::init(int vitesse_max, float coefficient)
{
    pinMode(pinSens, OUTPUT);
    ledcSetup(ledc_channel, 40000, 10);
    ledcAttachPin(pinPWM, ledc_channel);
    ledcWrite(ledc_channel, 0);
    this->vitesse_max = vitesse_max;
    this->coefficient = coefficient;
}

void Moteur::setVitesse(int vitesse)
{
    /*
     * Input : vitesse : vitesse du moteur en pourcentage (int)
     * Output : none
     * Définition : Cette fonction permet de définir la vitesse du moteur en pourcentage.
     *             La vitesse est comprise entre -100 et 100.
     */

    if (vitesse > 100){
        vitesse = 100;
    }
    else if (vitesse < -100){
        vitesse = -100;
    }
    if (vitesse < 0){
        sens_actuel = true;
        vitesse = -vitesse;
    }else{
        sens_actuel = false;
    }

    vitesse_actuelle = (vitesse * 1/100.0) * (1023*vitesse_max/100.0) * coefficient;
}

void Moteur::setSens(bool sens)
{
    sens_actuel = sens;
}

void Moteur::smoothMoteur()
{
    if (abs(vitesse_actuelle - vitesse_consigne) >= 100)
    {
        if (millis() > temps_mot + 2)
        {
            if (vitesse_actuelle < vitesse_consigne)
            {
                vitesse_actuelle += 5;
            }
            else if (vitesse_actuelle > vitesse_consigne)
            {
                vitesse_actuelle -= 5;
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
