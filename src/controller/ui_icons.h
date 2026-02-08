#pragma once

#include <lvgl.h>

// 48x48 monochrome icons stored as LVGL image descriptors
// These are alpha-only bitmaps (A8 format)
// Recolored via lv_obj_set_style_img_recolor()

extern const lv_img_dsc_t icon_fog;
extern const lv_img_dsc_t icon_low_beam;
extern const lv_img_dsc_t icon_high_beam;
extern const lv_img_dsc_t icon_light_bar;
