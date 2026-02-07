#include "axs5106l.h"

AXS5106L *AXS5106L::_instance = nullptr;

void IRAM_ATTR AXS5106L::intHandler() {
    if (_instance) _instance->_intFlag = true;
}

void AXS5106L::begin(TwoWire &wire, int sda, int scl, int rst, int intr,
                      uint16_t rotation, uint16_t width, uint16_t height) {
    _wire     = &wire;
    _width    = width;
    _height   = height;
    _rotation = rotation;
    _instance = this;

    _wire->begin(sda, scl);

    // Reset touch controller
    pinMode(rst, OUTPUT);
    digitalWrite(rst, LOW);
    delay(200);
    digitalWrite(rst, HIGH);
    delay(300);

    // Attach interrupt
    attachInterrupt(digitalPinToInterrupt(intr), intHandler, FALLING);

    // Verify chip presence
    uint8_t id[3] = {0};
    i2cRead(AXS5106L_ID_REG, id, 3);
    if (id[0] != 0) {
        Serial.printf("AXS5106L ID: %02X %02X %02X\n", id[0], id[1], id[2]);
    }
}

void AXS5106L::update() {
    _raw.count = 0;

    if (!_intFlag) return;
    _intFlag = false;

    uint8_t data[14] = {0};
    i2cRead(AXS5106L_TOUCH_REG, data, 14);

    _raw.count = data[1];
    if (_raw.count == 0) return;
    if (_raw.count > AXS_MAX_TOUCH_POINTS) _raw.count = AXS_MAX_TOUCH_POINTS;

    for (uint8_t i = 0; i < _raw.count; i++) {
        _raw.points[i].x = ((uint16_t)(data[2 + i * 6] & 0x0F)) << 8 | data[3 + i * 6];
        _raw.points[i].y = ((uint16_t)(data[4 + i * 6] & 0x0F)) << 8 | data[5 + i * 6];
    }
}

bool AXS5106L::getPoint(TouchData &data) {
    if (_raw.count == 0) return false;

    data.count = _raw.count;
    for (uint8_t i = 0; i < _raw.count; i++) {
        switch (_rotation) {
            case 1:
                data.points[i].y = _raw.points[i].x;
                data.points[i].x = _raw.points[i].y;
                break;
            case 2:
                data.points[i].x = _raw.points[i].x;
                data.points[i].y = _height - 1 - _raw.points[i].y;
                break;
            case 3:
                data.points[i].y = _height - 1 - _raw.points[i].x;
                data.points[i].x = _width - 1 - _raw.points[i].y;
                break;
            default: // rotation 0
                data.points[i].x = _width - 1 - _raw.points[i].x;
                data.points[i].y = _raw.points[i].y;
                break;
        }
    }
    return true;
}

bool AXS5106L::i2cRead(uint8_t reg, uint8_t *buf, uint32_t len) {
    _wire->beginTransmission(AXS5106L_ADDR);
    _wire->write(reg);
    if (_wire->endTransmission() != 0) return false;

    _wire->requestFrom((uint8_t)AXS5106L_ADDR, (uint8_t)len);
    if ((uint32_t)_wire->available() != len) return false;
    _wire->readBytes(buf, len);
    return true;
}
