"""Tests for asynchronous DeviceManager lifecycle and isolation."""

from pathlib import Path
from typing import Any, cast
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.my_verisure.core.api.device_manager import DeviceManager
from custom_components.my_verisure.core.file_manager import FileManager


@pytest.mark.asyncio
async def test_async_device_identifiers_load_from_entry_scoped_storage(
    tmp_path: Path,
) -> None:
    file_manager = FileManager(tmp_path)
    expected = {
        "idDevice": "device-1",
        "uuid": "uuid-1",
        "idDeviceIndigitall": "indigitall-1",
        "deviceName": "name",
        "deviceBrand": "brand",
        "deviceOsVersion": "os",
        "deviceVersion": "version",
        "deviceType": "",
        "deviceResolution": "",
    }

    with patch.object(
        file_manager,
        "async_load_device_identifiers",
        new=AsyncMock(return_value=expected),
    ) as load_mock:
        manager = DeviceManager(file_manager=file_manager)
        await manager.async_ensure_device_identifiers()

    assert manager.get_device_identifiers() == expected
    cast(Any, load_mock).assert_awaited_once_with()


@pytest.mark.asyncio
async def test_partial_persisted_identifiers_are_regenerated(
    tmp_path: Path,
) -> None:
    file_manager = FileManager(tmp_path)
    partial = {"idDevice": "device-1"}

    with (
        patch.object(
            file_manager,
            "async_load_device_identifiers",
            new=AsyncMock(return_value=partial),
        ),
        patch.object(
            file_manager,
            "async_save_device_identifiers",
            new=AsyncMock(return_value=True),
        ) as save_mock,
        patch.object(
            DeviceManager,
            "_generate_device_identifiers",
            return_value={
                "idDevice": "generated",
                "uuid": "uuid",
                "idDeviceIndigitall": "indigitall",
                "deviceName": "name",
                "deviceBrand": "brand",
                "deviceOsVersion": "os",
                "deviceVersion": "version",
                "deviceType": "",
                "deviceResolution": "",
            },
        ),
    ):
        manager = DeviceManager(file_manager=file_manager)
        await manager.async_ensure_device_identifiers()

    assert manager.get_device_identifiers()["idDevice"] == "generated"
    save_mock.assert_awaited_once()
@pytest.mark.asyncio
async def test_async_device_identifier_generation_is_isolated(
    tmp_path: Path,
) -> None:
    first_file_manager = FileManager(tmp_path / "first")
    second_file_manager = FileManager(tmp_path / "second")

    with (
        patch.object(
            first_file_manager,
            "async_load_device_identifiers",
            new=AsyncMock(return_value=None),
        ),
        patch.object(
            first_file_manager,
            "async_save_device_identifiers",
            new=AsyncMock(return_value=True),
        ) as first_save_mock,
        patch.object(
            second_file_manager,
            "async_load_device_identifiers",
            new=AsyncMock(return_value=None),
        ),
        patch.object(
            second_file_manager,
            "async_save_device_identifiers",
            new=AsyncMock(return_value=True),
        ) as second_save_mock,
    ):
        first = DeviceManager(file_manager=first_file_manager)
        second = DeviceManager(file_manager=second_file_manager)

        with patch.object(DeviceManager, "_generate_device_identifiers") as generate:
            generate.side_effect = [
                {"idDevice": "first"},
                {"idDevice": "second"},
            ]
            await first.async_ensure_device_identifiers()
            await second.async_ensure_device_identifiers()

    assert first.get_device_identifiers() == {"idDevice": "first"}
    assert second.get_device_identifiers() == {"idDevice": "second"}
    cast(Any, first_save_mock).assert_awaited_once_with({"idDevice": "first"})
    cast(Any, second_save_mock).assert_awaited_once_with({"idDevice": "second"})
