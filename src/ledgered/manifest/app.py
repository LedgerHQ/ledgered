from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Union

from ledgered.serializers import Jsonable, JsonSet
from .constants import EXISTING_DEVICES


@dataclass
class AppConfig(Jsonable):
    sdk: str
    build_directory: Path
    devices: JsonSet

    def __init__(self, sdk: str, build_directory: Union[str, Path], devices: Iterable[str]) -> None:
        sdk = sdk.lower()
        if sdk not in ["rust", "c"]:
            raise ValueError(f"'{sdk}' unknown. Must be either 'C' or 'Rust'")
        self.sdk = sdk
        self.build_directory = Path(build_directory)
        devices = JsonSet(device.lower() for device in devices)
        unknown_devices = devices.difference(EXISTING_DEVICES)
        if unknown_devices:
            unknown_devices_str = "', '".join(unknown_devices)
            raise ValueError(f"Unknown devices: '{unknown_devices_str}'")
        self.devices = devices

    @property
    def is_rust(self) -> bool:
        return self.sdk == "rust"

    @property
    def is_c(self) -> bool:
        return not self.is_rust
