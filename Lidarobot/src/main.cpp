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

// Fonction test
void testEncodeur(void);
void testMoteur(void);

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
Moteur moteurDroit(pinMotDroitSens, pinMotDroitPWM, 1);

Encodeur encodeur(pinEncodeurDroitA, pinEncodeurDroitB, pinEncodeurGaucheA, pinEncodeurGaucheB);

void setup()
{
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(pinLed, OUTPUT);

  // Initialisation des moteurs et des encodeurs
  moteurGauche.init();
  moteurDroit.init();

  // Initialisation des encodeurs
  encodeur.init(x, y, theta, rayon);

  // initialisation des boutons
  setup_bt(3);
}

void loop()
{
  read_bt(3);
  testEncodeur();
  switch (etat_sys)
  {
  case 0:
    // Etat 0 : Attente du départ

    if (bt[NOIR].click())
    {
      etat_sys = 1;
    }
    break;
  case 1:
    // Etat 1 : Test des moteurs
    digitalWrite(pinLed, HIGH);
    testMoteur();
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
  encodeur.print();
  envoie_JSON();
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

void test_ligne_droite(){
  //Fait avancer le robot en ligne droite afin de vérifier si le robot avance droit
  //Et trouve le coefficient de proportionnalité pour que les roues tournent à la même vitesse
  static int etat = 0;
  static unsigned long t0 = millis();
  static float vitesse = 0;
  static float coefficient = 0;
  float vitesseMotDroit, vitesseMotGauche;

  switch (etat)
  {
  case 0:
    // Etat 0 : Avancer
    moteurGauche.setVitesse(vitesse);
    moteurDroit.setVitesse(vitesse);
    if (millis() - t0 > 1000)
    {
      etat = 1;
      vitesseMotDroit = encodeur.readEncoderD() / 1000.0;
      vitesseMotGauche = encodeur.readEncoderG() / 1000.0;
      if(vitesseMotDroit < 0){
        vitesseMotDroit = -vitesseMotDroit;
        Serial.println("le moteur droit tourne à l'envers\n");
      }
      if(vitesseMotGauche < 0){
        vitesseMotGauche = -vitesseMotGauche;
        Serial.println("le moteur gauche tourne à l'envers\n");
      }
      t0 = millis();
    }
    break;
  case 1:
    // Etat 1 : Arrêt
    moteurGauche.setVitesse(0);
    moteurDroit.setVitesse(0);
    if (millis() - t0 > 1000)
    {
      etat = 2;
      t0 = millis();
    }
    break;
  case 2:
    // Etat 2 : Caclul du coefficient
    // Calcul de la vitessse en fonction du temps
    coefficient = (vitesseMotDroit - vitesseMotGauche) / (vitesseMotDroit + vitesseMotGauche);
    printf("coefficient : %f\n", coefficient);
    encodeur.reset();
    etat = 3;
    break;
  case 3:
    // Etat 3 : Avancer
    moteurGauche.setVitesse(vitesse);
    moteurDroit.setVitesse(vitesse * coefficient);
    if (millis() - t0 > 1000)
    {
      etat = 4;
      vitesseMotDroit = encodeur.readEncoderD() / 1000;
      vitesseMotGauche = encodeur.readEncoderG() / 1000;
      t0 = millis();
    }
    break;
  case 4:
    // Etat 4 : Arrêt
    moteurGauche.setVitesse(0);
    moteurDroit.setVitesse(0);
    if (millis() - t0 > 1000)
    {
      etat = 5;
      t0 = millis();   
      float new_coefficient = (vitesseMotDroit - vitesseMotGauche) / (vitesseMotDroit + vitesseMotGauche);
      printf("new_coefficient : %f\n", new_coefficient);
      if(coefficient - new_coefficient < 0.1){
        printf("Le robot avance droit\n");
      }
      else{
        printf("Le robot n'avance pas droit\n");
      }
      etat_sys = 0;
    }
    break;
  }