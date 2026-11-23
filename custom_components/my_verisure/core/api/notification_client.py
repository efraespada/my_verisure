"""Read the permitted open-incidence projection without acknowledging alerts.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import re

from .base_client import BaseClient
from .exceptions import MyVerisureError


OPEN_INCIDENTS_QUERY = """
query xSSmartNotificationsOpenIncidenceList($numinst: String!) {
  xSSmartNotificationsOpenIncidenceList(numinst: $numinst) {
    incidences {
      incidenceNumber
      date
    }
  }
}
"""


class NotificationClient(BaseClient):
    """Resolve explicit incident references using a bounded, read-only query."""

    async def get_open_incidents(
        self,
        installation_id: str,
        panel: str,
        capabilities: str,
    ) -> tuple[str, ...]:
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (installation_id, panel, capabilities)
        ):
            raise MyVerisureError("Incident query context unavailable")
        token, session = self._get_current_credentials()
        headers = self._get_session_headers(session, token)
        headers.update(
            {"numinst": installation_id, "panel": panel, "x-capabilities": capabilities}
        )
        response = await self._execute_query_direct(
            OPEN_INCIDENTS_QUERY,
            {"numinst": installation_id},
            headers,
        )
        return self._incident_ids(response)

    @staticmethod
    def _incident_ids(response: object) -> tuple[str, ...]:
        if not isinstance(response, dict):
            raise MyVerisureError("Open incident response unavailable")
        data = response.get("data")
        projection = (
            data.get("xSSmartNotificationsOpenIncidenceList")
            if isinstance(data, dict)
            else None
        )
        values = projection.get("incidences") if isinstance(projection, dict) else None
        if "errors" in response or not isinstance(values, list) or len(values) > 256:
            raise MyVerisureError("Open incident response unavailable")
        ids: list[str] = []
        for item in values:
            value = item.get("incidenceNumber") if isinstance(item, dict) else None
            if isinstance(value, bool) or not isinstance(value, (str, int)):
                raise MyVerisureError("Open incident response unavailable")
            identifier = str(value)
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", identifier):
                raise MyVerisureError("Open incident response unavailable")
            if identifier not in ids:
                ids.append(identifier)
        return tuple(ids)
