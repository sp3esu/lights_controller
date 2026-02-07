# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands

```bash
pio run -e controller            # Build controller (TX) firmware
pio run -e receiver              # Build receiver (RX) firmware
pio run -e controller -t upload  # Flash controller to ESP32-C6
pio run -e receiver -t upload    # Flash receiver to ESP32
pio device monitor               # Serial monitor (115200 baud)
```

No test framework is configured. There is no linter.

## Architecture

Two-device wireless RC light controller: a touchscreen controller (TX) sends commands over ESP-NOW to a receiver (RX) that drives GPIO light outputs.

**Single PlatformIO project, two environments** separated by `build_src_filter`:
- `controller` — ESP32-C6-Touch-LCD-1.47-M (Waveshare touch version), pioarduino v55.03.36
- `receiver` — generic ESP32 dev board, stock espressif32 platform

Both use IDF 5.x under the Arduino framework.

### Communication Flow

Controller sends `LightCommand` (4-bit bitmask) → Receiver applies GPIO states and replies with `LightAck`. Receiver sends heartbeats every 2s. TX disconnects after 6s silence; RX failsafe turns off all lights after 30s without commands. Pairing uses broadcast/unicast handshake, persisted to NVS via `Preferences`.

### Source Layout

- `src/controller/` — TX: display (JD9853 via ST7789 + custom init), touch (AXS5106L), LVGL UI (2x2 button grid), ESP-NOW TX with retry/pairing
- `src/receiver/` — RX: GPIO light outputs, ESP-NOW RX with heartbeats/pairing/failsafe
- `lib/protocol/` — Shared wire protocol: packed structs with common header (version, msg_type, seq_num)
- `lib/axs5106l_touch/` — Touch driver (controller-only)
- `include/lv_conf.h` — LVGL 8.4 configuration

### Display

The JD9853 panel is 172×320 native (portrait). Constructed as `Arduino_ST7789` with column offsets (34, 0), then custom register init via `bus->batchOperation()`. Rotated to landscape via `gfx->setRotation(1)`, giving **320×172 effective resolution** for LVGL.

- `DISP_NATIVE_W=172, DISP_NATIVE_H=320` — GFX constructor
- `DISP_WIDTH=320, DISP_HEIGHT=172` — LVGL and UI layout

## Critical Gotchas

- **Never use `-D CONTROLLER`** as a build flag — conflicts with a FastLED internal macro. Use `-D IS_CONTROLLER`.
- **ESP-NOW callback signature** on IDF 5.x (both envs): `void cb(const esp_now_recv_info_t *info, const uint8_t *data, int len)` — not the old `const uint8_t *mac` form.
- **Arduino_GFX** is pinned to `#v1.6.5` from GitHub (registry lags). The `BLACK` constant was renamed to `RGB565_BLACK`.
- **LVGL spinner widget** requires `LV_USE_ARC 1` in lv_conf.h.
- **`lv_img_set_zoom()` does not work** with `LV_IMG_CF_ALPHA_8BIT` images in LVGL v8.4 — renders nothing.
- **Touch version pin mapping** differs from the non-touch Waveshare board. Pins: SPI (DC=15, CS=14, SCK=1, MOSI=2, RST=22, BL=23), Touch I2C (SDA=18, SCL=19, RST=20, INT=21), NeoPixel=GPIO8.
- **Protocol structs use `__attribute__((packed))`** — required for cross-architecture compatibility (RISC-V controller ↔ Xtensa receiver).
