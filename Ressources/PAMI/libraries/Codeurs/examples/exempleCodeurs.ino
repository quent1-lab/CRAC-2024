#include "Codeurs.h"

Codeurs codeurs;

void setup() {
    codeurs.begin();
    Serial.begin(115200);
    Serial.println("\nI2C Encoders");
}

void loop() {
    int32_t g, d;
    Serial.println("CRAC encoders demo");
    
    Serial.println("Test");
    while (!codeurs.test()) {
        Serial.println("Codeurs non connectes");
        delay(1000);
    }
    Serial.println("Codeurs ok");
    codeurs.reset();  
    while(1) {
        codeurs.read(g, d);
        Serial.print(g);
        Serial.print(" ");
        Serial.println(d);
        delay(100);
    }
}
