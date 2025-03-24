from typing import Optional
from unittest import TestCase
from unittest.mock import MagicMock

from ledgered.github import Condition, GitHubApps, GitHubLedgerHQ, NoManifestException


class AppRepositoryMock:
    def __init__(
        self, name: str, sdk: Optional[str] = "c", archived: bool = False, private: bool = False
    ):
        self.name = name
        self.archived = archived
        self.private = private
        self._sdk = sdk

    @property
    def manifest(self) -> str:
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

    def test_first(self):
        self.assertEqual(self.apps.first("3"), self.app3)
        self.assertEqual(self.apps.first(), self.app1)


class TestGitHubLedgerHQ(TestCase):
    def setUp(self):
        self.g = GitHubLedgerHQ()

    def test_get_app_wrong_name(self):
        with self.assertRaises(AssertionError):
            self.g.get_app("not-starting-with-app-")
