import unittest
from unittest.mock import patch

import Game


class FakeEntry:
    def __init__(self, value=""):
        self.value = value
        self.deleted = False

    def get(self):
        return self.value

    def delete(self, start, end=None):
        self.deleted = True
        self.value = ""


class FakeListbox:
    def __init__(self):
        self.items = []

    def insert(self, index, value):
        self.items.append(value)

    def delete(self, start, end=None):
        self.items = []

    def size(self):
        return len(self.items)


class AccountDataTest(unittest.TestCase):
    def setUp(self):
        Game.AccountList = []
        Game.input_account = FakeEntry("new-user")
        Game.input_password = FakeEntry("secret")
        Game.input_second_password = FakeEntry("second")
        Game.input_trade_password = FakeEntry("1234")
        Game.myaccountlist = FakeListbox()
        Game.mypasswordlist = FakeListbox()
        Game.passwords_revealed = False

    @patch("Game.tk.messagebox.showinfo")
    def test_savedata_updates_visible_account_list(self, showinfo):
        Game.savedata()

        self.assertEqual([account.account for account in Game.AccountList], ["new-user"])
        self.assertEqual(Game.myaccountlist.items, ["new-user"])
        self.assertEqual(Game.mypasswordlist.items, [Game.PASSWORD_MASK])
        self.assertEqual(Game.input_account.value, "")
        self.assertEqual(Game.input_password.value, "")
        showinfo.assert_not_called()


class UiCallTest(unittest.TestCase):
    def tearDown(self):
        Game.root = None

    def test_ui_call_marshals_to_main_thread(self):
        calls = []

        class FakeRoot:
            def after(self, delay, callback):
                calls.append((delay, callback))

        Game.root = FakeRoot()
        sentinel = lambda: None
        Game.ui_call(sentinel)
        self.assertEqual(calls, [(0, sentinel)])

    def test_ui_call_runs_directly_without_root(self):
        Game.root = None
        ran = []
        Game.ui_call(lambda: ran.append(True))
        self.assertEqual(ran, [True])


class AccountCredentialsTest(unittest.TestCase):
    def setUp(self):
        Game.AccountList = []

    def test_reads_from_accountlist_not_listbox(self):
        Game.AccountList = [
            Game.AccountData("user1", "pw1"),
            Game.AccountData("user2", "pw2"),
        ]
        self.assertEqual(Game.account_credentials(0), ("user1", "pw1"))
        self.assertEqual(Game.account_credentials(1), ("user2", "pw2"))

    def test_out_of_range_index_returns_empty(self):
        Game.AccountList = [Game.AccountData("only", "pw")]
        self.assertEqual(Game.account_credentials(5), ("", ""))


class PasswordMaskingTest(unittest.TestCase):
    def setUp(self):
        Game.AccountList = [
            Game.AccountData("u1", "secret"),
            Game.AccountData("u2", "longerpass"),
        ]
        Game.mypasswordlist = FakeListbox()
        Game.passwords_revealed = False

    def tearDown(self):
        Game.passwords_revealed = False

    def test_masked_by_default(self):
        Game.render_password_list()
        self.assertEqual(
            Game.mypasswordlist.items,
            [Game.PASSWORD_MASK, Game.PASSWORD_MASK],
        )

    def test_mask_hides_length(self):
        self.assertEqual(Game.mask_password("a"), Game.PASSWORD_MASK)
        self.assertEqual(Game.mask_password("a much longer one"), Game.PASSWORD_MASK)
        self.assertEqual(Game.mask_password(""), "")

    def test_reveal_shows_plaintext(self):
        Game.set_passwords_revealed(True)
        self.assertEqual(Game.mypasswordlist.items, ["secret", "longerpass"])

    def test_reveal_then_hide_round_trips(self):
        Game.set_passwords_revealed(True)
        Game.set_passwords_revealed(False)
        self.assertEqual(
            Game.mypasswordlist.items,
            [Game.PASSWORD_MASK, Game.PASSWORD_MASK],
        )


class LabelMappingTest(unittest.TestCase):
    def test_label_from_prediction_maps_argmax_to_label_table(self):
        import numpy as np

        comma_vector = np.zeros(11)
        comma_vector[0] = 1.0
        self.assertEqual(Game.label_from_prediction(comma_vector), ",")

        digit_one_vector = np.zeros(11)
        digit_one_vector[2] = 1.0
        self.assertEqual(Game.label_from_prediction(digit_one_vector), 1)


if __name__ == "__main__":
    unittest.main()
