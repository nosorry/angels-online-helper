import unittest

from Game import launcher_start_click_position


class LauncherStartClickPositionTest(unittest.TestCase):
    def test_uses_global_launcher_start_button_position(self):
        self.assertEqual(
            launcher_start_click_position(left=684, top=266, width=551, height=500),
            (742, 745),
        )


if __name__ == "__main__":
    unittest.main()
