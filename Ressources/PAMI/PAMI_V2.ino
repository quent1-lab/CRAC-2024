#include "Vl53l0x.h"
#include "FreeRTOS.h"
#include "task.h"
#include "semphr.h"
#include "Codeurs.h"
#include "rgb_lcd.h"

Vl53l0x capteur1;
Vl53l0x capteur2;

Codeurs codeurs;
rgb_lcd lcd;


bool detectionCapteur1 = false;
bool detectionCapteur2 = false;

TaskHandle_t Handle_aTask;
TaskHandle_t Handle_bTask;
SemaphoreHandle_t xMutex;

#define BACKWARD 0x1
#define FORWARD 0x0

int _address = 0x10;
int32_t _gauche, _droit;
int16_t _g16, _d16;
static const int16_t MAX = 16384;
int32_t codeurGauche, codeurDroit;
int pinDirectionDroit = PA15;
int pinPWMDroit = PA13;
int pinDirectionGauche = PA14;
int pinPWMGauche = PA12;
const int mesureVbat = PB3;
const int TOR1 = 2;
const int TOR2 = 3;

int etat = 0;
int dplt = 0;


int mesure_capteur1;
int mesure_capteur2;

int TOR1_precedent = LOW;  // laisser en LOW

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
float angle_arrive = 0;  // Permet d'enregistrer l'angle d'arrivé

float erreur_moyenne;
float erreur_anglegauche;
float erreur_angleDroit;

float m_newX;
float m_newY;
float angle;

bool is_asserv_X_Y_Theta = false;  // Variable permettant de savoir si on est en mode asservissement XYT ou non

bool rotActiver = false;
////////////////////////////////////// Moteur Droit/////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////// Initialisation du moteur Droit/////////////////////////////////////////////////////////////////////////////////////////////////////
void initMoteurDroit() {
  pinMode(pinPWMDroit, OUTPUT);
  pinMode(pinDirectionDroit, OUTPUT);
}
//////////////////////// Permet de pouvoir déterminer dans un premier comment fonctionne les  moteurs//////////////////////////////////////////////////////
void controleMoteurDroit(int PWM) {
  if (PWM > 0) {
    digitalWrite(pinDirectionDroit, 0);
  }
  if (PWM < 0) {
    digitalWrite(pinDirectionDroit, 1);
  }
  PWM = abs(PWM);
  // analogWrite(pinPWMGauche, PWM);
  analogWrite(pinPWMDroit, PWM);
}
////////////////////////////////////// Moteur GAUCHE/////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////// Initialisation du moteur GAUCHE/////////////////////////////////////////////////////////////////////////////////////////////////////
void initMoteurGauche() {
  pinMode(pinPWMGauche, OUTPUT);
  pinMode(pinDirectionGauche, OUTPUT);
}
//////////////////////// Permet de pouvoir déterminer dans un premier comment fonctionne les  moteurs//////////////////////////////////////////////////////
void controleMoteurGauche(int PWM) {
  if (PWM < 0) {
    digitalWrite(pinDirectionGauche, 1);
  } else {
    digitalWrite(pinDirectionGauche, 0);
  }
  PWM = abs(PWM);
  analogWrite(pinPWMGauche, PWM);
  // analogWrite(pinPWMDroit, PWM);
}

void X_Y_Theta(float x, float y, float theta) {
  m_newX = x;
  m_newY = y;
  angle_arrive = theta;
  m_distance = sqrt(pow(m_newX - distance_prec_X, 2) + pow(m_newY - distance_prec_Y, 2));

  angle = atan2(m_newY - distance_prec_Y, m_newX - distance_prec_X);

  cons_rotation = degrees(angle);
  cons_asserv = m_distance;
  // etat = 2;
}



void asservissement() {

  // Asservissement en distance pour un ligne droite

  switch (etat_Ligne_Droite) {
    case -1:

      break;
    case 0:
      delay(50);
      codeurs.reset();
      //delay(1000);
      etat_Ligne_Droite = 1;
      break;
    case 1:
      codeurs.read(codeurGauche, codeurDroit);
      distance = (codeurGauche + codeurDroit) / 2.0;
      distance = distance * rayonRoue * 2.0 / 2048.0;
      erreur = (cons_asserv) - distance;  // + // Calcul de l'erreur par rapport a la consigne + une consigne d'équilibre due fait que le centre de gravité du robot n'est pas placé correctement
      commande = erreur * 0.25;           // Calcul de la commande permettant de savoir si on doit faire tourner le moteur plus ou moins fort
      // Serial.print("distance ");
      // Serial.print(distance);
      // Serial.print(" erreur ");
      // Serial.print(erreur);
      // Serial.print(" codeurGauche  ");
      // Serial.print(codeurGauche);
      // Serial.print("  codeurDroit ");
      // Serial.println(codeurDroit);


      if (commande < 0)  // si la commande est négatif, cela signifie qu'on doit faire tourner les moteurs dans un sens spécifiquement
      {
        commandeTraiter = commande - commandeComp;  // Etant donner que les moteur ont physiquement, un jeu et un couple de frottement sec qui doit être éliminer via un offset de la commande
        // PWMD = 10;
        // PWMG = 0;
      }
      if (commande > 0) {
        commandeTraiter = commande + commandeComp;
        // PWMG = 10;
        // PWMD = 0;
      }
      if (commandeTraiter > 1)  // Si la commande dépasse la saturation, on plafonne celle ci a une valeur fixe, due fait que le hacheur 4 quadrant a part son architecture des condensateurs de boostrap, qui doivent etre charger un peu, permettant le bon fonctionnement des transistor
      {
        commandeTraiter = 1;
        PWMD = 20;
        PWMG = 0;
      } else if (commandeTraiter < -1) {
        commandeTraiter = -1;
        PWMG = 20;
        PWMD = 0;
      }
      // Serial.println(erreur);
      // Serial.printf("avance\n");
      vitesse = 0.5 + commandeTraiter;  // Utilisant une commande unipolaire, 0.5 correspond au fait que les deux ponts du hacheur 4 quadrant donne la meme tension, ce qui fait qu'au bornes du moteur on a une tension = 0
      PWM = vitesse * Kalpha;           // On effectue une mise a l'échelle, J'ai décider de travailler sur 12bits
      // controleMoteurGauche(PWM -PWMG);
      // controleMoteurDroit(PWM - PWMD);
      controleMoteurGauche(PWM);
      controleMoteurDroit(PWM);


      if ((erreur >= -2) && (erreur < 5)) { //>=-2
        etat_Ligne_Droite = 2;
      }
      // Serial.println(erreur);
      break;
    case 2:
      Serial.print("Etat ligne droit ");
      Serial.println(etat_Ligne_Droite);
      Serial.print(" on a fini");
      controleMoteurDroit(0);
      controleMoteurGauche(0);
      etat_Ligne_Droite = -1; //-1
      etat = 0; //0
      break;
    default:
      break;
  }
}



void rotation() {

  // Asservissement en rotation
  switch (etat_Rotation) {
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
      if (cons_rotation > 0) {
        cons_rotation = cons_rotation + 20.0;
        angle_cons_droit = cons_rotation / 2.0;
        angle_cons_gauche = -1 * angle_cons_droit;
      }
      if (cons_rotation < 0) {
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
      if (cons_rotation >= 0) {
        if (erreur_moyenne < 0) {
          controleMoteurDroit(-vit_ang - (commandeComp * 255.0));
          controleMoteurGauche(vit_ang + (commandeComp * 255.0));
        }
        if (erreur_moyenne > 0) {
          controleMoteurDroit(0);
          controleMoteurGauche(0);
          etat_Rotation = 2;
        }
      } else {
        if (erreur_moyenne > 0) {
          controleMoteurDroit(20 + (commandeComp * 255.0));
          controleMoteurGauche(-20 - (commandeComp * 255.0));
        }
        if (erreur_moyenne < 0) {
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

void controle(void *parameters) {
  TickType_t xLastWakeTime;
  xLastWakeTime = xTaskGetTickCount();


  while (1) {
    xSemaphoreTake(xMutex, portMAX_DELAY);
    //taskYIELD();

    int etat_TOR1 = digitalRead(TOR1);
    int etat_TOR2 = digitalRead(TOR2);
    float vbat = analogRead(mesureVbat);
    float tensionBat = (vbat / 895) * 3.3;
    tensionBat = tensionBat * (7.2 / 3.3);
    // lcd.setCursor(7, 0);
    // lcd.print("vbat: ");
    // lcd.setCursor(12, 0);
    // lcd.print(tensionBat);
    // Serial.println(tensionBat);
    switch (etat) {
      case 0:
      if(etat_TOR1 == HIGH){
        etat = 1;
      }
        break;
      case 1:
        //X_Y_Theta(1500, 2000, 0);
        X_Y_Theta(2000,0,0);
        Serial.println("Calcul effectuer");
        etat = 2;
        etat_Rotation = 0;
        break;
      case 2:
        // Serial.println("etat 2");
        rotation();
        break;
      case 3:
        Serial.println("pret ligne droit");
        etat = 4;
        etat_Ligne_Droite = 0;
        break;
      case 4:
        asservissement();
        lcd.clear();
        lcd.setRGB(255,0,255);
        lcd.print("case 4");
        break;
      default:
        break;  //break
    }
    TOR1_precedent = etat_TOR1;
    // Serial.println("Controle");
    xSemaphoreGive(xMutex);

    vTaskDelayUntil(&xLastWakeTime, pdMS_TO_TICKS(Te));
  }

  // if (PWM > 0) {
  //   digitalWrite(pinDirectionGauche, 0);
  // }
  // if (PWM < 0) {
  //   digitalWrite(pinDirectionGauche, 1);
  // }
  // PWM = abs(PWM);
  // analogWrite(pinPWMGauche, PWM);
}



void jsp(void *parameters) {
  TickType_t xLastWakeTime;
  xLastWakeTime = xTaskGetTickCount();
  int i = 0;

  while (1) {
    xSemaphoreTake(xMutex, portMAX_DELAY);

    lcd.clear();
    lcd.setRGB(255, 0, 255);
    lcd.print(i);
    i++;
    Serial.print("i ");
    Serial.println(i);
    xSemaphoreGive(xMutex);
    vTaskDelayUntil(&xLastWakeTime, pdMS_TO_TICKS(Tc));
  }
}




void setup() {
  Serial.begin(115200);

  // VL53L0X_Error status1 = VL53L0X_ERROR_NONE;

  lcd.begin(16, 2);
  lcd.setRGB(0, 0, 255);
  codeurs.reset();
  //NE PAS OUBLIER DE METTRE INPUT_PULLUP
  pinMode(TOR1, INPUT_PULLUP);
  pinMode(TOR2, INPUT_PULLUP);
  pinMode(mesureVbat, INPUT);

  initMoteurDroit();
  initMoteurGauche();

  // capteur1.begin(I2C_DEFAULT_ADDR, false);
  // delay(500);
  // capteur1.changeAddress(0x50);
  // capteur1.continuousRangingInit();
  // Serial.print("changement d'adresse effectué");
  // lcd.print("chg 1 ok");
  // detectionCapteur1 = true;
  // lcd.clear();
  // lcd.print("brancher cpt2");
  // delay(5000);
  // capteur2.begin(I2C_DEFAULT_ADDR, false);
  // capteur2.continuousRangingInit();
  // detectionCapteur2 = true;
  // if (detectionCapteur2 == true) {
  //   lcd.setRGB(0, 255, 0);
  //   codeurs.begin(false);
  // }
  // delay(500);


  Serial.println("Fini");
  xMutex = xSemaphoreCreateMutex();  // Create a mutex
  xTaskCreate(controle, "Controle", 1000, NULL, 20, NULL);  // Create a task
  Serial.println("tache controle ok");
  //xTaskCreate(jsp, "jsp", 4096, NULL, 25, NULL);  // Create a task
  //xTaskCreate(readSensors,"readsensors",4096,NULL,20,NULL);
  //Serial.println("tache readsensors ok");
  //xTaskCreate(deplacement,"deplacement",4096,NULL,20,NULL);
  //Serial.println("tache deplacement ok");
  //delay(500);
  //Serial.print("Etat = ");
  //Serial.println(etat = 1);
  delay(500);
  Serial.println("Go");
}



void deplacement(void *pvParameters) {
  TickType_t xLastWakeTime;
  xLastWakeTime = xTaskGetTickCount();
  int i = 0;

  while (1) {
    //xSemaphoreTake(xMutex, portMAX_DELAY);

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


    //FONCTIONNEL

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


    if (mesure_capteur1 >= 2000) {
      Serial.println("capteur1 out of range");
    } else if (mesure_capteur2 >= 2000) {
      Serial.println("capteur 2 out of range");
    } else {
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

void readSensors(void *pvParameters) {
  while (1) {
    xSemaphoreTake(xMutex, portMAX_DELAY);  // Take the mutex before accessing I2C

    VL53L0X_RangingMeasurementData_t rangingMeasurementData1;
    VL53L0X_RangingMeasurementData_t rangingMeasurementData2;
    capteur1.performContinuousRangingMeasurement(&rangingMeasurementData1);
    capteur2.performContinuousRangingMeasurement(&rangingMeasurementData2);
    //codeurs.read(codeurGauche, codeurDroit);
    mesure_capteur1 = rangingMeasurementData1.RangeMilliMeter;
    mesure_capteur2 = rangingMeasurementData2.RangeMilliMeter;
    xSemaphoreGive(xMutex);  // Give the mutex back after accessing I2C

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




    vTaskDelay(pdMS_TO_TICKS(10));  // Delay for 100ms
  }
}

void loop() {
  taskYIELD();
}

// PROGRAMME POUR CHANGER L ADRESSE DU CAPTEUR AVEC RTOS

// #include "Vl53l0x.h"
// #include "FreeRTOS.h"
// #include "task.h"
// #include "rgb_lcd.h"

// Vl53l0x capteur1;
// Vl53l0x capteur2;

// rgb_lcd lcd;

// void setup() {
//   // put your setup code here, to run once:
//   Serial.begin(115200);

//   VL53L0X_Error status1 = VL53L0X_ERROR_NONE;

//   lcd.begin(16,2);
//   status1 = capteur1.begin(I2C_DEFAULT_ADDR, false);
//   lcd.setRGB(0,0,255);
//   lcd.print("brancher capteur");

//   // if (VL53L0X_ERROR_NONE != status1) {
//   //   Serial.println("start vl53l0x mesurement failed!");
//   //   capteur1.printPalError(status1);
//   //   while (1);
//   // }
//   capteur1.continuousRangingInit();
//   // if (VL53L0X_ERROR_NONE != status1) {
//   //   Serial.println("start vl53l0x mesurement failed!");
//   //   capteur1.printPalError(status1);
//   //   while (1);
//   // }

//   xTaskCreate(readSensor1, "ReadSensor1", 1000, NULL, 25, NULL); // Create a task
//   xTaskCreate(changeAddr, "changeAddr",1000,NULL,30,NULL);
// }

// void changeAddr(void *pvParameters){
//   VL53L0X_Error status1 = VL53L0X_ERROR_NONE;

//   status1 = capteur1.changeAddress(0x50);// Change the I2C address of the second sensor

//   if (VL53L0X_ERROR_NONE != status1) {
//     Serial.println("Impossible de changer l'adresse du capteur !");
//     lcd.clear();
//     lcd.print("imposible");
//   }else {
//     Serial.println("Addresse changée avec succès !");
//     lcd.clear();
//     lcd.setCursor(0,0);
//     lcd.print("Adresse changee");
//     capteur2.begin(I2C_DEFAULT_ADDR,false);
//     capteur2.continuousRangingInit();
//   }

//   vTaskDelete(NULL); //pour supprimer la tâche
// }

// void readSensor1(void *pvParameters) {
//   while (1) {

//     VL53L0X_RangingMeasurementData_t rangingMeasurementData1;
//     capteur1.performContinuousRangingMeasurement(&rangingMeasurementData1);

//     VL53L0X_RangingMeasurementData_t rangingMeasurementData2;
//     capteur2.performContinuousRangingMeasurement(&rangingMeasurementData2);

//     if (rangingMeasurementData1.RangeMilliMeter >= 2000) {
//       Serial.println("out of ranger");
//       lcd.clear();
//       lcd.setCursor(0,1);
//       lcd.print("out of range");
//     } else {
//     //   Serial.print("distance capteur 1: ");
//     //   Serial.println(rangingMeasurementData1.RangeMilliMeter);
//       lcd.clear();
//       lcd.setCursor(0,0);
//       lcd.print("dist capt: ");
//       lcd.print(rangingMeasurementData1.RangeMilliMeter);
//     }
//     vTaskDelay(pdMS_TO_TICKS(100));
//   }
// }

// void loop() {
//   taskYIELD();

// }

// PROGRAMME POUR VERIFIER LE CHANGEMENT D ADRESSE DU CAPTEUR

// #include "Vl53l0x.h"

// Vl53l0x monCapteur;

// void setup() {
//   // put your setup code here, to run once:
//   Serial.begin(115200);
//   VL53L0X_Error status = VL53L0X_ERROR_NONE;
//   //status = monCapteur.begin(I2C_DEFAULT_ADDR, true);
//   status = monCapteur.begin(0x50, true);
//   if (VL53L0X_ERROR_NONE != status) {
//     Serial.println("start vl53l0x mesurement failed!");
//     monCapteur.printPalError(status);
//     while (1);
//   }
//   monCapteur.continuousRangingInit();
//   if (VL53L0X_ERROR_NONE != status) {
//     Serial.println("start vl53l0x mesurement failed!");
//     monCapteur.printPalError(status);
//     while (1);
//   }
// }

// int count = 0;

// void loop() {
//   // put your main code here, to run repeatedly:
//   VL53L0X_RangingMeasurementData_t rangingMeasurementData;
//   monCapteur.performContinuousRangingMeasurement(&rangingMeasurementData);
//   if (rangingMeasurementData.RangeMilliMeter >= 2000) {
//     Serial.println("out of ranger");
//   } else {
//     Serial.print("distance::");
//     Serial.println(rangingMeasurementData.RangeMilliMeter);
//   }
//   delay(100);
//   count++;
//   VL53L0X_Error status = VL53L0X_ERROR_NONE;
//   if (count == 100) {
//     //status = monCapteur.changeAddress(0x50);
//     Serial.println("");
//     if (VL53L0X_ERROR_NONE != status) {
//       Serial.println("change address 0x50 failed!");
//       monCapteur.printPalError(status);
//       while (1);
//     }
//     //Serial.println("Change address : 0x50");
//     //Serial.println("");
//   }
// }
