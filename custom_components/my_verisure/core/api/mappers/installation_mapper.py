"""Mappings between installation transport DTOs and domain values."""

from ..models.domain.installation import (
    DetailedInstallation,
    Installation,
    InstallationData,
    InstallationsList,
    Service,
)
from ..models.dto.installation_dto import (
    DetailedInstallationDTO,
    InstallationDTO,
    InstallationDataDTO,
    InstallationsListDTO,
    ServiceDTO,
)
from .device_mapper import device_from_dto, device_to_dto


def service_from_dto(dto: ServiceDTO) -> Service:
    return Service(
        id_service=dto.id_service,
        active=dto.active,
        visible=dto.visible,
        bde=dto.bde,
        is_premium=dto.is_premium,
        cod_oper=dto.cod_oper,
        request=dto.request,
        min_wrapper_version=dto.min_wrapper_version,
        unprotect_active=dto.unprotect_active,
        unprotect_device_status=dto.unprotect_device_status,
        inst_date=dto.inst_date,
        generic_config=dto.generic_config,
        attributes=dto.attributes,
    )


def service_to_dto(value: Service) -> ServiceDTO:
    return ServiceDTO(
        id_service=value.id_service,
        active=value.active,
        visible=value.visible,
        bde=value.bde,
        is_premium=value.is_premium,
        cod_oper=value.cod_oper,
        request=value.request,
        min_wrapper_version=value.min_wrapper_version,
        unprotect_active=value.unprotect_active,
        unprotect_device_status=value.unprotect_device_status,
        inst_date=value.inst_date,
        generic_config=value.generic_config,
        attributes=value.attributes,
    )


def installation_from_dto(dto: InstallationDTO) -> Installation:
    return Installation(
        numinst=dto.numinst,
        alias=dto.alias,
        panel=dto.panel,
        type=dto.type,
        name=dto.name,
        surname=dto.surname,
        address=dto.address,
        city=dto.city,
        postcode=dto.postcode,
        province=dto.province,
        email=dto.email,
        phone=dto.phone,
        due=dto.due,
        role=dto.role,
    )


def installation_to_dto(value: Installation) -> InstallationDTO:
    return InstallationDTO(
        numinst=value.numinst,
        alias=value.alias,
        panel=value.panel,
        type=value.type,
        name=value.name,
        surname=value.surname,
        address=value.address,
        city=value.city,
        postcode=value.postcode,
        province=value.province,
        email=value.email,
        phone=value.phone,
        due=value.due,
        role=value.role,
    )


def installation_data_from_dto(dto: InstallationDataDTO) -> InstallationData:
    return InstallationData(
        numinst=dto.numinst,
        role=dto.role,
        alias=dto.alias,
        status=dto.status,
        panel=dto.panel,
        sim=dto.sim,
        instIbs=dto.instIbs,
        services=[service_from_dto(service) for service in dto.services],
        devices=[device_from_dto(device) for device in dto.devices],
        configRepoUser=dto.configRepoUser,
        capabilities=dto.capabilities,
    )


def installation_data_to_dto(value: InstallationData) -> InstallationDataDTO:
    return InstallationDataDTO(
        numinst=value.numinst,
        role=value.role,
        alias=value.alias,
        status=value.status,
        panel=value.panel,
        sim=value.sim,
        instIbs=value.instIbs,
        services=[service_to_dto(service) for service in value.services],
        devices=[device_to_dto(device) for device in value.devices],
        configRepoUser=value.configRepoUser,
        capabilities=value.capabilities,
    )


def detailed_installation_from_dto(dto: DetailedInstallationDTO) -> DetailedInstallation:
    return DetailedInstallation(installation_data_from_dto(dto.installation), dto.language)


def detailed_installation_to_dto(value: DetailedInstallation) -> DetailedInstallationDTO:
    return DetailedInstallationDTO(installation_data_to_dto(value.installation), value.language)


def installations_list_from_dto(dto: InstallationsListDTO) -> InstallationsList:
    return InstallationsList([installation_from_dto(item) for item in dto.installations])


def installations_list_to_dto(value: InstallationsList) -> InstallationsListDTO:
    return InstallationsListDTO([installation_to_dto(item) for item in value.installations])
