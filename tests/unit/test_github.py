from dataclasses import dataclass
from unittest import TestCase

from ledgered.github import Condition, GitHubApps, GitHubLedgerHQ


@dataclass
class AppRepositoryMock:
    name: str
    archived: bool = False
    private: bool = False


class TestGitHubApps(TestCase):
    def setUp(self):
        self.app1 = AppRepositoryMock("app-1")
        self.app2 = AppRepositoryMock("not-app")
        self.app3 = AppRepositoryMock("app-3", private=True)
        self.app4 = AppRepositoryMock("app-4", archived=True)
        self.apps = GitHubApps([self.app1, self.app2, self.app3, self.app4])

    def test___init__(self):
        self.assertListEqual(self.apps, [self.app1, self.app3, self.app4])

    def test_filter(self):
        self.assertCountEqual(self.apps.filter(), self.apps)
        self.assertCountEqual(self.apps.filter(name="3"), [self.app3])
        self.assertCountEqual(self.apps.filter(name="app"), self.apps)
        self.assertCountEqual(self.apps.filter(archived=Condition.WITHOUT), [self.app1, self.app3])
        self.assertCountEqual(self.apps.filter(archived=Condition.ONLY), [self.app4])
        self.assertCountEqual(self.apps.filter(private=Condition.WITHOUT), [self.app1, self.app4])
        self.assertCountEqual(self.apps.filter(private=Condition.ONLY), [self.app3])

    def test_first(self):
        self.assertEqual(self.apps.first("3"), self.app3)
        self.assertEqual(self.apps.first(), self.app1)


class TestGitHubLedgerHQ(TestCase):
    def setUp(self):
        self.g = GitHubLedgerHQ()

    def test_get_app_wrong_name(self):
        with self.assertRaises(AssertionError):
            self.g.get_app("not-starting-with-app-")
