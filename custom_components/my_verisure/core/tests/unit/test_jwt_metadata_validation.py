"""Exercise JWT metadata guards using real encoded payloads and decoder seams.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import base64
import json
import runpy
from unittest.mock import Mock, patch

import jwt
import pytest

from ...utils import jwt_utils
from ...file_manager import FileManager
from ...session_manager import SessionManager, TOKEN_MAX_AGE_SECONDS


def _json_token(payload):
    def segment(value):
        return (
            base64.urlsafe_b64encode(json.dumps(value).encode()).rstrip(b"=").decode()
        )

    return f"{segment({'alg': 'none', 'typ': 'JWT'})}.{segment(payload)}."


@pytest.mark.parametrize(
    "expiration",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
        True,
        False,
        "9999999999",
        None,
        [],
        {},
    ],
)
def test_invalid_expiration_in_real_json_token_is_expired(expiration):
    token = _json_token({"exp": expiration})
    assert jwt_utils.is_jwt_expired(token) is True


def test_missing_decoder_does_not_make_a_token_valid():
    with patch.object(jwt_utils, "jwt", None):
        assert jwt_utils.is_jwt_expired("token") is True
        assert jwt_utils.get_jwt_payload("token") is None


@pytest.mark.parametrize(
    "payload", [None, [], ["exp"], "metadata", 123, False, {1: "bad-key"}]
)
def test_decoder_output_must_be_a_json_mapping(payload):
    decoder = Mock(decode=Mock(return_value=payload))
    with patch.object(jwt_utils, "jwt", decoder):
        assert jwt_utils.get_jwt_payload("token") is None
        assert jwt_utils.is_jwt_expired("token") is True


@pytest.mark.parametrize(
    "token",
    [
        None,
        False,
        123,
        b"token",
        [],
        {},
        "",
        "é",
        pytest.param("x" * 65537, id="over-64k"),
    ],
)
def test_invalid_or_oversized_token_is_rejected_before_decode(token):
    decoder = Mock(decode=Mock(return_value={"exp": 9999999999}))
    with patch.object(jwt_utils, "jwt", decoder):
        assert jwt_utils.get_jwt_payload(token) is None
        assert jwt_utils.is_jwt_expired(token) is True
    decoder.decode.assert_not_called()


def test_token_at_size_limit_reaches_decoder():
    token = "x" * 65536
    decoder = Mock(decode=Mock(return_value={"exp": 9999999999}))
    with patch.object(jwt_utils, "jwt", decoder):
        assert jwt_utils.get_jwt_payload(token) == {"exp": 9999999999}
    decoder.decode.assert_called_once_with(token, options={"verify_signature": False})


@pytest.mark.parametrize("leeway", [float("nan"), float("inf"), True, -1, "30", None])
def test_invalid_early_refresh_margin_fails_closed(leeway):
    token = _json_token({"exp": 9999999999})
    assert jwt_utils.is_jwt_expired(token, leeway=leeway) is True


@pytest.mark.parametrize(
    "now,expired", [(969.999, False), (970.0, True), (970.001, True), (1000.0, True)]
)
def test_exact_early_refresh_boundary_uses_real_pyjwt_token(now, expired):
    token = jwt.encode({"exp": 1000, "sub": "synthetic-user"}, key="", algorithm="none")
    with patch.object(jwt_utils.time, "time", return_value=now):
        assert jwt_utils.is_jwt_expired(token, leeway=30) is expired


def test_missing_expiration_remains_legacy_metadata_with_an_independent_session_ttl():
    token = _json_token({"sub": "synthetic-user"})
    assert jwt_utils.get_jwt_payload(token) == {"sub": "synthetic-user"}
    assert jwt_utils.is_jwt_expired(token) is False


@pytest.mark.parametrize("age,valid", [(1, True), (TOKEN_MAX_AGE_SECONDS + 1, False)])
def test_no_expiration_claim_still_respects_the_real_session_age_limit(
    tmp_path, age, valid
):
    session = SessionManager(file_manager=FileManager(tmp_path))
    session.hash_token = _json_token({"sub": "synthetic-user"})
    session.session_timestamp = 10000 - age
    with patch.object(jwt_utils.time, "time", return_value=10000):
        assert session.is_session_valid() is valid


def test_each_decode_receives_fresh_options_for_unverified_metadata_only():
    options_seen = []

    def decode(_token, *, options):
        assert options == {"verify_signature": False}
        options_seen.append(options)
        options["verify_signature"] = True
        return {"sub": "synthetic-user"}

    with patch.object(jwt_utils, "jwt", Mock(decode=decode)):
        jwt_utils.get_jwt_payload("first")
        jwt_utils.get_jwt_payload("second")
    assert options_seen[0] is not options_seen[1]


@pytest.mark.parametrize("payload", [[], None, "metadata", 42, True])
def test_real_non_object_json_token_is_not_payload_metadata(payload):
    token = _json_token(payload)
    assert jwt_utils.get_jwt_payload(token) is None
    assert jwt_utils.is_jwt_expired(token) is True


@pytest.mark.parametrize("now", [float("nan"), float("inf"), "970", True])
def test_invalid_clock_cannot_make_expiration_valid(now):
    token = _json_token({"exp": 1000})
    with patch.object(jwt_utils.time, "time", return_value=now):
        assert jwt_utils.is_jwt_expired(token) is True


def test_unrepresentable_numeric_expiration_fails_closed():
    token = _json_token({"exp": 10**400})
    assert jwt_utils.is_jwt_expired(token) is True


def test_finite_fractional_expiration_retains_exact_refresh_boundary():
    token = _json_token({"exp": 1000.5})
    with patch.object(jwt_utils.time, "time", return_value=970.499):
        assert jwt_utils.is_jwt_expired(token) is False
    with patch.object(jwt_utils.time, "time", return_value=970.5):
        assert jwt_utils.is_jwt_expired(token) is True


def test_expiration_requires_exact_numeric_types():
    class Expiration(int):
        pass

    decoder = Mock(decode=Mock(return_value={"exp": Expiration(9999999999)}))
    with patch.object(jwt_utils, "jwt", decoder):
        assert jwt_utils.is_jwt_expired("token") is True


def test_module_remains_fail_closed_when_jwt_import_is_unavailable():
    with patch("importlib.import_module", side_effect=ImportError("unavailable")):
        namespace = runpy.run_path(jwt_utils.__file__)
    assert namespace["jwt"] is None
    assert namespace["is_jwt_expired"]("token") is True
    assert namespace["get_jwt_payload"]("token") is None
