"""Tests for camera request policy."""

from datetime import datetime

import pytest

from custom_components.my_verisure.core.api.camera_request_policy import (
    CameraRequestPolicy,
)


def test_build_context_adds_entry_specific_headers_and_variables():
    policy = CameraRequestPolicy()

    context = policy.build_context(
        installation_id="home-1",
        panel="panel",
        devices=[1, 2],
        capabilities="caps",
        session_data={"user": "user"},
        hash_token="hash",
        header_factory=lambda data, token: {"Authorization": token or ""},
    )

    assert context.variables == {
        "numinst": "home-1",
        "panel": "panel",
        "devices": [1, 2],
    }
    assert context.headers == {
        "Authorization": "hash",
        "numinst": "home-1",
        "panel": "panel",
        "x-capabilities": "caps",
    }


def test_build_context_requires_authenticated_session():
    policy = CameraRequestPolicy()

    with pytest.raises(ValueError, match="authenticated session required"):
        policy.build_context(
            installation_id="home-1",
            panel="panel",
            devices=[1],
            capabilities="caps",
            session_data=None,
            hash_token=None,
            header_factory=lambda data, token: {"Authorization": token or ""},
        )


@pytest.mark.parametrize(
    ("installation_id", "panel", "devices", "capabilities"),
    [
        ("", "panel", [1], "caps"),
        ("home-1", "", [1], "caps"),
        ("home-1", "panel", [], "caps"),
        ("home-1", "panel", [1], ""),
        ("home-1", " ", [1], "caps"),
    ],
)
def test_build_context_rejects_incomplete_installation_context(
    installation_id, panel, devices, capabilities
):
    with pytest.raises(ValueError, match="camera request context required"):
        CameraRequestPolicy().build_context(
            installation_id=installation_id,
            panel=panel,
            devices=devices,
            capabilities=capabilities,
            session_data={"user": "user"},
            hash_token="hash",
            header_factory=lambda data, token: {"Authorization": token or ""},
        )


def test_image_directory_normalizes_timestamp_and_has_deterministic_fallback():
    policy = CameraRequestPolicy()

    assert policy.image_directory("2026/08/13 12:30:00") == "2026-08-13_12-30-00"
    with pytest.raises(ValueError, match="camera timestamp required"):
        policy.image_directory("", datetime(2026, 8, 13, 12, 30, 0))
