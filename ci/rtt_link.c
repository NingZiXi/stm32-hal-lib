/**
 * @file    rtt_link.c
 * @brief   验证应用只链接 stm_log 即可使用 RTT；非板级固件
 */
#include "stm_log.h"
#include "SEGGER_RTT.h"

// 链接检查不使用 HAL 实现，不访问真实串口。
uint32_t HAL_GetTick(void) { return 0U; }
HAL_StatusTypeDef HAL_UART_Transmit(UART_HandleTypeDef *uart, const uint8_t *data,
                                    uint16_t size, uint32_t timeout)
{
    (void)uart;
    (void)data;
    (void)size;
    (void)timeout;
    return HAL_OK;
}

static void rtt_output(const char *data, uint16_t size)
{
    SEGGER_RTT_Write(0, data, size);
}

int main(void)
{
    SEGGER_RTT_Init();
    stm_log_init_output(rtt_output, STM_LOG_LVL_INFO);
    LOGI("ci", "RTT dependency linked");
    return 0;
}
