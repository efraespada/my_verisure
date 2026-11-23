"""Development commands must select one gate and preserve private HA storage.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import json
import os
import runpy
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]


def _helper(tmp_path: Path, *, existing: bool = False) -> tuple[Path, Path, dict]:
    """Copy the helper and replace external programs with inert recorders."""
    helper = tmp_path / "dev"
    shutil.copy2(ROOT / "dev", helper)
    binaries = tmp_path / "bin"
    binaries.mkdir()
    log = tmp_path / "commands"
    for name in ("make", "docker"):
        recorder = binaries / name
        recorder.write_text(
            '#!/bin/sh\n'
            'printf "%s\\n" "$0" "$@" "HA_PYTHON=$HA_PYTHON" >> "$COMMAND_LOG"\n'
            'if [ "$1" = "container" ]; then exit "$CONTAINER_INSPECT_RESULT"; fi\n'
        )
        recorder.chmod(0o755)
    env = {
        **os.environ,
        "PATH": str(binaries) + os.pathsep + os.environ["PATH"],
        "COMMAND_LOG": str(log),
        "CONTAINER_INSPECT_RESULT": "0" if existing else "1",
    }
    for key in ("HA_PYTHON", "MAKEFLAGS", "MFLAGS", "MAKEOVERRIDES", "GNUMAKEFLAGS"):
        env.pop(key, None)
    return helper, log, env


@pytest.mark.parametrize(
    ("command", "target"),
    [
        ("test", "test-ha-2026-11"),
        ("coverage", "coverage"),
        ("check", "ci"),
        ("lint", "lint"),
        ("type-check", "type-check"),
    ],
)
def test_helper_delegates_to_canonical_gates(tmp_path, command, target):
    helper, log, env = _helper(tmp_path)
    subprocess.run([str(helper), command], env=env, check=True, capture_output=True)
    lines = log.read_text().splitlines()
    assert lines[1] == target
    assert lines[2] == f"HA_PYTHON={tmp_path}/.ha-2026.11-venv/bin/python"


def test_helper_preserves_explicit_validation_interpreter(tmp_path):
    helper, log, env = _helper(tmp_path)
    env["HA_PYTHON"] = "/synthetic/external-env/bin/python"
    subprocess.run([str(helper), "test"], env=env, check=True, capture_output=True)
    assert "HA_PYTHON=/synthetic/external-env/bin/python" in log.read_text()


def test_docker_start_reuses_existing_container_without_removal(tmp_path):
    helper, log, env = _helper(tmp_path, existing=True)
    subprocess.run(
        [str(helper), "docker-start"], env=env, check=True, capture_output=True
    )
    lines = log.read_text().splitlines()
    assert "start" in lines and "my_verisure_dev" in lines
    assert not {"rm", "run", "stop"}.intersection(lines)


def test_new_docker_configuration_is_private_persistent_and_pinned(tmp_path):
    helper, log, env = _helper(tmp_path)
    subprocess.run(
        [str(helper), "docker-start"], env=env, check=True, capture_output=True
    )
    lines = log.read_text().splitlines()
    assert "my_verisure_dev_config:/config" in lines
    assert "127.0.0.1:8123:8123" in lines
    assert "ghcr.io/home-assistant/home-assistant:2026.11.2" in lines
    assert (
        f"{tmp_path}/custom_components/my_verisure:"
        "/config/custom_components/my_verisure:ro"
    ) in lines
    assert "rm" not in lines


def test_docker_stop_keeps_configuration_and_container(tmp_path):
    helper, log, env = _helper(tmp_path)
    subprocess.run(
        [str(helper), "docker-stop"], env=env, check=True, capture_output=True
    )
    lines = log.read_text().splitlines()
    assert "stop" in lines and "my_verisure_dev" in lines
    assert "rm" not in lines


def test_make_and_validation_script_select_same_default_interpreter(tmp_path):
    """Check the real Makefile's expanded recipe without installing anything."""
    makefile = tmp_path / "Makefile"
    shutil.copy2(ROOT / "Makefile", makefile)
    env = dict(os.environ)
    for key in ("HA_PYTHON", "MAKEFLAGS", "MFLAGS", "MAKEOVERRIDES", "GNUMAKEFLAGS"):
        env.pop(key, None)
    result = subprocess.run(
        ["make", "-n", "test-ha-2026-11"], cwd=tmp_path, env=env,
        check=True, capture_output=True, text=True,
    )
    assert f'HA_PYTHON="{tmp_path}/.ha-2026.11-venv/bin/python"' in result.stdout
    assert "scripts/test-ha-2026.11.sh" in result.stdout
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    runner = scripts / "test-ha-2026.11.sh"
    shutil.copy2(ROOT / "scripts/test-ha-2026.11.sh", runner)
    result = subprocess.run(
        [str(runner)], cwd=tmp_path, env=env, capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert f"{tmp_path}/.ha-2026.11-venv/bin/python" in result.stderr


def test_devcontainer_uses_pinned_target_and_declared_environment():
    config = json.loads((ROOT / ".devcontainer/devcontainer.json").read_text())
    assert config["image"].endswith(":2026.11.2")
    assert "requirements-dev.txt" in config["postCreateCommand"]
    assert config["containerEnv"]["HA_PYTHON"] == (
        config["customizations"]["vscode"]["settings"]["python.defaultInterpreterPath"]
    )


def test_primary_gate_rejects_coinstalled_harness_metadata(tmp_path):
    """Fail clearly before pytest can load overlapping external plugins."""
    metadata = tmp_path / "pytest_homeassistant_custom_component-0.0.0.dist-info"
    metadata.mkdir()
    (metadata / "METADATA").write_text(
        "Metadata-Version: 2.1\n"
        "Name: pytest-homeassistant-custom-component\nVersion: 0.0.0\n"
    )
    env = {**os.environ, "PYTHONPATH": str(tmp_path), "HA_PYTHON": sys.executable}
    result = subprocess.run(
        [str(ROOT / "scripts/test-ha-2026.11.sh")], env=env,
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "do not co-install both harnesses" in result.stderr


@pytest.mark.parametrize("exit_code", [0, 7])
def test_cli_compatibility_runner_preserves_gate_result(monkeypatch, exit_code):
    namespace = runpy.run_path(str(ROOT / "cli/tests/run_tests.py"))
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, exit_code)

    monkeypatch.setattr(namespace["subprocess"], "run", run)
    assert namespace["main"]() == exit_code
    assert len(calls) == 1
    assert calls[0][0] == ["make", "test-cli"]
    assert calls[0][1]["cwd"] == ROOT
