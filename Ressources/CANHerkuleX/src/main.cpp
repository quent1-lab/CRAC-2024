#include "mbed.h"
#include "herkulex.h"
#include "CAN.h"

#define SEC 1000
#define PAUSE 100
#define IDCARD 3

// ! Constantes pour les servos des pinces droites avant & arrière
#define RGRABBERMAX 0x03AD    // 941
#define RGRABBERMIN 0x0053    // 83
#define RGRABBERCENTER 0x0290 // 656

// ! Constantes pour les servos des pinces gauches avant & arrière
#define LGRABBERMAX 0x003D    // 61
#define LGRABBERMIN 0x0227    // 551
#define LGRABBERCENTER 0x015F // 351

// ! Constantes pour la levée et la descente des peignes
#define COMBUP 0x02DD   // 741
#define COMBDOWN 0x0209 // 521

// ! Constantes pour les servos des peignes avant & arrière
#define FRONTCOMB 0x06
#define BACKCOMB 0x05

// ! Constantes pour le CAN
#define FCLOSE 0x01
#define BCLOSE 0x02
#define FOPEN 0x03
#define BOPEN 0x04
#define FPLANT 0x05
#define BPLANT 0x06
#define FCOMBUP 0x07
#define FCOMBDOWN 0x08
#define BCOMBUP 0x09
#define BCOMBDOWN 0x0A

Herkulex servo(PB_6, PB_7, 115200);
DigitalOut led(LED1);
DigitalIn pin(PB_0);

CAN can(PA_11, PA_12, 1000000); // CAN Rx pin name, CAN Tx pin name
CANMessage RXMsg;

// TODO : Fonction pour faire une pause comme sur Arduino
void delay(int ms);

//* Envoie un message CAN
void CANFill(CANMessage &msg, char length, int id, char data0h, char data1h, char data2h, char data3h, char data4h, char data5h, char data6h, char data7h);

//* Affiche un message CAN reçu
void printCANMsg(CAN *can, CANMessage &msg);

//* Fonction pour ouvrir les pinces avant
void openingFrontGrabber();

//* Fonction pour ouvrir les pinces arrière
void openingBackGrabber();

//* Fonction pour fermer les pinces avant
void closingFrontGrabber();

//* Fonction pour fermer les pinces arrière
void closingBackGrabber();

//* Fonction pour fermer les pinces avant en position plant
void plantClosingFrontGrabber();

//* Fonction pour fermer les pinces arrière en position plant
void plantClosingBackGrabber();

//* Fonction pour lever le peigne avant
void frontCombUp();

//* Fonction pour baisser le peigne avant
void frontCombDown();

//* Fonction pour lever le peigne arrière
void backCombUp();

//* Fonction pour baisser le peigne arrière
void backCombDown();

int main()
{
  servo.clear(BROADCAST_ID);
  servo.setTorque(BROADCAST_ID, TORQUE_ON);
  while (1)
  {
    if (can.read(RXMsg) && (RXMsg.id == IDCARD))
    {
      switch (RXMsg.data[0])
      {
      case FCLOSE:
        closingFrontGrabber();
        break;

      case BCLOSE:
        closingBackGrabber();
        break;

      case FOPEN:
        openingFrontGrabber();
        break;

      case BOPEN:
        openingBackGrabber();
        break;

      case FPLANT:
        plantClosingFrontGrabber();
        break;

      case BPLANT:
        plantClosingBackGrabber();
        break;

      case FCOMBUP:
        frontCombUp();
        break;

      case FCOMBDOWN:
        frontCombDown();
        break;

      case BCOMBUP:
        backCombUp();
        break;

      case BCOMBDOWN:
        backCombDown();
        break;

      default:
        break;
      }
      delay(PAUSE);
    }
  }
}

void CANFill(CANMessage &msg, char length, int id, char data0h, char data1h, char data2h, char data3h, char data4h, char data5h, char data6h, char data7h)
{
  msg.len = length;
  msg.type = CANData;
  msg.format = CANStandard;
  msg.id = id;
  msg.data[0] = data0h;
  msg.data[1] = data1h;
  msg.data[2] = data2h;
  msg.data[3] = data3h;
  msg.data[4] = data4h;
  msg.data[5] = data5h;
  msg.data[6] = data6h;
  msg.data[7] = data7h;
}

void printCANMsg(CAN *can, CANMessage &msg)
{
  printf("  ID      = 0x%.3x\r\n", msg.id);
  printf("  Type    = %d\r\n", msg.type);
  printf("  format  = %d\r\n", msg.format);
  printf("  Length  = %d\r\n", msg.len);
  printf("  Data    =");
  for (int i = 0; i < msg.len; i++)
  {
    printf(" 0x%.2X", msg.data[i]);
  }
  printf("\r\n");
}

void openingFrontGrabber()
{
  servo.clear(BROADCAST_ID);
  servo.positionControl(0x01, RGRABBERMAX, 45, GLED_ON);
  servo.positionControl(0x02, LGRABBERMAX, 45, GLED_ON);
  servo.clear(BROADCAST_ID);
}

void openingBackGrabber()
{
  servo.clear(BROADCAST_ID);
  servo.positionControl(0x04, RGRABBERMAX, 45, GLED_ON);
  servo.positionControl(0x03, LGRABBERMAX, 45, GLED_ON);
  servo.clear(BROADCAST_ID);
}

void closingBackGrabber()
{
  servo.clear(BROADCAST_ID);
  servo.positionControl(0x04, RGRABBERMIN, 45, GLED_ON);
  servo.positionControl(0x03, LGRABBERMIN, 45, GLED_ON);
  servo.clear(BROADCAST_ID);
}

void closingFrontGrabber()
{
  servo.clear(BROADCAST_ID);
  servo.positionControl(0x01, RGRABBERMIN, 45, GLED_ON);
  servo.positionControl(0x02, LGRABBERMIN, 45, GLED_ON);
  servo.clear(BROADCAST_ID);
}

void plantClosingFrontGrabber()
{
  servo.clear(BROADCAST_ID);
  servo.positionControl(0x01, RGRABBERCENTER, 45, GLED_ON);
  servo.positionControl(0x02, LGRABBERCENTER, 45, GLED_ON);
  servo.clear(BROADCAST_ID);
}

void plantClosingBackGrabber()
{
  servo.clear(BROADCAST_ID);
  servo.positionControl(0x04, RGRABBERCENTER, 45, GLED_ON);
  servo.positionControl(0x03, LGRABBERCENTER, 45, GLED_ON);
  servo.clear(BROADCAST_ID);
}

void frontCombUp()
{
  servo.clear(FRONTCOMB);
  servo.positionControl(FRONTCOMB, COMBUP, 45, GLED_ON);
  servo.clear(FRONTCOMB);
}

void frontCombDown()
{
  servo.clear(FRONTCOMB);
  servo.positionControl(FRONTCOMB, COMBDOWN, 45, GLED_ON);
  servo.clear(FRONTCOMB);
}

void backCombUp()
{
  servo.clear(BACKCOMB);
  servo.positionControl(BACKCOMB, COMBUP, 45, GLED_ON);
  servo.clear(BACKCOMB);
}

void backCombDown()
{
  servo.clear(BACKCOMB);
  servo.positionControl(BACKCOMB, COMBDOWN, 45, GLED_ON);
  servo.clear(BACKCOMB);
}

void delay(int ms)
{
  wait_us((int)(ms * 1000.0));
}