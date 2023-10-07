#include <mbed.h>

DigitalOut led(LED1);

// CAN can(PA_11, PA_12, 1000000);  // CAN Rx pin name, CAN Tx pin name

int main() {
    double temps = 0;

    printf("CRAC stm32f303k8 démo\n");

    while (true) {
        ThisThread::sleep_for(250ms);
        led = 0;
        ThisThread::sleep_for(250ms);
        led = 1;
        printf("%.1f\n", temps);
        temps += 0.5;
    }
}
