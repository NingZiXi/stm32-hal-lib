"""Exercise stm_littlefs dependency resolution in isolated ARM builds."""
import argparse
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--deps-root', type=Path, default=ROOT / '.ci-deps')
    parser.add_argument('--littlefs-source', type=Path, required=True)
    parser.add_argument('--flash-repository', default='https://github.com/NingZiXi/stm_flash.git')
    parser.add_argument('--common-repository', default='https://github.com/NingZiXi/stm_common.git')
    args = parser.parse_args()
    deps = args.deps_root.resolve()
    source = args.littlefs_source.resolve()
    output = ROOT / 'build/littlefs-dependency'
    for scenario in ['missing_flash', 'missing_littlefs', 'provided_targets', 'fetch_flash']:
        folder = output / scenario
        component = folder / 'adapter'
        component.mkdir(parents=True, exist_ok=True)
        for name in ['CMakeLists.txt', 'stm_littlefs.c', 'stm_littlefs.h']:
            shutil.copyfile(ROOT / 'lib/stm_littlefs' / name, component / name)
        base = '''cmake_minimum_required(VERSION 3.22)
project(littlefs_dependency C)
add_library(stm32cubemx INTERFACE)
target_compile_definitions(stm32cubemx INTERFACE USE_HAL_DRIVER STM32H723xx)
'''
        includes = [ROOT / 'ci/include', deps / 'hal/Inc', deps / 'device/Include', deps / 'cmsis/CMSIS/Core/Include']
        base += 'target_include_directories(stm32cubemx INTERFACE ' + ' '.join(f'"{p.as_posix()}"' for p in includes) + ')\n'
        if scenario in ['missing_littlefs', 'provided_targets']:
            base += f'add_subdirectory("{ROOT.as_posix()}/lib/stm_flash" flash)\n'
        if scenario == 'provided_targets':
            base += f'''add_library(littlefs STATIC "{source.as_posix()}/lfs.c" "{source.as_posix()}/lfs_util.c")
target_include_directories(littlefs PUBLIC "{source.as_posix()}")
'''
        base += 'add_subdirectory(adapter)\n'
        (folder / 'CMakeLists.txt').write_text(base, encoding='utf-8')
        command = ['cmake', '-S', str(folder), '-B', str(folder / 'build'), '-G', 'Ninja',
                   f'-DCMAKE_TOOLCHAIN_FILE={ROOT / "ci/arm-gcc.cmake"}', '-DCMAKE_BUILD_TYPE=Debug',
                   '-DSTM_LITTLEFS_FETCH=OFF',
                   f'-DSTM_LITTLEFS_FETCH_FLASH={"ON" if scenario == "fetch_flash" else "OFF"}']
        if scenario == 'fetch_flash':
            command += [f'-DSTM_LITTLEFS_SOURCE_DIR={source}',
                        f'-DSTM_LITTLEFS_FLASH_GIT_REPOSITORY={args.flash_repository}',
                        f'-DSTM_COMMON_GIT_REPOSITORY={args.common_repository}']
        result = subprocess.run(command, capture_output=True, text=True)
        if scenario.startswith('missing_'):
            message = 'Provide stm_flash' if scenario == 'missing_flash' else 'Provide littlefs'
            if result.returncode == 0 or message not in result.stdout + result.stderr:
                raise SystemExit(result.stdout + result.stderr)
        else:
            if result.returncode:
                raise SystemExit(result.stdout + result.stderr)
            subprocess.run(['cmake', '--build', str(folder / 'build')], check=True)
            if scenario == 'fetch_flash':
                for name, sha in [('stm_flash', '2d44d3c091262a4d79b33b04ca47a8a04b2fee35'),
                                  ('stm_common', 'ce3d186dde2d374a8e9c7b9068a7b88f97d57dc1')]:
                    checkout = folder / 'build/_deps' / f'{name}-src'
                    actual = subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip()
                    if actual != sha:
                        raise SystemExit(f'{name}: expected {sha}, got {actual}')
        print(f'PASS LittleFS dependency: {scenario}', flush=True)


if __name__ == '__main__':
    main()
