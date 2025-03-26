from unittest import TestCase
from unittest.mock import patch
from github import Github

from ledgered.github import AppRepository


class TestAppRepository(TestCase):
    def setUp(self):
        self.gh = Github()

    def test__set_variants_VARIANTS(self):
        param = "COIN"
        coins = ["COIN1", "COIN2"]
        AppRepository.makefile = f"@echo VARIANTS {param} {' '.join(coins)}"
        with patch("github.Repository.Repository", AppRepository):
            app_repo = self.gh.get_repo("LedgerHQ/ledgered")
        self.assertIsNone(app_repo._variant_param)
        self.assertListEqual(app_repo._variant_values, [])

        self.assertIsNone(app_repo._set_variants())

        self.assertEqual(app_repo._variant_param, param)
        self.assertListEqual(app_repo._variant_values, coins)

    def test__set_variants_VARIANTS_variable(self):
        param = "COIN"
        AppRepository.makefile = f"@echo VARIANTS {param} $(COINS)"
        with patch("github.Repository.Repository", AppRepository):
            app_repo = self.gh.get_repo("LedgerHQ/ledgered")
        self.assertIsNone(app_repo._variant_param)
        self.assertListEqual(app_repo._variant_values, [])

        self.assertIsNone(app_repo._set_variants())

        # `$(COIN)` can not be interpreted from Ledgered, so the variants can not be parsed
        self.assertIsNone(app_repo._variant_param)
        self.assertListEqual(app_repo._variant_values, [])

    def test__set_variants_standard(self):
        param = "COIN"
        coins = ["COIN1", "COIN2"]
        AppRepository.makefile = f"VARIANT_PARAM={param}\nVARIANT_VALUES = {' '.join(coins)}"
        with patch("github.Repository.Repository", AppRepository):
            app_repo = self.gh.get_repo("LedgerHQ/ledgered")
        self.assertIsNone(app_repo._variant_param)
        self.assertListEqual(app_repo._variant_values, [])

        self.assertIsNone(app_repo._set_variants())

        self.assertEqual(app_repo._variant_param, param)
        self.assertListEqual(app_repo._variant_values, coins)

    def test__set_variants_standard_variable(self):
        param = "COIN"
        AppRepository.makefile = f"VARIANT_PARAM= {param}\nVARIANT_VALUES = $(COINS)"
        with patch("github.Repository.Repository", AppRepository):
            app_repo = self.gh.get_repo("LedgerHQ/ledgered")
        self.assertIsNone(app_repo._variant_param)
        self.assertListEqual(app_repo._variant_values, [])

        self.assertIsNone(app_repo._set_variants())

        # `$(COIN)` can not be interpreted from Ledgered, so the variants can not be parsed
        self.assertIsNone(app_repo._variant_param)
        self.assertListEqual(app_repo._variant_values, [])
