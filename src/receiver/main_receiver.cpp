#include <Arduino.h>
#include "lights.h"
#include "espnow_rx.h"
#include "protocol.h"

#define PIN_BOOT_BTN 0  // BOOT button for pairing mode

static bool failsafe_triggered = false;

static void on_light_command(uint8_t mask, uint8_t state) {
    lights_set(mask, state);
    failsafe_triggered = false;

    // Blink status LED
    digitalWrite(PIN_STATUS_LED, HIGH);
    delay(10);
    digitalWrite(PIN_STATUS_LED, LOW);
}

void setup() {
    Serial.begin(115200);
    delay(100);
    Serial.println("RC Light Controller - RX");

    lights_init();
    espnow_rx_init();
    espnow_rx_set_command_callback(on_light_command);

    // Check if BOOT button held during startup -> pairing mode
    pinMode(PIN_BOOT_BTN, INPUT_PULLUP);
    delay(100);
    if (digitalRead(PIN_BOOT_BTN) == LOW) {
        Serial.println("BOOT button held - entering pairing mode");
        espnow_rx_enter_pairing_mode();

        // Flash status LED to indicate pairing mode
        for (int i = 0; i < 6; i++) {
            digitalWrite(PIN_STATUS_LED, !digitalRead(PIN_STATUS_LED));
            delay(200);
        }
    }

    if (espnow_rx_is_paired()) {
        Serial.println("Paired and ready");
        digitalWrite(PIN_STATUS_LED, HIGH);
        delay(500);
        digitalWrite(PIN_STATUS_LED, LOW);
    } else {
        Serial.println("Not paired - hold BOOT button during startup to pair");
    }

    Serial.println("Setup complete");
}

void loop() {
    // Send heartbeats
    espnow_rx_update(lights_get_state());

    // Failsafe: turn off all lights if no command for FAILSAFE_TIMEOUT_MS
    if (!failsafe_triggered) {
        uint32_t elapsed = millis() - espnow_rx_last_command_time();
        if (elapsed >= FAILSAFE_TIMEOUT_MS && lights_get_state() != 0) {
            Serial.println("Failsafe: no commands received, lights off");
            lights_all_off();
            failsafe_triggered = true;
        }
    }

    delay(10);
}
