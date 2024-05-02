#ifndef _VL53L0X_H
#define _VL53L0X_H

#include <Arduino.h>
#include <Wire.h>

#include "vl53l0x_api.h"
#include "vl53l0x_platform.h"

#define DEBUG_EN
#define I2C_DEFAULT_ADDR  0x29
#define CONTINUOUS_MODE_MESURE_TIME  5

class Vl53l0x {

  public:
    ~Vl53l0x() {}
    VL53L0X_Error begin(uint8_t address = I2C_DEFAULT_ADDR, bool initWire = true);
    void printPalError(VL53L0X_Error Status);
    void printRangeStatus(VL53L0X_RangingMeasurementData_t* pRangingMeasurementData);

    VL53L0X_Error singleRangingInit();
    VL53L0X_Error highSpeedRangingInit();
    VL53L0X_Error highAccuracyRangingInit();
    VL53L0X_Error longDistanceRangingInit();
    VL53L0X_Error continuousRangingInit();

    VL53L0X_Error performSingleRangingMeasurement(VL53L0X_RangingMeasurementData_t* RangingMeasurementData);
    VL53L0X_Error performContinuousRangingMeasurement(VL53L0X_RangingMeasurementData_t* RangingMeasurementData);

    VL53L0X_Error changeAddress(uint8_t address = I2C_DEFAULT_ADDR);
  private:
    VL53L0X_Error checkVersion();
    VL53L0X_Error setLimitParam();
    VL53L0X_Error calibrationOprt();
    VL53L0X_Error calibrationSet();


    VL53L0X_Dev_t MyDevice;
    VL53L0X_Dev_t* pMyDevice = &MyDevice;
    VL53L0X_Version_t   Version;
    VL53L0X_Version_t*   pVersion   = &Version;
    //VL53L0X_DeviceInfo_t DeviceInfo;

};


#endif
