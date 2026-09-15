from __future__ import annotations

import json
import shutil
from pathlib import Path

from pptx import Presentation

from anuario2026.presentation import assemble_from_template


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_template_manifest_matches_placeholders() -> None:
    root = _project_root()
    config = json.loads((root / "config" / "proyecto.json").read_text(encoding="utf-8"))
    template = root / config["presentation"]["template"]
    manifest = json.loads(
        (root / config["presentation"]["manifest"]).read_text(encoding="utf-8")
    )
    presentation = Presentation(str(template))

    assert len(presentation.slides) == manifest["slide_count"] == 119
    assert len(manifest["entries"]) == manifest["figure_count"] == 105

    for entry in manifest["entries"]:
        slide = presentation.slides[entry["slide_number"] - 1]
        names = {shape.name for shape in slide.shapes}
        assert entry["figure_shape_name"] in names


def test_assemble_inserts_image_and_clears_token(tmp_path: Path) -> None:
    source_root = _project_root()
    project_root = tmp_path / "project"
    (project_root / "config").mkdir(parents=True)
    (project_root / "assets" / "presentation").mkdir(parents=True)
    (project_root / "build" / "figures" / "A").mkdir(parents=True)

    source_config = json.loads(
        (source_root / "config" / "proyecto.json").read_text(encoding="utf-8")
    )
    (project_root / "config" / "proyecto.json").write_text(
        json.dumps(source_config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    template_rel = Path(source_config["presentation"]["template"])
    manifest_rel = Path(source_config["presentation"]["manifest"])
    shutil.copy2(source_root / template_rel, project_root / template_rel)

    manifest = json.loads((source_root / manifest_rel).read_text(encoding="utf-8"))
    manifest["entries"] = [entry for entry in manifest["entries"] if entry["figure_id"] == "A.1"]
    manifest["figure_count"] = 1
    (project_root / manifest_rel).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    shutil.copy2(
        source_root / "build" / "figures" / "A" / "figura_a_1.png",
        project_root / "build" / "figures" / "A" / "figura_a_1.png",
    )

    output = project_root / "entrega" / "test.pptx"
    result = assemble_from_template(project_root, output, strict=True)
    assert result.inserted == 1
    assert result.missing == ()
    assert result.errors == ()

    presentation = Presentation(str(output))
    slide = presentation.slides[5]
    by_name = {shape.name: shape for shape in slide.shapes}
    assert by_name["ANUARIO_FIGURE_A_1"].text == ""
    assert "ANUARIO_IMAGE_A_1" in by_name
