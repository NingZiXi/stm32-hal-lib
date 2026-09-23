# CI 与本地检查

在总仓库根目录执行。工具需要 Git、Python 3.12、CMake 3.22+、Ninja、GNU Arm GCC/G++ 和 ARM newlib 头文件。CI 使用 Ubuntu 24.04，具体步骤见 [ci.yml](../.github/workflows/ci.yml)。

## 依赖

组件须完整初始化：

```sh
git submodule update --init --recursive
python ci/check_repository.py
```

文档检查只检查总仓库跟踪的 Markdown 中内联链接的本地文件目标，不检查外部网站可用性或标题锚点。子模块引用必须与暂存区记录一致；新增文件须先 `git add` 才会纳入检查。

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
cmake -S ci -B build/compile -G Ninja "-DCMAKE_TOOLCHAIN_FILE=arm-gcc.cmake" "-DCMAKE_BUILD_TYPE=Release"
cmake --build build/compile
```

此工程只生成静态库和编译检查对象，不产生可烧录固件。检查组件通过各自 CMake 目标继承 HAL 配置，检查组合公共头文件的 C11/C++17 消费者，以及 `STM_LOG_ENABLED=0` 的日志源文件。LittleFS 上游固定为 v2.11.2 对应提交，由适配组件自动下载。

LittleFS 主机测试使用本机 GCC/G++，无需连接开发板：

```sh
cmake -S lib/stm_littlefs/tests -B build/littlefs-tests -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build/littlefs-tests
ctest --test-dir build/littlefs-tests --output-on-failure
python ci/check_littlefs_dependency.py --littlefs-source build/compile/_deps/littlefs-src
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

当前不包含日志运行时测试、完整固件链接或硬件在环测试。CI 的成功只代表上述软件检查通过。

RTT 可选依赖还会执行独立编译和链接检查：

```sh
cmake -S ci -B build/rtt -G Ninja "-DCMAKE_TOOLCHAIN_FILE=arm-gcc.cmake" -DSTM_LOG_WITH_RTT=ON
cmake --build build/rtt
python ci/check_rtt_dependency.py --source build/rtt/_deps/segger_rtt-src
```

首个构建实际下载固定 RTT 提交，应用只链接 `stm_log`，验证 RTT 头文件和符号被正确传递；后续检查覆盖关闭依赖、指定本地源码/配置、同级目录、已有 target 和离线缺失报错。链接检查使用 HAL 桩和 newlib nosys，产物仅用于检查，不可烧录，也不代表 RTT 硬件通信测试通过。

升级依赖时同步修改工作流和本文的 commit，并重新运行全部检查。组件更新须先推送到独立远程，再提交总仓库的 gitlink；CI 的递归 checkout 会验证该提交能从远程获取。

## H757 / QSPI 扩展检查

```sh
cmake -S ci -B build/compile-h757 -G Ninja "-DCMAKE_TOOLCHAIN_FILE=arm-gcc.cmake" "-DCMAKE_BUILD_TYPE=Release" -DCI_MCU=STM32H757xx
cmake --build build/compile-h757
python lib/stm_flash/tests/run_tests.py --mcu STM32H757xx --bus qspi --include ci/include --include .ci-deps/hal/Inc --include .ci-deps/device/Include --include .ci-deps/cmsis/CMSIS/Core/Include --build-dir build/qspi-tests
python lib/stm_sdram/tests/run_tests.py --mcu STM32H757xx --include ci/include --include .ci-deps/hal/Inc --include .ci-deps/device/Include --include .ci-deps/cmsis/CMSIS/Core/Include --build-dir build/sdram-h757-tests
```

H723 使用 OSPI HAL，H757 使用 QSPI HAL；公共头文件仍同时检查 C11/C++17。板级接线、真实 SDRAM 刷新和 NOR 数据备份/恢复须单独做硬件验证。


## v4 开发分支的核心独立性

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

当前内存组件已发布为 `v4.0.0`；H757 QSPI/FMC 实板验证通过，H723 OSPI/FMC 已完成软件模型回归。总仓库 gitlink 固定到已推送的提交。
