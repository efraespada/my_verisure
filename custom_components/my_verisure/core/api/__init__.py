"""My Verisure API client."""

from .exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureError,
    MyVerisureOTPError,
)

__all__ = [
    "MyVerisureError",
    "MyVerisureAuthenticationError",
    "MyVerisureConnectionError",
    "MyVerisureOTPError",
]
