import json
import os
import tempfile
import unittest

import Game


class WriteJsonAtomicTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.target = os.path.join(self.tmpdir, "data.json")

    def tearDown(self):
        for name in os.listdir(self.tmpdir):
            os.remove(os.path.join(self.tmpdir, name))
        os.rmdir(self.tmpdir)

    def test_round_trip_writes_readable_json(self):
        payload = [{"account": "a", "password": "p"}]
        Game.write_json_atomic(self.target, payload)
        with open(self.target, encoding="utf-8") as f:
            self.assertEqual(json.load(f), payload)

    def test_failed_write_leaves_existing_file_intact(self):
        with open(self.target, "w", encoding="utf-8") as f:
            json.dump([{"account": "keep-me"}], f)

        with self.assertRaises(TypeError):
            Game.write_json_atomic(self.target, {"good": "value", "bad": object()})

        with open(self.target, encoding="utf-8") as f:
            self.assertEqual(json.load(f), [{"account": "keep-me"}])
        self.assertEqual(os.listdir(self.tmpdir), ["data.json"])


class LoadStartConfigFallbackTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config = os.path.join(self.tmpdir, "start_game.json")
        self._orig_config_path = Game.config_path
        Game.config_path = lambda name: self.config

    def tearDown(self):
        Game.config_path = self._orig_config_path
        for name in os.listdir(self.tmpdir):
            os.remove(os.path.join(self.tmpdir, name))
        os.rmdir(self.tmpdir)

    def test_falls_back_to_defaults_when_file_is_corrupt(self):
        with open(self.config, "w", encoding="utf-8") as f:
            f.write("{ this is not valid json")

        self.assertEqual(
            Game.load_start_config(),
            (Game.application_path, Game.game_window_title),
        )

    def test_falls_back_to_defaults_when_file_is_empty(self):
        open(self.config, "w").close()

        self.assertEqual(
            Game.load_start_config(),
            (Game.application_path, Game.game_window_title),
        )


if __name__ == "__main__":
    unittest.main()
