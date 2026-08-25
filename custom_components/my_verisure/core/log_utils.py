"""Safe logging helpers: redact secrets and optional developer-mode verbosity."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
import logging
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Any

_TOKEN_PREFIX_LEN = 20

# Per-task dev mode (singleton API clients read this during coordinator work).
_dev_mode_ctx: ContextVar[bool] = ContextVar("my_verisure_dev_mode", default=False)


def _norm_key(key: str) -> str:
    return key.replace("-", "_").lower()


# Keys to strip entirely from log payloads (case-insensitive match).
_DROP_KEYS_NORM = frozenset(
    {
        "x_capabilities",
    }
)

# Keys whose values are always truncated / redacted.
_REDACT_KEYS_NORM = frozenset(
    {
        "hash",
        "hash_token",
        "refresh_token",
        "refreshtoken",
        "password",
        "otp_code",
        "otpcode",
        "otp_hash",
        "otphash",
        "authorization",
        "accesstoken",
        "access_token",
        "token",
        "user",
        "username",
        "phone",
        "uuid",
        "deviceuuid",
        "device_uuid",
        "devicename",
        "device_name",
        "alias",
        "name",
        "devicealias",
        "device_alias",
        "cameraname",
        "camera_name",
        "displayname",
        "display_name",
        "friendlyname",
        "friendly_name",
        "servicename",
        "service_name",
        "installationname",
        "installation_name",
        "record_id",
        "recordid",
        "security",
        "id",
        "installation_id",
        "installationid",
        "current_installation",
        "numinst",
        "message",
        "msg",
        "detail",
        "reference_id",
        "referenceid",
        "id_service",
        "idservice",
        "capabilities",
        "panel",
        "auth_code",
        "authcode",
        "id_signal",
        "idsignal",
        "path",
        "file_path",
        "filepath",
        "reference",
        "error",
    }
)


def get_dev_mode() -> bool:
    """Return whether verbose (developer) logging is enabled for the current context."""
    return _dev_mode_ctx.get()


def set_dev_mode(value: bool) -> Token[bool]:
    """Set dev mode for the current context; returns a token for reset."""
    return _dev_mode_ctx.set(value)


def reset_dev_mode(token: Token[bool]) -> None:
    """Restore previous dev mode using the token from set_dev_mode."""
    _dev_mode_ctx.reset(token)


@contextmanager
def dev_mode_context(enabled: bool):
    """Temporarily enable or disable dev mode for this async task."""
    token = _dev_mode_ctx.set(enabled)
    try:
        yield
    finally:
        _dev_mode_ctx.reset(token)


def truncate_secret(value: str | None, prefix_len: int = _TOKEN_PREFIX_LEN) -> str:
    """Return a fully redacted marker without exposing any secret prefix."""
    del prefix_len
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    return "[REDACTED]" if value else ""


def _redact_structure(obj: Any) -> Any:
    """Deep-copy redaction for dicts/lists; leave primitives except long strings."""
    if isinstance(obj, BaseException):
        return "[REDACTED]"
    if is_dataclass(obj) and not isinstance(obj, type):
        return _redact_structure(asdict(obj))
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            nk = _norm_key(str(k))
            if nk in _DROP_KEYS_NORM:
                continue
            if nk in _REDACT_KEYS_NORM:
                out[k] = "[REDACTED]"
            else:
                out[k] = _redact_structure(v)
        return out
    if isinstance(obj, list):
        return [_redact_structure(item) for item in obj]
    if isinstance(obj, (tuple, set, frozenset)):
        return [_redact_structure(item) for item in obj]
    if obj is None:
        return None
    if isinstance(obj, (bool, int, float, str)):
        return "[REDACTED]"
    return "[REDACTED]"


def redact_sensitive_data(data: Any) -> str:
    """Serialize data for logs with secrets truncated and noisy keys removed."""
    try:
        redacted = _redact_structure(data)
        return json.dumps(redacted, ensure_ascii=False)
    except (TypeError, ValueError):
        return "<non-serializable>"


def redact_headers_for_log(headers: dict[str, Any] | None) -> str:
    """Redact auth header JSON (hash) and drop x-capabilities for logging."""
    if not headers:
        return "{}"
    safe: dict[str, Any] = {}
    for key, val in headers.items():
        lk = key.lower()
        if lk in ("x-capabilities", "x_capabilities"):
            continue
        if lk == "auth" and isinstance(val, str):
            try:
                parsed = json.loads(val)
                if isinstance(parsed, dict):
                    safe[key] = json.dumps(
                        _redact_structure(parsed), ensure_ascii=False
                    )
                else:
                    safe[key] = "<auth>"
            except json.JSONDecodeError:
                safe[key] = "<auth unparsable>"
        else:
            redacted = _redact_structure({key: val})
            safe[key] = redacted.get(key, "[REDACTED]")
    return json.dumps(safe, ensure_ascii=False)


def should_log_detailed() -> bool:
    """Whether to emit verbose DEBUG/INFO used only for troubleshooting."""
    return get_dev_mode()


def log_if_dev(
    logger: logging.Logger,
    level: int,
    msg: str,
    *args: Any,
    **kwargs: Any,
) -> None:
    """Log at the given level only when dev mode is on for the current context."""
    if get_dev_mode():
        logger.log(level, msg, *args, **kwargs)


def redact_otp_message() -> str:
    """Fixed message when an OTP was received (never log the code)."""
    return "OTP code received (redacted)"

