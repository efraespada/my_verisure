"""Installation responses must match the current native query contract.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import re
import json

import pytest

from custom_components.my_verisure.core.api.device_manager import DeviceManager
from custom_components.my_verisure.core.api.installation_client import InstallationClient
from custom_components.my_verisure.core.dependency_injection.composition_root import (
    build_my_verisure_composition_root,
)
from custom_components.my_verisure.core.session_manager import SessionManager


@pytest.mark.asyncio
@pytest.mark.parametrize("nullable_metadata", [False, True])
async def test_native_installation_query_selects_required_device_fields_and_binds_uuid(tmp_path, nullable_metadata):
    root = build_my_verisure_composition_root(project_root=tmp_path)
    session = root.get(SessionManager)
    session.update_credentials("synthetic-user", "synthetic-password", "synthetic-token", persist=False)
    device_manager = root.get(DeviceManager)
    await device_manager.async_ensure_device_identifiers()
    client = root.get(InstallationClient)
    requests = []
    installation = {
        "numinst": "synthetic-installation", "role": "ADMIN", "alias": "Synthetic home",
        "status": "D", "panel": "SYNTHETIC", "sim": "synthetic-sim",
        "instIbs": "synthetic-ibs", "capabilities": "synthetic-capabilities",
        "configRepoUser": {"alarmPartitions": []},
        "services": [{
            "idService": "synthetic-service", "active": True, "visible": True,
            "bde": False, "isPremium": False, "codOper": False, "request": "EST",
            "minWrapperVersion": None, "unprotectActive": False,
            "unprotectDeviceStatus": None, "instDate": None,
            "genericConfig": None, "attributes": None,
        }],
    }
    native_device = {
        "id": "synthetic-device", "code": "SENSOR", "name": "Synthetic sensor",
        "type": "SENSOR", "subtype": "CONTACT", "remoteUse": False,
        "idService": "synthetic-service", "isActive": True,
    }

    if nullable_metadata:
        native_device.update(subtype=None, remoteUse=None, isActive=None)

    async def provider(query, variables=None, headers=None):
        requests.append((query, variables, headers))
        if "query Srv" in query:
            return {"data": {"xSSrv": {
                "res": "OK", "language": json.loads(headers["auth"]).get("lang", ""), "installation": installation,
            }}}
        if "query xSDeviceList" in query:
            # GraphQL returns only requested fields, unlike the old full-record mocks.
            selected = set(re.findall(r"\b\w+\b", query))
            return {"data": {"xSDeviceList": {"res": "OK", "devices": [
                {key: value for key, value in native_device.items() if key in selected}
            ]}}}
        return {"data": {"xSInstallations": {"installations": [{
            **installation, "type": "HOUSE", "name": "Synthetic", "surname": "User",
            "address": "Synthetic address", "city": "Synthetic city", "postcode": "00000",
            "province": "Synthetic province", "email": "synthetic@example.invalid",
            "phone": "synthetic-phone",
        }]}}}

    client._execute_query_direct = provider

    result = await client.get_installation_services("synthetic-installation")

    assert result.installation.devices[0].remote_use is native_device["remoteUse"]
    assert result.installation.devices[0].is_active is native_device["isActive"]
    assert result.installation.devices[0].subtype == native_device["subtype"]
    assert result.installation.services[0].generic_config is None
    assert result.installation.services[0].unprotect_device_status is None
    assert requests[0][1]["uuid"] == device_manager.get_device_identifiers()["uuid"]
    assert requests[1][2]["x-capabilities"] == "synthetic-capabilities"
