"""Base client for My Verisure GraphQL API.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional

import aiohttp

from .fields import VERISURE_GRAPHQL_URL, NATIVE_APP_VERSION
from .exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureServiceBlockedError,
    MyVerisureTimeoutError,
)
from ..session_manager import SessionManager
from .native_profile import ProfileContext
from .provider_request_gate import ProviderRequestGate, get_provider_request_gate

_LOGGER = logging.getLogger(__name__)


class BaseClient:
    """Base client with HTTP and GraphQL functionality."""

    def __init__(self, session_manager: SessionManager, profile_context: ProfileContext | None = None) -> None:
        """Initialize the client with its entry-scoped session."""
        self._session_manager = session_manager
        self._profile_context = profile_context if isinstance(profile_context, ProfileContext) else ProfileContext()

    def _resolve_session_manager(self) -> SessionManager:
        """Return the session manager owned by this composition root."""
        return self._session_manager
    def _get_native_app_headers(self) -> Dict[str, str]:
        """Get native app headers for better authentication."""
        return {
            "App": json.dumps({"origin": "native", "appVersion": NATIVE_APP_VERSION}),
            "Extension": '{"mode": "full"}',
        }

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "HomeAssistant-MyVerisure/1.0",
        }

        # The native app's embedded client uses the web transport for data and
        # device verification while retaining OWI device-bound authentication.
        headers.update({
            "app-origin": "web",
            "app-version": NATIVE_APP_VERSION,
            "app-version-code": "3.8.0",
        })

        return headers

    def _get_current_credentials(self) -> tuple[Optional[str], Dict[str, Any]]:
        """Get current credentials from SessionManager."""
        session_manager = self._resolve_session_manager()
        session_data = session_manager.get_current_session_data() or {}
        return session_manager.hash_token, session_data


    def _get_session_headers(
        self, session_data: Dict[str, Any], hash_token: Optional[str] = None
    ) -> Dict[str, str]:
        """Get headers with session data for device validation."""        
        if (
            not isinstance(session_data, dict)
            or not session_data.get("user")
            or not isinstance(hash_token, str)
            or not hash_token.strip()
        ):
            raise MyVerisureAuthenticationError("Authenticated session unavailable")

        session_header: Dict[str, Any] = {
            "loginTimestamp": int(time.time() * 1000),
            "user": session_data["user"],
            "id": self._profile_context.current.session_id,
            "country": "ES",
            "callby": self._profile_context.current.callby,
            "hash": hash_token,
        }
        # Login uses the ES/es protocol profile. Keep that locale when the
        # persisted credential projection contains only user and login time.
        lang = session_data.get("lang", "es")
        if not isinstance(lang, str) or not lang.strip():
            raise MyVerisureAuthenticationError("Authenticated session unavailable")
        session_header["lang"] = lang
        
        headers = self._get_headers()
        headers["auth"] = json.dumps(session_header)
        
        return headers

    async def _execute_query_direct(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Admit one provider request before creating any HTTP resources."""
        gate = get_provider_request_gate()
        async with gate.async_request(self._resolve_session_manager()):
            return await self._execute_admitted_query(query, variables, headers, gate)

    async def _execute_admitted_query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]],
        headers: Optional[Dict[str, str]],
        gate: ProviderRequestGate,
    ) -> Dict[str, Any]:
        """Execute exactly once while holding origin admission, including close."""
        _session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30, connect=10)
        )
        
        try:
            request_data = {"query": query, "variables": variables or {}}
            request_headers = headers or self._get_headers()

            async with _session.post(
                VERISURE_GRAPHQL_URL,
                json=request_data,
                headers=request_headers,
            ) as response:
                if response.status in (403, 429):
                    retry_after = (getattr(response, "headers", None) or {}).get(
                        "Retry-After"
                    )
                    seconds = gate.record_blocked(retry_after)
                    recorder = getattr(
                        self._resolve_session_manager(), "record_service_blocked", None
                    )
                    if callable(recorder):
                        try:
                            recorder(seconds)
                        except Exception:
                            _LOGGER.debug("Could not record entry-local provider backoff")
                    _LOGGER.warning("Provider requests paused after HTTP %s", response.status)
                    raise MyVerisureServiceBlockedError(
                        "Service temporarily blocked; requests are paused"
                    )

                if response.status == 401:
                    raise MyVerisureAuthenticationError("Authentication failed") from None
                if response.status >= 400:
                    raise MyVerisureConnectionError("HTTP request failed") from None

                result = await response.json()
                return result

        except (
            MyVerisureAuthenticationError,
            MyVerisureConnectionError,
            MyVerisureServiceBlockedError,
            MyVerisureTimeoutError,
        ):
            raise
        except asyncio.CancelledError:
            raise
        except TimeoutError:
            _LOGGER.error("Connection to My Verisure timed out")
            raise MyVerisureTimeoutError("Connection timed out") from None
        except (aiohttp.ClientError, OSError):
            _LOGGER.error("Connection to My Verisure failed")
            raise MyVerisureConnectionError("Connection failed") from None
        except Exception:
            _LOGGER.error("Direct GraphQL query failed")
            raise MyVerisureConnectionError("Connection failed") from None
        finally:
            if not _session.closed:
                await _session.close()
