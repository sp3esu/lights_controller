#pragma once

#include <cstdint>
#include <cstring>

// Protocol version
#define PROTOCOL_VERSION 1

// Light bit positions
#define LIGHT_FOG      (1 << 0)
#define LIGHT_LOW_BEAM (1 << 1)
#define LIGHT_HIGH_BEAM (1 << 2)
#define LIGHT_BAR      (1 << 3)
#define LIGHT_HAZARD   (1 << 4)
#define LIGHT_ALL      (LIGHT_FOG | LIGHT_LOW_BEAM | LIGHT_HIGH_BEAM | LIGHT_BAR | LIGHT_HAZARD)

// Message types
enum MsgType : uint8_t {
    MSG_LIGHT_COMMAND  = 0x01,  // TX -> RX: set light state
    MSG_LIGHT_ACK      = 0x02,  // RX -> TX: confirm state
    MSG_HEARTBEAT      = 0x03,  // RX -> TX: keep-alive
    MSG_STATE_REPORT   = 0x04,  // RX -> TX: full state + uptime
    MSG_PAIR_REQUEST   = 0x10,  // TX -> RX: broadcast pairing request
    MSG_PAIR_RESPONSE  = 0x11,  // RX -> TX: pairing response with MAC
};

// ACK status codes
enum AckStatus : uint8_t {
    ACK_OK             = 0x00,
    ACK_ERR_INVALID    = 0x01,
    ACK_ERR_VERSION    = 0x02,
};

// Common message header
struct __attribute__((packed)) MsgHeader {
    uint8_t  version;
    uint8_t  msg_type;
    uint16_t seq_num;
};

// TX -> RX: Light command
struct __attribute__((packed)) LightCommand {
    MsgHeader header;
    uint8_t   light_mask;   // which lights to affect (bitmask)
    uint8_t   light_state;  // desired state for masked lights
};

// RX -> TX: Acknowledge command
struct __attribute__((packed)) LightAck {
    MsgHeader header;
    uint8_t   light_state;  // confirmed state of ALL lights
    uint8_t   status;       // AckStatus
};

// RX -> TX: Heartbeat (every 2s)
struct __attribute__((packed)) Heartbeat {
    MsgHeader header;
    uint8_t   light_state;  // current state of all lights
};

// RX -> TX: Full state report
struct __attribute__((packed)) StateReport {
    MsgHeader header;
    uint8_t   light_state;
    uint32_t  uptime_ms;
};

// TX -> RX: Pairing request (broadcast)
struct __attribute__((packed)) PairRequest {
    MsgHeader header;
    uint8_t   controller_mac[6];
};

// RX -> TX: Pairing response
struct __attribute__((packed)) PairResponse {
    MsgHeader header;
    uint8_t   receiver_mac[6];
};

// Union for receiving any message
union __attribute__((packed)) ProtoMessage {
    MsgHeader    header;
    LightCommand light_cmd;
    LightAck     light_ack;
    Heartbeat    heartbeat;
    StateReport  state_report;
    PairRequest  pair_req;
    PairResponse pair_resp;
    uint8_t      raw[32];
};

// Timing constants
#define ACK_TIMEOUT_MS       200
#define ACK_MAX_RETRIES      3
#define HEARTBEAT_INTERVAL_MS 2000
#define HEARTBEAT_TIMEOUT_MS  6000
#define FAILSAFE_TIMEOUT_MS   30000

// ESP-NOW broadcast address
static const uint8_t BROADCAST_ADDR[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

// Helper: build a LightCommand
inline LightCommand make_light_command(uint16_t seq, uint8_t mask, uint8_t state) {
    LightCommand cmd;
    cmd.header.version  = PROTOCOL_VERSION;
    cmd.header.msg_type = MSG_LIGHT_COMMAND;
    cmd.header.seq_num  = seq;
    cmd.light_mask      = mask;
    cmd.light_state     = state;
    return cmd;
}

// Helper: build a LightAck
inline LightAck make_light_ack(uint16_t seq, uint8_t light_state, AckStatus status) {
    LightAck ack;
    ack.header.version  = PROTOCOL_VERSION;
    ack.header.msg_type = MSG_LIGHT_ACK;
    ack.header.seq_num  = seq;
    ack.light_state     = light_state;
    ack.status          = status;
    return ack;
}

// Helper: build a Heartbeat
inline Heartbeat make_heartbeat(uint16_t seq, uint8_t light_state) {
    Heartbeat hb;
    hb.header.version  = PROTOCOL_VERSION;
    hb.header.msg_type = MSG_HEARTBEAT;
    hb.header.seq_num  = seq;
    hb.light_state     = light_state;
    return hb;
}

// Helper: build a PairRequest
inline PairRequest make_pair_request(uint16_t seq, const uint8_t* mac) {
    PairRequest req;
    req.header.version  = PROTOCOL_VERSION;
    req.header.msg_type = MSG_PAIR_REQUEST;
    req.header.seq_num  = seq;
    memcpy(req.controller_mac, mac, 6);
    return req;
}

// Helper: build a PairResponse
inline PairResponse make_pair_response(uint16_t seq, const uint8_t* mac) {
    PairResponse resp;
    resp.header.version  = PROTOCOL_VERSION;
    resp.header.msg_type = MSG_PAIR_RESPONSE;
    resp.header.seq_num  = seq;
    memcpy(resp.receiver_mac, mac, 6);
    return resp;
}
