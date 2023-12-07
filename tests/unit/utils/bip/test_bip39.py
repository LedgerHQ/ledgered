from unittest import TestCase

from ledgered.utils.bip import bip39


class TestBip39Module(TestCase):

    def test_generate_mnemonic_nok_nad_size(self):
        wrong_size = 49
        with self.assertRaises(AssertionError) as e:
            bip39.generate_mnemonic("whatever", wrong_size, format="not important")
        assert f"{wrong_size}" in str(e.exception)

    def test_generate_mnemonic_nok_bad_type(self):
        with self.assertRaises(AssertionError):
            bip39.generate_mnemonic("whatever", 12, format="not important")

    def test_generate_mnemonic_nok_bad_language(self):
        with self.assertRaises(ValueError):
            bip39.generate_mnemonic("whatever", 12, format=str)

    def test_generate_mnemonic_ok_12_list(self):
        format = list
        size = 12
        result = bip39.generate_mnemonic("english", size, format=format)
        self.assertIsInstance(result, format)
        self.assertEqual(len(result), size)

    def test_generate_mnemonic_ok_18_tuple(self):
        format = tuple
        size = 18
        result = bip39.generate_mnemonic("english", size, format=format)
        self.assertIsInstance(result, format)
        self.assertEqual(len(result), size)

    def test_generate_mnemonic_ok_24_str(self):
        size = 24
        result = bip39.generate_mnemonic("english", size)
        self.assertIsInstance(result, str)
        self.assertEqual(len(result.split()), size)
