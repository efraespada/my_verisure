# Config flow

Implemented in [`config_flow.py`](../../custom_components/my_verisure/config_flow.py).

## Steps

| Step ID | Purpose |
|---------|---------|
| `user` | Collect username/password; attempt login |
| `phone_selection` | Pick OTP destination |
| `otp_verification` | Enter SMS code (`verify_otp`) |
| `installation` | Choose installation from list |
| `reauth` | Update stored credentials |

## Errors

Mapped to `errors["base"]`: `invalid_auth`, `cannot_connect`, `unknown`, OTP-specific strings, `installation_not_found`, etc.

## Options flow (`MyVerisureOptionsFlowHandler`)

The `init` form exposes polling, supplementary perimeter, push reception,
notification observation, selective state reads, external photos and the advanced
bus. See [configuration](../user-guide/configuration.md) for defaults and option
dependencies. Invalid combinations preserve the submitted form for correction.

## Reauthentication and lifetime

Reauthentication updates the existing entry and continues through device-bound
phone/SMS steps when required; it does not require deleting the integration.
Successful verification is followed by native login. Session publication is
transactional with persistence; failure restores the prior state.

A flow owns an isolated `CompositionRoot`, and a loaded entry owns a separate
runtime graph. See [dependency injection](dependency-injection.md). Real HA
flow tests cover selection, OTP failures, reauthentication and reload outcomes.
