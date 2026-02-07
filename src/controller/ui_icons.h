#pragma once

#include <lvgl.h>

// 40x40 monochrome icons stored as LVGL image descriptors
// These are alpha-only bitmaps (A8 format stored as indexed)
// rendered with lv_canvas or drawn as img with recoloring

extern const lv_img_dsc_t icon_fog;
extern const lv_img_dsc_t icon_low_beam;
extern const lv_img_dsc_t icon_high_beam;
extern const lv_img_dsc_t icon_light_bar;
