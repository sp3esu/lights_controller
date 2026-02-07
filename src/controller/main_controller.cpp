#include <Arduino.h>
#include <FastLED.h>
#include "display.h"
#include "touch.h"
#include "ui.h"
#include "espnow_tx.h"

// WS2812 NeoPixel on GPIO8
#define PIN_NEOPIXEL 8
#define NUM_LEDS     1
static CRGB leds[NUM_LEDS];

// Pairing retry timer
static uint32_t last_pair_attempt = 0;
#define PAIR_RETRY_INTERVAL_MS 3000

static void on_ack(uint8_t light_state) {
    ui_set_light_state(light_state);
}

static void on_connection_change(bool connected) {
    ui_set_connection_status(connected);
    // Update NeoPixel
    leds[0] = connected ? CRGB::Green : CRGB::Red;
    FastLED.show();
}

void setup() {
    Serial.begin(115200);
    delay(100);
    Serial.println("RC Light Controller - TX");

    // Init NeoPixel
    FastLED.addLeds<WS2812, PIN_NEOPIXEL, GRB>(leds, NUM_LEDS);
    FastLED.setBrightness(20);
    leds[0] = CRGB::Blue;
    FastLED.show();

    // Init display + LVGL
    display_init();

    // Init touch input
    Arduino_GFX *gfx = display_get_gfx();
    touch_init(gfx->getRotation(), gfx->width(), gfx->height());

    // Init UI
    ui_init();

    // Init ESP-NOW
    espnow_tx_init();
    espnow_tx_set_ack_callback(on_ack);
    espnow_tx_set_connection_callback(on_connection_change);

    // Show appropriate screen
    if (espnow_tx_is_paired()) {
        ui_show_main();
        leds[0] = CRGB::Red;  // disconnected until first heartbeat
    } else {
        // No receiver paired - run in test mode so UI is usable
        ui_set_test_mode(true);
        ui_show_main();
        leds[0] = CRGB::Purple;
    }
    FastLED.show();

    Serial.println("Setup complete");
}

void loop() {
    // LVGL task handler
    lv_timer_handler();

    // ESP-NOW update (retries, heartbeat timeout)
    espnow_tx_update();

    // Once paired at runtime, switch from test mode to main
    if (espnow_tx_is_paired()) {
        static bool switched = false;
        if (!switched) {
            switched = true;
            ui_set_test_mode(false);
            ui_show_main();
        }
    }

    delay(5);
}
