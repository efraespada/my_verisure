"""Tests for OTP authorization policy."""

from custom_components.my_verisure.core.application.otp_authorization import (
    OTPAuthorizationPolicy,
)


def test_prepare_normalizes_phone_metadata_without_mutating_input():
    source = {
        "auth-phones": [{"id": 7, "phone": "+34 ***"}],
        "auth-otp-hash": "hash",
    }

    prepared = OTPAuthorizationPolicy().prepare(source)

    assert prepared is not None
    assert prepared.otp_hash == "hash"
    assert prepared.phones[0].id == 7
    assert prepared.phones[0].record_id == 7
    assert prepared.phones[0].otp_hash == "hash"
    assert source["auth-phones"][0] == {"id": 7, "phone": "+34 ***"}


def test_prepare_rejects_missing_or_invalid_metadata():
    policy = OTPAuthorizationPolicy()

    assert policy.prepare({}) is None
    assert policy.prepare({"auth-phones": [], "auth-otp-hash": "hash"}) is None
    assert policy.prepare({"auth-phones": [{"id": 1}], "auth-otp-hash": ""}) is None


def test_select_phone_returns_only_matching_phone():
    policy = OTPAuthorizationPolicy()
    prepared = policy.prepare(
        {
            "auth-phones": [{"id": 1, "phone": "one"}, {"id": 2, "phone": "two"}],
            "auth-otp-hash": "hash",
        }
    )

    assert prepared is not None
    assert policy.select_phone(prepared.phones, 2) is prepared.phones[1]
    assert policy.select_phone(prepared.phones, 99) is None
