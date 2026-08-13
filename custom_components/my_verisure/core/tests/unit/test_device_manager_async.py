"""Tests for asynchronous DeviceManager lifecycle and isolation."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.my_verisure.core.api.device_manager import DeviceManager
from custom_components.my_verisure.core.file_manager import FileManager


@pytest.mark.asyncio
async def test_async_device_identifiers_load_from_entry_scoped_storage(
    tmp_path: Path,
) -> None:
    file_manager = FileManager(tmp_path)
    expected = {"idDevice": "device-1", "uuid": "uuid-1"}
    file_manager.async_load_device_identifiers = AsyncMock(return_value=expected)

    manager = DeviceManager(file_manager=file_manager)
    await manager.async_ensure_device_identifiers()

    assert manager.get_device_identifiers() == expected
    file_manager.async_load_device_identifiers.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_async_device_identifier_generation_is_isolated(
    tmp_path: Path,
) -> None:
    first_file_manager = FileManager(tmp_path / "first")
    second_file_manager = FileManager(tmp_path / "second")
    for file_manager in (first_file_manager, second_file_manager):
        file_manager.async_load_device_identifiers = AsyncMock(return_value=None)
        file_manager.async_save_device_identifiers = AsyncMock(return_value=True)

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
    first_file_manager.async_save_device_identifiers.assert_awaited_once_with(
        {"idDevice": "first"}
    )
    second_file_manager.async_save_device_identifiers.assert_awaited_once_with(
        {"idDevice": "second"}
    )
