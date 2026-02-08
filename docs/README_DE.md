# RC-Lichtsteuerung

[English](../README.md) | [Polski](README_PL.md) | **Deutsch** | [Francais](README_FR.md) | [Русский](README_RU.md) | [Українська](README_UA.md)

Kabellose Lichtsteuerung fuer RC-Autos und -Trucks. Eine Touchscreen-Fernbedienung (TX) kommuniziert ueber ESP-NOW mit einem am Fahrzeug montierten Empfaenger (RX) zur Echtzeit-Steuerung mehrerer Lichtausgaenge.

## Funktionen

- **5 unabhaengige Lichtkanaele**: Abblendlicht, Fernlicht, Nebelscheinwerfer, Lichtleiste, Warnblinker
- **Touchscreen-Oberflaeche**: 2x3-Tastenraster auf einem 1,47"-Farbdisplay mit LVGL
- **ESP-NOW-Funk**: Protokoll mit geringer Latenz — kein WLAN-Router erforderlich
- **Automatisches Pairing**: Ein-Tasten-Kopplung mit dauerhafter NVS-Speicherung
- **Sicherheitsverriegelungen**: Fernlicht erfordert Abblendlicht; Failsafe schaltet alle Lichter nach 30 s ohne Signal ab
- **Verbindungsueberwachung**: Heartbeats, ACK-basierte Befehlsbestaetigung, NeoPixel-Status-LED
- **Testmodus**: Controller funktioniert eigenstaendig ohne Empfaenger

## Hardware

### Controller (TX)

| Komponente | Details |
|------------|---------|
| Platine | [Waveshare ESP32-C6-Touch-LCD-1.47-M](https://www.waveshare.com/wiki/ESP32-C6-Touch-LCD-1.47) |
| MCU | ESP32-C6 (RISC-V, 8 MB Flash) |
| Display | 1,47" JD9853, 172x320, auf 320x172 Querformat gedreht |
| Touch | AXS5106L kapazitiv (I2C @ 0x63) |
| Status-LED | WS2812 NeoPixel an GPIO8 |

### Empfaenger (RX)

| Komponente | Details |
|------------|---------|
| Platine | Beliebiges ESP32-Entwicklungsboard (klassisches Xtensa) |
| Lichtausgaenge | 5x GPIO, aktiv-HIGH |
| Status-LED | Eingebaute LED an GPIO2 |
| Pairing | BOOT-Taste (GPIO0) — beim Einschalten gedrueckt halten |

### Empfaenger-Verkabelung

Verbinden Sie die ESP32-GPIOs ueber geeignete Treiber (MOSFETs, Relais oder LED-Treiber) mit Ihren Lichtern, je nach Spannungs- und Stromanforderungen. Alle Ausgaenge sind aktiv-HIGH (3,3-V-Logik).

| GPIO | Funktion |
|------|----------|
| 16 | Nebelscheinwerfer |
| 17 | Abblendlicht |
| 18 | Fernlicht |
| 19 | Lichtleiste |
| 21 | Warnblinker |
| 2 | Status-LED |
| 0 | Pairing-Taste (BOOT) |

## Kompilieren & Flashen

### Voraussetzungen

- [PlatformIO](https://platformio.org/) (CLI oder IDE-Plugin)
- USB-Kabel fuer beide Platinen

### Kompilieren

```bash
# Controller-Firmware (TX) kompilieren
pio run -e controller

# Empfaenger-Firmware (RX) kompilieren
pio run -e receiver
```

### Flashen

```bash
# Controller flashen
pio run -e controller -t upload

# Empfaenger flashen
pio run -e receiver -t upload
```

### Serieller Monitor

```bash
pio device monitor    # 115200 Baud
```

## Pairing

1. Schalten Sie den **Empfaenger** ein und halten Sie dabei die **BOOT-Taste** (GPIO0) gedrueckt. Die Status-LED blinkt 3 Mal zur Bestaetigung des Pairing-Modus.
2. Oeffnen Sie auf dem **Controller** die **Einstellungen** und tippen Sie auf **Pairing starten**.
3. Beide Geraete tauschen MAC-Adressen ueber ESP-NOW-Broadcast aus und speichern sie im NVS.
4. Starten Sie beide Geraete neu. Das Pairing ist dauerhaft und uebersteht Neustarts.

## Protokoll

Die Kommunikation verwendet ESP-NOW mit gepackten C-Structs (`__attribute__((packed))`) fuer architekturuebergreifende Kompatibilitaet (RISC-V-Controller / Xtensa-Empfaenger).

| Nachricht | Richtung | Zweck |
|-----------|----------|-------|
| `LightCommand` | TX -> RX | Lichtzustand setzen (5-Bit-Maske) |
| `LightAck` | RX -> TX | Aktuellen Zustand bestaetigen |
| `Heartbeat` | RX -> TX | Verbindungserhaltung (alle 2 s) |
| `StateReport` | RX -> TX | Vollstaendiger Zustand + Betriebszeit |
| `PairRequest` | TX -> RX | Pairing-Anfrage (Broadcast) |
| `PairResponse` | RX -> TX | Pairing-Antwort mit MAC |

### Licht-Bitmaske

| Bit | Licht |
|-----|-------|
| 0 | Nebelscheinwerfer |
| 1 | Abblendlicht |
| 2 | Fernlicht |
| 3 | Lichtleiste |
| 4 | Warnblinker |

### Zeitvorgaben

| Parameter | Wert |
|-----------|------|
| ACK-Timeout | 200 ms |
| Max. Wiederholungen | 3 |
| Heartbeat-Intervall | 2 s |
| Verbindungs-Timeout (TX) | 6 s |
| Failsafe-Timeout (RX) | 30 s |

## Projektstruktur

```
light_controller/
├── src/
│   ├── controller/      # TX: Display, Touch, LVGL-UI, ESP-NOW TX
│   └── receiver/        # RX: GPIO-Ausgaenge, ESP-NOW RX, Failsafe
├── lib/
│   ├── protocol/        # Gemeinsame Protokolldefinitionen
│   └── axs5106l_touch/  # AXS5106L-Touch-Treiber
├── include/
│   └── lv_conf.h        # LVGL 8.4 Konfiguration
└── platformio.ini       # Build-Konfiguration (zwei Umgebungen)
```

## Abhaengigkeiten

### Controller
- [LVGL 8.4](https://lvgl.io/) — Touchscreen-UI-Framework
- [Arduino_GFX 1.6.5](https://github.com/moononournation/Arduino_GFX) — Display-Treiber
- [FastLED 3.9](https://fastled.io/) — NeoPixel-Status-LED

### Empfaenger
- Nur ESP-IDF-Bordmittel (ESP-NOW, WiFi, Preferences)

## Lizenz

Dieses Projekt ist Open Source. Details siehe [LICENSE](../LICENSE).
