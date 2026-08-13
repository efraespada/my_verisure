"""Tests for camera request policy."""

from datetime import datetime

from custom_components.my_verisure.core.application.camera_request_policy import (
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

    assert context.variables == {"numinst": "home-1", "panel": "panel", "devices": [1, 2]}
    assert context.headers == {
        "Authorization": "hash",
        "numinst": "home-1",
        "panel": "panel",
        "x-capabilities": "caps",
    }


def test_image_directory_normalizes_timestamp_and_has_deterministic_fallback():
    policy = CameraRequestPolicy()

    assert policy.image_directory("2026/08/13 12:30:00") == "2026-08-13_12-30-00"
    assert policy.image_directory("", datetime(2026, 8, 13, 12, 30, 0)) == "2026-08-13_12-30-00"
