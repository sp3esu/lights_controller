#include "lights.h"
#include "protocol.h"
#include <Arduino.h>

static uint8_t current_state = 0;

// Map from light bit to GPIO pin
static const struct {
    uint8_t bit;
    uint8_t pin;
} light_map[] = {
    { LIGHT_FOG,       PIN_FOG },
    { LIGHT_LOW_BEAM,  PIN_LOW_BEAM },
    { LIGHT_HIGH_BEAM, PIN_HIGH_BEAM },
    { LIGHT_BAR,       PIN_LIGHT_BAR },
};

void lights_init() {
    for (auto &l : light_map) {
        pinMode(l.pin, OUTPUT);
        digitalWrite(l.pin, LOW);
    }
    pinMode(PIN_STATUS_LED, OUTPUT);
    current_state = 0;
}

void lights_set(uint8_t mask, uint8_t state) {
    // Apply only the masked bits
    current_state = (current_state & ~mask) | (state & mask);
    lights_set_all(current_state);
}

void lights_set_all(uint8_t state) {
    current_state = state;
    for (auto &l : light_map) {
        digitalWrite(l.pin, (current_state & l.bit) ? HIGH : LOW);
    }
}

uint8_t lights_get_state() {
    return current_state;
}

void lights_all_off() {
    lights_set_all(0);
}
