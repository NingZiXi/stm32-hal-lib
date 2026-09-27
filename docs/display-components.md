# STM32 显示与触摸组件接入指南

本仓库按**实际芯片型号**选组件：SPI 面板 `stm_lcd_st7789` / `stm_lcd_st7796` 二选一；I²C 触摸 `stm_lcd_touch_ft5206` 按需添加；使用 LVGL 9 时再添加 `stm_lvgl_port`。没有额外的通用 `stm_display` / `stm_touch` 接口层。旧 `stm_display` / `stm_lvgl` 的 API 不再用于新工程。

这些驱动采用与乐鑫 LCD 组件相近的职责划分：板级 IO 回调负责总线传输和 GPIO，芯片组件负责命令与坐标，LVGL 粘合层负责把绘图、输入回调接到 LVGL。这里使用本仓库的 `stm_*` API，**不是**兼容 ESP-IDF 的 `esp_lcd_*` API。各组件的公开头文件与简明说明分别在 [ST7789](../lib/stm_lcd_st7789/README.md)、[ST7796](../lib/stm_lcd_st7796/README.md)、[FT5206](../lib/stm_lcd_touch_ft5206/README.md)、[LVGL port](../lib/stm_lvgl_port/README.md)。

乐鑫侧可对照[独立面板组件示例 esp_lcd_ili9341](https://components.espressif.com/components/espressif/esp_lcd_ili9341)和[esp_lvgl_port](https://components.espressif.com/components/espressif/esp_lvgl_port)。后者提供任务、定时器、屏幕与触摸注册等较完整能力；当前 `stm_lvgl_port` 只实现同步显示刷新及可选触摸输入，因此接入时必须按本文自行提供 tick、handler、板级锁与缓存维护。

## 从旧组件迁移

2026-09-27 起，`stm_display` 与 `stm_lvgl` 不再作为独立远端仓库提供；旧提交中指向这两个远端的子模块无法再从远端检出。已有旧工程需要先升级汇总仓库到删除旧子模块、加入新组件的提交，然后运行 `git submodule sync --recursive` 和 `git submodule update --init --recursive`。使用独立仓库的工程，则自行把引用改到所需新组件。

| 原引用 | 现在的接法 |
| --- | --- |
| `stm_display`（若实际是 ST7789/ST7796 SPI 模块） | 选对应的 `stm_lcd_st7789` 或 `stm_lcd_st7796`，在板级实现 SPI/GPIO IO 回调。 |
| `stm_display`（RGB/LTDC 帧缓冲） | 先实现板级 LTDC 显存绘制，再按需接 `stm_lvgl_port` 的 `draw` 回调；不能套用 SPI 芯片初始化。 |
| `stm_lvgl` | 用 LVGL 9 + `stm_lvgl_port_attach` 接板级绘图及可选触摸；旧 API 不兼容，tick、handler、任务锁仍由应用负责。 |

删除旧组件前已保存完整本地 Git 历史；新项目请只引用上表的现行组件。

## 组件内中文示例（默认入口）

每个组件的首页均为中文 `README.md`，并在自己的 `examples/stm32_hal/` 下提供中文操作说明与可移植的 C 代码。接入某个芯片时从该组件的示例开始，按实物补齐 HAL 句柄与引脚；示例不是已完成的 H757 屏幕工程，尚需实板验证。

| 组件 | 独立示例 | 演示内容 |
| --- | --- | --- |
| ST7789 | [stm_lcd_st7789 示例](../lib/stm_lcd_st7789/examples/stm32_hal/README.md) | SPI 阻塞发送、CS/DC、复位、初始化及 2×2 测试块 |
| ST7796 | [stm_lcd_st7796 示例](../lib/stm_lcd_st7796/examples/stm32_hal/README.md) | 同上，使用独立的 ST7796 驱动 |
| FT5206 | [stm_lcd_touch_ft5206 示例](../lib/stm_lcd_touch_ft5206/examples/stm32_hal/README.md) | HAL I²C 寄存器读取、可选复位与触点轮询 |
| LVGL 9 | [stm_lvgl_port 示例](../lib/stm_lvgl_port/examples/stm32_hal/README.md) | 绘图/触摸回调、计时、事件处理和最小标签 |

## 先确认硬件

慧勤智远 STM32H757XIH6 CB V1.0 的板上显示**接口**不是已确认插接的屏幕型号。厂商实验 50 提供 ST7789/ST7796 SPI 模块初始化参考，实验 24 有 FT5206 I²C 寄存器读取参考；其 RGB/LTDC 模块参数也不能据此认定为上述 SPI 芯片。在实板接入前记录屏幕 PCB/排线型号、控制芯片、分辨率、供电及电平、SPI 或 RGB 接口、引脚定义（含 CS/DC/RST/BL）、触摸芯片与地址。不能凭接口或通用示例推定是哪颗芯片。

H757 当前存储示例的 `.ioc` 和启动代码**尚未接入显示外设**。本指南展示新工程或确认模块后的可选接入方式，不修改已验证的存储启动路径。确认 GPIO 与现有 FMC、QSPI、SDMMC、I²C4 的引脚复用和总线使用后，再配置 CubeMX；如果实际为 RGB/LTDC 面板，先由板级代码实现显存绘制，不要选 SPI 芯片驱动。

## 1. 加入组件并配置 CubeMX

克隆汇总仓库时使用 `git clone --recurse-submodules`；已有检出使用 `git submodule update --init --recursive`。也可以在项目 `Lib/` 中固定检出实际需要的独立仓库。只选实际屏幕对应的面板库；无触摸或不使用 LVGL 时，无须添加对应库。

以下是 **CM7/CMakeLists.txt 中**可选的接入示意（先把选中的组件放在工程 `Lib/` 下）。`stm_lvgl_port` 要求在添加前已有 **LVGL 9 的 CMake 目标 `lvgl`**；LVGL 的源码和 `lv_conf.h` 由工程提供。

```cmake
# 假定真实模块为 ST7789；若为 ST7796，请将两处 stm_lcd_st7789 改成 stm_lcd_st7796。
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../Lib/stm_lcd_st7789
                 ${CMAKE_CURRENT_BINARY_DIR}/stm_lcd_st7789)
target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE stm_lcd_st7789)

# 确认有 FT5206 后才启用：
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../Lib/stm_lcd_touch_ft5206
                 ${CMAKE_CURRENT_BINARY_DIR}/stm_lcd_touch_ft5206)
target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE stm_lcd_touch_ft5206)

# 配好 LVGL 9 并创建 lvgl CMake 目标后才启用：
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../Lib/stm_lvgl_port
                 ${CMAKE_CURRENT_BINARY_DIR}/stm_lvgl_port)
target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE stm_lvgl_port)
```

面板为 SPI 时，在 CubeMX 中配置选定 SPI 外设和 CS/DC/RST/BL GPIO，SPI 数据位宽使用 8 位，核对模式、速率及供电时序。触摸确认型号为 FT5206 后再配置对应 I²C 和可选 RST。复用现有总线时须在每笔传输期间保护 CS 与总线访问。不要在 `main.c` 的自动生成区域写入调用；在板级代码持有 HAL 句柄和引脚，应用入口只调用板级初始化。

## 2. 将 HAL 传输接到面板组件

芯片配置结构体包含 `tx_param`、`tx_color`、可选 `reset`、必需的 `delay_ms`、用户上下文 `io`、屏幕逻辑宽高以及 `x_gap/y_gap`。两个发送回调返回 **0 表示成功，非 0 表示失败**，而且必须在返回前完成对缓冲区的使用。`tx_color` 收到的是 RAMWR 命令（通常 `0x2C`）及**字节长度**，必须在同一笔受保护的传输里发送命令和 RGB565 像素；不能只发送颜色数据。

以下示意中的 `LCD_CS_GPIO_Port`、`LCD_DC_GPIO_Port`、引脚宏、`hspi_display` 和锁函数应由板级代码根据已确认硬件提供。`board_lcd_send_all` 示例为阻塞发送；**不能**从中断回调调用这些阻塞 HAL API。

```c
#include <limits.h>
#include "stm_lcd_st7789.h"             /* ST7796 时换成 stm_lcd_st7796.h */
#include "spi.h"
#include "gpio.h"

static int board_lcd_send_all(const void *data, size_t bytes)
{
    const uint8_t *p = (const uint8_t *)data;
    while (bytes != 0u) {
        uint16_t n = (uint16_t)(bytes > UINT16_MAX ? UINT16_MAX : bytes);
        if (HAL_SPI_Transmit(&hspi_display, (uint8_t *)p, n, 1000u) != HAL_OK)
            return -1;
        p += n;
        bytes -= n;
    }
    return 0;
}

static int board_lcd_tx_param(void *io, uint8_t command,
                              const uint8_t *data, size_t bytes)
{
    (void)io;
    board_lcd_lock();                    /* 裸机独占总线时可为空实现 */
    HAL_GPIO_WritePin(LCD_CS_GPIO_Port, LCD_CS_Pin, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(LCD_DC_GPIO_Port, LCD_DC_Pin, GPIO_PIN_RESET);
    int rc = board_lcd_send_all(&command, 1u);
    if (rc == 0 && bytes != 0u) {
        HAL_GPIO_WritePin(LCD_DC_GPIO_Port, LCD_DC_Pin, GPIO_PIN_SET);
        rc = board_lcd_send_all(data, bytes);
    }
    HAL_GPIO_WritePin(LCD_CS_GPIO_Port, LCD_CS_Pin, GPIO_PIN_SET);
    board_lcd_unlock();
    return rc;
}

static int board_lcd_tx_color(void *io, uint8_t command,
                              const void *pixels, size_t bytes)
{
    (void)io;
    board_lcd_lock();
    HAL_GPIO_WritePin(LCD_CS_GPIO_Port, LCD_CS_Pin, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(LCD_DC_GPIO_Port, LCD_DC_Pin, GPIO_PIN_RESET);
    int rc = board_lcd_send_all(&command, 1u);
    if (rc == 0) {
        HAL_GPIO_WritePin(LCD_DC_GPIO_Port, LCD_DC_Pin, GPIO_PIN_SET);
        rc = board_lcd_send_all(pixels, bytes);  /* 大块像素按 HAL 上限分段，CS 不释放 */
    }
    HAL_GPIO_WritePin(LCD_CS_GPIO_Port, LCD_CS_Pin, GPIO_PIN_SET);
    board_lcd_unlock();
    return rc;
}

static void board_lcd_delay(void *io, uint32_t ms) { (void)io; HAL_Delay(ms); }
static void board_lcd_reset(void *io, int high)
{
    (void)io;
    HAL_GPIO_WritePin(LCD_RST_GPIO_Port, LCD_RST_Pin,
                      high ? GPIO_PIN_SET : GPIO_PIN_RESET);
}

static stm_lcd_st7789_t lcd;
static int board_display_init(void)
{
    const stm_lcd_st7789_config_t cfg = {
        .tx_param = board_lcd_tx_param, .tx_color = board_lcd_tx_color,
        .reset = board_lcd_reset, .delay_ms = board_lcd_delay,
        .width = PANEL_WIDTH, .height = PANEL_HEIGHT,
        .x_gap = 0, .y_gap = 0,          /* 依实物模块确定偏移 */
    };
    int rc = stm_lcd_st7789_new_panel(&lcd, &cfg);
    if (rc == 0) rc = stm_lcd_st7789_reset(&lcd);
    if (rc == 0) rc = stm_lcd_st7789_init(&lcd);
    if (rc == 0) board_backlight_on();  /* 由板级 GPIO/PWM 控制 */
    return rc;
}
```

SPI 模块的 MADCTL、反色、RGB/BGR、偏移等初始值来自厂商示例，实际模块的方向与颜色要实板校正。驱动不修改输入像素；调用者负责 RGB565 的线上字节顺序。若改用 DMA，回调必须等 DMA 结束再返回，并处理 CM7 D-cache 的清理/失效和 DMA 可访问内存；此同步接口不支持异步交还 LVGL 绘制缓冲。

绘制 API `stm_lcd_st7789_draw_bitmap(&lcd, x1, y1, x2, y2, pixels)`（ST7796 同理）的终点 **`x2/y2` 不包含在绘制区域内**。数组按行紧密排列，每像素 2 字节；先用小矩形或色条验证宽高、偏移和颜色，再打开完整 UI。返回码 `0` 成功、`-1` 参数或状态无效、`-2` 总线回调失败；不自动重试。

## 3. 可选：FT5206 I²C 触摸

FT5206 的 `read_reg(io, reg, buf, bytes)` 需要从寄存器地址开始连续读 `bytes` 字节，成功返回 0。厂商示例的读写地址为 `0x71/0x70`（8 位表示）；STM32 HAL 的 `HAL_I2C_Mem_Read` 接收**左移一位的 7 位地址**，常见写法为 `(0x38u << 1)`，以实物和实际 HAL 调用为准。

```c
#include "stm_lcd_touch_ft5206.h"
#include "i2c.h"

static int board_touch_read_reg(void *context, uint8_t reg,
                                uint8_t *data, size_t bytes)
{
    I2C_HandleTypeDef *bus = (I2C_HandleTypeDef *)context;
    if (bytes > UINT16_MAX) return -1;
    return HAL_I2C_Mem_Read(bus, 0x38u << 1, reg, I2C_MEMADD_SIZE_8BIT,
                            data, (uint16_t)bytes, 1000u) == HAL_OK ? 0 : -1;
}

static stm_lcd_touch_ft5206_t touch;
static int board_touch_init(void)
{
    const stm_lcd_touch_ft5206_config_t cfg = {
        .read_reg = board_touch_read_reg, .io = &hi2c_touch,
        .x_max = PANEL_WIDTH, .y_max = PANEL_HEIGHT,
        .swap_xy = 0, .mirror_x = 0, .mirror_y = 0,
    };
    int rc = stm_lcd_touch_ft5206_new_i2c(&touch, &cfg);
    /* 只有已接 FT5206 RST 且提供 reset/delay_ms 回调时才调用 reset。 */
    return rc;
}
```

循环中先 `stm_lcd_touch_ft5206_read_data(&touch)`，成功后再用 `stm_lcd_touch_ft5206_get_data(&touch, points, capacity, &count)` 读取最新触点。`get_data` 读取缓存而非重新发起 I²C；最多 5 点，`capacity` 限制拷贝个数。根据屏幕旋转方向设置 `swap_xy/mirror_x/mirror_y`。`read_data` 返回 `-2` 表示 I²C 读失败，`-3` 表示点数超限；失败时驱动清空旧触点。

## 4. 可选：连接 LVGL 9

先由工程提供 LVGL 9 目标和 `lv_conf.h`，初始化屏幕与可选触摸之后调用 `lv_init()`。粘合层只接收板级绘图和触摸函数，不依赖具体面板组件。

```c
#include "stm_lvgl_port.h"

static int board_draw(void *context, uint16_t x1, uint16_t y1,
                      uint16_t x2, uint16_t y2, const void *pixels)
{
    return stm_lcd_st7789_draw_bitmap((stm_lcd_st7789_t *)context,
                                       x1, y1, x2, y2, pixels);
}
static int board_read_pointer(void *context, int *pressed,
                              uint16_t *x, uint16_t *y)
{
    stm_lcd_touch_ft5206_t *t = (stm_lcd_touch_ft5206_t *)context;
    stm_lcd_touch_ft5206_point_t point;
    size_t count = 0;
    int rc = stm_lcd_touch_ft5206_read_data(t);
    if (rc == 0) rc = stm_lcd_touch_ft5206_get_data(t, &point, 1u, &count);
    if (rc != 0) return rc;
    *pressed = count != 0u;
    if (count != 0u) { *x = point.x; *y = point.y; }
    return 0;
}

static stm_lvgl_port_t display_port;             /* 全局静态，初始化时必须清零 */
static uint8_t draw_buffer[PANEL_WIDTH * 20u * 2u]; /* RGB565，20 行示例 */
static int board_lvgl_init(void)
{
    const stm_lvgl_port_config_t cfg = {
        .width = PANEL_WIDTH, .height = PANEL_HEIGHT,
        .draw_buffer = draw_buffer, .draw_buffer_bytes = sizeof(draw_buffer),
        .display_context = &lcd, .draw = board_draw,
        .touch_context = &touch, .touch = board_read_pointer, /* 没有触摸时将 .touch 留空 */
    };
    lv_init();
    return stm_lvgl_port_attach(&display_port, &cfg);
}
/* 应用通过定时器/任务提供 lv_tick_inc(实际经过的毫秒)，并定期调用 lv_timer_handler()。 */
```

`stm_lvgl_port_attach` 要求显示缓冲至少 `width * 2` 字节，LVGL 使用 RGB565、部分刷新。LVGL 的刷新坐标终点是**包含**的，粘合层会转换成面板 API 的**不包含**终点。`draw` 必须同步结束、使用完缓冲后返回；错误记在 `display_port.last_display_error`，输入错误在 `last_touch_error`。粘合层在失败时也会释放 LVGL 刷新缓冲，因此应由应用读错误状态并记录日志。退出前可调用 `stm_lvgl_port_detach`，调用后重新 attach 前保持 port 结构体清零。LVGL tick 和 handler 的运行线程、任务锁由应用自行安排。

## 5. 次日实板验证清单

1. 记录实际模组型号、芯片丝印、供电电压、接线/排线方向和外设引脚；核对现有存储外设资源无冲突。
2. 先只接单个面板驱动：上电、复位、初始化，背光最后打开；分别绘制纯色和四角定位点，验证坐标、方向、色序和像素字节序。记录返回码及 HAL 错误码。
3. 若有 FT5206，读寄存器并逐角触摸，核对读到的坐标、旋转与屏幕方向；没有对应芯片则不启用组件。
4. 最后接 LVGL 9：刷新小矩形、全屏及连续动画，观察图像、触摸、刷新耗时与错误码；检查与已有 EEPROM、SDRAM、QSPI、SDMMC 的联合启动。
5. 确认所用模组、版本、固件、接线、日志、测试结果；**当前完成的是主机侧测试与 H723/H757 编译检查，不代表屏幕实板已经通过**。
