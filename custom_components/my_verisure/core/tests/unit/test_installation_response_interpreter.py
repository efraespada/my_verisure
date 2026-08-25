"""Tests for installation response interpretation."""

import pytest

from custom_components.my_verisure.core.api.installation_response_interpreter import (
    InstallationResponseError,
    interpret_devices,
    interpret_installations,
    interpret_services,
)


def test_interprets_installations() -> None:
    assert interpret_installations(
        {"data": {"xSInstallations": {"installations": [{"numinst": "1"}]}}}
    ) == [{"numinst": "1"}]




def test_rejects_non_mapping_installation_records() -> None:
    with pytest.raises(InstallationResponseError, match="Invalid installations data"):
        interpret_installations(
            {"data": {"xSInstallations": {"installations": [None]}}}
        )


def test_interprets_services() -> None:
    assert interpret_services(
        {
            "data": {
                "xSSrv": {
                    "res": "OK",
                    "language": "ES",
                    "installation": {"numinst": "1"},
                }
            }
        }
    ) == {"installation": {"numinst": "1"}, "language": "ES"}


def test_interprets_devices() -> None:
    assert interpret_devices(
        {"data": {"xSDeviceList": {"res": "OK", "devices": [{"id": 1}]}}}
    ) == [{"id": 1}]


def test_rejects_non_mapping_device_records() -> None:
    with pytest.raises(InstallationResponseError, match="Invalid devices data"):
        interpret_devices(
            {"data": {"xSDeviceList": {"res": "OK", "devices": [None]}}}
        )


@pytest.mark.parametrize("interpreter", [interpret_installations, interpret_services, interpret_devices])
def test_rejects_graphql_errors(interpreter) -> None:
    with pytest.raises(InstallationResponseError, match="service request failed"):
        interpreter({"errors": [{"message": "provider failed"}]})


@pytest.mark.parametrize("interpreter", [interpret_installations, interpret_services, interpret_devices])
def test_rejects_empty_graphql_errors(interpreter) -> None:
    with pytest.raises(InstallationResponseError, match="service request failed"):
        interpreter({"errors": []})


@pytest.mark.parametrize("interpreter", [interpret_installations, interpret_services, interpret_devices])
def test_rejects_missing_response(interpreter) -> None:
    with pytest.raises(InstallationResponseError):
        interpreter({"data": {}})
