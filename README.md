# stm32-hal-lib

[![CI](https://github.com/NingZiXi/stm32-hal-lib/actions/workflows/ci.yml/badge.svg)](https://github.com/NingZiXi/stm32-hal-lib/actions/workflows/ci.yml)

基于 STM32 HAL 的模块化驱动与基础组件集合。组件独立维护，本仓库通过 Git submodule 固定版本组合，提供统一接入入口；它不是 ST 官方 HAL 的镜像，也不提供可烧录的完整板级工程。

支持范围与验证结果以各组件**当前提交**的说明为准。维护者阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，编码 Agent 从 [AGENTS.md](AGENTS.md) 按任务选择上下文；可复用应用接入技能见 [skills/](skills/README.md)。

## 组件与固定组合

| 组件 | 当前提交 | 发布状态 | 用途 |
| --- | --- | --- | --- |
| [stm_common](https://github.com/NingZiXi/stm_common) | [`cc68ae4ad9c0`](https://github.com/NingZiXi/stm_common/tree/cc68ae4ad9c03e39d37d567eaae54dcf3b83e081) | 未发布（基于 [v1.0.0](https://github.com/NingZiXi/stm_common/tree/ce3d186dde2d374a8e9c7b9068a7b88f97d57dc1)） | `stm_err_t` 与公共错误码 |
| [stm_flash](https://github.com/NingZiXi/stm_flash) | [`2d44d3c09126`](https://github.com/NingZiXi/stm_flash/tree/2d44d3c091262a4d79b33b04ca47a8a04b2fee35) | [![version 4.0.0](https://img.shields.io/badge/version-4.0.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_flash/tree/2d44d3c091262a4d79b33b04ca47a8a04b2fee35) | NOR Flash 读取、分页写入、扇区擦除与校验 |
| [stm_sdram](https://github.com/NingZiXi/stm_sdram) | [`86f106e8693f`](https://github.com/NingZiXi/stm_sdram/tree/86f106e8693f84a75e0ca120290e4867aee05e6c) | [![version 4.0.0](https://img.shields.io/badge/version-4.0.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_sdram/tree/86f106e8693f84a75e0ca120290e4867aee05e6c) | SDRAM 初始化、刷新、读写、填充及自检 |
| [stm_log](https://github.com/NingZiXi/stm_log) | [`15642aa90fe3`](https://github.com/NingZiXi/stm_log/tree/15642aa90fe3c5a91cd64680437f2ebd867ca20a) | [![version 2.4.0](https://img.shields.io/badge/version-2.4.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_log/tree/15642aa90fe3c5a91cd64680437f2ebd867ca20a) | 分级日志、标签过滤及自定义输出 |
| [stm_esp_hosted](https://github.com/NingZiXi/stm_esp_hosted) | [`be18b35709f9`](https://github.com/NingZiXi/stm_esp_hosted/tree/be18b35709f93dc1e22c3cc90e282003f86a1078) | [![version 0.8.0](https://img.shields.io/badge/version-0.8.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_esp_hosted/tree/be18b35709f93dc1e22c3cc90e282003f86a1078) | ESP32-C3 SPI 主机、STA/AP Wi-Fi、异步任务与发送队列、恢复诊断、国家/信道/功率、可选 lwIP 网卡 |
| [stm_littlefs](https://github.com/NingZiXi/stm_littlefs) | [`6360940d6dfb`](https://github.com/NingZiXi/stm_littlefs/tree/6360940d6dfbefdb09f5eed76fb58891af035f0d) | [![version 1.0.2](https://img.shields.io/badge/version-1.0.2-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_littlefs/tree/6360940d6dfbefdb09f5eed76fb58891af035f0d) | LittleFS 分区块设备适配与文件系统接入 |
| [stm_eeprom](https://github.com/NingZiXi/stm_eeprom) | [`1ac5b9a8dc66`](https://github.com/NingZiXi/stm_eeprom/tree/1ac5b9a8dc6612c5066cefb6b93f5ebbd7e6834c) | [![version 1.0.0](https://img.shields.io/badge/version-1.0.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_eeprom/tree/1ac5b9a8dc6612c5066cefb6b93f5ebbd7e6834c) | I2C EEPROM 器件与控制器适配 |
| [stm_sd](https://github.com/NingZiXi/stm_sd) | [`0ef93e067633`](https://github.com/NingZiXi/stm_sd/tree/0ef93e067633d3ebc22e3f3aa8dc5d80f25d5d32) | [![version 1.0.0](https://img.shields.io/badge/version-1.0.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_sd/tree/0ef93e067633d3ebc22e3f3aa8dc5d80f25d5d32) | SD NAND/TF 卡块设备与 SDMMC 适配 |
| [stm_fatfs](https://github.com/NingZiXi/stm_fatfs) | [`da4e096bfc7a`](https://github.com/NingZiXi/stm_fatfs/tree/da4e096bfc7a2137929abca28775479b93b787f9) | [![version 1.0.1](https://img.shields.io/badge/version-1.0.1-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_fatfs/tree/da4e096bfc7a2137929abca28775479b93b787f9) | FatFs 磁盘注册和块设备粘合层 |
| [esp_at_client](https://github.com/NingZiXi/esp_at_client) | [`b17f954c76ca`](https://github.com/NingZiXi/esp_at_client/tree/b17f954c76ca4cc3cddcddad48faa1328d80a29f) | [![version 0.5.0](https://img.shields.io/badge/version-0.5.0-5364b5?style=flat-square)](https://github.com/NingZiXi/esp_at_client/tree/b17f954c76ca4cc3cddcddad48faa1328d80a29f) | 平台无关 ESP-AT 轮询客户端，STM32 HAL 适配位于 ports/stm32_hal/ |
| [stm_lcd_st7789](https://github.com/NingZiXi/stm_lcd_st7789) | [`d3013e3e010c`](https://github.com/NingZiXi/stm_lcd_st7789/tree/d3013e3e010c40a15268ea301722808e5767552b) | [![version 0.2.0](https://img.shields.io/badge/version-0.2.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_lcd_st7789/tree/d3013e3e010c40a15268ea301722808e5767552b) | ST7789 SPI 面板芯片驱动 |
| [stm_lcd_st7796](https://github.com/NingZiXi/stm_lcd_st7796) | [`a45c88a1bd9f`](https://github.com/NingZiXi/stm_lcd_st7796/tree/a45c88a1bd9f4ce22eb60e19af8184cf3e3d1b1a) | [![version 0.2.0](https://img.shields.io/badge/version-0.2.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_lcd_st7796/tree/a45c88a1bd9f4ce22eb60e19af8184cf3e3d1b1a) | ST7796 SPI 面板芯片驱动 |
| [stm_lcd_touch_ft5206](https://github.com/NingZiXi/stm_lcd_touch_ft5206) | [`e49ae91ff723`](https://github.com/NingZiXi/stm_lcd_touch_ft5206/tree/e49ae91ff723b23ce7d619e895152d96727b3b02) | [![version 0.2.0](https://img.shields.io/badge/version-0.2.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_lcd_touch_ft5206/tree/e49ae91ff723b23ce7d619e895152d96727b3b02) | FT5206 I2C 触摸芯片驱动 |
| [stm_lcd_ili9881c](https://github.com/NingZiXi/stm_lcd_ili9881c) | [`daeb162266d2`](https://github.com/NingZiXi/stm_lcd_ili9881c/tree/daeb162266d217709187629ea90768cf6083ebaf) | [![version 0.2.0](https://img.shields.io/badge/version-0.2.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_lcd_ili9881c/tree/daeb162266d217709187629ea90768cf6083ebaf) | ILI9881C DSI 面板初始化，模组命令表仅适用于已测 10.1 寸屏幕 |
| [stm_lcd_touch_gt9271](https://github.com/NingZiXi/stm_lcd_touch_gt9271) | [`da4479a471bb`](https://github.com/NingZiXi/stm_lcd_touch_gt9271/tree/da4479a471bb21a1acd72fc5fdccca7d0fd2749b) | [![version 0.2.0](https://img.shields.io/badge/version-0.2.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_lcd_touch_gt9271/tree/da4479a471bb21a1acd72fc5fdccca7d0fd2749b) | GT9271 I²C 触摸与坐标读取 |
| [stm_lvgl_port](https://github.com/NingZiXi/stm_lvgl_port) | [`da24ddaf01ed`](https://github.com/NingZiXi/stm_lvgl_port/tree/da24ddaf01ed746965cc01d0af042de9fab6f8ca) | [![version 0.2.0](https://img.shields.io/badge/version-0.2.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_lvgl_port/tree/da24ddaf01ed746965cc01d0af042de9fab6f8ca) | 独立于屏幕型号的显示与触摸接入 |
| [stm_ota](https://github.com/NingZiXi/stm_ota) | [`f9163d2a7efe`](https://github.com/NingZiXi/stm_ota/tree/f9163d2a7efe2f67d089a62c413dc40360c49170) | [![version 0.5.0](https://img.shields.io/badge/version-0.5.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_ota/tree/f9163d2a7efe2f67d089a62c413dc40360c49170) | 同步 OTA 下载、A/B 分区切换与 Flash 校验 |

“当前提交”链接对应本仓库固定的 gitlink；徽章只用于有对应 tag 的提交。标为“未发布”的组合不能用其基线 tag 的硬件结论代替新提交验收。组件名称链接到独立仓库首页，那里可能已更新；使用此组合时请读克隆后的 `lib/<组件>/README.md`。

显示与触摸六组件当前固定为 `v0.2.0`，采用不透明句柄、`create/delete` 和 `stm_err_t`，不提供 `v0.1.0` 兼容包装。2026-10-07，ILI9881C/GT9271/LVGL port 在 H757 配套模组完成新接口的诊断、五次复位、Release 启动及官方 Widgets 滑动/点击回归；ST7789/ST7796/FT5206 仅完成软件验证。接入、迁移和验证边界见[显示接入指南](docs/display-components.md)。

## 获取与更新

二选一克隆，GitHub 的 Download ZIP 不包含子模块源码：

```sh
git clone --recurse-submodules https://github.com/NingZiXi/stm32-hal-lib.git Lib/stm32-hal-lib
# 或
git clone --recurse-submodules https://gitee.com/nzxhg/stm32-hal-lib.git Lib/stm32-hal-lib
```

子模块使用同账号相对地址，随克隆来源选择平台。镜像同步要求见维护约定。普通克隆后运行 `git submodule update --init --recursive`。

在无未提交修改且本地分支可快进时，从总仓库获取新组合：

```sh
git pull --ff-only
git submodule sync --recursive
git submodule update --init --recursive
git submodule status
```

这些命令获取总仓库固定的组合。总仓库仅保留 `main`，不发布自身的 tag；组件仍独立发布版本。目前自动创建候选分支的任务已停用，可通过手动脚本预览并由维护者审查更新；具体的 tag 选择、未发布组合保护与合入条件见[维护流程](CONTRIBUTING.md)。

## 接入 STM32CubeMX + CMake

以下示例针对已有 `stm32cubemx` target 的 CubeMX 工程。其他工程须按所选组件提供实际 HAL 头路径、芯片宏和链接依赖；不应直接套用不存在的目标。

Flash/SDRAM v4 的核心不依赖 HAL。H757 QSPI/FMC 的硬件接入需显式添加适配器：

```cmake
set(STM_LIB_DIR "${CMAKE_CURRENT_SOURCE_DIR}/Lib/stm32-hal-lib/lib")
add_subdirectory(${STM_LIB_DIR}/stm_common) # 已有该 target 时省略
add_subdirectory(${STM_LIB_DIR}/stm_flash)
add_subdirectory(${STM_LIB_DIR}/stm_sdram)

set(STM_FLASH_WITH_QSPI ON)
add_subdirectory(${STM_LIB_DIR}/stm_flash/adapters/stm32_hal)
add_subdirectory(${STM_LIB_DIR}/stm_sdram/adapters/stm32_hal)
target_compile_definitions(stm_flash_qspi PUBLIC STM_FLASH_HAL_HEADER="stm32h7xx_hal.h")
target_compile_definitions(stm_sdram_fmc PUBLIC STM_SDRAM_HAL_HEADER="stm32h7xx_hal.h")
target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE stm_flash_qspi stm_sdram_fmc)
```

H723 OSPI 改用 `STM_FLASH_WITH_OSPI` 和 `stm_flash_ospi`；板级还须按[Flash](lib/stm_flash/README.md)与[SDRAM](lib/stm_sdram/README.md)说明绑定器件和控制器。只需要平台无关核心时，仅链接核心 target。H757 的实测结论和 H723 的软件模型回归范围见对应版本说明，不能推定其他系列已支持。

其他功能按需读取对应说明，避免把核心链接误当作完整硬件接入：

| 功能 | 接入入口 |
| --- | --- |
| EEPROM / SD | [EEPROM](lib/stm_eeprom/README.md)、[SD](lib/stm_sd/README.md)：核心与 HAL I²C/SDMMC 适配器分别添加 |
| 文件系统 | [FatFs](lib/stm_fatfs/README.md)、[LittleFS](lib/stm_littlefs/README.md)：固定上游依赖、块设备绑定和文件操作 |
| ESP32-C3 SPI 联网 | [ESP-Hosted](lib/stm_esp_hosted/README.md)：板级 SPI、协处理器固件、轮询与可选 lwIP 目标 |
| ESP-AT / OTA | [ESP-AT](lib/esp_at_client/README.md)、[OTA](lib/stm_ota/README.md)：实际版本的适配层和调用顺序 |
| 显示、触摸与 LVGL | [显示接入指南](docs/display-components.md)：选择芯片、板级传输与 LVGL 9 接入 |

板级负责 HAL、时钟、GPIO、外设、供电和 MPU/Cache 配置。组件示例不会自动编入库，也不能替代其他开发板的配置；擦写测试必须明确范围并备份需保留的数据。

### 当前组合的日志与应用接入 skill

直接使用本仓库日志时，以组件表与对应头文件确定版本。下面是含 HAL 依赖的 **stm_log v2** 的 H7 接入示例；若选用 v3，不使用该 HAL 宏，按该版本说明提供输出回调：

```cmake
add_subdirectory(${STM_LIB_DIR}/stm_log)
target_compile_definitions(stm_log PUBLIC STM_LOG_HAL_HEADER="stm32h7xx_hal.h")
target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE stm_log)
```

RTT 在添加组件前设置 `STM_LOG_WITH_RTT=ON`；输出回调、固定 RTT 依赖与离线设置见[当前提交说明](lib/stm_log/README.md)。

分发的 `stm32-app-main` skill 在外部工程通过 FetchContent 获取 stm_log v3.0.0，使用平台无关输出回调。这是另一条消费路径，不会升级本仓库的日志子模块，也不能同时创建两个同名 `stm_log` target。先选择接入路径，再核对 API 和 HAL 依赖；技能的安装、适用范围与版本见 [skills/README.md](skills/README.md)。

## 目录与验证

```text
stm32-hal-lib/
├── AGENTS.md             # Agent 工作边界与按需阅读入口
├── README.md             # 项目与使用入口
├── CONTRIBUTING.md       # 通用维护和发布政策
├── lib/                  # 组件子模块；fatfs/ 为第三方固定源码副本
├── skills/               # 独立技能的固定版本分发
├── docs/                 # 跨组件接入与领域开发说明
├── ci/                   # 软件检查及 CI 专用 HAL 配置
└── .github/workflows/    # CI 与候选版本同步
```

[GitHub Actions](https://github.com/NingZiXi/stm32-hal-lib/actions)执行文档/gitlink 检查、H723/H757 编译及公共头文件检查、依赖获取与链接检查，以及主机/模拟测试。具体工具、命令与覆盖范围统一见 [ci/README.md](ci/README.md) 和工作流。

CI 不连接 J-Link，也不证明板级电气时序、温度或长期稳定性。总仓库检查不交付可烧录固件；硬件验证结果应对应具体组件提交、器件和条件，详见各组件 README。

## 贡献与许可

新增组件、接口契约、注释和发布流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。本仓库原创文档和工具采用 [MIT License](LICENSE)；子模块及第三方部分遵循各自许可证。
