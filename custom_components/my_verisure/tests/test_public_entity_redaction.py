"""Public Home Assistant entity attributes must not expose private identifiers."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from custom_components.my_verisure.alarm_control_panel import (
    MyVerisureAlarmControlPanel,
)
from custom_components.my_verisure.camera import VerisureCamera
from custom_components.my_verisure.device import get_device_info


def test_camera_attributes_exclude_device_code_and_private_image_path():
    config_entry = SimpleNamespace(
        entry_id="entry-1", data={"installation_id": "[REDACTED]"}
    )
    camera = VerisureCamera(
        MagicMock(),
        {"type": "YP", "code": "7", "name": "Camera"},
        config_entry,
    )
    camera._latest_image_path = "/private/cameras/YP07/image.jpg"

    attributes = camera.extra_state_attributes

    assert camera.name == "Verisure Camera"
    assert "7" not in camera.unique_id
    assert "device_name" not in camera.extra_state_attributes
    assert "latest_image_path" not in camera.extra_state_attributes


def test_alarm_attributes_omit_missing_installation_defaults():
    entry = SimpleNamespace(entry_id="entry-1", data={})
    coordinator = MagicMock(
        data={"alarm_status": {}, "detailed_installation": {}}
    )
    entity = MyVerisureAlarmControlPanel(coordinator, entry)

    assert "installation_status" not in entity.extra_state_attributes
    assert "installation_role" not in entity.extra_state_attributes


def test_device_info_does_not_expose_installation_id_in_public_name():
    config_entry = SimpleNamespace(
        entry_id="entry-1", data={"installation_id": "[REDACTED]"}
    )

    device_info = get_device_info(config_entry)

    assert device_info["name"] == "My Verisure Alarm"
    assert "installation-secret" not in device_info["name"]
