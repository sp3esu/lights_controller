#pragma once

#include <cstdint>

// Callback types for UI integration
typedef void (*ack_callback_t)(uint8_t light_state);
typedef void (*connection_callback_t)(bool connected);

void espnow_tx_init();
void espnow_tx_set_peer(const uint8_t *mac);
void espnow_tx_set_ack_callback(ack_callback_t cb);
void espnow_tx_set_connection_callback(connection_callback_t cb);

// Send a toggle command for a specific light bit
void espnow_tx_toggle_light(uint8_t light_bit);

// Send current desired state
void espnow_tx_send_state(uint8_t mask, uint8_t state);

// Call from loop() to handle retries and heartbeat timeout
void espnow_tx_update();

// Check connection status
bool espnow_tx_is_connected();

// Get last confirmed light state from receiver
uint8_t espnow_tx_get_confirmed_state();

// Get own MAC address
void espnow_tx_get_mac(uint8_t *mac);

// Pairing
void espnow_tx_start_pairing();
bool espnow_tx_is_paired();
