"""Application-domain errors for authentication and provider boundaries."""


class MyVerisureError(Exception):
    """Base application error."""


class MyVerisureAuthenticationError(MyVerisureError):
    """Authentication failed."""


class MyVerisureConnectionError(MyVerisureError):
    """Transport or provider connectivity failed."""


class MyVerisureTimeoutError(MyVerisureConnectionError):
    """Provider request exceeded its timeout."""


class MyVerisurePersistenceError(MyVerisureError):
    """Authenticated session persistence failed."""


class MyVerisureResponseError(MyVerisureError):
    """Provider response did not satisfy the application contract."""


class MyVerisureMFAError(MyVerisureError):
    """Multi-factor authentication failed."""


class MyVerisureOTPError(MyVerisureError):
    """OTP authentication error carrying the challenge for the application flow."""

    def __init__(
        self,
        message: str,
        *,
        phones=None,
        otp_hash: str | None = None,
        retryable: bool = False,
        code: str = "terminal",
    ):
        super().__init__(message)
        self.phones = tuple(phones or ())
        self.otp_hash = otp_hash
        self.retryable = retryable
        self.code = code


class MyVerisureDeviceAuthorizationError(MyVerisureError):
    """Device authorization is required or failed."""


class MyVerisureServiceBlockedError(MyVerisureError):
    """Provider temporarily blocked the service."""
