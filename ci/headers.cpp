#include "stm_lcd.h"
/**
 * @file    headers.cpp
 * @brief   C++ 消费者的组件公共头文件编译检查
 */
#include "stm_err.h"
#include "stm_flash.h"
#include "stm_sdram.h"
#include "stm_log.h"
#include "stm_littlefs.h"
#include "stm_eeprom.h"
#include "stm_sd.h"
#include "stm_fatfs.h"
#include "stm_fatfs_flash.h"
#include "stm_lcd_st7789.h"
#include "stm_lcd_st7796.h"
#include "stm_lcd_touch_ft5206.h"
#include "stm_lcd_ili9881c.h"
#include "stm_lcd_touch_gt9271.h"
#include "stm_lcd_axs15231b.h"
#include "stm_lcd_touch_axs15231b.h"

static_assert(STM_OK == 0, "STM_OK must remain zero");
stm_err_t ci_delete_handles(flash_handle_t *flash, sdram_handle_t *ram)
{
    const stm_err_t err = flash_delete(flash);
    return err == STM_OK ? sdram_delete(ram) : err;
}
