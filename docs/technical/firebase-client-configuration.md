# Public Firebase client configuration and alert #1

Reviewed: 2026-11-23. GitHub [secret-scanning alert #1](https://github.com/efraespada/my_verisure/security/secret-scanning/1)
identified a Google API-key literal in `core/api/push_config.py`, first published
in commit `c7195690e14cbe5e393525c8e56e196b33cfd009`.

## Classification and evidence

The value matches the Firebase configuration in Verisure's unauthenticated public
web client. Two bounded HTTPS GETs retrieved the entry page and its main asset;
the project, application, sender and client-key values matched the published
configuration. The [sanitized receipt](../validation/2026-11-23-public-firebase-config.json)
records the URLs, asset hash and comparison result without reproducing the key.
No account login, alarm command or Google registration was used in that check.

Firebase documents that its client API keys identify a project/application;
authorization depends on separate controls such as Security Rules, IAM and
App Check. See [Firebase API keys](https://firebase.google.com/docs/projects/api-keys)
and its [security checklist](https://firebase.google.com/support/guides/security-checklist).
This is public provider client configuration. It is not the owner's password,
Verisure access/refresh token, private receiver key, FCM server key or service-account
credential. The provider's Cloud key restrictions were not inspected, so this
review does not establish that the key is restricted correctly or harmless for
every Google service. Only the provider can audit or change those restrictions.

## Current implementation

The integration no longer embeds the provider client key. A new receiver resolves
it automatically from `https://customers.verisure.es/owa-static/home` and its
current same-origin main script. The adapter parses literal metadata without
executing JavaScript, requires the known project/application/sender, refuses
redirects and foreign or insecure assets, and limits time and response size.
The key stays in memory for SDK registration; it is not included in diagnostics,
logs or durable receiver credentials. No user-entered Firebase configuration is
required.

Valid durable receiver credentials skip these configuration GETs on startup and
ordinary transport reconnects. New registration or an actual MCS authentication
rejection can resolve the configuration. If discovery or validation fails,
polling remains available with the existing setup/reconnect backoff. A future
provider application/project migration requires review rather than silently
trusting a different Firebase project.

## Alert handling and verification limits

Classify this individual finding as public client configuration, with the public
source and comparison as evidence. Do not describe it as a revoked credential,
disable secret scanning, suppress all Google-key findings, or encode/split the
literal to evade detection. The original commit remains in Git history. Removing
the literal from current source does not erase that commit or revoke the provider's
key. No provider-owned key was rotated or revoked.

Focused synthetic regressions cover discovery, origin/size/status rejection,
configuration validation, failure before registration and cached startup without
configuration HTTP. The public-source comparison validates the new bootstrap
against production metadata. Earlier installed HA photo/polling/restart timings
refer to the preceding build; they are not a deployment test of this correction.

The correction is now installed with the notification implementation. Its 153
production files were verified on HA, and cached receiver credentials were reused
across restart and entry reload. One new photo completed in 23.22 seconds. This
does not add a fresh-registration bootstrap test; the production metadata GET
comparison and synthetic discovery coverage remain separate evidence. See the
[implementation receipt](../validation/2026-11-23-notification-implementation.json).
