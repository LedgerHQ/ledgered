from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, PropertyMock, patch

from github import ContentFile as PyContentFile
from github.GithubException import GithubException, UnknownObjectException

from ledgered.github import AppRepository, NoManifestException
from ledgered.manifest import MANIFEST_FILE_NAME

from . import TEST_MANIFEST_DIRECTORY

DEFAULT_BRANCH = "main"


def make_repo() -> AppRepository:
    requester = MagicMock()
    requester.base_url = "https://api.github.com"
    url = f"{requester.base_url}/repos/LedgerHQ/app-foo"
    return AppRepository(requester, {}, {"default_branch": DEFAULT_BRANCH, "url": url})


def make_content(content: str) -> PyContentFile.ContentFile:
    file = MagicMock(spec=PyContentFile.ContentFile)
    file.decoded_content = content.encode()
    return file


class TestAppRepository(TestCase):
    def _set_makefile(self, content: str) -> None:
        makefile_patch = patch.object(AppRepository, "makefile", new_callable=PropertyMock, return_value=content)
        makefile_patch.start()
        self.addCleanup(makefile_patch.stop)

    def _get_repo(self, is_rust: bool) -> AppRepository:
        app_repo = make_repo()
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
        self._set_makefile(f"@echo VARIANTS {param} {' '.join(coins)}")
        app_repo = self._get_repo(is_rust=False)
        self.assertIsNone(app_repo._variant_param)
        self.assertListEqual(app_repo._variant_values, [])

        self.assertIsNone(app_repo._set_variants())

        self.assertEqual(app_repo._variant_param, param)
        self.assertListEqual(app_repo._variant_values, coins)

    def test__set_variants_VARIANTS_variable(self):
        param = "COIN"
        self._set_makefile(f"@echo VARIANTS {param} $(COINS)")
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
        self._set_makefile(f"VARIANT_PARAM={param}\nVARIANT_VALUES = {' '.join(coins)}")
        app_repo = self._get_repo(is_rust=False)
        self.assertIsNone(app_repo._variant_param)
        self.assertListEqual(app_repo._variant_values, [])

        self.assertIsNone(app_repo._set_variants())

        self.assertEqual(app_repo._variant_param, param)
        self.assertListEqual(app_repo._variant_values, coins)

    def test__set_variants_standard_variable(self):
        param = "COIN"
        self._set_makefile(f"VARIANT_PARAM= {param}\nVARIANT_VALUES = $(COINS)")
        app_repo = self._get_repo(is_rust=False)
        self.assertIsNone(app_repo._variant_param)
        self.assertListEqual(app_repo._variant_values, [])

        self.assertIsNone(app_repo._set_variants())

        # `$(COIN)` can not be interpreted from Ledgered, so the variants can not be parsed
        self.assertIsNone(app_repo._variant_param)
        self.assertListEqual(app_repo._variant_values, [])

    def test__set_variants_rust(self):
        # Only the `default` feature and the `variant_`-prefixed features are
        # considered app variants; other features are ignored.
        self._set_makefile(
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
        self.assertListEqual(app_repo._variant_values, ["default", "variant_testnet", "variant_betanet"])

    def test__set_variants_rust_no_feature(self):
        self._set_makefile('[package]\nname = "app-boilerplate-rust"\n')
        app_repo = self._get_repo(is_rust=True)

        self.assertIsNone(app_repo._set_variants())

        self.assertIsNone(app_repo._variant_param)
        self.assertListEqual(app_repo._variant_values, [])

    def test__set_variants_rust_invalid_toml(self):
        self._set_makefile("not [ valid toml")
        app_repo = self._get_repo(is_rust=True)

        self.assertIsNone(app_repo._set_variants())

        self.assertIsNone(app_repo._variant_param)
        self.assertListEqual(app_repo._variant_values, [])

    def test__set_variants_rust_no_variant_feature(self):
        # Features that are neither `default` nor `variant_`-prefixed are not
        # variants, so nothing should be detected.
        self._set_makefile(
            "[package]\n"
            'name = "app-boilerplate-rust"\n'
            "\n"
            "[features]\n"
            'debug = ["ledger_device_sdk/debug"]\n'
            'pending_review_screen = ["ledger_device_sdk/pending_review_screen"]\n'
        )
        app_repo = self._get_repo(is_rust=True)

        self.assertIsNone(app_repo._set_variants())

        self.assertIsNone(app_repo._variant_param)
        self.assertListEqual(app_repo._variant_values, [])


class TestAppRepositoryContents(TestCase):
    def setUp(self):
        self.repo = make_repo()
        self.repo.get_contents = MagicMock()
        self.repo.get_branch = MagicMock()
        self.manifest_content = (TEST_MANIFEST_DIRECTORY / MANIFEST_FILE_NAME).read_text()

    def test_manifest(self):
        self.repo.get_contents.return_value = make_content(self.manifest_content)

        self.assertEqual(self.repo.manifest.app.sdk, "rust")
        self.repo.get_contents.assert_called_once_with(MANIFEST_FILE_NAME, ref=DEFAULT_BRANCH)

    def test_manifest_cached(self):
        self.repo.get_contents.return_value = make_content(self.manifest_content)

        self.assertIs(self.repo.manifest, self.repo.manifest)
        self.repo.get_contents.assert_called_once()

    def test_manifest_not_found(self):
        for exception in (GithubException, UnknownObjectException):
            with self.subTest(exception=exception):
                self.repo.get_contents.side_effect = exception(404)
                with self.assertRaises(NoManifestException):
                    _ = self.repo.manifest

    def test_manifest_other_error(self):
        for exception in (GithubException, UnknownObjectException):
            with self.subTest(exception=exception):
                self.repo.get_contents.side_effect = exception(500)
                with self.assertRaises(exception) as error:
                    _ = self.repo.manifest
                self.assertNotIsInstance(error.exception, NoManifestException)

    def _mock_manifest(self, is_rust: bool, build_directory: Path) -> None:
        manifest_patch = patch.object(AppRepository, "manifest", new_callable=PropertyMock)
        manifest = manifest_patch.start()
        manifest.return_value.app.is_rust = is_rust
        manifest.return_value.app.build_directory = build_directory
        self.addCleanup(manifest_patch.stop)

    def test_makefile_path_c(self):
        self._mock_manifest(is_rust=False, build_directory=Path("app"))
        self.assertEqual(self.repo.makefile_path, Path("app/Makefile"))

    def test_makefile_path_rust(self):
        self._mock_manifest(is_rust=True, build_directory=Path("app"))
        self.assertEqual(self.repo.makefile_path, Path("app/Cargo.toml"))

    def test_makefile(self):
        self._mock_manifest(is_rust=False, build_directory=Path("some/dir"))
        self.repo.get_contents.return_value = make_content("some makefile")

        self.assertEqual(self.repo.makefile, "some makefile")
        self.assertEqual(self.repo.makefile, "some makefile")
        self.repo.get_contents.assert_called_once_with("some/dir/Makefile", ref=DEFAULT_BRANCH)

    def test_makefile_windows_path(self):
        windows_path = MagicMock()
        windows_path.__str__.return_value = "some\\dir\\Makefile"
        with patch.object(AppRepository, "makefile_path", new_callable=PropertyMock, return_value=windows_path):
            self.repo.get_contents.return_value = make_content("")
            _ = self.repo.makefile
        self.repo.get_contents.assert_called_once_with("some/dir/Makefile", ref=DEFAULT_BRANCH)

    def test_variant_param_triggers_parsing(self):
        self._mock_manifest(is_rust=False, build_directory=Path(""))
        self.repo.get_contents.return_value = make_content("VARIANT_PARAM=COIN\nVARIANT_VALUES = A B")

        self.assertEqual(self.repo.variant_param, "COIN")
        self.assertListEqual(self.repo.variants, ["A", "B"])

    def test_current_branch(self):
        self.assertEqual(self.repo.current_branch, DEFAULT_BRANCH)
        self.repo.get_branch.return_value.name = "develop"

        self.repo.current_branch = "develop"

        self.repo.get_branch.assert_called_once_with("develop")
        self.assertEqual(self.repo.current_branch, "develop")

    def test_current_branch_invalidates_cache(self):
        self._mock_manifest(is_rust=False, build_directory=Path(""))
        self.repo.get_contents.return_value = make_content("VARIANT_PARAM=COIN\nVARIANT_VALUES = A B")
        self.assertListEqual(self.repo.variants, ["A", "B"])
        self.repo._manifest = MagicMock()

        self.repo.get_branch.return_value.name = "develop"
        self.repo.current_branch = "develop"

        self.assertIsNone(self.repo._manifest)
        self.assertIsNone(self.repo._makefile)
        self.assertIsNone(self.repo._variant_param)
        self.assertListEqual(self.repo._variant_values, [])

        self.repo.get_contents.return_value = make_content("VARIANT_PARAM=OTHER\nVARIANT_VALUES = C")
        self.assertEqual(self.repo.variant_param, "OTHER")
        self.assertListEqual(self.repo.variants, ["C"])
        self.repo.get_contents.assert_called_with("Makefile", ref="develop")
