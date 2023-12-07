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
    this->rayon = 2.2;
}

void Encodeur::init(float x, float y, float theta, float rayon)
{
    this->x = x;
    this->y = y;
    this->theta = theta;
    this->rayon = rayon;
    this->encoderD.setCount(0);
    this->encoderG.setCount(0);
    this->oldPositionD = 0;
    this->oldPositionG = 0;
}

void Encodeur::init(float x, float y, float theta, float rayon, int reduction, int resolution)
{
    this->x = x;
    this->y = y;
    this->theta = theta;
    this->rayon = rayon;
    this->reduction = reduction;
    this->resolution = resolution;
    this->encoderD.setCount(0);
    this->encoderG.setCount(0);
    this->oldPositionD = 0;
    this->oldPositionG = 0;
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

void Encodeur::print(int countD,int countG)
{
    Serial.print("EncodeurD : ");
    Serial.print(countD);
    Serial.print(" EncodeurG : ");
    Serial.print(countG);
    Serial.print(" x : ");
    Serial.print(this->x);
    Serial.print(" y : ");
    Serial.print(this->y);
    Serial.print(" theta : ");
    Serial.println(this->theta*180/PI);
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
    deltaD = deltaD * 2.0 * PI * rayon / (this->resolution*this->reduction);//
    deltaG = deltaG * 2.0 * PI * rayon / (this->resolution*this->reduction);//

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

    print(countD,countG);
    
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

void Encodeur::go_to(float x, float y, float theta)
{
    // Cette fonction permet de faire avancer le robot jusqu'à une position donnée
    // Elle utilise la fonction odometrie() pour se déplacer

    // Variables locales
    float distance, angle;
    float x0, y0, theta0;

    // Lecture de la position initiale
    x0 = this->x;
    y0 = this->y;
    theta0 = this->theta;

    // Calcul de la distance à parcourir
    distance = sqrt(pow(x - x0, 2) + pow(y - y0, 2));

    // Calcul de l'angle à parcourir
    angle = atan2(y - y0, x - x0);

    // Rotation du robot
    turn_to(angle);

    // Avance du robot
    moteurGauche.setVitesse(100);
    moteurDroit.setVitesse(100);
    while (sqrt(pow(this->x - x0, 2) + pow(this->y - y0, 2)) < distance)
    {
        odometrie();
    }
    moteurGauche.setVitesse(0);
    moteurDroit.setVitesse(0);

    // Rotation du robot
    turn_to(theta);

    // Mise à jour de la position
    this->x = x;
    this->y = y;
    this->theta = theta;
}

void Encodeur::go_to(float x, float y)
{
    // Cette fonction permet de faire avancer le robot jusqu'à une position donnée
    // Elle utilise la fonction odometrie() pour se déplacer

    // Variables locales
    float distance, angle;
    float x0, y0, theta0;

    // Lecture de la position initiale
    x0 = this->x;
    y0 = this->y;
    theta0 = this->theta;

    // Calcul de la distance à parcourir
    distance = sqrt(pow(x - x0, 2) + pow(y - y0, 2));

    // Calcul de l'angle à parcourir
    angle = atan2(y - y0, x - x0);

    // Rotation du robot
    turn_to(angle);

    // Avance du robot
    moteurGauche.setVitesse(100);
    moteurDroit.setVitesse(100);
    while (sqrt(pow(this->x - x0, 2) + pow(this->y - y0, 2)) < distance)
    {
        odometrie();
    }
    moteurGauche.setVitesse(0);
    moteurDroit.setVitesse(0);

    // Mise à jour de la position
    this->x = x;
    this->y = y;
}

void Encodeur::turn_to(float theta)
{
    // Cette fonction permet de faire tourner le robot jusqu'à un angle donné
    // Elle utilise la fonction odometrie() pour se déplacer

    // Variables locales
    float angle;
    float theta0;

    // Lecture de la position initiale
    theta0 = this->theta;

    // Calcul de l'angle à parcourir
    angle = theta - theta0;

    // Rotation du robot
    moteurGauche.setVitesse(100);
    moteurDroit.setVitesse(-100);
    while (this->theta - theta0 < angle)
    {
        odometrie();
    }
    moteurGauche.setVitesse(0);
    moteurDroit.setVitesse(0);

    // Mise à jour de la position
    this->theta = theta;
}