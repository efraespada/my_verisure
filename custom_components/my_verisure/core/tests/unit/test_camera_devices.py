"""Tests for camera device selection rules."""

from custom_components.my_verisure.core.application.models.device import Device
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


def test_camera_with_nullable_activity_remains_present_without_remote_access():
    camera = Device("synthetic-id", "3", "Synthetic camera", "YR", None, None, "CAM", None)

    assert camera_devices([camera]) == [camera]
    assert camera.is_active is None
    assert camera.is_remote_accessible is False
