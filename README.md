# RC Light Controller

Wireless light controller for RC cars and trucks. A touchscreen handheld remote (TX) communicates over ESP-NOW with a receiver (RX) mounted on the vehicle to control multiple light outputs in real time.

## Translations

- [Polski (PL)](docs/README_PL.md)
- [Deutsch (DE)](docs/README_DE.md)
- [Francais (FR)](docs/README_FR.md)
- [Русский (RU)](docs/README_RU.md)
- [Українська (UA)](docs/README_UA.md)

## Features

- **5 independent light channels**: low beam, high beam, fog lights, light bar, hazard lights
- **Touchscreen UI**: 2x3 button grid on a 1.47" color display with LVGL
- **ESP-NOW wireless**: low-latency, connectionless protocol — no WiFi router needed
- **Automatic pairing**: one-button pairing with persistent NVS storage
- **Safety interlocks**: high beam requires low beam; failsafe shuts off all lights after 30s without signal
- **Connection monitoring**: heartbeats, ACK-based command confirmation, NeoPixel status LED
- **Test mode**: controller works standalone for UI testing without a receiver

## Hardware

### Controller (TX)

| Component | Details |
|-----------|---------|
| Board | [Waveshare ESP32-C6-Touch-LCD-1.47-M](https://www.waveshare.com/wiki/ESP32-C6-Touch-LCD-1.47) |
| MCU | ESP32-C6 (RISC-V, 8 MB flash) |
| Display | 1.47" JD9853, 172x320, rotated to 320x172 landscape |
| Touch | AXS5106L capacitive (I2C @ 0x63) |
| Status LED | WS2812 NeoPixel on GPIO8 |

### Receiver (RX)

| Component | Details |
|-----------|---------|
| Board | Any ESP32 dev board (classic Xtensa) |
| Light outputs | 5x GPIO, active-HIGH |
| Status LED | Built-in LED on GPIO2 |
| Pairing | BOOT button (GPIO0) — hold during power-up |

### Receiver Wiring

Connect ESP32 GPIOs to your lights through appropriate drivers (MOSFETs, relays, or LED drivers) depending on voltage and current requirements. All outputs are active-HIGH (3.3 V logic).

| GPIO | Function |
|------|----------|
| 16 | Fog lights |
| 17 | Low beam |
| 18 | High beam |
| 19 | Light bar |
| 21 | Hazard lights |
| 2 | Status LED |
| 0 | Pairing button (BOOT) |

## Building & Flashing

### Prerequisites

- [PlatformIO](https://platformio.org/) (CLI or IDE plugin)
- USB cables for both boards

### Build

```bash
# Build controller (TX) firmware
pio run -e controller

# Build receiver (RX) firmware
pio run -e receiver
```

### Flash

```bash
# Flash controller
pio run -e controller -t upload

# Flash receiver
pio run -e receiver -t upload
```

### Serial Monitor

```bash
pio device monitor    # 115200 baud
```

## Pairing

1. Power on the **receiver** while holding the **BOOT button** (GPIO0). The status LED flashes 3 times to confirm pairing mode.
2. On the **controller**, open **Settings** and tap **Start Pairing**.
3. Both devices exchange MAC addresses over ESP-NOW broadcast and store them in NVS.
4. Power-cycle both devices. The pairing is persistent and survives reboots.

## Protocol

Communication uses ESP-NOW with packed C structs (`__attribute__((packed))`) for cross-architecture compatibility (RISC-V controller / Xtensa receiver).

| Message | Direction | Purpose |
|---------|-----------|---------|
| `LightCommand` | TX -> RX | Set light state (5-bit bitmask) |
| `LightAck` | RX -> TX | Confirm current state |
| `Heartbeat` | RX -> TX | Keep-alive (every 2 s) |
| `StateReport` | RX -> TX | Full state + uptime |
| `PairRequest` | TX -> RX | Broadcast pairing request |
| `PairResponse` | RX -> TX | Pairing response with MAC |

### Light Bitmask

| Bit | Light |
|-----|-------|
| 0 | Fog lights |
| 1 | Low beam |
| 2 | High beam |
| 3 | Light bar |
| 4 | Hazard lights |

### Timing

| Parameter | Value |
|-----------|-------|
| ACK timeout | 200 ms |
| Max retries | 3 |
| Heartbeat interval | 2 s |
| Connection timeout (TX) | 6 s |
| Failsafe timeout (RX) | 30 s |

## Project Structure

```
light_controller/
├── src/
│   ├── controller/      # TX: display, touch, LVGL UI, ESP-NOW TX
│   └── receiver/        # RX: GPIO outputs, ESP-NOW RX, failsafe
├── lib/
│   ├── protocol/        # Shared wire protocol definitions
│   └── axs5106l_touch/  # AXS5106L touch driver
├── include/
│   └── lv_conf.h        # LVGL 8.4 configuration
└── platformio.ini       # Build configuration (two environments)
```

## Dependencies

### Controller
- [LVGL 8.4](https://lvgl.io/) — touchscreen UI framework
- [Arduino_GFX 1.6.5](https://github.com/moononournation/Arduino_GFX) — display driver
- [FastLED 3.9](https://fastled.io/) — NeoPixel status LED

### Receiver
- ESP-IDF built-ins only (ESP-NOW, WiFi, Preferences)

## License

This project is open source. See [LICENSE](LICENSE) for details.
