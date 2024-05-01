#include <mbed.h>
#include <CAN.h>

DigitalOut led(LED1);

CAN can1(PA_11, PA_12, 1000000); // CAN Rx pin name (PA11), CAN Tx pin name (PA12), Frequency = 1000kbits

AnalogIn analogInPin0(A6); // Utilisez le port analogique (A6) sur la carte F303K8  - Cap_courant1
AnalogIn analogInPin1(A3); // Utilisez le port analogique (A3) sur la carte F303K8  - Cap_courant2
AnalogIn analogInPin2(A1); // Utilisez le port analogique (A1) sur la carte F303K8  - Cap_courant3

AnalogIn analogInPin3(A0); // Utilisez le port analogique (A0) sur la carte F303K8  - V_BatMain
AnalogIn analogInPin4(D3); // Utilisez le port analogique (D3) sur la carte F303K8  - V_Bat1
AnalogIn analogInPin5(D6); // Utilisez le port analogique (D6) sur la carte F303K8  - V_Bat2
AnalogIn analogInPin6(A2); // Utilisez le port analogique (A2) sur la carte F303K8  - V_Bat3

DigitalOut switchControl1(D4);  // Interrupteur 1 - D4
DigitalOut switchControl2(D5);  // Interrupteur 2 - D5
DigitalOut switchControl3(D11); // Interrupteur 3 - D11

DigitalIn ARU(PB_4, PullUp); // ARU - PB_4

void controlSwitch(DigitalOut &switchControl, bool on)
{
    switchControl = on;
}

float calcul_VBat_main(float x)
{
    float y;
    y = (0.0174 * pow(x, 6)) - (0.168 * pow(x, 5)) + (0.6307 * pow(x, 4)) - (1.1672 * pow(x, 3)) + (1.1073 * pow(x, 2)) + (7.6005 * x) + 0.0153;
    return y;
}

float calcul_VBat1(float x)
{
    float y;
    y = (0.0204 * pow(x, 6)) - (0.1802 * pow(x, 5)) + (0.5803 * pow(x, 4)) - (0.832 * pow(x, 3)) + (0.5209 * pow(x, 2)) + (7.9712 * x) + 0.0115;
    return y;
}

float calcul_VBat2(float x)
{
    float y;
    y = (0.0199 * pow(x, 6)) - (0.179 * pow(x, 5)) + (0.5926 * pow(x, 4)) - (0.8866 * pow(x, 3)) + (0.5933 * pow(x, 2)) + (7.951 * x) + 0.0093;
    return y;
}

float calcul_VBat3(float x)
{
    float y;
    y = (0.0199 * pow(x, 6)) - (0.1784 * pow(x, 5)) + (0.591 * pow(x, 4)) - (0.8979 * pow(x, 3)) + (0.6284 * pow(x, 2)) + (7.9408 * x) + 0.0095;
    return y;
}

bool checkVoltage(float voltage, float max)
{
    return voltage >= max;
}

bool checkARU()
{
    return ARU.read();
}

int main()
{
    printf("CRAC stm32f303k8 démo\n");

    // Création d'un message CAN
    CANMessage request;
    CANMessage response_V, response_I, response_S;
    CANMessage order;  // Ordre à exécuter
    CANMessage aruCan; // ARU
    // requetes (tension, courant, switch) / reponse (tension, courant, switch)

    // Définition de l'ID du message CAN (11 bits)
    response_V.id = 0x203;
    response_I.id = 0x204;
    response_S.id = 0x205;
    order.id = 0x206;
    aruCan.id = 0x207;

    // Définition de la longueur des données (8 octets maximum)
    response_V.len = 2;
    response_I.len = 2;
    response_S.len = 2;
    order.len = 2;
    aruCan.len = 1;

    float V_BatMain, V_Bat1, V_Bat2, V_Bat3;
    float TensionMaxBAT = 20.0;

    int compteur_ARU = 0;

    while (1)
    {
        float analogValue0 = analogInPin0.read(); // Lire la valeur analogique - Cap_courant1
        float analogValue1 = analogInPin1.read(); // Lire la valeur analogique - Cap_courant2
        float analogValue2 = analogInPin2.read(); // Lire la valeur analogique - Cap_courant3

        float analogValue3 = analogInPin3.read(); // Lire la valeur analogique -V_BatMain
        float analogValue4 = analogInPin4.read(); // Lire la valeur analogique -V_Bat1
        float analogValue5 = analogInPin5.read(); // Lire la valeur analogique -V_Bat2
        float analogValue6 = analogInPin6.read(); // Lire la valeur analogique -V_Bat3

        // Convertir la valeur analogique en courant en utilisant la sensibilité du capteur ACS711
        // La sensibilité typique du ACS711 est de 50mV/A

        float Cap_Courant1 = (((analogValue0) * 3.3) - 1.66) * 20;
        float Cap_Courant2 = (((analogValue1) * 3.3) - 1.66) * 20;
        float Cap_Courant3 = (((analogValue2) * 3.3) - 1.66) * 20;

        V_BatMain = calcul_VBat_main(analogValue3 * 3.3); // Supposons que la tension de référence est de 3.3V

        V_Bat1 = calcul_VBat1(analogValue4 * 3.3); // Supposons que la tension de référence est de 3.3V

        V_Bat2 = calcul_VBat2(analogValue5 * 3.3); // Supposons que la tension de référence est de 3.3V

        V_Bat3 = calcul_VBat3(analogValue6 * 3.3); // Supposons que la tension de référence est de 3.3V

        if (checkARU())
        {
            if (compteur_ARU == 10)
            {
                aruCan.data[0] = 1;
                can1.write(aruCan);
                compteur_ARU = 1;
            }
            else
            {
                compteur_ARU++;
            }

            // Eteindre les interrupteurs
            controlSwitch(switchControl1, false);
            controlSwitch(switchControl2, false);
            controlSwitch(switchControl3, false);
        }
        else
        {
            if (compteur_ARU != 0)
            {
                aruCan.data[0] = 0;
                can1.write(aruCan);
                compteur_ARU = 0;
            }
        }

        // Attendre une demande via CAN
        if (can1.read(request))
        {

            if (request.id == 0x200)
            {
                int batteryID = request.data[0];

                if (batteryID == 1)
                {
                    response_V.data[0] = 1;
                    response_V.data[1] = V_BatMain * 10;
                    can1.write(response_V);
                }
                else if (batteryID == 2)
                {
                    response_V.data[0] = 2;
                    response_V.data[1] = V_Bat1 * 10;
                    can1.write(response_V);
                }
                else if (batteryID == 3)
                {
                    response_V.data[0] = 3;
                    response_V.data[1] = V_Bat2 * 10;
                    can1.write(response_V);
                }
                else if (batteryID == 4)
                {
                    response_V.data[0] = 4;
                    response_V.data[1] = V_Bat3 * 10;
                    can1.write(response_V);
                }
            }
            else if (request.id == 0x201)
            {
                int batteryID = request.data[0];

                if (batteryID == 1)
                {
                    response_I.data[0] = 1;
                    response_I.data[1] = Cap_Courant1 * 100;
                    can1.write(response_I);
                }
                else if (batteryID == 2)
                {
                    response_I.data[0] = 2;
                    response_I.data[1] = Cap_Courant2 * 100;
                    can1.write(response_I);
                }
                else if (batteryID == 3)
                {
                    response_I.data[0] = 3;
                    response_I.data[1] = Cap_Courant3 * 100;
                    can1.write(response_I);
                }
            }
            else if (request.id == 0x202)
            {
                int batteryID = request.data[0];

                if (batteryID == 1)
                {
                    response_S.data[0] = 1;
                    response_S.data[1] = switchControl1;
                    can1.write(response_S);
                }
                else if (batteryID == 2)
                {
                    response_S.data[0] = 2;
                    response_S.data[1] = switchControl2;
                    can1.write(response_S);
                }
                else if (batteryID == 3)
                {
                    response_S.data[0] = 3;
                    response_S.data[1] = switchControl3;
                    can1.write(response_S);
                }
            }
            else if (request.id == 0x206)
            {
                int OrderID = request.data[0];
                int state = request.data[1];

                if (OrderID == 1)
                {
                    if (state == 1)
                    {
                        controlSwitch(switchControl1, true);
                    }
                    else if (state == 0)
                    {
                        controlSwitch(switchControl1, false);
                    }
                }
                else if (OrderID == 2)
                {
                    controlSwitch(switchControl2, state == 1 ? true : false);
                }
                else if (OrderID == 3)
                {
                    controlSwitch(switchControl3, state == 1 ? true : false);
                }
                else if (OrderID == 10)
                {
                    TensionMaxBAT = state;
                }
                else if (OrderID == 11)
                {
                    controlSwitch(switchControl1, false);
                    controlSwitch(switchControl2, false);
                    controlSwitch(switchControl3, false);
                }
            }
            else if (request.id == 0x001 || request.id == 0x002)
            {
                // Eteindre les interrupteurs
                controlSwitch(switchControl1, false);
                controlSwitch(switchControl2, false);
                controlSwitch(switchControl3, false);
            }
        }

        if (checkVoltage(V_Bat1, TensionMaxBAT))
        {
            controlSwitch(switchControl1, false);
        }
        if (checkVoltage(V_Bat2, TensionMaxBAT))
        {
            controlSwitch(switchControl2, false);
        }
        if (checkVoltage(V_Bat3, TensionMaxBAT))
        {
            controlSwitch(switchControl3, false);
        }

        ThisThread::sleep_for(10ms);
    }
}