#include "Moteur.h"

/**
 * @brief Constructeur de la classe Moteur
 * 
 * @param pinSens Pin pour le sens du moteur
 * @param pinPWM Pin pour le PWM du moteur
 * @param ledc_channel Canal pour le PWM du moteur
 */
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

/**
 * @brief Initialise le moteur avec une vitesse maximale par défaut
 */
void Moteur::init()
{
    pinMode(pinSens, OUTPUT);
    ledcSetup(ledc_channel, 40000, 10);
    ledcAttachPin(pinPWM, ledc_channel);
    ledcWrite(ledc_channel, 0);
    this->vitesse_max = 100;
    this->coefficient = 1;
}

/**
 * @brief Initialise le moteur avec une vitesse maximale spécifiée
 * 
 * @param vitesse_max Vitesse maximale du moteur (int)
 */
void Moteur::init(int vitesse_max)
{
    pinMode(pinSens, OUTPUT);
    ledcSetup(ledc_channel, 40000, 10);
    ledcAttachPin(pinPWM, ledc_channel);
    ledcWrite(ledc_channel, 0);
    this->vitesse_max = vitesse_max;
    this->coefficient = 1;
}

/**
 * @brief Initialise le moteur avec une vitesse maximale et un coefficient spécifiés
 * 
 * @param vitesse_max Vitesse maximale du moteur (int)
 * @param coefficient Coefficient pour la vitesse du moteur (float)
 */
void Moteur::init(int vitesse_max, float coefficient)
{
    pinMode(pinSens, OUTPUT);
    ledcSetup(ledc_channel, 40000, 10);
    ledcAttachPin(pinPWM, ledc_channel);
    ledcWrite(ledc_channel, 0);
    this->vitesse_max = vitesse_max;
    this->coefficient = coefficient;
}

/**
 * @brief Définit la vitesse du moteur
 * 
 * @param vitesse Vitesse du moteur en pourcentage (int) entre -100 et 100
 * Si la vitesse est négative, le sens du moteur est inversé
 */
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

/**
 * @brief Définit le sens du moteur
 * 
 * @param sens Sens du moteur (true = arrière, false = avant)
 */
void Moteur::setSens(bool sens)
{
    sens_actuel = sens;
}

/**
 * @brief Smooth le moteur pour éviter les changements brusques de vitesse
 */
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

/**
 * @brief Met à jour le sens et la vitesse du moteur
 */
void Moteur::moteur()
{
    digitalWrite(pinSens, sens_actuel);
    ledcWrite(ledc_channel, vitesse_actuelle);
}
