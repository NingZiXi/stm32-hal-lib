/**
 * @file    headers.cpp
 * @brief   C++ 消费者的组件公共头文件编译检查
 */
#include "stm_err.h"
#include "stm_flash.h"
#include "stm_sdram.h"
#include "stm_log.h"

static_assert(STM_OK == 0, "STM_OK must remain zero");
stm_err_t ci_delete_handles(flash_handle_t *flash, sdram_handle_t *ram)
{
    const stm_err_t err = flash_delete(flash);
    return err == STM_OK ? sdram_delete(ram) : err;
}
