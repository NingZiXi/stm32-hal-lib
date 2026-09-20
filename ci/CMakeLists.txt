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
target_compile_definitions(stm32cubemx INTERFACE USE_HAL_DRIVER STM32H723xx)
target_include_directories(stm32cubemx INTERFACE
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
    "${DEPS_ROOT}/hal/Inc"
    "${DEPS_ROOT}/device/Include"
    "${DEPS_ROOT}/cmsis/CMSIS/Core/Include")

add_subdirectory("${LIB_ROOT}/components/stm_common" stm_common)
add_subdirectory("${LIB_ROOT}/components/stm_flash" stm_flash)
add_subdirectory("${LIB_ROOT}/components/stm_sdram" stm_sdram)
add_subdirectory("${LIB_ROOT}/components/stm_log" stm_log)
target_compile_definitions(stm_log PUBLIC STM_LOG_HAL_HEADER="stm32h7xx_hal.h")

# 检查消费者通过 target 链接能取得全部公共头文件和宏。
add_library(public_headers OBJECT headers.c headers.cpp)
target_compile_features(public_headers PRIVATE c_std_11 cxx_std_17)
target_link_libraries(public_headers PRIVATE stm_flash stm_sdram stm_log)

add_library(log_disabled OBJECT "${LIB_ROOT}/components/stm_log/stm_log.c")
target_compile_definitions(log_disabled PRIVATE STM_LOG_HAL_HEADER="stm32h7xx_hal.h" STM_LOG_ENABLED=0)
target_link_libraries(log_disabled PRIVATE stm32cubemx)
