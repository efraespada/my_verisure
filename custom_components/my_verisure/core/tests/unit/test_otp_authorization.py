"""Tests for OTP authorization policy."""

import pytest

from custom_components.my_verisure.core.api.otp_authorization import (
    OTPAuthorizationPolicy,
)
from custom_components.my_verisure.core.application.otp_code_policy import is_valid_otp_code

HASH_SENTINEL = "HASH_SENTINEL"



@pytest.mark.parametrize("value", [None, "", "12345", "1234567", "12A456", " 123456"])
def test_otp_code_validator_rejects_invalid_codes(value):
    assert is_valid_otp_code(value) is False


def test_otp_code_validator_accepts_exact_six_digits():
    assert is_valid_otp_code("123456") is True


def test_prepare_normalizes_phone_metadata_without_mutating_input():
    source = {
        "auth-phones": [{"id": 7, "recordId": 70, "phone": "+34 ***"}],
        "auth-otp-hash": HASH_SENTINEL,
    }

    prepared = OTPAuthorizationPolicy().prepare(source)

    assert prepared is not None
    assert prepared.otp_hash == HASH_SENTINEL
    assert prepared.phones[0].id == 7
    assert prepared.phones[0].record_id == 70
    assert source["auth-phones"][0] == {
        "id": 7,
        "recordId": 70,
        "phone": "+34 ***",
    }


def test_prepare_rejects_missing_or_invalid_metadata():
    policy = OTPAuthorizationPolicy()

    assert policy.prepare({}) is None
    assert policy.prepare({"auth-phones": [], "auth-otp-hash": HASH_SENTINEL}) is None
    assert policy.prepare({"auth-phones": [{"id": 1}], "auth-otp-hash": ""}) is None


def test_prepare_rejects_missing_phone_record_id():
    prepared = OTPAuthorizationPolicy().prepare(
        {
            "auth-phones": [{"phone": "masked"}],
            "auth-otp-hash": HASH_SENTINEL,
        }
    )

    assert prepared is None


def test_select_phone_returns_only_matching_phone():
    policy = OTPAuthorizationPolicy()
    prepared = policy.prepare(
        {
            "auth-phones": [{"id": 1, "recordId": 11, "phone": "one"}, {"id": 2, "recordId": 12, "phone": "two"}],
            "auth-otp-hash": HASH_SENTINEL,
        }
    )

    assert prepared is not None
    assert policy.select_phone(prepared.phones, 2) is prepared.phones[1]
    assert policy.select_phone(prepared.phones, 99) is None


def test_prepare_rejects_conflicting_record_id_aliases():
    prepared = OTPAuthorizationPolicy().prepare(
        {
            "auth-phones": [
                {
                    "id": 7,
                    "recordId": 70,
                    "record_id": 71,
                    "phone": "PHONE_SENTINEL",
                }
            ],
            "auth-otp-hash": HASH_SENTINEL,
        }
    )

    assert prepared is None


@pytest.mark.parametrize("otp_hash", [123, {}, [], True])
def test_prepare_rejects_malformed_otp_hash(otp_hash):
    assert OTPAuthorizationPolicy().prepare(
        {
            "auth-phones": [{"id": 1, "phone": "PHONE_SENTINEL"}],
            "auth-otp-hash": otp_hash,
        }
    ) is None
