#include "Vl53l0x.h"

Vl53l0x monCapteur;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  VL53L0X_Error status = VL53L0X_ERROR_NONE;
  status = monCapteur.begin(I2C_DEFAULT_ADDR, true);
  if (VL53L0X_ERROR_NONE != status) {
    Serial.println("start vl53l0x mesurement failed!");
    monCapteur.printPalError(status);
    while (1);
  }
  monCapteur.continuousRangingInit();
  if (VL53L0X_ERROR_NONE != status) {
    Serial.println("start vl53l0x mesurement failed!");
    monCapteur.printPalError(status);
    while (1);
  }
}

int count = 0;

void loop() {
  // put your main code here, to run repeatedly:
  VL53L0X_RangingMeasurementData_t rangingMeasurementData;
  monCapteur.performContinuousRangingMeasurement(&rangingMeasurementData);
  if (rangingMeasurementData.RangeMilliMeter >= 2000) {
    Serial.println("out of ranger");
  } else {
    Serial.print("distance::");
    Serial.println(rangingMeasurementData.RangeMilliMeter);
  }
  delay(100);
  count++;
  VL53L0X_Error status = VL53L0X_ERROR_NONE;
  if (count == 100) {
    status = monCapteur.changeAddress(0x50);
    Serial.println("");
    if (VL53L0X_ERROR_NONE != status) {
      Serial.println("change address 0x50 failed!");
      monCapteur.printPalError(status);
      while (1);
    }
    Serial.println("Change address : 0x50");
    Serial.println("");
  }
  if (count == 200) {
    status = monCapteur.changeAddress(0x29);
    Serial.println("");
    if (VL53L0X_ERROR_NONE != status) {
      Serial.println("change address 0x29 failed!");
      monCapteur.printPalError(status);
      while (1);
    }
    Serial.println("Change address : 0x29");
    Serial.println("");
  }
}

