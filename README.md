# Ledgered

[![codecov](https://codecov.io/gh/LedgerHQ/ledgered/graph/badge.svg?token=0mwgQwrusz)](https://codecov.io/gh/LedgerHQ/ledgered)
[![CodeQL](https://github.com/LedgerHQ/ledgered/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/LedgerHQ/ledgered/actions/workflows/codeql-analysis.yml)

Python libraries and CLI tools for Ledger embedded applications (Nano S+, Nano X, Stax, Flex, ...).

Originally meant to regroup [LedgerComm](https://github.com/LedgerHQ/ledgercomm),
[Ledgerblue](https://github.com/LedgerHQ/blue-loader-python) and
[Ledgerctl](https://github.com/LedgerHQ/ledgerctl), it currently provides:

| Module              | CLI               | Purpose                                                       |
|---------------------|-------------------|---------------------------------------------------------------|
| `ledgered.manifest` | `ledger-manifest` | Parse and check an app `ledger_app.toml` manifest             |
| `ledgered.binary`   | `ledger-binary`   | Extract metadata from a compiled app ELF file                 |
| `ledgered.github`   |                   | List and filter LedgerHQ app repositories, read their content |
| `ledgered.devices`  |                   | Ledger devices reference (names, resolution, ...)             |

```sh
pip install ledgered
```

## Manifest

Every Ledger embedded application provides a `ledger_app.toml` manifest at the root of its repository.
It describes how to build and test the application, and is used by the
[reusable workflows](https://github.com/LedgerHQ/ledger-app-workflows) and the VSCode extension.

### Example

```toml
[app]
build_directory = "./"
sdk = "C"
devices = ["nanox", "nanos+", "stax", "flex"]

[use_cases]
debug = "DEBUG=1"
test_with_feature_activated = "TEST_FLAG_TO_SET=1"

[unit_tests]
directory = "./unit-tests/"

[pytest.standalone]
directory = "tests/"

[pytest.swap]
directory = "tests_swap/"
self_use_case = "test_with_feature_activated"
[pytest.swap.dependencies]
testing_with_latest = [
    {url = "https://github.com/LedgerHQ/app-exchange", ref = "develop", use_case = "dbg_use_test_keys"},
]
testing_with_prod = [
    {url = "https://github.com/LedgerHQ/app-exchange", ref = "master"},
]
```

### Sections

| Section                    | Required | Fields                                                                                                                        |
|----------------------------|----------|-------------------------------------------------------------------------------------------------------------------------------|
| `[app]`                    | yes      | `sdk` (`C` or `Rust`), `build_directory` (where the `Makefile` / `Cargo.toml` is), `devices`                                  |
| `[use_cases]`              | no       | `<use_case> = "<options>"`: make variables for C apps (`DEBUG=1`), Cargo options for Rust apps. `default` is implicit (no option) |
| `[unit_tests]`             | no       | `directory`                                                                                                                   |
| `[pytest.<name>]`          | no       | `directory` (contains a `conftest.py`), `self_use_case` (use case to build the app with for these tests)                      |
| `[pytest.<name>.dependencies]` | no   | `<scenario> = [{url, ref, use_case}, ...]`: apps to sideload for the tests                                                    |

Dependencies notes:
- `use_case` refers to the dependency's own manifest, and defaults to `default`.
- Dependencies are checked out in `<directory>/.dependencies/<repo_name>-<ref>-<use_case>`.

> [!WARNING]
> **Deprecated formats**
> - v1 used a single `[tests]` section (`unit_directory`, `pytest_directory`) with `[tests.dependencies]`
>   instead of `[unit_tests]` and `[pytest.*]`. It is still parsed. `pytest_directory` is mandatory as soon as
>   dependencies are declared.
> - The legacy Rust `[rust-app] manifest-path = "..."` format is no longer supported. Use
>   `[app] sdk = "Rust"` with `build_directory` and `devices` instead.

### Reusable workflows

Manifest values take precedence over workflow inputs, except `devices`, which is overridden by the
`run_for_devices` input (tests may only run on a subset of devices). In
[`reusable_ragger_tests.yml`](https://github.com/LedgerHQ/ledger-app-workflows/blob/master/.github/workflows/reusable_ragger_tests.yml),
`pytest_directory` takes precedence over the `test_dir` input.

### `ledger-manifest`

```sh
ledger-manifest ledger_app.toml -os -od    # outputs the SDK and the devices
ledger-manifest ledger_app.toml -c .       # checks the manifest against the given directory
ledger-manifest app-boilerplate -u -od -j  # fetches the manifest from GitHub, outputs as JSON
```

See `ledger-manifest --help` for all the outputs (build directory, use cases, tests directories and dependencies, ...).

## Binary

Ledger app ELF files embed metadata (target, SDK, API level, ...) used by tools like
[Speculos](https://speculos.ledger.com). `ledger-binary` extracts them:

```sh
$ ledger-binary build/stax/bin/app.elf
api_level 15
app_name Boilerplate
app_version 2.1.0
sdk_graphics bagl
sdk_hash a23bad84cbf39a5071644d2191b177191c089b23
sdk_name ledger-secure-sdk
sdk_version v15.1.0
target stax
target_id 0x33200004
target_name TARGET_STAX
```

Use `-j` for a JSON-like output.

## GitHub

```python
from ledgered.github import Condition, GitHubLedgerHQ

gh = GitHubLedgerHQ(auth=...)  # same arguments as `github.Github`
apps = gh.apps.filter(archived=Condition.WITHOUT, plugin=Condition.WITHOUT, sdk=["rust"])
app = gh.get_app("app-boilerplate")
app.current_branch = "develop"
print(app.manifest.app.devices, app.variant_param, app.variants)
```
