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
python -m pip install -r components/stm_flash/tests/requirements.txt -r components/stm_sdram/tests/requirements.txt
```

## 编译检查

```sh
cmake -S ci -B build/compile -G Ninja "-DCMAKE_TOOLCHAIN_FILE=arm-gcc.cmake" "-DCMAKE_BUILD_TYPE=Release"
cmake --build build/compile
```

此工程只生成静态库和编译检查对象，不产生可烧录固件。检查三个组件通过各自 CMake 目标继承 HAL 配置，检查组合公共头文件的 C11/C++17 消费者，以及 `STM_LOG_ENABLED=0` 的日志源文件。

`ci/include/stm32h7xx_hal_conf.h` 仅用于 H723 编译与 HAL 桩测试，没有 GPIO、启动、链接脚本或板级配置，不应替代实际工程的 HAL 配置。

## 模拟测试

以下命令 PowerShell 和 Bash 均可执行：

```sh
python components/stm_flash/tests/run_tests.py --include ci/include --include .ci-deps/hal/Inc --include .ci-deps/device/Include --include .ci-deps/cmsis/CMSIS/Core/Include --build-dir build/flash-tests
python components/stm_sdram/tests/run_tests.py --include ci/include --include .ci-deps/hal/Inc --include .ci-deps/device/Include --include .ci-deps/cmsis/CMSIS/Core/Include --build-dir build/sdram-tests
```

两个运行器分别编译并执行 O0/O2/Os 测试；使用 HAL 桩和 Unicorn Cortex-M7，不访问真实硬件。测试细节见各子模块的 `tests/README.md`，在线版本见 [Flash 测试](https://github.com/NingZiXi/stm_flash/blob/main/tests/README.md) 与 [SDRAM 测试](https://github.com/NingZiXi/stm_sdram/blob/main/tests/README.md)。

当前不包含日志运行时测试、完整固件链接或硬件在环测试。CI 的成功只代表上述软件检查通过。

升级依赖时同步修改工作流和本文的 commit，并重新运行全部检查。组件更新须先推送到独立远程，再提交总仓库的 gitlink；CI 的递归 checkout 会验证该提交能从远程获取。
