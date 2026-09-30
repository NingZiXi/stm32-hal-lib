"""Offline unit tests for the tag selector and version cell renderer."""
import unittest

from sync_latest_tags import latest_tag, update_badge


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
        row = "| [stm_log](https://github.com/NingZiXi/stm_log) | main (test) | notes |\n"
        new = update_badge(row, "stm_log", "v3.0.2", "f" * 40)
        self.assertIn("version-3.0.2-5364b5", new)
        self.assertIn("/tree/" + "f" * 40, new)
        self.assertEqual(update_badge(new, "stm_log", "v3.0.2", "f" * 40), new)


if __name__ == "__main__":
    unittest.main()
