"""显示组件的依赖解析、离线失败和真实 HAL/LVGL 示例编译检查，不连接硬件。"""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
HAL_COMPONENTS = ['stm_lcd_st7789', 'stm_lcd_st7796', 'stm_lcd_ili9881c',
                  'stm_lcd_touch_ft5206', 'stm_lcd_touch_gt9271', 'stm_lvgl_port']
# AXS15231B 示例使用 F407 HAL，不混入 H757 示例编译；核心/依赖/公共头文件仍检查。
COMPONENTS = HAL_COMPONENTS + ['stm_lcd_axs15231b', 'stm_lcd_touch_axs15231b']
PIN = 'ce3d186dde2d374a8e9c7b9068a7b88f97d57dc1'


def run(command, log, expect_missing=False):
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
    log.write_text(result.stdout + result.stderr, encoding='utf-8')
    if expect_missing:
        if result.returncode == 0 or 'stm_common is missing' not in result.stderr:
            raise RuntimeError(f'Expected offline dependency error: {log}')
    elif result.returncode:
        raise RuntimeError(f'Command failed: {command}\nSee {log}\n{result.stdout[-2000:]}{result.stderr[-2000:]}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lvgl-source', required=True, type=Path, help='Local LVGL 9.3.0 source')
    parser.add_argument('--c-compiler', default='gcc')
    parser.add_argument('--cxx-compiler', default='g++')
    parser.add_argument('--arm-compiler', default='arm-none-eabi-gcc')
    parser.add_argument('--repository', default=(ROOT / 'lib/stm_common').as_posix(), help='Repository/mirror used to test pinned FetchContent')
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'build/display-api-migration/integration')
    args = parser.parse_args()
    output = args.build_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    lvgl = args.lvgl_source.resolve()
    if not (lvgl / 'lvgl.h').is_file():
        raise RuntimeError(f'Missing LVGL source: {lvgl}')
    version = (lvgl / 'lv_version.h').read_text(encoding='utf-8')
    assert all(re.search(r'#define\s+LVGL_VERSION_' + part + r'\s+' + value + r'\b', version)
               for part, value in [('MAJOR', '9'), ('MINOR', '3'), ('PATCH', '0')]), 'Use LVGL 9.3.0'
    # 新目录隔离依赖，避免历史缓存掩盖下载/离线错误；保留目录与日志供排查。
    sandbox = Path(tempfile.mkdtemp(prefix='dependency-', dir=output)).resolve()
    assert sandbox.is_relative_to(output)
    modes = ['target', 'sibling', 'source_override', 'fetch_forward', 'fetch_reverse']
    modes += [f'offline_{name}' for name in COMPONENTS]
    for mode in modes:
        source = sandbox / mode
        source.mkdir()
        order = COMPONENTS if mode != 'fetch_reverse' else list(reversed(COMPONENTS))
        missing = mode.startswith('offline_')
        if missing:
            order = [mode.removeprefix('offline_')]
        for name in order:
            shutil.copytree(ROOT / 'lib' / name, source / 'lib' / name,
                            ignore=shutil.ignore_patterns('.git', 'build', '__pycache__'))
        flags = []
        prelude = ''
        common = ROOT / 'lib/stm_common'
        if mode == 'target':
            prelude = f'add_subdirectory("{common.as_posix()}" common)\n'
        elif mode == 'sibling':
            common = source / 'lib/stm_common'
            shutil.copytree(ROOT / 'lib/stm_common', common, ignore=shutil.ignore_patterns('.git'))
        elif mode == 'source_override':
            flags += [f'-DFETCHCONTENT_SOURCE_DIR_STM_COMMON={common.as_posix()}']
        if mode in ['target', 'sibling'] or missing:
            flags += ['-DSTM_COMMON_FETCH=OFF']
        flags += [f'-DSTM_COMMON_GIT_REPOSITORY={args.repository if mode.startswith("fetch_") else (source / "missing-repo").as_posix()}']
        cmake = 'cmake_minimum_required(VERSION 3.22)\nproject(display_dependencies C)\n'
        cmake += 'add_compile_options(-Wall -Wextra -Werror)\nadd_library(lvgl INTERFACE)\n'
        cmake += f'target_include_directories(lvgl INTERFACE "{(ROOT / "lib/stm_lvgl_port/tests").as_posix()}")\n'
        cmake += prelude + ''.join(f'add_subdirectory(lib/{name})\n' for name in order)
        cmake += 'get_target_property(common_source stm_common SOURCE_DIR)\nfile(WRITE "${CMAKE_BINARY_DIR}/common-source.txt" "${common_source}")\n'
        (source / 'CMakeLists.txt').write_text(cmake, encoding='utf-8')
        binary = source / 'out'
        run(['cmake', '-S', str(source), '-B', str(binary), '-G', 'Ninja',
             f'-DCMAKE_C_COMPILER={args.c_compiler}', *flags], output / f'{mode}-configure.log', missing)
        if not missing:
            actual = Path((binary / 'common-source.txt').read_text()).resolve()
            if mode.startswith('fetch_'):
                revision = subprocess.check_output(['git', '-C', str(actual), 'rev-parse', 'HEAD'], text=True).strip()
                assert revision == PIN, revision
            else:
                assert actual == common.resolve(), (actual, common)
            run(['cmake', '--build', str(binary)], output / f'{mode}-build.log')
        print(f'PASS: dependency {mode}', flush=True)

    # 使用真实 H757 HAL/CMSIS 和 LVGL 头文件，不用主机桩冒充 HAL 示例检查。
    config = output / 'lv_conf.h'
    config.write_text('#ifndef LV_CONF_H\n#define LV_CONF_H\n#define LV_COLOR_DEPTH 16\n#endif\n', encoding='utf-8')
    includes = [ROOT / 'ci/include', ROOT / '.ci-deps/hal/Inc', ROOT / '.ci-deps/device/Include',
                ROOT / '.ci-deps/cmsis/CMSIS/Core/Include', ROOT / 'lib/stm_common', lvgl]
    flags = ['-mcpu=cortex-m7', '-mthumb', '-mfloat-abi=soft', '-std=c11', '-Wall', '-Wextra', '-Werror',
             '-DSTM32H757xx', '-DUSE_HAL_DRIVER', '-DCORE_CM7', '-DHAL_DSI_MODULE_ENABLED',
             f'-DLV_CONF_PATH="{config.as_posix()}"']
    for name in HAL_COMPONENTS:
        component = ROOT / 'lib' / name
        command = [args.arm_compiler, *flags]
        for path in [*includes, component / 'include', component / 'examples/stm32_hal']:
            command += ['-I', str(path)]
        command += ['-c', str(component / 'examples/stm32_hal/example.c'), '-o', str(output / f'{name}-example.o')]
        run(command, output / f'{name}-example.log')
        print(f'PASS: HAL example {name}', flush=True)
    # 聚合所有公共头文件，使用真实 LVGL 检查 C11/C++17 消费者及 port 实现。
    port = ROOT / 'lib/stm_lvgl_port'
    for extension in ['c', 'cpp']:
        content = ''.join(f'#include "{name}.h"\n' for name in COMPONENTS)
        (output / f'all-display-headers.{extension}').write_text(content, encoding='utf-8')
    for extension, compiler, standard in [('c', args.c_compiler, 'c11'), ('cpp', args.cxx_compiler, 'c++17')]:
        command = [compiler, f'-std={standard}', '-Wall', '-Wextra', '-Werror',
                   f'-DLV_CONF_PATH="{config.as_posix()}"']
        for path in [lvgl, ROOT / 'lib/stm_common', *[ROOT / 'lib' / name / 'include' for name in COMPONENTS]]:
            command += ['-I', str(path)]
        # LVGL 来自源码 -I，不把测试桩的 include 路径加入消费者。
        command += ['-c', str(output / f'all-display-headers.{extension}'), '-o', str(output / f'lvgl-headers-{extension}.o')]
        run(command, output / f'lvgl-real-headers-{extension}.log')
    run([args.c_compiler, '-std=c11', '-Wall', '-Wextra', '-Werror',
         f'-DLV_CONF_PATH="{config.as_posix()}"', '-I', str(lvgl), '-I', str(ROOT / 'lib/stm_common'),
         '-I', str(port / 'include'), '-c', str(port / 'src/stm_lvgl_port.c'), '-o', str(output / 'lvgl-real-port.o')],
        output / 'lvgl-real-port.log')
    print('PASS: real LVGL port C11/C++17 headers and implementation', flush=True)


if __name__ == '__main__':
    main()
