"""Tests for camera device selection rules."""

from custom_components.my_verisure.core.api.models.domain.device import Device
from custom_components.my_verisure.core.application.camera_devices import (
    camera_devices,
    camera_identifier,
)


def _device(device_type: str, code: str, active: bool = True) -> Device:
    return Device("id", code, "camera", device_type, "", True, "CAM", active)


def test_camera_devices_selects_active_supported_types_in_order():
    devices = [
        _device("PIR", "1"),
        _device("YR", "2"),
        _device("YP", "3", active=False),
        _device("YP", "4"),
    ]

    selected = camera_devices(devices)

    assert [device.code for device in selected] == ["2", "4"]


def test_camera_identifier_zero_pads_numeric_code():
    assert camera_identifier(_device("YR", "3")) == "YR03"
