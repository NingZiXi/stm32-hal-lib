"""Check tracked documentation links and pinned, initialized submodules offline."""
import configparser
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

from sync_latest_tags import BADGE, COMMIT, component_row

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True, encoding='utf-8')


def check_readme_references(readme, entries):
    for path, sha in entries.items():
        if not path.startswith('lib/'):
            continue
        name = Path(path).name
        try:
            row = component_row(readme, name)
        except ValueError as error:
            raise SystemExit(str(error)) from error
        commit = COMMIT.fullmatch(row[2].strip())
        if not commit or commit['name'] != name or commit['sha'] != sha or commit['short'] != sha[:12]:
            raise SystemExit(f'{path}: README current commit differs from staged gitlink')
        release = row[3].strip()
        badge = BADGE.fullmatch(release)
        if badge:
            if badge['name'] != name or badge['sha'] != sha:
                raise SystemExit(f'{path}: README version badge must link to the current commit')
        elif not release.startswith('未发布（基于 '):
            raise SystemExit(f'{path}: expected a version badge or an unpublished baseline')


def main():
    modules = configparser.ConfigParser()
    modules.read(ROOT / '.gitmodules', encoding='utf-8')
    entries = {}
    for row in git('ls-files', '--stage').splitlines():
        metadata, path = row.split('\t', 1)
        mode, sha, stage = metadata.split()
        if stage != '0':
            raise SystemExit(f'Unresolved merge: {path}')
        if mode == '160000':
            entries[path] = sha

    configured = set()
    for section in modules.sections():
        path = modules[section]['path']
        url = modules[section]['url']
        configured.add(path)
        if not re.fullmatch(r'(lib/(stm_[a-z0-9_]+|esp_at_client)|skills/[^/]+)', path):
            raise SystemExit(f'Unexpected component path: {path}')
        expected_url = f'../{Path(path).name}.git'
        if url != expected_url:
            raise SystemExit(f'Expected same-owner relative URL {expected_url}: {url}')
        if path not in entries or not (ROOT / path / '.git').exists():
            raise SystemExit(f'Uninitialized/untracked component: {path}')
        for required in ['README.md', 'LICENSE']:
            if not (ROOT / path / required).is_file():
                raise SystemExit(f'Missing {path}/{required}')
        if path.startswith('lib/') and not (ROOT / path / 'CMakeLists.txt').is_file():
            raise SystemExit(f'Missing {path}/CMakeLists.txt')
        actual = git('-C', path, 'rev-parse', 'HEAD').strip()
        if actual != entries[path]:
            raise SystemExit(f'{path}: HEAD differs from staged gitlink; stage the intended version')
    if not entries or set(entries) != configured:
        raise SystemExit('Gitlinks and .gitmodules disagree')

    check_readme_references((ROOT / 'README.md').read_text(encoding='utf-8'), entries)

    checked = 0
    for name in git('ls-files', '-z').split('\0'):
        if not name.endswith('.md'):
            continue
        document = ROOT / name
        content = re.sub(r'```.*?```', '', document.read_text(encoding='utf-8'), flags=re.S)
        for link in re.findall(r'\]\(([^\s)]+)\)', content):
            parsed = urlsplit(link.strip('<>'))
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (document.parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(ROOT) or not target.exists():
                raise SystemExit(f'Broken local link in {name}: {link}')
            checked += 1
    subprocess.run(['git', 'diff', '--check'], cwd=ROOT, check=True)
    subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, check=True)
    print(f'PASS: {len(entries)} pinned components, {checked} local Markdown links')


if __name__ == '__main__':
    main()
