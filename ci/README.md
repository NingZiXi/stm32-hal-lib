# CI 与本地检查

在总仓库根目录执行。工具需要 Git、Python 3.12、CMake 3.22+、Ninja、GNU Arm GCC/G++ 和 ARM newlib 头文件。CI 使用 Ubuntu 24.04，具体步骤见 [ci.yml](../.github/workflows/ci.yml)。

## 依赖

组件须完整初始化。CI 的递归 checkout 使用 `fetch-depth: 0` 保留子模块历史；显示依赖检查会从本地 `stm_common` 克隆较旧的固定提交，只有浅克隆的当前提交无法完成此检查：

```sh
git submodule update --init --recursive
python ci/check_repository.py
```

文档检查只检查总仓库跟踪的 Markdown 中内联链接的本地文件目标，不检查外部网站可用性或标题锚点。子模块引用必须与暂存区记录一致；README 组件表的提交也须与暂存区 gitlink 一致。新增文件须先 `git add` 才会纳入检查（只验证新文件时可用 `git add -N`）。本检查不递归检查子模块内部 Markdown，也不查询远端 Release 或硬件状态。

HAL 和 CMSIS 是测试环境依赖，不是新组件。首次准备时执行以下命令（目录已存在时 fetch 后 checkout 同一提交即可）：

```sh
git clone https://github.com/STMicroelectronics/stm32h7xx-hal-driver.git .ci-deps/hal
git -C .ci-deps/hal checkout --detach e3c518ebda3e00c8e52b1625ca44fba65da3b63e
git clone https://github.com/STMicroelectronics/cmsis-device-h7.git .ci-deps/device
git -C .ci-deps/device checkout --detach 81db1ec63cdc191fae1565b772da3ea5aa29a683
git clone https://github.com/ARM-software/CMSIS_5.git .ci-deps/cmsis
git -C .ci-deps/cmsis checkout --detach 2b7495b8535bdcb306dac29b9ded4cfb679d7e5c
python -m venv .venv
```

激活虚拟环境：PowerShell 使用 `.venv/Scripts/Activate.ps1`，Linux/macOS 使用 `source .venv/bin/activate`，随后：

```sh
python -m pip install -r lib/stm_flash/tests/requirements.txt -r lib/stm_sdram/tests/requirements.txt
```

## 编译检查

```sh
cmake -S ci -B build/compile -G Ninja "-DCMAKE_TOOLCHAIN_FILE=/absolute/path/to/stm32-hal-lib/ci/arm-gcc.cmake" "-DCMAKE_BUILD_TYPE=Release"
cmake --build build/compile
```

基础编译工程生成静态库和检查对象；RTT 链接目标也仅用于检查，均不可烧录。平台无关核心不依赖 HAL，显式加入的 STM32 适配器继承 CI 配置。检查组合公共头文件的 C11/C++17 消费者，以及 `STM_LOG_ENABLED=0` 的日志源文件。LittleFS 上游固定为 v2.11.2 对应提交，由适配组件自动下载。EEPROM 同时检查硬件 I2C 和 GPIO 模拟 I2C 适配器；FatFs 检查 SD/NOR 桥接，并由 stm_fatfs 获取带 SHA-256 校验的官方 R0.14b 源码到构建目录，不再使用旧的 STM_FATFS_FETCH_DIR 选项。

LittleFS 主机测试使用本机 GCC/G++，无需连接开发板：

```sh
cmake -S lib/stm_littlefs/tests -B build/littlefs-tests -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build/littlefs-tests
ctest --test-dir build/littlefs-tests --output-on-failure
python ci/check_littlefs_dependency.py --littlefs-source lib/littlefs
```

主机测试执行官方 LittleFS 文件操作和 NOR 部分写入/擦除中断恢复。依赖检查覆盖已有 target、离线源目录、自动获取 Flash/Common 的固定版本和关闭下载后的缺失报错；可用 `--flash-repository`、`--common-repository` 指定镜像，`--deps-root` 指定 HAL/CMSIS 目录。

`ci/include/stm32h7xx_hal_conf.h` 仅用于 H723/H757 编译与 HAL 桩测试，没有 GPIO、启动、链接脚本或板级配置，不应替代实际工程的 HAL 配置。

## 模拟测试

公共依赖接入检查（需要网络下载固定版本）：

```sh
python ci/check_common_dependency.py
```

此检查在隔离目录中编译两个驱动，覆盖已有 target、同级目录、源码路径覆盖、两个添加顺序的自动下载，以及关闭下载时的缺失依赖错误。可传 `--repository https://gitee.com/nzxhg/stm_common.git` 检查 Gitee 镜像；下载后校验实际提交。

以下命令 PowerShell 和 Bash 均可执行：

```sh
python lib/stm_flash/tests/run_tests.py --include ci/include --include .ci-deps/hal/Inc --include .ci-deps/device/Include --include .ci-deps/cmsis/CMSIS/Core/Include --build-dir build/flash-tests
python lib/stm_sdram/tests/run_tests.py --include ci/include --include .ci-deps/hal/Inc --include .ci-deps/device/Include --include .ci-deps/cmsis/CMSIS/Core/Include --build-dir build/sdram-tests
```

两个运行器分别编译并执行 O0/O2/Os 测试；使用 HAL 桩和 Unicorn Cortex-M7，不访问真实硬件。测试细节见各子模块的 `tests/README.md`，在线版本见 [Flash 测试](https://github.com/NingZiXi/stm_flash/blob/main/tests/README.md) 与 [SDRAM 测试](https://github.com/NingZiXi/stm_sdram/blob/main/tests/README.md)。

日志运行时测试使用 v3 的真实实现，覆盖默认、无颜色/换行、文件行号、关闭日志、小缓冲区、C++ 头文件和示例：

```sh
cmake -S lib/stm_log/tests -B build/stm_log-tests -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build/stm_log-tests
ctest --test-dir build/stm_log-tests --output-on-failure
```

当前不包含完整固件链接或硬件在环测试。CI 的成功只代表上述软件检查通过。

RTT 可选依赖还会执行独立编译和链接检查：

```sh
cmake -S ci -B build/rtt -G Ninja "-DCMAKE_TOOLCHAIN_FILE=/absolute/path/to/stm32-hal-lib/ci/arm-gcc.cmake" -DSTM_LOG_WITH_RTT=ON
cmake --build build/rtt
python ci/check_rtt_dependency.py --source lib/segger_rtt
```

stm_log v3.0.2 首次自动获取 RTT 时将固定提交的源码放在 `lib/segger_rtt/`（已忽略），构建目录保存获取管理文件与编译产物；应用只链接 `stm_log`，验证 RTT 头文件和符号被正确传递；后续检查覆盖关闭依赖、指定本地源码/配置、同级目录、已有 target 和离线缺失报错。链接检查使用应用输出/tick 回调和 newlib nosys，不依赖 HAL，产物仅用于检查，不可烧录，也不代表 RTT 硬件通信测试通过。

升级依赖时同步修改工作流和本文的 commit，并重新运行全部检查。组件更新须先推送到独立远程，再提交总仓库的 gitlink；CI 的递归 checkout 会验证该提交能从远程获取。

## 显示接口软件迁移检查

九个显示框架/触摸/LVGL 组件（包括两个 AXS15231B 组件）各自的 tests/ 检查参数、分配故障、生命周期、错误传递和 C11/C++17 头文件；测试库替换 calloc/free，生产构建使用正常 libc。LVGL 主机测试使用桩验证资源回收和回调，不能替代真实 LVGL 编译或硬件检查。

```sh
python ci/check_display_integration.py --lvgl-source /absolute/path/to/lvgl-9.3.0
```

该脚本用新隔离目录验证 stm_common 已有 target、同级源码、离线源码覆盖、两个添加顺序的固定提交下载和每个组件关闭下载后的缺失报错；默认从本地 stm_common Git 仓库获取固定 v1.0.0 提交，无需联网，可用 --repository 指定 GitHub/Gitee 镜像。随后用真实 H757 HAL/CMSIS 及 LVGL 头文件编译原有六份中文 HAL 示例、LVGL port 实现和九个组件的 C11/C++17 消费者。AXS15231B 核心与公共头文件也纳入 H723/H757 编译工程和主机测试；两个新组件的示例专用于 F407，不混入 H757 示例编译，本轮在 F407 消费工程的真实 HAL/CMSIS 头文件下单独检查，尚未加入持续集成示例编译。原始命令日志及隔离源码保留在 build/display-api-migration/integration/。

Windows 可用 --c-compiler、--cxx-compiler 指定 MinGW GCC/G++，--arm-compiler 指定 GNU Arm GCC。CI 使用 LVGL v9.3.0。该脚本不烧录也不发布；外部消费工程的完整链接和硬件回归是独立验收步骤，不能因脚本通过就声明硬件支持。组合状态见[显示接入指南](../docs/display-components.md)。

### AXS 公共框架自动获取检查

```sh
python lib/stm_lcd_axs15231b/tests/test_dependency.py --lcd-source lib/stm_lcd --common-source lib/stm_common --lcd-repository /absolute/path/to/lib/stm_lcd --peer-source lib/stm_lcd_touch_axs15231b
python lib/stm_lcd_touch_axs15231b/tests/test_dependency.py --lcd-source lib/stm_lcd --common-source lib/stm_common --lcd-repository /absolute/path/to/lib/stm_lcd
```

分别覆盖 16/14 个隔离配置：已有 target/alias、同级源码、显式及 FetchContent 离线覆盖、优先级、固定提交拉取、关闭下载、无效目录/缺失 target、完全离线缺失，以及两个组件的正反添加顺序。配置成功后编译组件与 C11/C++17 消费者；关闭下载/无效目录时不得尝试联网。默认本地镜像验证固定提交；省略 `--lcd-repository` 时默认使用 `--lcd-source` 本地 Git checkout；显式传入 GitHub/Gitee URL 才进行真实网络获取验证。此测试不连接硬件，不改变此前板测范围。

## H757 / QSPI 扩展检查

```sh
cmake -S ci -B build/compile-h757 -G Ninja "-DCMAKE_TOOLCHAIN_FILE=/absolute/path/to/stm32-hal-lib/ci/arm-gcc.cmake" "-DCMAKE_BUILD_TYPE=Release" -DCI_MCU=STM32H757xx
cmake --build build/compile-h757
python lib/stm_flash/tests/run_tests.py --mcu STM32H757xx --bus qspi --include ci/include --include .ci-deps/hal/Inc --include .ci-deps/device/Include --include .ci-deps/cmsis/CMSIS/Core/Include --build-dir build/qspi-tests
python lib/stm_sdram/tests/run_tests.py --mcu STM32H757xx --include ci/include --include .ci-deps/hal/Inc --include .ci-deps/device/Include --include .ci-deps/cmsis/CMSIS/Core/Include --build-dir build/sdram-h757-tests
```

H723 使用 OSPI HAL，H757 使用 QSPI HAL；公共头文件仍同时检查 C11/C++17。板级接线、真实 SDRAM 刷新和 NOR 数据备份/恢复须单独做硬件验证。


## Flash/SDRAM v4 核心独立性

Flash/SDRAM 核心不再继承 stm32cubemx。此目录显式选择 H723 OSPI 或 H757 QSPI，并单独构建 FMC 适配器。
独立原生测试不加入任何 HAL/CMSIS 路径，覆盖自定义控制器、器件描述和多实例：

```sh
cmake -S lib/stm_flash/tests/portable -B build/flash-native -G Ninja
cmake --build build/flash-native
ctest --test-dir build/flash-native --output-on-failure
cmake -S lib/stm_sdram/tests/portable -B build/sdram-native -G Ninja
cmake --build build/sdram-native
ctest --test-dir build/sdram-native --output-on-failure
```

此前 Flash/SDRAM `v4.0.0` 组合的 H757 QSPI/FMC 实板验证通过，H723 OSPI/FMC 已完成软件模型回归。当前组合的实际提交与 tag 见总 README；SDRAM `v4.0.1` 增加 FMC ReadBurst 启用配置的接受与软件测试，旧版板测结论不等同于新版完成实板回归。

## 文档与候选版本同步检查

```sh
python ci/check_repository.py
python -m unittest discover -s ci -p test_sync_latest_tags.py
```

前者检查总仓库跟踪的 Markdown（包括 AGENTS.md）、组件目录、README 当前提交和暂存区 gitlink。后者离线测试 tag 选择、版本表更新与历史关系保护，不需要 HAL 或开发板。同步任务的候选选择、预览和合入条件统一见 [CONTRIBUTING.md](../CONTRIBUTING.md)，不用为文档整理运行会修改 gitlink 的同步命令。

## 统一 LCD 框架依赖检查

当前 `stm_lcd`、两个 AXS 驱动及 port 使用通用句柄。主机矩阵加入框架契约与分配失败测试；集成脚本保留五款旧驱动检查，补充框架已有 target/同级源码以及缺失时禁止隐式下载的失败检查。H757 port 示例为通用接口语法检查，不代表新 port 的 DIRECT 板测。

```sh
python lib/stm_lvgl_port/tests/test_dependency.py --lvgl-source .ci-deps/lvgl
```

保留 LVGL 既有 target（含 alias）、离线来源、固定下载选择、选项不覆盖、无配置/错误来源的检查，并用真实 LVGL 编译 C/C++、链接和运行通用面板消费者。该过程不烧录。
