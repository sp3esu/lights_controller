#include "espnow_rx.h"
#include "protocol.h"
#include "lights.h"
#include <Arduino.h>
#include <WiFi.h>
#include <esp_now.h>
#include <Preferences.h>

static uint16_t seq_num = 0;
static uint8_t controller_mac[6] = {0};
static bool paired = false;
static bool pairing_mode = false;

static uint32_t last_heartbeat_sent = 0;
static uint32_t last_cmd_time = 0;

static light_command_callback_t cmd_cb = nullptr;
static Preferences prefs;

static void send_ack(const uint8_t *dest, uint16_t ack_seq, uint8_t light_state, AckStatus status) {
    LightAck ack = make_light_ack(ack_seq, light_state, status);
    esp_now_send(dest, (uint8_t *)&ack, sizeof(ack));
}

static void send_heartbeat(uint8_t light_state) {
    if (!paired) return;
    Heartbeat hb = make_heartbeat(++seq_num, light_state);
    esp_now_send(controller_mac, (uint8_t *)&hb, sizeof(hb));
}

// IDF 5.x callback signature with esp_now_recv_info_t
static void on_data_recv(const esp_now_recv_info_t *info, const uint8_t *data, int len) {
    const uint8_t *mac = info->src_addr;
    if (len < (int)sizeof(MsgHeader)) return;

    const MsgHeader *hdr = (const MsgHeader *)data;
    if (hdr->version != PROTOCOL_VERSION) return;

    switch (hdr->msg_type) {
        case MSG_LIGHT_COMMAND: {
            if (len < (int)sizeof(LightCommand)) return;
            // Only accept from paired controller
            if (paired && memcmp(mac, controller_mac, 6) != 0) return;

            const LightCommand *cmd = (const LightCommand *)data;
            last_cmd_time = millis();

            if (cmd_cb) {
                cmd_cb(cmd->light_mask, cmd->light_state);
            }

            // Send ACK with current state
            send_ack(mac, cmd->header.seq_num, lights_get_state(), ACK_OK);
            break;
        }
        case MSG_PAIR_REQUEST: {
            if (!pairing_mode) return;
            if (len < (int)sizeof(PairRequest)) return;

            const PairRequest *req = (const PairRequest *)data;
            memcpy(controller_mac, req->controller_mac, 6);

            // Save to NVS
            prefs.begin("espnow", false);
            prefs.putBytes("ctrl_mac", controller_mac, 6);
            prefs.putBool("paired", true);
            prefs.end();

            // Add as ESP-NOW peer
            esp_now_peer_info_t peer_info = {};
            memcpy(peer_info.peer_addr, controller_mac, 6);
            peer_info.channel = 0;
            peer_info.encrypt = false;
            esp_now_add_peer(&peer_info);

            // Send pair response
            uint8_t my_mac[6];
            WiFi.macAddress(my_mac);
            PairResponse resp = make_pair_response(req->header.seq_num, my_mac);
            esp_now_send(controller_mac, (uint8_t *)&resp, sizeof(resp));

            paired = true;
            pairing_mode = false;
            Serial.printf("Paired with controller: %02X:%02X:%02X:%02X:%02X:%02X\n",
                controller_mac[0], controller_mac[1], controller_mac[2],
                controller_mac[3], controller_mac[4], controller_mac[5]);
            break;
        }
    }
}

void espnow_rx_init() {
    WiFi.mode(WIFI_STA);
    WiFi.disconnect();

    if (esp_now_init() != ESP_OK) {
        Serial.println("ESP-NOW init failed");
        return;
    }

    esp_now_register_recv_cb(on_data_recv);

    // Load stored controller MAC
    prefs.begin("espnow", true);
    paired = prefs.getBool("paired", false);
    if (paired) {
        prefs.getBytes("ctrl_mac", controller_mac, 6);
        prefs.end();

        // Add controller as peer
        esp_now_peer_info_t peer_info = {};
        memcpy(peer_info.peer_addr, controller_mac, 6);
        peer_info.channel = 0;
        peer_info.encrypt = false;
        esp_now_add_peer(&peer_info);

        Serial.printf("Loaded controller: %02X:%02X:%02X:%02X:%02X:%02X\n",
            controller_mac[0], controller_mac[1], controller_mac[2],
            controller_mac[3], controller_mac[4], controller_mac[5]);
    } else {
        prefs.end();
    }

    last_cmd_time = millis();
}

void espnow_rx_set_command_callback(light_command_callback_t cb) {
    cmd_cb = cb;
}

void espnow_rx_update(uint8_t current_light_state) {
    uint32_t now = millis();

    // Send heartbeat every 2s
    if (paired && (now - last_heartbeat_sent >= HEARTBEAT_INTERVAL_MS)) {
        last_heartbeat_sent = now;
        send_heartbeat(current_light_state);
    }
}

bool espnow_rx_is_paired() {
    return paired;
}

void espnow_rx_enter_pairing_mode() {
    pairing_mode = true;
    Serial.println("Entering pairing mode...");
}

uint32_t espnow_rx_last_command_time() {
    return last_cmd_time;
}
