"""Pure request definitions for alarm GraphQL operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..api.graphql_alarm_queries import (
    ARM_PANEL_MUTATION,
    ARM_STATUS_QUERY,
    CHECK_ALARM_QUERY,
    CHECK_ALARM_STATUS_QUERY,
    DISARM_PANEL_MUTATION,
    DISARM_STATUS_QUERY,
)


@dataclass(frozen=True)
class AlarmGraphQLRequest:
    """One fully specified alarm GraphQL request."""

    operation: str
    query: str
    variables: dict[str, Any]


class AlarmGraphQLRequestPolicy:
    """Build alarm requests without transport or session dependencies."""

    @staticmethod
    def check_alarm(installation_id: str, panel: str) -> AlarmGraphQLRequest:
        return AlarmGraphQLRequest(
            "CheckAlarm",
            CHECK_ALARM_QUERY,
            {"numinst": installation_id, "panel": panel},
        )

    @staticmethod
    def check_alarm_status(
        installation_id: str,
        panel: str,
        id_service: str,
        reference_id: str,
    ) -> AlarmGraphQLRequest:
        return AlarmGraphQLRequest(
            "CheckAlarmStatus",
            CHECK_ALARM_STATUS_QUERY,
            {
                "numinst": installation_id,
                "panel": panel,
                "idService": id_service,
                "referenceId": reference_id,
            },
        )

    @staticmethod
    def arm_panel(
        installation_id: str,
        panel: str,
        request: str,
        current_status: str,
    ) -> AlarmGraphQLRequest:
        return AlarmGraphQLRequest(
            "ArmPanel",
            ARM_PANEL_MUTATION,
            {
                "numinst": installation_id,
                "request": request,
                "panel": panel,
                "currentStatus": current_status,
                "forceArmingRemoteId": None,
                "armAndLock": False,
            },
        )

    @staticmethod
    def arm_status(
        installation_id: str,
        panel: str,
        request: str,
        reference_id: str,
        counter: int,
    ) -> AlarmGraphQLRequest:
        return AlarmGraphQLRequest(
            "ArmStatus",
            ARM_STATUS_QUERY,
            {
                "numinst": installation_id,
                "request": request,
                "panel": panel,
                "referenceId": reference_id,
                "counter": counter,
                "forceArmingRemoteId": None,
                "armAndLock": False,
            },
        )

    @staticmethod
    def disarm_panel(
        installation_id: str,
        panel: str,
        request: str,
    ) -> AlarmGraphQLRequest:
        return AlarmGraphQLRequest(
            "DisarmPanel",
            DISARM_PANEL_MUTATION,
            {
                "numinst": installation_id,
                "request": request,
                "panel": panel,
            },
        )

    @staticmethod
    def disarm_status(
        installation_id: str,
        panel: str,
        request: str,
        reference_id: str,
        counter: int,
    ) -> AlarmGraphQLRequest:
        return AlarmGraphQLRequest(
            "DisarmStatus",
            DISARM_STATUS_QUERY,
            {
                "numinst": installation_id,
                "panel": panel,
                "referenceId": reference_id,
                "counter": counter,
                "request": request,
            },
        )
