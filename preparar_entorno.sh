#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python_command="${PYTHON_EXECUTABLE:-python3}"
venv_python="$project_root/.venv/bin/python"

if [[ ! -x "$venv_python" ]]; then
  "$python_command" -c "import venv"
  "$python_command" -m venv "$project_root/.venv"
fi

"$venv_python" -m pip install --upgrade pip
"$venv_python" -m pip install -e "$project_root"

if command -v npm >/dev/null 2>&1; then
  (
    cd "$project_root/web"
    npm install --no-audit --no-fund
    npm run build
  )
else
  printf '%s\n' "Aviso: la interfaz React necesita Node.js 20 o superior y npm."
fi

if command -v soffice >/dev/null 2>&1 || command -v libreoffice >/dev/null 2>&1; then
  printf '%s\n' "Conversión PPTX a PDF disponible: LibreOffice."
else
  printf '%s\n' "Aviso: instala LibreOffice para habilitar la descarga PDF desde el PPTX."
fi

printf '%s\n' "Entorno listo."
printf '%s\n' "Diagnóstico: ./ejecutar.sh doctor"
printf '%s\n' "Interfaz web: ./ejecutar.sh web"
