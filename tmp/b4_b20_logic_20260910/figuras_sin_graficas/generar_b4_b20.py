# -*- coding: utf-8 -*-
"""Genera en secuencia las figuras B.4 a B.20."""
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent

for n in range(4, 21):
    script = HERE / f"figura_b{n}.py"
    print(f"\n=== Generando B.{n}: {script.name} ===")
    subprocess.run([sys.executable, str(script)], check=True)

print("\nListo: figuras B.4 a B.20 generadas.")
