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

cleanup_repowise_editor_files() {
  local file
  for file in "${repo_root}/.mcp.json" "${repo_root}/.vscode/mcp.json" "${repo_root}/.vscode/extensions.json"; do
    if [[ -f "${file}" ]] && grep -qi 'repowise' "${file}"; then
      rm -f "${file}"
    fi
  done
  if [[ -d "${repo_root}/.vscode" ]] && [[ -z "$(find "${repo_root}/.vscode" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
    rmdir "${repo_root}/.vscode"
  fi
}

set +e
"${venv_dir}/bin/repowise" "$@"
status=$?
set -e
cleanup_repowise_editor_files
exit "${status}"
