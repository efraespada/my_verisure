"""Base client for My Verisure GraphQL API."""

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional

import aiohttp

from .fields import VERISURE_GRAPHQL_URL
from .exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureServiceBlockedError,
    MyVerisureTimeoutError,
)
from ..session_manager import SessionManager

_LOGGER = logging.getLogger(__name__)


class BaseClient:
    """Base client with HTTP and GraphQL functionality."""

    def __init__(self, session_manager: SessionManager) -> None:
        """Initialize the client with its entry-scoped session."""
        self._session_manager = session_manager

    def _resolve_session_manager(self) -> SessionManager:
        """Return the session manager owned by this composition root."""
        return self._session_manager
    def _get_native_app_headers(self) -> Dict[str, str]:
        """Get native app headers for better authentication."""
        return {
            "App": '{"origin": "native", "appVersion": "10.154.0"}',
            "Extension": '{"mode": "full"}',
        }

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "HomeAssistant-MyVerisure/1.0",
        }

        # Add native app headers
        headers.update(self._get_native_app_headers())

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
            "id": "OWI______________________",
            "country": "ES",
            "callby": "OWI_10",
            "hash": hash_token,
        }
        if "lang" in session_data:
            lang = session_data["lang"]
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
        """Execute a GraphQL query using direct aiohttp request."""
        
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
                # Check for HTTP 403 status code (service blocked)
                if response.status == 403:
                    _LOGGER.error(
                        "Service temporarily blocked (HTTP 403) - too many requests"
                    )
                    try:
                        self._resolve_session_manager().record_service_blocked()
                    except Exception:  # noqa: BLE001
                        _LOGGER.debug("Could not record service-blocked backoff", exc_info=True)
                    raise MyVerisureServiceBlockedError(
                        "Service temporarily blocked due to too many requests. Please wait about 10 minutes before trying again."
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
