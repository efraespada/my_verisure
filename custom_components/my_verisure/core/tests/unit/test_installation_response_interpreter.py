"""Tests for installation response interpretation."""

import pytest

from custom_components.my_verisure.core.application.installation_response_interpreter import (
    InstallationResponseError,
    interpret_devices,
    interpret_installations,
    interpret_services,
)


def test_interprets_installations() -> None:
    assert interpret_installations(
        {"data": {"xSInstallations": {"installations": [{"numinst": "1"}]}}}
    ) == [{"numinst": "1"}]


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


@pytest.mark.parametrize("interpreter", [interpret_installations, interpret_services, interpret_devices])
def test_rejects_graphql_errors(interpreter) -> None:
    with pytest.raises(InstallationResponseError, match="provider failed"):
        interpreter({"errors": [{"message": "provider failed"}]})


@pytest.mark.parametrize("interpreter", [interpret_installations, interpret_services, interpret_devices])
def test_rejects_missing_response(interpreter) -> None:
    with pytest.raises(InstallationResponseError):
        interpreter({"data": {}})
