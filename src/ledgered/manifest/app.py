from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from ledgered.devices import Devices
from ledgered.serializers import Jsonable, JsonSet


@dataclass
class AppConfig(Jsonable):
    sdk: str
    build_directory: Path
    devices: JsonSet

    def __init__(self, sdk: str, build_directory: str | Path, devices: Iterable[str]) -> None:
        sdk = sdk.lower()
        if sdk not in ["rust", "c"]:
            raise ValueError(f"'{sdk}' unknown. Must be either 'C' or 'Rust'")
        self.sdk = sdk
        self.build_directory = Path(build_directory)
        self.devices = JsonSet(Devices.get_by_name(device).sdk_name for device in devices)

    @property
    def is_rust(self) -> bool:
        return self.sdk == "rust"

    @property
    def is_c(self) -> bool:
        return not self.is_rust
