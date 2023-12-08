#include <Arduino.h>
#include <Wire.h>
#include "Bouton.h"
#include "Moteur.h"
#include <Encodeur.h>
#include "esp32/rom/rtc.h"

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

// Fonction test
void testEncodeur(void);
void testMoteur(void);

// Fonction de déplacement
bool avancer(float distance);
bool tourner(float angle);
bool aller_a(float x, float y);
bool aller_a(float x, float y, float theta);

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

/*----------------------------- Variables pour l'odométrie ------------------------------*/
float x = 0;
float y = 0;
float theta = 0;

/*---------------------- Constructeur Bibliothèque -----------------------------*/

Bouton bt[3]; // création d'un tableau de 3 boutons.

// Déclaration des moteurs et encodeurs en tant qu'instances des classes Moteur et Encodeur
Moteur moteurGauche(pinMotGaucheSens, pinMotGauchePWM, 0);
Moteur moteurDroit(pinMotDroitSens, pinMotDroitPWM, 2);

Encodeur encodeur(pinEncodeurDroitB, pinEncodeurDroitA, pinEncodeurGaucheA, pinEncodeurGaucheB);

void setup()
{
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);// disable brownout detector
  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(pinLed, OUTPUT);

  // Initialisation des moteurs et des encodeurs
  moteurGauche.init();
  moteurDroit.init();

  // Initialisation des encodeurs
  encodeur.init(x, y, theta, rayon, 298, 6);

  // initialisation des boutons
  setup_bt(3);
}

void loop()
{
  read_bt(3);
  delay(1000);
  moteurGauche.setVitesse(100);
  moteurDroit.setVitesse(96);
  moteur();
  delay(1000);
  testEncodeur();
  moteurGauche.setVitesse(0);
  moteurDroit.setVitesse(0);
  moteur();
  delay(5000);
  encodeur.reset();
  switch (etat_sys)
  {
  case 0:
    // Etat 0 : Attente du départ
    //avancer(20);
    if (bt[NOIR].click())
    {
      etat_sys = 2;
      Serial.println("Etat 0");
    }
    if (bt[BLEU].click())
    {
      etat_sys = 2;
      Serial.println("Etat 0");
    }
    break;
  case 1:
    // Etat 1 : Test des moteurs
    digitalWrite(pinLed, HIGH);
    testMoteur();
    break;
  case 2:
    // Etat 2 : Test de la ligne droite
    break;
  default:
    break;
  }

  moteur();
}

/*---------------------------------- Fonction Setup BT ------------------------------------*/
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

/*---------------------- Fonction de test ---------------------------*/
// Fonction de test des encodeurs
void testEncodeur()
{
  encodeur.odometrie();
  //encodeur.print();
  //envoie_JSON();
}

void testMoteur()
{
  static int etat = 0;
  static unsigned long t0 = millis();

  switch (etat)
  {
  case 0:
    // Etat 0 : Avancer
    moteurGauche.setVitesse(100);
    moteurDroit.setVitesse(100);
    if (millis() - t0 > 1000)
    {
      etat = 1;
      t0 = millis();
    }
    break;
  case 1:
    // Etat 1 : Reculer
    moteurGauche.setVitesse(-100);
    moteurDroit.setVitesse(-100);
    if (millis() - t0 > 1000)
    {
      etat = 2;
      t0 = millis();
    }
    break;
  case 2:
    // Etat 2 : Tourner à gauche
    moteurGauche.setVitesse(-100);
    moteurDroit.setVitesse(100);
    if (millis() - t0 > 1000)
    {
      etat = 3;
      t0 = millis();
    }
    break;
  case 3:
    // Etat 3 : Tourner à droite
    moteurGauche.setVitesse(100);
    moteurDroit.setVitesse(-100);
    if (millis() - t0 > 1000)
    {
      etat = 0;
      t0 = millis();
    }
    break;
  default:
    break;
  }
}

/*---------------------- Fonction moteur ---------------------------*/
void moteur()
{
  moteurGauche.moteur();
  moteurDroit.moteur();
}

/*---------------------- Fonction de communication ---------------------------*/

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


bool avancer(float distance){
  /*
    Input : distance : distance à parcourir en cm (float)
    Output : none
    Description:  Cette fonction permet de faire avancer le robot d'une certaine distance
                  Un asservissement en position est utilisé pour que le robot avance droit
  */

  // Variables locales
  float new_x, new_y; // Nouvelle position du robot
  float distance_parcourue; // Distance parcourue par le robot
  float distance_restante; // Distance restante à parcourir
  float vitesse = 100.0; // Vitesse du robot

  encodeur.reset();
  theta = 0;
  y = 0;
  x = 0;
  // Initialisation des variables
  new_x = x + distance * cos(theta);
  new_y = y + distance * sin(theta);

  // Calcul de la distance restante à parcourir
  distance_restante = sqrt(pow(new_x - x, 2) + pow(new_y - y, 2));

  // Asservissement en position
  while(distance_restante > 0.1){
    // Calcul de la distance parcourue
    distance_parcourue = sqrt(pow(x - new_x, 2) + pow(y - new_y, 2));

    // Calcul de la distance restante à parcourir
    distance_restante = sqrt(pow(new_x - x, 2) + pow(new_y - y, 2));

    Serial.println(distance_restante);
    //encodeur.odometrie();
    // Calcul de la vitesse du robot
    vitesse = 100;

    // Asservissement en vitesse
    moteurGauche.setVitesse(vitesse);
    moteurDroit.setVitesse(vitesse);

    moteur();
    // Mise à jour des données
    mise_a_jour_donnees();
  }
  moteurGauche.setVitesse(0);
  moteurDroit.setVitesse(0);
  moteur();
  delay(5000);

  return true;
}

bool tourner(float angle){
  /*
    Input : angle : angle à tourner en radian (float)
    Output : none
    Description:  Cette fonction permet de faire tourner le robot d'un certain angle
                  Un asservissement en position est utilisé pour que le robot tourne droit
  */

  // Variables locales
  float new_theta; // Nouvelle orientation du robot
  float angle_parcouru; // Angle parcouru par le robot
  float angle_restant; // Angle restant à parcourir
  float vitesse; // Vitesse du robot

  // Initialisation des variables
  new_theta = theta + angle;

  // Calcul de l'angle restant à parcourir
  angle_restant = new_theta - theta;

  // Asservissement en position
  while(angle_restant > 0.1){
    // Calcul de l'angle parcouru
    angle_parcouru = new_theta - theta;

    // Calcul de l'angle restant à parcourir
    angle_restant = new_theta - theta;

    // Calcul de la vitesse du robot
    vitesse = 100 * angle_restant / angle_parcouru;

    // Asservissement en vitesse
    moteurGauche.setVitesse(vitesse);
    moteurDroit.setVitesse(-vitesse);

    // Mise à jour des données
    mise_a_jour_donnees();
  }
  return true;
}

bool aller_a(float x, float y){
  /*
    Input : x : position en x à atteindre (float)
            y : position en y à atteindre (float)
    Output : none
    Description:  Cette fonction permet de faire aller le robot à une certaine position
                  Un asservissement en position est utilisé pour que le robot aille droit
  */

  // Variables locales
  float distance_parcourue; // Distance parcourue par le robot
  float distance_restante; // Distance restante à parcourir
  float vitesse; // Vitesse du robot

  // Calcul de la distance restante à parcourir
  distance_restante = sqrt(pow(x - x, 2) + pow(y - y, 2));

  // Asservissement en position
  while(distance_restante > 0.1){
    // Calcul de la distance parcourue
    distance_parcourue = sqrt(pow(x - x, 2) + pow(y - y, 2));

    // Calcul de la distance restante à parcourir
    distance_restante = sqrt(pow(x - x, 2) + pow(y - y, 2));

    // Calcul de la vitesse du robot
    vitesse = 100 * distance_restante / distance_parcourue;

    // Asservissement en vitesse
    moteurGauche.setVitesse(vitesse);
    moteurDroit.setVitesse(vitesse);

    // Mise à jour des données
    mise_a_jour_donnees();
  }
  return true;
}

bool aller_a(float x, float y, float theta){
  /*
    Input : x : position en x à atteindre (float)
            y : position en y à atteindre (float)
            theta : orientation à atteindre (float)
    Output : none
    Description:  Cette fonction permet de faire aller le robot à une certaine position
                  Un asservissement en position est utilisé pour que le robot aille droit
  */

  // Variables locales
  float distance_parcourue; // Distance parcourue par le robot
  float distance_restante; // Distance restante à parcourir
  float vitesse; // Vitesse du robot
  float angle_parcouru; // Angle parcouru par le robot
  float angle_restant; // Angle restant à parcourir

  // Calcul de la distance restante à parcourir
  distance_restante = sqrt(pow(x - x, 2) + pow(y - y, 2));

  // Calcul de l'angle restant à parcourir
  angle_restant = theta - theta;

  // Asservissement en position
  while(distance_restante > 0.1 || angle_restant > 0.1){
    // Calcul de la distance parcourue
    distance_parcourue = sqrt(pow(x - x, 2) + pow(y - y, 2));

    // Calcul de la distance restante à parcourir
    distance_restante = sqrt(pow(x - x, 2) + pow(y - y, 2));

    // Calcul de l'angle parcouru
    angle_parcouru = theta - theta;

    // Calcul de l'angle restant à parcourir
    angle_restant = theta - theta;

    // Calcul de la vitesse du robot
    vitesse = 100 * distance_restante / distance_parcourue;

    // Asservissement en vitesse
    moteurGauche.setVitesse(vitesse);
    moteurDroit.setVitesse(vitesse);

    // Mise à jour des données
    mise_a_jour_donnees();
  }
  return true;
}
