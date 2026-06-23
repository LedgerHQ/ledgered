from unittest import TestCase
from unittest.mock import patch, PropertyMock
from github import Github

from ledgered.github import AppRepository


class TestAppRepository(TestCase):
    def setUp(self):
        self.gh = Github()

    def _get_repo(self, is_rust: bool) -> AppRepository:
        with patch("github.Repository.Repository", AppRepository):
            app_repo = self.gh.get_repo("LedgerHQ/ledgered")
        # `_set_variants` dispatches on the app language, so the manifest must be
        # mocked to avoid a real network fetch.
        manifest_patch = patch.object(AppRepository, "manifest", new_callable=PropertyMock)
        manifest = manifest_patch.start()
        manifest.return_value.app.is_rust = is_rust
        self.addCleanup(manifest_patch.stop)
        return app_repo

    def test__set_variants_VARIANTS(self):
        param = "COIN"
        coins = ["COIN1", "COIN2"]
        AppRepository.makefile = f"@echo VARIANTS {param} {' '.join(coins)}"
        app_repo = self._get_repo(is_rust=False)
        self.assertIsNone(app_repo._variant_param)
        self.assertListEqual(app_repo._variant_values, [])

        self.assertIsNone(app_repo._set_variants())

        self.assertEqual(app_repo._variant_param, param)
        self.assertListEqual(app_repo._variant_values, coins)

    def test__set_variants_VARIANTS_variable(self):
        param = "COIN"
        AppRepository.makefile = f"@echo VARIANTS {param} $(COINS)"
        app_repo = self._get_repo(is_rust=False)
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
        app_repo = self._get_repo(is_rust=False)
        self.assertIsNone(app_repo._variant_param)
        self.assertListEqual(app_repo._variant_values, [])

        self.assertIsNone(app_repo._set_variants())

        self.assertEqual(app_repo._variant_param, param)
        self.assertListEqual(app_repo._variant_values, coins)

    def test__set_variants_standard_variable(self):
        param = "COIN"
        AppRepository.makefile = f"VARIANT_PARAM= {param}\nVARIANT_VALUES = $(COINS)"
        app_repo = self._get_repo(is_rust=False)
        self.assertIsNone(app_repo._variant_param)
        self.assertListEqual(app_repo._variant_values, [])

        self.assertIsNone(app_repo._set_variants())

        # `$(COIN)` can not be interpreted from Ledgered, so the variants can not be parsed
        self.assertIsNone(app_repo._variant_param)
        self.assertListEqual(app_repo._variant_values, [])

    def test__set_variants_rust(self):
        AppRepository.makefile = (
            "[package]\n"
            'name = "app-boilerplate-rust"\n'
            "\n"
            "[features]\n"
            'default = ["ledger_device_sdk/nano_nbgl"]\n'
            'debug = ["ledger_device_sdk/debug"]\n'
            'variant_testnet = ["ledger_device_sdk/variant_0"]\n'
            'variant_betanet = ["ledger_device_sdk/variant_1"]\n'
        )
        app_repo = self._get_repo(is_rust=True)
        self.assertIsNone(app_repo._variant_param)
        self.assertListEqual(app_repo._variant_values, [])

        self.assertIsNone(app_repo._set_variants())

        self.assertEqual(app_repo._variant_param, "--features")
        self.assertListEqual(app_repo._variant_values, ["variant_testnet", "variant_betanet"])

    def test__set_variants_rust_no_variant(self):
        AppRepository.makefile = (
            "[package]\n"
            'name = "app-boilerplate-rust"\n'
            "\n"
            "[features]\n"
            'default = ["ledger_device_sdk/nano_nbgl"]\n'
            'debug = ["ledger_device_sdk/debug"]\n'
        )
        app_repo = self._get_repo(is_rust=True)

        self.assertIsNone(app_repo._set_variants())

        self.assertIsNone(app_repo._variant_param)
        self.assertListEqual(app_repo._variant_values, [])
