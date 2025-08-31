"""Custom exceptions for My Verisure API."""


class MyVerisureError(Exception):
    """Base exception for My Verisure API errors."""


class MyVerisureAuthenticationError(MyVerisureError):
    """Authentication failed."""


class MyVerisureConnectionError(MyVerisureError):
    """Connection to My Verisure API failed."""


class MyVerisureResponseError(MyVerisureError):
    """Invalid response from My Verisure API."""


class MyVerisureMFAError(MyVerisureError):
    """MFA authentication error."""


class MyVerisureOTPError(MyVerisureError):
    """OTP authentication error."""


class MyVerisureDeviceAuthorizationError(MyVerisureError):
    """Device authorization error - device needs to be authorized."""
