# Kontroler Oswietlenia RC

[English](../README.md) | **Polski** | [Deutsch](README_DE.md) | [Francais](README_FR.md) | [Русский](README_RU.md) | [Українська](README_UA.md)

Bezprzewodowy kontroler oswietlenia do samochodow i ciezarowek RC. Reczny pilot z ekranem dotykowym (TX) komunikuje sie przez ESP-NOW z odbiornikiem (RX) zamontowanym w pojezdzie, sterujac wieloma wyjsciami swietlnymi w czasie rzeczywistym.

## Funkcje

- **5 niezaleznych kanalow swiatla**: swiatla mijania, swiatla drogowe, swiatla przeciwmgielne, listwa swietlna, swiatla awaryjne
- **Interfejs dotykowy**: siatka przyciskow 2x3 na kolorowym wyswietlaczu 1,47" z LVGL
- **Lacznosc bezprzewodowa ESP-NOW**: protokol o niskim opoznieniu, bez potrzeby routera WiFi
- **Automatyczne parowanie**: parowanie jednym przyciskiem z trwalym zapisem w NVS
- **Blokady bezpieczenstwa**: swiatla drogowe wymagaja wlaczonych swiatel mijania; tryb awaryjny wylacza wszystkie swiatla po 30 s bez sygnalu
- **Monitorowanie polaczenia**: heartbeaty, potwierdzenia ACK, dioda LED NeoPixel
- **Tryb testowy**: kontroler dziala samodzielnie bez odbiornika

## Sprzet

### Kontroler (TX)

| Element | Szczegoly |
|---------|-----------|
| Plytka | [Waveshare ESP32-C6-Touch-LCD-1.47-M](https://www.waveshare.com/wiki/ESP32-C6-Touch-LCD-1.47) |
| MCU | ESP32-C6 (RISC-V, 8 MB flash) |
| Wyswietlacz | 1,47" JD9853, 172x320, obrocony do 320x172 poziomo |
| Dotyk | AXS5106L pojemnosciowy (I2C @ 0x63) |
| Dioda statusu | WS2812 NeoPixel na GPIO8 |

### Odbiornik (RX)

| Element | Szczegoly |
|---------|-----------|
| Plytka | Dowolna plytka ESP32 (klasyczny Xtensa) |
| Wyjscia swiatla | 5x GPIO, aktywne-WYSOKO |
| Dioda statusu | Wbudowana LED na GPIO2 |
| Parowanie | Przycisk BOOT (GPIO0) — przytrzymaj przy wlaczaniu |

### Polaczenia odbiornika

Podlacz GPIO ESP32 do swiatel przez odpowiednie sterowniki (MOSFET-y, przekazniki lub sterowniki LED) w zaleznosci od napiecia i pradu. Wszystkie wyjscia sa aktywne-WYSOKO (logika 3,3 V).

| GPIO | Funkcja |
|------|---------|
| 16 | Swiatla przeciwmgielne |
| 17 | Swiatla mijania |
| 18 | Swiatla drogowe |
| 19 | Listwa swietlna |
| 21 | Swiatla awaryjne |
| 2 | Dioda statusu |
| 0 | Przycisk parowania (BOOT) |

## Kompilacja i programowanie

### Wymagania

- [PlatformIO](https://platformio.org/) (CLI lub wtyczka IDE)
- Kable USB do obu plytek

### Kompilacja

```bash
# Kompilacja firmware kontrolera (TX)
pio run -e controller

# Kompilacja firmware odbiornika (RX)
pio run -e receiver
```

### Programowanie

```bash
# Programowanie kontrolera
pio run -e controller -t upload

# Programowanie odbiornika
pio run -e receiver -t upload
```

### Monitor szeregowy

```bash
pio device monitor    # 115200 baud
```

## Parowanie

1. Wlacz **odbiornik** przytrzymujac **przycisk BOOT** (GPIO0). Dioda statusu mrugnie 3 razy potwierdzajac tryb parowania.
2. Na **kontrolerze** wejdz w **Ustawienia** i dotknij **Rozpocznij parowanie**.
3. Urzadzenia wymieniaja adresy MAC przez broadcast ESP-NOW i zapisuja je w NVS.
4. Zrestartuj oba urzadzenia. Parowanie jest trwale i przetrwa ponowne uruchomienie.

## Protokol

Komunikacja uzywa ESP-NOW z upakowanymi strukturami C (`__attribute__((packed))`) dla kompatybilnosci miedzy architekturami (RISC-V kontroler / Xtensa odbiornik).

| Wiadomosc | Kierunek | Cel |
|-----------|----------|-----|
| `LightCommand` | TX -> RX | Ustaw stan swiatel (maska 5-bitowa) |
| `LightAck` | RX -> TX | Potwierdz aktualny stan |
| `Heartbeat` | RX -> TX | Podtrzymanie polaczenia (co 2 s) |
| `StateReport` | RX -> TX | Pelny stan + czas pracy |
| `PairRequest` | TX -> RX | Zadanie parowania (broadcast) |
| `PairResponse` | RX -> TX | Odpowiedz parowania z MAC |

### Maska bitowa swiatel

| Bit | Swiatlo |
|-----|---------|
| 0 | Swiatla przeciwmgielne |
| 1 | Swiatla mijania |
| 2 | Swiatla drogowe |
| 3 | Listwa swietlna |
| 4 | Swiatla awaryjne |

### Czasy

| Parametr | Wartosc |
|----------|---------|
| Timeout ACK | 200 ms |
| Maks. powtorzen | 3 |
| Interwal heartbeat | 2 s |
| Timeout polaczenia (TX) | 6 s |
| Timeout awaryjny (RX) | 30 s |

## Struktura projektu

```
light_controller/
├── src/
│   ├── controller/      # TX: wyswietlacz, dotyk, UI LVGL, ESP-NOW TX
│   └── receiver/        # RX: wyjscia GPIO, ESP-NOW RX, tryb awaryjny
├── lib/
│   ├── protocol/        # Wspoldzielone definicje protokolu
│   └── axs5106l_touch/  # Sterownik dotyku AXS5106L
├── include/
│   └── lv_conf.h        # Konfiguracja LVGL 8.4
└── platformio.ini       # Konfiguracja kompilacji (dwa srodowiska)
```

## Zaleznosci

### Kontroler
- [LVGL 8.4](https://lvgl.io/) — framework UI ekranu dotykowego
- [Arduino_GFX 1.6.5](https://github.com/moononournation/Arduino_GFX) — sterownik wyswietlacza
- [FastLED 3.9](https://fastled.io/) — dioda statusu NeoPixel

### Odbiornik
- Tylko wbudowane komponenty ESP-IDF (ESP-NOW, WiFi, Preferences)

## Licencja

Ten projekt jest open source. Szczegoly w pliku [LICENSE](../LICENSE).
