from __future__ import annotations

import json
from pathlib import Path

import anuario2026.sources as sources_module
from anuario2026.sources import SourceCatalog


def test_existing_verified_download_is_reused(tmp_path: Path, monkeypatch):
    source_id = "fuente_prueba"
    filename = "crudo.csv"
    path = tmp_path / "data" / "raw" / source_id / "objects" / "abc" / filename
    path.parent.mkdir(parents=True)
    path.write_text("valor\n1\n", encoding="utf-8")
    (tmp_path / "inventario_fuentes.csv").write_text(
        "source_id,acquisition_mode,filename,exact_url\n"
        f"{source_id},http,{filename},https://invalid.example/crudo.csv\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("ANUARIO_FORCE_DOWNLOAD", raising=False)
    monkeypatch.delenv("ANUARIO_OFFLINE", raising=False)

    reused, metadata = SourceCatalog(tmp_path).acquire(source_id)

    assert reused == path
    assert metadata["cache_status"] == "REUTILIZADO"
    assert metadata["status"] == "VERIFICADO"


def test_large_verified_cache_uses_recorded_fingerprint(tmp_path: Path, monkeypatch):
    source_id = "bit_global"
    filename = "TODO.zip"
    path = tmp_path / "data" / "raw" / source_id / "objects" / "abc" / filename
    path.parent.mkdir(parents=True)
    path.write_bytes(b"copia previamente validada")
    stat = path.stat()
    (path.parent / "metadata.json").write_text(
        json.dumps(
            {
                "status": "VERIFICADO",
                "sha256": "a" * 64,
                "bytes": stat.st_size,
                "verified_mtime_ns": stat.st_mtime_ns,
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "inventario_fuentes.csv").write_text(
        "source_id,acquisition_mode,filename,exact_url\n"
        f"{source_id},http,{filename},https://invalid.example/TODO.zip\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sources_module,
        "verify_raw_file",
        lambda _: (_ for _ in ()).throw(AssertionError("no debe releer el ZIP")),
    )

    reused, metadata = SourceCatalog(tmp_path).acquire(source_id)

    assert reused == path
    assert metadata["sha256"] == "a" * 64
    assert metadata["cache_status"] == "REUTILIZADO"
