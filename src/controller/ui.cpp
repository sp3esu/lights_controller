#include "ui.h"
#include "ui_icons.h"
#include "espnow_tx.h"
#include "display.h"
#include "protocol.h"
#include <lvgl.h>

// Color definitions
#define COLOR_BG        lv_color_hex(0x0F0F1A)

// ON colors per light
#define COLOR_FOG_ON     lv_color_hex(0xFFB84D)  // amber
#define COLOR_LOW_ON     lv_color_hex(0xFFDD44)  // warm yellow
#define COLOR_HIGH_ON    lv_color_hex(0x88CCFF)  // light blue
#define COLOR_BAR_ON     lv_color_hex(0xFFFFFF)  // white


// Light button info
struct LightBtnInfo {
    uint8_t            light_bit;
    const lv_img_dsc_t *icon;
    lv_color_t         on_color;
};

static const LightBtnInfo btn_info[4] = {
    { LIGHT_FOG,       &icon_fog,       COLOR_FOG_ON },
    { LIGHT_LOW_BEAM,  &icon_low_beam,  COLOR_LOW_ON },
    { LIGHT_HIGH_BEAM, &icon_high_beam, COLOR_HIGH_ON },
    { LIGHT_BAR,       &icon_light_bar, COLOR_BAR_ON },
};

// UI elements
static lv_obj_t *scr_main = nullptr;
static lv_obj_t *scr_pairing = nullptr;
static lv_obj_t *btn_objs[4] = {};
static lv_obj_t *btn_icons[4] = {};

static bool updating_ui = false;  // guard against recursive events
static bool test_mode = false;    // local-only toggle without ESP-NOW

static void apply_btn_style(int idx, bool on) {
    lv_obj_t *btn = btn_objs[idx];
    if (on) {
        // ON: colored background, dark icon
        lv_obj_set_style_bg_opa(btn, LV_OPA_COVER, LV_PART_MAIN);
        lv_obj_set_style_bg_color(btn, btn_info[idx].on_color, LV_PART_MAIN);
        lv_obj_set_style_img_recolor(btn_icons[idx], COLOR_BG, LV_PART_MAIN);
    } else {
        // OFF: transparent background, colored icon
        lv_obj_set_style_bg_opa(btn, LV_OPA_TRANSP, LV_PART_MAIN);
        lv_obj_set_style_img_recolor(btn_icons[idx], btn_info[idx].on_color, LV_PART_MAIN);
    }
    lv_obj_set_style_img_recolor_opa(btn_icons[idx], LV_OPA_COVER, LV_PART_MAIN);

    if (on) lv_obj_add_state(btn, LV_STATE_CHECKED);
    else    lv_obj_clear_state(btn, LV_STATE_CHECKED);
}

static void btn_event_cb(lv_event_t *e) {
    if (updating_ui) return;

    lv_obj_t *btn = lv_event_get_target(e);
    int idx = (int)(intptr_t)lv_event_get_user_data(e);
    bool checked = lv_obj_has_state(btn, LV_STATE_CHECKED);

    // Optimistic UI update
    apply_btn_style(idx, checked);

    // In test mode, just toggle locally; otherwise send via ESP-NOW
    if (!test_mode) {
        espnow_tx_toggle_light(btn_info[idx].light_bit);
    }
}

static lv_obj_t *create_light_button(lv_obj_t *parent, int idx) {
    lv_obj_t *btn = lv_obj_create(parent);
    lv_obj_remove_style_all(btn);
    lv_obj_set_size(btn, 154, 80);
    lv_obj_set_style_bg_opa(btn, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_radius(btn, 12, LV_PART_MAIN);

    // Checkable toggle
    lv_obj_add_flag(btn, LV_OBJ_FLAG_CHECKABLE | LV_OBJ_FLAG_CLICKABLE);

    // Pressed feedback: semi-transparent white overlay (works for both ON and OFF)
    lv_obj_set_style_bg_opa(btn, LV_OPA_30, (lv_style_selector_t)(LV_PART_MAIN | LV_STATE_PRESSED));
    lv_obj_set_style_bg_color(btn, lv_color_white(), (lv_style_selector_t)(LV_PART_MAIN | LV_STATE_PRESSED));

    // Center content
    lv_obj_set_flex_flow(btn, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_flex_align(btn, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);

    // Icon — starts with light's signature color (OFF state)
    lv_obj_t *img = lv_img_create(btn);
    lv_img_set_src(img, btn_info[idx].icon);
    lv_obj_set_style_img_recolor(img, btn_info[idx].on_color, LV_PART_MAIN);
    lv_obj_set_style_img_recolor_opa(img, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_clear_flag(img, LV_OBJ_FLAG_CLICKABLE);
    btn_icons[idx] = img;

    // Event
    lv_obj_add_event_cb(btn, btn_event_cb, LV_EVENT_VALUE_CHANGED, (void *)(intptr_t)idx);

    btn_objs[idx] = btn;
    return btn;
}

void ui_init() {
    // Main screen
    scr_main = lv_obj_create(NULL);
    lv_obj_set_style_bg_color(scr_main, COLOR_BG, LV_PART_MAIN);
    lv_obj_set_style_bg_opa(scr_main, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_pad_all(scr_main, 0, LV_PART_MAIN);

    // Full-screen 2x2 grid
    lv_obj_t *grid = lv_obj_create(scr_main);
    lv_obj_remove_style_all(grid);
    lv_obj_set_size(grid, DISP_WIDTH, DISP_HEIGHT);
    lv_obj_align(grid, LV_ALIGN_TOP_LEFT, 0, 0);
    lv_obj_set_style_pad_all(grid, 4, LV_PART_MAIN);
    lv_obj_set_style_pad_gap(grid, 4, LV_PART_MAIN);
    lv_obj_clear_flag(grid, LV_OBJ_FLAG_SCROLLABLE);

    // 2x2 flex layout with wrap
    lv_obj_set_flex_flow(grid, LV_FLEX_FLOW_ROW_WRAP);
    lv_obj_set_flex_align(grid, LV_FLEX_ALIGN_SPACE_EVENLY, LV_FLEX_ALIGN_SPACE_EVENLY, LV_FLEX_ALIGN_SPACE_EVENLY);

    // Create 4 buttons
    for (int i = 0; i < 4; i++) {
        create_light_button(grid, i);
    }

    // Pairing screen
    scr_pairing = lv_obj_create(NULL);
    lv_obj_set_style_bg_color(scr_pairing, COLOR_BG, LV_PART_MAIN);
    lv_obj_set_style_bg_opa(scr_pairing, LV_OPA_COVER, LV_PART_MAIN);

    lv_obj_t *pair_label = lv_label_create(scr_pairing);
    lv_label_set_text(pair_label, "Pairing...");
    lv_obj_set_style_text_color(pair_label, lv_color_white(), LV_PART_MAIN);
    lv_obj_set_style_text_font(pair_label, &lv_font_montserrat_16, LV_PART_MAIN);
    lv_obj_center(pair_label);

    lv_obj_t *spinner = lv_spinner_create(scr_pairing, 1000, 60);
    lv_obj_set_size(spinner, 50, 50);
    lv_obj_align(spinner, LV_ALIGN_CENTER, 0, 40);
}

void ui_set_light_state(uint8_t state) {
    updating_ui = true;
    for (int i = 0; i < 4; i++) {
        bool on = (state & btn_info[i].light_bit) != 0;
        apply_btn_style(i, on);
    }
    updating_ui = false;
}

void ui_set_connection_status(bool connected) {
    // Connection state shown via NeoPixel — no on-screen indicator
    (void)connected;
}

void ui_show_pairing() {
    lv_scr_load(scr_pairing);
}

void ui_show_main() {
    lv_scr_load(scr_main);
}

void ui_set_test_mode(bool enabled) {
    test_mode = enabled;
}
