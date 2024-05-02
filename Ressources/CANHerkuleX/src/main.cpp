#include "mbed.h"
#include "herkulex.h"
#include "CAN.h"

#define SEC 1000
#define PAUSE 100
#define IDCARD 0x1A0

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
#define COMB 0x05

// ! Constantes pour le CAN
#define CLOSE 0x01
#define OPEN 0x03
#define PLANT 0x05
#define COMBUP 0x07
#define COMBDOWN 0x08
#define SHAKING 0x0B
#define ELEVATORUP 0x0D
#define ELEVATORDOWN 0x0E
#define ELEVATORMID 0x0F
#define ELEVATORHOMING 0x10

// ! Constantes pour le moteur pas-à-pas
#define CLOCKWISE 1
#define COUNTERCLOCKWISE 0

// ! Constantes CAN pour les aknowledge
#define ACK_RGRABBER 0x300 // Aknowledge pour la pince droite
#define ACK_LGRABBER 0x301 // Aknowledge pour la pince gauche
#define ACK_COMB 0x302 // Aknowledge pour le peigne
#define ACK_ELEVATOR 0x303 // Aknowledge pour l'ascenseur


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

// Fin de course
DigitalIn endstop(PA_1);

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

//* Fonction pour fermer les pinces avant
void closingFrontGrabber();

//* Fonction pour fermer les pinces avant en position plant
void plantClosingFrontGrabber();

//* Fonction pour lever le peigne avant
void frontCombUp();

//* Fonction pour baisser le peigne avant
void frontCombDown();

//* Fonction pour baisser le peigne avant à mi-hauteur
void frontCombMid();

//* Fonction pour secouer le peigne avant
void frontCombShaking();

//* Fonction pour monter l'ascenseur
void elevatorUp();

//* Fonction pour descendre l'ascenseur
void elevatorDown();

//* Fonction pour descendre l'ascenseur à mi-hauteur
void elevatorMid();

//* Fonction pour homing l'ascenseur
void elevatorHoming();

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
      case CLOSE:
        closingFrontGrabber();
        break;

      case OPEN:
        openingFrontGrabber();
        break;

      case PLANT:
        plantClosingFrontGrabber();
        break;

      case COMBUP:
        frontCombUp();
        break;

      case COMBDOWN:
        frontCombDown();
        break;

      case SHAKING:
        frontCombShaking();
        break;

      case ELEVATORUP:
        elevatorUp();
        break;

      case ELEVATORDOWN:
        elevatorDown();
        break;

      case ELEVATORHOMING:
        elevatorHoming();
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

void frontCombUp()
{
  servo.clear(COMB);
  servo.positionControl(COMB, COMBUP, 45, GLED_ON);
  servo.clear(COMB);
}

void frontCombDown()
{
  servo.clear(COMB);
  servo.positionControl(COMB, COMBDOWN, 45, GLED_ON);
  servo.clear(COMB);
}

void frontCombShaking()
{
  int count = 50;
  for (int i = 0; i < count; i++)
  {
    servo.positionControl(COMB, COMBDOWN - 5, 1, GLED_ON);
    servo.positionControl(COMB, COMBDOWN + 5, 1, GLED_ON);
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

void elevatorHoming(void)
{
  // Monte l'ascenseur jusqu'à ce qu'il atteigne le fin de course
  while (endstop.read() == 0)
  {
    stepper(20, 0, 0, 0, 1, 1);
  }
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
