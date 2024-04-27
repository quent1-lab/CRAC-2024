#include "mbed.h"
#include "herkulex.h"
#include "CAN.h"

#define SEC 1000
#define PAUSE 100
#define IDCARD 3

// ! Constantes pour les servos des pinces droites avant & arrière
#define RGRABBERMAX 0x03AD    // 941
#define RGRABBERMIN 0x01CD    // 461
#define RGRABBERCENTER 0x0290 // 656

// ! Constantes pour les servos des pinces gauches avant & arrière
#define LGRABBERMAX 0x0051    // 81
#define LGRABBERMIN 0x0227    // 551
#define LGRABBERCENTER 0x015F // 351

// ! Constantes pour la levée et la descente des peignes
#define COMBUP 0x02E5   // 741
#define COMBDOWN 0x01FC // 512

// ! Constantes pour les servos des peignes avant & arrière
#define FRONTCOMB 0x05
#define BACKCOMB 0x06

// ! Constantes pour le CAN
#define FRONTCLOSE 0x01
#define BCLOSE 0x02
#define FRONTOPEN 0x03
#define BOPEN 0x04
#define FRONTPLANT 0x05
#define BPLANT 0x06
#define FRONTCOMBUP 0x07
#define FRONTCOMBDOWN 0x08
#define BCOMBUP 0x09
#define BCOMBDOWN 0x0A
#define FRONTSHAKING 0x0B
#define BSHAKING 0x0C
#define ELEVATORUP 0x0D
#define ELEVATORDOWN 0x0E

// ! Constantes pour le moteur pas-à-pas
#define CLOCKWISE 1
#define COUNTERCLOCKWISE 0

#ifdef CARTEDEF
DigitalOut STBY(D7);
DigitalOut STEP(D6);
DigitalOut DIr(D3);
DigitalOut EN(A2);
DigitalOut M0(D5);
DigitalOut M1(D9);
DigitalOut M2(D8);
DigitalOut led(LED1);
#else
DigitalOut STBY(D7);
DigitalOut STEP(D6);
DigitalOut DIr(D3);
DigitalOut EN(A2);
DigitalOut M0(D5);
DigitalOut M1(D9);
DigitalOut M2(D8);
DigitalOut led(LED1);
#endif

Herkulex servo(PB_6, PB_7, 115200);

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

//* Fonction pour baisser le peigne avant à mi-hauteur
void frontCombMid();

//* Fonction pour lever le peigne arrière
void backCombUp();

//* Fonction pour baisser le peigne arrière
void backCombDown();

//* Fonction pour baisser le peigne arrière à mi-hauteur
void backCombMid();

//* Fonction pour secouer le peigne avant
void frontCombShaking();

//* Fonction pour secouer le peigne arrière
void backCombShaking();

//* Fonction pour monter l'ascenseur
void elevatorUp();

//* Fonction pour descendre l'ascenseur
void elevatorDown();

//* Fonction pour descendre l'ascenseur à mi-hauteur
void elevatorMid();

//* Fonction pour activer le couple du moteur pas-à-pas de l'ascenseur
void blockStepper();

//* Fonction pour initialiser le moteur pas-à-pas
void initStepper();

//* Fonction pour initialiser les servos
void initServo();

//* Fonction pour la mise en route du moteur pas-à-pas
int stepper(int nsteps, bool m0, bool m1, bool m2, bool direction, float time);

int main()
{
  initServo();
  initStepper();
  while (1)
  {
    if (can.read(RXMsg) && (RXMsg.id == IDCARD))
    {
      switch (RXMsg.data[0])
      {
      case FRONTCLOSE:
        closingFrontGrabber();
        break;

      case BCLOSE:
        closingBackGrabber();
        break;

      case FRONTOPEN:
        openingFrontGrabber();
        break;

      case BOPEN:
        openingBackGrabber();
        break;

      case FRONTPLANT:
        plantClosingFrontGrabber();
        break;

      case BPLANT:
        plantClosingBackGrabber();
        break;

      case FRONTCOMBUP:
        frontCombUp();
        break;

      case FRONTCOMBDOWN:
        frontCombDown();
        break;

      case BCOMBUP:
        backCombUp();
        break;

      case BCOMBDOWN:
        backCombDown();
        break;

      case FRONTSHAKING:
        frontCombShaking();
        break;

      case BSHAKING:
        backCombShaking();
        break;

      case ELEVATORUP:
        elevatorUp();
        break;

      case ELEVATORDOWN:
        elevatorDown();
        break;

      default:
        break;
      }
      delay(PAUSE);
    }
    // else
    // {
    //   blockStepper();
    // }
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

int stepper(int swpulse, int m0, int m1, int m2, int dir, int dur)
{
  M0 = m0;
  M1 = m1;
  M2 = m2;
  DIr = dir;
  EN = 1;
  // step generator
  for (int i = 0; i < swpulse; i++)
  {
    STEP = 1;
    ThisThread::sleep_for(1ms);
    STEP = 0;
    ThisThread::sleep_for(1ms);
  }
  EN = 0;
  return 0;
}

void initServo(void)
{
  servo.clear(BROADCAST_ID);
  servo.setTorque(BROADCAST_ID, TORQUE_ON);
}

void openingFrontGrabber()
{
  servo.clear(BROADCAST_ID);
  servo.positionControl(0x01, RGRABBERMAX, 35, GLED_ON);
  servo.positionControl(0x02, LGRABBERMAX, 20, GLED_ON);
  servo.clear(BROADCAST_ID);
}

void openingBackGrabber()
{
  servo.clear(BROADCAST_ID);
  servo.positionControl(0x04, RGRABBERMAX, 35, GLED_ON);
  servo.positionControl(0x03, LGRABBERMAX, 20, GLED_ON);
  servo.clear(BROADCAST_ID);
}

void closingBackGrabber()
{
  servo.clear(BROADCAST_ID);
  servo.positionControl(0x04, RGRABBERMIN, 35, GLED_ON);
  servo.positionControl(0x03, LGRABBERMIN, 20, GLED_ON);
  servo.clear(BROADCAST_ID);
}

void closingFrontGrabber()
{
  servo.clear(BROADCAST_ID);
  servo.positionControl(0x01, RGRABBERMIN, 35, GLED_ON);
  servo.positionControl(0x02, LGRABBERMIN, 20, GLED_ON);
  servo.clear(BROADCAST_ID);
}

void plantClosingFrontGrabber()
{
  servo.clear(BROADCAST_ID);
  servo.positionControl(0x01, RGRABBERCENTER, 45, GLED_ON);
  servo.positionControl(0x02, LGRABBERCENTER, 35, GLED_ON);
  servo.clear(BROADCAST_ID);
}

void plantClosingBackGrabber()
{
  servo.clear(BROADCAST_ID);
  servo.positionControl(0x04, RGRABBERCENTER, 45, GLED_ON);
  servo.positionControl(0x03, LGRABBERCENTER, 35, GLED_ON);
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
  servo.positionControl(BACKCOMB, COMBDOWN, 60, GLED_ON);
  servo.clear(BACKCOMB);
}

void frontCombShaking()
{
  int count = 50;
  for (int i = 0; i < count; i++)
  {
    servo.positionControl(FRONTCOMB, COMBDOWN - 5, 1, GLED_ON);
    servo.positionControl(FRONTCOMB, COMBDOWN + 5, 1, GLED_ON);
  }
}

void backCombShaking()
{
  int count = 50;
  for (int i = 0; i < count; i++)
  {
    servo.positionControl(BACKCOMB, COMBDOWN - 5, 1, GLED_ON);
    servo.positionControl(BACKCOMB, COMBDOWN + 5, 1, GLED_ON);
  }
}

void elevatorDown(void)
{
  stepper(660, 0, 0, 0, 0, 1);
}

void elevatorUp(void)
{
  stepper(660, 0, 0, 0, 1, 1);
}

void blockStepper(void)
{
  STBY = 1;
  EN = 1;
  M0 = 1;
  M1 = 1;
  M2 = 1;
}
void initStepper(void)
{
  STBY = 1;
  EN = 0;
  M0 = 0;
  M1 = 0;
  M2 = 0;
}

void delay(int ms)
{
  wait_us((int)(ms * 1000.0));
}
