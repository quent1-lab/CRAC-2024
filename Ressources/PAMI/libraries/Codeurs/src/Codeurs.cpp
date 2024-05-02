#include "Codeurs.h"
#include <Wire.h>

Codeurs::Codeurs(int address) : _address(address)
{
    _gauche = 0;
    _droit = 0;
    _g16 = 0;
    _d16 = 0;
}

void Codeurs::begin(bool initWire)
{
    if (initWire) Wire.begin();
}

bool Codeurs::test()
{
    byte data = 5, error;
    Wire.beginTransmission(_address);
    Wire.write(data);
    error = Wire.endTransmission();
    if (error == 0) {
      Serial.print("I2C device found at address 0x");
      Serial.println(_address, HEX);
      Wire.requestFrom(_address, 1);
      data = 0;
      while (Wire.available()) {  // slave may send less than requested
        data = Wire.read();   // receive a byte
      }
      Serial.print("Data = 0x");
      Serial.println(data, HEX);
      return (data == 0x1F);
    }
    return false;
}

void Codeurs::read16(int16_t &gauche, int16_t &droit)
{
    byte data[4];
    data[0] = 1;
    Wire.beginTransmission(_address);
    Wire.write(data[0]);
    Wire.endTransmission();
    Wire.requestFrom(_address, 4);
    int i = 0;
    while (Wire.available()) {  // slave may send less than requested
      data[i++] = Wire.read();   // receive a byte
    }
    if (i==4) {
      gauche = data[0]<<8 | (data[1]&0xFF);
      droit = data[2]<<8 | (data[3]&0xFF);
    }
}

void Codeurs::reset()
{
    byte data[2] = {0, 1};
    Wire.beginTransmission(_address);
    Wire.write(data[0]);
    Wire.write(data[1]);
    Wire.endTransmission();
    _gauche = 0;
    _droit = 0;
    _g16 = 0;
    _d16 = 0;
}

void Codeurs::read(int32_t &gauche, int32_t &droit)
{
    int16_t ng, nd;
    read16(ng, nd);
    if ((ng > MAX) && (_g16 < -MAX)) {
        _gauche = _gauche - _g16 + ng - 65536;
    } else if ((ng < -MAX) && (_g16 > MAX)) {
        _gauche = _gauche - _g16 + ng + 65536;
    } else {
        _gauche = _gauche - _g16 + ng;
    }
    _g16 = ng;
    if ((nd > MAX) && (_d16 < -MAX)) {
        _droit = _droit - _d16 + nd - 65536;
    } else if ((nd < -MAX) && (_d16 > MAX)) {
        _droit = _droit - _d16 + nd + 65536;
    } else {
        _droit = _droit - _d16 + nd;
    }
    _d16 = nd;
    gauche = _gauche;
    droit =  -_droit; //rajout - pour avoir les valeurs positives
}
