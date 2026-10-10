"""验证本地通用显示迁移的依赖能力与优先级，不联网、不接触硬件。"""
import argparse
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CHIPS = ['stm_lcd_st7789', 'stm_lcd_st7796', 'stm_lcd_ili9881c',
         'stm_lcd_touch_ft5206', 'stm_lcd_touch_gt9271']
COMPONENTS = CHIPS + ['stm_lvgl_port']
EXTENDED = CHIPS[2:] + ['stm_lvgl_port']
BASELINE = 'c359e54a657be38aec90c797ea19ee3d492d9284'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lvgl-source', type=Path,
                        default=ROOT / '.ci-deps/lvgl-c033a98afddd65aaafeebea625382a94020fe4a7')
    parser.add_argument('--build-dir', type=Path,
                        default=ROOT / 'build/display-migration-dependencies')
    args = parser.parse_args()
    output = args.build_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    sandbox = Path(tempfile.mkdtemp(prefix='cases-', dir=output))
    baseline = sandbox / 'published-lcd'
    baseline.mkdir()
    archive = subprocess.run(['git', '-C', str(ROOT / 'lib/stm_lcd'), 'archive', BASELINE],
                             check=True, capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as files:
        for member in files.getmembers():
            target = (baseline / member.name).resolve()
            if not target.is_relative_to(baseline.resolve()):
                raise RuntimeError('Archive path outside baseline directory')
            if member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(files.extractfile(member).read())
    if not (args.lvgl_source / 'lvgl.h').is_file():
        raise RuntimeError('Provide actual local LVGL 9.3.0 source')
    results = []

    def case(name, components, mode, expected=None, flags=()):
        source = sandbox / name
        source.mkdir()
        for chip in components:
            shutil.copytree(ROOT / 'lib' / chip, source / 'lib' / chip,
                            ignore=shutil.ignore_patterns('.git', 'build', '__pycache__'))
        common = (ROOT / 'lib/stm_common').as_posix()
        lcd = (ROOT / 'lib/stm_lcd').as_posix()
        lines = ['cmake_minimum_required(VERSION 3.22)', 'project(dependencies C)',
                 f'add_subdirectory("{common}" common)',
                 'set(STM_COMMON_FETCH OFF CACHE BOOL "" FORCE)',
                 'set(STM_LCD_FETCH OFF CACHE BOOL "" FORCE)',
                 'set(STM_LVGL_PORT_FETCH_LVGL OFF CACHE BOOL "" FORCE)',
                 f'set(STM_LVGL_PORT_LVGL_SOURCE_DIR "{args.lvgl_source.resolve().as_posix()}" CACHE PATH "" FORCE)',
                 f'set(LV_BUILD_CONF_PATH "{(ROOT / "lib/stm_lvgl_port/tests/real_lvgl/lv_conf.h").as_posix()}" CACHE FILEPATH "" FORCE)']
        if mode in ('target', 'build_interface'):
            lines += [f'add_subdirectory("{lcd}" lcd)',
                      'set(STM_LCD_SOURCE_DIR "invalid-but-target-wins" CACHE PATH "" FORCE)']
            if mode == 'build_interface':
                lines += [f'set_property(TARGET stm_lcd PROPERTY INTERFACE_INCLUDE_DIRECTORIES "$<BUILD_INTERFACE:{lcd}/include>;$<INSTALL_INTERFACE:include>")']
        elif mode == 'alias':
            lines += [f'add_library(actual_lcd STATIC "{lcd}/src/stm_lcd_io.c" "{lcd}/src/stm_lcd_panel.c" "{lcd}/src/stm_lcd_touch.c")',
                      f'target_include_directories(actual_lcd PUBLIC "$<BUILD_INTERFACE:{lcd}/include>" "$<INSTALL_INTERFACE:include>")',
                      'target_link_libraries(actual_lcd PUBLIC stm_common)',
                      'add_library(stm_lcd ALIAS actual_lcd)']
        elif mode in ('explicit', 'fetch_override'):
            # 明确本地来源应优先于旧同级源码。
            shutil.copytree(baseline, source / 'lib/stm_lcd')
            variable = 'STM_LCD_SOURCE_DIR' if mode == 'explicit' else 'FETCHCONTENT_SOURCE_DIR_STM_LCD'
            lines += [f'set({variable} "{lcd}" CACHE PATH "" FORCE)']
        elif mode == 'sibling':
            shutil.copytree(ROOT / 'lib/stm_lcd', source / 'lib/stm_lcd',
                            ignore=shutil.ignore_patterns('.git', 'build', '__pycache__'))
        elif mode == 'baseline':
            lines += [f'add_subdirectory("{baseline.as_posix()}" lcd)']
        elif mode == 'invalid':
            shutil.copytree(ROOT / 'lib/stm_lcd', source / 'lib/stm_lcd',
                            ignore=shutil.ignore_patterns('.git', 'build', '__pycache__'))
            lines += ['set(STM_LCD_SOURCE_DIR "missing-explicit" CACHE PATH "" FORCE)']
        elif mode == 'mirror':
            lines += ['set(STM_LCD_FETCH ON CACHE BOOL "" FORCE)',
                      f'set(STM_LCD_GIT_REPOSITORY "{lcd}" CACHE STRING "" FORCE)']
        lines += [f'add_subdirectory(lib/{chip} {chip})' for chip in components]
        (source / 'CMakeLists.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
        command = ['cmake', '-S', str(source), '-B', str(source / 'out'), '-G', 'Ninja',
                   '-DCMAKE_C_COMPILER=gcc', *flags]
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
        text = result.stdout + result.stderr
        (sandbox / (name + '.log')).write_text(text, encoding='utf-8')
        passed = result.returncode == 0 if expected is None else result.returncode != 0 and expected in text
        results.append({'case': name, 'passed': passed, 'expected_error': expected})
        if not passed:
            raise RuntimeError(f'{name} failed; see {sandbox / (name + ".log")}\n{text[-1500:]}')
        if mode == 'mirror' and expected != 'fully disconnected':
            sha = subprocess.run(['git', '-C', str(source / 'out/_deps/stm_lcd-src'), 'rev-parse', 'HEAD'],
                                 capture_output=True, text=True, check=True).stdout.strip()
            if sha != BASELINE:
                raise RuntimeError(f'{name}: unexpected downloaded SHA {sha}')

    try:
        for mode in ('target', 'build_interface', 'alias', 'sibling'):
            case(mode, COMPONENTS, mode)
        for mode in ('explicit', 'fetch_override'):
            case(mode, CHIPS, mode)
        case('old_spi', CHIPS[:2], 'baseline')
        for chip in EXTENDED:
            case('old_' + chip, [chip], 'baseline', 'STM_LCD_FRAMEBUFFER_API=1')
        for chip in CHIPS:
            case('invalid_' + chip, [chip], 'invalid', 'stm_lcd local source is invalid')
            case('missing_' + chip, [chip], 'missing', 'stm_lcd is missing')
            case('disconnected_' + chip, [chip], 'mirror', 'fully disconnected',
                 ['-DFETCHCONTENT_FULLY_DISCONNECTED=ON'])
        case('missing_port', ['stm_lvgl_port'], 'missing', 'stm_lcd is missing')
        case('mirror_spi', CHIPS[:2], 'mirror')
        for chip in CHIPS[2:]:
            case('mirror_old_' + chip, [chip], 'mirror', 'STM_LCD_FRAMEBUFFER_API=1')
    finally:
        (sandbox / 'results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{len(results)} dependency cases passed; logs: {sandbox}')


if __name__ == '__main__':
    main()
