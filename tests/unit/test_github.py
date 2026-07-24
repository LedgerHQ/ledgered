from typing import Optional
from unittest import TestCase
from unittest.mock import MagicMock

from ledgered.github import Condition, GitHubApps, GitHubLedgerHQ, NoManifestException


class AppRepositoryMock:
    def __init__(
        self,
        name: str,
        sdk: Optional[str] = "c",
        archived: bool = False,
        private: bool = False,
        error: Optional[Exception] = None,
    ):
        self.name = name
        self.archived = archived
        self.private = private
        self._sdk = sdk
        self._error = error

    @property
    def manifest(self) -> str:
        if self._error is not None:
            raise self._error
        if self._sdk:
            mock = MagicMock()
            mock.app.sdk = self._sdk
            return mock
        else:
            raise NoManifestException(MagicMock())


class TestGitHubApps(TestCase):
    def setUp(self):
        self.app1 = AppRepositoryMock("app-1", sdk="rust")
        self.app2 = AppRepositoryMock("not-app")
        self.app3 = AppRepositoryMock("app-3", private=True)
        self.app4 = AppRepositoryMock("app-4", archived=True)
        self.app5 = AppRepositoryMock("app-plugin-foo")
        self.app6 = AppRepositoryMock("app-foo-legacy")
        self.apps = GitHubApps([self.app1, self.app2, self.app3, self.app4, self.app5, self.app6])

    def test___init__(self):
        self.assertListEqual(self.apps, [self.app1, self.app3, self.app4, self.app5, self.app6])

    def test_filter(self):
        self.assertCountEqual(self.apps.filter(), self.apps)
        self.assertCountEqual(self.apps.filter(name="3"), [self.app3])
        self.assertCountEqual(self.apps.filter(name="app"), self.apps)
        self.assertCountEqual(
            self.apps.filter(archived=Condition.WITHOUT),
            [self.app1, self.app3, self.app5, self.app6],
        )
        self.assertCountEqual(self.apps.filter(archived=Condition.ONLY), [self.app4])
        self.assertCountEqual(
            self.apps.filter(private=Condition.WITHOUT),
            [self.app1, self.app4, self.app5, self.app6],
        )
        self.assertCountEqual(self.apps.filter(private=Condition.ONLY), [self.app3])
        self.assertCountEqual(
            self.apps.filter(legacy=Condition.WITHOUT), [self.app1, self.app3, self.app4, self.app5]
        )
        self.assertCountEqual(self.apps.filter(legacy=Condition.ONLY), [self.app6])
        self.assertCountEqual(
            self.apps.filter(plugin=Condition.WITHOUT), [self.app1, self.app3, self.app4, self.app6]
        )
        self.assertCountEqual(self.apps.filter(plugin=Condition.ONLY), [self.app5])
        self.assertCountEqual(
            self.apps.filter(only_list=["app-1", "app-3"]), [self.app1, self.app3]
        )
        self.assertCountEqual(
            self.apps.filter(exclude_list=["app-1", "app-3"]), [self.app4, self.app5, self.app6]
        )
        self.assertCountEqual(self.apps.filter(sdk=["rust"]), [self.app1])

    def test_filter_sdk_preserves_order(self):
        # The SDK filter reads manifests concurrently; the result must keep the
        # input order and return every match (not just the first).
        apps = GitHubApps(
            [
                AppRepositoryMock("app-a", sdk="rust"),
                AppRepositoryMock("app-b", sdk="c"),
                AppRepositoryMock("app-c", sdk="rust"),
                AppRepositoryMock("app-d", sdk="rust"),
            ]
        )
        self.assertListEqual(apps.filter(sdk=["rust"]), [apps[0], apps[2], apps[3]])

    def test_filter_sdk_is_case_insensitive(self):
        self.assertCountEqual(self.apps.filter(sdk=["RUST"]), [self.app1])

    def test_filter_sdk_skips_apps_without_manifest(self):
        apps = GitHubApps(
            [
                AppRepositoryMock("app-a", sdk="rust"),
                AppRepositoryMock("app-no-manifest", sdk=None),  # raises NoManifestException
                AppRepositoryMock("app-b", sdk="rust"),
            ]
        )
        self.assertListEqual(apps.filter(sdk=["rust"]), [apps[0], apps[2]])

    def test_filter_sdk_propagates_other_errors(self):
        apps = GitHubApps(
            [
                AppRepositoryMock("app-a", sdk="rust"),
                AppRepositoryMock("app-boom", error=RuntimeError("boom")),
            ]
        )
        with self.assertRaises(RuntimeError):
            apps.filter(sdk=["rust"])

    def test_filter_sdk_empty_candidate_list(self):
        # No candidate survives the (manifest-free) filters -> the concurrent
        # section must be a no-op and not spin up a zero-worker pool.
        self.assertListEqual(self.apps.filter(name="does-not-exist", sdk=["rust"]), [])

    def test_first(self):
        self.assertEqual(self.apps.first("3"), self.app3)
        self.assertEqual(self.apps.first(), self.app1)


class TestGitHubLedgerHQ(TestCase):
    def setUp(self):
        self.g = GitHubLedgerHQ()

    def test_get_app_wrong_name(self):
        with self.assertRaises(AssertionError):
            self.g.get_app("not-starting-with-app-")
