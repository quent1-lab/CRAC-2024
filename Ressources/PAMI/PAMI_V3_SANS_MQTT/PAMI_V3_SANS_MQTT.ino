#include "Vl53l0x.h"
#include "FreeRTOS.h"
#include "task.h"
#include "semphr.h"
#include "rgb_lcd.h"
#include <Encodeur.h>
#include <queue>
#include <SoftwareSerial.h>
#include <HerkulexServo.h>



/*----------------------------- Variables pour l'herkulex ------------------------------*/

#define PIN_SW_RX PB2
#define PIN_SW_TX PB1
#define SERVO_ID  0xFD

#define ouvert 590
#define ferme 907
#define serre 700 //780 750


SoftwareSerial   servo_serial(PIN_SW_RX, PIN_SW_TX);
HerkulexServoBus herkulex_bus(servo_serial);
HerkulexServo    herkulex(herkulex_bus, SERVO_ID);

int mouvement;

unsigned long last_update = 0;
unsigned long now = 0;
bool toggle = false;


/*-------------------------------------------------------------------------------------*/

#define PI 3.14159265358979323846

Vl53l0x capteur1;
Vl53l0x capteur2;

rgb_lcd lcd;

Encodeur encodeur;

TaskHandle_t Handle_aTask;
TaskHandle_t Handle_bTask;
SemaphoreHandle_t xMutex;

#define BACKWARD 0x1
#define FORWARD 0x0

#define COEFFROUEDROITE 1.013 //1.04 pour 20 de vitesse  1.013 pour 50 de vitesse 
#define COEFFROUEGAUCHE 1.0 

// static const int16_t MAX = 16384;
const int pinDirectionDroit = PA14;
const int pinPWMDroit = PA12;
const int pinDirectionGauche = PA15;
const int pinPWMGauche = PA13;
const int mesureVbat = PB3;
const int TOR1 = 2;
const int TOR2 = 3;

int etat_TOR1;
int etat_TOR2;

bool detectionCapteur1 = false; 
bool detectionCapteur2 = false;
bool init_capteurs = false;
/*----------------------------- Variables pour l'odométrie ------------------------------*/
// Variables pour les compteurs des encodeurs
float rayon = 31.2;
float entraxe = 100; //101 //distance entre les roues

int vitesse = 50;

float x = 0;
float y = 0;
float theta = 0;
int resolution = 2000;
int reduction = 1;
int32_t countD = 0;
int32_t countG = 0;

/*--------------------------- Prototype fonction -------------------------------------*/
void avancer(float distance);
void tourner(float angle);
void aller_a(float X, float Y,float angle_arrivee);
void avancer_non_bloquant();
void tourner_non_bloquant();
void controleMoteurDroit(int PWM);
void controleMoteurGauche(int PWM);
void initMoteurDroit();
void initMoteurGauche();
void odo(void *parameters);
void controle(void *parameters);
float asservissement_pas_Droit(float consigne);
float asservissement_pas_Gauche(float consigne);
void ajouterActionAvancer(float distance);
void ajouterActionTourner(float angle);

/*--------------------------- Variables pour le controle -------------------------------------*/
float distance_to_travel = 0;
float nbr_pas_a_parcourir = 0;
int pas_gauche = 0;
int pas_droit = 0;
float angle_to_turn = 0;
int sens = 0;

int etat = 0;

int mesure_capteur1;
int mesure_capteur2;

int TOR1_precedent = LOW; // laisser en LOW

/*----------------------- Variables asservissement ---------------------------*/
float Kp = 0.001;
float Ki = 0.000001;
float Kd = 0.00001;
float erreur_precedente_G = 0;
float somme_erreur_G = 0;
float erreur_precedente_D = 0;
float somme_erreur_D = 0;

float Te = 5; // Delai de 5ms pour le controle
float Tc = 5; // Delai de 1ms pour la récuperation des données des encodeurs
float Ta = 5; // Delai de 1ms pour l'asservissement

enum RobotState
{
  IDLE,
  AVANCER,
  TOURNER,
  STOP,
  HERKULEX
};
RobotState state = IDLE;

enum ActionType
{
  AVANCER_,
  TOURNER_,
  HERKULEX_
};

struct Action
{
  ActionType type;
  float value;
};

std::queue<Action> actions; // Liste des actions à effectuer

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
  analogWrite(pinPWMDroit, PWM * COEFFROUEDROITE);
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
  analogWrite(pinPWMGauche, PWM * COEFFROUEGAUCHE);
}

void odo(void *parameters)
{
  TickType_t xLastWakeTime;
  xLastWakeTime = xTaskGetTickCount();

  while (1)
  {
    xSemaphoreTake(xMutex, portMAX_DELAY);

    encodeur.odometrie();
    countD = encodeur.get_countD() * (-1);
    countG = encodeur.get_countG() * (-1);

    
    //VL53L0X_RangingMeasurementData_t rangingMeasurementData1;
    // VL53L0X_RangingMeasurementData_t rangingMeasurementData2;
    //capteur1.performContinuousRangingMeasurement(&rangingMeasurementData1);
    // capteur2.performContinuousRangingMeasurement(&rangingMeasurementData2);
    // mesure_capteur1 = rangingMeasurementData1.RangeMilliMeter;
    // mesure_capteur2 = rangingMeasurementData2.RangeMilliMeter;

  // if(mesure_capteur1 > 2000){
  //   state = STOP;
  //   etat=0;
  // }else if(mesure_capteur2 >2000){
  //   state=STOP;
  //   etat=0;
  // }else{
  //   state = IDLE;
  //   etat=1;
  // }

    //encodeur.print(countD, countG);

    xSemaphoreGive(xMutex);
    vTaskDelayUntil(&xLastWakeTime, pdMS_TO_TICKS(Tc));
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

    etat_TOR1 = digitalRead(TOR1);
    etat_TOR2 = digitalRead(TOR2);
    float vbat = analogRead(mesureVbat);
    float tensionBat = (vbat / 895) * 3.3;
    tensionBat = tensionBat * (7.2 / 3.3);

    avancer_non_bloquant();
    tourner_non_bloquant();

    switch (etat)
    {
    case 0:
      if (etat_TOR1 == HIGH)
      {
        etat = 1;
      }
      controleMoteurDroit(int(asservissement_pas_Droit(pas_droit) * (255) * (1.1)));
      controleMoteurGauche(int(asservissement_pas_Gauche(pas_gauche) * (255) * (1.1)));
      break;
    case 1:
      if (state == IDLE && !actions.empty() && state !=STOP)
      {
        Action action = actions.front();
        actions.pop();

        switch (action.type)
        {
        case AVANCER_:
          avancer(action.value);
          break;
        case TOURNER_:
          tourner(action.value);
          break;
        case HERKULEX_:
          herkulex.setPosition(action.value,50,HerkulexLed::Green);
          break;
        }
      }else if (state == IDLE && actions.empty())
      {
        etat = 0;
      }else if (state == STOP){
        controleMoteurDroit(2);
        controleMoteurGauche(2);
      }
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
  servo_serial.begin(115200);
  delay(500);
  herkulex.setTorqueOn();

  // VL53L0X_Error status1 = VL53L0X_ERROR_NONE;

  lcd.begin(16, 2);
  lcd.setRGB(0, 0, 255);

  // NE PAS OUBLIER DE METTRE INPUT_PULLUP
  pinMode(TOR1, INPUT_PULLUP);
  pinMode(TOR2, INPUT_PULLUP);
  pinMode(mesureVbat, INPUT);

  initMoteurDroit();
  initMoteurGauche();

  herkulex.setPosition(ferme,100,HerkulexLed::Cyan);
  delay(500);

  capteur1.begin(I2C_DEFAULT_ADDR,false);
  capteur1.continuousRangingInit();


  if(init_capteurs == true){
 
  capteur1.begin(I2C_DEFAULT_ADDR, false);
  delay(500);
  capteur1.changeAddress(0x50);
  capteur1.continuousRangingInit();
  Serial.print("changement d'adresse effectué");
  lcd.print("chg 1 ok");
  detectionCapteur1 = true;
  lcd.clear();
  lcd.print("brancher cpt2");
  delay(5000);
  capteur2.begin(I2C_DEFAULT_ADDR, false);
  capteur2.continuousRangingInit();
  detectionCapteur2 = true;
  if (detectionCapteur2 == true) {
    lcd.setRGB(0, 255, 0);
    lcd.clear();
  }
  delay(500);

  }

  // Initialisation des encodeurs
  encodeur.init(x, y, theta, rayon, entraxe, reduction, resolution);

  xMutex = xSemaphoreCreateMutex();                        // Create a mutex
  xTaskCreate(controle, "Controle", 4960, NULL, 20, NULL); // Create a task
  xTaskCreate(odo, "Odo", 4960, NULL, 22, NULL);  
  //xTaskCreate(Therkulex,"Therkulex",4960,NULL,10,NULL);
  xTaskCreate(readSensors,"readSensors",4960,NULL,15,NULL); 
  delay(500);
  Serial.println("tache controle ok");




  aller_a(200,200,PI/2.3); //1730 775
  ajouterActionHerkulex(ouvert);
  ajouterActionAvancer(50);
  ajouterActionHerkulex(serre);

  //ajouterActionAvancer(2000);


  // ajouterActionAvancer(630);
  // ajouterActionTourner(PI/2.4);
  // ajouterActionAvancer(995);
  // ajouterActionHerkulex(ouvert);
  // ajouterActionAvancer(200);
  // ajouterActionHerkulex(serre);
  

  // ajouterActionAvancer(300);
  // ajouterActionHerkulex(ouvert);
  // ajouterActionTourner(PI);
  // ajouterActionAvancer(300);
  // ajouterActionTourner(PI);
  // ajouterActionHerkulex(ferme);
}



void Therkulex(void *parameters){
  TickType_t xLastWakeTime;
  xLastWakeTime = xTaskGetTickCount();
  while(1){
    if(mouvement==1){
      herkulex.setPosition(ouvert,100,HerkulexLed::Green);
    }else if(mouvement == 2){
  herkulex.setPosition(ferme,100,HerkulexLed::Blue);
    }
  }

}

void ajouterActionAvancer(float distance)
{
  Action action;
  action.type = AVANCER_;
  action.value = distance;
  actions.push(action);
}


void ajouterActionHerkulex(int position)
{
  Action action;
  action.type = HERKULEX_;
  action.value = position;
  actions.push(action);
}


void recalage(){
  ajouterActionAvancer(-1000);
  if(etat_TOR1 == HIGH) {
    state = STOP;
  }
}



void ajouterActionTourner(float angle)
{
  Action action;
  action.type = TOURNER_;
  action.value = angle;
  actions.push(action);
}

void avancer_non_bloquant()
{
  if (state != AVANCER)
  {
    return;
  }



  if (countG >= pas_gauche && countD >= pas_droit)
  {
    controleMoteurGauche(2);
    controleMoteurDroit(2);
    delay(500); // pour le bon positionnement
    state = IDLE;
    return;
  }

  float vitesseG = vitesse; //20
  float vitesseD = vitesse; //20

  controleMoteurGauche(vitesseG / 100.0 * 255.0);
  controleMoteurDroit(vitesseD / 100.0 * 255.0);
}

void avancer(float distance)
{
  state = AVANCER;
  distance_to_travel = distance;
  nbr_pas_a_parcourir = distance / (2 * PI * rayon) * encodeur.get_resolution() * encodeur.get_reduction();
  pas_gauche = countG + nbr_pas_a_parcourir;
  pas_droit = countD + nbr_pas_a_parcourir;
}

void tourner_non_bloquant()
{
  if (state != TOURNER)
  {
    return;
  }

  if (sens == 1 ? (countG >= pas_gauche && countD <= pas_droit) : (countG <= pas_gauche && countD >= pas_droit))
  {
    state = IDLE;
    controleMoteurGauche(2);
    controleMoteurDroit(2);
    delay(500); //pour le bon positionnement
    return;
  }

  float vitesseG = vitesse * sens;
  float vitesseD = vitesse * -sens;

  controleMoteurGauche(vitesseG / 100.0 * 255.0);
  controleMoteurDroit(vitesseD / 100.0 * 255.0);
}

void tourner(float angle)
{
  state = TOURNER;
  angle_to_turn = angle;
  float nbr_pas_a_parcourir = abs((angle * entraxe) / (2 * 2 * PI * rayon) * encodeur.get_resolution() * encodeur.get_reduction());

  if (angle >= 0)
  {
    pas_gauche = countG + int(nbr_pas_a_parcourir);
    pas_droit = countD - int(nbr_pas_a_parcourir);
    sens = 1;
  }
  else
  {
    pas_gauche = countG - int(nbr_pas_a_parcourir);
    pas_droit = countD + int(nbr_pas_a_parcourir);
    sens = -1;
  }
}

float asservissement_pas_Gauche(float consigne)
{
  // Commande entre -1 et 1
  float erreur = consigne - countG;

  float terme_proportionnel = Kp * erreur;
  float terme_integral = Ki * somme_erreur_G;
  float terme_derive = Kd * (erreur - erreur_precedente_G) * 1000 / Ta;

  somme_erreur_G += terme_integral;
  // Saturation de la somme
  somme_erreur_G = constrain(somme_erreur_G, -0.1, 0.1);

  float commande = terme_proportionnel + terme_integral + terme_derive;
  erreur_precedente_G = erreur;
  commande = constrain(commande, -0.8, 0.8);
  // Serial.print("EG ");
  // Serial.println(erreur);
  // Serial.print("CG ");
  // Serial.println(commande);

  return commande;
}





float asservissement_pas_Droit(float consigne)
{
  // Commande entre -1 et 1
  float erreur = consigne - countD;

  float terme_proportionnel = Kp * erreur;
  float terme_integral = Ki * somme_erreur_D;
  float terme_derive = Kd * (erreur - erreur_precedente_D) * 1000 / Ta;

  somme_erreur_D += terme_integral;
  // Saturation de la somme
  somme_erreur_D = constrain(somme_erreur_D, -0.1, 0.1);

  float commande = terme_proportionnel + terme_integral + terme_derive;
  erreur_precedente_D = erreur;
  commande = constrain(commande, -0.8, 0.8);
  return commande;
}

void aller_a(float X, float Y,float angle_arrivee)
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
  ajouterActionTourner(angle);
  ajouterActionAvancer(distance);
  ajouterActionTourner(angle_arrivee-angle);
}




void readSensors(void *parameters)
{
  int i=0;
  while (1)
  {
    xSemaphoreTake(xMutex, portMAX_DELAY); // Take the mutex before accessing I2C

    VL53L0X_RangingMeasurementData_t rangingMeasurementData1;
    // VL53L0X_RangingMeasurementData_t rangingMeasurementData2;
    capteur1.performContinuousRangingMeasurement(&rangingMeasurementData1);
    // capteur2.performContinuousRangingMeasurement(&rangingMeasurementData2);
    mesure_capteur1 = rangingMeasurementData1.RangeMilliMeter;
    // mesure_capteur2 = rangingMeasurementData2.RangeMilliMeter;

  lcd.clear();
  lcd.print(mesure_capteur1);

  // Serial.print("mesure capteurs: ");
  // Serial.print(mesure_capteur1);
  // Serial.print(" ");
  // Serial.println(mesure_capteur2);


  xSemaphoreGive(xMutex); // Give the mutex back after accessing I2C

  // if(mesure_capteur1 > 2000){
  //   state = STOP;
  //   etat=0;
  // }else if(mesure_capteur2 <= 50){
  //   state=STOP;
  //   etat=0;
  // }else{
  //   state = IDLE;
  //   etat=1;
  // }

  // Serial.println(mesure_capteur1);
  // if(mesure_capteur1 <=300){
  //   //herkulex.setPosition(ouvert);
  //   state=STOP;
  // }
  //else {
    //herkulex.setPosition(ferme);
  //}

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

    vTaskDelay(pdMS_TO_TICKS(300)); // Delay for 100ms
  }
}

void loop()
{
  taskYIELD();
}
