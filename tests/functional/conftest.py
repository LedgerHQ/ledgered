import pytest
from github.Auth import Token

from ledgered.github import GitHubLedgerHQ


def pytest_addoption(parser):
    parser.addoption(
        "--token",
        required=False,
        default=None,
        help="Provide a GitHub token so that functional test won't trigger API restrictions too fast",
    )


@pytest.fixture(scope="session")
def token(pytestconfig) -> Token | None:
    token = pytestconfig.getoption("token")
    return None if token is None else Token(token)


@pytest.fixture(scope="session")
def gh(token: Token):
    return GitHubLedgerHQ() if token is None else GitHubLedgerHQ(auth=token)


@pytest.fixture(scope="session")
def exchange(gh):
    return gh.get_app("app-exchange")
