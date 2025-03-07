# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0] - 2025-03-??

### Added

- `ledger-manifest`: new `--token` argument, allowing to provide a PAT to evade GitHub API
  limitations when parsing remote manifest (with the `--url` argument).

## [0.8.0] - 2025-03-06

### Added

- `ledger-manifest`: new `--url` argument allows to parse manifest from an application GH repository
  rather than a local file.

### Changed

- Package tested & published on Python3.12 and 3.13. Python 3.8 support is dropped.


## [0.7.1] - 2024-04-30

### Fixed

- Clean error management when there is not `ledger_app.toml` manifest to access to on a given
  repository/branch.


## [0.7.0] - 2024-04-12

### Added

- Added wrapper around GitHub API to ease manipulating Ledger application repositories.


## [0.6.3] - 2024-03-26

### Fixed

- `ledger-binary`: NanoS SDK has a unique `target_version` section.


## [0.6.2] - 2024-03-26

### Fixed

- `ledger-binary`: Striping occasional trailing newlines in metadata content.


## [0.6.1] - 2024-03-26

### Fixed

- `ledger-binary`: Adding Rust application specific metadata sections.


## [0.6.0] - 2024-03-26

### Added

- `ledger-binary`: Adding an utilitary to parse embedded application ELF file metadatas.

### Changed

- Renamed 'Europa' with official product name 'Flex'


## [0.5.0] - 2024-03-11

### Added

- `ledger-manifest`: "Europa" is now a valid `app.devices` value.

### Removed

- BREAKING: removing references to `LegacyManifest` and `RepoManifest`. Only `Manifest` is to be
  used from now on.


## [0.4.1] - 2024-02-22

### Fixed

- Fix handling of None value of tests.pytest_directory and tests.unit_directory


## [0.4.0] - 2024-02-22

### Added

- Dedicated logger for the `manifest` subpackage.
- `manifest` can now manage `use_cases` and `tests.dependencies`
- outputs can be JSONified

### Changed

- BREAKING: moving the `utils/manifest.py` module into its own `manifest/` subpackage.


## [0.3.0] - 2023-10-30

### Added

- `utils/manifest.py`: RepoManifest now has a `.from_path` method which returns either a `Manifest`
  or a `LegacyManifest`.

### Changed

- `utils/manifest.py`: LegacyManifest now has a `.from_path` method which mimics its initializer
  previous behavior. The initializer signature has changed.


## [0.2.1] - 2023-10-20

### Fixed

- `ledger-manifest`: typo `test` instead of `tests` was leading to runtime AttributeError.


## [0.2.0] - 2023-10-19

### Changed

- `ledger-manifest`: devices are output as a list "[...]" rather than a set "{...}" for easier
  reusability.


## [0.1.0] - 2023-10-17

### Added

- `ledgered` library Python package
- Application 'ledger_app.toml' manifest parser utilitary
