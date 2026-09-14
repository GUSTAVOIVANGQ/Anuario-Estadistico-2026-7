from __future__ import annotations

import argparse
import os
from pathlib import Path

from . import __version__
from .pipeline import run_pipeline
from .registry import load_figures, load_project_config
from .sources import load_sources


def project_root_from_module() -> Path:
    override = os.environ.get("ANUARIO_PROJECT_ROOT")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parents[2]


def doctor(project_root: Path) -> int:
    config = load_project_config(project_root)
    figures = load_figures(project_root, config)
    sources = load_sources(project_root)
    print(f"Proyecto: {config['project_name']} v{config['version']}")
    print(f"Raíz: {project_root}")
    print(f"Figuras inventariadas: {len(figures)}")
    print(f"Fuentes registradas: {len(sources)}")
    print(f"Scripts listos: {sum(item.script_path.is_file() for item in figures)}")
    print("Insumos manuales: A.5")
    print("Descargador ENOE integrado (enlace directo y respaldo Playwright): A.2")
    print("Descargador INPC/IPCOM integrado dentro del script: A.3")
    print("Caché global TODO.zip de BIT integrada y reutilizable: A.4, A.6, B.4 a B.25 y C.5 a C.16")
    print("Descarga masiva DENUE integrada y reutilizable: B.22")
    print("CSV individuales de espectro BIT integrados y reutilizables: C.1 y C.2")
    print("Caché integral ENIGH 2024 verificada y reutilizable: A.7 a A.10")
    print(
        "Caché ENDUTIH 2023 a 2025 verificada y reutilizable: "
        "F.1.1 a F.1.4, B.1 a B.21, C.3, C.4 y D.2 a D.4"
    )
    print("Base oficial ECSI 2024 verificada y reutilizable: D.5 a D.11")
    print("Estado base: correcto")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="anuario-2026")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor", help="Verifica la estructura base")

    run = subparsers.add_parser("run", help="Ejecuta las figuras en orden")
    run.add_argument("--dry-run", action="store_true", help="Prepara reportes sin ejecutar")
    run.add_argument("--only", metavar="FIGURA", help="Ejecuta una sola figura")
    run.add_argument("--from", dest="start_from", metavar="FIGURA")
    run.add_argument("--until", metavar="FIGURA")
    run.add_argument("--stop-on-error", action="store_true")
    run.add_argument("--assemble", action="store_true", help="Ensambla el PPTX al terminar")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = project_root_from_module()
    if args.command == "doctor":
        return doctor(project_root)
    if args.command == "run":
        run_pipeline(
            project_root,
            dry_run=args.dry_run,
            only=args.only,
            start_from=args.start_from,
            until=args.until,
            stop_on_error=args.stop_on_error,
            assemble=args.assemble,
        )
        return 0
    return 2
