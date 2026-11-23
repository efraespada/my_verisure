"""Reject misleading scope omissions and coverage regressions.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from copy import deepcopy
import json

import pytest

from scripts import check_project_coverage as gate


@pytest.fixture
def complete_report(tmp_path):
    files = {}
    for scope in gate.FLOORS:
        file = tmp_path / scope / "production.py"
        file.parent.mkdir(parents=True)
        file.write_text("value = 1\n", encoding="utf-8")
        files[f"{scope}/production.py"] = {
            "summary": {
                "covered_lines": 100,
                "num_statements": 100,
                "covered_branches": 100,
                "num_branches": 100,
            }
        }
        test = tmp_path / scope / "tests" / "test_excluded.py"
        test.parent.mkdir()
        test.write_text("assert False\n", encoding="utf-8")
    for module in gate.COMPLETE_MODULES:
        name = f"custom_components/my_verisure/{module}"
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("value = 1\n")
        files[name] = {
            "summary": {
                "covered_lines": 1,
                "num_statements": 1,
                "covered_branches": 1,
                "num_branches": 1,
            },
            "missing_lines": [],
            "missing_branches": [],
        }
    return {"meta": {"branch_coverage": True}, "files": files}


def test_complete_measurement_accepts_all_three_scopes(tmp_path, complete_report):
    assert gate.check_coverage(complete_report, tmp_path) == []


def test_statement_only_coverage_is_not_accepted(tmp_path, complete_report):
    complete_report["meta"]["branch_coverage"] = False
    assert gate.check_coverage(complete_report, tmp_path) == [
        "branch measurement is required"
    ]


@pytest.mark.parametrize("dimension", ["missing_lines", "missing_branches"])
def test_critical_module_missing_path_fails_even_with_high_totals(
    tmp_path, complete_report, dimension
):
    name = f"custom_components/my_verisure/{gate.COMPLETE_MODULES[0]}"
    complete_report["files"][name][dimension] = [1]
    assert "complete executable" in gate.check_coverage(complete_report, tmp_path)[0]


@pytest.mark.parametrize("scope", gate.FLOORS)
def test_omitting_a_scope_cannot_make_the_result_look_better(
    tmp_path, complete_report, scope
):
    del complete_report["files"][f"{scope}/production.py"]
    assert "files missing" in gate.check_coverage(complete_report, tmp_path)[0]


@pytest.mark.parametrize("scope", gate.FLOORS)
@pytest.mark.parametrize("kind", ["covered_lines", "covered_branches"])
def test_each_scope_blocks_line_and_branch_regressions(
    tmp_path, complete_report, scope, kind
):
    complete_report["files"][f"{scope}/production.py"]["summary"][kind] = 0
    assert "required" in gate.check_coverage(complete_report, tmp_path)[0]


def test_missing_source_tree_is_an_error(tmp_path, complete_report):
    (tmp_path / "cli/production.py").unlink()
    assert "source is missing" in gate.check_coverage(complete_report, tmp_path)[0]


def test_empty_denominators_cannot_bypass_the_gate(tmp_path, complete_report):
    for key in complete_report["files"]["cli/production.py"]["summary"]:
        complete_report["files"]["cli/production.py"]["summary"][key] = 0
    assert "0.00%" in gate.check_coverage(complete_report, tmp_path)[0]


def test_main_reports_success_and_failure(
    tmp_path, complete_report, monkeypatch, capsys
):
    report_file = tmp_path / "report.json"
    report_file.write_text(json.dumps(complete_report))
    monkeypatch.setattr(gate.sys, "argv", ["check", str(report_file)])
    check = gate.check_coverage
    monkeypatch.setattr(gate, "check_coverage", lambda report: check(report, tmp_path))
    assert gate.main() == 0
    assert "PROJECT_COVERAGE_OK" in capsys.readouterr().out
    bad_report = deepcopy(complete_report)
    bad_report["files"] = {}
    report_file.write_text(json.dumps(bad_report))
    assert gate.main() == 1
    assert "PROJECT_COVERAGE_FAILED" in capsys.readouterr().err
    report_file.write_text("{")
    assert gate.main() == 1
