#include <mbed.h>
#include <CAN.h>

#define TensionMin 0
#define TensionMax 30

DigitalOut led(LED1);

CAN can1(PA_11, PA_12, 1000000); // CAN Rx pin name (PA11), CAN Tx pin name (PA12), Frequency = 500kbits

AnalogIn analogInPin0(A2); // Utilisez le port analogique (A2) sur la carte F303K8  - Cap_courant1
AnalogIn analogInPin1(D6); // Utilisez le port analogique (D6) sur la carte F303K8  - Cap_courant2
AnalogIn analogInPin2(A6); // Utilisez le port analogique (A6) sur la carte F303K8  - Cap_courant3

AnalogIn analogInPin3(A1); // Utilisez le port analogique (A1) sur la carte F303K8  - V_BatMain
AnalogIn analogInPin4(A3); // Utilisez le port analogique (A3) sur la carte F303K8  - V_Bat1
AnalogIn analogInPin5(D3); // Utilisez le port analogique (D3) sur la carte F303K8  - V_Bat2
AnalogIn analogInPin6(A0); // Utilisez le port analogique (A0) sur la carte F303K8  - V_Bat3

DigitalOut switchControl1(D5); // Interrupteur 1 - D5
DigitalOut switchControl2(D4); // Interrupteur 2 - D4
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

int main()
{
    double temps = 0;
    printf("CRAC stm32f303k8 démo\n");

    // Création d'un message CAN
    CANMessage msg, msg1, msg2, msg3, msg4, msg5, msg6;

    // Définition de l'ID du message CAN (11 bits)
    msg.id = 0x123;
    msg1.id = 0x124;
    msg2.id = 0x125;
    msg3.id = 0x126;
    msg4.id = 0x127;
    msg5.id = 0x128;
    msg6.id = 0x129;

    // Définition de la longueur des données (8 octets maximum)
    msg.len = 4;
    msg1.len = 4;
    msg2.len = 4;
    msg3.len = 4;
    msg4.len = 4;
    msg5.len = 4;
    msg6.len = 4;
    float V_BatMain, V_Bat1, V_Bat2, V_Bat3;

    while (1)
    {
        // Attendre un court laps de temps avant la prochaine lecture
        ThisThread::sleep_for(500ms);
        led = 0;
        ThisThread::sleep_for(500ms);
        led = 1;
        // printf("%.1f\n", temps);
        temps += 0.5;

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

        // Control des seuils de tension:

        if (V_Bat1 >= TensionMin && V_Bat1 <= TensionMax)
        {
            controlSwitch(switchControl1, true);
        }
        else
        {
            controlSwitch(switchControl1, false);
        }

        if (V_Bat2 >= TensionMin && V_Bat2 <= TensionMax)
        {
            controlSwitch(switchControl2, true);
        }
        else
        {
            controlSwitch(switchControl2, false);
        }

        if (V_Bat3 >= TensionMin && V_Bat3 <= TensionMax)
        {
            controlSwitch(switchControl3, true);
        }
        else
        {
            controlSwitch(switchControl3, false);
        }

        // Remplissage des données
        msg.data[0] = V_BatMain;
        msg1.data[0] = V_Bat1;
        msg2.data[0] = V_Bat2;
        msg3.data[0] = V_Bat3;
        msg4.data[0] = Cap_I1;
        msg5.data[0] = Cap_Courant2;
        msg6.data[0] = Cap_Courant3;
        /*if (V_Bat1 < 7.0)
        {
            printf("Batterie Faible 1. Mettre à Charger !!\n");
        }
        if (V_Bat2 < 7.0)
        {
            printf("Batterie Faible 2. Mettre à Charger !!\n");
        }
        if (V_Bat3 < 7.0)
        {
            printf("Batterie Faible 3. Mettre à Charger !!\n");
        }*/

        // Afficher la valeur du courant
        printf("Cap_Courant1: %.3f A\r\n", Cap_I1);
        if (can1.write(msg4))
        {
            printf("Erreur lors de l'envoi du message CAN 4 !\n");
        }
        else
        {
            printf("Message CAN 4 envoyé avec succès !\n");
        }
        // ThisThread::sleep_for(500ms);

        printf("Cap_Courant2: %.3f A\r\n", Cap_Courant2);
        if (can1.write(msg5))
        {
            printf("Erreur lors de l'envoi du message CAN 5 !\n");
        }
        else
        {
            printf("Message CAN 5 envoyé avec succès !\n");
        }
        // ThisThread::sleep_for(500ms);

        printf("Cap_Courant3: %.3f A\r\n\r\n", Cap_Courant3);
        if (can1.write(msg6))
        {
            printf("Erreur lors de l'envoi du message CAN 6 !\n");
        }
        else
        {
            printf("Message CAN 6 envoyé avec succès !\n");
        }
        // ThisThread::sleep_for(500ms);

        printf("V_BatMain: %.3f V\r\n", V_BatMain);
        // Envoi du message CAN de V_BatMain
        if (can1.write(msg))
        {
            printf("Erreur lors de l'envoi du message CAN !\n");
        }
        else
        {
            printf("Message CAN envoyé avec succès !\n");
        }
        // ThisThread::sleep_for(500ms);

        printf("V_Bat1: %.3f V\r\n", V_Bat1);
        if (can1.write(msg1))
        {
            printf("Erreur lors de l'envoi du message CAN 1 !\n");
        }
        else
        {
            printf("Message CAN 1 envoyé avec succès !\n");
        }
        // ThisThread::sleep_for(500ms);

        printf("V_Bat2: %.3f V\r\n", V_Bat2);
        if (can1.write(msg2))
        {
            printf("Erreur lors de l'envoi du message CAN 2 !\n");
        }
        else
        {
            printf("Message CAN 2 envoyé avec succès !\n");
        }
        // ThisThread::sleep_for(500ms);

        printf("V_Bat3: %.3f V\r\n\r\n", V_Bat3);
        if (can1.write(msg3))
        {
            printf("Erreur lors de l'envoi du message CAN 3 !\n");
        }
        else
        {
            printf("Message CAN 3 envoyé avec succès !\n");
        }
    }
}