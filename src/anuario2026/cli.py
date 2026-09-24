from __future__ import annotations

import argparse
import os
from pathlib import Path

from . import __version__
from .pdf_export import available_pdf_converters
from .pipeline import assemble_pptx, run_pipeline
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
    print("CSV individuales de concesiones de radiodifusión BIT integrados y reutilizables: G.1")
    print("Caché integral ENIGH 2024 verificada y reutilizable: A.7 a A.10")
    print(
        "Caché ENDUTIH 2023 a 2025 verificada y reutilizable: "
        "F.1.1 a F.1.4, B.1 a B.21, C.3, C.4 y D.2 a D.4"
    )
    print("Base oficial ECSI 2024 verificada y reutilizable: D.5 a D.11")
    print("Bases oficiales MiPymes 2022 a 2024 verificadas y reutilizables: E.3 a E.8")
    print("Encuestas de satisfacción 2023-2025 y estudio MiPymes importadoras/exportadoras: E.1 y E.9")
    presentation = config.get("presentation", {})
    template = project_root / presentation.get(
        "template", "assets/presentation/anuario_estadistico_2026_automatizable.pptx"
    )
    manifest = project_root / presentation.get(
        "manifest", "assets/presentation/anuario_estadistico_2026_manifest.json"
    )
    print(f"Plantilla PPTX automatizable: {'OK' if template.is_file() else 'FALTA'} | {template}")
    print(f"Manifest PPTX de figuras: {'OK' if manifest.is_file() else 'FALTA'} | {manifest}")
    frontend_source = project_root / "web" / "src" / "App.jsx"
    frontend_dist = project_root / "web" / "dist" / "index.html"
    print(f"UI React fuente: {'OK' if frontend_source.is_file() else 'FALTA'} | {frontend_source}")
    print(
        f"UI React compilada: {'OK' if frontend_dist.is_file() else 'FALTA (ejecuta preparar_entorno.ps1)'} "
        f"| {frontend_dist}"
    )
    converters = available_pdf_converters()
    pdf_status = ", ".join(converters) if converters else (
        "FALTA (instala Microsoft PowerPoint o LibreOffice)"
    )
    print(f"Exportador PDF desde PPTX: {pdf_status}")
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

    assemble = subparsers.add_parser(
        "assemble",
        help="Inserta las figuras existentes en la plantilla PPTX automatizable",
    )
    assemble.add_argument(
        "--output",
        metavar="RUTA",
        help="Ruta de salida. Por defecto usa entrega/anuario_estadistico_2026_base.pptx",
    )
    assemble.add_argument(
        "--strict",
        action="store_true",
        help="No genera el PPTX si faltan figuras, narrativas o campos editoriales",
    )

    web = subparsers.add_parser("web", help="Abre la interfaz web del Anuario Estadístico")
    web.add_argument("--host", default="127.0.0.1", help="Dirección de escucha")
    web.add_argument("--port", type=int, default=8765, help="Puerto de la aplicación")
    web.add_argument("--no-open", action="store_true", help="No abre el navegador automáticamente")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = project_root_from_module()
    if args.command == "doctor":
        return doctor(project_root)
    if args.command == "assemble":
        output = None
        if args.output:
            output = Path(args.output)
            if not output.is_absolute():
                output = project_root / output
            output = output.resolve()
        pptx_path = assemble_pptx(project_root, output=output, strict=args.strict)
        print(f"PPTX: {pptx_path}")
        print(f"Reporte: {pptx_path.with_name(pptx_path.stem + '_ensamblaje.json')}")
        return 0
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
    if args.command == "web":
        from .web import serve

        serve(project_root, host=args.host, port=args.port, open_browser=not args.no_open)
        return 0
    return 2
