"""Contract tests for installation and device DTO adapters."""

from custom_components.my_verisure.core.api.mappers.device_mapper import (
    device_list_from_dto,
    device_list_to_dto,
    device_to_dto,
)
from custom_components.my_verisure.core.api.mappers.installation_mapper import (
    detailed_installation_from_dto,
    detailed_installation_to_dto,
    installation_from_dto,
    installation_to_dto,
)
from custom_components.my_verisure.core.api.models.dto.device_dto import (
    DeviceDTO,
    DeviceListDTO,
)
from custom_components.my_verisure.core.api.models.dto.installation_dto import (
    DetailedInstallationDTO,
    InstallationDTO,
    InstallationDataDTO,
    ServiceDTO,
)


def test_installation_mapping_round_trip() -> None:
    dto = InstallationDTO(
        "123", "alias", "panel", "type", "Name", "Surname", "Address",
        "City", "00000", "Province", "mail@example.invalid", "000",
    )
    value = installation_from_dto(dto)
    assert installation_to_dto(value) == dto


def test_device_list_mapping_round_trip() -> None:
    device = DeviceDTO("id", "code", "Camera", "CAMERA", "IP", True, "service", True)
    dto = DeviceListDTO("OK", [device])
    value = device_list_from_dto(dto)
    assert device_to_dto(value.devices[0]) == device
    assert device_list_to_dto(value) == dto


def test_detailed_installation_mapping_round_trip() -> None:
    service = ServiceDTO("alarm", True, True)
    device = DeviceDTO("id", "code", "Camera", "CAMERA", "IP", True, "service", True)
    data = InstallationDataDTO(
        "123", "owner", "alias", "ACTIVE", "panel", "sim", "ibs",
        [service], [device], "repo", "capabilities",
    )
    dto = DetailedInstallationDTO(data, "en")
    value = detailed_installation_from_dto(dto)
    assert detailed_installation_to_dto(value) == dto
