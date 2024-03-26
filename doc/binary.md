# Binary parser

Ledger embedded application ELF file contains metadata injected during the compilation. These
information are used by tools like [Speculos](https://speculos.ledger.com) to ease the manipulation
of the binaries (for instance: no need to explicit the device type, the SDK version, etc.).

For easier integration in Python code, `Ledgered` integrates a small binary parser to extract these
data. This code is the `ledgered.binary` library, and `Ledgered` also provides a CLI entrypoint
(`ledger-binary`).

## `ledger-binary` utilitary

### Example

Let's suppose we're compiling of the [Boilerplate application](https://github.com/LedgerHQ/app-boilerplate)
for Stax:

```bash
bash-5.1# make -j BOLOS_SDK=$STAX_SDK
```

The resulting ELF file is stored at (relative path) `./build/stax/bin/app.elf`. Let's use
`ledger-binary` to inspect this file:

```bash
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

It is also possible to ask for a JSON-like output:

```bash
$ ledger-binary build/stax/bin/app.elf -j
{'api_level': '15', 'app_name': 'Boilerplate', 'app_version': '2.1.0', 'sdk_graphics': 'bagl', 'sdk_hash': 'a23bad84cbf39a5071644d2191b177191c089b23', 'sdk_name': 'ledger-secure-sdk', 'sdk_version': 'v15.1.0', 'target': 'stax', 'target_id': '0x33200004', 'target_name': 'TARGET_STAX'}
```
