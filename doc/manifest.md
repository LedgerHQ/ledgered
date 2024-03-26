# Manifest

Ledger embedded application must provide a manifest at the root of the repository, under the form of
a `ledger_app.toml` [TOML](https://toml.io/) file.
This manifest contains application metadata such as build directory, compatible devices and such,
and is used by several tools to know how to build or test the application.

The `ledgered.utils.manifest` library is used to parse and manipulate application manifests
in Python code. `Ledgered` also provides a CLI entrypoint (`ledger-manifest`) to parse, extract
and check information from manifests.

## Manifest content

### Example

Example of `ledger_app.toml` manifest from the [boilerplate application](https://github.com/LedgerHQ/app-boilerplate)

```toml
[app]
build_directory = "./"
sdk = "C"
devices = ["nanos", "nanox", "nanos+", "stax"]

[use_cases]
debug = "DEBUG=1"
test = "DEBUG=1"

[tests]
unit_directory = "./unit-tests/"
pytest_directory = "./tests/"

[tests.dependencies]
testing_develop = [
  { url = "https://github.com/<owner>/<app-repository>", ref = "develop", use_case = "debug" },
  { url = "https://github.com/<owner>/<other-app-repository>", ref = "develop" },
]
```

### Sections

#### `[app]`

This section and all its fields are required. It contains metadata helping to build the application.

| Field name        | Description                                                                                            |
|-------------------|--------------------------------------------------------------------------------------------------------|
| `sdk`             | The SDK of the application (currently `C` or `Rust`)                                                   |
| `build_directory` | Path of the build directory (i.e the directory where the `Makefile` or `Cargo.toml` file can be found) |
| `devices`         | The list of devices on which the application can be built.                                             |

#### `[use_cases]`

This section is optional. It contains metadata helping select build options depending on use cases
The VSCode extension leverages this section to provide alternative build targets.

| Field name   | Description                                                             |
|--------------|-------------------------------------------------------------------------|
| `<use_case>` | Options string: <ul><li>Environment variables definitions for C applications (e.g. `DEBUG=1`)</li><li>Valid Cargo build options for Rust applications (e.g. `--outdir mydir`)</li></ul> |

This specifies that in order to build for `<use_case>`, the options string must be provided in the build command line.
You are free to add any use case you wish to have a VSCode build target for.
> [!WARNING]
> The use case `"default"` refers to a standard build with no option. It is implicit and can't be redefined.

Example:
```
[use_cases] # Coherent build options that make sense for your application
debug = "DEBUG=1"
test = "TESTING=1 TEST_PUBLIC_KEY=1"
my_variant = "COIN=MY_VARIANT"
```

#### `[tests]`

This section is optional. It contains metadata used to run application tests.

| Field name         | Description                                                                                    |
|--------------------|------------------------------------------------------------------------------------------------|
| `unit_directory`   | Path of the directory where unit tests can be found                                            |
| `pytest_directory` | Path of the directory where functional, Python test can be found (`conftest.py` file expected) |

#### `[tests.dependencies.<test_use_case>]`

The tests.dependencies.* sections are optional. They contain a list of apps metadata helping building side applications needed for your tests.
You can define as many as you need.
The VSCode extension leverages this field to build test dependencies for Speculos tests or device tests.

The syntax to describe a single side application is the following:

| Field name | Description                                                           |
|------------|-----------------------------------------------------------------------|
| `url`      | The URL of the application git repository  |
| `ref`      | The reference to checkout in the repository |
| `use_case` | The `use_case` to use to build the application |

This is to be included in a list of applications attached to a particular testing scenario, for instance:
```toml
[[tests.dependencies.test_use_case]]
url = <url>
ref = <ref>
use_case = <use_case>
```
This specifies that the `test_use_case` scenario needs the application located at `<url>` on ref `<ref>` and should be built according to its `<use_case>`.

This following syntax can be used, as it is lighter and equivalent to the previous one:
```toml
[tests.dependencies]
test_use_case = [{url = <url>, ref = <ref>, use_case = <use_case>}]
```

> [!NOTE]
> The `<use_case>` is the one of the application referred to, not to this manifest's application. Hence it must be defined on the other application own manifest (or be `"default"`)

> [!NOTE]
> The `<use_case>` is optional, and will fallback to `use_case = "default"` if non present.

Example for an Ethereum plugin that needs the Ethereum application sideloaded on the device:
```toml
[tests.dependencies] # Set of applications to load on the device (or Speculos) for a given test suite

testing_with_prod = [
  {url = "https://github.com/LedgerHQ/app-ethereum", ref = "master", use_case = "cal_key_debug"},
]

testing_with_latest = [
  {url = "https://github.com/LedgerHQ/app-ethereum", ref = "develop", use_case = "cal_key_debug"},
]

```

> [!WARNING]
> As soon as a single `[[tests.dependencies]]` is defined, the `[tests] pytest_directory` field becomes mandatory.
> This field will be used in order for ledgered to generate a deterministic path for every dependency.
> Currently, this path is `<pytest_directory>/.dependencies/<repo_name>-<ref>-<use_case>`.


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
usage: ledger-manifest [-h] [-v] [-l] [-c CHECK] [-os] [-ob] [-od] [-otu] [-otp] [-otd [OUTPUT_TESTS_DEPENDENCIES ...]] [-ouc [OUTPUT_USE_CASES ...]] [-j] manifest

Utilitary to parse and check an application 'ledger_app.toml' manifest

positional arguments:
  manifest              The manifest file, generally 'ledger_app.toml' at the root of the application's repository

options:
  -h, --help            show this help message and exit
  -v, --verbose
  -c CHECK, --check CHECK
                        Check the manifest content against the provided directory.
  -os, --output-sdk     outputs the SDK type
  -ob, --output-build-directory
                        outputs the build directory (where the Makefile in C app, or the Cargo.toml in Rust app is expected to be)
  -od, --output-devices
                        outputs the list of devices supported by the application
  -otu, --output-tests-unit-directory
                        outputs the directory of the unit tests. Fails if none
  -otp, --output-tests-pytest-directory
                        outputs the directory of the pytest (functional) tests. Fails if none
  -otd [OUTPUT_TESTS_DEPENDENCIES ...], --output-tests-dependencies [OUTPUT_TESTS_DEPENDENCIES ...]
                        outputs the given use cases. Fails if none
  -ouc [OUTPUT_USE_CASES ...], --output-use-cases [OUTPUT_USE_CASES ...]
                        outputs the given use cases. Fails if none
  -j, --json            outputs as JSON rather than text
```

## Deprecated `Rust` manifest

Since early 2023, `Rust` applications were already using a `ledger_app.toml` manifest to declare
their build directory.
This manifest had this format:

```toml
[rust-app]
manifest-path = "rust-app/Cargo.toml"
```

This format is considered legacy since October 2023 and is no longer supported since February 2024.
It should be changed to fit the new manifest format.

In this case, the new manifest should be:

```toml
[app]
sdk = "Rust"
build_directory = "rust-app"
devices = [<the list of devices on which the application is deemed to be built>]
```
