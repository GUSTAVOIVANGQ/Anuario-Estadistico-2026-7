"""Pipeline reproducible del Anuario Estadístico 2026."""

import os
import sys
from pathlib import Path


# Un venv creado desde Anaconda en Windows no hereda siempre sus DLL de OpenSSL.
# Conservar el handle mantiene la ruta activa durante toda la corrida.
_conda_dll_handle = None
if os.name == "nt" and hasattr(os, "add_dll_directory"):
    _conda_dll_dir = Path(sys.base_prefix) / "Library" / "bin"
    if _conda_dll_dir.is_dir():
        _conda_dll_handle = os.add_dll_directory(str(_conda_dll_dir))

__version__ = "0.29.0"
