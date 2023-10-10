#include <Arduino.h>
#include <Wire.h>
#include "Bouton.h"

/*-------------------------------- DEFINE --------------------------------------*/

// define pour les boutons
#define NOIR 0
#define BLEU 1
#define VERT 2
#define DEPART 3


/*---------------------- Constructeur Bibliothèque -----------------------------*/

Bouton bt[4];         // création d'un tableau de 3 boutons

/*----------------------- Prototypes des fonctions -----------------------------*/
// Fonction pour la bibliothèque Bouton
void setup_bt(int nb_bt);
void read_bt(int nb_bt);

// Fonction test
void testMoteur(void);
void testEncodeur(void);

// Fonction utilitaire
bool readDigital(int pin);

// Fonction moteur
void smoothMoteur();
void moteurGauche(int vitesse);
void moteurDroit(int vitesse);
void moteur(void);
void setVitesseGauche(int vitesse);
void setVitesseDroit(int vitesse);
void setSensDroit(bool sensD);
void setSensGauche(bool sensG);
void setSpeed(float cmd);

/*---------------------- Variable des pins de sortis ---------------------------*/
// Aucune des pins ne sont bien définies, il faut les définir en fonction des branchements
// Pin des moteurs
const int pinMotGaucheSens = 26;
const int pinMotGauchePWM = 14;
const int pinMotDroitSens = 25;
const int pinMotDroitPWM = 27;

// Pin des encodeurs
const int pinEncodeurGaucheA = 33;
const int pinEncodeurGaucheB = 13;
const int pinEncodeurDroitA = 17;
const int pinEncodeurDroitB = 16;

const int pinLed = 19;
const int pinBoutonJaune = 35;
const int pinBoutonBleu = 4;
const int pinBoutonVert = 32;

/*-------------------------- Variables pour les boutons -------------------------*/
// Pin des boutons
const int button_pin[4] = {pinBoutonJaune, pinBoutonBleu, pinBoutonVert, 0};

/*----------------------------- Variables systèmes ------------------------------*/
// Machine à état
int etat_suivie = 0;
int etat_sys = 0;
int etat_test_moteur = 0;

unsigned long temps_test = 0;
unsigned long time_course = 0;

// Temps de délai pour les boutons
int t_delay_click = 140;
int t_delay_press = 1500;
int t_delay_bounce = 120;

// Moteur
int ledc_channel[2] = {2, 3};
int vitesse_actuelle[2] = {0, 0};
int vitesse_consigne[2] = {0, 0};
bool sens_actuelle[2] = {0, 0};
bool sens_consigne[2] = {0, 0};
unsigned long temps_mot[2] = {0, 0};
unsigned long temps_course = 0;
unsigned long millis_avant = 0;

float coefLigneDroite = 0.98;

void setup()
{
  Wire.begin();
  delay(100);

  // put your setup code here, to run once:
  Serial.begin(9600);
  pinMode(pinMotGaucheSens, OUTPUT);
  pinMode(pinMotDroitSens, OUTPUT);
  pinMode(pinEncodeurGaucheA, INPUT);
  pinMode(pinEncodeurGaucheB, INPUT);
  pinMode(pinEncodeurDroitA, INPUT);
  pinMode(pinEncodeurDroitB, INPUT);
  pinMode(pinBoutonJaune, INPUT);
  pinMode(pinBoutonBleu, INPUT);
  pinMode(pinBoutonVert, INPUT);
  pinMode(pinLed, OUTPUT);

  // initialisation des moteurs
  ledcSetup(ledc_channel[0], 20000, 8);
  ledcSetup(ledc_channel[1], 20000, 8);
  ledcAttachPin(pinMotGauchePWM, ledc_channel[1]);
  ledcAttachPin(pinMotDroitPWM, ledc_channel[0]);
  ledcWrite(ledc_channel[0], 0);
  ledcWrite(ledc_channel[1], 0);

  // initialisation des boutons
  setup_bt(4);
}

void loop()
{
  read_bt(4);
  switch (etat_sys)
  {
  case 0:
    // Etat 0 : Attente du départ
    if(bt[NOIR].click())
    {
      etat_sys = 1;
      temps_test = millis();
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
// Fonction de test des moteurs
void testMoteur(void)
{
  moteur();

  if (millis() > temps_test + 2000)
  {
    etat_test_moteur++;
    temps_test = millis();
  }

  // test des moteurs
  switch (etat_test_moteur)
  {
  case 0:
    setVitesseDroit(0);
    setVitesseGauche(240);
    setSensGauche(true);
    break;
  case 1:
    setVitesseGauche(0);
    if (vitesse_actuelle[1] == vitesse_consigne[1])
    {
      etat_test_moteur++;
      temps_test = millis();
    }
    break;
  case 2:
    setVitesseGauche(240);
    setSensGauche(false);
    break;
  case 3:
    setVitesseGauche(0);
    if (vitesse_actuelle[1] == vitesse_consigne[1])
    {
      etat_test_moteur++;
      temps_test = millis();
    }
  case 4:
    setVitesseDroit(240);
    setVitesseGauche(0);
    setSensDroit(true);
    break;
  case 5:
    setVitesseDroit(0);
    if (vitesse_actuelle[0] == vitesse_consigne[0])
    {
      etat_test_moteur++;
      temps_test = millis();
    }
    break;
  case 6:
    setVitesseDroit(240);
    setSensDroit(false);
    break;
  case 7:
    setVitesseDroit(0);
    if (vitesse_actuelle[0] == vitesse_consigne[0])
    {
      etat_test_moteur++;
      temps_test = millis();
    }
  case 8:
    setVitesseDroit(240);
    setVitesseGauche(240);
    setSensDroit(true);
    setSensGauche(true);
    break;
  case 9:
    setVitesseDroit(0);
    setVitesseGauche(0);
    if (vitesse_actuelle[0] == vitesse_consigne[0] && vitesse_actuelle[1] == vitesse_consigne[1])
    {
      etat_test_moteur++;
      temps_test = millis();
    }
    break;
  case 10:
    setVitesseDroit(240);
    setVitesseGauche(240);
    setSensDroit(false);
    setSensGauche(false);
    break;
  case 11:
    setVitesseDroit(0);
    setVitesseGauche(0);
    if (vitesse_actuelle[0] == vitesse_consigne[0] && vitesse_actuelle[1] == vitesse_consigne[1])
    {
      etat_test_moteur++;
      temps_test = millis();
    }
    break;
  case 12:
    setVitesseDroit(240);
    setVitesseGauche(240);
    setSensDroit(true);
    setSensGauche(false);
    break;
  case 13:
    setVitesseDroit(0);
    setVitesseGauche(0);
    if (vitesse_actuelle[0] == vitesse_consigne[0] && vitesse_actuelle[1] == vitesse_consigne[1])
    {
      etat_test_moteur++;
      temps_test = millis();
    }
    break;
  case 14:
    setVitesseDroit(240);
    setVitesseGauche(240);
    setSensDroit(false);
    setSensGauche(true);
    break;
  case 15:
    setVitesseDroit(0);
    setVitesseGauche(0);
    if (vitesse_actuelle[0] == vitesse_consigne[0] && vitesse_actuelle[1] == vitesse_consigne[1])
    {
      etat_test_moteur = 0;
      temps_test = millis();
    }
    break;
  default:
    break;
  }
}
/*
// Fonction de test des encodeurs
void testEncodeur(void)
{
  // test des encodeurs
  // moteur gauche
  if (digitalRead(pinEncodeurGaucheA) == 1 && digitalRead(pinEncodeurGaucheB) == 0)
  {
    printLCD("Gauche : ", 0, 0, true);
    printLCD("Avance", 1, 0, false);
  }
  else if (digitalRead(pinEncodeurGaucheA) == 0 && digitalRead(pinEncodeurGaucheB) == 1)
  {
    printLCD("Gauche : ", 0, 0, true);
    printLCD("Recule", 1, 0, false);
  }
  else
  {
    printLCD("Gauche : ", 0, 0, true);
    printLCD("Arret", 1, 0, false);
  }

  // moteur droit
  if (digitalRead(pinEncodeurDroitA) == 1 && digitalRead(pinEncodeurDroitB) == 0)
  {
    printLCD("Droit : ", 0, 9, true);
    printLCD("Avance", 1, 9, false);
  }
  else if (digitalRead(pinEncodeurDroitA) == 0 && digitalRead(pinEncodeurDroitB) == 1)
  {
    printLCD("Droit : ", 0, 9, true);
    printLCD("Recule", 1, 9, false);
  }
  else
  {
    printLCD("Droit : ", 0, 9, true);
    printLCD("Arret", 1, 9, false);
  }
}
*/
bool readDigital(int pin)
{
  return digitalRead(pin);
}

void moteurGauche(int vitesse)
{
  ledcWrite(ledc_channel[1], (vitesse));
}

void moteurDroit(int vitesse)
{
  ledcWrite(ledc_channel[0], vitesse);
}

void setVitesseGauche(int vitesse)
{
  vitesse_consigne[1] = vitesse;
}

void setVitesseDroit(int vitesse)
{
  vitesse_consigne[0] = vitesse;
}

void setSensGauche(bool sensG)
{
  sens_consigne[1] = sensG;
}

void setSensDroit(bool sensD)
{
  sens_consigne[0] = sensD;
}

void moteur()
{
  //smoothMoteur();
  digitalWrite(pinMotGaucheSens, sens_actuelle[1]);
  digitalWrite(pinMotDroitSens, sens_actuelle[0]);
  moteurGauche(vitesse_actuelle[1]);
  moteurDroit(vitesse_actuelle[0]);
}

void smoothMoteur()
{
  // Cette fonction permet de faire varier la vitesse des moteurs d'une vitesse à une nouvelle vitesse en douceur
  // La vitesse des moteurs varie de 0 à 255

  for (int i = 0; i < 2; i++)
  {
    if (abs(vitesse_actuelle[i] - vitesse_consigne[i]) > 100)
    {
      if (millis() > temps_mot[i] + 2)
      {
        if (vitesse_actuelle[i] < vitesse_consigne[i])
        {
          vitesse_actuelle[i] += 2;
        }
        else if (vitesse_actuelle[i] > vitesse_consigne[i])
        {
          vitesse_actuelle[i] -= 2;
        }
        temps_mot[i] = millis();
      }
    }
    else
    {
      vitesse_actuelle[i] = vitesse_consigne[i];
    }
  }
}

void setSpeed(float cmd)
{
  static float valG, valD;

  valG = 255 * (1.0 + cmd);
  valD = 255 * (1.0 - cmd);
  if (valD < 0)
    valD = 0;
  if (valD > 1)
    valD = 1;
  if (valG < 0)
    valG = 0;
  if (valG > 1)
    valG = 1;

  setVitesseGauche((unsigned int)(255 * valD));
  setVitesseGauche((unsigned int)(255 * valG));
}