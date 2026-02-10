#include "lights.h"
#include "protocol.h"
#include <Arduino.h>

static uint8_t current_levels[NUM_LIGHT_CHANNELS] = {0};

// Map from channel index to GPIO pin
static const uint8_t light_pins[NUM_LIGHT_CHANNELS] = {
    PIN_FOG, PIN_LOW_BEAM, PIN_HIGH_BEAM, PIN_LIGHT_BAR, PIN_HAZARD
};

// Map from channel index to protocol bitmask bit
static const uint8_t light_bits[NUM_LIGHT_CHANNELS] = {
    LIGHT_FOG, LIGHT_LOW_BEAM, LIGHT_HIGH_BEAM, LIGHT_BAR, LIGHT_HAZARD
};

// Convert a protocol bitmask bit to channel index, returns -1 if not found
static int bit_to_index(uint8_t bit) {
    for (int i = 0; i < NUM_LIGHT_CHANNELS; i++) {
        if (light_bits[i] == bit) return i;
    }
    return -1;
}

void lights_init() {
    for (int i = 0; i < NUM_LIGHT_CHANNELS; i++) {
        ledcAttach(light_pins[i], LIGHT_PWM_FREQ, LIGHT_PWM_RESOLUTION);
        ledcWrite(light_pins[i], 0);
        current_levels[i] = 0;
    }
    pinMode(PIN_STATUS_LED, OUTPUT);
}

void lights_set(uint8_t mask, uint8_t state) {
    for (int i = 0; i < NUM_LIGHT_CHANNELS; i++) {
        if (mask & light_bits[i]) {
            current_levels[i] = (state & light_bits[i]) ? 255 : 0;
            ledcWrite(light_pins[i], current_levels[i]);
        }
    }
}

void lights_set_all(uint8_t state) {
    for (int i = 0; i < NUM_LIGHT_CHANNELS; i++) {
        current_levels[i] = (state & light_bits[i]) ? 255 : 0;
        ledcWrite(light_pins[i], current_levels[i]);
    }
}

uint8_t lights_get_state() {
    uint8_t state = 0;
    for (int i = 0; i < NUM_LIGHT_CHANNELS; i++) {
        if (current_levels[i] > 0) {
            state |= light_bits[i];
        }
    }
    return state;
}

void lights_all_off() {
    for (int i = 0; i < NUM_LIGHT_CHANNELS; i++) {
        current_levels[i] = 0;
        ledcWrite(light_pins[i], 0);
    }
}

void lights_set_level(uint8_t light_bit, uint8_t level) {
    int idx = bit_to_index(light_bit);
    if (idx < 0) return;
    current_levels[idx] = level;
    ledcWrite(light_pins[idx], level);
}

void lights_set_levels(const uint8_t *levels) {
    for (int i = 0; i < NUM_LIGHT_CHANNELS; i++) {
        current_levels[i] = levels[i];
        ledcWrite(light_pins[i], levels[i]);
    }
}

const uint8_t* lights_get_levels() {
    return current_levels;
}
