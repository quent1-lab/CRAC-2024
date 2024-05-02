#include "Vl53l0x.h"
#include "FreeRTOS.h"
#include "task.h"
#include "semphr.h"
#include "rgb_lcd.h"
#include <Encodeur.h>

Vl53l0x capteur1;
Vl53l0x capteur2;

rgb_lcd lcd;

Encodeur encodeur();

bool detectionCapteur1 = false;
bool detectionCapteur2 = false;

TaskHandle_t Handle_aTask;
TaskHandle_t Handle_bTask;
SemaphoreHandle_t xMutex;

#define BACKWARD 0x1
#define FORWARD 0x0

// static const int16_t MAX = 16384;
int pinDirectionDroit = PA15;
int pinPWMDroit = PA13;
int pinDirectionGauche = PA14;
int pinPWMGauche = PA12;
const int mesureVbat = PB3;
const int TOR1 = 2;
const int TOR2 = 3;

/*----------------------------- Variables pour l'odométrie ------------------------------*/
// Variables pour les compteurs des encodeurs
float rayon = 60;
float entraxe = 100;

float x = 1500;
float y = 1000;
float theta = 0;
int resolution = 2000;
int reduction = 1;
int countD = 0;
int countG = 0;

/*--------------------------- Prototype fonction -------------------------------------*/
void avancer(float distance);
void tourner(float angle);
void aller_a(float x, float y);

int etat = 0;
int dplt = 0;

int mesure_capteur1;
int mesure_capteur2;

int TOR1_precedent = LOW; // laisser en LOW

/// Variable utiliser pour l'asservissemnt de direction
float distance = 0, erreur, commande, commandeTraiter, commandeComp = 0.1, vitesse, Kalpha = 50, PWM, PWMD = 0, PWMG = 0, consDistance = 0;
float m_distance;
float angle_cons_droit, angle_cons_gauche;
float rayonRoue = 60.0;
float vit_ang = 75.0;

float distance_prec_Y = 0;
float distance_prec_X = 1500;

float Te = 10;
float Tc = 50;

int etat_Asserv = 0;
int etat_Ligne_Droite = -1;
int etat_Rotation = -1;

float cons_asserv = 0;
float cons_rotation = 0;
float angle_arrive = 0; // Permet d'enregistrer l'angle d'arrivé

float erreur_moyenne;
float erreur_anglegauche;
float erreur_angleDroit;

float m_newX;
float m_newY;
float angle;

bool is_asserv_X_Y_Theta = false; // Variable permettant de savoir si on est en mode asservissement XYT ou non

bool rotActiver = false;
////////////////////////////////////// Moteur Droit/////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////// Initialisation du moteur Droit/////////////////////////////////////////////////////////////////////////////////////////////////////
void initMoteurDroit()
{
  pinMode(pinPWMDroit, OUTPUT);
  pinMode(pinDirectionDroit, OUTPUT);
}
//////////////////////// Permet de pouvoir déterminer dans un premier comment fonctionne les  moteurs//////////////////////////////////////////////////////
void controleMoteurDroit(int PWM)
{
  if (PWM > 0)
  {
    digitalWrite(pinDirectionDroit, 0);
  }
  if (PWM < 0)
  {
    digitalWrite(pinDirectionDroit, 1);
  }
  PWM = abs(PWM);
  // analogWrite(pinPWMGauche, PWM);
  analogWrite(pinPWMDroit, PWM);
}
////////////////////////////////////// Moteur GAUCHE/////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////// Initialisation du moteur GAUCHE/////////////////////////////////////////////////////////////////////////////////////////////////////
void initMoteurGauche()
{
  pinMode(pinPWMGauche, OUTPUT);
  pinMode(pinDirectionGauche, OUTPUT);
}
//////////////////////// Permet de pouvoir déterminer dans un premier comment fonctionne les  moteurs//////////////////////////////////////////////////////
void controleMoteurGauche(int PWM)
{
  if (PWM < 0)
  {
    digitalWrite(pinDirectionGauche, 1);
  }
  else
  {
    digitalWrite(pinDirectionGauche, 0);
  }
  PWM = abs(PWM);
  analogWrite(pinPWMGauche, PWM);
}

void X_Y_Theta(float x, float y, float theta)
{
  m_newX = x;
  m_newY = y;
  angle_arrive = theta;
  m_distance = sqrt(pow(m_newX - distance_prec_X, 2) + pow(m_newY - distance_prec_Y, 2));

  angle = atan2(m_newY - distance_prec_Y, m_newX - distance_prec_X);

  cons_rotation = degrees(angle);
  cons_asserv = m_distance;
  // etat = 2;
}

void rotation()
{

  // Asservissement en rotation
  switch (etat_Rotation)
  {
  case -1:
    // Serial.print("etat_Rotation ");
    // Serial.println(etat_Rotation);
    break;
  case 0:
    // if (r == 0) {
    etat_Rotation = 1;
    delay(50);
    codeurs.reset();
    delay(1000);
    Serial.println("Reset codeur effecuter");
    delay(1000);
    erreur_moyenne;
    if (cons_rotation > 0)
    {
      cons_rotation = cons_rotation + 20.0;
      angle_cons_droit = cons_rotation / 2.0;
      angle_cons_gauche = -1 * angle_cons_droit;
    }
    if (cons_rotation < 0)
    {
      cons_rotation = cons_rotation - 20.0;
      angle_cons_droit = cons_rotation / 2.0;
      angle_cons_gauche = -1 * angle_cons_droit;
    }

    //   r = 1;
    // }

    break;
  case 1:
    // Serial.println("action rot");
    // /*
    codeurs.read(codeurGauche, codeurDroit);
    erreur_anglegauche = (codeurGauche * rayonRoue * 2.0 / 2048.0) - (2.0 * 3.1415 * 52.0 * angle_cons_droit / 360.0);
    erreur_angleDroit = (codeurDroit * rayonRoue * 2.0 / 2048.0) - (2.0 * 3.1415 * 52.0 * angle_cons_gauche / 360.0);
    erreur_moyenne = (erreur_anglegauche - erreur_angleDroit) / 2.0;

    // Serial.print(" erreur_moyenne ::: ");
    // Serial.print(erreur_moyenne);
    // Serial.print(" Errer dRoit ::: ");
    // Serial.print(erreur_angleDroit);
    // Serial.print("  gauche");
    // Serial.println(erreur_anglegauche);
    if (cons_rotation >= 0)
    {
      if (erreur_moyenne < 0)
      {
        controleMoteurDroit(-vit_ang - (commandeComp * 255.0));
        controleMoteurGauche(vit_ang + (commandeComp * 255.0));
      }
      if (erreur_moyenne > 0)
      {
        controleMoteurDroit(0);
        controleMoteurGauche(0);
        etat_Rotation = 2;
      }
    }
    else
    {
      if (erreur_moyenne > 0)
      {
        controleMoteurDroit(20 + (commandeComp * 255.0));
        controleMoteurGauche(-20 - (commandeComp * 255.0));
      }
      if (erreur_moyenne < 0)
      {
        controleMoteurDroit(0);
        controleMoteurGauche(0);
        etat_Rotation = 2;
      }
    }
    // if ((erreur_moyenne < -2) && (erreur_moyenne > 1.5)) {
    // }
    // Serial.print("etat rotation ");
    // Serial.println(etat_Rotation);
    // Serial.print("erreur ");
    // Serial.println(erreur_moyenne);
    // */
    break;

  case 2:
    controleMoteurDroit(0);
    controleMoteurGauche(0);
    etat_Rotation = -1;
    etat = 3;
    break;
  default:
    Serial.println("probleme");
    break;
  }
}

void controle(void *parameters)
{
  TickType_t xLastWakeTime;
  xLastWakeTime = xTaskGetTickCount();

  while (1)
  {
    xSemaphoreTake(xMutex, portMAX_DELAY);
    // taskYIELD();

    int etat_TOR1 = digitalRead(TOR1);
    int etat_TOR2 = digitalRead(TOR2);
    float vbat = analogRead(mesureVbat);
    float tensionBat = (vbat / 895) * 3.3;
    tensionBat = tensionBat * (7.2 / 3.3);

    encodeur.odometrie();

    switch (etat)
    {
    case 0:
      if (etat_TOR1 == HIGH)
      {
        etat = 1;
      }
      break;
    case 1:
      avancer(100);
      Serial.println("Calcul effectuer");
      etat = 2;
      break;
    case 2:
      tourner(PI);
      etat = 3;
      break;
    case 3:
      avancer(100);
      etat = 4;
      break;
    case 4:
      lcd.clear();
      lcd.setRGB(255, 0, 255);
      lcd.print("case 4");
      break;
    default:
      break; // break
    }
    TOR1_precedent = etat_TOR1;
    // Serial.println("Controle");
    xSemaphoreGive(xMutex);

    vTaskDelayUntil(&xLastWakeTime, pdMS_TO_TICKS(Te));
  }
}

void setup()
{
  Serial.begin(115200);

  // VL53L0X_Error status1 = VL53L0X_ERROR_NONE;

  lcd.begin(16, 2);
  lcd.setRGB(0, 0, 255);

  // NE PAS OUBLIER DE METTRE INPUT_PULLUP
  pinMode(TOR1, INPUT_PULLUP);
  pinMode(TOR2, INPUT_PULLUP);
  pinMode(mesureVbat, INPUT);

  initMoteurDroit();
  initMoteurGauche();

  // Initialisation des encodeurs
  encodeur.init(x, y, theta, rayon, entraxe, reduction, resolution);

  xMutex = xSemaphoreCreateMutex();                        // Create a mutex
  xTaskCreate(controle, "Controle", 1000, NULL, 20, NULL); // Create a task
  delay(500);
  Serial.println("tache controle ok");
}

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

    controleMoteurGauche(vitesseG/100.0*255.0);
    controleMoteurDroit(vitesseD/100.0*255.0);
  }
  controleMoteurGauche(2);
  controleMoteurDroit(2);
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

    controleMoteurGauche(vitesseG/100.0*255.0);
    controleMoteurDroit(vitesseD/100.0*255.0);
  }
  controleMoteurGauche(2);
  controleMoteurDroit(2);
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


void deplacement(void *pvParameters)
{
  TickType_t xLastWakeTime;
  xLastWakeTime = xTaskGetTickCount();
  int i = 0;

  while (1)
  {
    // xSemaphoreTake(xMutex, portMAX_DELAY);

    // FAIS PLANTER LA TACHE
    // int etat_TOR1 = digitalRead(TOR1);
    // int etat_TOR2 = digitalRead(TOR2);

    // float vbat = analogRead(mesureVbat);
    // float tensionBat = (vbat / 895) * 3.3;
    // tensionBat = tensionBat * (7.2 / 3.3);

    // lcd.clear();
    // lcd.setRGB(255,0,0);
    // lcd.setCursor(7, 0);
    // lcd.print("v: ");
    // lcd.setCursor(12, 0);
    // lcd.print(tensionBat);
    // //xSemaphoreGive(xMutex);
    // lcd.setCursor(0,0);
    // lcd.print("cpt1: ");
    // lcd.setCursor(5,0);
    // lcd.print(mesure_capteur1);
    // lcd.setCursor(0,1);
    // lcd.print("cpt2: ");
    // lcd.setCursor(8,1);
    // lcd.print(mesure_capteur2);

    // lcd.setRGB(255,0,255);
    // lcd.clear();
    // lcd.print("tache 1");
    // lcd.setCursor(0,1);
    // lcd.print(i);
    // lcd.setCursor(5,1);
    // lcd.print(etat_TOR1);
    // i++;
    // if (i >= 100){
    //   i=0;
    // }

    // FONCTIONNEL

    // switch(dplt){
    //   case 0:
    //   //lcd.setRGB(255,0,0);
    //   controleMoteurDroit(0);
    //   controleMoteurGauche(0);
    //   // lcd.clear();
    //   // lcd.print("dplt 0");
    //   // if (etat_TOR1 != TOR1_precedent) {
    //       if (etat_TOR1 == HIGH) { //ETAT_TOR1
    //         dplt = 1;
    //       }
    //     // }
    //   break;
    //   case 1:
    //   controleMoteurDroit(75);
    //   controleMoteurGauche(75);
    //   if(mesure_capteur1 >= 2000 && mesure_capteur2 >= 2000){
    //     dplt = 0;
    //   }
    //   break;
    //  }

    if (mesure_capteur1 >= 2000)
    {
      Serial.println("capteur1 out of range");
    }
    else if (mesure_capteur2 >= 2000)
    {
      Serial.println("capteur 2 out of range");
    }
    else
    {
      Serial.print("distance capteur 1: ");
      Serial.print(mesure_capteur1);
      Serial.print(" distance capteur 2: ");
      Serial.print(mesure_capteur2);
      Serial.print(" Encodeurs: ");
      Serial.print(codeurGauche);
      Serial.print(" ");
      Serial.println(codeurDroit);
    }

    vTaskDelay(pdMS_TO_TICKS(100));
  }
}

void readSensors(void *pvParameters)
{
  while (1)
  {
    xSemaphoreTake(xMutex, portMAX_DELAY); // Take the mutex before accessing I2C

    VL53L0X_RangingMeasurementData_t rangingMeasurementData1;
    VL53L0X_RangingMeasurementData_t rangingMeasurementData2;
    capteur1.performContinuousRangingMeasurement(&rangingMeasurementData1);
    capteur2.performContinuousRangingMeasurement(&rangingMeasurementData2);
    // codeurs.read(codeurGauche, codeurDroit);
    mesure_capteur1 = rangingMeasurementData1.RangeMilliMeter;
    mesure_capteur2 = rangingMeasurementData2.RangeMilliMeter;
    xSemaphoreGive(xMutex); // Give the mutex back after accessing I2C

    // X_Y_Theta(2000,1200,0);

    // lcd.clear();
    // lcd.setCursor(0,0);
    // lcd.print("dist capt1: ");
    // lcd.print(rangingMeasurementData1.RangeMilliMeter);
    // lcd.setCursor(0, 1);
    // lcd.print("dist capt 2: ");
    // lcd.print(rangingMeasurementData2.RangeMilliMeter);

    // if (rangingMeasurementData1.RangeMilliMeter >= 2000) {
    //   Serial.println("capteur1 out of range");
    // } else if (rangingMeasurementData2.RangeMilliMeter >= 2000) {
    //   Serial.println("capteur 2 out of range");
    // } else {
    //   Serial.print("distance capteur 1: ");
    //   Serial.print(rangingMeasurementData1.RangeMilliMeter);
    //   Serial.print(" distance capteur 2: ");
    //   Serial.print(rangingMeasurementData2.RangeMilliMeter);
    //   Serial.print(" Encodeurs: ");
    //   Serial.print(codeurGauche);
    //   Serial.print(" ");
    //   Serial.println(codeurDroit);
    // }

    vTaskDelay(pdMS_TO_TICKS(10)); // Delay for 100ms
  }
}

void loop()
{
  taskYIELD();
}
