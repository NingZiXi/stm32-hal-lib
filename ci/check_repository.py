"""Check tracked documentation links and pinned, initialized submodules offline."""
import configparser
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True, encoding='utf-8')


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
        if not re.fullmatch(r'lib/stm_[a-z0-9_]+', path):
            raise SystemExit(f'Unexpected component path: {path}')
        expected_url = f'../{Path(path).name}.git'
        if url != expected_url:
            raise SystemExit(f'Expected same-owner relative URL {expected_url}: {url}')
        if path not in entries or not (ROOT / path / '.git').exists():
            raise SystemExit(f'Uninitialized/untracked component: {path}')
        for required in ['README.md', 'LICENSE', 'CMakeLists.txt']:
            if not (ROOT / path / required).is_file():
                raise SystemExit(f'Missing {path}/{required}')
        actual = git('-C', path, 'rev-parse', 'HEAD').strip()
        if actual != entries[path]:
            raise SystemExit(f'{path}: HEAD differs from staged gitlink; stage the intended version')
    if not entries or set(entries) != configured:
        raise SystemExit('Gitlinks and .gitmodules disagree')

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
