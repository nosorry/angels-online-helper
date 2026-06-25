import os
import tempfile
import unittest

import Game


class LauncherPathIsValidTest(unittest.TestCase):
    def test_empty_path_is_invalid(self):
        self.assertFalse(Game.launcher_path_is_valid(""))

    def test_missing_path_is_invalid(self):
        self.assertFalse(
            Game.launcher_path_is_valid(r"C:\does\not\exist\START.EXE")
        )

    def test_existing_file_is_valid(self):
        with tempfile.NamedTemporaryFile(suffix=".EXE", delete=False) as tmp:
            path = tmp.name
        try:
            self.assertTrue(Game.launcher_path_is_valid(path))
        finally:
            os.remove(path)

    def test_directory_is_not_a_valid_launcher(self):
        tmpdir = tempfile.mkdtemp()
        try:
            self.assertFalse(Game.launcher_path_is_valid(tmpdir))
        finally:
            os.rmdir(tmpdir)


class CountMatchingTitlesTest(unittest.TestCase):
    def test_empty_needle_matches_nothing(self):
        self.assertEqual(
            Game.count_matching_titles(["Angels Online Global"], ""), 0
        )

    def test_counts_substring_matches(self):
        titles = [
            "Angels Online Global - hero1",
            "Angels Online Global - hero2",
            "Notepad",
            "Angels Online Global",
        ]
        self.assertEqual(
            Game.count_matching_titles(titles, "Angels Online Global"), 3
        )

    def test_no_match_returns_zero(self):
        self.assertEqual(
            Game.count_matching_titles(["Notepad", "Chrome"], "Angels Online Global"),
            0,
        )

    def test_empty_title_list_returns_zero(self):
        self.assertEqual(Game.count_matching_titles([], "Angels Online Global"), 0)


if __name__ == "__main__":
    unittest.main()
