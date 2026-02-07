#pragma once

#include <lvgl.h>

// Touch pin definitions - ESP32-C6-Touch-LCD-1.47-M
#define PIN_TOUCH_SDA 18
#define PIN_TOUCH_SCL 19
#define PIN_TOUCH_RST 20
#define PIN_TOUCH_INT 21

void touch_init(uint16_t rotation, uint16_t width, uint16_t height);
