#!/usr/bin/env python3
"""Generate 48x48 LVGL alpha-map icon arrays from MDI SVG paths.

Usage:
    source scripts/.venv/bin/activate
    python3 scripts/generate_icons.py --size 48 --flip --output src/controller/ui_icons.cpp

Dependencies (install in venv):
    pip install cairosvg Pillow
"""

import argparse
import io
import textwrap

import cairosvg
from PIL import Image, ImageDraw

# MDI SVG path data (viewBox 0 0 24 24, Apache 2.0 license)
# Source: https://pictogrammers.com/library/mdi/
MDI_PATHS = {
    "fog": (
        "M13,4.8C9,4.8 9,19.2 13,19.2C17,19.2 22,16.5 22,12"
        "C22,7.5 17,4.8 13,4.8"
        "M13.1,17.2C12.7,16.8 12,15 12,12C12,9 12.7,7.2 13.1,6.8"
        "C16,6.9 20,8.7 20,12C20,15.3 16,17.1 13.1,17.2"
        "M6,8V11H8C8,11.3 8,11.7 8,12C8,12.3 8,12.7 8,13H6V16"
        "H8.4C8.6,16.7 8.8,17.4 9,18H6V21H4V18H2V16H4V13H2V11"
        "H4V8H2V6H4V3H6V6H9C9,6.1 8.9,6.2 8.9,6.4"
        "C8.7,6.9 8.5,7.4 8.4,8H6Z"
    ),
    "low_beam": (
        "M13,4.8C9,4.8 9,19.2 13,19.2C17,19.2 22,16.5 22,12"
        "C22,7.5 17,4.8 13,4.8"
        "M13.1,17.2C12.7,16.8 12,15 12,12C12,9 12.7,7.2 13.1,6.8"
        "C16,6.9 20,8.7 20,12C20,15.3 15.9,17.1 13.1,17.2"
        "M8,10.5C8,11 7.9,11.5 7.9,12C7.9,12.2 7.9,12.4 7.9,12.6"
        "L2.4,14L1.9,12.1L8,10.5"
        "M2,7L9.4,5.1C9.2,5.4 9,5.8 8.9,6.3C8.8,6.6 8.7,7 8.6,7.4"
        "L2.5,8.9L2,7"
        "M8.2,15.5C8.3,16.2 8.5,16.9 8.7,17.4L2.4,19L1.9,17.1L8.2,15.5Z"
    ),
    "high_beam": (
        "M13,4.8C9,4.8 9,19.2 13,19.2C17,19.2 22,16.5 22,12"
        "C22,7.5 17,4.8 13,4.8"
        "M13.1,17.2C12.7,16.8 12,15 12,12C12,9 12.7,7.2 13.1,6.8"
        "C16,6.9 20,8.7 20,12C20,15.3 16,17.1 13.1,17.2"
        "M2,5H9.5C9.3,5.4 9,5.8 8.9,6.4C8.8,6.6 8.8,6.8 8.7,7"
        "H2V5"
        "M8,11H2V9H8.2C8.1,9.6 8.1,10.3 8,11"
        "M8.7,17C8.9,17.8 9.2,18.4 9.6,19H2.1V17H8.7"
        "M8.2,15H2V13H8C8.1,13.7 8.1,14.4 8.2,15Z"
    ),
}


def svg_path_to_alpha(path_d: str, size: int, flip_h: bool = False) -> Image.Image:
    """Rasterize an SVG path to a grayscale alpha image."""
    # Build SVG document
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'width="{size}" height="{size}">'
        f'<path d="{path_d}" fill="white"/>'
        f"</svg>"
    )
    png_data = cairosvg.svg2png(bytestring=svg.encode(), output_width=size, output_height=size)
    img = Image.open(io.BytesIO(png_data)).convert("RGBA")

    # Extract alpha from rendered white-on-transparent
    # The white fill means R=G=B=255 where drawn, alpha carries opacity
    alpha = img.split()[3]  # alpha channel

    if flip_h:
        alpha = alpha.transpose(Image.FLIP_LEFT_RIGHT)

    return alpha


def draw_light_bar(size: int, flip_h: bool = False) -> Image.Image:
    """Draw a custom light bar icon using Pillow (no standard MDI icon)."""
    img = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(img)

    # Scale factor from 48-pixel reference design
    s = size / 48.0

    # Bar housing - centered rectangle
    bar_left = int(3 * s)
    bar_right = int(45 * s)
    bar_top = int(16 * s)
    bar_bottom = int(32 * s)
    draw.rectangle([bar_left, bar_top, bar_right, bar_bottom], fill=255)

    # Inner dark area (will show as lower alpha = gap between housing and lights)
    inner_margin = int(2 * s)
    draw.rectangle(
        [bar_left + inner_margin, bar_top + inner_margin,
         bar_right - inner_margin, bar_bottom - inner_margin],
        fill=0,
    )

    # 6 light cells inside the bar
    cell_h = int(12 * s) - 2 * inner_margin
    cell_w = int(5 * s)
    cell_top = bar_top + inner_margin + int(1 * s)
    cell_bottom = cell_top + cell_h
    gap = int(1.5 * s)

    total_cells_w = 6 * cell_w + 5 * gap
    start_x = (size - total_cells_w) // 2

    for i in range(6):
        cx = start_x + i * (cell_w + gap)
        draw.rectangle([cx, cell_top, cx + cell_w, cell_bottom], fill=255)

    # Mounting brackets below bar
    bracket_w = int(2 * s)
    bracket_h = int(5 * s)
    bracket_y_top = bar_bottom + int(1 * s)
    bracket_y_bot = bracket_y_top + bracket_h
    # Left bracket
    bx1 = bar_left + int(5 * s)
    draw.rectangle([bx1, bracket_y_top, bx1 + bracket_w, bracket_y_bot], fill=255)
    # Right bracket
    bx2 = bar_right - int(5 * s) - bracket_w
    draw.rectangle([bx2, bracket_y_top, bx2 + bracket_w, bracket_y_bot], fill=255)

    # Rays going up from bar
    ray_y_top = int(4 * s)
    ray_y_bot = bar_top - int(2 * s)
    ray_w = int(1.5 * s)

    # 5 rays evenly spaced
    ray_positions = [
        int(10 * s), int(16 * s), int(24 * s), int(32 * s), int(38 * s)
    ]
    for rx in ray_positions:
        draw.rectangle([rx, ray_y_top, rx + ray_w, ray_y_bot], fill=200)

    # Diagonal rays at edges
    for angle_x, direction in [(int(7 * s), -1), (int(41 * s), 1)]:
        for y in range(ray_y_top, ray_y_bot):
            frac = (ray_y_bot - y) / (ray_y_bot - ray_y_top)
            x = angle_x + int(direction * frac * 3 * s)
            for dx in range(int(ray_w)):
                if 0 <= x + dx < size and 0 <= y < size:
                    img.putpixel((x + dx, y), 180)

    if flip_h:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)

    return img


def alpha_to_c_array(img: Image.Image, name: str) -> str:
    """Convert a grayscale/alpha image to a C uint8_t array string."""
    size = img.width
    assert img.width == img.height, "Icon must be square"
    pixels = list(img.getdata())

    lines = []
    for row in range(size):
        row_data = pixels[row * size : (row + 1) * size]
        line = ",".join(f"{p:>3}" for p in row_data)
        lines.append(f"    {line},")

    array_str = "\n".join(lines)
    return f"static const uint8_t {name}[{size} * {size}] = {{\n{array_str}\n}};"


def generate_cpp(size: int, flip: bool) -> str:
    """Generate the full ui_icons.cpp content."""
    icons = {}

    # Rasterize MDI icons
    for name, path_d in MDI_PATHS.items():
        icons[name] = svg_path_to_alpha(path_d, size, flip_h=flip)

    # Custom light bar
    icons["light_bar"] = draw_light_bar(size, flip_h=flip)

    # Build C source
    parts = [
        '#include "ui_icons.h"',
        "",
        f"// {size}x{size} pixel icons as LVGL-compatible alpha maps (LV_IMG_CF_ALPHA_8BIT)",
        "// Each byte = one pixel alpha value (0x00 = transparent, 0xFF = opaque)",
        "// Icons can be recolored via lv_obj_set_style_img_recolor()",
        "// MDI icons: Apache 2.0 license, https://pictogrammers.com/library/mdi/",
        "",
    ]

    icon_names = [
        ("fog", "fog_map", "Fog lamp icon (mdi:car-light-fog)"),
        ("low_beam", "low_beam_map", "Low beam icon (mdi:car-light-dimmed)"),
        ("high_beam", "high_beam_map", "High beam icon (mdi:car-light-high)"),
        ("light_bar", "light_bar_map", "Light bar icon (custom drawn)"),
    ]

    for key, array_name, comment in icon_names:
        parts.append(f"// {comment}")
        parts.append(alpha_to_c_array(icons[key], array_name))
        parts.append("")

    # LVGL image descriptors
    descriptors = [
        ("icon_fog", "fog_map"),
        ("icon_low_beam", "low_beam_map"),
        ("icon_high_beam", "high_beam_map"),
        ("icon_light_bar", "light_bar_map"),
    ]

    parts.append("// LVGL image descriptors")
    for dsc_name, data_name in descriptors:
        parts.append(textwrap.dedent(f"""\
            const lv_img_dsc_t {dsc_name} = {{
                .header = {{
                    .cf = LV_IMG_CF_ALPHA_8BIT,
                    .always_zero = 0,
                    .reserved = 0,
                    .w = {size},
                    .h = {size},
                }},
                .data_size = {size} * {size},
                .data = {data_name},
            }};"""))
        parts.append("")

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Generate LVGL icon arrays from MDI SVG paths")
    parser.add_argument("--size", type=int, default=48, help="Icon size in pixels (default: 48)")
    parser.add_argument("--flip", action="store_true", help="Flip icons horizontally")
    parser.add_argument("--output", type=str, default=None, help="Output file path (default: stdout)")
    args = parser.parse_args()

    cpp = generate_cpp(args.size, args.flip)

    if args.output:
        with open(args.output, "w") as f:
            f.write(cpp)
        print(f"Written to {args.output} ({args.size}x{args.size}, flip={args.flip})")
    else:
        print(cpp)


if __name__ == "__main__":
    main()
