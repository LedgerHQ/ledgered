from github import Github as PyGithub, Repository as PyRepository
from typing import List, Optional
from unittest.mock import patch

from ledgered.manifest import MANIFEST_FILE_NAME, Manifest

LEDGER_ORG_NAME = "ledgerhq"


class AppRepository(PyRepository.Repository):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._manifest: Optional[Manifest] = None

    @property
    def manifest(self) -> Manifest:
        if self._manifest is None:
            manifest_content = self.get_contents(MANIFEST_FILE_NAME).decoded_content.decode()
            self._manifest = Manifest.from_string(manifest_content)
        return self._manifest


class GitHubApps(list):

    def __init__(self, the_list):
        with patch("github.Repository.Repository", AppRepository):
            new_list = [r for r in self._org.get_repos() if r.name.startswith("app-")]
        super(self).__init__(new_list)

    def filter(self,
               include_archived: bool = False,
               include_private: bool = True) -> GitHubApps:


    def get(self, name_filter: str = None) -> List[AppRepository]:
        results = self._repos
        if name_filter is not None:
            results = [r for r in results if name_filter.lower() in r.name.lower()]
        return results

    def first(self, *args, **kwargs) -> Optional[AppRepository]:
        results = self.get(*args, **kwargs)
        return results[0] if results else None


class LedgerHQ(Github):

    def __init__(self, *args, **kwargs):
        super(*args, **kwargs)
        self._org = self.get_organization(LEDGER_ORG_NAME)
        self._apps: Optional[GitHubApps] = None

    @property
    def apps(self) -> GitHubApps:
        if self._apps = None:
            pass
        return self._apps
