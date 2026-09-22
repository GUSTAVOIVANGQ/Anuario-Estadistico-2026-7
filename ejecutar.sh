#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
venv_python="$project_root/.venv/bin/python"

if [[ ! -x "$venv_python" ]]; then
  printf '%s\n' "No existe .venv. Ejecuta primero: ./preparar_entorno.sh" >&2
  exit 1
fi

export PYTHONPATH="$project_root/src"
exec "$venv_python" -m anuario2026 "$@"
