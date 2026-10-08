/**
 * @file    rtt_link.c
 * @brief   验证应用只链接 stm_log 即可使用 RTT；非板级固件
 */
#include "stm_log.h"
#include "SEGGER_RTT.h"

// 链接检查不依赖 HAL，也不访问真实外设。
static uint32_t test_tick(void) { return 0U; }

static void rtt_output(const char *data, uint16_t size)
{
    SEGGER_RTT_Write(0, data, size);
}

int main(void)
{
    SEGGER_RTT_Init();
    stm_log_set_tick(test_tick);
    stm_log_init_output(rtt_output, STM_LOG_LVL_INFO);
    LOGI("ci", "RTT dependency linked");
    return 0;
}
