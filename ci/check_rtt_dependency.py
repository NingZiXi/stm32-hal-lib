"""Check local RTT reuse, existing targets and disabled/missing dependency modes."""
from pathlib import Path
import argparse
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True, help='Previously downloaded RTT root')
    args = parser.parse_args()
    rtt = args.source.resolve()
    assert (rtt / 'RTT/SEGGER_RTT.c').is_file()
    with tempfile.TemporaryDirectory(prefix='rtt-check-', dir=ROOT / 'build') as temp:
        for mode in ['disabled', 'source', 'sibling', 'target', 'missing']:
            src = Path(temp) / mode
            src.mkdir()
            shutil.copytree(ROOT / 'lib/stm_log', src / 'lib/stm_log',
                            ignore=shutil.ignore_patterns('.git', 'build', '__pycache__'))
            config = 'cmake_minimum_required(VERSION 3.22)\nproject(check C)\n'
            config += 'add_library(stm32cubemx INTERFACE)\n'
            config += 'target_compile_definitions(stm32cubemx INTERFACE STM32H723xx USE_HAL_DRIVER)\n'
            includes = [ROOT / 'ci/include', ROOT / '.ci-deps/hal/Inc', ROOT / '.ci-deps/device/Include', ROOT / '.ci-deps/cmsis/CMSIS/Core/Include']
            config += 'target_include_directories(stm32cubemx INTERFACE ' + ' '.join(f'"{p.as_posix()}"' for p in includes) + ')\n'
            config += 'set(STM_LOG_RTT_FETCH OFF CACHE BOOL "")\n'
            config += f'set(STM_LOG_WITH_RTT {"OFF" if mode == "disabled" else "ON"} CACHE BOOL "")\n'
            if mode == 'source':
                config += f'set(STM_LOG_RTT_SOURCE_DIR "{rtt.as_posix()}" CACHE PATH "")\n'
                config += f'set(STM_LOG_RTT_CONFIG_DIR "{rtt.as_posix()}/Config" CACHE PATH "")\n'
            elif mode == 'sibling':
                shutil.copytree(rtt, src / 'lib/RTT', ignore=shutil.ignore_patterns('.git'))
            elif mode == 'target':
                config += f'add_library(segger_rtt STATIC "{rtt.as_posix()}/RTT/SEGGER_RTT.c")\n'
                config += f'target_include_directories(segger_rtt PUBLIC "{rtt.as_posix()}/RTT" "{rtt.as_posix()}/Config")\n'
            config += 'add_subdirectory(lib/stm_log)\n'
            config += 'target_compile_definitions(stm_log PUBLIC STM_LOG_HAL_HEADER="stm32h7xx_hal.h")\n'
            if mode == 'disabled':
                config += 'if(TARGET segger_rtt)\nmessage(FATAL_ERROR "Unexpected RTT target")\nendif()\n'
            else:
                config += f'add_executable(check "{(ROOT / "ci/rtt_link.c").as_posix()}")\n'
                config += 'target_link_libraries(check PRIVATE stm_log)\n'
                config += 'target_link_options(check PRIVATE --specs=nosys.specs -nostartfiles -Wl,-e,main)\n'
            (src / 'CMakeLists.txt').write_text(config, encoding='utf-8')
            result = subprocess.run(['cmake', '-S', str(src), '-B', str(src / 'out'), '-G', 'Ninja',
                f'-DCMAKE_TOOLCHAIN_FILE={(ROOT / "ci/arm-gcc.cmake").as_posix()}'], capture_output=True, text=True)
            if mode == 'missing':
                assert result.returncode and 'RTT is missing' in result.stderr
            else:
                if result.returncode:
                    raise RuntimeError(result.stdout + result.stderr)
                build = subprocess.run(['cmake', '--build', str(src / 'out')], capture_output=True, text=True)
                if build.returncode:
                    raise RuntimeError(build.stdout + build.stderr)
            print(f'PASS: RTT {mode}', flush=True)


if __name__ == '__main__':
    main()
