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
#include <ArduinoJson.h>

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
void move(float x, float y, float theta);

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
float rayon = 22;
float entraxe = 88;

/*----------------------------- Variables pour l'odométrie ------------------------------*/
float x = 1500;
float y = 1000;
float theta = 0;
int resolution = 298;
int reduction = 6;
int countD = 0;
int countG = 0;

/*----------------------------- Constructeur Bibliothèque ------------------------------*/

Bouton bt[3]; // création d'un tableau de 3 boutons.

// Déclaration des moteurs et encodeurs en tant qu'instances des classes Moteur et Encodeur
Moteur moteurGauche(pinMotGaucheSens, pinMotGauchePWM, 0);
Moteur moteurDroit(pinMotDroitSens, pinMotDroitPWM, 2);

Encodeur encodeur(pinEncodeurDroitB, pinEncodeurDroitA, pinEncodeurGaucheA, pinEncodeurGaucheB);

/*----------------------------- Fonction OS temps réel ----------------------------------*/

// Buffer pour stocker les données reçues
char rxBuffer[256];
char last_rxBuffer[256];
// Déclaration des variables globales
float x_rx;
float y_rx;
float theta_rx;
String commande = "";

// Tâche pour l'envoi de données
void taskEnvoyer(void *pvParameters)
{
  while (1)
  {
    // Envoyer des données ici
    if(etat_sys != 0){
      envoie_JSON();
    }
    vTaskDelay(pdMS_TO_TICKS(100)); // Delay de 100ms
  }
}

// Tâche pour la réception de données
void taskRecevoir(void *pvParameters)
{
  while (1)
  {
    if (Serial.available())
    {
      // Lire les données reçues
      size_t len = Serial.readBytesUntil('\n', rxBuffer, sizeof(rxBuffer) - 1);
      rxBuffer[len] = '\0';
      //Serial.println(rxBuffer);
    }
    vTaskDelay(pdMS_TO_TICKS(10)); // Delay de 10ms
  }
}

void taskMoteur(void *pvParameters)
{
  while (1)
  {
    // Appeler la fonction moteur ici
    moteur();
    vTaskDelay(pdMS_TO_TICKS(5)); // Delay de 10ms
  }
}

void taskMiseAJourDonnees(void *pvParameters)
{
  while (1)
  {
    // Appeler la fonction de mise à jour des données ici
    mise_a_jour_donnees();
    vTaskDelay(pdMS_TO_TICKS(10)); // Delay de 20ms
  }
}

void setup()
{
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); // disable brownout detector

  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(pinLed, OUTPUT);

  // Initialisation des moteurs et des encodeurs
  moteurGauche.init();
  moteurDroit.init();

  // Initialisation des encodeurs
  encodeur.init(x, y, theta, rayon, entraxe, reduction, resolution);

  // initialisation des boutons
  setup_bt(3);

  xTaskCreate(taskEnvoyer, "Envoyer", 1000, NULL, 2, NULL);
  xTaskCreate(taskRecevoir, "Recevoir", 1000, NULL, 2, NULL);
  xTaskCreatePinnedToCore(taskMoteur, "taskMoteur", 4096, NULL, 1, NULL, 0);
  xTaskCreatePinnedToCore(taskMiseAJourDonnees, "taskMiseAJourDonnees", 4096, NULL, 2, NULL, 0);
}

void loop()
{
  // read_bt(3);
  if (strcmp(rxBuffer, last_rxBuffer) != 0)
  {
    // rxBuffer est différent de last_rxBuffer
    //  Définir la capacité du document JSON
    const size_t capacity = JSON_OBJECT_SIZE(4) + 50;

    // Créer un objet DynamicJsonDocument
    DynamicJsonDocument doc(capacity);

    // Convertir rxBuffer en un objet JSON
    deserializeJson(doc, rxBuffer);

    // Extraire les valeurs x, y, theta
    x_rx = doc["x"];
    y_rx = doc["y"];
    theta_rx = doc["theta"];
    commande = doc["cmd"].as<String>();

    // Vérifier si la commande "start" a été reçue
    if (commande == "start")
    {
      // Changer l'état du système
      etat_sys = 1;
      // Réinitialiser les encodeurs
      encodeur.reset();
      x = x_rx;
      y = y_rx;
      theta = theta_rx;
    }
    // Vérifier si la commande "stop" a été reçue
    else if (commande == "stop")
    {
      // Changer l'état du système
      etat_sys = 0;
    }
    else if (commande == "move")
    {
      etat_sys = 2;
    }
    
  }

  switch (etat_sys)
  {
  case 0:
    // Etat 0 : Attente du départ
    digitalWrite(pinLed, LOW);
    break;
  case 1:
    // Etat 1:Test de la ligne droite
    digitalWrite(pinLed, HIGH);
    delay(2000);
    etat_sys = 2;
    break;
  case 2:
    // Etat 2:Test de la ligne droite
    //move(x_rx, y_rx, theta_rx);
    //etat_sys = 1;

    avancer(500);
    tourner(PI / 2);
    /*avancer(100);
    tourner(PI);
    avancer(100);
    tourner(-PI / 2);
    avancer(100);
    tourner(PI);*/

    break;
  default:
    break;
  }
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
  countD = encodeur.get_countD();
  countG = encodeur.get_countG();
  moteurGauche.moteur();
  moteurDroit.moteur();
}

/*-------------------------------- Fonction de communication ---------------------------------*/

void envoie(String message)
{
  // Envoie un message sur le port série
  Serial.print(message);
}

String reception()
{
  // Reçoit un message sur le port série
  String message = "";
  while (Serial.available())
  {
    message += char(Serial.read());
  }
  if (message == "")
  {
    return "";
  }
  // supprimer les caractères inutiles du message
  message.replace("b", "");
  message.replace("'", "");
  // Charger le message dans un JSON
  DynamicJsonDocument json(1024);
  DeserializationError error = deserializeJson(json, message);
  if (error)
  {
    Serial.print(F("deserializeJson() failed: "));
    Serial.println(error.f_str());
    return "";
  }
  // Récupérer les données du JSON
  x = json["x"];
  y = json["y"];
  return "";
}

String formatage_JSON()
{
  // Formate les données du robot en JSON
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
  // Envoie les données du robot en JSON toutes les 100ms
  envoie(formatage_JSON());
}

void mise_a_jour_donnees()
{
  // Met à jour les données du robot
  countD = encodeur.get_countD();
  countG = encodeur.get_countG();
  encodeur.odometrie();
  x = encodeur.get_x();
  y = encodeur.get_y();
  theta = encodeur.get_theta();
}

/*-------------------------------- Fonction de déplacement -----------------------------------*/

void avancer(float distance)
{
  /*
    Input : distance : distance à parcourir en cm (float)
    Output : none
    Description:  Cette fonction permet de faire avancer le robot d'une certaine distance
                  Un asservissement en pas est utilisé pour avancer droit
  */

  // Calcul de la distance totale à parcourir par chaque roue
  float nbr_pas_a_parcourir = distance / (2 * PI * rayon) * encodeur.get_resolution() * encodeur.get_reduction();

  // Asservissement en pas pour chaque roue
  int pas_gauche = countG + nbr_pas_a_parcourir;
  int pas_droit = countD + nbr_pas_a_parcourir;

  // Asservissement en pas pour chaque roue
  while (countG < pas_gauche && countD < pas_droit)
  {
    // Adapter la vitesse des moteurs en fonction de l'erreur
    float erreurG = pas_gauche - countG;
    float erreurD = pas_droit - countD;

    // Vitesse des moteurs (Démarrage rapide et freinage adaptatif)
    float vitesseG = 60;
    float vitesseD = 60;
    if (erreurG <= 0)
    {
      vitesseG = 2; // Valeur non nulle pour bloquer le moteur
    }
    if (erreurD <= 0)
    {
      vitesseD = 2;
    }

    moteurGauche.setVitesse(vitesseG);
    moteurDroit.setVitesse(vitesseD);
  }
  moteurGauche.setVitesse(2);
  moteurDroit.setVitesse(2);
}

void tourner(float angle)
{
  /*
    Input : angle : angle à parcourir en rad (float)
    Output : none
    Description:  Cette fonction permet de faire tourner le robot d'un certain angle
                  Un asservissement en pas est utilisé pour tourner droit
  */

  // Calcul de la distance totale à parcourir par chaque roue pour tourner d'un certain angle
  float nbr_pas_a_parcourir = abs((angle * entraxe) / (2 * 2 * PI * rayon) * encodeur.get_resolution() * encodeur.get_reduction());

  // Asservissement en pas pour chaque roue
  int pas_gauche, pas_droit, sens;
  if (angle >= 0)
  {
    pas_gauche = countG + nbr_pas_a_parcourir;
    pas_droit = countD - nbr_pas_a_parcourir;
    sens = 1;
  }
  else
  {
    pas_gauche = countG - nbr_pas_a_parcourir;
    pas_droit = countD + nbr_pas_a_parcourir;
    sens = -1;
  }
  // Asservissement en pas pour chaque roue
  while (sens == 1 ? (countG < pas_gauche && countD > pas_droit) : (countG > pas_gauche && countD < pas_droit))
  {
    // Adapter la vitesse des moteurs en fonction de l'erreur
    float erreurG = pas_gauche - countG;
    float erreurD = pas_droit - countD;

    // Vitesse des moteurs (Démarrage rapide et freinage adaptatif)
    float vitesseG = 60 * sens;
    float vitesseD = 60 * -sens;

    /*if(erreurG <= 0){
      vitesseG = 2; //Valeur non nulle pour bloquer le moteur
    }
    if(erreurD <= 0){
      vitesseD = 2;
    }*/

    moteurGauche.setVitesse(vitesseG);
    moteurDroit.setVitesse(vitesseD);
  }
  moteurGauche.setVitesse(2);
  moteurDroit.setVitesse(2);
}

void aller_a(float X, float Y)
{
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

  // Calcul de la distance à parcourir par chaque roue
  float distance = sqrt(pow(new_x - x, 2) + pow(new_y - y, 2));

  // calcul de l'angle à parcourir
  float angle = atan2(new_y - y, new_x - x) - theta;
  if (angle > 2 * PI)
  {
    angle -= 2 * PI;
  }
  else if (angle < 0)
  {
    angle += 2 * PI;
  }

  // Asservissement en pas pour chaque roue
  tourner(angle);
  avancer(distance);

  /*// Vérification de la position
  float erreur_x = new_x - encodeur.get_x();
  float erreur_y = new_y - encodeur.get_y();

  if (abs(erreur_x) > 0.5 || abs(erreur_y) > 0.5)
  {
    // Si la position n'est pas bonne, on corrige
    aller_a(new_x, new_y, new_theta);
  }*/
}

void move(float X, float Y, float Theta)
{
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

  // Calcul de la distance à parcourir par chaque roue
  float distance = sqrt(pow(new_x - x, 2) + pow(new_y - y, 2));

  // calcul de l'angle à parcourir
  float angle = atan2(new_y - y, new_x - x) - theta;
  if (angle > 2 * PI)
  {
    angle -= 2 * PI;
  }
  else if (angle < 0)
  {
    angle += 2 * PI;
  }

  // Asservissement en pas pour chaque roue
  tourner(angle);
  avancer(distance);
  tourner(Theta);

  /*// Vérification de la position
  float erreur_x = new_x - encodeur.get_x();
  float erreur_y = new_y - encodeur.get_y();
  float erreur_theta = new_theta - encodeur.get_theta();

  if (abs(erreur_x) > 0.5 || abs(erreur_y) > 0.5 || abs(erreur_theta) > 0.1)
  {
    // Si la position n'est pas bonne, on corrige
    aller_a(new_x, new_y, new_theta);
  }*/
}