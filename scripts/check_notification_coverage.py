"""Require complete executable line/branch coverage of notification modules.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import json
from pathlib import Path
import sys

MODULES = (
    "core/api/notification_client.py",
    "core/api/notification_mapper.py",
    "core/api/provider_request_gate.py",
    "core/application/notifications.py",
    "core/application/notification_refresh.py",
    "core/application/notification_verification.py",
    "event.py",
    "notification_context.py",
    "notification_runtime.py",
    "push.py",
)


def main() -> int:
    report = json.loads(Path(sys.argv[1]).read_text())
    if report.get("meta", {}).get("branch_coverage") is not True:
        print(
            "NOTIFICATION_COVERAGE_FAILED: branch coverage is required", file=sys.stderr
        )
        return 1
    failures = []
    for module in MODULES:
        path = "custom_components/my_verisure/" + module
        result = report.get("files", {}).get(path)
        if result is None or result["missing_lines"] or result["missing_branches"]:
            failures.append(path)
    if failures:
        print("NOTIFICATION_COVERAGE_FAILED: " + ", ".join(failures), file=sys.stderr)
        return 1
    print(
        f"NOTIFICATION_COVERAGE_OK: {len(MODULES)} modules, "
        "100% executable lines and branches"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
