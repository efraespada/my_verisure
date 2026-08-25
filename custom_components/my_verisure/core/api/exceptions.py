"""Compatibility exports for provider-facing imports.

Canonical exception ownership lives in the application boundary so use cases do
not depend on the API adapter package.
"""

from ..application.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureDeviceAuthorizationError,
    MyVerisureError,
    MyVerisureMFAError,
    MyVerisureOTPError,
    MyVerisurePersistenceError,
    MyVerisureResponseError,
    MyVerisureServiceBlockedError,
    MyVerisureTimeoutError,
)

__all__ = [
    "MyVerisureError",
    "MyVerisureAuthenticationError",
    "MyVerisureConnectionError",
    "MyVerisureTimeoutError",
    "MyVerisurePersistenceError",
    "MyVerisureResponseError",
    "MyVerisureMFAError",
    "MyVerisureOTPError",
    "MyVerisureDeviceAuthorizationError",
    "MyVerisureServiceBlockedError",
]
