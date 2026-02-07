#include "espnow_tx.h"
#include "protocol.h"
#include <Arduino.h>
#include <WiFi.h>
#include <esp_now.h>
#include <Preferences.h>

static uint16_t seq_num = 0;
static uint8_t peer_mac[6] = {0};
static bool peer_set = false;
static bool paired = false;

// Pending command state for retry logic
static bool cmd_pending = false;
static LightCommand pending_cmd;
static uint32_t cmd_sent_time = 0;
static uint8_t cmd_retries = 0;

// Optimistic state tracking
static uint8_t desired_state = 0;
static uint8_t confirmed_state = 0;

// Connection tracking
static uint32_t last_heartbeat_time = 0;
static bool connected = false;

// Callbacks
static ack_callback_t ack_cb = nullptr;
static connection_callback_t conn_cb = nullptr;

// NVS storage
static Preferences prefs;

// ESP32-C6 uses IDF 5.x with esp_now_recv_info_t callback signature
static void on_data_recv(const esp_now_recv_info_t *info, const uint8_t *data, int len) {
    if (len < (int)sizeof(MsgHeader)) return;

    const MsgHeader *hdr = (const MsgHeader *)data;
    if (hdr->version != PROTOCOL_VERSION) return;

    switch (hdr->msg_type) {
        case MSG_LIGHT_ACK: {
            if (len < (int)sizeof(LightAck)) return;
            const LightAck *ack = (const LightAck *)data;
            if (ack->header.seq_num == pending_cmd.header.seq_num) {
                cmd_pending = false;
            }
            confirmed_state = ack->light_state;
            desired_state = confirmed_state;
            last_heartbeat_time = millis();
            if (!connected) {
                connected = true;
                if (conn_cb) conn_cb(true);
            }
            if (ack_cb) ack_cb(confirmed_state);
            break;
        }
        case MSG_HEARTBEAT: {
            if (len < (int)sizeof(Heartbeat)) return;
            const Heartbeat *hb = (const Heartbeat *)data;
            confirmed_state = hb->light_state;
            last_heartbeat_time = millis();
            if (!connected) {
                connected = true;
                if (conn_cb) conn_cb(true);
            }
            if (ack_cb) ack_cb(confirmed_state);
            break;
        }
        case MSG_STATE_REPORT: {
            if (len < (int)sizeof(StateReport)) return;
            const StateReport *sr = (const StateReport *)data;
            confirmed_state = sr->light_state;
            desired_state = confirmed_state;
            last_heartbeat_time = millis();
            if (!connected) {
                connected = true;
                if (conn_cb) conn_cb(true);
            }
            if (ack_cb) ack_cb(confirmed_state);
            break;
        }
        case MSG_PAIR_RESPONSE: {
            if (len < (int)sizeof(PairResponse)) return;
            const PairResponse *resp = (const PairResponse *)data;
            memcpy(peer_mac, resp->receiver_mac, 6);
            // Save to NVS
            prefs.begin("espnow", false);
            prefs.putBytes("peer_mac", peer_mac, 6);
            prefs.putBool("paired", true);
            prefs.end();
            // Add as peer
            espnow_tx_set_peer(peer_mac);
            paired = true;
            Serial.printf("Paired with: %02X:%02X:%02X:%02X:%02X:%02X\n",
                peer_mac[0], peer_mac[1], peer_mac[2],
                peer_mac[3], peer_mac[4], peer_mac[5]);
            break;
        }
    }
}

void espnow_tx_init() {
    WiFi.mode(WIFI_STA);
    WiFi.disconnect();

    if (esp_now_init() != ESP_OK) {
        Serial.println("ESP-NOW init failed");
        return;
    }

    esp_now_register_recv_cb(on_data_recv);

    // Load stored peer MAC
    prefs.begin("espnow", true);
    paired = prefs.getBool("paired", false);
    if (paired) {
        prefs.getBytes("peer_mac", peer_mac, 6);
        prefs.end();
        espnow_tx_set_peer(peer_mac);
        Serial.printf("Loaded peer: %02X:%02X:%02X:%02X:%02X:%02X\n",
            peer_mac[0], peer_mac[1], peer_mac[2],
            peer_mac[3], peer_mac[4], peer_mac[5]);
    } else {
        prefs.end();
    }

    last_heartbeat_time = millis();
}

void espnow_tx_set_peer(const uint8_t *mac) {
    // Remove old peer if exists
    if (peer_set) {
        esp_now_del_peer(peer_mac);
    }

    memcpy(peer_mac, mac, 6);

    esp_now_peer_info_t peer_info = {};
    memcpy(peer_info.peer_addr, mac, 6);
    peer_info.channel = 0;
    peer_info.encrypt = false;

    if (esp_now_add_peer(&peer_info) != ESP_OK) {
        Serial.println("Failed to add peer");
        return;
    }
    peer_set = true;
}

void espnow_tx_set_ack_callback(ack_callback_t cb) {
    ack_cb = cb;
}

void espnow_tx_set_connection_callback(connection_callback_t cb) {
    conn_cb = cb;
}

void espnow_tx_toggle_light(uint8_t light_bit) {
    desired_state ^= light_bit;
    espnow_tx_send_state(light_bit, desired_state & light_bit);
}

void espnow_tx_send_state(uint8_t mask, uint8_t state) {
    if (!peer_set) return;

    pending_cmd = make_light_command(++seq_num, mask, state);
    cmd_pending = true;
    cmd_retries = 0;
    cmd_sent_time = millis();

    esp_now_send(peer_mac, (uint8_t *)&pending_cmd, sizeof(pending_cmd));
}

void espnow_tx_update() {
    uint32_t now = millis();

    // Retry logic
    if (cmd_pending && (now - cmd_sent_time >= ACK_TIMEOUT_MS)) {
        if (cmd_retries < ACK_MAX_RETRIES) {
            cmd_retries++;
            cmd_sent_time = now;
            esp_now_send(peer_mac, (uint8_t *)&pending_cmd, sizeof(pending_cmd));
        } else {
            // Give up, revert to confirmed state
            cmd_pending = false;
            desired_state = confirmed_state;
            if (ack_cb) ack_cb(confirmed_state);
        }
    }

    // Heartbeat timeout check
    if (connected && (now - last_heartbeat_time >= HEARTBEAT_TIMEOUT_MS)) {
        connected = false;
        if (conn_cb) conn_cb(false);
    }
}

bool espnow_tx_is_connected() {
    return connected;
}

uint8_t espnow_tx_get_confirmed_state() {
    return confirmed_state;
}

void espnow_tx_get_mac(uint8_t *mac) {
    WiFi.macAddress(mac);
}

void espnow_tx_start_pairing() {
    // Add broadcast peer for pairing
    esp_now_peer_info_t bcast = {};
    memcpy(bcast.peer_addr, BROADCAST_ADDR, 6);
    bcast.channel = 0;
    bcast.encrypt = false;
    esp_now_add_peer(&bcast);

    uint8_t mac[6];
    WiFi.macAddress(mac);
    PairRequest req = make_pair_request(++seq_num, mac);
    esp_now_send(BROADCAST_ADDR, (uint8_t *)&req, sizeof(req));

    Serial.println("Pairing request sent (broadcast)");
}

bool espnow_tx_is_paired() {
    return paired;
}
