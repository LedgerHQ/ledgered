import dataclasses
import json
from enum import IntEnum, auto
from pathlib import Path
from pydantic.dataclasses import dataclass


class DeviceType(IntEnum):
    NANOS = auto()
    NANOSP = auto()
    NANOX = auto()
    STAX = auto()
    FLEX = auto()


@dataclass
class Resolution:
    x: int
    y: int


@dataclass
class Device:
    type: DeviceType
    resolution: Resolution
    touchable: bool = True
    deprecated: bool = False
    names: list[str] = dataclasses.field(default_factory=lambda: [])

    @property
    def name(self) -> str:
        """
        Returns the name of the current firmware's device
        """
        return self.type.name.lower()

    @property
    def is_nano(self):
        """
        States if the firmware's name starts with 'nano' or not.
        """
        return self.type in [DeviceType.NANOS, DeviceType.NANOSP, DeviceType.NANOX]

    @classmethod
    def from_dict(cls, dico: dict) -> "Device":
        type = dico.pop("type")
        dico["type"] = DeviceType[type.upper()]
        return Device(**dico)


class Devices:
    _devices_file = Path(__file__).absolute().parent / "devices.json"
    with _devices_file.open() as filee:
        _devices = json.load(filee)

    DEVICE_DATA = {item.type: item for item in [Device.from_dict(i) for i in _devices]}

    def __iter__(self):
        for d in self.DEVICE_DATA.values():
            yield d

    @classmethod
    def get_by_type(cls, device_type: DeviceType) -> Device:
        return cls.DEVICE_DATA[device_type]

    @classmethod
    def get_by_name(cls, name: str) -> Device:
        for device in cls.DEVICE_DATA.values():
            if name.lower() == device.name or name.lower() in device.names:
                return device
        raise KeyError(f"Device named '{name}' unknown")
