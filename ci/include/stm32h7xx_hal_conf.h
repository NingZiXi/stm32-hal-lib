/**
 * @file    stm32h7xx_hal_conf.h
 * @brief   H723 编译和模拟测试专用 HAL 配置，不是开发板配置
 */
#ifndef STM32H7XX_HAL_CONF_H
#define STM32H7XX_HAL_CONF_H

#define HAL_MODULE_ENABLED
#define HAL_RCC_MODULE_ENABLED
#define HAL_GPIO_MODULE_ENABLED
#define HAL_CORTEX_MODULE_ENABLED
#define HAL_DMA_MODULE_ENABLED
#define HAL_MDMA_MODULE_ENABLED
#define HAL_FLASH_MODULE_ENABLED
#define HAL_PWR_MODULE_ENABLED
#define HAL_SDRAM_MODULE_ENABLED
#if defined(STM32H757xx)
#define HAL_QSPI_MODULE_ENABLED
#else
#define HAL_OSPI_MODULE_ENABLED
#endif
#define HAL_UART_MODULE_ENABLED
#define HAL_I2C_MODULE_ENABLED
#define HAL_SD_MODULE_ENABLED

#define HSE_VALUE 25000000U
#define HSE_STARTUP_TIMEOUT 100U
#define HSI_VALUE 64000000U
#define CSI_VALUE 4000000U
#define LSE_VALUE 32768U
#define LSE_STARTUP_TIMEOUT 5000U
#define LSI_VALUE 32000U
#define EXTERNAL_CLOCK_VALUE 12288000U
#define VDD_VALUE 3300U
#define TICK_INT_PRIORITY 15U
#define USE_RTOS 0U
#define USE_HAL_SDRAM_REGISTER_CALLBACKS 0U
#define USE_HAL_OSPI_REGISTER_CALLBACKS 0U
#define USE_HAL_QSPI_REGISTER_CALLBACKS 0U
#define USE_HAL_UART_REGISTER_CALLBACKS 0U

#include "stm32h7xx_hal_rcc.h"
#include "stm32h7xx_hal_gpio.h"
#include "stm32h7xx_hal_cortex.h"
#include "stm32h7xx_hal_dma.h"
#include "stm32h7xx_hal_mdma.h"
#include "stm32h7xx_hal_flash.h"
#include "stm32h7xx_hal_pwr.h"
#include "stm32h7xx_hal_sdram.h"
#if defined(STM32H757xx)
#include "stm32h7xx_hal_qspi.h"
#else
#include "stm32h7xx_hal_ospi.h"
#endif
#include "stm32h7xx_hal_uart.h"
#include "stm32h7xx_hal_i2c.h"
#include "stm32h7xx_hal_sd.h"

#define assert_param(expr) ((void)0U)
#endif
