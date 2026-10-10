#include "stm_lcd.h"
/**
 * @file    headers.c
 * @brief   C 消费者的组件公共头文件编译检查
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

_Static_assert(STM_OK == 0, "STM_OK must remain zero");
stm_err_t ci_read_info(flash_handle_t flash, sdram_handle_t ram)
{
    flash_info_t flash_info;
    sdram_info_t ram_info;
    stm_err_t err = flash_get_info(flash, &flash_info);
    return err == STM_OK ? sdram_get_info(ram, &ram_info) : err;
}
