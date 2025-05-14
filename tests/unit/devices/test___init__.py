from ledgered.devices import Device, DeviceType, Devices, Resolution
from unittest import TestCase


class TestDevice(TestCase):
    def setUp(self):
        self.res = Resolution(x=10, y=20)

    def test___init__simple(self):
        type = DeviceType.NANOS
        device = Device(type, self.res)
        self.assertEqual(device.type, type)
        self.assertEqual(device.touchable, True)
        self.assertFalse(device.deprecated)
        self.assertEqual(device.name, type.name.lower())
        self.assertEqual(device.resolution, self.res)

    def test_is_nano(self):
        device = Device(DeviceType.NANOS, self.res)
        self.assertTrue(device.is_nano)
        device = Device(DeviceType.STAX, self.res)
        self.assertFalse(device.is_nano)

    def test_from_dict(self):
        type, touchable, deprecated = "flex", False, True
        device = Device.from_dict(
            {
                "type": type,
                "resolution": {"x": self.res.x, "y": self.res.y},
                "touchable": touchable,
                "deprecated": deprecated,
            }
        )
        self.assertEqual(device.type, DeviceType[type.upper()])
        self.assertEqual(device.touchable, touchable)
        self.assertEqual(device.deprecated, deprecated)
        self.assertEqual(device.name, type)
        self.assertEqual(device.resolution, Resolution(x=self.res.x, y=self.res.y))


class TestDevices(TestCase):
    def test_get_type_ok(self):
        type = DeviceType.STAX
        device = Devices.get_by_type(type)
        self.assertIsInstance(device, Device)
        self.assertEqual(device.type, type)

    def test_get_type_nok(self):
        with self.assertRaises(KeyError):
            Devices.get_by_type(9)

    def test_get_by_name_ok(self):
        device = Devices.get_by_name("nanos+")
        self.assertIsInstance(device, Device)
        self.assertEqual(device.type, DeviceType.NANOSP)
        self.assertEqual(device.name, "nanosp")
        self.assertEqual(device.sdk_name, "nanos+")

    def test_get_by_name_nok(self):
        with self.assertRaises(KeyError):
            Devices.get_by_name("non existent")

    def test___iter__(self):
        for d in Devices():
            self.assertIsInstance(d, Device)
