---
name: kicad
description: Work with KiCad 8 PCB design files. Use when reading, generating, validating, or modifying KiCad schematics (.kicad_sch), PCB layouts (.kicad_pcb), or project files (.kicad_pro). Provides format reference, validation rules, and generator workflow.
---

# KiCad 8 File Format & Generator Skill

## Source of Truth

`scripts/generate_kicad.py` generates all hardware files. Never hand-edit files in `hardware/` — always modify the generator and re-run.

Hardware design spec: `docs/led-driver-board.md`

## Regenerate Files

```bash
python3 scripts/generate_kicad.py
```

Produces:
- `hardware/led-driver-board.kicad_pro` (project)
- `hardware/led-driver-board.kicad_sch` (schematic)
- `hardware/led-driver-board.kicad_pcb` (PCB layout)

## KiCad 8 S-Expression Format Rules

### Version Headers

- Schematic: `(version 20231120)`
- PCB: `(version 20240108)`

### Schematic — Required Fields

**Symbol instances** must include these fields after `(at ...)` and before `(uuid ...)`:

```
(symbol (lib_id "Device:R") (at 25.40 120.65)
  (unit 1)
  (in_bom yes)
  (on_board yes)
  (uuid "...")
  (property "Reference" "R1" ...)
  ...
  (instances ...)
)
```

**Wires** must include `(stroke ...)` before `(uuid ...)`:

```
(wire (pts (xy 25.40 114.30) (xy 25.40 116.84))
  (stroke (width 0) (type default))
  (uuid "...")
)
```

**Net labels** must include an `(effects ...)` block:

```
(label "NET_NAME" (at x y) (effects (font (size 1.27 1.27)))
  (uuid "...")
)
```

### PCB — Required Fields

**Pads** must always include a `(net N "name")` declaration, even if unconnected. Use `(net 0 "")` for unconnected pads:

```
(pad "1" thru_hole circle (at 0 0) (size 1.7 1.7) (drill 1.0)
  (layers "*.Cu" "*.Mask") (net 0 ""))
```

**Footprints** must include:
- `(layer "F.Cu")` or appropriate layer
- `(uuid "...")`
- `(property "Reference" "R1" ...)` with layer, uuid, and effects
- `(property "Value" "100" ...)` with layer, uuid, and effects

## Verification Commands

After regenerating, verify required fields are present:

```bash
# Count symbol instances with (in_bom) — should match total symbol count
grep -c "in_bom" hardware/led-driver-board.kicad_sch

# Count wires with (stroke) — should match wire count
grep -c "(wire" hardware/led-driver-board.kicad_sch
grep -c "stroke" hardware/led-driver-board.kicad_sch

# Verify no pads are missing (net ...) — should return 0 matches
grep -cP '\(layers.*\) \)$' hardware/led-driver-board.kicad_pcb

# Count unconnected pads — should match expected unconnected count
grep -c '(net 0 "")' hardware/led-driver-board.kicad_pcb
```

## KiCad 9 Compatibility

KiCad 9.0 enforces stricter parsing than KiCad 8. These rules are **required** for KiCad 9 and backward-compatible with KiCad 8:

1. **`(at x y)` must always include angle** — use `(at x y 0)` not `(at x y)` for all `symbol` and `label` elements. KiCad 9 rejects the two-argument form.
2. **`gr_rect` must not have `(fill ...)`** — `(fill (type none))` on `gr_rect` (e.g., Edge.Cuts outline) causes a KiCad 9 parse failure. Omit the fill attribute entirely.

## Common Pitfalls

1. **Missing `(unit)`, `(in_bom)`, `(on_board)`** on symbol instances causes KiCad parser to reject the schematic
2. **Missing `(stroke)` on wires** causes KiCad parser to reject the schematic
3. **Omitting `(net ...)` on unconnected pads** causes KiCad PCB parser to fail — always use `(net 0 "")`
4. **Net manager** (`NET_MGR.get("")`) returns `0` for empty net names, so `(net 0 "")` is correct for unconnected
5. **Packed structs** in the generator use Python f-strings with specific indentation — maintain 6-space indent inside symbol blocks
6. **Missing angle in `(at ...)`** on symbols/labels causes KiCad 9 to reject the file — always use the 3-argument form `(at x y angle)`
7. **`(fill ...)` on `gr_rect`** causes KiCad 9 to reject the PCB — omit fill on graphic rectangles

## Architecture Notes

- 9 MOSFET channels, each with: gate resistor (100R), pulldown (10K), NMOS (AO3400A), JST-XH output
- Power: screw terminal -> MP1584EN buck module -> 5V rail, with input/output caps
- ESP32 DevKit 30-pin via two 1x15 pin sockets
- Status LED on GPIO2 with 1K series resistor
