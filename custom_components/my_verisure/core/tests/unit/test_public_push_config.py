"""Public client discovery without copying provider API keys into source.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import pytest

from custom_components.my_verisure.core.api.push_config import (
    APP_ID, MESSAGING_SENDER_ID, PROJECT_ID,
)
from custom_components.my_verisure.core.api.public_push_config import (
    async_resolve_public_api_key, find_main_script, parse_public_api_key,
)

HOME = "https://customers.verisure.es/owa-static/home"
SCRIPT = "https://customers.verisure.es/3.8.0/static/js/main.synthetic.js"


def bundle(project=PROJECT_ID, key="synthetic-public-client-key"):
    return (
        f'REACT_APP_FIREBASE_PROJECT_ID:"{project}",'
        f'REACT_APP_FIREBASE_APP_ID:"{APP_ID}",'
        f'REACT_APP_FIREBASE_MESSAGING_SENDER_ID:"{MESSAGING_SENDER_ID}",'
        f'REACT_APP_FIREBASE_API_KEY:"{key}"'
    )


def test_public_script_and_configuration_match_known_project():
    assert find_main_script('<script src="/3.8.0/static/js/main.synthetic.js"></script>') == SCRIPT
    assert parse_public_api_key(bundle()) == "synthetic-public-client-key"


@pytest.mark.parametrize("src", [
    "http://customers.verisure.es/3.8.0/static/js/main.synthetic.js",
    "https://other.example/3.8.0/static/js/main.synthetic.js",
    "https://user@customers.verisure.es/3.8.0/static/js/main.synthetic.js",
    "https://customers.verisure.es:444/3.8.0/static/js/main.synthetic.js",
    "https://customers.verisure.es/3.8.0/static/js/main.synthetic.js?redirect=other",
    "https://customers.verisure.es/3.8.0/static/js/main.synthetic.js#other",
])
def test_foreign_or_insecure_script_is_rejected(src):
    with pytest.raises(ValueError):
        find_main_script(f'<script src="{src}"></script>')


@pytest.mark.parametrize("html", [
    '<script src="/3.8.0/static/js/415.chunk.js"></script>',
    '<script src="/3.8.0/static/js/main.first.js"></script>'
    '<script src="/3.8.0/static/js/main.second.js"></script>',
])
def test_missing_or_ambiguous_main_asset_is_rejected(html):
    with pytest.raises(ValueError):
        find_main_script(html)


@pytest.mark.parametrize("source", [
    bundle(project="other-project"), bundle(key="invalid key text"), "missing",
    bundle() + ',REACT_APP_FIREBASE_API_KEY:"different-synthetic-key"',
    bundle().replace(APP_ID, "foreign-application"),
    bundle().replace(MESSAGING_SENDER_ID, "123456789"),
])
def test_invalid_or_ambiguous_configuration_fails_without_echoing_value(source):
    with pytest.raises(ValueError) as failure:
        parse_public_api_key(source)
    assert "different-synthetic-key" not in str(failure.value)


class Response:
    def __init__(self, body, status=200):
        self.body = body.encode()
        self.status = status
        self.content = self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def iter_chunked(self, size):
        yield self.body


class Session:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return next(self.responses)


@pytest.mark.asyncio
async def test_resolution_reads_only_public_get_endpoints():
    session = Session([
        Response('<script src="/3.8.0/static/js/main.synthetic.js"></script>'),
        Response(bundle()),
    ])
    assert await async_resolve_public_api_key(session) == "synthetic-public-client-key"
    assert [url for url, options in session.calls] == [HOME, SCRIPT]
    assert all(options["allow_redirects"] is False for url, options in session.calls)
    assert all("Authorization" not in options["headers"] for url, options in session.calls)


@pytest.mark.asyncio
@pytest.mark.parametrize("response", [
    Response("blocked", 403), Response("redirect", 302), Response("x" * (1024 * 1024 + 1)),
])
async def test_failed_or_oversized_public_page_stops_before_script(response):
    session = Session([response])
    with pytest.raises(ValueError):
        await async_resolve_public_api_key(session)
    assert len(session.calls) == 1
