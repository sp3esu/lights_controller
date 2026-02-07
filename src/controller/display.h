#pragma once

#include <Arduino.h>
#include <lvgl.h>
#include <Arduino_GFX_Library.h>

// Native panel dimensions (portrait, used by GFX driver constructor)
#define DISP_NATIVE_W 172
#define DISP_NATIVE_H 320

// Post-rotation dimensions (landscape, used by LVGL and UI)
#define DISP_WIDTH  320
#define DISP_HEIGHT 172

// Pin definitions - ESP32-C6-Touch-LCD-1.47-M (touch version)
#define PIN_LCD_DC   15
#define PIN_LCD_CS   14
#define PIN_LCD_SCK   1
#define PIN_LCD_MOSI  2
#define PIN_LCD_RST  22
#define PIN_LCD_BL   23

void display_init();
Arduino_GFX *display_get_gfx();
