# stm32-hal-lib

[![CI](https://github.com/NingZiXi/stm32-hal-lib/actions/workflows/ci.yml/badge.svg)](https://github.com/NingZiXi/stm32-hal-lib/actions/workflows/ci.yml)

基于 STM32 HAL 的模块化驱动与基础组件库。组件独立维护，本仓库通过 Git submodule 汇集经过检查的版本，提供统一的使用入口。

这是应用层组件集合，不是 ST 官方 HAL 的镜像。当前存储驱动主要在 **STM32H723ZG** 上验证，具体支持范围以各组件说明为准。

配套的可复用开发技能集中在 [`skills/`](skills/README.md)，当前包含 STM32CubeMX + CMake 的 `main/` 应用结构与 `stm_log v3` 接入技能。

## 组件

| 组件 | 当前引用版本 | 用途 |
|---|---|---|
| [stm_common](https://github.com/NingZiXi/stm_common) | [![version 1.0.0](https://img.shields.io/badge/version-1.0.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_common/tree/ce3d186dde2d374a8e9c7b9068a7b88f97d57dc1) | `stm_err_t` 与公共错误码 |
| [stm_flash](https://github.com/NingZiXi/stm_flash) | [![version 4.0.0](https://img.shields.io/badge/version-4.0.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_flash/tree/2d44d3c091262a4d79b33b04ca47a8a04b2fee35) | NOR Flash 读取、分页写入、扇区擦除与校验 |
| [stm_sdram](https://github.com/NingZiXi/stm_sdram) | [![version 4.0.0](https://img.shields.io/badge/version-4.0.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_sdram/tree/86f106e8693f84a75e0ca120290e4867aee05e6c) | SDRAM 初始化、刷新、读写、填充及自检 |
| [stm_log](https://github.com/NingZiXi/stm_log) | [![version 2.4.0](https://img.shields.io/badge/version-2.4.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_log/tree/15642aa90fe3c5a91cd64680437f2ebd867ca20a) | 分级日志、标签过滤及自定义输出 |
| [stm_esp_hosted](https://github.com/NingZiXi/stm_esp_hosted) | [![version 0.8.0](https://img.shields.io/badge/version-0.8.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_esp_hosted/tree/v0.8.0) | ESP32-C3 SPI 主机、STA/AP Wi-Fi、异步任务与发送队列、恢复诊断、国家/信道/功率、可选 lwIP 网卡 |
| [stm_littlefs](https://github.com/NingZiXi/stm_littlefs) | [![version 1.0.2](https://img.shields.io/badge/version-1.0.2-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_littlefs/tree/6360940d6dfbefdb09f5eed76fb58891af035f0d) | LittleFS 分区块设备适配与文件系统接入 |
| [stm_eeprom](https://github.com/NingZiXi/stm_eeprom) | [![version 1.0.0](https://img.shields.io/badge/version-1.0.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_eeprom/tree/1ac5b9a8dc6612c5066cefb6b93f5ebbd7e6834c) | I2C EEPROM 器件与控制器适配 |
| [stm_sd](https://github.com/NingZiXi/stm_sd) | [![version 1.0.0](https://img.shields.io/badge/version-1.0.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_sd/tree/0ef93e067633d3ebc22e3f3aa8dc5d80f25d5d32) | SD NAND/TF 卡块设备与 SDMMC 适配 |
| [stm_fatfs](https://github.com/NingZiXi/stm_fatfs) | [![version 1.0.1](https://img.shields.io/badge/version-1.0.1-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_fatfs/tree/da4e096bfc7a2137929abca28775479b93b787f9) | FatFs 磁盘注册和块设备粘合层 |
| [esp_at_client](https://github.com/NingZiXi/esp_at_client) | [![version 0.5.0](https://img.shields.io/badge/version-0.5.0-5364b5?style=flat-square)](https://github.com/NingZiXi/esp_at_client/tree/b17f954c76ca4cc3cddcddad48faa1328d80a29f) | 平台无关 ESP-AT 轮询客户端，STM32 HAL 适配位于 ports/stm32_hal/ |
| [stm_lcd_st7789](https://github.com/NingZiXi/stm_lcd_st7789) | [![version 0.1.0](https://img.shields.io/badge/version-0.1.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_lcd_st7789/tree/81bcb60a282014432c58770a37db29c183066492) | ST7789 SPI 面板芯片驱动 |
| [stm_lcd_st7796](https://github.com/NingZiXi/stm_lcd_st7796) | [![version 0.1.0](https://img.shields.io/badge/version-0.1.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_lcd_st7796/tree/f3b01c31868be9697a4d157700c4729a3eb8eae5) | ST7796 SPI 面板芯片驱动 |
| [stm_lcd_touch_ft5206](https://github.com/NingZiXi/stm_lcd_touch_ft5206) | [![version 0.1.0](https://img.shields.io/badge/version-0.1.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_lcd_touch_ft5206/tree/9fa64830343e0610adbd7f17b0eaa69540365c4a) | FT5206 I2C 触摸芯片驱动 |
| [stm_lcd_ili9881c](https://github.com/NingZiXi/stm_lcd_ili9881c) | [![version 0.1.0](https://img.shields.io/badge/version-0.1.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_lcd_ili9881c/tree/2ba5622b9f8f47c4e6f6a85240c80d488d119417) | ILI9881C DSI 面板初始化，模组命令表仅适用于已测 10.1 寸屏幕 |
| [stm_lcd_touch_gt9271](https://github.com/NingZiXi/stm_lcd_touch_gt9271) | [![version 0.1.0](https://img.shields.io/badge/version-0.1.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_lcd_touch_gt9271/tree/53c68fe1de0acbbd47ed120ad5413163a23349f4) | GT9271 I²C 触摸与坐标读取 |
| [stm_lvgl_port](https://github.com/NingZiXi/stm_lvgl_port) | [![version 0.1.0](https://img.shields.io/badge/version-0.1.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_lvgl_port/tree/cd07ab8d66dc88b9c1ba0d2b309ac681e04d7470) | 独立于屏幕型号的显示与触摸接入 |
| [stm_ota](https://github.com/NingZiXi/stm_ota) | [![version 0.5.0](https://img.shields.io/badge/version-0.5.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_ota/tree/f9163d2a7efe2f67d089a62c413dc40360c49170) | 同步 OTA 下载、A/B 分区切换与 Flash 校验 |

显示、触摸与 LVGL 粘合层的首次版本统一为 `v0.1.0`（初始预览版本），GitHub Release 记录各组件的 API 与验证范围。ILI9881C、GT9271 和 LVGL port 已在 H757 配套模组完成实板验证；ST7789、ST7796、FT5206 已通过主机测试。

显示与触摸组件以中文 README 为默认入口，各自提供 `examples/stm32_hal/` 中文接入示例。屏幕组件按实际芯片拆分，旧 `stm_display` / `stm_lvgl` 已退出汇总仓库，旧远端已清理；从组件选择、CubeMX/CMake、HAL 传输回调到 LVGL 9 的步骤见[显示与触摸接入指南](docs/display-components.md)。H757 配套 ILI9881C/GT9271 模组已完成 LVGL 显示、触摸和五次复位的用户现场观察；默认存储固件已在无屏幕、TF 插入时复测五个外设初始化成功；最终板上恢复为 LVGL 示例。ILI9881C 命令表保留来源，并按维护者确认的 MIT 条款发布。

表中链接指向独立仓库的最新说明；当前固定版本的说明位于克隆后的 `lib/<组件>/README.md`。

版本徽章对应本仓库当前引用的提交，点击可查看该版本源码。自动同步任务每天查询各组件的最新稳定语义化版本 tag（`vX.Y.Z` 或 `X.Y.Z`），并更新子模块引用及徽章。尚无版本 tag 的组件保持当前提交，不自动跟随 `main`。新版本先创建草稿 PR，需审查兼容性并验证后合并；README 不会在新 tag 发布瞬间自行改变。

Flash、SDRAM 不依赖日志、RTT 或 RTOS。`stm_log` 保留现有 API；新设备驱动沿用 `flash_*`、`sdram_*` 这样的接口命名，规范见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 获取代码

在项目根目录执行：

```sh
git clone --recurse-submodules https://github.com/NingZiXi/stm32-hal-lib.git Lib/stm32-hal-lib
```

也可从 Gitee 获取，二选一即可：

```sh
git clone --recurse-submodules https://gitee.com/nzxhg/stm32-hal-lib.git Lib/stm32-hal-lib
```

子模块采用同账号下的相对地址：从 GitHub 克隆时使用 GitHub，从 Gitee 克隆时使用 Gitee。两个平台保持相同提交；CI 在 GitHub Actions 执行。

如果已经普通克隆过：

```sh
git -C Lib/stm32-hal-lib submodule update --init --recursive
```

**GitHub 的 Download ZIP 不包含子模块源码**，请优先使用上述命令。也可以根据各组件 README 单独克隆组件及其依赖。

目录结构：

```text
stm32-hal-lib/
├── lib/
│   ├── stm_common/
│   ├── stm_flash/
│   ├── stm_sdram/
│   ├── stm_log/
│   ├── stm_esp_hosted/
│   ├── stm_littlefs/
│   ├── stm_eeprom/
│   ├── stm_sd/
│   ├── stm_fatfs/
│   ├── fatfs/          # FatFs 固定源码副本
│   ├── esp_at_client/
│   └── stm_ota/
├── skills/               # 配套开发技能及其分发副本
│   ├── README.md
│   └── stm32-app-main/
├── ci/                  # 编译检查、文档检查及 CI 专用 HAL 配置
├── .github/workflows/
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

各组件自带的示例和测试保留在组件目录中。总仓库不复制驱动源码，也不分发 CubeMX 工程或 ST HAL/CMSIS。

## 接入 STM32CubeMX + CMake 工程

先由 CubeMX 生成并创建 `stm32cubemx` 目标，再在工程根 `CMakeLists.txt` 中按需添加组件：

```cmake
set(STM_LIB_DIR "${CMAKE_CURRENT_SOURCE_DIR}/Lib/stm32-hal-lib/lib")
add_subdirectory(${STM_LIB_DIR}/stm_common)
add_subdirectory(${STM_LIB_DIR}/stm_flash)
add_subdirectory(${STM_LIB_DIR}/stm_sdram)
target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE stm_flash stm_sdram)
```

只使用一个驱动时，删除另一个驱动的两处引用即可。`stm_common` 是头文件库，驱动会传递它的 include 路径；已经在其他位置添加过该目标时，不要重复添加。

需要 EEPROM、SD 或 FatFs 时，按需添加对应组件：

```cmake
add_subdirectory(${STM_LIB_DIR}/stm_eeprom)
add_subdirectory(${STM_LIB_DIR}/stm_sd)
add_subdirectory(${STM_LIB_DIR}/stm_fatfs)
target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE stm_eeprom stm_sd stm_fatfs)
```

需要 LittleFS 时，在上述驱动接入之后添加：

```cmake
add_subdirectory(${STM_LIB_DIR}/stm_littlefs)
target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE stm_littlefs)
```

`stm_littlefs` 提供分区块设备回调，文件操作使用官方 `lfs_*` API；组件通过 CMake 自动获取固定版本 LittleFS 到同级 `lib/littlefs/`，主工程无需单独拉取。也支持自定义下载位置和离线源码。分区划分、生命周期和 `example/main.c` 见 [组件说明](lib/stm_littlefs/README.md)。

单独克隆 Flash 或 SDRAM 时，无需手动下载 `stm_common`：驱动优先使用已有 target 或同级目录，缺失时通过 FetchContent 自动获取 `v1.0.0` 对应的固定提交，两个驱动共享一份依赖。默认下载源为 GitHub；在添加驱动前设置 `STM_COMMON_GIT_REPOSITORY` 可切换到 `https://gitee.com/nzxhg/stm_common.git`，设置 `STM_COMMON_FETCH=OFF` 可禁止自动下载。详细离线配置见各驱动 README。

ESP32-C3 的 SPI 联网组件可按需加入。项目先提供 `lwip` 静态库目标和 `NO_SYS=1` 配置，然后添加组件；若只需 SPI/RPC 传输，则仅链接 `stm_esp_hosted`：

```cmake
add_subdirectory(${STM_LIB_DIR}/stm_esp_hosted)
target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE stm_esp_hosted_lwip)
```

主循环负责轮询组件和 lwIP 定时器，板级接线、ESP32-C3 固件及完整调用顺序见 [组件说明](lib/stm_esp_hosted/README.md)。实板已验证 STA 的 DHCP、DNS、TCP/UDP、主动断线重连，以及单客户端 AP 的 HTTP 与 UDP 回显；两小时纯 STA 持续运行完成 121 轮回显，三种 STA 省电模式各完成 10 轮 DHCP/DNS/TCP/UDP 验证；整板断电重启独立观察 13 次，其中 10 次有效通过（非连续无故障通过），另有一次欠压启动失败、一次采集缺口无法判定、一次无法证明整板重启且网络验证失败；详见组件 README。

日志组件按需加入。下面是 H7 的设置，其他系列须使用对应 HAL 头文件：

```cmake
add_subdirectory(${STM_LIB_DIR}/stm_log)
target_compile_definitions(stm_log PUBLIC STM_LOG_HAL_HEADER="stm32h7xx_hal.h")
target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE stm_log)
```

使用 RTT 输出时，在添加 `stm_log` 前设置 `STM_LOG_WITH_RTT=ON`，组件会自动提供 `segger_rtt` 链接依赖。默认从 [GitHub RTT](https://github.com/NingZiXi/RTT) 拉取固定提交，也可通过 `STM_LOG_RTT_GIT_REPOSITORY` 切换到 [Gitee RTT](https://gitee.com/nzxhg/RTT)。本地源码、离线选项与输出回调示例见 stm_log README。默认 UART 用法不拉取 RTT。

组件默认从已有的 `stm32cubemx` 目标继承 HAL 头文件和芯片宏。自定义构建系统的配置见各组件 README；Keil/IAR 可手动添加所选组件的 `.c` 文件及 include 路径。

板级仍负责 HAL、时钟、GPIO、外设和 MPU 配置。Flash/SDRAM 的创建使用内部 RAM 堆；器件参数、内存属性、访问限制和最小 `example/main.c` 见对应组件说明。示例不自动加入库目标。

`stm_esp_hosted v0.6.0` 已验证 B/HT20、BG/HT20、BGN/HT20、BGN/HT40 四组 STA 的 40 轮 DHCP/DNS/TCP/UDP 及四次断线恢复，单手机 AP 四组 DHCP/HTTP/UDP 与原配置恢复通过。HT40 读回为配置值，不代表实际 40 MHz 通信；本轮不新增吞吐、长期运行或断电稳定性结论，复现步骤与限制见组件说明。

`stm_esp_hosted v0.7.0` 补齐心跳、本地诊断和异步传输恢复，以及国家策略、共享信道和功率配置。应用负责密码和配置重放、lwIP 与探针清理。十个 CP 故障注入及后续十轮周期、CN 两种策略共二十轮、三档功率共三十轮及三次断线恢复通过；单手机信道 1/6/11、AP+STA 同时通信、CP 独立复位、三档功率与原配置恢复复测通过。国家配置可能持久写入 CP Flash，功率接口单位 0.25 dBm，读回与通信不代表射频输出测量；本轮不新增长期运行、吞吐或整板断电结论。

stm_esp_hosted v0.8.0 增加单槽有类型异步控制任务、有界轮询及 STA/AP 共用两槽 Ethernet FIFO，保留同步 API。H723 从联网状态机开始测得轮询/主循环/lwIP 服务/10 ms 定时器延迟最大约 9.563/9.661/9.599/5.034 ms；自动故障回归、单手机 AP+STA 同时通信及原配置恢复验收通过。仅覆盖当前 H723/SPI 与有界回调，不构成硬实时或新增长期、吞吐、断电结论；生命周期和复现步骤见组件 README。

## 更新与版本

总仓库提交记录固定每个组件的完整 commit，不会在构建时自动跟随组件的最新分支。每日的 [自动同步任务](.github/workflows/sync-latest-tags.yml) 与手动触发会选择带 tag 组件的最新稳定版本，更新 gitlink 和 README，并提交草稿 PR；合并后才成为总仓库的新组合。也可以在干净的工作区手动运行 `python ci/sync_latest_tags.py`（先以 `--dry-run` 预览）。查看当前组合：

```sh
git submodule status
```

在工作区无未提交修改时，获取总仓库的新组合：

```sh
git pull --ff-only
git submodule sync --recursive
git submodule update --init --recursive
```

驱动改动先提交到独立仓库并发布稳定版本 tag，再通过同步任务更新本仓库引用并验证。不要用 `git submodule update --remote` 替代上述更新命令，它会跳过总仓库固定的版本组合。新版本可能不兼容，草稿 PR 必须人工审查；GitHub Actions 自带的 token 创建的 PR 不会自动触发 CI，需要手动运行 CI 或由维护者推送后再合并。组件独立发布版本，总仓库后续按验证过的组合发布版本；当前未创建发布标签。

## 验证

[GitHub Actions](https://github.com/NingZiXi/stm32-hal-lib/actions) 在 push、pull request 和手动触发时执行：

- 总仓库 Markdown 本地文件链接、组件目录和子模块引用检查。
- STM32H723xx / Cortex-M7 配置下，三个 C 驱动组件、ESP-AT 协议核心及其 STM32 适配层 (`ports/stm32_hal/`) 的 CMake 编译与组合公共头文件的 C/C++ 编译；额外检查日志关闭配置。
- 公共依赖的本地接入、两个驱动添加顺序、固定提交下载与离线缺失报错。
- RTT 可选依赖的固定提交下载、本地复用、关闭及缺失检查，以及只链接 stm_log 的消费者链接检查。
- Flash、SDRAM 真实驱动的 Unicorn 模拟测试，分别使用 O0/O2/Os，覆盖生命周期、边界、错误注入和存储操作。
- LittleFS 适配层与官方文件系统的主机测试，覆盖分区保护、文件操作、重挂载、部分写入/擦除中断恢复和依赖获取。

CI 使用固定提交的 ST HAL、CMSIS Device 和 CMSIS Core，依赖仅下载到工作目录，不随本仓库分发。运行方式及范围见 [ci/README.md](ci/README.md)。

实板验证记录由各组件 README 给出。CI 不连接 J-Link，不验证电气时序、焊接、温度或长期稳定性；日志组件在本仓库仅做编译检查。

## 贡献与许可

新增组件、接口和注释约定见 [CONTRIBUTING.md](CONTRIBUTING.md)。

本仓库原创文档和工具采用 [MIT License](LICENSE)。各子模块及其第三方部分遵循各自许可证；总仓库许可证不替代组件内的授权说明。
