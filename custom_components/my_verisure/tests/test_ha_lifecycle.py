"""Real Home Assistant lifecycle tests for the My Verisure integration."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.my_verisure.core.const import DOMAIN
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.api.exceptions import (
    MyVerisureConnectionError,
)
from custom_components.my_verisure.core.application.models.auth import AuthResult
from custom_components.my_verisure.core.application.models.camera_refresh import CameraRefresh
from custom_components.my_verisure.core.application.models.camera_refresh_data import CameraRefreshData
from custom_components.my_verisure.core.use_cases.interfaces.auth_use_case import AuthUseCase
from custom_components.my_verisure.core.use_cases.interfaces.installation_use_case import InstallationUseCase
from custom_components.my_verisure.core.use_cases.interfaces.create_dummy_camera_images_use_case import CreateDummyCameraImagesUseCase


class _FakeAuthUseCase:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error

    async def login(self, username, password):
        if self.error:
            raise self.error
        return self.result

    def get_available_phones(self):
        return []

    def select_phone(self, phone_id):
        return False

    async def send_otp(self, record_id, otp_hash=None):
        return False

    async def verify_otp(self, otp_code):
        return AuthResult(False, "invalid")

    def invalidate_otp_challenge(self):
        return None


class _FakeInstallationUseCase:
    def __init__(self, installations):
        self.installations = installations

    async def get_installations(self):
        return self.installations


class _FakeDummyCameraUseCase:
    def __init__(self, result=None):
        self.result = result or CameraRefresh.create(
            [
                CameraRefreshData.create(
                    timestamp="2026-08-13T12:00:00",
                    num_images=1,
                    camera_identifier="camera",
                )
            ]
        )

    async def create_dummy_camera_images(self, installation_id):
        return self.result


class _FakeRoot:
    def __init__(self, auth, installations):
        session = SimpleNamespace(
            update_credentials=Mock(),
            async_clear_session_file=AsyncMock(return_value=True),
            async_clear_credentials=AsyncMock(return_value=True),
            async_session_file_exists=AsyncMock(return_value=False),
            async_load_session_from_disk=AsyncMock(),
            async_capture_transaction_state=AsyncMock(return_value=({}, None)),
            async_restore_transaction_state=AsyncMock(),
            is_authenticated=bool(
                getattr(getattr(auth, "result", None), "success", False)
            ),
            get_current_hash_token=lambda: "valid-session"
            if session.is_authenticated
            else None,
            username="[REDACTED]",
        )
        session.is_session_valid = lambda: session.is_authenticated
        file_manager = SimpleNamespace(
            async_cleanup_project_root=AsyncMock(),
            async_device_identifiers_exists=AsyncMock(return_value=False),
        )
        self.values = {
            AuthUseCase: auth,
            InstallationUseCase: _FakeInstallationUseCase(installations),
            CreateDummyCameraImagesUseCase: _FakeDummyCameraUseCase(),
            FileManager: file_manager,
            "session": session,
        }

    def get(self, dependency):
        if dependency.__name__ == "SessionManager":
            return self.values["session"]
        return self.values[dependency]


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_config_flow_starts_with_user_form(hass, enable_custom_integrations):
    """The real HA config-entry manager exposes the initial user form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_config_flow_reports_invalid_auth_from_application_port(
    hass, enable_custom_integrations
):
    """Authentication failures become the HA config-flow error contract."""
    root = _FakeRoot(_FakeAuthUseCase(AuthResult(False, "invalid")), [])
    with patch(
        "custom_components.my_verisure.config_flow.build_my_verisure_composition_root",
        return_value=root,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"user": "[REDACTED]", "password": "[REDACTED]"},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_auth"}


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_config_flow_maps_connection_failure(
    hass, enable_custom_integrations
):
    """Connection failures become an actionable cannot_connect error."""
    root = _FakeRoot(
        _FakeAuthUseCase(error=MyVerisureConnectionError("offline")), []
    )
    with patch(
        "custom_components.my_verisure.config_flow.build_my_verisure_composition_root",
        return_value=root,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"user": "[REDACTED]", "password": "[REDACTED]"},
        )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "cannot_connect"}


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_config_flow_creates_entry_after_installation_selection(
    hass, enable_custom_integrations
):
    """A valid application result creates a real HA config entry."""
    installation = SimpleNamespace(
        numinst="123", alias="Home", type="alarm"
    )
    root = _FakeRoot(_FakeAuthUseCase(AuthResult(True, "ok")), [installation])
    with patch(
        "custom_components.my_verisure.config_flow.build_my_verisure_composition_root",
        return_value=root,
    ), patch(
        "custom_components.my_verisure.async_setup_entry",
        new=AsyncMock(return_value=True),
    ), patch(
        "custom_components.my_verisure.integration.async_setup_entry",
        new=AsyncMock(return_value=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"user": "[REDACTED]", "password": "[REDACTED]"},
        )
        assert result["step_id"] == "installation"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"installation_id": "123"}
        )

    assert result["type"] == "create_entry"
    assert result["data"]["installation_id"] == "123"
    assert result["data"]["password"] == "[REDACTED]"
    root.values[FileManager].async_cleanup_project_root.assert_awaited_once()


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_config_flow_rejects_incomplete_initial_camera_persistence(
    hass, enable_custom_integrations
):
    """Initial setup must not create an entry after a partial camera refresh."""
    installation = SimpleNamespace(numinst="123", alias="Home", type="alarm")
    failed_refresh = CameraRefresh.create(
        [
            CameraRefreshData.create(
                timestamp="2026-08-13T12:00:00",
                num_images=0,
                camera_identifier="camera",
            )
        ]
    )
    root = _FakeRoot(_FakeAuthUseCase(AuthResult(True, "ok")), [installation])
    root.values[CreateDummyCameraImagesUseCase] = _FakeDummyCameraUseCase(
        failed_refresh
    )

    with patch(
        "custom_components.my_verisure.config_flow.build_my_verisure_composition_root",
        return_value=root,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"user": "[REDACTED]", "password": "[REDACTED]"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"installation_id": "123"}
        )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {}
    root.values[FileManager].async_cleanup_project_root.assert_awaited_once()


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_config_entry_setup_and_unload_are_isolated(
    hass, enable_custom_integrations
):
    """A config entry can be set up and unloaded through HA's real manager."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test My Verisure",
        data={
            "installation_id": "123",
            "user": "[REDACTED]",
            "password": "not-a-real-password",
        },
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.my_verisure.coordinator.MyVerisureDataUpdateCoordinator.async_load_session",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "custom_components.my_verisure.coordinator.MyVerisureDataUpdateCoordinator.async_config_entry_first_refresh",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "custom_components.my_verisure.coordinator.MyVerisureDataUpdateCoordinator.get_session_hash",
            return_value=None,
        ),
        patch(
            "custom_components.my_verisure.coordinator.MyVerisureDataUpdateCoordinator.load_alarm_info",
            return_value=None,
        ),
        patch(
            "custom_components.my_verisure.coordinator.MyVerisureDataUpdateCoordinator.has_valid_session",
            return_value=False,
        ),
        patch(
            "custom_components.my_verisure.device.async_setup_device",
            new=AsyncMock(return_value=None),
        ),
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            new=AsyncMock(return_value=None),
        ),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        assert entry.state.name == "LOADED"
        assert entry.runtime_data is not None
        assert DOMAIN in hass.data
        assert await hass.config_entries.async_unload(entry.entry_id)
        assert entry.state.name == "NOT_LOADED"
        assert DOMAIN not in hass.data


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_two_config_entries_keep_runtime_data_separate(
    hass, enable_custom_integrations
):
    """Two HA entries receive distinct coordinators and composition roots."""
    entries = [
        MockConfigEntry(
            domain=DOMAIN,
            title=f"Test My Verisure {index}",
            entry_id=f"entry-{index}",
            data={
                "installation_id": str(index),
                "user": f"USER_{index}_SENTINEL",
                "password": "not-a-real-password",
            },
        )
        for index in (1, 2)
    ]
    for entry in entries:
        entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.my_verisure.coordinator.MyVerisureDataUpdateCoordinator.async_load_session",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "custom_components.my_verisure.coordinator.MyVerisureDataUpdateCoordinator.async_config_entry_first_refresh",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "custom_components.my_verisure.coordinator.MyVerisureDataUpdateCoordinator.get_session_hash",
            return_value=None,
        ),
        patch(
            "custom_components.my_verisure.coordinator.MyVerisureDataUpdateCoordinator.load_alarm_info",
            return_value=None,
        ),
        patch(
            "custom_components.my_verisure.coordinator.MyVerisureDataUpdateCoordinator.has_valid_session",
            return_value=False,
        ),
        patch(
            "custom_components.my_verisure.device.async_setup_device",
            new=AsyncMock(return_value=None),
        ),
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            new=AsyncMock(return_value=None),
        ),
    ):
        assert await hass.config_entries.async_setup(entries[0].entry_id)
        assert entries[0].state.name == "LOADED"
        assert entries[1].state.name == "LOADED"
        assert entries[0].runtime_data is not entries[1].runtime_data
        assert (
            entries[0].runtime_data.composition_root
            is not entries[1].runtime_data.composition_root
        )
        first_runtime = entries[0].runtime_data
        second_runtime = entries[1].runtime_data
        assert first_runtime.installation_id == "1"
        assert second_runtime.installation_id == "2"
        assert first_runtime.session_manager is not second_runtime.session_manager
        assert first_runtime.file_manager is not second_runtime.file_manager
        assert first_runtime.session_file != second_runtime.session_file
        assert Path(first_runtime.session_file).name == "session.json"
        assert Path(second_runtime.session_file).name == "session.json"
        assert Path(first_runtime.session_file).parent.name == "data"
        assert Path(second_runtime.session_file).parent.name == "data"
        assert "USER_" not in str(first_runtime.session_file)
        assert "USER_" not in str(second_runtime.session_file)
        assert first_runtime.file_manager.get_project_root() != (
            second_runtime.file_manager.get_project_root()
        )
        assert first_runtime.session_manager.username == "USER_1_SENTINEL"
        assert second_runtime.session_manager.username == "USER_2_SENTINEL"
        assert first_runtime.session_manager is not second_runtime.session_manager

        assert await hass.config_entries.async_unload(entries[0].entry_id)
        assert entries[1].state.name == "LOADED"
        assert await hass.config_entries.async_unload(entries[1].entry_id)
