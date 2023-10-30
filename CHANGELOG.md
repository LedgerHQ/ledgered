# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2023-10-30

### Added

- `utils/manifest.py`: RepoManifest now has a `.from_path` method which returns either a `Manifest`
  or a `LegacyManifest`.

### Changed

- `utils/manifest.py`: LegacyManifest now has a `.from_path` method which mimics its initializer
  previous behavior. The initializer signature has changed.

## [0.2.1] - 2023-10-20

### Fixed

- ledger-manifest: typo `test` instead of `tests` was leading to runtime AttributeError.


## [0.2.0] - 2023-10-19

### Changed

- ledger-manifest: devices are output as a list "[...]" rather than a set "{...}" for easier
  reusability.


## [0.1.0] - 2023-10-17

### Added

- 'ledgered' library Python package
- Application 'ledger_app.toml' manifest parser utilitary
