#!/usr/bin/env bash
# Run the integration gates against the pinned Home Assistant production target.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HA_PYTHON="${HA_PYTHON:-/tmp/ha-2026.8.1-venv/bin/python}"
HA_CORE="${HA_CORE:-/tmp/ha-core-2026.8.1}"

if [[ ! -x "${HA_PYTHON}" ]]; then
  echo "ERROR: HA_PYTHON is not executable: ${HA_PYTHON}" >&2
  exit 2
fi
if [[ ! -f "${HA_CORE}/pyproject.toml" ]]; then
  echo "ERROR: HA_CORE does not point to a Home Assistant checkout: ${HA_CORE}" >&2
  exit 2
fi

actual_ha="$(${HA_PYTHON} -c 'from importlib.metadata import version; print(version("homeassistant"))')"
actual_py="$(${HA_PYTHON} -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')"
actual_plugin="$(${HA_PYTHON} -c 'from importlib.metadata import version; print(version("pytest-homeassistant-custom-component"))')"

[[ "${actual_ha}" == "2026.8.1" ]] || { echo "ERROR: expected HA 2026.8.1, got ${actual_ha}" >&2; exit 3; }
[[ "${actual_plugin}" == "0.13.355" ]] || { echo "ERROR: expected pytest-homeassistant-custom-component 0.13.355, got ${actual_plugin}" >&2; exit 3; }
${HA_PYTHON} -c 'import sys; assert sys.version_info >= (3, 14, 2)'
${HA_PYTHON} -c 'import turbojpeg'

cd "${REPO_ROOT}"
export PYTHONPATH="${HA_CORE}:${REPO_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
printf 'Home Assistant %s | Python %s | pytest-homeassistant-custom-component %s\n' "${actual_ha}" "${actual_py}" "${actual_plugin}"
exec "${HA_PYTHON}" -m pytest -c pytest.ini -q "$@"
