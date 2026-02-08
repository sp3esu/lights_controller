# Controleur d'eclairage RC

[English](../README.md) | [Polski](README_PL.md) | [Deutsch](README_DE.md) | **Francais** | [Русский](README_RU.md) | [Українська](README_UA.md)

Controleur d'eclairage sans fil pour voitures et camions RC. Une telecommande a ecran tactile (TX) communique via ESP-NOW avec un recepteur (RX) monte sur le vehicule pour controler plusieurs sorties lumineuses en temps reel.

## Fonctionnalites

- **5 canaux lumineux independants** : feux de croisement, feux de route, antibrouillards, barre lumineuse, feux de detresse
- **Interface tactile** : grille de boutons 2x3 sur un ecran couleur 1,47" avec LVGL
- **Communication ESP-NOW** : protocole a faible latence — aucun routeur WiFi necessaire
- **Appairage automatique** : appairage en un bouton avec stockage persistant NVS
- **Verrouillages de securite** : les feux de route necessitent les feux de croisement ; le mode securite eteint toutes les lumieres apres 30 s sans signal
- **Surveillance de connexion** : heartbeats, confirmation de commandes par ACK, LED NeoPixel de statut
- **Mode test** : le controleur fonctionne de maniere autonome sans recepteur

## Materiel

### Controleur (TX)

| Composant | Details |
|-----------|---------|
| Carte | [Waveshare ESP32-C6-Touch-LCD-1.47-M](https://www.waveshare.com/wiki/ESP32-C6-Touch-LCD-1.47) |
| MCU | ESP32-C6 (RISC-V, 8 Mo flash) |
| Ecran | 1,47" JD9853, 172x320, pivote en 320x172 paysage |
| Tactile | AXS5106L capacitif (I2C @ 0x63) |
| LED de statut | WS2812 NeoPixel sur GPIO8 |

### Recepteur (RX)

| Composant | Details |
|-----------|---------|
| Carte | Toute carte de developpement ESP32 (Xtensa classique) |
| Sorties lumineuses | 5x GPIO, actif-HAUT |
| LED de statut | LED integree sur GPIO2 |
| Appairage | Bouton BOOT (GPIO0) — maintenir a l'allumage |

### Cablage du recepteur

Connectez les GPIO de l'ESP32 a vos lumieres via des pilotes appropries (MOSFETs, relais ou pilotes LED) selon les exigences de tension et de courant. Toutes les sorties sont actif-HAUT (logique 3,3 V).

| GPIO | Fonction |
|------|----------|
| 16 | Antibrouillards |
| 17 | Feux de croisement |
| 18 | Feux de route |
| 19 | Barre lumineuse |
| 21 | Feux de detresse |
| 2 | LED de statut |
| 0 | Bouton d'appairage (BOOT) |

## Compilation et flashage

### Prerequis

- [PlatformIO](https://platformio.org/) (CLI ou plugin IDE)
- Cables USB pour les deux cartes

### Compilation

```bash
# Compiler le firmware du controleur (TX)
pio run -e controller

# Compiler le firmware du recepteur (RX)
pio run -e receiver
```

### Flashage

```bash
# Flasher le controleur
pio run -e controller -t upload

# Flasher le recepteur
pio run -e receiver -t upload
```

### Moniteur serie

```bash
pio device monitor    # 115200 bauds
```

## Appairage

1. Allumez le **recepteur** en maintenant le **bouton BOOT** (GPIO0). La LED de statut clignote 3 fois pour confirmer le mode d'appairage.
2. Sur le **controleur**, ouvrez les **Parametres** et appuyez sur **Demarrer l'appairage**.
3. Les appareils echangent leurs adresses MAC via broadcast ESP-NOW et les stockent en NVS.
4. Redemarrez les deux appareils. L'appairage est persistant et survit aux redemarrages.

## Protocole

La communication utilise ESP-NOW avec des structures C compactees (`__attribute__((packed))`) pour la compatibilite inter-architectures (controleur RISC-V / recepteur Xtensa).

| Message | Direction | Fonction |
|---------|-----------|----------|
| `LightCommand` | TX -> RX | Definir l'etat des lumieres (masque 5 bits) |
| `LightAck` | RX -> TX | Confirmer l'etat actuel |
| `Heartbeat` | RX -> TX | Maintien de connexion (toutes les 2 s) |
| `StateReport` | RX -> TX | Etat complet + duree de fonctionnement |
| `PairRequest` | TX -> RX | Demande d'appairage (broadcast) |
| `PairResponse` | RX -> TX | Reponse d'appairage avec MAC |

### Masque binaire des lumieres

| Bit | Lumiere |
|-----|---------|
| 0 | Antibrouillards |
| 1 | Feux de croisement |
| 2 | Feux de route |
| 3 | Barre lumineuse |
| 4 | Feux de detresse |

### Temporisations

| Parametre | Valeur |
|-----------|--------|
| Timeout ACK | 200 ms |
| Essais max. | 3 |
| Intervalle heartbeat | 2 s |
| Timeout de connexion (TX) | 6 s |
| Timeout de securite (RX) | 30 s |

## Structure du projet

```
light_controller/
├── src/
│   ├── controller/      # TX : ecran, tactile, UI LVGL, ESP-NOW TX
│   └── receiver/        # RX : sorties GPIO, ESP-NOW RX, mode securite
├── lib/
│   ├── protocol/        # Definitions de protocole partagees
│   └── axs5106l_touch/  # Pilote tactile AXS5106L
├── include/
│   └── lv_conf.h        # Configuration LVGL 8.4
└── platformio.ini       # Configuration de compilation (deux environnements)
```

## Dependances

### Controleur
- [LVGL 8.4](https://lvgl.io/) — framework d'interface tactile
- [Arduino_GFX 1.6.5](https://github.com/moononournation/Arduino_GFX) — pilote d'ecran
- [FastLED 3.9](https://fastled.io/) — LED NeoPixel de statut

### Recepteur
- Uniquement les composants integres ESP-IDF (ESP-NOW, WiFi, Preferences)

## Licence

Ce projet est open source. Voir [LICENSE](../LICENSE) pour les details.
