#include "touch.h"
#include "axs5106l.h"
#include <Wire.h>

static AXS5106L touchpad;

static void touchpad_read_cb(lv_indev_drv_t *drv, lv_indev_data_t *data) {
    (void)drv;
    touchpad.update();

    TouchData td;
    if (touchpad.getPoint(td)) {
        data->point.x = td.points[0].x;
        data->point.y = td.points[0].y;
        data->state = LV_INDEV_STATE_PRESSED;
    } else {
        data->state = LV_INDEV_STATE_RELEASED;
    }
}

void touch_init(uint16_t rotation, uint16_t width, uint16_t height) {
    touchpad.begin(Wire, PIN_TOUCH_SDA, PIN_TOUCH_SCL,
                   PIN_TOUCH_RST, PIN_TOUCH_INT,
                   rotation, width, height);

    static lv_indev_drv_t indev_drv;
    lv_indev_drv_init(&indev_drv);
    indev_drv.type    = LV_INDEV_TYPE_POINTER;
    indev_drv.read_cb = touchpad_read_cb;
    lv_indev_drv_register(&indev_drv);
}
