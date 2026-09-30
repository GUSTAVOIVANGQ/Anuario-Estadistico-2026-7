import json
from pathlib import Path

from anuario2026 import cli


def test_run_command_returns_failure_when_figure_failed(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "reportes" / "corrida"
    run_dir.mkdir(parents=True)
    (run_dir / "resumen_ejecucion.json").write_text(
        json.dumps({"statuses": [{"figure_id": "B.22", "status": "ERROR"}]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(cli, "project_root_from_module", lambda: tmp_path)
    monkeypatch.setattr(cli, "run_pipeline", lambda *args, **kwargs: run_dir)

    assert cli.main(["run", "--assemble"]) == 1
