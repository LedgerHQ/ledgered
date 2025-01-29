import pytest
import requests
from pathlib import Path

from github.GithubException import GithubException
from ledgered.github import AppRepository, GitHubApps


def test_apps(gh):
    assert isinstance(gh.apps, list)
    assert isinstance(gh.apps, GitHubApps)


def test_get_app(gh):
    name = "app-exchange"
    app = gh.get_app(name)
    assert isinstance(app, AppRepository)
    assert app.name == name


def test_exchange_manifest(exchange):
    assert exchange.manifest.app.sdk == "c"
    assert len(exchange.manifest.app.devices) == 4


def test_exchange_makefile_path(exchange):
    assert exchange.makefile_path == Path("./Makefile")


def test_exchange_makefile(exchange):
    makefile = requests.get(
        "https://raw.githubusercontent.com/LedgerHQ/app-exchange/develop/Makefile"
    ).content.decode()
    assert exchange.makefile == makefile


def test_exchange_branches(exchange):
    assert exchange.current_branch == "develop"
    exchange.current_branch = "master"
    assert exchange.current_branch == "master"

    with pytest.raises(GithubException):
        exchange.current_branch = "does not exists"


def test_exchange_variant(exchange):
    assert exchange.variants == ["exchange"]


def test_starknet_makefile_path(gh):
    app = gh.get_app("app-starknet")
    assert app.makefile_path == Path("./starknet/Cargo.toml")
