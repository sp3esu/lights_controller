#pragma once

#include <cstdint>

// GPIO assignments for light outputs
#define PIN_FOG       16
#define PIN_LOW_BEAM  17
#define PIN_HIGH_BEAM 18
#define PIN_LIGHT_BAR 19
#define PIN_HAZARD    21
#define PIN_STATUS_LED 2

// PWM configuration
#define LIGHT_PWM_FREQ       5000  // 5kHz — no visible flicker
#define LIGHT_PWM_RESOLUTION    8  // 8-bit (0-255)

// Channel index constants
#define NUM_LIGHT_CHANNELS 5
#define LIGHT_IDX_FOG       0
#define LIGHT_IDX_LOW_BEAM  1
#define LIGHT_IDX_HIGH_BEAM 2
#define LIGHT_IDX_BAR       3
#define LIGHT_IDX_HAZARD    4

void lights_init();

// Set individual light by bitmask (on/off, backward-compatible)
void lights_set(uint8_t mask, uint8_t state);

// Set all lights from bitmask (on/off, backward-compatible)
void lights_set_all(uint8_t state);

// Get current light state bitmask (level > 0 = bit set)
uint8_t lights_get_state();

// All lights off (failsafe)
void lights_all_off();

// Set a single light to an arbitrary brightness (0-255)
void lights_set_level(uint8_t light_bit, uint8_t level);

// Set all 5 channels from an array of levels
void lights_set_levels(const uint8_t *levels);

// Get current brightness levels array (NUM_LIGHT_CHANNELS elements)
const uint8_t* lights_get_levels();
