"""Entry-owned native protocol profiles.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from dataclasses import dataclass

from .fields import NATIVE_OS_VERSION, NATIVE_SESSION_ID


@dataclass(frozen=True)
class NativeProfile:
    callby: str
    session_id: str
    os_version: str


IOS = NativeProfile("OWI_10", NATIVE_SESSION_ID, NATIVE_OS_VERSION)
ANDROID = NativeProfile("OWA_10", "OWA______________________", "16")


class ProfileContext:
    """Share the selected profile only within one composition root."""

    def __init__(self) -> None:
        self.current = IOS

    def select(self, name: str | None) -> None:
        self.current = ANDROID if name == "android" else IOS
