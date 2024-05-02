#include "Vl53l0x.h"

/** @brief Print corresponding string of error code.
    @param error code.
 * */
void Vl53l0x::printPalError(VL53L0X_Error status) {
    char buf[VL53L0X_MAX_STRING_LENGTH];
    VL53L0X_GetPalErrorString(status, buf);
    Serial.print("API status:");
    Serial.print(status);
    Serial.print("API error string:");
    Serial.println(buf);
}

/** @brief Print ranging status through param:pRangingMeasurementData
    @param The struct contains ranging status.
 * */
void Vl53l0x::printRangeStatus(VL53L0X_RangingMeasurementData_t* pRangingMeasurementData) {
    char buf[VL53L0X_MAX_STRING_LENGTH];
    uint8_t rangeStatus;

    /*
        New Range status: data is valid when pRangingMeasurementData->RangeStatus = 0
    */
    rangeStatus = pRangingMeasurementData->RangeStatus;

    VL53L0X_GetRangeStatusString(rangeStatus, buf);
    Serial.print("Range status:");
    Serial.print(rangeStatus);
    Serial.println(buf);
}


/** @brief IIC init
    @param IIC address.default address is 0x29.
 * */
VL53L0X_Error Vl53l0x::begin(uint8_t address, bool initWire) {
    if (initWire) Wire.begin();
    pMyDevice->I2cDevAddr      = address;
    pMyDevice->comms_type      =  1;
    pMyDevice->comms_speed_khz =  400;

    VL53L0X_Error status = VL53L0X_ERROR_NONE;

    status = checkVersion();
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    //Serial.println("Call of VL53L0X_DataInit\n");
    status = VL53L0X_DataInit(&MyDevice);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    //Serial.println("Call of VL53L0X_StaticInit\n");
    status = VL53L0X_StaticInit(pMyDevice);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    //Serial.println("Call of VL53L0X_calibration\n");
    status = calibrationOprt();
    //print_pal_error(status);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    //Serial.println("Call of VL53L0X_SetDeviceMode\n");
    status = VL53L0X_SetDeviceMode(pMyDevice, VL53L0X_DEVICEMODE_SINGLE_RANGING); // Setup in single ranging mode
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }


    //Serial.println("Call of VL53L0X_set_limit_param\n");
    status = setLimitParam();
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    return status;
}

/** @brief The module need to calibrated after power-on.

    @return Error code, error if not equal to zero
 * */
VL53L0X_Error Vl53l0x::calibrationOprt() {
    uint32_t refSpadCount;
    uint8_t isApertureSpads;
    uint8_t VhvSettings;
    uint8_t PhaseCal;
    VL53L0X_Error status = VL53L0X_ERROR_NONE;

    //Serial.println("Call of VL53L0X_PerformRefSpadManagement\n");
    status = VL53L0X_PerformRefSpadManagement(pMyDevice,
             &refSpadCount, &isApertureSpads); // Device Initialization
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    //Serial.println("Call of VL53L0X_PerformRefCalibration\n");
    status = VL53L0X_PerformRefCalibration(pMyDevice,
                                           &VhvSettings, &PhaseCal); // Device Initialization
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    return status;
}

/** @brief Called when module need to calibrated. retain.

 * */
VL53L0X_Error Vl53l0x::calibrationSet() {
    VL53L0X_Error status = VL53L0X_ERROR_NONE;
    return status;
}

/** @brief Set limitation factor.

    @return Error code, error if not equal to zero
 * */
VL53L0X_Error Vl53l0x::setLimitParam() {
    VL53L0X_Error status = VL53L0X_ERROR_NONE;
    status = VL53L0X_SetLimitCheckEnable(pMyDevice,
                                         VL53L0X_CHECKENABLE_SIGMA_FINAL_RANGE, 1);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    status = VL53L0X_SetLimitCheckEnable(pMyDevice,
                                         VL53L0X_CHECKENABLE_SIGNAL_RATE_FINAL_RANGE, 1);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    status = VL53L0X_SetLimitCheckEnable(pMyDevice,
                                         VL53L0X_CHECKENABLE_RANGE_IGNORE_THRESHOLD, 1);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    status = VL53L0X_SetLimitCheckValue(pMyDevice,
                                        VL53L0X_CHECKENABLE_RANGE_IGNORE_THRESHOLD,
                                        (FixPoint1616_t)(1.5 * 0.023 * 65536));
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    return status;
}

/** @brief As function name.

    @return Error code, error if not equal to zero
 * */
VL53L0X_Error Vl53l0x::checkVersion() {
    VL53L0X_Error status = VL53L0X_ERROR_NONE;
    int32_t status_int;

    status_int = VL53L0X_GetVersion(pVersion);
    if (status_int != 0) {
        status = VL53L0X_ERROR_CONTROL_INTERFACE;
        return status;
    }

    // if (pVersion->major != VERSION_REQUIRED_MAJOR ||
    //         pVersion->minor != VERSION_REQUIRED_MINOR ||
    //         pVersion->build != VERSION_REQUIRED_BUILD) {
    //     // Serial.println("VL53L0X API Version Error");
    // }
    return status;
}

/** @brief The single ranging mode init.

    @return Error code, error if not equal to zero
 * */
VL53L0X_Error Vl53l0x::singleRangingInit() {
    VL53L0X_Error status = VL53L0X_ERROR_NONE;
    //Serial.println("Call of VL53L0X_SetDeviceMode\n");
    status = VL53L0X_SetDeviceMode(pMyDevice, VL53L0X_DEVICEMODE_SINGLE_RANGING); // Setup in single ranging mode
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }


    //Serial.println("Call of VL53L0X_set_limit_param\n");
    status = VL53L0X_SetLimitCheckEnable(pMyDevice,
                                         VL53L0X_CHECKENABLE_SIGMA_FINAL_RANGE, 1);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    status = VL53L0X_SetLimitCheckEnable(pMyDevice,
                                         VL53L0X_CHECKENABLE_SIGNAL_RATE_FINAL_RANGE, 1);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    status = VL53L0X_SetLimitCheckEnable(pMyDevice,
                                         VL53L0X_CHECKENABLE_RANGE_IGNORE_THRESHOLD, 1);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    status = VL53L0X_SetLimitCheckValue(pMyDevice,
                                        VL53L0X_CHECKENABLE_RANGE_IGNORE_THRESHOLD,
                                        (FixPoint1616_t)(1.5 * 0.023 * 65536));
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    return status;
}

/** @brief The single&high speed ranging ranging mode init.Reduce excute time.

    @return Error code, error if not equal to zero
 * */
VL53L0X_Error Vl53l0x::highSpeedRangingInit() {
    VL53L0X_Error status = VL53L0X_ERROR_NONE;
    //Serial.println("Call of VL53L0X_SetDeviceMode\n");
    status = VL53L0X_SetDeviceMode(pMyDevice, VL53L0X_DEVICEMODE_SINGLE_RANGING); // Setup in single ranging mode
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    status = VL53L0X_SetLimitCheckEnable(pMyDevice,
                                         VL53L0X_CHECKENABLE_SIGMA_FINAL_RANGE, 1);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    status = VL53L0X_SetLimitCheckEnable(pMyDevice,
                                         VL53L0X_CHECKENABLE_SIGNAL_RATE_FINAL_RANGE, 1);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }


    status = VL53L0X_SetLimitCheckValue(pMyDevice,
                                        VL53L0X_CHECKENABLE_SIGNAL_RATE_FINAL_RANGE,
                                        (FixPoint1616_t)(0.25 * 65536));
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }


    status = VL53L0X_SetLimitCheckValue(pMyDevice,
                                        VL53L0X_CHECKENABLE_SIGMA_FINAL_RANGE,
                                        (FixPoint1616_t)(32 * 65536));
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }


    status = VL53L0X_SetMeasurementTimingBudgetMicroSeconds(pMyDevice,
             30000);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    return status;
}


/** @brief The single&high accuracy ranging ranging mode init.It will cost much more time

    @return Error code, error if not equal to zero
 * */
VL53L0X_Error Vl53l0x::highAccuracyRangingInit() {
    VL53L0X_Error status = VL53L0X_ERROR_NONE;
    //Serial.println("Call of VL53L0X_SetDeviceMode\n");
    status = VL53L0X_SetDeviceMode(pMyDevice, VL53L0X_DEVICEMODE_SINGLE_RANGING); // Setup in single ranging mode
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    status = VL53L0X_SetLimitCheckEnable(pMyDevice,
                                         VL53L0X_CHECKENABLE_SIGMA_FINAL_RANGE, 1);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    status = VL53L0X_SetLimitCheckEnable(pMyDevice,
                                         VL53L0X_CHECKENABLE_SIGNAL_RATE_FINAL_RANGE, 1);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }


    status = VL53L0X_SetLimitCheckValue(pMyDevice,
                                        VL53L0X_CHECKENABLE_SIGNAL_RATE_FINAL_RANGE,
                                        (FixPoint1616_t)(0.25 * 65536));
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    status = VL53L0X_SetLimitCheckValue(pMyDevice,
                                        VL53L0X_CHECKENABLE_SIGMA_FINAL_RANGE,
                                        (FixPoint1616_t)(18 * 65536));
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    status = VL53L0X_SetMeasurementTimingBudgetMicroSeconds(pMyDevice,
             200000);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    return status;
}

/** @brief The single&long distance ranging ranging mode init.

    @return Error code, error if not equal to zero
 * */
VL53L0X_Error Vl53l0x::longDistanceRangingInit() {
    VL53L0X_Error status = VL53L0X_ERROR_NONE;
    //Serial.println("Call of VL53L0X_SetDeviceMode\n");
    status = VL53L0X_SetDeviceMode(pMyDevice, VL53L0X_DEVICEMODE_SINGLE_RANGING); // Setup in single ranging mode
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    status = VL53L0X_SetLimitCheckEnable(pMyDevice,
                                         VL53L0X_CHECKENABLE_SIGMA_FINAL_RANGE, 1);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    status = VL53L0X_SetLimitCheckEnable(pMyDevice,
                                         VL53L0X_CHECKENABLE_SIGNAL_RATE_FINAL_RANGE, 1);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    status = VL53L0X_SetLimitCheckValue(pMyDevice,
                                        VL53L0X_CHECKENABLE_SIGNAL_RATE_FINAL_RANGE,
                                        (FixPoint1616_t)(0.1 * 65536));
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    status = VL53L0X_SetLimitCheckValue(pMyDevice,
                                        VL53L0X_CHECKENABLE_SIGMA_FINAL_RANGE,
                                        (FixPoint1616_t)(60 * 65536));
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    status = VL53L0X_SetMeasurementTimingBudgetMicroSeconds(pMyDevice,
             33000);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    status = VL53L0X_SetVcselPulsePeriod(pMyDevice,
                                         VL53L0X_VCSEL_PERIOD_PRE_RANGE, 18);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    status = VL53L0X_SetVcselPulsePeriod(pMyDevice,
                                         VL53L0X_VCSEL_PERIOD_FINAL_RANGE, 14);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    return status;
}

/** @brief The continuous ranging ranging mode init.Excute without interval.

    @return Error code, error if not equal to zero
 * */
VL53L0X_Error Vl53l0x::continuousRangingInit() {
    VL53L0X_Error status = VL53L0X_ERROR_NONE;
    status = VL53L0X_SetDeviceMode(pMyDevice, VL53L0X_DEVICEMODE_CONTINUOUS_RANGING);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }
    return status;
}

/** @brief start mesurement and get result.
    @param The result.
    @return Error code, error if not equal to zero
 * */
VL53L0X_Error Vl53l0x::performContinuousRangingMeasurement(VL53L0X_RangingMeasurementData_t*
        RangingMeasurementData) {
    VL53L0X_Error status = VL53L0X_ERROR_NONE;
    uint8_t stat = 0;
    // uint32_t stop_stat = 0;
    status = VL53L0X_StartMeasurement(pMyDevice);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }

    // while(1)
    // {
    while (1) {
        status = VL53L0X_GetMeasurementDataReady(pMyDevice, &stat);
        if (VL53L0X_ERROR_NONE != status) {
            return status;
        }
        if (1 == stat) {
            break;
        }
    }

    status = VL53L0X_GetRangingMeasurementData(pMyDevice, RangingMeasurementData);
    if (VL53L0X_ERROR_NONE != status) {
        return status;
    }
    if (RangingMeasurementData->RangeMilliMeter >= 2000) {
        // SerialUSB.println("out of ranger");
    } else {
        // SerialUSB.print("distance::");
        // SerialUSB.println(RangingMeasurementData->RangeMilliMeter);
    }

    VL53L0X_ClearInterruptMask(pMyDevice, VL53L0X_REG_SYSTEM_INTERRUPT_GPIO_NEW_SAMPLE_READY);
    VL53L0X_PollingDelay(pMyDevice);
    // }

    /***************************************************stop_part************************/
    // status = VL53L0X_StopMeasurement(pMyDevice);
    // if(VL53L0X_ERROR_NONE!=status) return status;

    // while(1)
    // {
    //     status = VL53L0X_GetStopCompletedstatus(pMyDevice,(uint32_t*)&stop_stat);
    //     if(VL53L0X_ERROR_NONE!=status) return status;
    //     if(1==stop_stat) break;
    // }
    return status;
}

/** @brief start mesurement and get result.
    @param The result.
    @return Error code, error if not equal to zero
 * */
VL53L0X_Error Vl53l0x::performSingleRangingMeasurement(VL53L0X_RangingMeasurementData_t* RangingMeasurementData) {
    VL53L0X_Error status = VL53L0X_ERROR_NONE;
    // uint32_t milli_value_start = 0, milli_value_stop = 0;
    //VL53L0X_RangingMeasurementData_t RangingMeasurementData;
    if (status == VL53L0X_ERROR_NONE) {
        // milli_value_start = millis();
        status = VL53L0X_PerformSingleRangingMeasurement(pMyDevice,
                 RangingMeasurementData);
        // milli_value_stop = millis();

        // Serial.print("time of mesurement: ");
        // Serial.println(milli_value_stop-milli_value_start);

    }
    return status;
}

VL53L0X_Error Vl53l0x::changeAddress(uint8_t address) {
    VL53L0X_Error status = VL53L0X_ERROR_NONE;
    status = VL53L0X_SetDeviceAddress(pMyDevice, address * 2);
    if (status == VL53L0X_ERROR_NONE) {
        pMyDevice->I2cDevAddr = address;
    }
    return status;
}
