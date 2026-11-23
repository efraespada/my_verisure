"""The notification gate must fail when either executable dimension is missing.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import json

import pytest

from scripts import check_notification_coverage as gate


@pytest.mark.parametrize(
    "missing", [None, "line", "branch", "module", "branch_measurement"]
)
def test_notification_coverage_contract(tmp_path, monkeypatch, capsys, missing):
    report = {
        "meta": {"branch_coverage": missing != "branch_measurement"},
        "files": {
            "custom_components/my_verisure/" + name: {
                "missing_lines": [],
                "missing_branches": [],
            }
            for name in gate.MODULES
        },
    }
    module = next(iter(report["files"]))
    if missing == "line":
        report["files"][module]["missing_lines"] = [10]
    elif missing == "branch":
        report["files"][module]["missing_branches"] = [[10, 12]]
    elif missing == "module":
        del report["files"][module]
    report_file = tmp_path / "report.json"
    report_file.write_text(json.dumps(report))
    monkeypatch.setattr(gate.sys, "argv", ["check", str(report_file)])

    assert gate.main() == (0 if missing is None else 1)
    captured = capsys.readouterr()
    assert ("NOTIFICATION_COVERAGE_OK" in captured.out) is (missing is None)
