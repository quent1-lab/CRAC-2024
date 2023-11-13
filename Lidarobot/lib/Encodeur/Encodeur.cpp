#include "Encodeur.h"

Encodeur::Encodeur(int pinA, int pinB, int pinC, int pinD)
{
    encoderD.attachHalfQuad(pinA, pinB);
    encoderG.attachHalfQuad(pinC, pinD);
    this->oldPositionD = -999;
    this->oldPositionG = -999;
}

void Encodeur::init()
{
    this->x = 0;
    this->y = 0;
    this->theta = 0;
    this->rayon = 0.022;
}

void Encodeur::init(int x,int y, int theta,float rayon)
{
    this->x = x;
    this->y = y;
    this->theta = theta;
    this->rayon = rayon;
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

void Encodeur::print()
{
    Serial.print("EncodeurD : ");
    Serial.print(readEncoderD());
    Serial.print(" EncodeurG : ");
    Serial.print(readEncoderG());
    Serial.print(" x : ");
    Serial.print(this->x);
    Serial.print(" y : ");
    Serial.print(this->y);
    Serial.print(" theta : ");
    Serial.println(this->theta);
}

void Encodeur::change_position(int x, int y, int theta)
{
    this->x = x;
    this->y = y;
    this->theta = theta;
}

void Encodeur::odometrie()
{
    // Cette fonction permet de calculer la position du robot en fonction des encodeurs

    // Variables locales
    float deltaD, deltaG, deltaT, deltaS;
    float x0, y0, vitesse0;

    // Lecture des encodeurs
    deltaD = readEncoderD() - oldPositionD;
    deltaG = readEncoderG() - oldPositionG;

    // Calcul de la distance parcourue par chaque roue
    deltaD = deltaD * 2 * PI * rayon / 360;
    deltaG = deltaG * 2 * PI * rayon / 360;

    // Calcul de la distance parcourue par le robot
    deltaS = (deltaD + deltaG) / 2;

    // Calcul de la variation d'angle en fonction de l'entraxe
    deltaT = (deltaD - deltaG) / 90;

    // Calcul de la nouvelle position
    this->x += deltaS * cos(*theta + deltaT / 2);
    this->y += deltaS * sin(*theta + deltaT / 2);
    this->theta += deltaT;

    // Mise à jour des variables
    this->oldPositionD = readEncoderRight();
    this->oldPositionG = readEncoderLeft();
}
