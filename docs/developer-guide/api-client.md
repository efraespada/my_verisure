# API clients (GraphQL)

All HTTP traffic uses **`aiohttp`** asynchronous sessions inside client classes derived from [`BaseClient`](../../custom_components/my_verisure/core/api/base_client.py).

## Endpoint

Configured in [`core/api/fields.py`](../../custom_components/my_verisure/core/api/fields.py):

`VERISURE_GRAPHQL_URL = https://customers.verisure.es/owa-api/graphql`

`fields.py` supplies the endpoint and native version constants used by the clients.

## Headers / auth

`BaseClient` builds:

- JSON content type  
- Native login/refresh headers and embedded-web data headers, matching their observed roles
- **`auth` header** JSON payload including `hash` token from `SessionManager`

## Clients

| Client | Responsibility |
|--------|----------------|
| `AuthClient` | Login, OTP, session lifecycle |
| `InstallationClient` | Installations, services |
| `AlarmClient` | Alarm status, arm/disarm mutations |
| `CameraClient` | Pending photo, optional push completion, polling and exact image retrieval |
| `PushReceiver` | Google registration, MCS reception and private credential reuse |

Exact GraphQL strings live alongside each client implementation — treat them as **vendor-private** and subject to change.

## Errors

Raised as `MyVerisure*` exceptions from [`api/exceptions.py`](../../custom_components/my_verisure/core/api/exceptions.py); coordinators translate them into HA exceptions.

## Entry-scoped native profile

A shared `ProfileContext` keeps login, refresh, SMS and data clients consistent.
Existing entries default to OWI. Enabling immediate updates binds the receiver's
FCM token as `idDevice` with OWA while retaining the UUID. Disabling the listener
retains that verified profile and polling. No captured account identifier or
Indigitall registration is required.
