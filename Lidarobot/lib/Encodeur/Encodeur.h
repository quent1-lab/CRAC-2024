/*
 * Nom de la bibliothèque : Encodeur
 * Auteur : Quent1-lab
 * Date : 15/12/2023
 * Version : 1.0.0
 * 
 * Description : Bibliothèque pour la gestion des encodeurs pour un ESP32.
 * 
 * Cette bibliothèque est un logiciel libre ; vous pouvez la redistribuer et/ou
 * la modifier selon les termes de la Licence Publique Générale GNU telle que publiée
 * par la Free Software Foundation ; soit la version 2 de la Licence, ou
 * (à votre discrétion) toute version ultérieure.
 */

#ifndef Encodeur_h
#define Encodeur_h

#include <Arduino.h>
#include <ESP32Encoder.h>

class Encodeur {
  private:
    ESP32Encoder encoderD;
    ESP32Encoder encoderG;
    long oldPositionD;
    long oldPositionG;
    float x;
    float y;
    float theta;
    float rayon;
    float entraxe;
    int reduction;
    int resolution;

  public:
    Encodeur(int pinD_A, int pinD_B,int pinG_A, int pinG_B);
    void init();
    void init(float x, float y, float theta, float rayon, float entraxe);
    void init(float x, float y, float theta, float rayon,float entraxe, int reduction, int resolution);
    void change_position(float x, float y, float theta);
    int readEncoderD();
    int readEncoderG();
    void reset();
    void odometrie();
    void print(int countD,int countG);
    
    float get_x();
    float get_y();
    float get_theta();
    float get_theta_deg();
    int get_resolution();
    int get_reduction();

    int x_to_step(float x);
    int y_to_step(float y);
    int theta_to_step(float theta);
};

#endif
