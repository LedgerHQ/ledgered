# Manifest

Ledger embedded application must provide a manifest at the root of the repository, under the form of
a `ledger_app.toml` [TOML](https://toml.io/) file.
This manifest contains application metadata such as build directory, compatible devices and such,
and is used by several tools to know how to build or test the application.

The `ledgered.utils.manifest` library is used to parse and manipulate application manifests
in Python code. `Ledgered` also provides a cli entrypoint (`ledger-manifest`) to parse, extract
and check information from manifests.

## Manifest content

### Example

Example of `ledger_app.toml` manifest from the [boilerplate application](https://github.com/LedgerHQ/app-boilerplate)

```toml
[app]
build_directory = "./"
sdk = "C"
devices = ["nanos", "nanox", "nanos+", "stax"]

[tests]
unit_directory = "./unit-tests/"
pytest_directory = "./tests/"
```

### Sections

#### `[app]`

This section and all its fields are required. It contains metadata helping to build the application.

| Field name        | Description                                                                                            |
|-------------------|--------------------------------------------------------------------------------------------------------|
| `sdk`             | The SDK of the application (currently `C` or `Rust`)                                                   |
| `build_directory` | Path of the build directory (i.e the directory where the `Makefile` or `Cargo.toml` file can be found) |
| `devices`         | The list of devices on which the application can be built.                                             |

#### `[tests]`

This section is optional. It contains metadata used to run application tests.

| Field name         | Description                                                                                    |
|--------------------|------------------------------------------------------------------------------------------------|
| `unit_directory`   | Path of the directory where unit tests can be found                                            |
| `pytest_directory` | Path of the directory where functional, Python test can be found (`conftest.py` file expected) |


### Relations with the [reusable workflows](https://github.com/LedgerHQ/ledger-app-workflows/)

When present, the `ledger_app.toml` manifest is used in the
[Ledger app workflows](https://github.com/LedgerHQ/ledger-app-workflows). It is processed in the
[_get_app_metadata.yml](https://github.com/LedgerHQ/ledger-app-workflows/blob/master/.github/workflows/_get_app_metadata.yml)
workflow, which itself is used in higher-level reusable workflows.

In general, the metadata provided by the manifest will take precedence over workflow inputs, but
there is exceptions. Notably, the `devices` manifest field is overridden by the `run_for_devices`
input of workflows. The rationale is that, even though the application is compatible with a list
of devices, some workflows (the tests for instance) may only run on a subset of these devices.

The impacted workflows and the manifest field / workflow input relations are the following:

#### [`reusable_build.yml`](https://github.com/LedgerHQ/ledger-app-workflows/blob/master/.github/workflows/reusable_build.yml)

| `ledger_app.toml` field | workflow input           | Effect                                                           |
|-------------------------|--------------------------|------------------------------------------------------------------|
| `devices`               | `run_for_devices`        | `devices` is overridden by `run_for_devices`                     |


#### [`reusable_guidelines_enforcer.yml`](https://github.com/LedgerHQ/ledger-app-workflows/blob/master/.github/workflows/reusable_guidelines_enforcer.yml)

| `ledger_app.toml` field | workflow input           | Effect                                                           |
|-------------------------|--------------------------|------------------------------------------------------------------|
| `devices`               | `run_for_devices`        | `devices` is overridden by `run_for_devices`                     |


#### [`reusable_ragger_tests.yml`](https://github.com/LedgerHQ/ledger-app-workflows/blob/master/.github/workflows/reusable_ragger_tests.yml)

| `ledger_app.toml` field | workflow input           | Effect                                                           |
|-------------------------|--------------------------|------------------------------------------------------------------|
| `devices`               | `run_for_devices`        | `devices` is overridden by `run_for_devices`                     |
| `pytest_directory`      | `test_dir`               | `pytest_directory` takes precedence over `test_dir`              |

## `ledger-manifest` utilitary

```sh
$ ledger-manifest --help
usage: ledger-manifest [-h] [-v] [-l] [-c CHECK] [-os] [-ob] [-od] [-ou] [-op] manifest

Utilitary to parse and check an application 'ledger_app.toml' manifest

positional arguments:
  manifest              The manifest file, generally 'ledger_app.toml' at the root of the application's repository

options:
  -h, --help            show this help message and exit
  -v, --verbose
  -l, --legacy          Specifies if the 'ledger_app.toml' file is a legacy one (with 'rust-app' section)
  -c CHECK, --check CHECK
                        Check the manifest content against the provided directory.
  -os, --output-sdk     outputs the SDK type
  -ob, --output-build-directory
                        outputs the build directory (where the Makefile in C app, or the Cargo.toml in Rust app is expected to be)
  -od, --output-devices
                        outputs the list of devices supported by the application
  -ou, --output-unit-directory
                        outputs the directory of the unit tests. Fails if none
  -op, --output-pytest-directory
                        outputs the directory of the pytest (functional) tests. Fails if none
```

## Deprecated `Rust` manifest

Since early 2023, `Rust` applications were already using a `ledger_app.toml` manifest to declare
their build directory.
This manifest had this format:

```toml
[rust-app]
manifest-path = "rust-app/Cargo.toml"
```

This format is now considered legacy and won't be supported soon. It should be changed to the new
manifest format.

In this case, the new manifest should be:

```toml
[app]
sdk = "Rust"
build_directory = "rust-app"
devices = [<the list of devices on which the application is deemed to be built>]
```
