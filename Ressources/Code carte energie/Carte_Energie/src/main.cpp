#include <mbed.h>
#include <CAN.h>

DigitalOut led(LED1);

CAN can1(PA_11, PA_12, 1000000); // CAN Rx pin name (PA11), CAN Tx pin name (PA12), Frequency = 1000kbits

AnalogIn analogInPin0(A2); // Utilisez le port analogique (A2) sur la carte F303K8  - Cap_courant1
AnalogIn analogInPin1(D6); // Utilisez le port analogique (D6) sur la carte F303K8  - Cap_courant2
AnalogIn analogInPin2(A6); // Utilisez le port analogique (A6) sur la carte F303K8  - Cap_courant3

AnalogIn analogInPin3(A1); // Utilisez le port analogique (A1) sur la carte F303K8  - V_BatMain
AnalogIn analogInPin4(A3); // Utilisez le port analogique (A3) sur la carte F303K8  - V_Bat1
AnalogIn analogInPin5(D3); // Utilisez le port analogique (D3) sur la carte F303K8  - V_Bat2
AnalogIn analogInPin6(A0); // Utilisez le port analogique (A0) sur la carte F303K8  - V_Bat3

DigitalOut switchControl1(D5);  // Interrupteur 1 - D5
DigitalOut switchControl2(D4);  // Interrupteur 2 - D4
DigitalOut switchControl3(D11); // Interrupteur 3 - D11

void controlSwitch(DigitalOut &switchControl, bool on)
{
    switchControl = on;
}

float calcul_VBat_main(float x)
{
    float y;
    y = (-0.15 * pow(x, 6)) + (1.3883 * pow(x, 5)) - (5.1117 * pow(x, 4)) + (9.5784 * pow(x, 3)) - (9.83 * pow(x, 2)) + (16.839 * x) + 0.00495;
    return y;
}

float calcul_VBat1(float x)
{
    float y;
    y = (-0.028 * pow(x, 6)) + (0.2332 * pow(x, 5)) - (0.7459 * pow(x, 4)) + (1.157 * pow(x, 3)) - (0.885 * pow(x, 2)) + (11.353 * x) + 0.0123;
    return y;
}

float calcul_VBat2(float x)
{
    float y;
    y = (0.058 * pow(x, 6)) - (0.524 * pow(x, 5)) + (1.7346 * pow(x, 4)) - (2.516 * pow(x, 3)) + (1.4789 * pow(x, 2)) + (11.012 * x) + 0.0213;
    return y;
}

float calcul_VBat3(float x)
{
    float y;
    y = (0.0286 * pow(x, 6)) - (0.258 * pow(x, 5)) + (0.8607 * pow(x, 4)) - (1.2997 * pow(x, 3)) + (0.8741 * pow(x, 2)) + (10.989 * x) + 0.0138;
    return y;
}

float calcul_courant1(float x)
{
    float y;
    y = (-0.0023 * pow(x, 6)) + (0.0165 * pow(x, 5)) - (0.0396 * pow(x, 4)) + (0.0338 * pow(x, 3)) + (0.0134 * pow(x, 2)) + (0.8671 * x) + 0.1753;
    return y;
}

bool checkVoltage(float voltage, float min, float max)
{
    return voltage >= min && voltage <= max;
}

int main()
{
    printf("CRAC stm32f303k8 démo\n");

    // Création d'un message CAN
    CANMessage request;
    CANMessage response_V, response_I, response_S;
    CANMessage order; // Ordre à exécuter
    // requetes (tension, courant, switch) / reponse (tension, courant, switch)

    // Définition de l'ID du message CAN (11 bits)
    response_V.id = 0x203;
    response_I.id = 0x204;
    response_S.id = 0x205;
    order.id = 0x206;

    // Définition de la longueur des données (8 octets maximum)
    request.len = 3;
    response_V.len = 2;
    response_I.len = 2;
    response_S.len = 2;
    order.len = 2;

    float V_BatMain, V_Bat1, V_Bat2, V_Bat3;
    float TensionMin = 0, TensionMaxBAT1 = 20, TensionMaxBAT2 = 20, TensionMaxBAT3 = 20;

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
        float Cap_I1 = calcul_courant1(Cap_Courant1);
        float Cap_Courant2 = (((analogValue1) * 3.3) - 1.66) * 20;
        float Cap_Courant3 = (((analogValue2) * 3.3) - 1.66) * 20;

        V_BatMain = calcul_VBat_main(analogValue3 * 3.3); // Supposons que la tension de référence est de 3.3V

        V_Bat1 = calcul_VBat1(analogValue4 * 3.3); // Supposons que la tension de référence est de 3.3V

        V_Bat2 = calcul_VBat2(analogValue5 * 3.3); // Supposons que la tension de référence est de 3.3V

        V_Bat3 = calcul_VBat3(analogValue6 * 3.3); // Supposons que la tension de référence est de 3.3V

        // Attendre une demande via CAN
        if (can1.read(request))
        {


            switch (request.id)
            {
            case 0x200:
            {
                printf("Id 0x200 \n");
                int batteryID = request.data[0];
                switch (batteryID)
                {
                case 1:
                    response_V.data[0] = 1;
                    response_V.data[1] = V_BatMain *10;
                    can1.write(response_V);
                    break;
                case 2:
                    response_V.data[0] = 2;
                    response_V.data[1] = V_Bat1;
                    can1.write(response_V);
                    break;
                case 3:
                    response_V.data[0] = 3;
                    response_V.data[1] = V_Bat2;
                    can1.write(response_V);
                    break;
                case 4:
                    response_V.data[0] = 4;
                    response_V.data[1] = V_Bat3;
                    can1.write(response_V);
                    break;
                default:
                    continue;
                }
                break;
            }
            case 0x201:
            {
                int batteryID = request.data[0];

                switch (batteryID)
                {
                case 1:
                    response_I.data[0] = 1;
                    response_I.data[1] = Cap_I1;
                    can1.write(response_I);
                    break;
                case 2:
                    response_I.data[0] = 2;
                    response_I.data[1] = Cap_Courant2;
                    can1.write(response_I);
                    break;
                case 3:
                    response_I.data[0] = 3;
                    response_I.data[1] = Cap_Courant3;
                    can1.write(response_I);
                    break;
                default:
                    continue;
                }
                break;
            }
            case 0x202:
            {
                int batteryID = request.data[0];

                switch (batteryID)
                {
                case 1:
                    response_S.data[0] = 1;
                    response_S.data[1] = switchControl1;
                    can1.write(response_S);
                    break;
                case 2:
                    response_S.data[0] = 2;
                    response_S.data[1] = switchControl2;
                    can1.write(response_S);
                    break;
                case 3:
                    response_S.data[0] = 3;
                    response_S.data[1] = switchControl3;
                    can1.write(response_S);
                    break;
                default:
                    continue;
                }
                break;
            }
            case 0x206:
            {
                int OrderID = request.data[0];
                float state = request.data[1];

                switch (OrderID)
                {
                case 1:
                    controlSwitch(switchControl1, state == 1.0f ? true : false);
                    break;
                case 2:
                    controlSwitch(switchControl2, state == 1.0f ? true : false);
                    break;
                case 3:
                    controlSwitch(switchControl3, state == 1.0f ? true : false);
                    break;
                case 10:
                    TensionMin = state;
                    break;
                case 11:
                    TensionMaxBAT1 = state;
                    break;
                case 12:
                    TensionMaxBAT2 = state;
                    break;
                case 13:
                    TensionMaxBAT3 = state;
                    break;
                }
            }
            break;
            }
        }

        // Contrôle des seuils de tension
        switchControl1 = checkVoltage(V_Bat1, TensionMin, TensionMaxBAT1) ? 1 : 0;
        switchControl2 = checkVoltage(V_Bat2, TensionMin, TensionMaxBAT2) ? 1 : 0;
        switchControl3 = checkVoltage(V_Bat3, TensionMin, TensionMaxBAT3) ? 1 : 0;

        ThisThread::sleep_for(100ms);
    }
}