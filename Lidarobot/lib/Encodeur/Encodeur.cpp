#include "Encodeur.h"

Encodeur::Encodeur(int pinA, int pinB, int pinC, int pinD)
{
    encoderD.attachHalfQuad(pinA, pinB);
    encoderG.attachHalfQuad(pinC, pinD);
    oldPositionD = -999;
    oldPositionG = -999;
}

void Encodeur::init()
{
    // Other initialization if needed
}

int Encodeur::readEncoderD()
{
    return encoderD.getCount();
}

int Encodeur::readEncoderG()
{
    return encoderG.getCount();
}

void Encodeur::reset()
{
    encoderD.setCount(0);
    encoderG.setCount(0);
}

void Encodeur::odometrie(float *x, float *y, float *theta)
{
    // Cette fonction permet de calculer la position du robot en fonction des encodeurs

    // Variables locales
    float deltaD, deltaG, deltaT, deltaS;
    float x0, y0, vitesse0;

    // Lecture des encodeurs
    deltaD = readEncoderRight() - oldPositionD;
    deltaG = readEncoderLeft() - oldPositionG;

    // Calcul de la distance parcourue par chaque roue
    deltaD = deltaD * 2 * PI * rayon / 360;
    deltaG = deltaG * 2 * PI * rayon / 360;

    // Calcul de la distance parcourue par le robot
    deltaS = (deltaD + deltaG) / 2;

    // Calcul de la variation d'angle en fonction de l'entraxe
    deltaT = (deltaD - deltaG) / 90;

    // Calcul de la nouvelle position
    *x = *x + deltaS * cos(*theta + deltaT / 2);
    *y = *y + deltaS * sin(*theta + deltaT / 2);
    *theta = *theta + deltaT;

    // Mise à jour des variables
    oldPositionD = readEncoderRight();
    oldPositionG = readEncoderLeft();

    // Affichage des variables
    Serial.print("x = ");
    Serial.print(*x);
    Serial.print(" y = ");
    Serial.print(*y);
    Serial.print(" theta = ");
    Serial.println(*theta);
}
