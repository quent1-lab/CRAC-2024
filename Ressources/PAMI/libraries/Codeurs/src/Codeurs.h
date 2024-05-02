#ifndef _CODEURS_H
#define _CODEURS_H

#include <Arduino.h>

class Codeurs {
    public:
        Codeurs(int address = 0x10);
        void begin(bool initWire = true);
        bool test();
        void reset();
        void read16(int16_t &gauche, int16_t &droit);
        void read(int32_t &gauche, int32_t &droit);
    private:
        static const int16_t MAX = 16384;
        int _address;
        int32_t _gauche, _droit;
        int16_t _g16, _d16;
};

#endif
