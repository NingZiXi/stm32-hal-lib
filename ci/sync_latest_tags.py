"""Move tagged library submodules to their newest stable semantic-version tag.

Run from any directory: python ci/sync_latest_tags.py
Only lib/ submodules with vMAJOR.MINOR.PATCH (or MAJOR.MINOR.PATCH) tags
are changed. Untagged libraries and skills stay at their current commits.
"""

import argparse
import configparser
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TAG = re.compile(r"v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\Z")
BADGE = re.compile(
    r"\[!\[version [^]]+\]\(https://img\.shields\.io/badge/"
    r"version-[^)]*\)\]\(https://github\.com/NingZiXi/[^/)]+/tree/[^)]+\)"
)


def git(*args, cwd=ROOT):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True, encoding="utf-8").strip()


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


def update_badge(readme, name, tag, sha):
    pattern = re.compile(rf"^(\| \[{re.escape(name)}\]\([^)]*\) \| )([^|]*)( \|.*)$", re.M)
    version = tag.removeprefix("v")
    badge = (f"[![version {version}](https://img.shields.io/badge/version-{version}-5364b5?style=flat-square)]"
             f"(https://github.com/NingZiXi/{name}/tree/{sha})")

    def replace(match):
        if not BADGE.fullmatch(match[2].strip()) and not match[2].strip().startswith("main"):
            raise ValueError(f"Unexpected README version cell for {name}: {match[2]}")
        return match[1] + badge + match[3]

    updated, count = pattern.subn(replace, readme)
    if count != 1:
        raise ValueError(f"Expected exactly one README row for {name}; found {count}")
    return updated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report available updates without modifying files")
    args = parser.parse_args()
    if not args.dry_run and git("status", "--porcelain", "--untracked-files=no"):
        raise SystemExit("Commit or stash tracked changes in the root repository first")
    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    changes = []
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
        updated = update_badge(readme, Path(path).name, tag, sha)
        if current == sha and updated == readme:
            continue
        changes.append(f"{path}: {current[:12]} -> {tag} ({sha[:12]})")
        if not args.dry_run:
            if current != sha:
                git("-C", path, "fetch", "--no-tags", "origin", "tag", tag)
                # Refuse a tag that moved between listing and fetching.
                fetched = git("-C", path, "rev-parse", f"refs/tags/{tag}^{{commit}}")
                if fetched != sha:
                    raise SystemExit(f"Remote tag moved during update: {path} {tag}")
                git("-C", path, "checkout", "--detach", sha)
            readme = updated
            git("add", path)
    if not args.dry_run and readme != readme_path.read_text(encoding="utf-8"):
        readme_path.write_text(readme, encoding="utf-8")
        git("add", "README.md")
    print("\n".join(changes) if changes else "All tagged libraries already up to date")


if __name__ == "__main__":
    main()
