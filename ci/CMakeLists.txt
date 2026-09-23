cmake_minimum_required(VERSION 3.22)
project(stm32_hal_lib_compile_check LANGUAGES C CXX)

get_filename_component(LIB_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/.." ABSOLUTE)
set(DEPS_ROOT "${LIB_ROOT}/.ci-deps" CACHE PATH "HAL/CMSIS checkout directory")
foreach(header hal/Inc/stm32h7xx_hal.h device/Include/stm32h723xx.h cmsis/CMSIS/Core/Include/core_cm7.h)
    if(NOT EXISTS "${DEPS_ROOT}/${header}")
        message(FATAL_ERROR "Missing ${DEPS_ROOT}/${header}; see ci/README.md")
    endif()
endforeach()

add_compile_options(-Wall -Wextra -Werror)
add_library(stm32cubemx INTERFACE)
set(CI_MCU STM32H723xx CACHE STRING "MCU for HAL compile checks")
target_compile_definitions(stm32cubemx INTERFACE USE_HAL_DRIVER ${CI_MCU} CORE_CM7)
target_include_directories(stm32cubemx INTERFACE
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
    "${DEPS_ROOT}/hal/Inc"
    "${DEPS_ROOT}/device/Include"
    "${DEPS_ROOT}/cmsis/CMSIS/Core/Include")

add_subdirectory("${LIB_ROOT}/lib/stm_common" stm_common)
add_subdirectory("${LIB_ROOT}/lib/stm_flash" stm_flash)
add_subdirectory("${LIB_ROOT}/lib/stm_sdram" stm_sdram)
if(CI_MCU STREQUAL "STM32H757xx")
    set(STM_FLASH_WITH_QSPI ON)
    set(STM_FLASH_WITH_OSPI OFF)
    set(memory_flash_adapter stm_flash_qspi)
else()
    set(STM_FLASH_WITH_QSPI OFF)
    set(STM_FLASH_WITH_OSPI ON)
    set(memory_flash_adapter stm_flash_ospi)
endif()
add_subdirectory("${LIB_ROOT}/lib/stm_flash/adapters/stm32_hal" flash_hal)
add_subdirectory("${LIB_ROOT}/lib/stm_sdram/adapters/stm32_hal" sdram_hal)
target_compile_definitions(${memory_flash_adapter} PUBLIC STM_FLASH_HAL_HEADER="stm32h7xx_hal.h")
target_compile_definitions(stm_sdram_fmc PUBLIC STM_SDRAM_HAL_HEADER="stm32h7xx_hal.h")
add_library(memory_adapter_headers OBJECT memory_adapter_headers.cpp)
target_compile_features(memory_adapter_headers PRIVATE cxx_std_17)
target_link_libraries(memory_adapter_headers PRIVATE ${memory_flash_adapter} stm_sdram_fmc)
add_subdirectory("${LIB_ROOT}/lib/stm_log" stm_log)
add_subdirectory("${LIB_ROOT}/lib/stm_littlefs" stm_littlefs)
# 上游仅在 assert 中使用此辅助函数，Release 的 NDEBUG 会使其未使用。
target_compile_options(littlefs PRIVATE -Wno-unused-function)
add_subdirectory("${LIB_ROOT}/lib/esp_at_client" esp_at_client)
target_compile_definitions(stm_log PUBLIC STM_LOG_HAL_HEADER="stm32h7xx_hal.h")

# 验证 STM32 HAL 适配层在 H7 下编译：必须显式 add_subdirectory，库不会自动加入。
add_subdirectory("${LIB_ROOT}/lib/esp_at_client/ports/stm32_hal" esp_at_stm32_hal)
target_compile_definitions(esp_at_stm32_hal PUBLIC ESP_AT_STM32_HAL_HEADER="stm32h7xx_hal.h")
target_link_libraries(esp_at_stm32_hal PUBLIC stm32cubemx)

# 检查消费者通过 target 链接能取得全部公共头文件和宏。
add_library(public_headers OBJECT headers.c headers.cpp)
target_compile_features(public_headers PRIVATE c_std_11 cxx_std_17)
target_link_libraries(public_headers PRIVATE stm_flash stm_sdram stm_log stm_littlefs)

add_library(log_disabled OBJECT "${LIB_ROOT}/lib/stm_log/stm_log.c")
target_compile_definitions(log_disabled PRIVATE STM_LOG_HAL_HEADER="stm32h7xx_hal.h" STM_LOG_ENABLED=0)
target_link_libraries(log_disabled PRIVATE stm32cubemx)

# STM32 适配层编译检查：未引用具体工程 main.h，仅检查 HAL 类型与 UART/DMA 接线。
add_library(esp_at_stm32_hal_check OBJECT
    "${LIB_ROOT}/lib/esp_at_client/ports/stm32_hal/esp_at_port_stm32.c"
    "${LIB_ROOT}/lib/esp_at_client/ports/stm32_hal/esp_at_esp_port.c")
target_link_libraries(esp_at_stm32_hal_check PRIVATE esp_at_stm32_hal)

if(STM_LOG_WITH_RTT)
    add_executable(rtt_link_check rtt_link.c)
    target_link_libraries(rtt_link_check PRIVATE stm_log)
    target_link_options(rtt_link_check PRIVATE --specs=nosys.specs -nostartfiles -Wl,-e,main)
endif()
