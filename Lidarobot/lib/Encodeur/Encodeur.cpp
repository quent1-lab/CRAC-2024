#include "Encodeur.h"

Encodeur::Encodeur(int pinD_A, int pinD_B,int pinG_A, int pinG_B)
{
    encoderD.attachHalfQuad(pinD_A, pinD_B);
    encoderG.attachHalfQuad(pinG_A, pinG_B);
    this->oldPositionD = 0;
    this->oldPositionG = 0;
}

void Encodeur::init()
{
    this->x = 0;
    this->y = 0;
    this->theta = 0;
    this->rayon = 0.022;
}

void Encodeur::init(float x, float y, float theta, float rayon)
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

void Encodeur::change_position(float x, float y, float theta)
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

    int countD = readEncoderD();
    int countG = readEncoderG();

    // Lecture des encodeurs
    deltaD = countD - oldPositionD;
    deltaG = countG - oldPositionG;
    
    // Calcul de la distance parcourue par chaque roue
    deltaD = deltaD * 2 * PI * rayon / 24.0;//
    deltaG = deltaG * 2 * PI * rayon / 24.0;//

    // Calcul de la distance parcourue par le robot
    deltaS = (deltaD + deltaG) / 2.0;

    // Calcul de la variation d'angle en fonction de l'entraxe
    deltaT = (deltaD - deltaG) / 9.0;

    // Calcul de la nouvelle position
    this->theta += deltaT;//a 2 pi pres
    if(this->theta > 2*PI)
        this->theta -= 2*PI;
    if(this->theta < 0)
        this->theta += 2*PI;
    this->x += deltaS * cos(this->theta);
    this->y += deltaS * sin(this->theta);

    // Mise à jour des variables
    this->oldPositionD = countD;
    this->oldPositionG = countG;
}

float Encodeur::get_x()
{
    return this->x;
}

float Encodeur::get_y()
{
    return this->y;
}

float Encodeur::get_theta()
{
    return this->theta;
}

float Encodeur::get_theta_deg(){
    return this->theta*180/PI;
}
