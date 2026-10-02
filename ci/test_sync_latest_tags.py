"""Offline unit tests for the tag selector and version cell renderer."""
import contextlib
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import sync_latest_tags
from check_repository import check_readme_references
from sync_latest_tags import latest_tag, update_badge


def readme_row(sha, release='未发布（基于 v1.0.0）'):
    return (f'| [stm_log](https://github.com/NingZiXi/stm_log) | '
            f'[`{sha[:12]}`](https://github.com/NingZiXi/stm_log/tree/{sha}) | {release} | notes |\n')


class SyncLatestTagsTest(unittest.TestCase):
    def test_annotated_lightweight_and_prerelease(self):
        listing = "\n".join([
            "a" * 40 + "\trefs/tags/v1.9.0",
            "b" * 40 + "\trefs/tags/v2.0.0",
            "c" * 40 + "\trefs/tags/v2.0.0^{}",
            "d" * 40 + "\trefs/tags/v3.0.0-rc1",
            "e" * 40 + "\trefs/tags/v1.10.0",
        ])
        self.assertEqual(latest_tag(listing), ("v2.0.0", "c" * 40))

    def test_no_release(self):
        self.assertIsNone(latest_tag("a" * 40 + "\trefs/tags/v1.2.0-beta"))

    def test_badge_tracks_selected_commit(self):
        row = readme_row('a' * 40)
        new = update_badge(row, "stm_log", "v3.0.2", "f" * 40)
        self.assertIn("version-3.0.2-5364b5", new)
        self.assertIn("/tree/" + "f" * 40, new)
        self.assertEqual(update_badge(new, "stm_log", "v3.0.2", "f" * 40), new)

    def test_missing_or_duplicate_rows_fail(self):
        row = readme_row('a' * 40)
        for document in ['', row + row]:
            with self.assertRaises(ValueError):
                update_badge(document, 'stm_log', 'v3.0.2', 'f' * 40)

    def test_repository_check_rejects_stale_references(self):
        current = 'f' * 40
        entries = {'lib/stm_log': current}
        published = update_badge(readme_row(current), 'stm_log', 'v3.0.2', current)
        check_readme_references(published, entries)
        check_readme_references(readme_row(current), entries)
        with self.assertRaisesRegex(SystemExit, 'current commit differs'):
            check_readme_references(readme_row('a' * 40), entries)
        stale_badge = published.rsplit('/tree/' + current, 1)
        with self.assertRaisesRegex(SystemExit, 'badge must link'):
            check_readme_references(('/tree/' + 'a' * 40).join(stale_badge), entries)


class LocalRepositorySyncTest(unittest.TestCase):
    """Exercise the real updater against local repositories, without network."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.remote = base / 'component'
        self.remote.mkdir()
        self.run_git(self.remote, 'init', '-b', 'main')
        self.configure(self.remote)
        self.initial = self.commit('initial')
        self.run_git(self.remote, 'tag', 'v1.0.0')
        self.development = self.commit('unpublished')
        self.root = base / 'aggregate'
        self.root.mkdir()
        self.run_git(self.root, 'init', '-b', 'main')
        self.configure(self.root)
        self.module = self.root / 'lib/stm_log'
        self.run_git(self.root, 'clone', str(self.remote), str(self.module))
        (self.root / '.gitmodules').write_text(
            '[submodule "lib/stm_log"]\npath = lib/stm_log\nurl = ../component\n', encoding='utf-8')
        self.readme = self.root / 'README.md'
        self.readme.write_text(readme_row(self.development), encoding='utf-8')
        self.run_git(self.root, 'add', '.gitmodules', 'README.md', 'lib/stm_log')
        self.run_git(self.root, 'commit', '-m', 'fixed combination')

    @staticmethod
    def run_git(directory, *args):
        return subprocess.check_output(['git', *args], cwd=directory, text=True,
                                       encoding='utf-8', stderr=subprocess.PIPE).strip()

    def configure(self, directory):
        self.run_git(directory, 'config', 'user.name', 'Sync tests')
        self.run_git(directory, 'config', 'user.email', 'sync-tests@example.invalid')

    def commit(self, value):
        (self.remote / 'source.txt').write_text(value, encoding='utf-8')
        self.run_git(self.remote, 'add', 'source.txt')
        self.run_git(self.remote, 'commit', '-m', value)
        return self.run_git(self.remote, 'rev-parse', 'HEAD')

    def invoke(self, *args):
        output = io.StringIO()
        with patch.object(sync_latest_tags, 'ROOT', self.root), \
                patch('sys.argv', ['sync_latest_tags.py', *args]), contextlib.redirect_stdout(output):
            sync_latest_tags.main()
        return output.getvalue()

    def test_old_tag_preserves_development_combination(self):
        original = self.readme.read_bytes()
        output = self.invoke()
        self.assertIn('not a fast-forward', output)
        self.assertEqual(self.run_git(self.module, 'rev-parse', 'HEAD'), self.development)
        self.assertEqual(self.readme.read_bytes(), original)
        self.assertEqual(self.run_git(self.root, 'status', '--porcelain'), '')

    def test_new_tag_preview_then_fast_forward(self):
        newest = self.commit('new release')
        self.run_git(self.remote, 'tag', '-a', 'v1.0.1', '-m', 'new release')
        original = self.readme.read_bytes()
        output = self.invoke('--dry-run')
        self.assertIn('history needs fetching', output)
        self.assertEqual(self.readme.read_bytes(), original)
        self.assertEqual(self.run_git(self.module, 'rev-parse', 'HEAD'), self.development)
        self.assertEqual(self.run_git(self.root, 'status', '--porcelain'), '')
        self.invoke()
        self.assertEqual(self.run_git(self.module, 'rev-parse', 'HEAD'), newest)
        self.assertIn(newest, self.readme.read_text(encoding='utf-8'))
        self.assertIn('version-1.0.1-', self.readme.read_text(encoding='utf-8'))
        staged = self.run_git(self.root, 'ls-files', '--stage', 'lib/stm_log')
        self.assertIn(newest, staged)
        self.run_git(self.root, 'commit', '-m', 'accept update')
        self.assertIn('No eligible updates', self.invoke())

    def test_divergent_release_preserves_combination(self):
        self.run_git(self.remote, 'checkout', '--detach', self.initial)
        self.commit('other history')
        self.run_git(self.remote, 'tag', 'v2.0.0')
        original = self.readme.read_bytes()
        self.assertIn('not a fast-forward', self.invoke())
        self.assertEqual(self.run_git(self.module, 'rev-parse', 'HEAD'), self.development)
        self.assertEqual(self.readme.read_bytes(), original)
        self.assertEqual(self.run_git(self.root, 'status', '--porcelain'), '')


if __name__ == "__main__":
    unittest.main()
