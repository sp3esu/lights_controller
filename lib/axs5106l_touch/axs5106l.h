#pragma once

#include <Arduino.h>
#include <Wire.h>

#define AXS_MAX_TOUCH_POINTS 5
#define AXS5106L_ADDR        0x63
#define AXS5106L_ID_REG      0x08
#define AXS5106L_TOUCH_REG   0x01

struct TouchPoint {
    uint16_t x;
    uint16_t y;
};

struct TouchData {
    TouchPoint points[AXS_MAX_TOUCH_POINTS];
    uint8_t    count;
};

class AXS5106L {
public:
    AXS5106L() = default;

    // Initialize touch controller
    // rotation: 0-3 matching display rotation
    void begin(TwoWire &wire, int sda, int scl, int rst, int intr,
               uint16_t rotation, uint16_t width, uint16_t height);

    // Poll for new touch data (call before read)
    void update();

    // Get touch coordinates (returns true if touching)
    bool getPoint(TouchData &data);

private:
    TwoWire *_wire = nullptr;
    uint16_t _width = 0;
    uint16_t _height = 0;
    uint16_t _rotation = 0;
    volatile bool _intFlag = false;
    TouchData _raw;

    bool i2cRead(uint8_t reg, uint8_t *buf, uint32_t len);
    static void IRAM_ATTR intHandler();
    static AXS5106L *_instance;
};
