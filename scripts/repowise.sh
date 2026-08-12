#!/usr/bin/env bash
# Run Repowise without contaminating the Home Assistant development environment.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv_dir="${REPOWISE_VENV:-${repo_root}/.repowise-venv}"
requirements_file="${repo_root}/requirements-repowise.txt"

if [[ ! -x "${venv_dir}/bin/repowise" ]]; then
  python3 -m venv "${venv_dir}"
  "${venv_dir}/bin/python" -m pip install --disable-pip-version-check -r "${requirements_file}"
fi

export REPOWISE_SKIP_EDITOR_SETUP=1
exec "${venv_dir}/bin/repowise" "$@"
