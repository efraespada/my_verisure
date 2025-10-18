"""Base client for My Verisure GraphQL API."""

import json
import logging
import time
from typing import Any, Dict, Optional

import aiohttp

from .fields import VERISURE_GRAPHQL_URL

_LOGGER = logging.getLogger(__name__)


class BaseClient:
    """Base client with HTTP and GraphQL functionality."""

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
        if not session_data:
            _LOGGER.warning("No session data available, using basic headers")
            return self._get_headers()

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

    async def _execute_query_direct(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Execute a GraphQL query using direct aiohttp request."""
        _session = aiohttp.ClientSession()
        
        try:
            request_data = {"query": query, "variables": variables or {}}
            request_headers = headers or self._get_headers()

            async with _session.post(
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
            if not _session.closed:
                await _session.close()
            _session = None
