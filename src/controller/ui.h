#pragma once

#include <cstdint>

void ui_init();
void ui_set_test_mode(bool enabled);

// Update light button states from confirmed receiver state
void ui_set_light_state(uint8_t state);

// Update connection status display
void ui_set_connection_status(bool connected);

// Show pairing screen
void ui_show_pairing();

// Show main control screen
void ui_show_main();
