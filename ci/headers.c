/**
 * @file    headers.c
 * @brief   C 消费者的组件公共头文件编译检查
 */
#include "stm_err.h"
#include "stm_flash.h"
#include "stm_sdram.h"
#include "stm_log.h"
#include "stm_littlefs.h"

_Static_assert(STM_OK == 0, "STM_OK must remain zero");
stm_err_t ci_read_info(flash_handle_t flash, sdram_handle_t ram)
{
    flash_info_t flash_info;
    sdram_info_t ram_info;
    stm_err_t err = flash_get_info(flash, &flash_info);
    return err == STM_OK ? sdram_get_info(ram, &ram_info) : err;
}
