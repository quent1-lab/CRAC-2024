//------------------------------------------------------------------------------
/* herkulex servo library for mbed
 *
 * Copyright (c) 2012-2013 Yoonseok Pyo, MIT License
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy of this software
 * and associated documentation files (the "Software"), to deal in the Software without restriction,
 * including without limitation the rights to use, copy, modify, merge, publish, distribute,
 * sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all copies or
 * substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
 * BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
 * DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */
//------------------------------------------------------------------------------
#include "mbed.h"
#include "herkulex.h"

// Create a DigitalOutput object to toggle an LED whenever data is received.
static DigitalOut led(LED1);
int16_t pos_position = 0;
uint8_t pos_time = 0;
uint8_t pos_led = 0;

//------------------------------------------------------------------------------
Herkulex::Herkulex(PinName tx, PinName rx, uint32_t baudRate)
{
    serial = new BufferedSerial(tx, rx);

    serial->set_baud(115200);
    serial->set_format(
        /* bits */ 8,
        /* parity */ SerialBase::None,
        /* stop bit */ 1);
}

//------------------------------------------------------------------------------
Herkulex::~Herkulex()
{
    delete serial;
}

//------------------------------------------------------------------------------
void Herkulex::txPacket(uint8_t packetSize, uint8_t *data)
{
    printf("WRITE %d Bytes on serial :\n", serial->write(data, packetSize));

    for (int i = 0; i < packetSize; i++)
    {
        printf("\t0x%X", data[i]);
    }
    printf("\n");
}

//------------------------------------------------------------------------------
void Herkulex::rxPacket(uint8_t packetSize, uint8_t *data)
{
    printf("READ %d Bytes on serial\n", serial->read(data, packetSize));

    for (int i = 0; i < packetSize; i++)
    {
        printf("\t0x%X", data[i]);
    }
    printf("\n");
}

//------------------------------------------------------------------------------
void Herkulex::clear(uint8_t id)
{
    uint8_t txBuf[11];

    txBuf[0] = HEADER;              // Packet Header (0xFF)
    txBuf[1] = HEADER;              // Packet Header (0xFF)
    txBuf[2] = MIN_PACKET_SIZE + 4; // Packet Size
    txBuf[3] = id;                  // Servo ID
    txBuf[4] = CMD_RAM_WRITE;       // Command Ram Write (0x03)
    txBuf[5] = 0;                   // Checksum1
    txBuf[6] = 0;                   // Checksum2
    txBuf[7] = RAM_STATUS_ERROR;    // Address 48
    txBuf[8] = BYTE2;               // Length
    txBuf[9] = 0;                   // Clear RAM_STATUS_ERROR
    txBuf[10] = 0;                  // Clear RAM_STATUS_DETAIL

    // Checksum1 = (PacketSize ^ pID ^ CMD ^ Data[0] ^ Data[1] ^ ... ^ Data[n]) & 0xFE
    // Checksum2 = (~Checksum1)&0xFE
    txBuf[5] = (txBuf[2] ^ txBuf[3] ^ txBuf[4] ^ txBuf[7] ^ txBuf[8] ^ txBuf[9] ^ txBuf[10]) & 0xFE;
    txBuf[6] = (~(txBuf[5])) & 0xFE;

    // send packet (mbed -> herkulex)
    txPacket(11, txBuf);
}

//------------------------------------------------------------------------------
void Herkulex::rollback(uint8_t id, bool idSkip, bool baudSkip)
{
    uint8_t txBuf[11];

    txBuf[0] = HEADER;              // Packet Header (0xFF)
    txBuf[1] = HEADER;              // Packet Header (0xFF)
    txBuf[2] = MIN_PACKET_SIZE + 2; // Packet Size
    txBuf[3] = id;                  // Servo ID
    txBuf[4] = CMD_ROLLBACK;        // Command Ram Write (0x03)
    txBuf[5] = 0;                   // Checksum1
    txBuf[6] = 0;                   // Checksum2
    txBuf[7] = idSkip;
    txBuf[8] = baudSkip;

    txBuf[5] = (txBuf[2] ^ txBuf[3] ^ txBuf[4] ^ txBuf[7] ^ txBuf[8]) & 0xFE;
    txBuf[6] = (~(txBuf[5])) & 0xFE;

    // send packet (mbed -> herkulex)
    txPacket(MIN_PACKET_SIZE + 2, txBuf);
}

//------------------------------------------------------------------------------
void Herkulex::reset(uint8_t id)
{
    uint8_t txBuf[11];

    txBuf[0] = HEADER;          // Packet Header (0xFF)
    txBuf[1] = HEADER;          // Packet Header (0xFF)
    txBuf[2] = MIN_PACKET_SIZE; // Packet Size
    txBuf[3] = id;              // Servo ID
    txBuf[4] = CMD_REBOOT;      // Command Ram Write (0x03)
    txBuf[5] = 0;               // Checksum1
    txBuf[6] = 0;

    // Checksum1 = (PacketSize ^ pID ^ CMD ^ Data[0] ^ Data[1] ^ ... ^ Data[n]) & 0xFE
    // Checksum2 = (~Checksum1)&0xFE
    txBuf[5] = (txBuf[2] ^ txBuf[3] ^ txBuf[4]) & 0xFE;
    txBuf[6] = (~(txBuf[5])) & 0xFE;

    // send packet (mbed -> herkulex)
    txPacket(MIN_PACKET_SIZE, txBuf);
}

//------------------------------------------------------------------------------
int Herkulex::getId(void)
{
    uint8_t txBuf[MIN_PACKET_SIZE];
    uint8_t rxBuf[MIN_PACKET_SIZE + 2];

    for (int id = 1; id < 0xFE; id++)
    {
        txBuf[0] = HEADER;          // Packet Header (0xFF)
        txBuf[1] = HEADER;          // Packet Header (0xFF)
        txBuf[2] = MIN_PACKET_SIZE; // Packet Size
        txBuf[3] = id;              // Servo ID
        txBuf[4] = ROM_ACK_POLICY;  // Command Ram Read (0x04)
        txBuf[5] = 0;               // Checksum1
        txBuf[6] = 0;

        // Checksum1 = (PacketSize ^ pID ^ CMD ^ Data[0] ^ Data[1] ^ ... ^ Data[n]) & 0xFE
        // Checksum2 = (~Checksum1)&0xFE
        txBuf[5] = (txBuf[2] ^ txBuf[3] ^ txBuf[4]) & 0xFE;
        txBuf[6] = (~(txBuf[5])) & 0xFE;

        txPacket(MIN_PACKET_SIZE, txBuf);
        ThisThread::sleep_for(200ms);
        rxPacket(MIN_PACKET_SIZE + 2, rxBuf);

        if ((rxBuf[0] == HEADER) && (rxBuf[1] == HEADER) && (rxBuf[2] == MIN_PACKET_SIZE + 2) && (rxBuf[3] == id) && (rxBuf[4] == ROM_STOP_DETECTION_PERIOD) && (rxBuf[5] == ((rxBuf[2] ^ rxBuf[3] ^ rxBuf[4] ^ rxBuf[7] ^ rxBuf[8]) & 0xFE)) && (rxBuf[6] == ((~(rxBuf[5])) & 0xFE)) && (rxBuf[7] == 0) && (rxBuf[8] == 0))
        {
            printf("ID = %d", id);
            return id;
        }
    }
}
/*
+Send : FF FF [07] 01 (07) {00 FE}
-Recv : FF FF [09] 01 (47) {4E B0} 00 00
+Send : FF FF [09] 01 (02) {08 F6} 00 02
-Recv : FF FF [0D] 01 (42) {4C B2} 00 02 01 01 00 00

+Send : FF FF [07] 02 (07) {02 FC}
-Recv : FF FF [09] 02 (47) {4C B2} 00 00
+Send : FF FF [09] 02 (02) {0A F4} 00 02
-Recv : FF FF [0D] 02 (42) {4E B0} 00 02 01 01 00 00

+Send : FF FF [07] 03 (07) {02 FC}
-Recv : FF FF [09] 03 (47) {4C B2} 00 00
+Send : FF FF [09] 03 (02) {0A F4} 00 02
-Recv : FF FF [0D] 03 (42) {4E B0} 00 02 01 01 00 00

+Send : FF FF [0D] 02 (01) {46 B8} 06 04 01 01 7F 35
+Send : FF FF [0D] 02 (03) {42 BC} 00 04 01 01 7F 35
+Send : FF FF [09] 02 (02) {0A F4} 06 04
+Send : FF FF [09] 02 (04) {0A F4} 00 04
+Send : FF FF [07] 01 (07) {00 FE}
-Recv : FF FF [09] 01 (47) {4E B0} 00 00
+Send : FF FF [09] 01 (02) {08 F6} 00 02
-Recv : FF FF [0D] 01 (42) {4C B2} 00 02 01 01 00 00
+Send : FF FF [09] 01 (02) {3C C2} 00 36
+Send : FF FF [09] 01 (04) {46 B8} 00 4A
+Send : FF FF [07] 01 (07) {00 FE}
+Send : FF FF [09] 01 (02) {3C C2} 00 36
+Send : FF FF [09] 01 (04) {46 B8} 00 4A
+Send : FF FF [07] 01 (07) {00 FE}
-Recv : FF FF [09] 01 (47) {4E B0} 00 00
-Recv : FF FF [09] 01 (47) {4E B0} 00 00
*/
//------------------------------------------------------------------------------
void Herkulex::setTorque(uint8_t id, uint8_t cmdTorue)
{
    uint8_t txBuf[10];

    txBuf[0] = HEADER;              // Packet Header (0xFF)
    txBuf[1] = HEADER;              // Packet Header (0xFF)
    txBuf[2] = MIN_PACKET_SIZE + 3; // Packet Size
    txBuf[3] = id;                  // Servo ID
    txBuf[4] = CMD_RAM_WRITE;       // Command Ram Write (0x03)
    txBuf[5] = 0;                   // Checksum1
    txBuf[6] = 0;                   // Checksum2
    txBuf[7] = RAM_TORQUE_CONTROL;  // Address 52
    txBuf[8] = BYTE1;               // Length
    txBuf[9] = cmdTorue;            // Torque ON

    // Checksum1 = (PacketSize ^ pID ^ CMD ^ Data[0] ^ Data[1] ^ ... ^ Data[n]) & 0xFE
    // Checksum2 = (~Checksum1)&0xFE
    txBuf[5] = (txBuf[2] ^ txBuf[3] ^ txBuf[4] ^ txBuf[7] ^ txBuf[8] ^ txBuf[9]) & 0xFE;
    txBuf[6] = (~(txBuf[5])) & 0xFE;

    // send packet (mbed -> herkulex)
    txPacket(10, txBuf);
}

//------------------------------------------------------------------------------
void Herkulex::positionControl(uint8_t id, uint16_t position, uint8_t playtime, uint8_t setLED)
{
    if (position > 1023)
        return;
    // if (playtime > 255) return;

    uint8_t txBuf[12];

    txBuf[0] = HEADER;                   // Packet Header (0xFF)
    txBuf[1] = HEADER;                   // Packet Header (0xFF)
    txBuf[2] = MIN_PACKET_SIZE + 5;      // Packet Size
    txBuf[3] = id;                       // pID is total number of servos in the network (0 ~ 253)
    txBuf[4] = CMD_S_JOG;                // Command S JOG (0x06)
    txBuf[5] = 0;                        // Checksum1
    txBuf[6] = 0;                        // Checksum2
    txBuf[7] = playtime;                 // Playtime
    txBuf[8] = position & 0x00FF;        // Position (LSB, Least Significant Bit)
    txBuf[9] = (position & 0xFF00) >> 8; // position (MSB, Most Significanct Bit)
    txBuf[10] = POS_MODE | setLED;       // Pos Mode and LED on/off
    txBuf[11] = id;                      // Servo ID

    // Checksum1 = (PacketSize ^ pID ^ CMD ^ Data[0] ^ Data[1] ^ ... ^ Data[n]) & 0xFE
    // Checksum2 = (~Checksum1)&0xFE

    int checksum1 = 0;
    for (int i = 2; i < 12; i++)
    {
        checksum1 ^= txBuf[i];
    }
    txBuf[5] = checksum1 & 0xFE;
    txBuf[6] = (~checksum1) & 0xFE;

    // send packet (mbed -> herkulex)
    txPacket(12, txBuf);
}

//------------------------------------------------------------------------------
void Herkulex::velocityControl(uint8_t id, int16_t speed, uint8_t setLED)
{
    if (speed > 1023 || speed < -1023)
        return;

    uint8_t txBuf[12];

    txBuf[0] = HEADER;                // Packet Header (0xFF)
    txBuf[1] = HEADER;                // Packet Header (0xFF)
    txBuf[2] = MIN_PACKET_SIZE + 5;   // Packet Size
    txBuf[3] = id;                    // pID is total number of servos in the network (0 ~ 253)
    txBuf[4] = CMD_S_JOG;             // Command S JOG (0x06)
    txBuf[5] = 0;                     // Checksum1
    txBuf[6] = 0;                     // Checksum2
    txBuf[7] = 0;                     // Playtime, unmeaningful in turn mode
    txBuf[8] = speed & 0x00FF;        // Speed (LSB, Least Significant Bit)
    txBuf[9] = (speed & 0xFF00) >> 8; // Speed (MSB, Most Significanct Bit)
    txBuf[10] = TURN_MODE | setLED;   // Turn Mode and LED on/off
    txBuf[11] = id;                   // Servo ID

    // Checksum1 = (PacketSize ^ pID ^ CMD ^ Data[0] ^ Data[1] ^ ... ^ Data[n]) & 0xFE
    // Checksum2 = (~Checksum1)&0xFE
    txBuf[5] = (txBuf[2] ^ txBuf[3] ^ txBuf[4] ^ txBuf[7] ^ txBuf[8] ^ txBuf[9] ^ txBuf[10] ^ txBuf[11]) & 0xFE;
    txBuf[6] = (~(txBuf[5])) & 0xFE;

    // send packet (mbed -> herkulex)
    txPacket(12, txBuf);
}

//------------------------------------------------------------------------------
int8_t Herkulex::getStatus(uint8_t id)
{
    uint8_t status;
    uint8_t rxBuf[9];
    uint8_t txBuf[7];
    uint8_t chksum1;
    uint8_t chksum2;

    txBuf[0] = HEADER;          // Packet Header (HEADER)
    txBuf[1] = HEADER;          // Packet Header (HEADER)
    txBuf[2] = MIN_PACKET_SIZE; // Packet Size
    txBuf[3] = id;              // Servo ID
    txBuf[4] = CMD_STAT;        // Status Error, Status Detail request

    // Check Sum1 and Check Sum2
    txBuf[5] = (txBuf[2] ^ txBuf[3] ^ txBuf[4]) & 0xFE;
    txBuf[6] = (~(txBuf[5])) & 0xFE;

    // send packet (mbed -> herkulex)
    txPacket(7, txBuf);
    ThisThread::sleep_for(1s);
    rxPacket(9, rxBuf);

    // Checksum1
    chksum1 = (rxBuf[2] ^ rxBuf[3] ^ rxBuf[4] ^ rxBuf[7] ^ rxBuf[8]) & 0xFE;
    if (chksum1 != rxBuf[5])
    {
        return -1;
    }

    // Checksum2
    chksum2 = checksum2(chksum1);
    if (chksum2 != rxBuf[6])
    {
        return -1;
    }

    status = rxBuf[7]; // Status Error
    // status = rxBuf[8];  // Status Detail

    return status;
}

//------------------------------------------------------------------------------
int16_t Herkulex::getPos(uint8_t id)
{
    uint16_t position = 0;

    uint8_t txBuf[9];

    txBuf[0] = HEADER;                  // Packet Header (0xFF)
    txBuf[1] = HEADER;                  // Packet Header (0xFF)
    txBuf[2] = MIN_PACKET_SIZE + 2;     // Packet Size
    txBuf[3] = id;                      // Servo ID
    txBuf[4] = CMD_RAM_READ;            // Status Error, Status Detail request
    txBuf[5] = 0;                       // Checksum1
    txBuf[6] = 0;                       // Checksum2
    txBuf[7] = RAM_CALIBRATED_POSITION; // Address 52
    txBuf[8] = BYTE2;                   // Address 52 and 53

    // Check Sum1 and Check Sum2
    txBuf[5] = (txBuf[2] ^ txBuf[3] ^ txBuf[4] ^ txBuf[7] ^ txBuf[8]) & 0xFE;
    txBuf[6] = (~(txBuf[5])) & 0xFE;

    // send packet (mbed -> herkulex)
    txPacket(9, txBuf);

    uint8_t rxBuf[13] = {0};
    rxPacket(13, rxBuf);

    // Checksum1
    uint8_t chksum1 = (rxBuf[2] ^ rxBuf[3] ^ rxBuf[4] ^ rxBuf[7] ^ rxBuf[8] ^ rxBuf[9] ^ rxBuf[10] ^ rxBuf[11] ^ rxBuf[12]) & 0xFE;
    if (chksum1 != rxBuf[5])
    {
        printf(" RX buf 5 : %d\t checsum1 : %d\n", rxBuf[5], chksum1);

        return -1;
    }

    // Checksum2
    uint8_t chksum2 = (~rxBuf[5] & 0xFE);
    if (chksum2 != rxBuf[6])
    {
        printf(" RX buf 6 : %d\t checsum2 : %d\n", rxBuf[6], chksum2);

        return -1;
    }

    position = ((rxBuf[10] & 0x03) << 8) | rxBuf[9];

    return position;
}

//------------------------------------------------------------------------------
void Herkulex::positionControl_Mul_ensemble(uint8_t id, uint16_t position, uint8_t playtime, uint8_t setLED, uint8_t id2, uint16_t position2, uint8_t setLED2)

{
    // if (position > 1023) return; //1002-21
    if (playtime > 254)
        return; // 1-254 == 11.2ms-2.844sec.
    // float tempo = playtime*0.012;
    uint8_t txBuf[16];
    // etat = pos;
    pos_position = position;
    pos_time = playtime;
    pos_led = setLED;
    txBuf[0] = HEADER;              // Packet Header (0xFF)
    txBuf[1] = HEADER;              // Packet Header (0xFF)
    txBuf[2] = MIN_PACKET_SIZE + 9; // Packet Size
    // txBuf[3] = MAX_PID; // pID is total number of servos in the network (0 ~ 253)
    txBuf[3] = 254;                        // broadcast ID
    txBuf[4] = CMD_S_JOG;                  // Command S JOG (0x06)
    txBuf[5] = 0;                          // Checksum1
    txBuf[6] = 0;                          // Checksum2
    txBuf[7] = playtime;                   // Playtime
    txBuf[8] = position & 0x00FF;          // Position (LSB, Least Significant Bit)
    txBuf[9] = (position & 0xFF00) >> 8;   // position (MSB, Most Significanct Bit)
    txBuf[10] = POS_MODE | setLED;         // Pos Mode and LED on/off
    txBuf[11] = id;                        // Servo ID
    txBuf[12] = position2 & 0x00FF;        // Position (LSB, Least Significant Bit)
    txBuf[13] = (position2 & 0xFF00) >> 8; // position (MSB, Most Significanct Bit)
    txBuf[14] = POS_MODE | setLED2;        // Pos Mode and LED on/off
    txBuf[15] = id2;                       // Servo ID
                                           // Checksum1 = (PacketSize ^ pID ^ CMD ^ Data[0] ^ Data[1] ^ ... ^ Data[n]) & 0xFE
                                           // Checksum2 = (~Checksum1)&0xFE
    txBuf[5] = (txBuf[2] ^ txBuf[3] ^ txBuf[4] ^ txBuf[7] ^ txBuf[8] ^ txBuf[9] ^ txBuf[10] ^ txBuf[11] ^ txBuf[12] ^ txBuf[13] ^ txBuf[14] ^ txBuf[15]) & 0xFE;
    txBuf[6] = (~(txBuf[5])) & 0xFE;

    // send packet (mbed -> herkulex)
    txPacket(16, txBuf);
}
//------------------------------------------------------------------------------
void Herkulex::positionControl_Mul_playtime_different(uint8_t id, uint16_t position, uint8_t playtime, uint8_t setLED, uint8_t id2, uint16_t position2, uint8_t playtime2, uint8_t setLED2)
{
    // float tempo=0;

    if (playtime > 254)
        playtime = 254; // return; //1-254 == 11.2ms-2.844sec.
    // if(playtime>playtime2) {
    //     tempo=playtime*0.012;
    // } else if(playtime<playtime2) {
    //     tempo=playtime2*0.012;
    // }
    uint8_t txBuf[17];
    // etat = pos;
    pos_position = position;
    pos_time = playtime;
    pos_led = setLED;
    txBuf[0] = HEADER;              // Packet Header (0xFF)
    txBuf[1] = HEADER;              // Packet Header (0xFF)
    txBuf[2] = MIN_PACKET_SIZE + 9; // Packet Size
    // txBuf[3] = MAX_PID; // pID is total number of servos in the network (0 ~ 253)
    txBuf[3] = 254;                        // broadcast ID
    txBuf[4] = CMD_I_JOG;                  // Command I JOG
    txBuf[5] = 0;                          // Checksum1
    txBuf[6] = 0;                          // Checksum2
    txBuf[7] = position & 0x00FF;          // Position (LSB, Least Significant Bit)
    txBuf[8] = (position & 0xFF00) >> 8;   // position (MSB, Most Significanct Bit)
    txBuf[9] = POS_MODE | setLED;          // Pos Mode and LED on/off
    txBuf[10] = id;                        // Servo ID
    txBuf[11] = playtime;                  // Playtime
    txBuf[12] = position2 & 0x00FF;        // Position (LSB, Least Significant Bit)
    txBuf[13] = (position2 & 0xFF00) >> 8; // position (MSB, Most Significanct Bit)
    txBuf[14] = POS_MODE | setLED2;        // Pos Mode and LED on/off
    txBuf[15] = id2;                       // Servo ID
    txBuf[16] = playtime2;                 // Playtime
                                           // Checksum1 = (PacketSize ^ pID ^ CMD ^ Data[0] ^ Data[1] ^ ... ^ Data[n]) & 0xFE
                                           // Checksum2 = (~Checksum1)&0xFE
    txBuf[5] = (txBuf[2] ^ txBuf[3] ^ txBuf[4] ^ txBuf[7] ^ txBuf[8] ^ txBuf[9] ^ txBuf[10] ^ txBuf[11] ^ txBuf[12] ^ txBuf[13] ^ txBuf[14] ^ txBuf[15]) & 0xFE;
    txBuf[6] = (~(txBuf[5])) & 0xFE;

    // send packet (mbed -> herkulex)
    txPacket(17, txBuf);
    // ThisThread::sleep_for(tempo);
}

//------------------------------------------------------------------------------
int32_t Herkulex::checksum2(int XOR)
{
    return (~XOR) & 0xFE;
}