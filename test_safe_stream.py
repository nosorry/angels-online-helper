import unittest

import Game


class FakeStream:
    def __init__(self):
        self.written = []

    def write(self, message):
        self.written.append(message)

    def flush(self):
        pass


class BrokenStream:
    def write(self, message):
        raise ValueError("no console available")

    def flush(self):
        pass


class SafeStreamTest(unittest.TestCase):
    def test_buffers_until_attached(self):
        stream = Game.SafeStream()
        stream.write("early line\n")
        target = FakeStream()
        stream.attach(target)
        self.assertEqual(target.written, ["early line\n"])

    def test_passthrough_to_initial_target(self):
        target = FakeStream()
        stream = Game.SafeStream(target)
        stream.write("hello\n")
        self.assertEqual(target.written, ["hello\n"])

    def test_write_survives_broken_target(self):
        stream = Game.SafeStream(BrokenStream())
        stream.write("x")  # must not raise
        good = FakeStream()
        stream.attach(good)
        self.assertEqual(good.written, ["x"])

    def test_empty_write_is_ignored(self):
        target = FakeStream()
        stream = Game.SafeStream(target)
        stream.write("")
        self.assertEqual(target.written, [])

    def test_write_after_attach_passes_through(self):
        stream = Game.SafeStream()
        target = FakeStream()
        stream.attach(target)
        target.written.clear()  # clear the (empty) replay
        stream.write("after\n")
        self.assertEqual(target.written, ["after\n"])


if __name__ == "__main__":
    unittest.main()
