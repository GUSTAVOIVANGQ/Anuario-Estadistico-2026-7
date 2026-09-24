"""Rescata H.1-H.14 del PDF 2024 sin atribuirles un corte 2026."""

from __future__ import annotations

import json
import re
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "anuarioestadistico2024vf_0.pdf"
MANIFEST = ROOT / "assets/presentation/anuario_estadistico_2026_manifest.json"
NARRATIVES = ROOT / "assets/presentation/narrativas_figuras_2026.json"
IMAGES = ROOT / "assets/reference/audiencias_2024"


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\ufb01", "fi").replace("\ufb02", "fl")).strip()


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    registry = json.loads(NARRATIVES.read_text(encoding="utf-8"))
    existing = {item["figure_id"]: item for item in registry["entries"]}
    IMAGES.mkdir(parents=True, exist_ok=True)
    with fitz.open(SOURCE) as pdf:
        for number in range(1, 15):
            page_number = 101 + number
            figure_id = f"H.{number}"
            page = pdf[page_number - 1]
            body = [
                block for block in page.get_text("blocks")
                if block[6] == 0 and 65 <= block[0] < 440 and 120 <= block[1] < 800
            ]
            body.sort(key=lambda block: block[1])
            text = "\n\n".join(clean(block[4]) for block in body)
            if len(text) < 60:
                raise ValueError(f"No se recuperó la narrativa {figure_id}")
            registry_entry = {
                "figure_id": figure_id,
                "source_pdf_page": page_number,
                "baseline_text_2024": text,
                "updated_text": text,
                "update_mode": "historical_replica",
                "notes": [
                    "Reproducción literal de la redacción 2024; periodo julio 2023-junio 2024.",
                    "No hay acceso a Nielsen IBOPE/MSS TV o INRA/INRAM para actualizar la figura.",
                ],
                "data_file": None,
                "data_sha256": None,
            }
            existing[figure_id] = registry_entry
            # El recorte comprende gráfica, leyenda, fuente y nota originales.
            clip = fitz.Rect(450, 125, 1550, 830)
            image = IMAGES / f"h_{number:02d}_2024.png"
            page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=clip, alpha=False).save(image)
            entry = next(item for item in manifest["entries"] if item["figure_id"] == figure_id)
            entry["historical_image"] = image.relative_to(ROOT).as_posix()
            entry["historical_period"] = "julio de 2023 a junio de 2024"
            entry["historical_source_pdf_page"] = page_number
    registry["entries"] = [existing[key] for key in sorted(existing, key=lambda key: (key.split(".")[0], [int(part) for part in key.split(".")[1:]]))]
    registry["figure_count"] = len(registry["entries"])
    NARRATIVES.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Audiencias históricas: 14; narrativas registradas: {len(registry['entries'])}")


if __name__ == "__main__":
    main()
