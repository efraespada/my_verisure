"""Base client for My Verisure GraphQL API."""

import json
import logging
import time
from typing import Any, Dict, Optional

import aiohttp

from .exceptions import MyVerisureConnectionError
from .fields import VERISURE_GRAPHQL_URL

_LOGGER = logging.getLogger(__name__)


class BaseClient:
    """Base client with HTTP and GraphQL functionality."""

    def __init__(self) -> None:
        """Initialize the base client."""
        self._session: Optional[aiohttp.ClientSession] = None
        self._cookies: Dict[str, str] = {}


    async def __aenter__(self):
        """Async context manager entry."""
        await self._connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self._disconnect()

    async def _connect(self) -> None:
        """Connect to My Verisure API (private)."""
        if self._session is None:
            self._session = aiohttp.ClientSession()

    async def _disconnect(self) -> None:
        """Disconnect from My Verisure API (private)."""
        _LOGGER.warning("🔌 BaseClient._disconnect() called - session: %s", self._session)
        if self._session:
            # Close the aiohttp session properly
            if not self._session.closed:
                _LOGGER.warning("🔌 Closing aiohttp session")
                await self._session.close()
            self._session = None
            _LOGGER.warning("🔌 Session closed and set to None")

    async def _ensure_session(self) -> None:
        """Ensure session is ready for use."""
        if self._session is None:
            await self._connect()

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
        from ..session_manager import get_session_manager
        session_manager = get_session_manager()
        return session_manager.hash_token, session_manager.get_current_session_data()


    def _get_session_headers(
        self, session_data: Dict[str, Any], hash_token: Optional[str] = None
    ) -> Dict[str, str]:
        """Get headers with session data for device validation."""
        _LOGGER.warning("_get_session_headers called with session_data=%s, hash_token=%s", session_data, hash_token)
        
        if not session_data:
            _LOGGER.warning("No session data available, using basic headers")
            return self._get_headers()

        # Create session header as shown in the browser
        session_header = {
            "loginTimestamp": int(time.time() * 1000),
            "user": session_data.get("user", ""),
            "id": f"OWI______________________",
            "country": "ES",
            "lang": session_data.get("lang", "es"),
            "callby": "OWI_10",
            "hash": hash_token if hash_token else None,
        }
        
        _LOGGER.warning("Created session_header: %s", session_header)

        headers = self._get_headers()
        headers["auth"] = json.dumps(session_header)
        
        _LOGGER.warning("Final headers: %s", headers)

        return headers

    def _get_cookies(self) -> Dict[str, str]:
        """Get cookies for API requests."""
        return self._cookies.copy()

    def _update_cookies_from_response(self, response_cookies: Any) -> None:
        """Update cookies from response."""
        if hasattr(response_cookies, "items"):
            for name, value in response_cookies.items():
                if value:
                    self._cookies[name] = value
                    _LOGGER.debug("Updated cookie: %s", name)

    

    async def _execute_query_direct(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Execute a GraphQL query using direct aiohttp request."""
        # Ensure session is ready
        await self._ensure_session()
        
        try:
            request_data = {"query": query, "variables": variables or {}}
            request_headers = headers or self._get_headers()

            async with self._session.post(
                VERISURE_GRAPHQL_URL,
                json=request_data,
                headers=request_headers,
            ) as response:
                result = await response.json()
                return result

        except Exception as e:
            _LOGGER.error("Direct GraphQL query failed: %s", e)
            return {"errors": [{"message": str(e), "data": {}}]}
        finally:
            # Always disconnect after the request
            await self._disconnect()
