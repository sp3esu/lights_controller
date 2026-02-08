# LED Driver Board — Design & Assembly Guide

Dedicated PCB for driving RC car LEDs from ESP32 GPIOs via MOSFET low-side switching.

## Overview

```
3S LiPo (11.1V) ──┬── MP1584EN buck ── 5V ── ESP32 Vin
                   │
                   └── Battery+ to LED channels (via resistor+LED off-board)
                        │
                   AO3400A MOSFETs (low-side switch, gate driven by ESP32 GPIO)
                        │
                       GND
```

- **9 output channels** — MOSFET-switched ground for each LED group
- **On-board 5V buck** — powers ESP32 dev board via Vin pin
- **LED resistors mounted near LEDs** (off-board) — keeps PCB small, allows per-LED tuning
- **ESP32 dev board plugs in via pin headers** — no USB/boot circuitry on PCB

## Power Supply

**Input:** 3S LiPo (11.1V nominal, 9.9V–12.6V range)

**On-board regulation:**

| Stage | Converter | Input | Output | Notes |
|-------|-----------|-------|--------|-------|
| 1 | MP1584EN buck module | 9.9–12.6V | 5V | ~92% efficient, powers ESP32 |
| 2 | ESP32 onboard LDO | 5V (Vin pin) | 3.3V | Internal to dev board |

**MP1584EN module pinout:**

| Pin | Connection |
|-----|------------|
| IN+ | Battery + (via screw terminal) |
| IN- | GND |
| OUT+ | ESP32 Vin |
| OUT- | GND |

Adjust the trimpot to 5.0V **before** connecting the ESP32.

## Channel Allocation

| Ch | GPIO | Function | LED Color | Typical LEDs | Resistor (20mA @ 11.1V) |
|----|------|----------|-----------|-------------|--------------------------|
| 1 | 16 | Low beam | White | 2 (parallel) | 390R 1/4W each |
| 2 | 17 | High beam | White | 2 (parallel) | 390R 1/4W each |
| 3 | 18 | Left turn | Amber | 3+ (parallel) | 470R 1/4W each |
| 4 | 19 | Right turn | Amber | 3+ (parallel) | 470R 1/4W each |
| 5 | 21 | Stop/brake | Red | 3+ (parallel) | 470R 1/4W each |
| 6 | 22 | Reverse | White | 1–2 (parallel) | 390R 1/4W each |
| 7 | 23 | Light bar | White | High current | Sized per strip |
| 8 | 25 | Spare 1 | Any | User choice | — |
| 9 | 26 | Spare 2 | Any | User choice | — |
| — | 2 | Status LED | — | On-board | On-board |

All GPIOs support hardware PWM (LEDC) on ESP32.

## Circuit Topology

### Per-channel schematic (low-side MOSFET switch)

```
Battery+ ──── [to off-board connector] ──── Resistor ──── LED(+) ──── LED(-) ──── [back to board]
                                                                                        │
                                                                                      Drain
                                                                                        │
                                                                                   AO3400A (N-ch)
                                                                                        │
                                                                                      Source
                                                                                        │
                                                                                       GND

ESP32 GPIO ──[100R]──── Gate
                          │
                        [10K]
                          │
                         GND
```

**Each output connector provides two pins:**
- **Pin 1:** Battery+ (always hot)
- **Pin 2:** MOSFET drain (switched ground)

The LED + current-limiting resistor are wired off-board between these two pins.

### Gate drive circuit

| Component | Value | Purpose |
|-----------|-------|---------|
| R_gate | 100R (0603) | Limits gate inrush current, dampens ringing |
| R_pulldown | 10K (0603) | Keeps MOSFET OFF during ESP32 boot/reset |

The 10K pull-down ensures all lights are OFF when the ESP32 is resetting or unprogrammed.

## MOSFET Selection: AO3400A

| Parameter | Value |
|-----------|-------|
| Package | SOT-23 |
| Type | N-channel enhancement |
| Vds (max) | 30V |
| Id (max) | 5.7A |
| Rds(on) @ Vgs=4.5V | 32mΩ |
| Rds(on) @ Vgs=2.5V | 48mΩ |
| Vgs(th) | 0.65V typ, 1.05V max |
| LCSC # | C20917 |

At 3.3V gate drive from ESP32, the AO3400A is fully enhanced. Power dissipation at 20mA per LED is negligible (~0.01mW).

For the light bar channel (Ch 7), the AO3400A handles up to 5.7A — sufficient for LED strips.

## Resistor Calculations

### Formula

```
R = (V_supply - V_f) / I_target
```

Where:
- V_supply = 11.1V (nominal), range 9.9V–12.6V
- I_target = 20mA (standard 5mm LED)
- V_f = forward voltage of LED

### White LEDs (Vf ≈ 3.2V)

```
R = (11.1 - 3.2) / 0.020 = 395Ω → use 390R (standard value)
```

| Condition | Current |
|-----------|---------|
| Full charge (12.6V) | 24.1mA |
| Nominal (11.1V) | 20.3mA |
| Low battery (9.9V) | 17.2mA |

### Red LEDs (Vf ≈ 2.0V)

```
R = (11.1 - 2.0) / 0.020 = 455Ω → use 470R (standard value)
```

| Condition | Current |
|-----------|---------|
| Full charge (12.6V) | 22.6mA |
| Nominal (11.1V) | 19.4mA |
| Low battery (9.9V) | 16.8mA |

### Amber LEDs (Vf ≈ 2.1V)

```
R = (11.1 - 2.1) / 0.020 = 450Ω → use 470R (standard value)
```

| Condition | Current |
|-----------|---------|
| Full charge (12.6V) | 22.3mA |
| Nominal (11.1V) | 19.1mA |
| Low battery (9.9V) | 16.6mA |

### Important notes

- **Each LED gets its own resistor** — parallel LEDs each have a dedicated series resistor
- **Do NOT put 3 white LEDs in series** — only 0.3V headroom at low battery (9.9V - 3×3.2V = 0.3V), LEDs will flicker and die
- **PWM dimming** works on top of the resistor — the resistor sets max current at 100% duty, PWM reduces average current proportionally
- **Resistor power:** P = I²R = 0.020² × 470 = 0.19W → 1/4W resistors are fine

## Connector Pinouts

### Power input (2-pin screw terminal, 5mm pitch)

| Pin | Signal |
|-----|--------|
| 1 | Battery + (11.1V) |
| 2 | Battery - (GND) |

### LED output channels (JST-XH 2-pin per channel)

| Pin | Signal |
|-----|--------|
| 1 | Battery + (always hot) |
| 2 | Switched GND (MOSFET drain) |

Wire LED + resistor between pin 1 and pin 2 (off-board).

### ESP32 dev board (2×15 or 2×19 pin headers, 2.54mm)

The ESP32 dev board plugs directly into female pin headers on the PCB. Only the following pins are actively used:

| ESP32 Pin | Board Connection |
|-----------|-----------------|
| Vin | 5V from MP1584EN buck |
| GND | Common ground |
| GPIO 2 | Status LED (on-board) |
| GPIO 16 | Ch 1 MOSFET gate |
| GPIO 17 | Ch 2 MOSFET gate |
| GPIO 18 | Ch 3 MOSFET gate |
| GPIO 19 | Ch 4 MOSFET gate |
| GPIO 21 | Ch 5 MOSFET gate |
| GPIO 22 | Ch 6 MOSFET gate |
| GPIO 23 | Ch 7 MOSFET gate |
| GPIO 25 | Ch 8 MOSFET gate |
| GPIO 26 | Ch 9 MOSFET gate |

## PCB Specifications

| Parameter | Value |
|-----------|-------|
| Dimensions | ~30 × 50 mm |
| Layers | 2 |
| Copper weight | 1 oz (35μm) |
| Min trace width | 0.25mm (signal), 0.5mm+ (power) |
| Min via | 0.3mm drill |
| Surface finish | HASL (lead-free) |

### Layout guidelines

- **Power traces** (battery, 5V): 0.5mm minimum, 1mm preferred
- **Light bar channel (Ch 7):** thicker traces or copper pour, screw terminal option for high current
- **Ground plane** on bottom layer — provides return path and heat dissipation
- **Decoupling caps** near MP1584EN: 22μF input, 22μF output (0805)
- **MOSFETs** placed in a row near board edge, close to output connectors
- **Pin headers** for ESP32 centered on board

## Bill of Materials

| # | Component | Qty | Package | LCSC # | ~Cost |
|---|-----------|-----|---------|--------|-------|
| 1 | AO3400A N-ch MOSFET | 9 | SOT-23 | C20917 | $0.63 |
| 2 | 100R resistor (gate) | 9 | 0603 | C25803 | $0.09 |
| 3 | 10K resistor (pulldown) | 9 | 0603 | C25804 | $0.09 |
| 4 | MP1584EN buck module | 1 | Module | — | $0.50 |
| 5 | 22μF ceramic cap | 2 | 0805 | C45783 | $0.10 |
| 6 | JST-XH 2-pin header | 10 | Through-hole | C158012 | $1.50 |
| 7 | Female pin headers 1×15 | 2 | 2.54mm TH | C35445 | $0.20 |
| 8 | Screw terminal 2-pin | 1 | 5mm TH | C8465 | $0.15 |
| 9 | Status LED (green) | 1 | 0805 | C2297 | $0.02 |
| 10 | 1K resistor (status LED) | 1 | 0603 | C25585 | $0.01 |
| | **PCB (5 boards, JLCPCB)** | | | | **$2.00** |
| | **Total per board** | | | | **~$3–4** |

### Off-board components (per car)

| Component | Qty | Notes |
|-----------|-----|-------|
| 390R 1/4W resistor | 6–8 | For white LEDs (low/high beam, reverse) |
| 470R 1/4W resistor | 9+ | For red/amber LEDs (turn, brake) |
| 5mm white LED | 6–8 | Headlights, reverse |
| 5mm amber LED | 6+ | Turn signals |
| 5mm red LED | 3+ | Brake/stop lights |
| JST-XH 2-pin housing + crimps | 9 | One per channel |

## Assembly Order

### Factory (JLCPCB SMD assembly)
1. All 0603 resistors (gate + pulldown)
2. All SOT-23 MOSFETs
3. 0805 capacitors
4. Status LED + resistor

### Hand-solder (after boards arrive)
1. Female pin headers for ESP32 (solder from bottom)
2. 2-pin screw terminal for battery input
3. JST-XH connectors for LED outputs
4. MP1584EN buck module (solder 4 pins)
5. **Set buck output to 5.0V** before inserting ESP32

### Testing
1. Connect battery, verify 5V output from buck
2. Insert ESP32, flash receiver firmware
3. Test each channel: measure voltage at JST output (should see battery voltage when GPIO high)
4. Connect test LED + resistor to each channel, verify operation
5. Test PWM dimming via serial commands or controller

## Design Tool

**Recommended: EasyEDA (Standard or Pro)**
- Free, browser-based
- LCSC component library (all parts above available)
- One-click BOM/pick-and-place export for JLCPCB assembly
- Direct order to JLCPCB

**Alternative: KiCad 9** — desktop, no vendor lock-in, steeper learning curve.

## Manufacturing

**JLCPCB** — ~$2 for 5 boards (2-layer, 30×50mm), SMD assembly ~$8–10 extra.

Order flow:
1. Export Gerber files from EasyEDA
2. Upload to jlcpcb.com
3. Select "SMD Assembly" and upload BOM + pick-and-place files
4. Review component placements
5. Order — 1–3 day production, ~2 week shipping to EU

## Reference Designs

- [Dubious Creations ESP32 8-ch LED controller](https://dubiouscreations.com/2020/08/16/building-an-esp32-light-controller/) — closest match, AO3400A MOSFETs, 20kHz PWM
- [TheDIYGuy999 RC Sound+Light ESP32](https://github.com/TheDIYGuy999/Rc_Engine_Sound_ESP32) — 12 channels, Eagle + Gerber files
- [Lane Boys MK4 RC Light Controller](https://github.com/laneboysrc/rc-light-controller) — TLC5940 constant-current approach
