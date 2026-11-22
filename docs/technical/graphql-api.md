# GraphQL API

**Endpoint:** `https://customers.verisure.es/owa-api/graphql` (`VERISURE_GRAPHQL_URL`).

## Transport

[`BaseClient`](../../custom_components/my_verisure/core/api/base_client.py) issues POST requests with JSON payloads `{ "query": ..., "variables": ... }` via **aiohttp**.

## Headers

Native authentication uses `App`/`Extension` metadata; embedded-web data calls
use their observed transport headers and serialized `auth` context. The selected
entry-owned profile supplies consistent OWI/OWA identifiers for login, refresh,
SMS and data calls. Account/session values stay private.

## Queries / mutations

Concrete GraphQL documents reside beside each specialized client (`AuthClient`, `AlarmClient`, …). Treat them as **private contracts** — upstream may change field names without notice.

## Errors

HTTP/API failures normalize into `MyVerisure*` exceptions ([exceptions.py](../../custom_components/my_verisure/core/api/exceptions.py)).
