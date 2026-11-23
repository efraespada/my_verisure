# FAQ

## Does this replace the old `verisure` Python library?

This integration uses **direct GraphQL** clients under `custom_components/my_verisure/core/api/` — not the legacy `verisure` PyPI package.

## Can I configure everything in YAML?

Initial setup is **UI only** (Config Flow). Options (poll interval, perimeter flags) are edited in the integration **Options** dialog.

## What is the default poll interval?

**10 minutes** (`DEFAULT_SCAN_INTERVAL` in `core/const.py`), unless changed in options.

## Do I need an alarm code to disarm?

The HA alarm **panel entity** is configured without required codes. Disarm is executed through the vendor API; there is **no** validated `code` field on the `my_verisure.disarm` service schema (optional read in code only).

## Does it work outside Spain?

The configured GraphQL endpoint is **`customers.verisure.es`**. Other regions may use different endpoints — **not supported** by this fork unless you change constants and verify API compatibility yourself.

## Can I stream video?

No — camera entities expose **snapshot images** from stored files, not RTSP/WebRTC streams.

## Multiple houses / installations?

Add **one config entry per installation** from the same account (each picks a different installation in the flow). Watch for **alarm panel `unique_id`** collisions ([Entities](entities.md)).
