"""Validate documented configurations and render their time-sensitive behavior.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from datetime import timedelta
from pathlib import Path
import re

from homeassistant.components.automation.config import (
    AUTOMATION_BLUEPRINT_SCHEMA, PLATFORM_SCHEMA,
)
from homeassistant.components.blueprint.models import Blueprint, BlueprintInputs
from homeassistant.components.script.config import SCRIPT_ENTITY_SCHEMA
from homeassistant.components.template.config import CONFIG_SECTION_SCHEMA
from homeassistant.helpers.template import Template
from homeassistant.util import dt as dt_util
from homeassistant.util.yaml import load_yaml
import pytest
import yaml

from custom_components.my_verisure import services as integration_services

pytestmark = pytest.mark.usefixtures("hass")

ROOT = Path(__file__).resolve().parents[3]
AUTOMATIONS = sorted((ROOT / "docs/examples/automations").glob("*.yaml"))
SCRIPTS = sorted((ROOT / "docs/examples/scripts").glob("*.yaml"))
TEMPLATES = sorted((ROOT / "docs/examples/templates").glob("*.yaml"))


@pytest.mark.parametrize("path", AUTOMATIONS, ids=lambda path: path.name)
async def test_automation_examples_use_valid_ha_schemas(path):
    config = PLATFORM_SCHEMA(load_yaml(str(path)))
    assert config["triggers"] and config["actions"]


@pytest.mark.parametrize("path", SCRIPTS, ids=lambda path: path.name)
async def test_script_examples_use_valid_ha_schemas(path):
    config = SCRIPT_ENTITY_SCHEMA(load_yaml(str(path)))
    assert config["sequence"]


@pytest.mark.parametrize("path", TEMPLATES, ids=lambda path: path.name)
async def test_template_examples_use_valid_ha_schemas(path):
    config = load_yaml(str(path))
    assert CONFIG_SECTION_SCHEMA(config["template"][0])


async def test_notification_blueprint_expands_to_valid_automation():
    path = ROOT / "blueprints/automation/my_verisure/notification_light.yaml"
    blueprint = Blueprint(
        load_yaml(str(path)), expected_domain="automation",
        schema=AUTOMATION_BLUEPRINT_SCHEMA,
    )
    inputs = BlueprintInputs(
        blueprint,
        {"use_blueprint": {"path": "my_verisure/notification_light.yaml", "input": {
            "result_event": "event.synthetic_confirmed",
            "light_target": {"entity_id": "light.synthetic"},
        }}},
    )
    inputs.validate()
    config = PLATFORM_SCHEMA(inputs.async_substitute())
    assert config["triggers"][0]["options"]["event_type"] == ["photo_ready"]
    assert config["actions"][0]["action"] == "light.turn_on"
    assert blueprint.validate() is None


async def test_notification_guide_yaml_examples_use_valid_ha_schemas():
    source = (ROOT / "docs/automation-notifications.md").read_text()
    blocks = re.findall(r"```yaml\n(.*?)\n```", source, re.S)
    assert len(blocks) >= 2
    configs = [PLATFORM_SCHEMA(yaml.safe_load(block)) for block in blocks]
    assert configs[0]["triggers"][0]["platform"] == "event.received"
    assert configs[1]["triggers"][0]["event_type"] == "my_verisure_event"


@pytest.mark.parametrize("state", ["unknown", "unavailable", None, "malformed"])
async def test_last_update_age_handles_missing_or_invalid_source(hass, state):
    source = "sensor.my_verisure_last_updated"
    if state is not None:
        hass.states.async_set(source, state)
    config = load_yaml(str(ROOT / "docs/examples/templates/numeric-last-update.yaml"))
    sensor = config["template"][0]["sensor"][0]
    assert Template(sensor["availability"], hass).async_render() is False
    assert Template(sensor["state"], hass).async_render() is None


async def test_age_uses_source_timestamp_instead_of_the_new_ha_state_time(hass):
    """Restoring an old timestamp must not make stale data appear fresh."""
    old = dt_util.utcnow() - timedelta(hours=3)
    hass.states.async_set("sensor.my_verisure_last_updated", old.isoformat())
    config = load_yaml(str(ROOT / "docs/examples/templates/numeric-last-update.yaml"))
    sensor = config["template"][0]["sensor"][0]
    assert Template(sensor["availability"], hass).async_render() is True
    assert Template(sensor["state"], hass).async_render() >= 10800
    watch = load_yaml(str(
        ROOT / "docs/examples/automations/coordinator-stale-watch.yaml"
    ))
    rendered = Template(watch["condition"][0]["value_template"], hass).async_render()
    assert rendered is True


async def test_last_update_age_is_never_negative_for_a_future_timestamp(hass):
    future = dt_util.utcnow() + timedelta(minutes=1)
    hass.states.async_set("sensor.my_verisure_last_updated", future.isoformat())
    config = load_yaml(str(ROOT / "docs/examples/templates/numeric-last-update.yaml"))
    sensor = config["template"][0]["sensor"][0]
    assert Template(sensor["state"], hass).async_render() == 0


async def test_mode_sync_does_not_disarm_for_unknown_helper_values(hass):
    """The example must require an explicit mode, including disarm."""
    from homeassistant.helpers.condition import async_from_config

    config = PLATFORM_SCHEMA(load_yaml(
        str(ROOT / "docs/examples/automations/mode-arm-sync.yaml")
    ))
    action = config["actions"][0]
    for value in ("unknown", "unavailable", "unexpected"):
        hass.states.async_set("input_select.home_security_mode", value)
        for choice in action["choose"]:
            for condition in choice["conditions"]:
                check = await async_from_config(hass, condition)
                assert check(hass) is False
    assert not action.get("default")


async def test_service_descriptions_only_advertise_supported_fields():
    metadata = load_yaml(str(
        ROOT / "custom_components/my_verisure/services.yaml"
    ))
    for name, description in metadata.items():
        schema = getattr(integration_services, f"SERVICE_{name.upper()}_SCHEMA")
        assert "target" not in description
        fields = description["fields"]
        assert set(fields) == {marker.schema for marker in schema.schema}
        values = {field: "camera.synthetic" if field == "camera_entity_id"
                  else "synthetic-installation" for field in fields}
        assert schema(values) == values
