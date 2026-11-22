# Linux push decoder experiment

An offline decoder and synthetic regression for the encrypted FCM photo event
received during the owner-authorized experiment. The production HA integration
still uses polling. This directory is outside the installable custom component
and has no live registration, login or alarm-command entry point.

`decoder.py` preserves the functions used by the successful Linux receiver.
It parses named `dh`/salt parameters and base64url padding rather than assuming
Crypto-Key contains only a `dh=` prefix. `decode(record, credentials)` accepts
an in-memory MCS envelope/receiver key mapping and returns authenticated JSON;
this module performs no network or filesystem operations.

The supported observed encoding is legacy `aesgcm`. This is an experimental
extraction, not a general Web Push parser or a maintained replacement for the
upstream transport. Input limits, other encodings and production error/lifecycle
handling remain requirements in the draft specification.

Run the synthetic check in an isolated Python 3.14 environment:

```sh
python3.14 -m venv /tmp/my-verisure-push-check
/tmp/my-verisure-push-check/bin/pip install -r experiments/linux_push/requirements.txt
/tmp/my-verisure-push-check/bin/python experiments/linux_push/check_decoder.py
```

The check generates ephemeral EC keys, encrypts synthetic plaintext, verifies four
header/padding forms and reproduces the old firebase-messaging 0.4.5 decoder
failure. It requires no account, token, private capture or provider request.
The dependency pins reproduce the isolated probe; do not install them into HA's
managed environment. These checks are separate from the 834-test repository suite.

The private live harness and household data remain outside Git. See the
[technical evidence](../../docs/technical/push-reception-investigation.md),
[sanitized receipt](../../docs/validation/2026-11-22-linux-fcm.json) and
[draft specification](../../specs/linux-push-photo-completion.md).
