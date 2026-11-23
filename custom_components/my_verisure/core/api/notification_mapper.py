"""Bounded mapping of official provider request names to private typed notices.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from __future__ import annotations

import json
import math
import re
from typing import Any

from ..application.notifications import (
    NotificationEvent,
    NotificationMapping,
    NotificationNotice,
    opaque_id,
)

_GROUPS = {
    "photo_reported": ("INF",),
    "alarm_operation_reported": (
        "ARMDISARM",
        "ALARMCONNECT",
        "ALARMDISCONNECT",
        "ALARMSTATUS",
    ),
    "security_incident_reported": ("SMARTNOT", "ALARMTRIGGER", "ALARMTRIPCANCELED"),
    "arm_reminder": ("SCHCD",),
    "unprotected_home": ("UNPROTECTED",),
    "smart_disarm_notice": ("SMARTDISARM",),
    "device_maintenance_notice": (
        "DIY",
        "DIYKEYS",
        "DIYREMINDER",
        "DIYTRACKING",
        "BATTERYSTATUS",
        "PREDIY",
        "PREDIYREMINDER",
    ),
    "device_tamper_reported": ("DIYTAMPER_DIY", "DIYTAMPER_NO_DIY"),
    "maintenance_appointment": ("MAINTENANCE", "MAINTENANCES", "RSCHAFTERSUSPEND"),
    "support_reply": ("ANSWER", "CHATHELP", "SUPPORTHUB"),
    "account_notice": (
        "AUTH",
        "AUTHTESTMODE",
        "TRUSTEDDEVICES",
        "RESETPASSW",
        "ACTIONPLAN",
        "CODEWORDS",
        "ALARMCHANGEUSER",
        "BILLINGDATA",
        "CONTRACT",
        "FIRST_INVOICE",
        "INVOICES",
        "KEYSREMOTE",
        "FAMILIES",
        "INVITATIONACCEPTED",
    ),
    "generic_notice": (
        "NOT",
        "PWC",
        "DEVICESFAST",
        "DEVICESMOONSHOT",
        "ENTRYEXITTIME",
        "HOME",
        "HOMEMOVE",
        "IND",
        "NOACCESSBROKER",
        "NOINTERNET",
        "SENTINELCONFIG",
        "WIFI",
        "WIFISETTINGS",
    ),
}
REQUEST_KINDS = {
    request: kind for kind, requests in _GROUPS.items() for request in requests
}
_PERSONAL = {"FAMILIES", "INVITATIONACCEPTED"}


def _strict_constant(value: str) -> None:
    raise ValueError("Unsupported JSON numeric constant")


def _private_id(value: object) -> str | None:
    if isinstance(value, str) and 0 < len(value) <= 128:
        return value
    return None


class NotificationMapper:
    """Provider grammar and recipient validation, with no HTTP or HA effects."""

    def __init__(self, installation_id: str, namespace: str) -> None:
        self._installation_id = installation_id
        self._namespace = namespace

    def __call__(
        self, payload: dict[str, Any], persistent_id: str, now: float
    ) -> NotificationMapping:
        try:
            text = payload["data"]["text"]
            if not isinstance(text, str):
                raise ValueError
            if len(text) > 8192 or len(text.encode()) > 32768:
                return NotificationMapping(None, "oversized")
            data = json.loads(text, parse_constant=_strict_constant)
            if not isinstance(data, dict):
                raise ValueError
            request = data.get("request")
            if not isinstance(request, str) or not re.fullmatch(
                r"[A-Z][A-Z0-9_]{0,63}", request
            ):
                raise ValueError
            installation = data.get("numinst")
            if installation is not None:
                if type(installation) not in (str, int) or len(str(installation)) > 64:
                    raise ValueError
                if str(installation) != self._installation_id:
                    return NotificationMapping(None, "foreign_scope")
            scope = (
                "personal"
                if request in _PERSONAL
                else "installation"
                if installation is not None
                else "account"
            )
            stamp = data.get("timeStamp")
            occurred: float | None = None
            if stamp is not None:
                if type(stamp) not in (str, int, float) or isinstance(stamp, bool):
                    raise ValueError
                occurred = float(stamp) / 1000
                if not math.isfinite(occurred) or occurred < 0:
                    raise ValueError
                if occurred > now + 60:
                    return NotificationMapping(None, "future")
            freshness = (
                "unknown"
                if occurred is None
                else "stale"
                if occurred < now - 300
                else "fresh"
            )
            kind = REQUEST_KINDS.get(request, "unclassified_notice")
            category = (
                "photo"
                if kind == "photo_reported"
                else "alarm"
                if kind == "alarm_operation_reported"
                else "incident"
                if kind == "security_incident_reported"
                else "reminder"
                if kind in {"arm_reminder", "unprotected_home", "smart_disarm_notice"}
                else "maintenance"
                if kind
                in {
                    "device_maintenance_notice",
                    "device_tamper_reported",
                    "maintenance_appointment",
                }
                else "support"
                if kind == "support_reply"
                else "account"
                if kind == "account_notice"
                else "other"
            )
            identity = opaque_id(self._namespace, "delivery:" + persistent_id)
            event = NotificationEvent(
                kind,
                "reported",
                identity,
                identity,
                category,
                scope,
                now,
                provider_request=request if request in REQUEST_KINDS else None,
                occurred_at=occurred,
                freshness=freshness,
            )
            signal = (
                _private_id(data.get("idSignal"))
                if request in {"INF", "SMARTNOT"}
                else None
            )
            if signal is not None and not signal.isdigit():
                signal = None
            operation = None
            if request == "ARMDISARM":
                advanced = data.get("advancedInfo")
                try:
                    detail = (
                        json.loads(advanced, parse_constant=_strict_constant)
                        if isinstance(advanced, str)
                        else advanced
                    )
                    if isinstance(detail, dict):
                        operation = _private_id(detail.get("requestId"))
                except (TypeError, ValueError, RecursionError):
                    pass
            photo_type = (
                data.get("type")
                if request == "INF" and type(data.get("type")) is int
                else None
            )
            return NotificationMapping(
                NotificationNotice(event, signal, operation, photo_type), "accepted"
            )
        except (
            KeyError,
            TypeError,
            ValueError,
            OverflowError,
            UnicodeError,
            RecursionError,
        ):
            return NotificationMapping(None, "malformed")
