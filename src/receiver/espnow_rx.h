#pragma once

#include <cstdint>

// Callback when a valid light command is received
typedef void (*light_command_callback_t)(uint8_t light_mask, uint8_t light_state);

void espnow_rx_init();
void espnow_rx_set_command_callback(light_command_callback_t cb);

// Call from loop() to send heartbeats
void espnow_rx_update(uint8_t current_light_state);

// Pairing
bool espnow_rx_is_paired();
void espnow_rx_enter_pairing_mode();

// Connection tracking
uint32_t espnow_rx_last_command_time();
