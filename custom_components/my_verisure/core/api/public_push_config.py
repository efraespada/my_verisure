"""Discover public Firebase configuration without storing provider keys in source.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
from html.parser import HTMLParser
import re
from urllib.parse import urljoin, urlsplit

import aiohttp

from .push_config import APP_ID, MESSAGING_SENDER_ID, PROJECT_ID, PUBLIC_CLIENT_HOME


class _Scripts(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.sources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script":
            self.sources.extend(value for key, value in attrs if key == "src" and value)


def find_main_script(html: str) -> str:
    """Accept exactly one main asset on the known HTTPS origin."""
    parser = _Scripts()
    parser.feed(html)
    matches: set[str] = set()
    for source in parser.sources:
        url = urljoin(PUBLIC_CLIENT_HOME, source)
        parsed = urlsplit(url)
        if not re.fullmatch(r"/[^?\s]*/static/js/main\.[A-Za-z0-9_-]+\.js", parsed.path):
            continue
        if (
            parsed.scheme != "https" or parsed.hostname != "customers.verisure.es"
            or parsed.username is not None or parsed.password is not None
            or parsed.port not in (None, 443) or parsed.query or parsed.fragment
        ):
            raise ValueError("Public client asset has an unexpected origin")
        matches.add(url)
    if len(matches) != 1:
        raise ValueError("Public client main asset is missing or ambiguous")
    return matches.pop()


def parse_public_api_key(source: str) -> str:
    """Read literal metadata only; never execute JavaScript or echo its values."""
    fields: dict[str, str] = {}
    for name in ("PROJECT_ID", "APP_ID", "MESSAGING_SENDER_ID", "API_KEY"):
        values = set(re.findall(r'REACT_APP_FIREBASE_' + name + r'\s*:\s*"([^"\r\n]+)"', source))
        if len(values) != 1:
            raise ValueError("Public Firebase configuration is missing or ambiguous")
        fields[name] = values.pop()
    if (
        fields["PROJECT_ID"] != PROJECT_ID or fields["APP_ID"] != APP_ID
        or fields["MESSAGING_SENDER_ID"] != MESSAGING_SENDER_ID
        or not re.fullmatch(r"[A-Za-z0-9_-]{16,128}", fields["API_KEY"])
    ):
        raise ValueError("Public Firebase configuration does not match the known client")
    return fields["API_KEY"]


async def _read(session: aiohttp.ClientSession, url: str, limit: int) -> str:
    async with session.get(
        url, allow_redirects=False,
        headers={"User-Agent": "Mozilla/5.0 (compatible; HomeAssistant-MyVerisure/1.0)",
                 "Accept": "text/html,application/javascript"},
        timeout=aiohttp.ClientTimeout(total=15, connect=10),
    ) as response:
        if response.status != 200:
            raise ValueError("Public client configuration could not be retrieved")
        body = bytearray()
        async for chunk in response.content.iter_chunked(65536):
            if len(body) + len(chunk) > limit:
                raise ValueError("Public client configuration exceeds the size limit")
            body.extend(chunk)
        return body.decode("utf-8")


async def async_resolve_public_api_key(session: aiohttp.ClientSession | None = None) -> str:
    """Resolve metadata only for new registration, with bounded public GETs."""
    owned = session is None
    client = session if session is not None else aiohttp.ClientSession()
    try:
        page = await _read(client, PUBLIC_CLIENT_HOME, 1024 * 1024)
        script = find_main_script(page)
        source = await _read(client, script, 16 * 1024 * 1024)
        return await asyncio.to_thread(parse_public_api_key, source)
    finally:
        if owned:
            await client.close()
