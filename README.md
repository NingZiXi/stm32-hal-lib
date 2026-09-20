# stm32-hal-lib

[![CI](https://github.com/NingZiXi/stm32-hal-lib/actions/workflows/ci.yml/badge.svg)](https://github.com/NingZiXi/stm32-hal-lib/actions/workflows/ci.yml)

基于 STM32 HAL 的模块化驱动与基础组件库。组件独立维护，本仓库通过 Git submodule 汇集经过检查的版本，提供统一的使用入口。

这是应用层组件集合，不是 ST 官方 HAL 的镜像。当前存储驱动主要在 **STM32H723ZG** 上验证，具体支持范围以各组件说明为准。

## 组件

| 组件 | 当前引用版本 | 用途 | 当前适用范围 | 依赖 |
|---|---|---|---|---|
| [stm_common](https://github.com/NingZiXi/stm_common) | [![commit ce3d186](https://img.shields.io/badge/commit-ce3d186-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_common/tree/ce3d186dde2d374a8e9c7b9068a7b88f97d57dc1) | `stm_err_t` 与公共错误码 | 无 MCU 外设依赖 | C 标准整数类型 |
| [stm_flash](https://github.com/NingZiXi/stm_flash) | [![version 2.0.0](https://img.shields.io/badge/version-2.0.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_flash/tree/7858884cb8bafd0913a2f0ef53ecfcc6e025aea7) | NOR Flash 读取、分页写入、扇区擦除与校验 | H7 OCTOSPI；实测 W25Q256JVEIQ、32 MiB | HAL、stm_common |
| [stm_sdram](https://github.com/NingZiXi/stm_sdram) | [![version 2.0.0](https://img.shields.io/badge/version-2.0.0-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_sdram/tree/b61fe2af57b15fa07ba9c47477a5d867ef60547a) | SDRAM 初始化、刷新、读写、填充及自检 | H7 FMC、16 位 SDR SDRAM；实测 W9825G6KH-6、32 MiB | HAL、stm_common |
| [stm_log](https://github.com/NingZiXi/stm_log) | [![version 2.3.1+059e5bc](https://img.shields.io/badge/version-2.3.1%2B059e5bc-5364b5?style=flat-square)](https://github.com/NingZiXi/stm_log/tree/059e5bc096233fa715d66ba3e92ea9defc697b52) | 分级日志、标签过滤及自定义输出 | HAL UART；可接自定义后端，按系列指定 HAL 头文件 | HAL；互斥功能可选依赖 FreeRTOS |

表中链接指向独立仓库的最新说明；当前固定版本的说明位于克隆后的 `lib/<组件>/README.md`。

版本徽章对应本仓库固定的提交，点击可查看该版本源码。Flash/SDRAM 显示源码中的版本号，尚无发布标签；`stm_common` 暂用短提交号；`stm_log` 为 `v2.3.1` 加后续修复。更新子模块时同步更新徽章，不自动跟随最新发布版。

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
│   └── stm_log/
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
set(STM_LIB_DIR "${CMAKE_CURRENT_SOURCE_DIR}/Lib/stm32-hal-lib/components")
add_subdirectory(${STM_LIB_DIR}/stm_common)
add_subdirectory(${STM_LIB_DIR}/stm_flash)
add_subdirectory(${STM_LIB_DIR}/stm_sdram)
target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE stm_flash stm_sdram)
```

只使用一个驱动时，删除另一个驱动的两处引用即可。`stm_common` 是头文件库，驱动会传递它的 include 路径；已经在其他位置添加过该目标时，不要重复添加。

日志组件按需加入。下面是 H7 的设置，其他系列须使用对应 HAL 头文件：

```cmake
add_subdirectory(${STM_LIB_DIR}/stm_log)
target_compile_definitions(stm_log PUBLIC STM_LOG_HAL_HEADER="stm32h7xx_hal.h")
target_link_libraries(${CMAKE_PROJECT_NAME} PRIVATE stm_log)
```

组件默认从已有的 `stm32cubemx` 目标继承 HAL 头文件和芯片宏。自定义构建系统的配置见各组件 README；Keil/IAR 可手动添加所选组件的 `.c` 文件及 include 路径。

板级仍负责 HAL、时钟、GPIO、外设和 MPU 配置。Flash/SDRAM 的创建使用内部 RAM 堆；器件参数、内存属性、访问限制和最小 `example/main.c` 见对应组件说明。示例不自动加入库目标。

## 更新与版本

总仓库提交记录固定每个组件的完整 commit，不会在构建时自动跟随组件的最新分支。查看当前组合：

```sh
git submodule status
```

在工作区无未提交修改时，获取总仓库的新组合：

```sh
git pull --ff-only
git submodule sync --recursive
git submodule update --init --recursive
```

驱动改动先提交到独立仓库，再更新本仓库引用并通过 CI。不要用 `git submodule update --remote` 替代上述更新命令，它会跳过总仓库固定的版本组合。组件独立发布版本，总仓库后续按验证过的组合发布版本；当前未创建发布标签。

## 验证

[GitHub Actions](https://github.com/NingZiXi/stm32-hal-lib/actions) 在 push、pull request 和手动触发时执行：

- 总仓库 Markdown 本地文件链接、组件目录和子模块引用检查。
- STM32H723xx / Cortex-M7 配置下，三个 C 组件的 CMake 编译及组合公共头文件的 C/C++ 编译；额外检查日志关闭配置。
- Flash、SDRAM 真实驱动的 Unicorn 模拟测试，分别使用 O0/O2/Os，覆盖生命周期、边界、错误注入和存储操作。

CI 使用固定提交的 ST HAL、CMSIS Device 和 CMSIS Core，依赖仅下载到工作目录，不随本仓库分发。运行方式及范围见 [ci/README.md](ci/README.md)。

实板验证记录由各组件 README 给出。CI 不连接 J-Link，不验证电气时序、焊接、温度或长期稳定性；日志组件在本仓库仅做编译检查。

## 贡献与许可

新增组件、接口和注释约定见 [CONTRIBUTING.md](CONTRIBUTING.md)。

本仓库原创文档和工具采用 [MIT License](LICENSE)。各子模块及其第三方部分遵循各自许可证；总仓库许可证不替代组件内的授权说明。
