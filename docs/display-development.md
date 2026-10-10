# 显示组件开发规范

本文件是新增或迁移屏幕、触摸驱动，以及扩展 LVGL 粘合层的共同开发依据。通用维护、依赖和发布政策见 [CONTRIBUTING.md](../CONTRIBUTING.md)，使用已有组件见[显示接入指南](display-components.md)。规范要求与当前支持能力分开描述；接口事实以目标版本公开头文件、实现和测试为准，不能把规划当作已实现 API。

## 1. 开始前：版本基线与阅读顺序

当前统一接口基线为 `stm_lcd`、两个 AXS15231B 驱动及 `stm_lvgl_port` 的 `v1.0.0`，实际组合由[组件表](../README.md)及 gitlink 固定。五款驱动的固定 `v0.2.0` tag 仍使用旧 API。本地工作区已将 ST7789、ST7796、ILI9881C、FT5206、GT9271 迁移为通用句柄，并扩展框架与 port；尚未更新 gitlink 或发布。使用本地扩展必须选择同一组源码，旧 H757 DIRECT 板测不能作为迁移后的验收。2026-10-11 本地迁移组合已完成 H757 ILI9881C/GT9271 的 DIRECT 诊断 Debug 回归；范围及未验证项见[接入指南](display-components.md#本地迁移组合尚未发布)，不代表其他器件或已发布 gitlink 通过验收。

1. 检查根仓库和目标子模块的状态、HEAD、暂存区引用及局部 AGENTS.md，保留用户改动，不自动升级其他组件。
2. 阅读本规范、目标组件 README/CMake/公开头文件、芯片与具体模组资料；确认分辨率、总线、像素格式、复位/供电及共享引脚。不猜接线或初始化表。
3. 读框架[公开接口](../lib/stm_lcd/include/stm_lcd.h)及[实现者操作表](../lib/stm_lcd/include/stm_lcd_impl.h)。面板参考 [AXS 驱动](../lib/stm_lcd_axs15231b/src/stm_lcd_axs15231b.c)，触摸参考 [AXS 触摸驱动](../lib/stm_lcd_touch_axs15231b/src/stm_lcd_touch_axs15231b.c)，只借鉴结构，不复制芯片协议。
4. 涉及 port 再读[配置与生命周期](../lib/stm_lvgl_port/include/stm_lvgl_port.h)及[渲染限制](../lib/stm_lvgl_port/docs/render-modes.md)；涉及 HAL 才读[适配器说明](../lib/stm_lcd/adapters/stm32f4/README.md)。
5. 先列能力清单、修改边界和测试计划。发现现有接口不能表达硬件要求时先提出扩展设计，不在应用堆连接包装或伪造同步完成。

## 2. 组件边界与依赖方向

```text
应用：硬件配置、共享复位协调、创建对象、创建 UI、调用 process
                                  │
                           stm_lvgl_port
                                  │ 通用句柄
                     stm_lcd panel / touch 公共接口
                                  │ 操作表
                       各芯片面板 / 触摸实现
                                  │
                            stm_lcd IO
                                  │
                       MCU 外设 / DMA / 缓存适配
```

公共接口由框架定义，芯片组件和 port 均依赖框架；框架不反向依赖任何芯片或 LVGL。

| 层 | 应当负责 | 不应负责 |
| --- | --- | --- |
| `stm_common` | 跨领域基础类型与错误定义 | 屏幕/触摸专属接口 |
| `stm_lcd` | IO、面板、触摸契约，资源借用和快照等公共薄封装 | 芯片判断、LVGL、日志、RTOS、设备注册中心 |
| 芯片面板驱动 | 模组初始化、窗口/像素命令、支持的显示控制 | HAL 初始化、LVGL flush、业务 UI、通用轮询状态机 |
| 芯片触摸驱动 | 真实总线协议、帧校验、原始触点解析 | LVGL 状态转换、重复镜像/交换轴、通用离线重试 |
| IO/平台适配器 | 外设事务、DMA 分段和停止、缓存一致性、完成邮箱 | 芯片窗口命令、UI、擅自占用 HAL 全局回调 |
| `stm_lvgl_port` | LVGL 初始化/tick、刷新完成连接、输入服务与协作式 handler | 按芯片名分支、直接访问 HAL、分配大帧缓冲 |
| 应用 | 接线/时钟/外设配置、复位协调、设备创建、UI 和业务 | draw/wait/touch/flush_ready 包装、另一层 display_service |

换芯片修改驱动；换总线/MCU 修改适配器；新增通用渲染/输入语义才扩展框架或 port。不为每个芯片增加新的公共框架组件。

## 3. 通用契约：所有新驱动必须遵守

### 3.1 构造、借用与删除

- 芯片构造函数返回通用 panel/touch 句柄；实现对象的首成员为对应已清零 base，操作表持续有效，不额外分配转发包装对象。构造不访问硬件，复位和初始化显式执行。
- `out` 必须有效且 `*out == NULL`；已有对象时返回错误，不能清空或覆盖原句柄。初始空输出在任何失败路径仍为空；检查参数、分配、base 初始化，最后才发布句柄。
- 当前 base 初始化成功后完成借用。将可能失败的配置检查放到这一步之前，避免订阅/借用后增加无回滚步骤；若必须增加，逐项逆序解除并测试，不只 free 内存。
- IO 和硬件由调用方持有，panel/touch 借用 IO，port 借用设备、缓冲和回调上下文。复制配置不复制其指向资源；借用资源应比对象存活更久。
- 只通过框架初始化、订阅/借用、释放和删除接口管理 base；芯片 destroy 仅释放实现对象，不删除 IO 或共享外设，不手动修改公共 pending/owner/borrowers。
- 当前一个 IO 只有一个面板完成订阅者，一个面板只有一个刷新接入所有者；这不是线程安全或多显示支持。按创建逆序清理：停止提交并服务完成 → 删除 port → 删除设备 → 清除 IO → 释放硬件。
- 在途、回调分发、process 内不得删除对象；删除失败必须保留有效句柄。不得提前释放仍被硬件或设备借用的内存。

### 3.2 面板矩形、像素和能力

- 当前公共绘图矩形为 `[x1, x2) × [y1, y2)`，右/下端点不包含。控制器若使用包含端点，由驱动转换为 `x2 - 1`、`y2 - 1`，不可改变公共定义。
- 当前统一绘图路径为紧密排列 RGB565，无任意 stride 参数。窗口尺寸/偏移、总线长度与乘法溢出须检查；同步传输返回时硬件不得继续引用像素。
- 每次绘图必须建立正确的独立窗口和像素写入语义，特别测试非零 y 起点、小矩形、相邻/不相邻窗口。是否允许续写由芯片协议决定，不能照抄其他芯片的命令。
- RGB/BGR、RGB565 字节序、地址偏移是不同问题。明确每个转换由哪一层处理，不能由驱动和 port 重复交换；用彩条和边角像素验证。
- ops 按实际能力填写。不支持的可选 reset、显示开关、窗口或异步绘图返回 `STM_ERR_NOT_SUPPORTED`，不以返回成功的空函数蒙混通过。能够接入当前 port 的面板至少提供可用绘图能力；构造阶段检查该实现需要的 IO 操作。
- 不为使代码符合表面 API 而把 LTDC/RGB/DSI 帧缓冲驱动包装成已同步完成的 SPI 写入。当前框架不能表达的行为按第 6 节扩展。

### 3.3 异步完成与错误保护

```text
LVGL 渲染 → port 提交 → panel 请求 → IO/DMA 传输
                          IRQ 只记录状态
主循环 process → 确认硬件停止 → IO complete → panel complete → LVGL flush ready
```

- 面板异步实现通过公共 IO 异步接口提交，不能自行调用 LVGL 或绕开框架的完成链。平台 IRQ 仅记录邮箱状态，公共完成操作在主循环执行。
- “DMA 中断到达”“函数返回错误”“超时到达”均不等于硬件已停止。适配器必须确认 SPI/DMA 不再访问像素、完成必要停止与缓存维护后，才允许归还缓冲；不能以超时直接 flush ready。
- 成功接收的请求最终安全完成恰好一次。提交失败且确认硬件空闲时回滚；即使提交报错，只要硬件仍忙就必须继续持有缓冲、服务在途请求，不能立刻复用。
- 重复/异常完成不得释放另一笔请求；立即完成、超时、终止、硬件停止失败均有测试。停止失败继续保护资源并暴露错误，不能伪造成功或通过删除对象逃避。
- port 的显示错误锁存可阻止新绘图，但不能停止在途 IO 服务。诊断开关仅控制观察/展示，不关闭超时、所有权或错误保护。
- 禁止 ISR 调用通用操作/port、递归 process，以及在观察回调中调用 LVGL 或删除对象。HAL 全局回调由消费工程显式转发，适配器不抢占。

### 3.4 触摸协议、快照与坐标

- 驱动 `read_data` 只输出原始触点和数量；先令数量为零，完整读帧、校验长度/状态/数量后再发布。协议定义的无触点帧/零触点为正常松手；截断或畸形帧返回 `STM_ERR_VERIFY`，通信失败保留 `STM_ERR_IO`/`STM_ERR_TIMEOUT` 等实际错误，不随意复用错误码。
- 当前只支持单点快照。控制器原生多点时必须明确单点选择规则和异常计数处理；不能越界写输出，也不能宣称完整支持多点。需要多点时先升级公共契约与测试。
- 公共 read 更新快照；get 不访问总线、不消费快照。读取失败会清空快照，不能无限保留上一次按下。
- 交换轴 → 检查逻辑边界 → 镜像由公共框架执行一次；镜像端点为 `max - 1 - coordinate`。当前越界会得到空快照，不等于总线故障。驱动输出与配置范围必须匹配；需要缩放/校准时先定义转换位置，不能多层重复变换。
- 协议按芯片资料选用。当前 IO 的 raw write/read 是独立事务；不能假设 write 后 read 自动提供 repeated START，也不能强行把所有触摸改成寄存器读取。硬件若要求现有 IO 不支持的组合事务，先设计可选 IO 能力及适配测试。
- 当前 port 默认 20 ms 采样、200 ms 过期释放、通信故障离线、1000 ms 探测重试；这些是可配置默认值，不是触摸驱动的内置调度。畸形帧释放但不直接判为总线离线。
- DMA 等待期间可继续服务独立 I2C 输入，不递归进入 LVGL；共享同一 IO/总线则需单独证明仲裁和时间约束，不能假定仍可并行。恢复不得自动执行可能影响屏幕的共享复位；复位协调属于应用。

## 4. 最小实现骨架

下面只展示 `v1.0.0` 的对象与生命周期结构，分别作为两个翻译单元。`example_panel_*`、`example_touch_read_raw` 是必须按芯片协议实现的函数声明，不是可运行 Demo，不得用空成功 stub 代替。公开配置/构造声明应放进各组件头文件并补 Doxygen；实际驱动还须检查其 IO 能力、控制回调、偏移和协议参数。参考 AXS 实现补齐，不复制其初始化表或触摸报文。

### 4.1 面板实现

```c
#include "stm_lcd_impl.h"
#include <stdlib.h>

typedef struct
{
    stm_lcd_io_handle_t io; // 借用的 IO。
    uint16_t width, height; // 非零逻辑尺寸。
} lcd_example_config_t;

struct lcd_example
{
    struct stm_lcd_panel base;   // 首成员，框架管理生命周期。
    lcd_example_config_t config; // 芯片配置副本，资源仍为借用。
};

stm_err_t example_panel_init(stm_lcd_panel_handle_t panel);
stm_err_t example_panel_draw(stm_lcd_panel_handle_t panel,
                             uint16_t x1,
                             uint16_t y1,
                             uint16_t x2,
                             uint16_t y2,
                             const void *pixels);

static void panel_destroy(stm_lcd_panel_handle_t panel)
{
    free(panel);
}

static const stm_lcd_panel_ops_t panel_ops =
{
    .init = example_panel_init,
    .draw = example_panel_draw,
    .destroy = panel_destroy,
};

stm_err_t lcd_example_create(const lcd_example_config_t *config, stm_lcd_panel_handle_t *out)
{
    if (!config || !out)
    {
        return STM_ERR_INVALID_ARG;
    }
    if (*out)
    {
        return STM_ERR_INVALID_STATE;
    }
    if (!config->io || !config->io->ops || !config->width || !config->height)
    {
        return STM_ERR_INVALID_CONFIG;
    }
    struct lcd_example *panel = calloc(1, sizeof(*panel));
    if (!panel)
    {
        return STM_ERR_NO_MEM;
    }
    panel->config = *config;
    stm_err_t err = stm_lcd_panel_base_init(&panel->base, &panel_ops, config->io, config->width,
                                            config->height);
    if (err != STM_OK)
    {
        free(panel);
        return err;
    }
    *out = &panel->base;
    return STM_OK;
}
```

该骨架是同步路径。异步扩展须实现 `draw_async`，通过 `stm_lcd_io_tx_color_async` 提交，验证 IO 的异步能力和完成服务；不是把同步函数名改为 async。

### 4.2 触摸实现

```c
#include "stm_lcd_impl.h"
#include <stdlib.h>

typedef struct
{
    stm_lcd_io_handle_t io;             // 借用的 IO。
    stm_lcd_touch_config_t coordinates; // 公共坐标变换配置。
} lcd_touch_example_config_t;

struct lcd_touch_example
{
    struct stm_lcd_touch base;         // 首成员，框架管理快照。
    lcd_touch_example_config_t config; // 控制器配置副本。
};

stm_err_t example_touch_read_raw(stm_lcd_touch_handle_t touch,
                                 stm_lcd_touch_point_t *point,
                                 size_t *count);

static void touch_destroy(stm_lcd_touch_handle_t touch)
{
    free(touch);
}

static const stm_lcd_touch_ops_t touch_ops =
{
    .read_data = example_touch_read_raw,
    .destroy = touch_destroy,
};

stm_err_t lcd_touch_example_create(const lcd_touch_example_config_t *config,
                                   stm_lcd_touch_handle_t *out)
{
    if (!config || !out)
    {
        return STM_ERR_INVALID_ARG;
    }
    if (*out)
    {
        return STM_ERR_INVALID_STATE;
    }
    if (!config->io || !config->io->ops)
    {
        return STM_ERR_INVALID_CONFIG;
    }
    struct lcd_touch_example *touch = calloc(1, sizeof(*touch));
    if (!touch)
    {
        return STM_ERR_NO_MEM;
    }
    touch->config = *config;
    stm_err_t err =
        stm_lcd_touch_base_init(&touch->base, &touch_ops, config->io, &config->coordinates);
    if (err != STM_OK)
    {
        free(touch);
        return err;
    }
    *out = &touch->base;
    return STM_OK;
}
```

协议函数用 `touch->io` 访问所需 IO，校验后输出零或一个原始点；不执行 swap/mirror，不实现 LVGL pressed/released。当前没有通用触摸 init 操作，不能发明 `stm_lcd_touch_init()`；若器件必须独立配置启动，先定义适合的芯片专用步骤或提出框架扩展，不能悄悄在构造中访问硬件。

## 5. 新驱动编写与旧驱动迁移流程

1. **建立能力表**：记录芯片/模组、总线事务、初始化/复位、窗口和颜色格式、同步/异步能力、触摸帧结构与原始范围、硬件限制及资料来源。区分现有接口、可选不支持和确需扩展的能力。
2. **实现最小协议**：先按第 4 节嵌入 base，保留已验收协议和初始化表，返回通用句柄。业务通过公共 panel/touch API 使用；芯片配置只保留真实差异，不加入业务 UI 或通用运行状态机。
3. **先做假 IO 测试**：录制命令/数据/事务边界，测试非零窗口、边界像素、故障与资源回滚；触摸逐字节构造正常/异常帧，验证原始解析及公共变换后的结果。不依赖“画面看起来正常”代替协议测试。
4. **再接入同一 port**：无触摸、同步、可用时异步均使用同一份 port 源码。应用只创建板级设备、配置 port、创建 UI，并在主循环调用一个处理入口；不能增加 draw/wait/touch 包装来掩盖接口缺口。
5. **迁移全部消费入口**：旧驱动逐项映射原公开操作与测试，同步头文件、CMake、示例、README、AGENTS 和集成检查。正常删除旧连接实现，不只是换文件夹；不得删原有测试来通过，也不得顺手迁移无关驱动。
6. **验证并交付**：执行第 8 节对应检查，报告精确提交、支持能力与未验证项。破坏性 API 迁移按 major 发布，旧 tag 保留；是否保留旧 API 包装须在具体任务确认，不自行增加双套 API。发布与双镜像/聚合同步按通用政策，须有当前用户授权。

旧五驱动逐个迁移，不把 AXS/F407 协议、共享复位和刷新对齐当作通用条件。示例保持板级逻辑薄，实际应用可以一个独立显示文件完成设备和 port 创建，不因组件数量增加必需的 BSP/display 服务目录。

## 6. 公共框架和 LVGL port 扩展规则

### 6.1 先判断扩展位置

| 需求 | 优先位置与处理 |
| --- | --- |
| 新芯片初始化表、寄存器、窗口、触摸帧 | 芯片驱动；port 不出现芯片名判断 |
| 新 MCU SPI/I2C、DMA、总线事务或缓存要求 | IO/平台适配；公共 IO 无法表达才新增可选操作 |
| 通用面板控制、旋转、像素布局 | 先定义 panel/IO 契约和能力，再让驱动实现，port 按通用能力使用 |
| LVGL 脏区、调度、缓冲衔接、输入转换 | port；不得直接操作 HAL 或芯片寄存器 |
| 接线、上电、共享复位、UI | 消费工程，不回填通用组件 |

新增可选能力可保持既有驱动可用；缺失时明确 NOT_SUPPORTED 或在创建阶段拒绝不满足要求的配置，不隐式降级。不要靠读取内部字段或具体型号代替能力接口。

### 6.2 当前能力与后续设计分开

已发布 port v1.0.0 支持 LVGL 9、PARTIAL RGB565、外部缓冲、可选单点触摸和协作式主循环。本地扩展保持 PARTIAL 为零值默认，增加显式 DIRECT 双缓冲；没有 FULL、任意 stride、多显示管理或 RTOS 服务。F4 原始适配器不提供新增寄存器和整帧能力，不能因此声明支持全部 MCU/总线。

本地迁移经明确授权，增加 `draw_region`、`present/process/busy/stop_scanout` 及原子 `read_reg/write_reg`。ILI9881C 保留 DCS 初始化，板级提供 LTDC/DSI 的区域复制或整帧扫描适配；FT5206/GT9271 使用各自 8/16 位寄存器事务。详见[接入指南](display-components.md)和[渲染契约](../lib/stm_lvgl_port/docs/render-modes.md)。FULL、多点 LVGL 输入、旋转、其他像素格式、多显示和 RTOS 仍需单独设计。每项扩展至少说明：

- **语义**：逻辑/物理尺寸、坐标变换归属、像素格式/字节序/stride、刷新区域，现有字段是否足够。
- **所有权与完成**：谁持有哪个缓冲、何时允许 CPU 重用，提交、DMA 完成、扫描/VSync/换帧各自含义；DIRECT/FULL 不能套用“字节传输结束即完成”。
- **安全**：超时/终止/停止失败、缓存/内存限制、共享总线仲裁，必要的硬件同步。不隐藏所有权或绕开错误保护。
- **兼容性**：新增能力是否可选，旧驱动缺失时如何失败，API/ABI 与版本影响。保留现有配置默认语义，不能硬编码新板子的参数。
- **验证**：假设备证明协议和状态机，现有 AXS 路径回归，至少一套不同实现证明 port 可替换，再做指定硬件验收；旧硬件结论不能移用。

port 必须保持芯片无关；若必须扩展公共接口，应作为明确可审查的框架改动，而不是同时悄悄修改驱动、应用和 port 让测试恰好能通过。

## 7. 板级特例不是通用默认

以下仅为当前已说明的 F407/AXS15231B 参考组合，详细验收范围见[接入指南](display-components.md)：

| 当前特例 | 其他驱动应如何处理 |
| --- | --- |
| SPI 21 MHz、170×560 原生竖屏 | 按芯片、模组及硬件确定，不套用旋转或时钟 |
| RGB565、两块16行 SRAM 缓冲（各5440字节） | 当前 port 的格式限制仍适用；缓冲行数/位置按硬件配置并验证 |
| 渲染前全宽、8行对齐 | 当前刷新策略配置，不加入新芯片的强制规则，不在渲染后扩区传输未渲染像素 |
| AXS 独立 CASET/RASET/RAMWR | 别的芯片按其协议决定窗口与续写方式 |
| AXS 写请求—STOP—独立读响应、单点 | 不套用到要求寄存器/组合事务的控制器 |
| swap_xy=1、mirror_x=0、mirror_y=1；不操作 PD15 | 仅当前板子坐标/接线，其他硬件重新核对 |

## 8. 验证矩阵与架构验收

检查命令和环境见 [ci/README.md](../ci/README.md)，按实际修改选择；缺依赖应明确报错，不造空 target、不修改 HAL/LVGL 供应商源码来通过。

| 检查层 | 必须覆盖的内容 |
| --- | --- |
| 独立组件 | C11/C++17 公共头消费、参数/分配失败、构造无硬件访问、生命周期与借用回滚，核心不依赖 HAL/LVGL |
| 面板协议 | 独立/非零窗口、包含端点转换、长度与偏移/溢出、颜色/字节序、命令或像素提交失败、不支持能力 |
| 异步生命周期（适用时） | 提交成功/失败、立即/重复/异常完成、超时、终止、停止失败、在途删除、订阅解除、不得提前复用缓冲 |
| 触摸 | 零/单触点、畸形/截断帧、通信失败、越界、变换端点、多次 get 不消费、失败清空、过期释放、离线恢复 |
| port 可替换性 | 同一 port 源码接另一套假面板/假触摸，无触摸/同步/异步，DMA 等待期间独立输入、重入/回调限制、错误后继续完成服务 |
| 依赖解析 | 已有 target/alias、本地来源与优先级、同级源码、固定 SHA/镜像、禁止下载/完全离线失败、共享依赖正反添加顺序 |
| 固件构建 | 消费工程完整编译/链接，同步/DMA及诊断关闭；非LVGL彩条模式适用时检查，记录 Flash/RAM、DMA可访问内存及缓存约束 |
| 实板验收 | 初始化、彩条/边角、局部刷新、残影、拖动/松手/方向、按方案断连恢复；时间范围和硬件条件独立记录 |

审查时确认：应用/BSP 没有 LVGL 绘图/完成/等待/触摸连接包装及通用状态机；驱动没有 HAL/LVGL 耦合；port 没有芯片判断；诊断关闭不关闭安全机制；旧测试覆盖已映射而非删除。测试结果、完整链接、实板验收分别报告，不因软件通过就声明未测试器件、渲染模式或长时间运行正常。

可从新/已迁移组件根目录运行基础主机测试（使用主机编译器，不使用 MCU 工具链；先准备实际依赖）：

```sh
cmake -S tests -B build/tests -G Ninja
cmake --build build/tests
ctest --test-dir build/tests --output-on-failure
```

涉及依赖、port 或平台适配时继续执行 CI 文档中的相应真实依赖/集成检查；骨架语法检查不等于协议、链接或硬件通过。

## 9. 注释、文档与交付清单

- C11、Allman 括号、4 空格；按组件自己的 `.clang-format` 处理自有代码，不格式化供应商文件。
- C/H 文件头只保留 `@file` 与一句 `@brief`。公开函数声明使用 Doxygen 描述参数、返回值和关键限制，void 不写虚构返回值；C 实现不写函数 Doxygen，函数前至多一句简短中文 `//`。
- struct/enum 可以有一句整体说明；字段和枚举项仅用同行右侧简短 `//`，不在每个成员上方放块注释，不使用 `/**< */`。复杂原因/硬件约束简短说明，不写教学段落或修改历史。
- 保留维护者 MIT 及必要第三方授权信息，不因统一注释删除许可或改署第三方作者。
- 各独立组件提供 README、AGENTS、公开头、CMake、最小示例及测试。README 面向人，Agent 提示在简介后合为一段；AGENTS 提供阅读路径及该芯片独有约束，不复制整套聚合规范。
- 独立组件不能要求用户必须克隆聚合仓库才能使用；各自保留必要接口与依赖说明。聚合规范是开发依据，不是组件构建依赖。
- 默认依赖策略遵循通用约定：复用已有 target、本地显式来源及同级源码优先，需要网络时仅固定发布验证 SHA/校验归档，支持禁用下载和可信镜像。当前 `stm_lcd` 与 port 的框架来源要求、AXS 默认 pin 以各自 CMake 为准，不因写规范自动增删下载路径。
- 交付列出改动组件/文件、旧操作和测试映射、实际依赖来源/版本、命令及结果、支持/不支持能力、硬件与未验证项。组件发布后才更新聚合 gitlink、版本徽章与组合说明，不覆盖旧 tag；总仓库不打版本 tag。

### 交给后续 Agent 的任务提示

> 按 stm32-hal-lib 的 AGENTS.md、CONTRIBUTING.md 和 docs/display-development.md，将 `<屏幕/触摸组件>` 迁移到当前 stm_lcd 通用接口。先检查目标子模块、芯片/模组资料和已有测试，保留已验收协议；返回通用句柄，让同一 stm_lvgl_port 源码无需按芯片修改即可接入。不要改无关组件或供应商源码，不删测试、不增加应用连接包装；接口缺口先说明。同步目标组件文档、示例与 CI，报告编译、测试和未验证项；未经当前授权不烧录、发布或推送。
