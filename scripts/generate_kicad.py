#!/usr/bin/env python3
"""Generate KiCad 8 project files for the LED Driver Board.

Produces:
  hardware/led-driver-board.kicad_pro  — project file
  hardware/led-driver-board.kicad_sch  — schematic
  hardware/led-driver-board.kicad_pcb  — PCB with placed footprints (unrouted)

No external dependencies — uses only Python stdlib.
"""

import json
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HARDWARE_DIR = Path(__file__).resolve().parent.parent / "hardware"

CHANNELS = [
    {"num": 1, "gpio": 16, "name": "Low beam",   "gate_r": "100", "pd_r": "10K"},
    {"num": 2, "gpio": 17, "name": "High beam",  "gate_r": "100", "pd_r": "10K"},
    {"num": 3, "gpio": 18, "name": "Left turn",  "gate_r": "100", "pd_r": "10K"},
    {"num": 4, "gpio": 19, "name": "Right turn",  "gate_r": "100", "pd_r": "10K"},
    {"num": 5, "gpio": 21, "name": "Stop/brake", "gate_r": "100", "pd_r": "10K"},
    {"num": 6, "gpio": 22, "name": "Reverse",    "gate_r": "100", "pd_r": "10K"},
    {"num": 7, "gpio": 23, "name": "Light bar",  "gate_r": "100", "pd_r": "10K"},
    {"num": 8, "gpio": 25, "name": "Spare 1",    "gate_r": "100", "pd_r": "10K"},
    {"num": 9, "gpio": 26, "name": "Spare 2",    "gate_r": "100", "pd_r": "10K"},
]

# Reference counters
_ref_counters = {}

def _next_ref(prefix):
    _ref_counters.setdefault(prefix, 0)
    _ref_counters[prefix] += 1
    return f"{prefix}{_ref_counters[prefix]}"

def gen_uuid():
    return str(uuid.uuid4())

# ---------------------------------------------------------------------------
# Net management
# ---------------------------------------------------------------------------

class NetManager:
    def __init__(self):
        self.nets = {"": 0, "GND": 1, "+BATT": 2, "+5V": 3}
        self._counter = 4
        # Pre-register all channel nets
        for ch in CHANNELS:
            self.get(f"GPIO_{ch['gpio']}")
            self.get(f"GATE_{ch['num']}")
            self.get(f"DRAIN_{ch['num']}")
        self.get("STATUS_LED")

    def get(self, name):
        if name not in self.nets:
            self.nets[name] = self._counter
            self._counter += 1
        return self.nets[name]

NET_MGR = NetManager()

# ---------------------------------------------------------------------------
# KiCad S-expression helpers
# ---------------------------------------------------------------------------

SCH_VERSION = 20231120
PCB_VERSION = 20240108
GENERATOR = "led_driver_generator"

def _xy(x, y):
    return f"(at {x:.2f} {y:.2f})"

def _xy_rot(x, y, rot=0):
    return f"(at {x:.2f} {y:.2f} {rot})"

# ---------------------------------------------------------------------------
# Schematic lib_symbols (embedded)
# ---------------------------------------------------------------------------

def lib_symbol_resistor():
    return """    (symbol "Device:R" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "R" (at 2.032 0 90) (effects (font (size 1.27 1.27))))
      (property "Value" "R" (at -2.032 0 90) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at -1.778 0 90) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "ki_keywords" "R res resistor" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "ki_fp_filters" "R_*" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "R_0_1"
        (rectangle (start -1.016 -2.54) (end 1.016 2.54) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "R_1_1"
        (pin passive line (at 0 3.81 270) (length 1.27) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -3.81 90) (length 1.27) (name "~" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )"""

def lib_symbol_nmos():
    return """    (symbol "Device:Q_NMOS_GSD" (pin_names (offset 0.254)) (in_bom yes) (on_board yes)
      (property "Reference" "Q" (at 5.08 1.905 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Value" "Q_NMOS_GSD" (at 5.08 0 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Footprint" "" (at 5.08 -1.905 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "ki_keywords" "transistor NMOS N-MOS N-MOSFET" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Q_NMOS_GSD_0_1"
        (polyline (pts (xy 0.254 0) (xy -2.54 0)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0.254 1.905) (xy 0.254 -1.905)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 0.762 -1.27) (xy 0.762 -2.286)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 0.762 0.508) (xy 0.762 -0.508)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 0.762 2.286) (xy 0.762 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 2.54 2.54) (xy 2.54 1.778) (xy 0.762 1.778)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 2.54 -2.54) (xy 2.54 0) (xy 0.762 0)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0.762 -1.778) (xy 2.54 -1.778) (xy 2.54 -2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 1.016 0) (xy 2.032 0.381) (xy 2.032 -0.381) (xy 1.016 0)) (stroke (width 0) (type default)) (fill (type outline)))
        (circle (center 1.651 0) (radius 2.794) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "Q_NMOS_GSD_1_1"
        (pin input line (at -5.08 0 0) (length 2.54) (name "G" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 2.54 -5.08 90) (length 2.54) (name "S" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 2.54 5.08 270) (length 2.54) (name "D" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
      )
    )"""

def lib_symbol_capacitor():
    return """    (symbol "Device:C" (pin_numbers hide) (pin_names (offset 0.254)) (in_bom yes) (on_board yes)
      (property "Reference" "C" (at 0.635 2.54 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Value" "C" (at 0.635 -2.54 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Footprint" "" (at 0.9652 -3.81 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "ki_keywords" "cap capacitor" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "ki_fp_filters" "C_*" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "C_0_1"
        (polyline (pts (xy -2.032 -0.762) (xy 2.032 -0.762)) (stroke (width 0.508) (type default)) (fill (type none)))
        (polyline (pts (xy -2.032 0.762) (xy 2.032 0.762)) (stroke (width 0.508) (type default)) (fill (type none)))
      )
      (symbol "C_1_1"
        (pin passive line (at 0 3.81 270) (length 3.048) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -3.81 90) (length 3.048) (name "~" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )"""

def lib_symbol_led():
    return """    (symbol "Device:LED" (pin_numbers hide) (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "D" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
      (property "Value" "LED" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "ki_keywords" "LED diode" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "ki_fp_filters" "LED* D_*" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "LED_0_1"
        (polyline (pts (xy -1.27 -1.27) (xy -1.27 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy -1.27 0) (xy 1.27 0)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 -1.27) (xy 1.27 1.27) (xy -1.27 0) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy -3.048 -0.762) (xy -4.572 -2.286)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy -1.778 -0.762) (xy -3.302 -2.286)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "LED_1_1"
        (pin passive line (at -3.81 0 0) (length 2.54) (name "A" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 3.81 0 180) (length 2.54) (name "K" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )"""

def lib_symbol_conn_01x02():
    return """    (symbol "Connector:Conn_01x02_Pin" (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Conn_01x02_Pin" (at 0 -5.08 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "ki_keywords" "connector" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Conn_01x02_Pin_1_1"
        (rectangle (start -1.27 -2.413) (end 0 -2.667) (stroke (width 0.1524) (type default)) (fill (type none)))
        (rectangle (start -1.27 0.127) (end 0 -0.127) (stroke (width 0.1524) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 0) (xy 0.508 0)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 -2.54) (xy 0.508 -2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (pin passive line (at 3.81 0 180) (length 2.54) (name "Pin_1" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 3.81 -2.54 180) (length 2.54) (name "Pin_2" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )"""

def lib_symbol_conn_01x15_socket():
    pins = ""
    for i in range(15):
        y = 17.78 - i * 2.54
        pins += f'        (pin passive line (at 3.81 {y:.2f} 180) (length 2.54) (name "Pin_{i+1}" (effects (font (size 1.27 1.27)))) (number "{i+1}" (effects (font (size 1.27 1.27)))))\n'
    rects = ""
    for i in range(15):
        y = 17.78 - i * 2.54
        rects += f'        (rectangle (start -1.27 {y+0.127:.3f}) (end 0 {y-0.127:.3f}) (stroke (width 0.1524) (type default)) (fill (type none)))\n'
        rects += f'        (polyline (pts (xy 1.27 {y:.2f}) (xy 0.508 {y:.2f})) (stroke (width 0) (type default)) (fill (type none)))\n'
    return f"""    (symbol "Connector:Conn_01x15_Socket" (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 20.32 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Conn_01x15_Socket" (at 0 -38.1 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "ki_keywords" "connector" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Conn_01x15_Socket_1_1"
{rects}{pins}      )
    )"""

def lib_symbol_conn_01x04():
    return """    (symbol "Connector:Conn_01x04_Pin" (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 5.08 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Conn_01x04_Pin" (at 0 -10.16 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "ki_keywords" "connector" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Conn_01x04_Pin_1_1"
        (rectangle (start -1.27 2.667) (end 0 2.413) (stroke (width 0.1524) (type default)) (fill (type none)))
        (rectangle (start -1.27 0.127) (end 0 -0.127) (stroke (width 0.1524) (type default)) (fill (type none)))
        (rectangle (start -1.27 -2.413) (end 0 -2.667) (stroke (width 0.1524) (type default)) (fill (type none)))
        (rectangle (start -1.27 -4.953) (end 0 -5.207) (stroke (width 0.1524) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 2.54) (xy 0.508 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 0) (xy 0.508 0)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 -2.54) (xy 0.508 -2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 -5.08) (xy 0.508 -5.08)) (stroke (width 0) (type default)) (fill (type none)))
        (pin passive line (at 3.81 2.54 180) (length 2.54) (name "Pin_1" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 3.81 0 180) (length 2.54) (name "Pin_2" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 3.81 -2.54 180) (length 2.54) (name "Pin_3" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 3.81 -5.08 180) (length 2.54) (name "Pin_4" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
      )
    )"""

def lib_symbol_power_gnd():
    return """    (symbol "power:GND" (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 -6.35 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "GND" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "ki_keywords" "global power" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "GND_0_1"
        (polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 0)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "GND_1_1"
        (pin power_in line (at 0 0 270) (length 0) (name "GND" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      )
    )"""

def lib_symbol_power_5v():
    return """    (symbol "power:+5V" (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 -3.81 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "+5V" (at 0 3.556 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "ki_keywords" "global power" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "+5V_0_1"
        (polyline (pts (xy -0.762 1.27) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 0) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "+5V_1_1"
        (pin power_in line (at 0 0 90) (length 0) (name "+5V" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      )
    )"""

def lib_symbol_power_batt():
    return """    (symbol "power:+BATT" (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 -3.81 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "+BATT" (at 0 3.556 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "ki_keywords" "global power" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "+BATT_0_1"
        (polyline (pts (xy -0.762 1.27) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 0) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "+BATT_1_1"
        (pin power_in line (at 0 0 90) (length 0) (name "+BATT" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      )
    )"""

# ---------------------------------------------------------------------------
# Schematic symbol instances
# ---------------------------------------------------------------------------

def sch_gnd(x, y):
    """Place a GND power symbol."""
    ref = _next_ref("#PWR")
    uid = gen_uuid()
    return f"""    (symbol (lib_id "power:GND") (at {x:.2f} {y:.2f} 0)
      (unit 1)
      (in_bom yes)
      (on_board yes)
      (uuid "{uid}")
      (property "Reference" "{ref}" (at 0 -2.54 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "GND" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (instances
        (project "led-driver-board"
          (path "/" (reference "{ref}") (unit 1))
        )
      )
    )"""

def sch_power(x, y, symbol, net_name):
    """Place a power symbol (+5V, +BATT)."""
    ref = _next_ref("#PWR")
    uid = gen_uuid()
    return f"""    (symbol (lib_id "power:{symbol}") (at {x:.2f} {y:.2f} 0)
      (unit 1)
      (in_bom yes)
      (on_board yes)
      (uuid "{uid}")
      (property "Reference" "{ref}" (at 0 2.54 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "{symbol}" (at 0 3.556 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (instances
        (project "led-driver-board"
          (path "/" (reference "{ref}") (unit 1))
        )
      )
    )"""

def sch_net_label(x, y, name, rot=0):
    """Place a net label."""
    uid = gen_uuid()
    at_str = f"(at {x:.2f} {y:.2f} {rot})"
    return f"""    (label "{name}" {at_str} (effects (font (size 1.27 1.27)))
      (uuid "{uid}")
    )"""

def sch_wire(x1, y1, x2, y2):
    """Place a wire segment."""
    return f"""    (wire (pts (xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f}))
      (stroke (width 0) (type default))
      (uuid "{gen_uuid()}")
    )"""

def sch_text(x, y, text):
    """Place a text annotation."""
    return f"""    (text "{text}" (at {x:.2f} {y:.2f} 0) (effects (font (size 2.54 2.54)))
      (uuid "{gen_uuid()}")
    )"""

# ---------------------------------------------------------------------------
# Schematic generation — channel block
# ---------------------------------------------------------------------------

def generate_channel(ch, x, y):
    """Generate one MOSFET channel block at (x, y).

    Layout (top to bottom):
      GPIO label at top
      R_gate (100R) vertical
      junction → gate of MOSFET
      R_pulldown (10K) to GND (parallel to gate)
      MOSFET: Gate-Source-Drain
      Drain connects to output connector pin 2
      Connector pin 1 = +BATT
    """
    parts = []
    wires = []

    ch_num = ch["num"]
    gpio = ch["gpio"]
    name = ch["name"]

    # Net label: GPIO_xx at top
    parts.append(sch_net_label(x, y, f"GPIO_{gpio}"))

    # Wire from label down to gate resistor
    wires.append(sch_wire(x, y, x, y + 2.54))

    # R_gate (vertical, pin1=top, pin2=bottom)
    r_gate_ref = _next_ref("R")
    r_gate_y = y + 2.54 + 3.81  # center of resistor
    parts.append(f"""    (symbol (lib_id "Device:R") (at {x:.2f} {r_gate_y:.2f} 0)
      (unit 1)
      (in_bom yes)
      (on_board yes)
      (uuid "{gen_uuid()}")
      (property "Reference" "{r_gate_ref}" (at 2.54 0 0) (effects (font (size 1.27 1.27))))
      (property "Value" "100" (at -2.54 0 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at -1.778 0 90) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (instances
        (project "led-driver-board"
          (path "/" (reference "{r_gate_ref}") (unit 1))
        )
      )
    )""")

    # Junction point below R_gate
    junc_y = r_gate_y + 3.81

    # MOSFET placed to the right, gate pin at mosfet_cx - 5.08
    mosfet_cx = x + 10.16
    mosfet_cy = junc_y
    # Wire from junction right to MOSFET gate pin
    wires.append(sch_wire(x, junc_y, mosfet_cx - 5.08, junc_y))

    # MOSFET
    q_ref = _next_ref("Q")
    parts.append(f"""    (symbol (lib_id "Device:Q_NMOS_GSD") (at {mosfet_cx:.2f} {mosfet_cy:.2f} 0)
      (unit 1)
      (in_bom yes)
      (on_board yes)
      (uuid "{gen_uuid()}")
      (property "Reference" "{q_ref}" (at 5.08 1.905 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Value" "AO3400A" (at 5.08 0 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Footprint" "Package_TO_SOT_SMD:SOT-23" (at 5.08 -1.905 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (instances
        (project "led-driver-board"
          (path "/" (reference "{q_ref}") (unit 1))
        )
      )
    )""")

    # R_pulldown (10K) from junction down to GND
    r_pd_ref = _next_ref("R")
    r_pd_y = junc_y + 7.62
    parts.append(f"""    (symbol (lib_id "Device:R") (at {x:.2f} {r_pd_y:.2f} 0)
      (unit 1)
      (in_bom yes)
      (on_board yes)
      (uuid "{gen_uuid()}")
      (property "Reference" "{r_pd_ref}" (at 2.54 0 0) (effects (font (size 1.27 1.27))))
      (property "Value" "10K" (at -2.54 0 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at -1.778 0 90) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (instances
        (project "led-driver-board"
          (path "/" (reference "{r_pd_ref}") (unit 1))
        )
      )
    )""")
    # Wire from junction down to R_pulldown top
    wires.append(sch_wire(x, junc_y, x, r_pd_y - 3.81))

    # GND below pulldown
    gnd_y = r_pd_y + 3.81 + 2.54
    parts.append(sch_gnd(x, gnd_y))
    wires.append(sch_wire(x, r_pd_y + 3.81, x, gnd_y))

    # MOSFET Source (pin 2) goes to GND: source at mosfet_cx + 2.54, mosfet_cy + 5.08 (down)
    # Actually Q_NMOS_GSD pin 2 (Source) is at +2.54, -5.08 from center
    src_x = mosfet_cx + 2.54
    src_y = mosfet_cy + 5.08
    gnd2_y = src_y + 2.54
    parts.append(sch_gnd(src_x, gnd2_y))
    wires.append(sch_wire(src_x, src_y, src_x, gnd2_y))

    # MOSFET Drain (pin 3) goes up: at mosfet_cx + 2.54, mosfet_cy - 5.08
    drain_x = mosfet_cx + 2.54
    drain_y = mosfet_cy - 5.08

    # Net label for drain
    parts.append(sch_net_label(drain_x, drain_y, f"DRAIN_{ch_num}", 90))

    # Output connector (JST-XH 2-pin) — placed to the right of drain
    conn_x = drain_x + 10.16
    conn_y = drain_y - 2.54
    j_ref = _next_ref("J")
    parts.append(f"""    (symbol (lib_id "Connector:Conn_01x02_Pin") (at {conn_x:.2f} {conn_y:.2f} 180)
      (unit 1)
      (in_bom yes)
      (on_board yes)
      (uuid "{gen_uuid()}")
      (property "Reference" "{j_ref}" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Ch{ch_num} {name}" (at 0 -5.08 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (instances
        (project "led-driver-board"
          (path "/" (reference "{j_ref}") (unit 1))
        )
      )
    )""")

    # Connector pin 1 (+BATT) — at conn_x - 3.81, conn_y (mirrored)
    # With 180 rotation, pin 1 is at conn_x - 3.81, conn_y and pin 2 at conn_x - 3.81, conn_y + 2.54
    batt_x = conn_x - 3.81
    parts.append(sch_power(batt_x, conn_y - 2.54, "+BATT", "+BATT"))
    wires.append(sch_wire(batt_x, conn_y - 2.54, batt_x, conn_y))

    # Connector pin 2 (drain net) — wire from DRAIN label to connector
    drain_label_x = conn_x - 3.81
    drain_label_y = conn_y + 2.54
    parts.append(sch_net_label(drain_label_x, drain_label_y, f"DRAIN_{ch_num}", 90))

    return "\n".join(parts), "\n".join(wires)

# ---------------------------------------------------------------------------
# Schematic generation — power section
# ---------------------------------------------------------------------------

def generate_power_section(x, y):
    """Screw terminal → MP1584EN module → caps → power nets."""
    parts = []
    wires = []

    # Title text
    parts.append(sch_text(x, y - 5.08, "Power Supply"))

    # Screw terminal J1 (2-pin)
    j_ref = _next_ref("J")
    parts.append(f"""    (symbol (lib_id "Connector:Conn_01x02_Pin") (at {x:.2f} {y:.2f} 180)
      (unit 1)
      (in_bom yes)
      (on_board yes)
      (uuid "{gen_uuid()}")
      (property "Reference" "{j_ref}" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Battery" (at 0 -5.08 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "TerminalBlock:TerminalBlock_bornier-2_P5.08mm" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (instances
        (project "led-driver-board"
          (path "/" (reference "{j_ref}") (unit 1))
        )
      )
    )""")

    # Pin 1 = Battery+ → +BATT power symbol
    batt_pin_x = x - 3.81
    parts.append(sch_power(batt_pin_x, y - 2.54, "+BATT", "+BATT"))
    wires.append(sch_wire(batt_pin_x, y - 2.54, batt_pin_x, y))

    # Pin 2 = GND
    gnd_pin_y = y + 2.54
    parts.append(sch_gnd(batt_pin_x, gnd_pin_y + 2.54))
    wires.append(sch_wire(batt_pin_x, gnd_pin_y, batt_pin_x, gnd_pin_y + 2.54))

    # MP1584EN module (4-pin connector: IN+, IN-, OUT+, OUT-)
    mp_x = x + 25.4
    mp_y = y
    mp_ref = _next_ref("J")
    parts.append(f"""    (symbol (lib_id "Connector:Conn_01x04_Pin") (at {mp_x:.2f} {mp_y:.2f} 180)
      (unit 1)
      (in_bom yes)
      (on_board yes)
      (uuid "{gen_uuid()}")
      (property "Reference" "{mp_ref}" (at 0 5.08 0) (effects (font (size 1.27 1.27))))
      (property "Value" "MP1584EN" (at 0 -10.16 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (instances
        (project "led-driver-board"
          (path "/" (reference "{mp_ref}") (unit 1))
        )
      )
    )""")

    # MP1584EN pins (180 rotation):
    # Pin 1 (IN+) at mp_x - 3.81, mp_y - 2.54 → +BATT
    mp_pin_x = mp_x - 3.81
    parts.append(sch_power(mp_pin_x, mp_y - 2.54 - 2.54, "+BATT", "+BATT"))
    wires.append(sch_wire(mp_pin_x, mp_y - 2.54 - 2.54, mp_pin_x, mp_y - 2.54))
    # Pin 2 (IN-) at mp_pin_x, mp_y → GND
    # With 180 rotation: pin1 at y+2.54, pin2 at y, pin3 at y-2.54, pin4 at y-5.08
    # Let me recalculate for the 4-pin connector with 180 rotation:
    # Original pins: pin1 at +2.54, pin2 at 0, pin3 at -2.54, pin4 at -5.08
    # With 180 rotation the y-offsets flip: pin1 at -2.54, pin2 at 0, pin3 at +2.54, pin4 at +5.08
    # And x offset: pins are at x-3.81 (flipped from x+3.81)
    parts.append(sch_gnd(mp_pin_x, mp_y + 2.54))
    wires.append(sch_wire(mp_pin_x, mp_y, mp_pin_x, mp_y + 2.54))

    # Pin 3 (OUT+) → +5V
    parts.append(sch_power(mp_pin_x, mp_y + 2.54 - 7.62, "+5V", "+5V"))
    wires.append(sch_wire(mp_pin_x, mp_y + 2.54 - 7.62, mp_pin_x, mp_y + 2.54 - 5.08))
    # Pin 4 (OUT-) → GND
    parts.append(sch_gnd(mp_pin_x, mp_y + 5.08 + 2.54))
    wires.append(sch_wire(mp_pin_x, mp_y + 5.08, mp_pin_x, mp_y + 5.08 + 2.54))

    # Input cap C1 (22uF) between +BATT and GND, near MP1584EN input
    cap_x = mp_x + 12.7
    c1_ref = _next_ref("C")
    parts.append(f"""    (symbol (lib_id "Device:C") (at {cap_x:.2f} {mp_y:.2f} 0)
      (unit 1)
      (in_bom yes)
      (on_board yes)
      (uuid "{gen_uuid()}")
      (property "Reference" "{c1_ref}" (at 2.54 0 0) (effects (font (size 1.27 1.27))))
      (property "Value" "22uF" (at -2.54 0 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Capacitor_SMD:C_0805_2012Metric" (at 0.9652 -3.81 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (instances
        (project "led-driver-board"
          (path "/" (reference "{c1_ref}") (unit 1))
        )
      )
    )""")
    parts.append(sch_power(cap_x, mp_y - 3.81 - 2.54, "+BATT", "+BATT"))
    wires.append(sch_wire(cap_x, mp_y - 3.81, cap_x, mp_y - 3.81 - 2.54))
    parts.append(sch_gnd(cap_x, mp_y + 3.81 + 2.54))
    wires.append(sch_wire(cap_x, mp_y + 3.81, cap_x, mp_y + 3.81 + 2.54))

    # Output cap C2 (22uF) between +5V and GND
    cap2_x = cap_x + 10.16
    c2_ref = _next_ref("C")
    parts.append(f"""    (symbol (lib_id "Device:C") (at {cap2_x:.2f} {mp_y:.2f} 0)
      (unit 1)
      (in_bom yes)
      (on_board yes)
      (uuid "{gen_uuid()}")
      (property "Reference" "{c2_ref}" (at 2.54 0 0) (effects (font (size 1.27 1.27))))
      (property "Value" "22uF" (at -2.54 0 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Capacitor_SMD:C_0805_2012Metric" (at 0.9652 -3.81 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (instances
        (project "led-driver-board"
          (path "/" (reference "{c2_ref}") (unit 1))
        )
      )
    )""")
    parts.append(sch_power(cap2_x, mp_y - 3.81 - 2.54, "+5V", "+5V"))
    wires.append(sch_wire(cap2_x, mp_y - 3.81, cap2_x, mp_y - 3.81 - 2.54))
    parts.append(sch_gnd(cap2_x, mp_y + 3.81 + 2.54))
    wires.append(sch_wire(cap2_x, mp_y + 3.81, cap2_x, mp_y + 3.81 + 2.54))

    return "\n".join(parts), "\n".join(wires)

# ---------------------------------------------------------------------------
# Schematic generation — ESP32 headers
# ---------------------------------------------------------------------------

def generate_esp32_headers(x, y):
    """Two 1x15 pin sockets representing ESP32 dev board."""
    parts = []
    wires = []

    parts.append(sch_text(x + 5.08, y - 22.86, "ESP32 Dev Board"))

    # Left header
    j_left_ref = _next_ref("J")
    parts.append(f"""    (symbol (lib_id "Connector:Conn_01x15_Socket") (at {x:.2f} {y:.2f} 0)
      (unit 1)
      (in_bom yes)
      (on_board yes)
      (uuid "{gen_uuid()}")
      (property "Reference" "{j_left_ref}" (at -2.54 0 0) (effects (font (size 1.27 1.27))))
      (property "Value" "ESP32_Left" (at -2.54 -38.1 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Connector_PinSocket_2.54mm:PinSocket_1x15_P2.54mm_Vertical" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (instances
        (project "led-driver-board"
          (path "/" (reference "{j_left_ref}") (unit 1))
        )
      )
    )""")

    # Right header — 25.4mm to the right
    j_right_ref = _next_ref("J")
    right_x = x + 25.4
    parts.append(f"""    (symbol (lib_id "Connector:Conn_01x15_Socket") (at {right_x:.2f} {y:.2f} 180)
      (unit 1)
      (in_bom yes)
      (on_board yes)
      (uuid "{gen_uuid()}")
      (property "Reference" "{j_right_ref}" (at 2.54 0 0) (effects (font (size 1.27 1.27))))
      (property "Value" "ESP32_Right" (at 2.54 -38.1 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Connector_PinSocket_2.54mm:PinSocket_1x15_P2.54mm_Vertical" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (instances
        (project "led-driver-board"
          (path "/" (reference "{j_right_ref}") (unit 1))
        )
      )
    )""")

    # ESP32 DevKit 30-pin typical pinout (left side top to bottom):
    # 3V3, EN, GPIO36(VP), GPIO39(VN), GPIO34, GPIO35, GPIO32, GPIO33,
    # GPIO25, GPIO26, GPIO27, GPIO14, GPIO12, GND, GPIO13
    # Right side top to bottom:
    # Vin, GND, GPIO23, GPIO22, GPIO1(TX), GPIO3(RX), GPIO21, (NC),
    # GPIO19, GPIO18, GPIO5, GPIO17, GPIO16, GPIO4, GPIO0, GPIO2, GPIO15, GND

    # Left header labels (pin 1 = top = pin at y + 17.78)
    left_labels = [
        ("3V3", None), ("EN", None), ("GPIO36", None), ("GPIO39", None),
        ("GPIO34", None), ("GPIO35", None), ("GPIO32", None), ("GPIO33", None),
        ("GPIO25", "GPIO_25"), ("GPIO26", "GPIO_26"), ("GPIO27", None),
        ("GPIO14", None), ("GPIO12", None), ("GND_L", "GND_LABEL"),
        ("GPIO13", None),
    ]

    # Add net labels for GPIO pins that we use
    for i, (label, net) in enumerate(left_labels):
        pin_y = y + 17.78 - i * 2.54
        pin_x = x + 3.81
        if net and net.startswith("GPIO_"):
            parts.append(sch_net_label(pin_x + 2.54, pin_y, net))
            wires.append(sch_wire(pin_x, pin_y, pin_x + 2.54, pin_y))
        elif label == "GND_L":
            parts.append(sch_gnd(pin_x + 5.08, pin_y))
            wires.append(sch_wire(pin_x, pin_y, pin_x + 5.08, pin_y))

    # Right header labels (180 rotation - pin 1 at bottom)
    # With 180 rotation on the 15-pin socket: pin layout is flipped
    # Pin 1 at right_x + 3.81 (due to 180), y - 17.78
    right_labels = [
        ("Vin", "+5V"), ("GND_R1", "GND_LABEL"),
        ("GPIO23", "GPIO_23"), ("GPIO22", "GPIO_22"),
        ("TX", None), ("RX", None),
        ("GPIO21", "GPIO_21"), ("NC", None),
        ("GPIO19", "GPIO_19"), ("GPIO18", "GPIO_18"),
        ("GPIO5", None), ("GPIO17", "GPIO_17"),
        ("GPIO16", "GPIO_16"), ("GPIO4", None),
        ("GPIO2", "GPIO_2"),
    ]

    for i, (label, net) in enumerate(right_labels):
        # 180 rotation: pins go from bottom (pin1) to top (pin15)
        # Pin positions: pin1 at y-17.78, pin15 at y+17.78
        pin_y = y - 17.78 + i * 2.54
        pin_x = right_x - 3.81
        if net == "+5V":
            parts.append(sch_power(pin_x - 5.08, pin_y - 2.54, "+5V", "+5V"))
            wires.append(sch_wire(pin_x, pin_y, pin_x - 5.08, pin_y))
            wires.append(sch_wire(pin_x - 5.08, pin_y - 2.54, pin_x - 5.08, pin_y))
        elif net == "GND_LABEL":
            parts.append(sch_gnd(pin_x - 5.08, pin_y))
            wires.append(sch_wire(pin_x, pin_y, pin_x - 5.08, pin_y))
        elif net and net.startswith("GPIO_"):
            parts.append(sch_net_label(pin_x - 2.54, pin_y, net, 180))
            wires.append(sch_wire(pin_x, pin_y, pin_x - 2.54, pin_y))

    # GPIO2 net label for status LED
    # Already handled by GPIO_2 label on GPIO2 pin

    return "\n".join(parts), "\n".join(wires)

# ---------------------------------------------------------------------------
# Schematic generation — status LED
# ---------------------------------------------------------------------------

def generate_status_led(x, y):
    """GPIO2 → 1K resistor → LED → GND."""
    parts = []
    wires = []

    parts.append(sch_text(x, y - 5.08, "Status LED"))

    # GPIO_2 net label
    parts.append(sch_net_label(x, y, "GPIO_2"))

    # Wire down to resistor
    wires.append(sch_wire(x, y, x, y + 2.54))

    # 1K resistor
    r_ref = _next_ref("R")
    r_y = y + 2.54 + 3.81
    parts.append(f"""    (symbol (lib_id "Device:R") (at {x:.2f} {r_y:.2f} 0)
      (unit 1)
      (in_bom yes)
      (on_board yes)
      (uuid "{gen_uuid()}")
      (property "Reference" "{r_ref}" (at 2.54 0 0) (effects (font (size 1.27 1.27))))
      (property "Value" "1K" (at -2.54 0 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at -1.778 0 90) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (instances
        (project "led-driver-board"
          (path "/" (reference "{r_ref}") (unit 1))
        )
      )
    )""")

    # LED — placed so anode pin touches resistor bottom pin
    led_y = r_y + 3.81 + 3.81

    # LED (horizontal, rotated 90 to be vertical: anode at top, cathode at bottom)
    d_ref = _next_ref("D")
    parts.append(f"""    (symbol (lib_id "Device:LED") (at {x:.2f} {led_y:.2f} 90)
      (unit 1)
      (in_bom yes)
      (on_board yes)
      (uuid "{gen_uuid()}")
      (property "Reference" "{d_ref}" (at 2.54 0 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Green" (at -2.54 0 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "LED_SMD:LED_0805_2012Metric" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (instances
        (project "led-driver-board"
          (path "/" (reference "{d_ref}") (unit 1))
        )
      )
    )""")

    # GND below LED
    gnd_y = led_y + 3.81 + 2.54
    parts.append(sch_gnd(x, gnd_y))
    wires.append(sch_wire(x, led_y + 3.81, x, gnd_y))

    return "\n".join(parts), "\n".join(wires)

# ---------------------------------------------------------------------------
# Full schematic assembly
# ---------------------------------------------------------------------------

def generate_schematic():
    """Assemble the complete .kicad_sch file."""
    all_parts = []
    all_wires = []

    # Power section at top-left
    p, w = generate_power_section(30.48, 40.64)
    all_parts.append(p)
    all_wires.append(w)

    # ESP32 headers in top-center
    p, w = generate_esp32_headers(127.0, 40.64)
    all_parts.append(p)
    all_wires.append(w)

    # Status LED near ESP32
    p, w = generate_status_led(180.34, 40.64)
    all_parts.append(p)
    all_wires.append(w)

    # Channels in two rows
    # Row 1: channels 1-5
    for i, ch in enumerate(CHANNELS[:5]):
        cx = 25.4 + i * 50.8
        cy = 114.3
        p, w = generate_channel(ch, cx, cy)
        all_parts.append(p)
        all_wires.append(w)

    # Row 2: channels 6-9
    for i, ch in enumerate(CHANNELS[5:]):
        cx = 25.4 + i * 50.8
        cy = 200.66
        p, w = generate_channel(ch, cx, cy)
        all_parts.append(p)
        all_wires.append(w)

    # Build lib_symbols
    lib_symbols = "\n".join([
        lib_symbol_resistor(),
        lib_symbol_nmos(),
        lib_symbol_capacitor(),
        lib_symbol_led(),
        lib_symbol_conn_01x02(),
        lib_symbol_conn_01x04(),
        lib_symbol_conn_01x15_socket(),
        lib_symbol_power_gnd(),
        lib_symbol_power_5v(),
        lib_symbol_power_batt(),
    ])

    parts_str = "\n".join(all_parts)
    wires_str = "\n".join(all_wires)

    sch = f"""(kicad_sch
  (version {SCH_VERSION})
  (generator "{GENERATOR}")
  (generator_version "8.0")
  (uuid "{gen_uuid()}")
  (paper "A3")
  (lib_symbols
{lib_symbols}
  )
{parts_str}
{wires_str}
  (sheet_instances
    (path "/" (page "1"))
  )
)
"""
    return sch

# ---------------------------------------------------------------------------
# PCB generation
# ---------------------------------------------------------------------------

def pcb_footprint(ref, footprint_lib, x, y, rot=0, value="", pads=None, layer="F.Cu"):
    """Generate a footprint placement on the PCB.

    pads: list of (pad_num, net_name, rel_x, rel_y, shape, size_x, size_y, pad_type, layers[, drill])
    """
    uid = gen_uuid()
    rot_str = f" {rot}" if rot else ""
    pad_strs = []
    if pads:
        for p in pads:
            pad_num, net_name, px, py, shape, sx, sy, pad_type, pad_layers = p[:9]
            drill = p[9] if len(p) > 9 else None
            net_id = NET_MGR.get(net_name) if net_name else 0
            net_section = f'(net {net_id} "{net_name}")'
            if pad_type == "thru_hole" and drill:
                drill_str = f" (drill {drill:.1f})"
            else:
                drill_str = ""
            pad_strs.append(
                f'    (pad "{pad_num}" {pad_type} {shape} (at {px:.3f} {py:.3f}) '
                f'(size {sx:.3f} {sy:.3f}){drill_str} '
                f'(layers {pad_layers}) {net_section})'
            )
    pads_block = "\n".join(pad_strs)

    return f"""  (footprint "{footprint_lib}"
    (layer "{layer}")
    (uuid "{uid}")
    (at {x:.2f} {y:.2f}{rot_str})
    (property "Reference" "{ref}" (at 0 -2.5 0) (layer "F.SilkS") (uuid "{gen_uuid()}")
      (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "{value}" (at 0 2.5 0) (layer "F.Fab") (uuid "{gen_uuid()}")
      (effects (font (size 1 1) (thickness 0.15))))
{pads_block}
  )"""

def pcb_smd_pads(pad_defs):
    """Generate SMD pad entries.
    pad_defs: list of (num, net, rx, ry, sx, sy)
    """
    pads = []
    for num, net, rx, ry, sx, sy in pad_defs:
        pads.append((num, net, rx, ry, "rect", sx, sy, "smd", '"F.Cu" "F.Paste" "F.Mask"'))
    return pads

def pcb_thru_pads(pad_defs, drill=1.0):
    """Generate through-hole pad entries.
    pad_defs: list of (num, net, rx, ry, sx, sy)
    """
    pads = []
    for num, net, rx, ry, sx, sy in pad_defs:
        pads.append((num, net, rx, ry, "circle", sx, sy, "thru_hole", '"*.Cu" "*.Mask"', drill))
    return pads

def generate_pcb():
    """Generate the .kicad_pcb file with board outline + placed footprints."""
    # Board dimensions: 60mm x 55mm (fits ESP32 pin sockets + MOSFET channels)
    board_w = 60.0
    board_h = 55.0
    origin_x = 100.0
    origin_y = 80.0

    footprints = []

    # -- Board outline --
    edge_cuts = f"""  (gr_rect (start {origin_x:.2f} {origin_y:.2f}) (end {origin_x + board_w:.2f} {origin_y + board_h:.2f})
    (stroke (width 0.15) (type default)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))"""

    # -- Screw terminal J1 (top-left) --
    j1_x = origin_x + 5.08
    j1_y = origin_y + 5.08
    footprints.append(pcb_footprint("J1", "TerminalBlock:TerminalBlock_bornier-2_P5.08mm",
                                     j1_x, j1_y, value="Battery",
                                     pads=pcb_thru_pads([
                                         ("1", "+BATT", 0, 0, 1.7, 1.7),
                                         ("2", "GND", 5.08, 0, 1.7, 1.7),
                                     ])))

    # -- MP1584EN module (4-pin header, top center) --
    mp_x = origin_x + 20.0
    mp_y = origin_y + 5.08
    footprints.append(pcb_footprint("J11", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
                                     mp_x, mp_y, value="MP1584EN",
                                     pads=pcb_thru_pads([
                                         ("1", "+BATT", 0, 0, 1.7, 1.7),
                                         ("2", "GND", 2.54, 0, 1.7, 1.7),
                                         ("3", "+5V", 5.08, 0, 1.7, 1.7),
                                         ("4", "GND", 7.62, 0, 1.7, 1.7),
                                     ])))

    # -- Input cap C1 --
    c1_x = origin_x + 35.0
    c1_y = origin_y + 5.08
    footprints.append(pcb_footprint("C1", "Capacitor_SMD:C_0805_2012Metric",
                                     c1_x, c1_y, value="22uF",
                                     pads=pcb_smd_pads([
                                         ("1", "+BATT", -1.0, 0, 1.0, 1.25),
                                         ("2", "GND", 1.0, 0, 1.0, 1.25),
                                     ])))

    # -- Output cap C2 --
    c2_x = origin_x + 42.0
    c2_y = origin_y + 5.08
    footprints.append(pcb_footprint("C2", "Capacitor_SMD:C_0805_2012Metric",
                                     c2_x, c2_y, value="22uF",
                                     pads=pcb_smd_pads([
                                         ("1", "+5V", -1.0, 0, 1.0, 1.25),
                                         ("2", "GND", 1.0, 0, 1.0, 1.25),
                                     ])))

    # -- ESP32 pin sockets (two 1x15, 25.4mm apart) --
    # Centered horizontally
    esp_left_x = origin_x + 12.7
    esp_y = origin_y + 15.0
    esp_right_x = esp_left_x + 25.4

    left_pads = []
    for i in range(15):
        left_pads.append((str(i + 1), "", 0, i * 2.54, 1.7, 1.7))
    footprints.append(pcb_footprint("J12", "Connector_PinSocket_2.54mm:PinSocket_1x15_P2.54mm_Vertical",
                                     esp_left_x, esp_y, value="ESP32_Left",
                                     pads=pcb_thru_pads(left_pads)))

    right_pads = []
    for i in range(15):
        right_pads.append((str(i + 1), "", 0, i * 2.54, 1.7, 1.7))
    footprints.append(pcb_footprint("J13", "Connector_PinSocket_2.54mm:PinSocket_1x15_P2.54mm_Vertical",
                                     esp_right_x, esp_y, value="ESP32_Right",
                                     pads=pcb_thru_pads(right_pads)))

    # -- Status LED + resistor (near ESP32) --
    led_x = origin_x + 50.0
    led_y = origin_y + 15.0
    footprints.append(pcb_footprint("R19", "Resistor_SMD:R_0603_1608Metric",
                                     led_x, led_y, value="1K",
                                     pads=pcb_smd_pads([
                                         ("1", "GPIO_2", -0.8, 0, 0.9, 0.95),
                                         ("2", "STATUS_LED", 0.8, 0, 0.9, 0.95),
                                     ])))
    footprints.append(pcb_footprint("D1", "LED_SMD:LED_0805_2012Metric",
                                     led_x + 4.0, led_y, value="Green",
                                     pads=pcb_smd_pads([
                                         ("1", "STATUS_LED", -1.0, 0, 1.0, 1.25),
                                         ("2", "GND", 1.0, 0, 1.0, 1.25),
                                     ])))

    # -- 9 MOSFET channels --
    # MOSFETs in a row near bottom, JST connectors below them
    mosfet_y = origin_y + board_h - 15.0
    jst_y = origin_y + board_h - 5.0
    channel_spacing = 6.0
    ch_start_x = origin_x + 3.0

    for i, ch in enumerate(CHANNELS):
        ch_x = ch_start_x + i * channel_spacing
        ch_num = ch["num"]
        gpio = ch["gpio"]

        # Gate resistor (100R)
        r_gate_ref = f"R{i * 2 + 1}"
        footprints.append(pcb_footprint(
            r_gate_ref, "Resistor_SMD:R_0603_1608Metric",
            ch_x, mosfet_y - 5.0, 90, value="100",
            pads=pcb_smd_pads([
                ("1", f"GPIO_{gpio}", 0, -0.8, 0.9, 0.95),
                ("2", f"GATE_{ch_num}", 0, 0.8, 0.9, 0.95),
            ])))

        # Pulldown resistor (10K)
        r_pd_ref = f"R{i * 2 + 2}"
        footprints.append(pcb_footprint(
            r_pd_ref, "Resistor_SMD:R_0603_1608Metric",
            ch_x + 2.0, mosfet_y - 5.0, 90, value="10K",
            pads=pcb_smd_pads([
                ("1", f"GATE_{ch_num}", 0, -0.8, 0.9, 0.95),
                ("2", "GND", 0, 0.8, 0.9, 0.95),
            ])))

        # MOSFET (SOT-23: pin1=Gate, pin2=Source, pin3=Drain)
        q_ref = f"Q{ch_num}"
        footprints.append(pcb_footprint(
            q_ref, "Package_TO_SOT_SMD:SOT-23",
            ch_x + 1.0, mosfet_y, 0, value="AO3400A",
            pads=pcb_smd_pads([
                ("1", f"GATE_{ch_num}", -1.1, 0.95, 0.6, 0.7),
                ("2", "GND", 1.1, 0.95, 0.6, 0.7),
                ("3", f"DRAIN_{ch_num}", 1.1, -0.95, 0.6, 0.7),
            ])))

        # JST-XH 2-pin output connector
        j_ref = f"J{ch_num + 1}"  # J2-J10
        footprints.append(pcb_footprint(
            j_ref, "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical",
            ch_x + 0.5, jst_y, 0, value=f"Ch{ch_num}",
            pads=pcb_thru_pads([
                ("1", "+BATT", 0, 0, 1.7, 1.7),
                ("2", f"DRAIN_{ch_num}", 2.5, 0, 1.7, 1.7),
            ])))

    # -- Net declarations --
    net_lines = []
    for name, nid in sorted(NET_MGR.nets.items(), key=lambda x: x[1]):
        net_lines.append(f'  (net {nid} "{name}")')
    nets_block = "\n".join(net_lines)

    # -- Ground zone on B.Cu --
    zone_uid = gen_uuid()
    gnd_id = NET_MGR.get("GND")
    zone = f"""  (zone (net {gnd_id}) (net_name "GND") (layer "B.Cu") (uuid "{zone_uid}")
    (hatch edge 0.5)
    (connect_pads (clearance 0.3))
    (min_thickness 0.25)
    (filled_areas_thickness no)
    (fill yes (thermal_gap 0.5) (thermal_bridge_width 0.5))
    (polygon (pts
      (xy {origin_x:.2f} {origin_y:.2f})
      (xy {origin_x + board_w:.2f} {origin_y:.2f})
      (xy {origin_x + board_w:.2f} {origin_y + board_h:.2f})
      (xy {origin_x:.2f} {origin_y + board_h:.2f})
    ))
  )"""

    footprints_block = "\n".join(footprints)

    pcb = f"""(kicad_pcb
  (version {PCB_VERSION})
  (generator "{GENERATOR}")
  (generator_version "8.0")
  (general
    (thickness 1.6)
    (legacy_teardrops no)
  )
  (paper "A4")
  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user "B.Mask")
    (39 "F.Mask" user "F.Mask")
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1")
    (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user)
    (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user "B.Fabrication")
    (49 "F.Fab" user "F.Fabrication")
    (50 "User.1" user)
    (51 "User.2" user)
  )
  (setup
    (pad_to_mask_clearance 0)
    (allow_soldermask_bridges_in_footprints no)
    (pcbplotparams
      (layerselection 0x00010fc_ffffffff)
      (plot_on_all_layers_selection 0x0000000_00000000)
      (disableapertmacros no)
      (usegerberextensions no)
      (usegerberattributes yes)
      (usegerberadvancedattributes yes)
      (creategerberjobfile yes)
      (dashed_line_dash_ratio 12.000000)
      (dashed_line_gap_ratio 3.000000)
      (svgprecision 4)
      (plotframeref no)
      (viasonmask no)
      (mode 1)
      (useauxorigin no)
      (hpglpennumber 1)
      (hpglpenspeed 20)
      (hpglpendiameter 15.000000)
      (pdf_front_fp_property_popups yes)
      (pdf_back_fp_property_popups yes)
      (dxf_units mm)
      (dxf_use_pcbnew_font yes)
      (psnegative no)
      (psa4output no)
      (plotreference yes)
      (plotvalue yes)
      (plotfptext yes)
      (plotinvisibletext no)
      (sketchpadsonfab no)
      (subtractmaskfromsilk no)
      (outputformat 1)
      (mirror no)
      (drillshape 1)
      (scaleselection 1)
      (outputdirectory "")
    )
  )
{nets_block}
{edge_cuts}
{footprints_block}
{zone}
)
"""
    return pcb

# ---------------------------------------------------------------------------
# Project file
# ---------------------------------------------------------------------------

def generate_project():
    """Generate the .kicad_pro JSON file."""
    proj = {
        "board": {
            "3dviewports": [],
            "design_settings": {
                "defaults": {
                    "board_outline_line_width": 0.15,
                    "copper_line_width": 0.2,
                    "copper_text_size_h": 1.5,
                    "copper_text_size_v": 1.5,
                    "copper_text_thickness": 0.3,
                    "other_line_width": 0.15,
                    "silk_line_width": 0.15,
                    "silk_text_size_h": 1.0,
                    "silk_text_size_v": 1.0,
                    "silk_text_thickness": 0.15,
                },
                "diff_pair_dimensions": [],
                "drc_exclusions": [],
                "rules": {
                    "min_clearance": 0.2,
                    "min_copper_edge_clearance": 0.3,
                    "min_hole_clearance": 0.25,
                    "min_hole_to_hole": 0.25,
                    "min_microvia_diameter": 0.2,
                    "min_microvia_drill": 0.1,
                    "min_resolved_spokes": 2,
                    "min_silk_clearance": 0.0,
                    "min_text_height": 0.8,
                    "min_text_thickness": 0.08,
                    "min_through_hole_diameter": 0.3,
                    "min_track_width": 0.2,
                    "min_via_annular_width": 0.1,
                    "min_via_diameter": 0.5,
                    "solder_mask_to_copper_clearance": 0.0,
                    "use_height_for_length_calcs": True,
                },
                "track_widths": [0.0, 0.25, 0.5, 1.0],
                "via_dimensions": [{"diameter": 0.0, "drill": 0.0}],
                "zones_allow_external_fillets": False,
            },
            "ipc2581": {"dist": "", "distpn": "", "intcomp": "", "mfg": "", "mpn": ""},
            "layer_presets": [],
            "layer_pairs": [],
        },
        "boards": [],
        "cvpcb": {"equivalence_files": []},
        "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
        "meta": {
            "filename": "led-driver-board.kicad_pro",
            "version": 1,
        },
        "net_settings": {
            "classes": [
                {
                    "bus_width": 12,
                    "clearance": 0.2,
                    "diff_pair_gap": 0.25,
                    "diff_pair_via_gap": 0.25,
                    "diff_pair_width": 0.2,
                    "line_style": 0,
                    "microvia_diameter": 0.3,
                    "microvia_drill": 0.1,
                    "name": "Default",
                    "pcb_color": "rgba(0, 0, 0, 0.000)",
                    "schematic_color": "rgba(0, 0, 0, 0.000)",
                    "track_width": 0.25,
                    "via_diameter": 0.6,
                    "via_drill": 0.3,
                    "wire_width": 6,
                }
            ],
            "meta": {"version": 3},
            "net_colors": None,
            "netclass_assignments": None,
            "netclass_patterns": [],
        },
        "pcbnew": {
            "last_paths": {"gencad": "", "idf": "", "netlist": "", "plot": "", "pos_files": "", "specctra_dsn": "", "step": "", "vrml": ""},
            "page_layout_descr_file": "",
        },
        "schematic": {
            "annotate_start_num": 0,
            "bom_export_filename": "",
            "bom_fmt_presets": [],
            "bom_fmt_settings": {"field_delimiter": ",", "keep_line_breaks": False, "keep_tabs": False, "name": "", "ref_delimiter": ",", "ref_range_delimiter": "", "string_delimiter": "\""},
            "connection_grid_size": 50.0,
            "drawing": {
                "dashed_lines_dash_length_ratio": 12.0,
                "dashed_lines_gap_length_ratio": 3.0,
                "default_line_thickness": 6.0,
                "default_text_size": 50.0,
                "field_names": [],
                "intersheets_ref_own_page": False,
                "intersheets_ref_prefix": "",
                "intersheets_ref_short": False,
                "intersheets_ref_show": False,
                "intersheets_ref_suffix": "",
                "junction_size_choice": 3,
                "label_size_ratio": 0.375,
                "operating_point_overlay_i_precision": 3,
                "operating_point_overlay_i_range": "~A",
                "operating_point_overlay_v_precision": 3,
                "operating_point_overlay_v_range": "~V",
                "overbar_offset_ratio": 1.23,
                "pin_symbol_size": 25.0,
                "text_offset_ratio": 0.15,
            },
            "legacy_lib_dir": "",
            "legacy_lib_list": [],
            "meta": {"version": 1},
            "net_format_name": "",
            "page_layout_descr_file": "",
            "plot_directory": "",
            "spice_current_sheet_as_root": False,
            "spice_external_command": "spice \"%I\"",
            "spice_model_current_sheet_as_root": True,
            "spice_save_all_currents": False,
            "spice_save_all_dissipations": False,
            "spice_save_all_voltages": False,
            "subpart_first_id": 65,
            "subpart_id_separator": 0,
        },
        "sheets": [["", ""]],
        "text_variables": {},
    }
    return json.dumps(proj, indent=2) + "\n"

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    HARDWARE_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating KiCad project files...")

    # Project file
    pro_path = HARDWARE_DIR / "led-driver-board.kicad_pro"
    pro_path.write_text(generate_project())
    print(f"  {pro_path}")

    # Schematic
    sch_path = HARDWARE_DIR / "led-driver-board.kicad_sch"
    sch_path.write_text(generate_schematic())
    print(f"  {sch_path}")

    # PCB
    pcb_path = HARDWARE_DIR / "led-driver-board.kicad_pcb"
    pcb_path.write_text(generate_pcb())
    print(f"  {pcb_path}")

    print("Done. Open led-driver-board.kicad_pro in KiCad 8.")


if __name__ == "__main__":
    main()
