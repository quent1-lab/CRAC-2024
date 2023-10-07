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
void printLCD(String message, int ligne, int colonne, bool effacer);
int readAnalog(int pin);
bool readDigital(int pin);
float analog1(int pin);
int analog100(int pin);

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

// Fonction course
void suivieLigne(void);
void suivie(void);


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
const int pinBuzzer = 5;
const int pinBoutonJaune = 35;
const int pinBoutonBleu = 4;
const int pinBoutonVert = 32;

/*-------------------------- Variables pour les boutons -------------------------*/
// Pin des boutons
const int button_pin[4] = {pinBoutonJaune, pinBoutonBleu, pinBoutonVert, 0};

/*----------------------------- Variables systèmes ------------------------------*/
// Machine à état
int etat_suivie = 0;
int etat_sys = 1;
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


/*-------------------------------- Variable asservissement --------------------------------------------*/
// Asservissement
float Kp = 0.55;
float Kd = 0.5;
float vmax = 0;
float vitesse_max = 80.0;
float servooo = 0;
float erreur = 0;
float erreur_1 = 0;
float deriv = 0;
float commande = 0;

float distance;

int last_G_D = 0;
int compteur = 0;
int compteur1 = 0;
int compteur_crois = 0;

int capteurAv[4] = {0};
int capteurAr[2] = {0};

float Cig = 0;
float Cid = 0;
float Cag = 0;
float Cad = 0;

float CigMax = 1050.0;
float CigMin = 140.0;
float CidMax = 1050.0;
float CidMin = 140.0;

float coefLigneDroite = 0.98;

bool marque_d = false;
bool marque_d2 = false;
bool marque_g = false;
bool croisement = false;
bool cha11 = false;

float gyro[3] = {0};
float angle[3] = {0};

int compteur2 = 0;
int compteur3 = 0;

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
  pinMode(pinBuzzer, OUTPUT);
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
  etat_sys = 1;
  switch (etat_sys)
  {
  case 0:
    // Etat 0 : TEST
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
  if (millis() > temps_test + 2000)
  {
    etat_test_moteur++;
    temps_test = millis();
  }

  // test des moteurs
  switch (etat_test_moteur)
  {
  case 0:
    printLCD("Moteur", 0, 0, true);
    printLCD("Niveau : ", 1, 0, false);
    printLCD("1", 1, 9, false);

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
    printLCD("2", 1, 9, false);
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
    printLCD("3", 1, 9, false);

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
    printLCD("4", 1, 9, false);
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
    printLCD("5", 1, 9, false);
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
    printLCD("6", 1, 9, false);
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
    printLCD("7", 1, 9, false);
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
    printLCD("8", 1, 9, false);
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
  printLCD(String(digitalRead(pinEncodeurDroitB)), 1, 12, false);
}

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

// Fonction print LCD
void printLCD(String message, int ligne, int colonne, bool effacer){
  return;
}

int readAnalog(int pin)
{
  return analogRead(pin);
}

int analog100(int pin)
{
  return map(analogRead(pin), 0, 4095, 0, 100);
}

float analog1(int pin)
{
  return (analogRead(pin) / 4095.0);
}

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
  smoothMoteur();
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

  valG = vmax * (1.0 + cmd);
  valD = vmax * (1.0 - cmd);
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

void getCapteurAv(void)
{
  // Cette fonction permet de lire les capteurs avant et de les stocker dans un tableau
  // Les capteurs sont numérotés de 0 à 3
}

void getCapteurAr(void)
{
}

/*-----------------------------------------− Suivie de ligne --------------------------------------------*/

void suivieLigne(void)
{
  // Suivie d'une ligne noire sur fond blanc (noir = 0, blanc = 1050)
  // La ligne est comprise entre les capteurs 2 et 3

  if (CigMax < capteurAv[1])
    CigMax = capteurAv[1];
  if (CigMin > capteurAv[1])
    CigMin = capteurAv[1];
  if (CidMax < capteurAv[2])
    CidMax = capteurAv[2];
  if (CidMin > capteurAv[2])
    CidMin = capteurAv[2];

  Cig = (capteurAv[1] - CigMin) / (CigMax - CigMin);
  Cid = (capteurAv[2] - CidMin) / (CidMax - CidMin);

  erreur = Cig - Cid;
  time_course = millis() - time_course;
  deriv = 8 * 4000 * (erreur - erreur_1) / time_course;
  time_course = millis();
  erreur_1 = erreur;
  commande = Kp * erreur + Kd * deriv;

  printLCD("Cig:" + String(Cig), 0, 0, true);
  printLCD("Cid:" + String(Cid), 0, 9, false);
  printLCD("Erreur : " + String(erreur), 1, 0, false);

  switch (etat_suivie)
  {
  case (0):
    // INIT
    printLCD("Attente depart", 0, 1, true);
    delay(10);
    if (bt[3].click())
    {
      temps_course = millis();
      etat_suivie = 1;
      // klaxon_reset();
    }
    break;
  case (1):
    // COURSE
    setSpeed(commande);
    break;
  default:
    break;
  }
  /*
    if (erreur > 0.1)
    {
      setVitesseGauche(vitesse_max);
      setVitesseDroit(vitesse_max * (1 - erreur));
    }
    else if (erreur < -0.1)
    {
      setVitesseGauche(vitesse_max * (1 + erreur));
      setVitesseDroit(vitesse_max);
    }
    else
    {
      setVitesseGauche(vitesse_max);
      setVitesseDroit(vitesse_max);
    }*/
}

void suivie()
{
  Cig = 100 - ((capteurAv[1] * 100) / 1050);
  Cid = 100 - ((capteurAv[2] * 100) / 1050);

  int G__D = (Cig - Cid);

  printLCD("Cig:" + String(Cig), 0, 0, true);
  printLCD("Cid:" + String(Cid), 0, 9, false);
  printLCD("G__D:" + String(G__D), 1, 0, false);
  printLCD("etat:" + String(etat_suivie), 1, 9, false);

  switch (etat_suivie)
  {
  case (0):
    // INIT
    printLCD("Attente depart", 0, 1, true);
    delay(10);
    if (bt[3].click())
    {
      //lcd.clear();
      temps_course = millis();
      etat_suivie = 1;
      // klaxon_reset();
    }
    break;
  case (1):
    moteurDroit(vitesse_max);
    moteurGauche(vitesse_max);
    if (G__D > 0)
      etat_suivie = 2;
    if (G__D < 0)
      etat_suivie = 3;
    break;
  case (2): // Dérive vers la droite
  {
    float vit = (G__D * Kp + (Kd * (G__D - last_G_D)));

    moteurDroit(vitesse_max + vit);
    moteurGauche(vitesse_max - vit);

    if (G__D <= 0)
      etat_suivie = 1;
    /*if (Cig > 80)
      etat_suivie = 4;*/
    break;
  }
  case (3): // Dérive vers la gauche
  {
    float vit = (G__D * Kp + (Kd * (G__D - last_G_D))); // normalement néfatif

    moteurDroit(vitesse_max + vit);
    moteurGauche(vitesse_max - vit);

    if (G__D >= 0)
      etat_suivie = 1;
    /*if (Cid > 80)
      etat_suivie = 5;*/
    break;
  }
  case (4): // Rattrapge vers la gauche
    setVitesseDroit(vitesse_max * 0.9);
    setVitesseGauche(vitesse_max * 0.2);

    if (Cid > 20)
      etat_suivie = 1;
  case (5): // Rattrapage vers la droite
    setVitesseDroit(vitesse_max * 0.2);
    setVitesseGauche(vitesse_max * 0.9);

    if (Cig > 20)
      etat_suivie = 1;
    break;
  }
  last_G_D = G__D;
  millis_avant = millis();
}
