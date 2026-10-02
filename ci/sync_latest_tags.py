"""Propose fast-forward library updates to their highest numeric version tag.

Run from any directory: python ci/sync_latest_tags.py
Only lib/ submodules with vMAJOR.MINOR.PATCH (or MAJOR.MINOR.PATCH) tags
are considered. Untagged libraries, newer development commits, divergent
histories and skills stay at their current commits. Tags are not Release checks.
"""

import argparse
import configparser
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TAG = re.compile(r"v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\Z")
BADGE = re.compile(
    r"\[!\[version (?P<version>\d+\.\d+\.\d+)\]\(https://img\.shields\.io/badge/"
    r"version-(?P=version)-5364b5\?style=flat-square\)\]"
    r"\(https://github\.com/NingZiXi/(?P<name>[^/)]+)/tree/(?P<sha>[0-9a-f]{40})\)"
)
COMMIT = re.compile(
    r"\[`(?P<short>[0-9a-f]{12})`\]"
    r"\(https://github\.com/NingZiXi/(?P<name>[^/)]+)/tree/(?P<sha>[0-9a-f]{40})\)"
)


def git(*args, cwd=None):
    return subprocess.check_output(["git", *args], cwd=ROOT if cwd is None else cwd,
                                   text=True, encoding="utf-8").strip()


def latest_tag(remote_output):
    """Return (tag, peeled commit) from ls-remote, excluding prereleases."""
    refs = {}
    for row in remote_output.splitlines():
        sha, ref = row.split("\t", 1)
        if not ref.startswith("refs/tags/"):
            continue
        name = ref.removeprefix("refs/tags/")
        peeled = name.endswith("^{}")
        if peeled:
            name = name[:-3]
        if TAG.fullmatch(name):
            refs.setdefault(name, {})["peeled" if peeled else "ref"] = sha
    if not refs:
        return None
    # Prefer v-prefixed tags if two tag names represent the same version.
    name = max(refs, key=lambda tag: (*map(int, TAG.fullmatch(tag).groups()), tag.startswith("v")))
    return name, refs[name].get("peeled") or refs[name]["ref"]


def configured_libraries():
    config = configparser.ConfigParser()
    config.read(ROOT / ".gitmodules", encoding="utf-8")
    return [config[section]["path"] for section in config.sections()
            if config[section]["path"].startswith("lib/")]


def component_row(readme, name):
    pattern = re.compile(
        rf"^(\| \[{re.escape(name)}\]\(https://github\.com/NingZiXi/{re.escape(name)}\) \| )"
        r"([^|]+) \| ([^|]+)( \|[^\r\n]*\|)$", re.M)
    rows = list(pattern.finditer(readme))
    if len(rows) != 1:
        raise ValueError(f"Expected exactly one README row for {name}; found {len(rows)}")
    return rows[0]


def update_badge(readme, name, tag, sha):
    row = component_row(readme, name)
    if not COMMIT.fullmatch(row[2].strip()):
        raise ValueError(f"Unexpected README commit cell for {name}: {row[2]}")
    if not BADGE.fullmatch(row[3].strip()) and not row[3].strip().startswith("未发布（基于 "):
        raise ValueError(f"Unexpected README release cell for {name}: {row[3]}")
    version = tag.removeprefix("v")
    badge = (f"[![version {version}](https://img.shields.io/badge/version-{version}-5364b5?style=flat-square)]"
             f"(https://github.com/NingZiXi/{name}/tree/{sha})")
    commit = f"[`{sha[:12]}`](https://github.com/NingZiXi/{name}/tree/{sha})"
    replacement = row[1] + commit + " | " + badge + row[4]
    return readme[:row.start()] + replacement + readme[row.end():]


def update_relation(module, current, candidate):
    """Check history without downloading objects (also used by dry-run)."""
    if current == candidate:
        return "same"
    available = subprocess.run(["git", "cat-file", "-e", f"{candidate}^{{commit}}"],
                               cwd=module, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if available.returncode:
        return "unknown"
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", current, candidate], cwd=module)
    if ancestor.returncode == 0:
        return "forward"
    if ancestor.returncode != 1:
        raise RuntimeError(f"Unable to inspect history: {module}")
    return "development-or-divergent"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report available updates without modifying files")
    args = parser.parse_args()
    if not args.dry_run and git("status", "--porcelain", "--untracked-files=no"):
        raise SystemExit("Commit or stash tracked changes in the root repository first")
    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    changes = []
    planned = []
    for path in configured_libraries():
        module = ROOT / path
        if not (module / ".git").exists():
            raise SystemExit(f"Uninitialized submodule: {path}; run git submodule update --init --recursive")
        if git("status", "--porcelain", cwd=module):
            raise SystemExit(f"Submodule has local changes: {path}")
        remote = git("-C", path, "remote", "get-url", "origin")
        selected = latest_tag(git("ls-remote", "--tags", remote))
        if selected is None:
            print(f"SKIP {path}: no stable version tags")
            continue
        tag, sha = selected
        current = git("-C", path, "rev-parse", "HEAD")
        relation = update_relation(module, current, sha)
        if relation == "unknown" and not args.dry_run:
            git("-C", path, "fetch", "--no-tags", "origin", "tag", tag)
            fetched = git("-C", path, "rev-parse", f"refs/tags/{tag}^{{commit}}")
            if fetched != sha:
                raise SystemExit(f"Remote tag moved during update: {path} {tag}")
            relation = update_relation(module, current, sha)
        if relation == "development-or-divergent":
            print(f"SKIP {path}: {tag} is not a fast-forward; preserve current commit")
            continue
        updated = update_badge(readme, Path(path).name, tag, sha)
        if current == sha and updated == readme:
            continue
        suffix = " (history needs fetching and verification)" if relation == "unknown" else ""
        changes.append(f"{path}: {current[:12]} -> {tag} ({sha[:12]}){suffix}")
        readme = updated
        planned.append((path, current, sha))
    # Validate the whole plan before changing working trees, gitlinks or README.
    if not args.dry_run:
        for path, current, sha in planned:
            if current != sha:
                git("-C", path, "checkout", "--detach", sha)
            git("add", path)
    if not args.dry_run and readme != readme_path.read_text(encoding="utf-8"):
        readme_path.write_text(readme, encoding="utf-8")
        git("add", "README.md")
    print("\n".join(changes) if changes else "No eligible updates (current commits unchanged)")


if __name__ == "__main__":
    main()
