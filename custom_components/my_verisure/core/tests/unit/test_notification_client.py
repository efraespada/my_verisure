"""Bounded read-only incident projection and session permission policy.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure.core.api.notification_client import (
    NotificationClient,
)
from custom_components.my_verisure.core.application.exceptions import MyVerisureError
from custom_components.my_verisure.core.application.notification_verification import (
    has_smart_notifications,
)
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.session_manager import SessionManager


@pytest.mark.parametrize(
    "active,visible,expected",
    [
        (True, True, True),
        (False, True, False),
        (True, False, False),
        (1, True, False),
        (True, "true", False),
        (None, None, False),
    ],
)
def test_smart_notifications_requires_effective_service_520(active, visible, expected):
    snapshot = {
        "detailed_installation": {
            "installation": {
                "role": "ADMIN",
                "services": [
                    {"id_service": "520", "active": active, "visible": visible}
                ],
            }
        }
    }
    assert has_smart_notifications(snapshot) is expected


@pytest.mark.parametrize(
    "snapshot",
    [
        None,
        {},
        {"detailed_installation": None},
        {"detailed_installation": {"installation": {"services": []}}},
        {
            "detailed_installation": {
                "installation": {
                    "services": [
                        {"id_service": "other", "active": True, "visible": True}
                    ]
                }
            }
        },
    ],
)
def test_missing_permission_never_infers_owner_access(snapshot):
    assert not has_smart_notifications(snapshot)


async def test_incident_query_is_read_only_and_omits_customer_names(tmp_path):
    client = NotificationClient(SessionManager(file_manager=FileManager(tmp_path)))
    client._get_current_credentials = Mock(
        return_value=("synthetic", {"user": "synthetic"})
    )
    client._execute_query_direct = AsyncMock(
        return_value={
            "data": {
                "xSSmartNotificationsOpenIncidenceList": {
                    "incidences": [
                        {
                            "incidenceNumber": "123",
                            "date": "synthetic",
                            "customerName": "must-not-be-returned",
                        },
                        {"incidenceNumber": "123", "date": "synthetic"},
                        {"incidenceNumber": 456, "date": "synthetic"},
                    ]
                },
            }
        }
    )
    assert await client.get_open_incidents("house", "panel", "caps") == ("123", "456")
    document, variables, headers = client._execute_query_direct.await_args.args
    assert "query xSSmartNotificationsOpenIncidenceList" in document
    assert "mutation" not in document
    assert "customerName" not in document
    assert variables == {"numinst": "house"}
    assert headers["numinst"] == "house" and headers["x-capabilities"] == "caps"


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {},
        {"data": None},
        {"errors": [{"message": "private-provider-detail"}]},
        {"data": {"xSSmartNotificationsOpenIncidenceList": {"incidences": None}}},
        {"data": {"xSSmartNotificationsOpenIncidenceList": {"incidences": [None]}}},
        {
            "data": {
                "xSSmartNotificationsOpenIncidenceList": {
                    "incidences": [{"incidenceNumber": True}]
                }
            }
        },
        {
            "data": {
                "xSSmartNotificationsOpenIncidenceList": {
                    "incidences": [{"incidenceNumber": "../../private"}]
                }
            }
        },
    ],
)
async def test_bad_incident_response_is_unknown_not_empty(tmp_path, payload):
    client = NotificationClient(SessionManager(file_manager=FileManager(tmp_path)))
    client._get_current_credentials = Mock(
        return_value=("synthetic", {"user": "synthetic"})
    )
    client._execute_query_direct = AsyncMock(return_value=payload)
    with pytest.raises(MyVerisureError) as failure:
        await client.get_open_incidents("house", "panel", "caps")
    assert "private-provider-detail" not in str(failure.value)


async def test_empty_open_incident_list_is_valid_and_never_means_closed(tmp_path):
    client = NotificationClient(SessionManager(file_manager=FileManager(tmp_path)))
    client._get_current_credentials = Mock(
        return_value=("synthetic", {"user": "synthetic"})
    )
    client._execute_query_direct = AsyncMock(
        return_value={
            "data": {
                "xSSmartNotificationsOpenIncidenceList": {"incidences": []},
            }
        }
    )
    assert await client.get_open_incidents("house", "panel", "caps") == ()


@pytest.mark.parametrize(
    "context", [("", "panel", "caps"), ("house", None, "caps"), ("house", "panel", " ")]
)
async def test_missing_incident_context_rejects_before_credentials_or_provider(
    tmp_path, context
):
    client = NotificationClient(SessionManager(file_manager=FileManager(tmp_path)))
    client._get_current_credentials = Mock(
        side_effect=AssertionError("No credentials without context")
    )
    client._execute_query_direct = AsyncMock(
        side_effect=AssertionError("No request without context")
    )
    with pytest.raises(MyVerisureError, match="Incident query context unavailable"):
        await client.get_open_incidents(*context)
    client._get_current_credentials.assert_not_called()
    client._execute_query_direct.assert_not_awaited()
