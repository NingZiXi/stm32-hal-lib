# STM32 显示与触摸组件接入指南

每个芯片独立维护组件，板级负责传输、GPIO、电源和时序；LVGL port 连接显示/输入回调。没有额外的通用显示或触摸转发层，不兼容 ESP-IDF API。本文针对总仓库当前 gitlink 的五款芯片组件 `v0.2.0` 与 `stm_lvgl_port v0.2.1`，`v0.1.0` 保留旧接口。使用旧 tag 时请读取该 tag 的组件文档，不直接复制本文的新接口。新增 AXS15231B 显示与触摸组件固定为未标记版本的提交，采用同类句柄/回调契约；其 STM32F407 示例和验证范围以组件 README 为准。当前提交与发布状态见[总仓库组件表](../README.md)。

## 1. 选择与添加组件

| 器件/功能 | 组件与中文示例 | 边界 |
| --- | --- | --- |
| ST7789 SPI | [stm_lcd_st7789](../lib/stm_lcd_st7789/examples/stm32_hal/README.md) | 独立命令表、窗口、RGB565 写入 |
| ST7796 SPI | [stm_lcd_st7796](../lib/stm_lcd_st7796/examples/stm32_hal/README.md) | 独立命令表、窗口、RGB565 写入 |
| ILI9881C DSI | [stm_lcd_ili9881c](../lib/stm_lcd_ili9881c/examples/stm32_hal/README.md) | 已测 10.1 寸模组 DCS 初始化，DSI/LTDC 归板级 |
| FT5206 I²C | [stm_lcd_touch_ft5206](../lib/stm_lcd_touch_ft5206/examples/stm32_hal/README.md) | 8 位寄存器、最多 5 点 |
| GT9271 I²C | [stm_lcd_touch_gt9271](../lib/stm_lcd_touch_gt9271/examples/stm32_hal/README.md) | 16 位寄存器、最多 10 点、帧 ACK |
| AXS15231B SPI | [stm_lcd_axs15231b](../lib/stm_lcd_axs15231b/examples/stm32_hal/README.md) | SPI 命令、窗口与 RGB565，板级提供模组初始化表，不支持 QSPI |
| AXS15231B I²C | [stm_lcd_touch_axs15231b](../lib/stm_lcd_touch_axs15231b/examples/stm32_hal/README.md) | 11 字节查询命令、8 字节响应、单点坐标与变换 |
| LVGL 9 | [stm_lvgl_port](../lib/stm_lvgl_port/examples/stm32_hal/README.md) | 同步 PARTIAL RGB565，输入可选 |

只选实物对应组件。旧 stm_display/stm_lvgl 已退出，不继续使用其 API。参考职责来自乐鑫独立 LCD 组件和 esp_lvgl_port，当前库不提供其 RTOS 任务、自动定时器或异步 DMA 能力。

```cmake
# Lib/stm_common 可同级提供，也可提前定义其 target。
add_subdirectory(Lib/stm_lcd_st7789)
target_link_libraries(your_firmware PRIVATE stm_lcd_st7789)
# 需要 LVGL 时先提供 LVGL 9 的 lvgl target 和 lv_conf.h。
add_subdirectory(Lib/stm_lvgl_port)
target_link_libraries(your_firmware PRIVATE stm_lvgl_port)
```

组件复用已有 stm_common target，或自动加入同级源码；否则固定下载 stm_common v1.0.0 提交 ce3d186dde2d374a8e9c7b9068a7b88f97d57dc1。STM_COMMON_FETCH=OFF 禁止网络，STM_COMMON_GIT_REPOSITORY 可指定 Gitee 镜像，FETCHCONTENT_SOURCE_DIR_STM_COMMON 可指定离线源码。

## 2. 板级 HAL 适配与句柄

CubeMX 配置实际 GPIO/总线；芯片组件不硬编码 MCU 系列或板级引脚。SPI 示例用 8-bit 数据宽度，CS 覆盖命令与全部像素；I²C 地址存 7 位值，HAL 参数左移一位。GT9271 的 INT/RST 地址选择和屏幕背光时序由板级完成。示例 example.c/example.h 复制到应用后按中文说明填写 HAL 句柄和引脚，不自动编入芯片库。

```c
static lcd_st7789_handle_t panel = NULL;
const lcd_st7789_config_t cfg = {
    .tx_param=board_tx_param, .tx_color=board_tx_color,
    .delay_ms=board_delay_ms, .reset=board_reset, .io=&board_io,
    .width=PANEL_WIDTH, .height=PANEL_HEIGHT,
};
stm_err_t err = lcd_st7789_create(&cfg, &panel);
if (err == STM_OK) err = lcd_st7789_reset(panel);
if (err == STM_OK) err = lcd_st7789_init(panel);
if (err != STM_OK) lcd_st7789_delete(&panel);
```

create 只分配小型控制对象并复制配置，不访问芯片；out 必须指向 NULL 句柄，重复创建返回 INVALID_STATE 且原对象不变。面板统一 reset/init 顺序，ILI9881C init 不再隐式复位。delete(&handle) 释放对象、清空句柄，空句柄也成功，不关闭或释放借用的 HAL/总线/背光/缓冲。删除前停止并发访问并清除别名。

所有操作及传输/复位回调返回 stm_err_t，delay_ms 返回 void。HAL_OK→STM_OK、HAL_TIMEOUT→STM_ERR_TIMEOUT、HAL_ERROR/HAL_BUSY→STM_ERR_IO；底层统一错误原样传递。只用 err != STM_OK 检查，禁止 err < 0。回调必须同步完成，阻塞 API 不从中断调用；共享总线整笔事务加锁，DMA/DCache 一致性由板级保证。

## 3. 绘图与触摸

draw_bitmap(handle,x1,y1,x2,y2,pixels) 使用半开矩形 [x1,x2)×[y1,y2)，每像素 2 字节、紧密按行排列；tx_color 长度是字节，调用者负责像素容量和线上色序。参数失败不访问硬件；复位/初始化失败不得绘图，可重新初始化。绘图通信失败停止后续命令，可能已写部分像素，不回滚、不重试，实例仍可使用。

触摸采用 lcd_touch_<型号>_create/read_data/get_data/delete。逻辑尺寸是 swap_xy 后的尺寸，方向仅允许 0/1；越界点过滤。get_data 复制 min(点数,capacity)，capacity=0 允许 NULL 数组，失败时有效 count 清零。通信或畸形帧失败清空缓存，下一次读取可恢复。GT9271 没有新帧时保持状态，仅有效零点帧释放；就绪帧解析失败仍尝试 ACK，返回首个错误。ID 不匹配返回 NOT_SUPPORTED，并保留实际读到的 ID。

## 4. LVGL 注册与板级扩展

```c
lvgl_port_handle_t port = NULL;
lvgl_port_config_t cfg = {
    .width=PANEL_WIDTH, .height=PANEL_HEIGHT,
    .draw_buffer=buffer, .draw_buffer_bytes=sizeof(buffer),
    .display_context=panel, .draw=board_draw,
    .touch_context=touch, .touch=board_touch, /* 无触摸设为 NULL。 */
};
lv_init();
stm_err_t err = lvgl_port_create(&cfg, &port);
lv_display_t *display = NULL;
if (err == STM_OK) err = lvgl_port_get_display(port, &display);
/* 应用设置 tick 并周期调用 lv_timer_handler。 */
lvgl_port_status_t status;
if (err == STM_OK) err = lvgl_port_get_status(port, &status);
/* 退出时停止 handler/所有访问，再 lvgl_port_delete(&port)。 */
```

buffer 至少一行 RGB565，最大 UINT32_MAX，满足 LV_DRAW_BUF_ALIGN。PARTIAL 回调将 LVGL 闭区间终点转换一次为半开区间；刷新失败也 flush_ready，输入失败释放，错误由 get_status 查询。create 在任意分配阶段失败都回收资源；delete 顺序为 indev→display→控制对象，外部缓冲/上下文始终归应用。

get_display/get_indev 返回借用对象，不得删除或替换 user_data，无触摸时 indev 为 NULL。板级可在首次绘制前配置 DIRECT 和自定义 flush，但自定义 flush 错误须由板级记录；组件 get_status 只记录其自身回调。组件不新增 DIRECT/DMA/VSYNC 功能。

## 5. PARTIAL / DIRECT 职责与数据流

通用 port 保持同步 PARTIAL；应用持有小块 RGB565 缓冲，draw 接收半开矩形、紧密行排列，返回前必须完成像素使用。组件转换闭区间坐标一次，并在成功或失败后调用 flush_ready。启动 DMA 后立即返回不符合该契约。

DIRECT 是消费工程通过借用 display 实现的扩展：首次 handler 前设置两块全屏缓冲、明确 stride 和自定义 flush，不替换 user_data。LVGL 管理双帧渲染区域同步，板级负责缓存一致性、扫描地址、安全切换和 flush_ready；自定义显示错误独立记录，触摸仍查询 port。旧前台还在扫描时不能继续复用；异步地址重载必须等待完成。

CPU 写、LTDC 读时先 clean 再提交，不 invalidate 尚未写回的像素。VSYNC 轮询只是特定 H757 实例策略，不等同通用 DMA/异步 VBlank 支持。同步切帧失败须锁存错误，当前 handler 返回后停止后续处理。详细责任表、缓存对齐、错误恢复及缓冲生命周期见 [stm_lvgl_port 刷新模式指南](../lib/stm_lvgl_port/docs/render-modes.md)。

## H757 外部板级参考（非本仓库固件）

以下参数记录既有 H757 消费工程的特定配置，该完整固件没有随本仓库分发。`STM_DISPLAY_LVGL_DEMO`、`STM_LVGL_OFFICIAL_WIDGETS` 是该外部工程的开关，不是组件或总仓库 CMake 选项；分别控制示例启用及官方 Widgets/诊断界面选择。该实例使用 ILI9881C/GT9271 与 LVGL 9.3.0；其他工程应按实际 CMake 配置接入。

该板级实例使用 800×1280 RGB565，两块缓冲 0xD0000000/0xD0200000，每块 2,048,000 字节、stride=1600；LVGL 96 KiB 池位于 0xD0400000。DIRECT 双缓冲、DCache clean、VSYNC 切帧、4ms 刷新和 1ms 服务属于该实例的设置，不可直接用作其他开发板配置。ILI9881C 命令表来自板厂实验 13，按维护者确认的 MIT 许可保留来源；不代表其他模组均适用。GT9271 地址 0x5d、swap_xy/mirror_x/mirror_y 均为 0。

2026-10-07，v0.2.0 配套实例通过诊断显示、触摸/按钮、五次软件复位、Release 启动及官方 Widgets 滑动/点击回归。未记录新的 FPS，未分别归档各角坐标。当前组合的验证边界见下节；这些地址、周期与现象仅描述该板级实例。

## v0.1.0 API 迁移表

| 旧用法 | 新用法 |
| --- | --- |
| stm_lcd_<型号>_t / stm_lcd_touch_<型号>_t | lcd_<型号>_handle_t / lcd_touch_<型号>_handle_t，初始化 NULL |
| new_panel/new_i2c(&instance,&cfg) | lcd_<型号>_create(&cfg,&handle) / lcd_touch_<型号>_create(&cfg,&handle) |
| stm_lvgl_port_t、attach/detach | lvgl_port_handle_t、lvgl_port_create/delete |
| config_t/point_t/MAX_POINTS 旧前缀 | lcd_<型号> 或 lcd_touch_<型号> 前缀；LVGL 类型使用 lvgl_port 前缀 |
| 操作传 &instance | 操作直接传 handle，只有 create/delete 传 &handle |
| 直接访问 port.display/indev/last_*_error | get_display/get_indev/get_status；DIRECT 错误板级独立记录 |
| int 与 -1/-2/-3 | stm_err_t、STM_OK 与公共错误；回调同步迁移，不保留兼容包装 |

状态和错误详细契约见对应提交的公开头文件；维护规则见[显示组件开发规范](display-development.md)。

## v0.2.0 组合的验证状态

| 组合 | 已有验证 | 范围与限制 |
| --- | --- | --- |
| ILI9881C / GT9271 / LVGL port v0.2.0 | H757 配套 800×1280 模组、LVGL 9.3.0 诊断持续刷新、触摸/按钮、五次软件复位、Release 启动，官方 Widgets 滑动/点击现场确认 | RGB565 DIRECT 板级扩展，mirror_x/y=0；未覆盖其他模组或长期稳定性，未单独归档各角坐标 |
| ST7789 / ST7796 / FT5206 v0.2.0 | 主机软件契约、中文 HAL 示例及公共头文件检查 | 本轮没有对应实物，硬件回归待完成 |
| 六组件及外部 H757 工程 | 默认存储、诊断 LVGL、官方 Widgets 的 CM4/CM7/顶层 Debug/Release 构建 | 构建不能替代硬件；默认 PARTIAL 刷新本轮仅主机测试 |

六组件保留 v0.1.0，并以新 v0.2.0 tag 固定统一接口；GitHub/Gitee 指向同一提交，GitHub 提供 Release 与迁移说明。总仓库只维护 main 与子模块组合，不创建版本 tag。具体测试契约见各组件同一版本 README；硬件原始日志和备份留在消费工程本地构建目录，不随驱动库公开。

## v0.2.1 粘合层文档与板级呈现整理

五款芯片组件继续固定 v0.2.0；stm_lvgl_port v0.2.1 只补充 PARTIAL/DIRECT 职责与中文接入文档，源码、公开 API、CMake 与 v0.2.0 相同。消费工程将 SDRAM 缓冲、MPU/DCache、VSYNC 与 DIRECT 提交集中到板级呈现模块，组件不承担这些板级资源。

2026-10-07，整理后的 H757 配套 ILI9881C/GT9271、LVGL 9.3.0 完成诊断 Debug 显示/触摸及连续五次复位、诊断 Release 按钮和官方 Widgets Debug 滑动/点击回归；显示及输入错误均为 0，默认存储 Debug 恢复后初始化与心跳正常。Widgets Release、默认存储 Release 完成构建，未另行烧录。默认 PARTIAL 本轮仅主机测试，未新增 FPS 基准、逐角坐标独立记录或长期稳定性结论。
