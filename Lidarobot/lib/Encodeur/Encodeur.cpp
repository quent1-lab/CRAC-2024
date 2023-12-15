#include "Encodeur.h"

/**
 * @brief Constructeur de la classe Encodeur
 * 
 * @param pinD_A Pin A de l'encodeur droit
 * @param pinD_B Pin B de l'encodeur droit
 * @param pinG_A Pin A de l'encodeur gauche
 * @param pinG_B Pin B de l'encodeur gauche
 */
Encodeur::Encodeur(int pinD_A, int pinD_B,int pinG_A, int pinG_B)
{
    encoderD.attachHalfQuad(pinD_A, pinD_B);
    encoderG.attachHalfQuad(pinG_A, pinG_B);
    this->oldPositionD = 0;
    this->oldPositionG = 0;
}

/**
 * @brief Initialise les variables de la classe Encodeur
 */
void Encodeur::init()
{
    this->x = 0;
    this->y = 0;
    this->theta = 0;
    this->rayon = 2.2;
}

/**
 * @brief Initialise les variables de la classe Encodeur
 * 
 * @param x Position en x du robot
 * @param y Position en y du robot
 * @param theta Angle du robot
 * @param rayon Rayon des roues du robot
 * @param entraxe Entraxe des roues du robot
*/
void Encodeur::init(float x, float y, float theta, float rayon, float entraxe)
{
    this->x = x;
    this->y = y;
    this->theta = theta;
    this->rayon = rayon;
    this->entraxe = entraxe;
    this->encoderD.setCount(0);
    this->encoderG.setCount(0);
    this->oldPositionD = 0;
    this->oldPositionG = 0;
}

/**
 * @brief Initialise les variables de la classe Encodeur
 * 
 * @param x Position en x du robot
 * @param y Position en y du robot
 * @param theta Angle du robot
 * @param rayon Rayon des roues du robot
 * @param entraxe Entraxe des roues du robot
 * @param reduction Rapport de réduction des moteurs
 * @param resolution Résolution des encodeurs
*/
void Encodeur::init(float x, float y, float theta, float rayon,float entraxe, int reduction, int resolution)
{
    this->x = x;
    this->y = y;
    this->theta = theta;
    this->rayon = rayon;
    this->entraxe = entraxe;
    this->reduction = reduction;
    this->resolution = resolution;
    this->encoderD.setCount(0);
    this->encoderG.setCount(0);
    this->oldPositionD = 0;
    this->oldPositionG = 0;
}

/**
 * @brief Lit la valeur de l'encodeur droit
*/
int Encodeur::readEncoderD()
{
    return encoderD.getCount();
}

/**
 * @brief Lit la valeur de l'encodeur gauche
*/
int Encodeur::readEncoderG()
{
    return encoderG.getCount();
}

/**
 * @brief Remet à zéro les encodeurs
*/
void Encodeur::reset()
{
    encoderD.setCount(0);
    encoderG.setCount(0);
}

/**
 * @brief Affiche les valeurs des encodeurs et de la position du robot
 * 
 * @param countD Valeur de l'encodeur droit
 * @param countG Valeur de l'encodeur gauche
*/
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

/**
 * @brief Change la position du robot
 * 
 * @param x Position en x du robot
 * @param y Position en y du robot
 * @param theta Angle du robot
*/
void Encodeur::change_position(float x, float y, float theta)
{
    this->x = x;
    this->y = y;
    this->theta = theta;
}

/**
 * @brief Calcule la position du robot en fonction des encodeurs
*/
void Encodeur::odometrie()
{
    // Cette fonction permet de calculer la position du robot en fonction des encodeurs

    // Variables locales
    float deltaD, deltaG, deltaT, deltaS;

    this->countD = readEncoderD();
    this->countG = readEncoderG();

    // Lecture des encodeurs
    deltaD = this->countD - oldPositionD;
    deltaG = this->countG - oldPositionG;
    
    // Calcul de la distance parcourue par chaque roue
    deltaD = deltaD * 2.0 * PI * rayon / (this->resolution*this->reduction);//
    deltaG = deltaG * 2.0 * PI * rayon / (this->resolution*this->reduction);//

    // Calcul de la distance parcourue par le robot
    deltaS = (deltaD + deltaG) / 2.0;

    // Calcul de la variation d'angle en fonction de l'entraxe
    deltaT = (deltaD - deltaG) / this->entraxe;

    // Calcul de la nouvelle position
    this->theta += deltaT;//a 2 pi pres
    if(this->theta > 2*PI)
        this->theta -= 2*PI;
    if(this->theta < 0)
        this->theta += 2*PI;
    this->x += deltaS * cos(this->theta);
    this->y += deltaS * sin(this->theta);

    print(this->countD,this->countG);
    
    // Mise à jour des variables
    this->oldPositionD = this->countD;
    this->oldPositionG = this->countG;
}

/**
 * @brief Retourne la position en x du robot
*/
float Encodeur::get_x()
{
    return this->x;
}

/**
 * @brief Retourne la position en y du robot
*/
float Encodeur::get_y()
{
    return this->y;
}

/**
 * @brief Retourne l'angle du robot
*/
float Encodeur::get_theta()
{
    return this->theta;
}

/**
 * @brief Retourne l'angle du robot en degrés
*/
float Encodeur::get_theta_deg(){
    return this->theta*180/PI;
}

/**
 * @brief Convertit une distance en nombre de pas moteur
 * 
 * @param x Distance en cm
*/
int Encodeur::x_to_step(float x)
{
    /*
    Cette fonction permet de convertir une distance en nombre de pas moteur
    x : distance en cm
    output : nombre de pas moteur
    */
    return x * this->resolution * this->reduction / (2.0 * PI * this->rayon);
}

/**
 * @brief Convertit une distance en nombre de pas moteur
 * 
 * @param y Distance en cm
*/
int Encodeur::y_to_step(float y)
{
    /*
    Cette fonction permet de convertir une distance en nombre de pas moteur
    y : distance en cm
    output : nombre de pas moteur
    */
    return y * this->resolution * this->reduction / (2.0 * PI * this->rayon);
}

/**
 * @brief Convertit un angle en nombre de pas moteur
 * 
 * @param theta Angle en radian
*/
int Encodeur::theta_to_step(float theta)
{
    /*
    Cette fonction permet de convertir un angle en nombre de pas moteur
    theta : angle en radian
    output : nombre de pas moteur
    */
    return theta * this->entraxe * this->resolution * this->reduction / (2.0 * 2 * PI * this->rayon);
}

/**
 * @brief Retourne la résolution des encodeurs
*/
int Encodeur::get_resolution(){
    return this->resolution;
}

/**
 * @brief Retourne le rapport de réduction des moteurs
*/
int Encodeur::get_reduction(){
    return this->reduction;
}

/**
 * @brief Retourne la valeur de l'encodeur droit
*/
int Encodeur::get_countD(){
    return this->countD;
}

/**
 * @brief Retourne la valeur de l'encodeur gauche
*/
int Encodeur::get_countG(){
    return this->countG;
}