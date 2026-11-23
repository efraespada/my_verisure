#!/usr/bin/env bash
# Run the primary offline gate with the matching official HA test harness.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HA_PYTHON="${HA_PYTHON:-${REPO_ROOT}/.ha-2026.11-venv/bin/python}"
HA_CORE="${HA_CORE-}"

if [[ "${HA_PYTHON}" != */* ]]; then
  HA_PYTHON="$(command -v "${HA_PYTHON}" || true)"
fi
if [[ ! -x "${HA_PYTHON}" ]]; then
  echo "ERROR: HA_PYTHON is not executable: ${HA_PYTHON}" >&2
  exit 2
fi
if [[ -n "${HA_CORE}" && ! -f "${HA_CORE}/pyproject.toml" ]]; then
  echo "ERROR: HA_CORE is not a Home Assistant checkout" >&2
  exit 2
fi
if [[ -n "${HA_CORE}" ]]; then
  export PYTHONPATH="${HA_CORE}:${REPO_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
else
  export PYTHONPATH="${REPO_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
fi

"${HA_PYTHON}" - <<'PY'
from importlib.metadata import PackageNotFoundError, version
import sys


def installed(name):
    try:
        return version(name)
    except PackageNotFoundError:
        return None


if installed("pytest-homeassistant-custom-component") is not None:
    raise SystemExit(
        "ERROR: the legacy HA harness is installed; use a fresh primary environment "
        "with pytest-homeassistant only (do not co-install both harnesses)"
    )
for name, expected in (
    ("homeassistant", "2026.11.2"),
    ("pytest-homeassistant", "2026.11.2"),
):
    actual = installed(name)
    if actual != expected:
        raise SystemExit(f"ERROR: expected {name} {expected}, got {actual}")
if sys.version_info < (3, 14, 2):
    raise SystemExit("ERROR: Python >=3.14.2 is required")
from homeassistant.const import __version__
if __version__ != "2026.11.2":
    raise SystemExit(f"ERROR: imported HA source is {__version__}, expected 2026.11.2")
import turbojpeg
print(
    f"Home Assistant {__version__} | Python {sys.version.split()[0]} | "
    "pytest-homeassistant 2026.11.2 (primary)"
)
PY

cd "${REPO_ROOT}"
exec "${HA_PYTHON}" -m pytest -c pytest.ini -q "$@"
