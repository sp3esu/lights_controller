#pragma once

#include <cstdint>

// GPIO assignments for light outputs
#define PIN_FOG       16
#define PIN_LOW_BEAM  17
#define PIN_HIGH_BEAM 18
#define PIN_LIGHT_BAR 19
#define PIN_HAZARD    21
#define PIN_STATUS_LED 2

void lights_init();

// Set individual light by bitmask
void lights_set(uint8_t mask, uint8_t state);

// Set all lights from bitmask
void lights_set_all(uint8_t state);

// Get current light state bitmask
uint8_t lights_get_state();

// All lights off (failsafe)
void lights_all_off();
