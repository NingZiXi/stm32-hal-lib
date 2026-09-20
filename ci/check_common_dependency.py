"""Build isolated consumers to verify local, shared and fetched stm_common."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PIN = 'ce3d186dde2d374a8e9c7b9068a7b88f97d57dc1'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', default='https://github.com/NingZiXi/stm_common.git')
    args = parser.parse_args()
    output = ROOT / 'build'
    output.mkdir(exist_ok=True)
    # 每次用独立目录，防止同级依赖或旧 FetchContent 缓存掩盖自动下载问题。
    with tempfile.TemporaryDirectory(prefix='common-check-', dir=output) as temp:
        for mode, order in [('target', ['stm_flash', 'stm_sdram']),
                            ('sibling', ['stm_sdram', 'stm_flash']),
                            ('source_override', ['stm_flash', 'stm_sdram']),
                            ('fetch_flash', ['stm_flash', 'stm_sdram']),
                            ('fetch_sdram', ['stm_sdram', 'stm_flash']),
                            ('offline_missing', ['stm_flash']),
                            ('offline_missing_sdram', ['stm_sdram'])]:
            source = Path(temp) / mode
            source.mkdir()
            for name in order:
                shutil.copytree(ROOT / 'lib' / name, source / 'lib' / name,
                                ignore=shutil.ignore_patterns('.git', 'build', '__pycache__'))
            common = ROOT / 'lib/stm_common'
            prelude = ''
            flags = []
            if mode == 'target':
                prelude = f'add_subdirectory("{common.as_posix()}" common)\n'
            elif mode == 'sibling':
                shutil.copytree(common, source / 'lib/stm_common',
                                ignore=shutil.ignore_patterns('.git'))
                common = source / 'lib/stm_common'
            elif mode == 'source_override':
                flags += [f'-DFETCHCONTENT_SOURCE_DIR_STM_COMMON={common.as_posix()}']
            if mode in ('target', 'sibling') or mode.startswith('offline_missing'):
                flags += ['-DSTM_COMMON_FETCH=OFF']
            remote = mode.startswith('fetch_')
            flags += [f'-DSTM_COMMON_GIT_REPOSITORY={args.repository if remote else source.as_posix() + "/missing-repo"}']
            includes = [ROOT / 'ci/include', ROOT / '.ci-deps/hal/Inc',
                        ROOT / '.ci-deps/device/Include', ROOT / '.ci-deps/cmsis/CMSIS/Core/Include']
            cmake = 'cmake_minimum_required(VERSION 3.22)\nproject(check C)\n'
            cmake += 'add_library(stm32cubemx INTERFACE)\n'
            cmake += 'target_compile_definitions(stm32cubemx INTERFACE STM32H723xx USE_HAL_DRIVER)\n'
            cmake += 'target_include_directories(stm32cubemx INTERFACE ' + ' '.join(f'"{p.as_posix()}"' for p in includes) + ')\n'
            cmake += 'add_compile_options(-Wall -Wextra -Werror)\n' + prelude
            cmake += ''.join(f'add_subdirectory(lib/{name})\n' for name in order)
            cmake += 'get_target_property(common_source stm_common SOURCE_DIR)\n'
            cmake += 'file(WRITE "${CMAKE_BINARY_DIR}/common-source.txt" "${common_source}")\n'
            (source / 'CMakeLists.txt').write_text(cmake, encoding='utf-8')
            binary = source / 'out'
            command = ['cmake', '-S', str(source), '-B', str(binary), '-G', 'Ninja',
                       f'-DCMAKE_TOOLCHAIN_FILE={(ROOT / "ci/arm-gcc.cmake").as_posix()}', *flags]
            result = subprocess.run(command, capture_output=True, text=True)
            if mode.startswith('offline_missing'):
                if result.returncode == 0 or 'stm_common is missing' not in result.stderr:
                    raise RuntimeError(result.stdout + result.stderr)
            else:
                if result.returncode:
                    raise RuntimeError(result.stdout + result.stderr)
                actual = Path((binary / 'common-source.txt').read_text()).resolve()
                if remote:
                    revision = subprocess.check_output(['git', '-C', str(actual), 'rev-parse', 'HEAD'], text=True).strip()
                    assert revision == PIN, revision
                else:
                    assert actual == common.resolve(), (actual, common)
                subprocess.run(['cmake', '--build', str(binary)], check=True)
            print(f'PASS: {mode}', flush=True)


if __name__ == '__main__':
    main()
