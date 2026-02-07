#include "display.h"

static Arduino_DataBus *bus = nullptr;
static Arduino_GFX *gfx = nullptr;

// LVGL display buffer
static lv_disp_draw_buf_t draw_buf;
static lv_color_t *buf1 = nullptr;
static lv_disp_drv_t disp_drv;

// JD9853 register init sequence from Waveshare demo
static void lcd_reg_init() {
    static const uint8_t init_operations[] = {
        BEGIN_WRITE,
        WRITE_COMMAND_8, 0x11,
        END_WRITE,
        DELAY, 120,

        BEGIN_WRITE,
        WRITE_C8_D16, 0xDF, 0x98, 0x53,
        WRITE_C8_D8, 0xB2, 0x23,

        WRITE_COMMAND_8, 0xB7,
        WRITE_BYTES, 4,
        0x00, 0x47, 0x00, 0x6F,

        WRITE_COMMAND_8, 0xBB,
        WRITE_BYTES, 6,
        0x1C, 0x1A, 0x55, 0x73, 0x63, 0xF0,

        WRITE_C8_D16, 0xC0, 0x44, 0xA4,
        WRITE_C8_D8, 0xC1, 0x16,

        WRITE_COMMAND_8, 0xC3,
        WRITE_BYTES, 8,
        0x7D, 0x07, 0x14, 0x06, 0xCF, 0x71, 0x72, 0x77,

        WRITE_COMMAND_8, 0xC4,
        WRITE_BYTES, 12,
        0x00, 0x00, 0xA0, 0x79, 0x0B, 0x0A, 0x16, 0x79, 0x0B, 0x0A, 0x16, 0x82,

        WRITE_COMMAND_8, 0xC8,
        WRITE_BYTES, 32,
        0x3F, 0x32, 0x29, 0x29, 0x27, 0x2B, 0x27, 0x28, 0x28, 0x26, 0x25, 0x17, 0x12, 0x0D, 0x04, 0x00,
        0x3F, 0x32, 0x29, 0x29, 0x27, 0x2B, 0x27, 0x28, 0x28, 0x26, 0x25, 0x17, 0x12, 0x0D, 0x04, 0x00,

        WRITE_COMMAND_8, 0xD0,
        WRITE_BYTES, 5,
        0x04, 0x06, 0x6B, 0x0F, 0x00,

        WRITE_C8_D16, 0xD7, 0x00, 0x30,
        WRITE_C8_D8, 0xE6, 0x14,
        WRITE_C8_D8, 0xDE, 0x01,

        WRITE_COMMAND_8, 0xB7,
        WRITE_BYTES, 5,
        0x03, 0x13, 0xEF, 0x35, 0x35,

        WRITE_COMMAND_8, 0xC1,
        WRITE_BYTES, 3,
        0x14, 0x15, 0xC0,

        WRITE_C8_D16, 0xC2, 0x06, 0x3A,
        WRITE_C8_D16, 0xC4, 0x72, 0x12,
        WRITE_C8_D8, 0xBE, 0x00,
        WRITE_C8_D8, 0xDE, 0x02,

        WRITE_COMMAND_8, 0xE5,
        WRITE_BYTES, 3,
        0x00, 0x02, 0x00,

        WRITE_COMMAND_8, 0xE5,
        WRITE_BYTES, 3,
        0x01, 0x02, 0x00,

        WRITE_C8_D8, 0xDE, 0x00,
        WRITE_C8_D8, 0x35, 0x00,
        WRITE_C8_D8, 0x3A, 0x05,

        WRITE_COMMAND_8, 0x2A,
        WRITE_BYTES, 4,
        0x00, 0x22, 0x00, 0xCD,

        WRITE_COMMAND_8, 0x2B,
        WRITE_BYTES, 4,
        0x00, 0x00, 0x01, 0x3F,

        WRITE_C8_D8, 0xDE, 0x02,

        WRITE_COMMAND_8, 0xE5,
        WRITE_BYTES, 3,
        0x00, 0x02, 0x00,

        WRITE_C8_D8, 0xDE, 0x00,
        WRITE_C8_D8, 0x36, 0x00,
        WRITE_COMMAND_8, 0x21,
        END_WRITE,

        DELAY, 10,

        BEGIN_WRITE,
        WRITE_COMMAND_8, 0x29,
        END_WRITE
    };
    bus->batchOperation(init_operations, sizeof(init_operations));
}

static void disp_flush(lv_disp_drv_t *drv, const lv_area_t *area, lv_color_t *color_p) {
    uint32_t w = area->x2 - area->x1 + 1;
    uint32_t h = area->y2 - area->y1 + 1;

#if (LV_COLOR_16_SWAP != 0)
    gfx->draw16bitBeRGBBitmap(area->x1, area->y1, (uint16_t *)&color_p->full, w, h);
#else
    gfx->draw16bitRGBBitmap(area->x1, area->y1, (uint16_t *)&color_p->full, w, h);
#endif

    lv_disp_flush_ready(drv);
}

void display_init() {
    // Create SPI bus and GFX driver
    bus = new Arduino_HWSPI(PIN_LCD_DC, PIN_LCD_CS, PIN_LCD_SCK, PIN_LCD_MOSI);
    gfx = new Arduino_ST7789(
        bus, PIN_LCD_RST, 0 /* rotation */, false /* IPS */,
        DISP_NATIVE_W, DISP_NATIVE_H,
        34 /* col_offset1 */, 0 /* row_offset1 */,
        34 /* col_offset2 */, 0 /* row_offset2 */
    );

    if (!gfx->begin()) {
        Serial.println("GFX init failed!");
        return;
    }
    lcd_reg_init();
    gfx->setRotation(1);
    gfx->fillScreen(RGB565_BLACK);

    // Backlight on
    pinMode(PIN_LCD_BL, OUTPUT);
    digitalWrite(PIN_LCD_BL, HIGH);

    // Init LVGL
    lv_init();

    // Allocate draw buffer
    uint32_t buf_size = DISP_WIDTH * 40;
    buf1 = (lv_color_t *)heap_caps_malloc(buf_size * sizeof(lv_color_t), MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT);
    if (!buf1) {
        buf1 = (lv_color_t *)malloc(buf_size * sizeof(lv_color_t));
    }
    if (!buf1) {
        Serial.println("LVGL buffer alloc failed!");
        return;
    }

    lv_disp_draw_buf_init(&draw_buf, buf1, NULL, buf_size);

    // Register display driver
    lv_disp_drv_init(&disp_drv);
    disp_drv.hor_res  = DISP_WIDTH;
    disp_drv.ver_res  = DISP_HEIGHT;
    disp_drv.flush_cb = disp_flush;
    disp_drv.draw_buf = &draw_buf;
    lv_disp_drv_register(&disp_drv);
}

Arduino_GFX *display_get_gfx() {
    return gfx;
}
