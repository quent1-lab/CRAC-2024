/*
*  Projet : Lidarobot
*  Description : Projet de robot autonome avec un lidar
*  Auteur : Quent1-lab
*  Date : 15/12/2023
*  Version : 1.0.0
*
*  Cette bibliothèque est un logiciel libre ; vous pouvez la redistribuer et/ou
*  la modifier selon les termes de la Licence Publique Générale GNU telle que publiée
*  par la Free Software Foundation ; soit la version 2 de la Licence, ou
*  (à votre discrétion) toute version ultérieure.
*/

#include <Arduino.h>
#include <Wire.h>
#include "Bouton.h"
#include "Moteur.h"
#include <Encodeur.h>
#include "esp32/rom/rtc.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"

/*-------------------------------- DEFINE --------------------------------------*/

// define pour les boutons
#define NOIR 0
#define BLEU 1
#define VERT 2
#define DEPART 3

// Pin des encodeurs
const int pinEncodeurGaucheA = 33;
const int pinEncodeurGaucheB = 13;
const int pinEncodeurDroitA = 17;
const int pinEncodeurDroitB = 16;

/*----------------------- Prototypes des fonctions -----------------------------*/
// Fonction pour la bibliothèque Bouton
void setup_bt(int nb_bt);
void read_bt(int nb_bt);

void moteur();

// Fonction de communication
void envoie(String message);
String reception();
String formatage_JSON();
void envoie_JSON();
void mise_a_jour_donnees();

// Fonction de déplacement
void avancer(float distance);
void tourner(float angle);
void aller_a(float x, float y);
void aller_a(float x, float y, float theta);

/*---------------------- Variable des pins de sortis ---------------------------*/
// Aucune des pins ne sont bien définies, il faut les définir en fonction des branchements
// Pin des moteurs
const int pinMotGaucheSens = 26;
const int pinMotGauchePWM = 14;
const int pinMotDroitSens = 25;
const int pinMotDroitPWM = 27;

const int pinLed = 19;
const int pinBoutonJaune = 35;
const int pinBoutonBleu = 4;
const int pinBoutonVert = 32;

/*-------------------------- Variables pour les boutons -------------------------*/
// Pin des boutons
const int button_pin[3] = {pinBoutonJaune, pinBoutonBleu, pinBoutonVert};

/*----------------------------- Variables systèmes ------------------------------*/
// Machine à état
int etat_sys = 0;

// Temps de délai pour les boutons
int t_delay_click = 140;
int t_delay_press = 1500;
int t_delay_bounce = 120;

// Variables pour les compteurs des encodeurs
float rayon = 2.2;
float entraxe = 8.8;

/*----------------------------- Variables pour l'odométrie ------------------------------*/
float x = 0;
float y = 0;
float theta = 0;

/*----------------------------- Constructeur Bibliothèque ------------------------------*/

Bouton bt[3]; // création d'un tableau de 3 boutons.

// Déclaration des moteurs et encodeurs en tant qu'instances des classes Moteur et Encodeur
Moteur moteurGauche(pinMotGaucheSens, pinMotGauchePWM, 0);
Moteur moteurDroit(pinMotDroitSens, pinMotDroitPWM, 2);

Encodeur encodeur(pinEncodeurDroitB, pinEncodeurDroitA, pinEncodeurGaucheA, pinEncodeurGaucheB);

/*----------------------------- Fonction OS temps réel ----------------------------------*/

void taskAvancer(void *pvParameters) {
    while (1) {
        // Appeler la fonction avancer ici
        avancer(10);
        vTaskDelay(pdMS_TO_TICKS(100));  // Delay de 100ms
    }
}

void taskTourner(void *pvParameters) {
    while (1) {
        // Appeler la fonction tourner ici
        tourner(PI/2);
        vTaskDelay(pdMS_TO_TICKS(100));  // Delay de 100ms
    }
}

void taskCommuniquer(void *pvParameters) {
    while (1) {
        // Appeler la fonction de communication ici
        envoie_JSON();
        vTaskDelay(pdMS_TO_TICKS(100));  // Delay de 100ms
    }
}


void setup()
{
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);// disable brownout detector

  xTaskCreatePinnedToCore(taskAvancer, "taskAvancer", 4096, NULL, 2, NULL, 0);  // Tâche avec priorité 1
  xTaskCreatePinnedToCore(taskTourner, "taskTourner", 4096, NULL, 2, NULL, 0);
  xTaskCreatePinnedToCore(taskCommuniquer, "taskCommuniquer", 4096, NULL, 1, NULL, 0);

  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(pinLed, OUTPUT);

  // Initialisation des moteurs et des encodeurs
  moteurGauche.init();
  moteurDroit.init();

  // Initialisation des encodeurs
  encodeur.init(x, y, theta, rayon, entraxe, 298, 6);

  // initialisation des boutons
  setup_bt(3);
}

void loop()
{
  read_bt(3);
  switch (etat_sys)
  {
  case 0:
    // Etat 0 : Attente du départ
    if (bt[NOIR].click())
    {
      etat_sys = 2;
    }
    break;
  case 1:
    // Etat 1 : Test des moteurs
    break;
  case 2:
    // Etat 2 : Test de la ligne droite
    avancer(20);
    tourner(PI/2);
    avancer(10);
    tourner(PI);
    avancer(10);
    tourner(-PI/2);
    avancer(20);
    tourner(PI);
    etat_sys = 0;
    break;
  default:
    break;
  }

  moteur();
}

/*---------------------------------- Fonction setup bouton ------------------------------------*/
void setup_bt(int nb_bt)
{
  /*
    Input : nb_bt : number of buttons (int)
    Output : none
    Description: This function is used to initialize the buttons
  */
  for (int k = 0; k < nb_bt; k++)
  {
    bt[k].begin(button_pin[k], LOW, t_delay_click, t_delay_press, t_delay_bounce);
  }
}

void read_bt(int nb_bt)
{
  /*
    Input : nb_bt : number of buttons (int)
    Output : none
    Description: This function is used to read the buttons
  */
  for (int k = 0; k < nb_bt; k++)
  {
    bt[k].read_Bt();
  }
}

/*------------------------------------ Fonction moteur ---------------------------------------*/
void moteur()
{
  moteurGauche.moteur();
  moteurDroit.moteur();
}

/*-------------------------------- Fonction de communication ---------------------------------*/

void envoie(String message)
{
  //Envoie un message sur le port série
  Serial.print(message);
}

String reception()
{
  //Reçoit un message sur le port série
  String message = "";
  while (Serial.available())
  {
    message += char(Serial.read());
  }
  return message;
}

String formatage_JSON()
{
  //Formate les données du robot en JSON
  String message = "{";
  message += "\"x\":";
  message += x;
  message += ",";
  message += "\"y\":";
  message += y;
  message += ",";
  message += "\"theta\":";
  message += theta;
  message += "}";
  return message;
}

void envoie_JSON()
{
  //Envoie les données du robot en JSON toutes les 100ms
  static unsigned long t0 = millis();
  if (millis() - t0 > 100)
  {
    mise_a_jour_donnees();
    t0 = millis();
    envoie(formatage_JSON());
  }
}

void mise_a_jour_donnees(){
  //Met à jour les données du robot
  encodeur.odometrie();
  x = encodeur.get_x();
  y = encodeur.get_y();
  theta = encodeur.get_theta();
}

/*-------------------------------- Fonction de déplacement -----------------------------------*/

void avancer(float distance){
  /*
    Input : distance : distance à parcourir en cm (float)
    Output : none
    Description:  Cette fonction permet de faire avancer le robot d'une certaine distance
                  Un asservissement en pas est utilisé pour avancer droit
  */

  float new_x = x + distance*cos(theta);
  float new_y = y + distance*sin(theta);
  float new_theta = theta;

  //Calcul de la distance totale à parcourir par chaque roue
  float nbr_pas_a_parcourir = distance / (2*PI*rayon) * encodeur.get_resolution() * encodeur.get_reduction();
  Serial.println(nbr_pas_a_parcourir);
  //Asservissement en pas pour chaque roue
  int pas_gauche = encodeur.readEncoderG() + nbr_pas_a_parcourir;
  int pas_droit = encodeur.readEncoderD() + nbr_pas_a_parcourir;

  //Asservissement en pas pour chaque roue
  while(encodeur.readEncoderG() < pas_gauche && encodeur.readEncoderD() < pas_droit){
    //Adapter la vitesse des moteurs en fonction de l'erreur
    float erreurG = pas_gauche - encodeur.readEncoderG();
    float erreurD = pas_droit - encodeur.readEncoderD();

    //Vitesse des moteurs (Démarrage rapide et freinage adaptatif)
    float vitesseG = 100;
    float vitesseD = 100;
    if(erreurG < (298 * 6)){
      //Adapter la vitesse en fonction de l'erreur entre 100 et 30 (30 = vitesse minimale)
      vitesseG = 30 + (100 - 30) * (1 - (298 * 6 - erreurG) / (298 * 6));
    }
    if(erreurD < 298 * 6){
      vitesseD = 30 + (100 - 30) * (1 - (298 * 6 - erreurD) / (298 * 6));
    }

    moteurGauche.setVitesse(vitesseG);
    moteurDroit.setVitesse(vitesseD);

    moteur();
  }
  moteurGauche.setVitesse(2);
  moteurDroit.setVitesse(2);
  moteur();
}

void tourner(float angle){
  /*
    Input : angle : angle à parcourir en rad (float)
    Output : none
    Description:  Cette fonction permet de faire tourner le robot d'un certain angle
                  Un asservissement en pas est utilisé pour tourner droit
  */

  //Calcul de la distance totale à parcourir par chaque roue pour tourner d'un certain angle
  float nbr_pas_a_parcourir = abs((angle*entraxe) / (2*2*PI*rayon) * encodeur.get_resolution() * encodeur.get_reduction()); 

  //Asservissement en pas pour chaque roue
  int pas_gauche, pas_droit,sens;
  if (angle >= 0) {
    pas_gauche = encodeur.readEncoderG() + nbr_pas_a_parcourir;
    pas_droit = encodeur.readEncoderD() - nbr_pas_a_parcourir;
    sens = 1; 
  } else {
    pas_gauche = encodeur.readEncoderG() - nbr_pas_a_parcourir;
    pas_droit = encodeur.readEncoderD() + nbr_pas_a_parcourir;
    sens = -1;
  }
  //Asservissement en pas pour chaque roue
  while(sens == 1 ? (encodeur.readEncoderG() < pas_gauche && encodeur.readEncoderD() > pas_droit) : (encodeur.readEncoderG() > pas_gauche && encodeur.readEncoderD() < pas_droit)){
    //Adapter la vitesse des moteurs en fonction de l'erreur
    float erreurG = pas_gauche - encodeur.readEncoderG();
    float erreurD = pas_droit - encodeur.readEncoderD();

    //Vitesse des moteurs (Démarrage rapide et freinage adaptatif)
    float vitesseG = 100 * sens;
    float vitesseD = 100 * -sens;

    moteurGauche.setVitesse(vitesseG);
    moteurDroit.setVitesse(vitesseD);

    moteur();
  }
  moteurGauche.setVitesse(2);
  moteurDroit.setVitesse(2);
  moteur();
}

void aller_a(float X, float Y){
  /*
    Input : x : position en x du robot (float)
            y : position en y du robot (float)
    Output : none
    Description:  Cette fonction permet de faire aller le robot à une certaine position
                  Un asservissement en pas est utilisé pour aller droit
  */

  float new_x = X;
  float new_y = Y;
  float new_theta = theta;

  //Calcul de la distance à parcourir par chaque roue
  float distance = sqrt(pow(new_x - x, 2) + pow(new_y - y, 2));

  //calcul de l'angle à parcourir
  float angle = atan2(new_y - y, new_x - x) - theta;
  if(angle > 2*PI){
    angle -= 2*PI;
  }else if(angle < 0){
    angle += 2*PI;
  }



  //Asservissement en pas pour chaque roue
  tourner(angle);
  avancer(distance);

  //Vérification de la position
  encodeur.odometrie();
  float erreur_x = new_x - encodeur.get_x();
  float erreur_y = new_y - encodeur.get_y();

  if(abs(erreur_x) > 0.5 || abs(erreur_y) > 0.5){
    //Si la position n'est pas bonne, on corrige
    aller_a(new_x, new_y, new_theta);
  }
}

void aller_a(float X, float Y, float Theta){
  /*
    Input : x : position en x du robot (float)
            y : position en y du robot (float)
            theta : angle du robot (float)
    Output : none
    Description:  Cette fonction permet de faire aller le robot à une certaine position
                  Un asservissement en pas est utilisé pour aller droit
  */

  float new_x = X;
  float new_y = Y;
  float new_theta = Theta;

  //Calcul de la distance à parcourir par chaque roue
  float distance = sqrt(pow(new_x - x, 2) + pow(new_y - y, 2));

  //calcul de l'angle à parcourir
  float angle = atan2(new_y - y, new_x - x) - theta;
  if(angle > 2*PI){
    angle -= 2*PI;
  }else if(angle < 0){
    angle += 2*PI;
  }

  //Asservissement en pas pour chaque roue
  tourner(angle);
  avancer(distance);
  tourner(Theta);

  //Vérification de la position
  encodeur.odometrie();
  float erreur_x = new_x - encodeur.get_x();
  float erreur_y = new_y - encodeur.get_y();
  float erreur_theta = new_theta - encodeur.get_theta();

  if(abs(erreur_x) > 0.5 || abs(erreur_y) > 0.5 || abs(erreur_theta) > 0.1){
    //Si la position n'est pas bonne, on corrige
    aller_a(new_x, new_y, new_theta);
  }
}