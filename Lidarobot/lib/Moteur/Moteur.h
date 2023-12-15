/*
 * Nom de la bibliothèque : Moteur
 * Auteur : Quent1-lab
 * Date : 15/12/2023
 * Version : 1.0.0
 * 
 * Description : Bibliothèque pour la gestion des moteurs.
 * 
 * Cette bibliothèque est un logiciel libre ; vous pouvez la redistribuer et/ou
 * la modifier selon les termes de la Licence Publique Générale GNU telle que publiée
 * par la Free Software Foundation ; soit la version 2 de la Licence, ou
 * (à votre discrétion) toute version ultérieure.
 */

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
