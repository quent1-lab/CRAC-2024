#include <Arduino.h>
#include <Wire.h>
#include "Bouton.h"
#include "Moteur.h"
#include <Encoder.h>
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

// Fonction test
void testEncodeur(void);

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
int etat_sys = 10;

// Temps de délai pour les boutons
int t_delay_click = 140;
int t_delay_press = 1500;
int t_delay_bounce = 120;

// Variables pour les compteurs des encodeurs
float rayon = 0.022;

/*----------------------------- Variables pour l'odométrie ------------------------------*/
float x = 0;
float y = 0;
float theta = 0;

/*---------------------- Constructeur Bibliothèque -----------------------------*/

Bouton bt[3]; // création d'un tableau de 3 boutons.

// Déclaration des moteurs et encodeurs en tant qu'instances des classes Moteur et Encodeur
Moteur moteurGauche(pinMotGaucheSens, pinMotGauchePWM);
Moteur moteurDroit(pinMotDroitSens, pinMotDroitPWM);

Encoder encoder;


void setup()
{
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(pinLed, OUTPUT);

  // Initialisation des moteurs et des encodeurs
  moteurGauche.init();
  moteurDroit.init();

  // initialisation des encodeurs
  encoderD.attachHalfQuad(pinEncodeurDroitA, pinEncodeurDroitB);
  encoderG.attachHalfQuad(pinEncodeurGaucheA, pinEncodeurGaucheB);

  // set starting count value after attaching
  encoderD.setCount(0);
  encoderG.setCount(0);

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
    
    break;
  default:

    break;
  }

  // moteur();
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
  odometrie(&x, &y, &theta);
}

/*---------------------- Fonction des encodeurs ---------------------------*/
int readEncoderRight()
{
  return encoderD.getCount();
}

int readEncoderLeft()
{
  return encoderG.getCount();
}

void odometrie(float* x, float* y, float* theta)
{
  // Cette fonction permet de calculer la position du robot en fonction des encodeurs

  // Variables locales  
  float deltaD, deltaG, deltaT, deltaS;
  float x0, y0, vitesse0;

  // Lecture des encodeurs
  deltaD = readEncoderRight() - oldPositionD;
  deltaG = readEncoderLeft() - oldPositionG;

  // Calcul de la distance parcourue par chaque roue
  deltaD = deltaD * 2 * PI * rayon / 360;
  deltaG = deltaG * 2 * PI * rayon / 360;

  // Calcul de la distance parcourue par le robot
  deltaS = (deltaD + deltaG) / 2;

  // Calcul de la variation d'angle en fonction de l'entraxe 
  deltaT = (deltaD - deltaG) / 90;

  // Calcul de la nouvelle position
  *x = *x + deltaS * cos(*theta + deltaT / 2);
  *y = *y + deltaS * sin(*theta + deltaT / 2);
  *theta = *theta + deltaT;

  // Mise à jour des variables
  oldPositionD = readEncoderRight();
  oldPositionG = readEncoderLeft();

  // Affichage des variables
  Serial.print("x = ");
  Serial.print(*x);
  Serial.print(" y = ");
  Serial.print(*y);
  Serial.print(" theta = ");
  Serial.println(*theta);
}