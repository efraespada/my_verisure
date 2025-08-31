"""Base client for My Verisure GraphQL API."""

import json
import logging
import time
from typing import Any, Dict, Optional

import aiohttp
from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport

from .exceptions import MyVerisureConnectionError
from .fields import VERISURE_GRAPHQL_URL

_LOGGER = logging.getLogger(__name__)


class BaseClient:
    """Base client with HTTP and GraphQL functionality."""

    def __init__(self) -> None:
        """Initialize the base client."""
        self._session: Optional[aiohttp.ClientSession] = None
        self._client: Optional[Client] = None
        self._cookies: Dict[str, str] = {}

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> None:
        """Connect to My Verisure API."""
        if self._session is None:
            self._session = aiohttp.ClientSession()

        headers = self._get_headers()
        transport = AIOHTTPTransport(
            url=VERISURE_GRAPHQL_URL,
            headers=headers,
            cookies=self._get_cookies(),
        )

        self._client = Client(
            transport=transport, fetch_schema_from_transport=False
        )

    async def disconnect(self) -> None:
        """Disconnect from My Verisure API."""
        if self._client:
            self._client = None

        if self._session:
            await self._session.close()
            self._session = None

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

    def _get_session_headers(
        self, session_data: Dict[str, Any], hash_token: Optional[str] = None
    ) -> Dict[str, str]:
        """Get headers with session data for device validation."""
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

        headers = self._get_headers()
        headers["auth"] = json.dumps(session_header)

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

    async def _execute_query(
        self, query: Any, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a GraphQL query."""
        if not self._client:
            raise MyVerisureConnectionError("Client not connected")

        try:
            result = await self._client.execute_async(
                query, variable_values=variables
            )
            return result
        except Exception as e:
            _LOGGER.error("GraphQL query failed: %s", e)
            # Check if this is a GraphQL error response
            if "errors" in str(e):
                try:
                    error_str = str(e)
                    if "{" in error_str and "}" in error_str:
                        start = error_str.find("{")
                        end = error_str.rfind("}") + 1
                        error_json = error_str[start:end]
                        error_data = json.loads(error_json)
                        return error_data
                except:
                    pass

            # Return a generic error if we can't parse it
            return {"errors": [{"message": str(e), "data": {}}]}

    async def _execute_query_direct(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Execute a GraphQL query using direct aiohttp request."""
        if not self._session:
            raise MyVerisureConnectionError("Client not connected")

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
