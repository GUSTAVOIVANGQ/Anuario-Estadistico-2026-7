from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SourceError(RuntimeError):
    pass


def load_sources(project_root: Path) -> dict[str, dict[str, str]]:
    path = project_root / "inventario_fuentes.csv"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return {row["source_id"].strip(): row for row in csv.DictReader(stream)}


def verify_raw_file(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size == 0:
        raise SourceError(f"Archivo crudo ausente o vacío: {path}")
    suffix = path.suffix.lower()
    if suffix in {".zip", ".xlsx", ".pptx", ".docx"}:
        try:
            with zipfile.ZipFile(path) as archive:
                bad = archive.testzip()
                if bad:
                    raise SourceError(f"Archivo comprimido dañado en {bad}: {path}")
        except zipfile.BadZipFile as exc:
            raise SourceError(f"Archivo ZIP/Office inválido: {path}") from exc
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"sha256": digest.hexdigest(), "bytes": path.stat().st_size, "status": "VERIFICADO"}


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class SourceCatalog:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.sources = load_sources(project_root)

    def _existing_artifact(self, source_id: str, source: dict[str, str]) -> Path | None:
        value = source.get("artifact", "").strip()
        if value:
            path = self.project_root / Path(value)
            if path.is_file():
                return path
        filename = source.get("filename", "").strip()
        object_root = self.project_root / "data" / "raw" / source_id / "objects"
        if object_root.is_dir():
            candidates = [
                path
                for path in object_root.glob(f"*/{filename or '*'}")
                if path.is_file() and path.name != "metadata.json"
            ]
            if candidates:
                return max(candidates, key=lambda path: path.stat().st_mtime)
        return None

    def acquire(self, source_id: str) -> tuple[Path, dict[str, Any]]:
        if source_id not in self.sources:
            raise SourceError(f"Fuente no registrada: {source_id}")
        source = self.sources[source_id]
        existing = self._existing_artifact(source_id, source)
        offline = os.environ.get("ANUARIO_OFFLINE", "").strip().lower() in {
            "1",
            "true",
            "si",
            "sí",
        }
        mode = (source.get("acquisition_mode") or "").strip().lower()
        exact_url = (source.get("exact_url") or "").strip()

        force_download = os.environ.get("ANUARIO_FORCE_DOWNLOAD", "").strip().lower() in {
            "1",
            "true",
            "si",
            "sí",
        }

        # La caché verificada es la primera opción. Esto evita volver a descargar
        # archivos grandes en cada corrida; ANUARIO_FORCE_DOWNLOAD=1 permite
        # solicitar de forma explícita una copia nueva.
        if existing and not force_download:
            saved_metadata: dict[str, Any] = {}
            metadata_path = existing.parent / "metadata.json"
            if metadata_path.is_file():
                saved_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            stat = existing.stat()
            cached_verification = (
                saved_metadata.get("status") == "VERIFICADO"
                and str(saved_metadata.get("sha256", ""))
                and int(saved_metadata.get("bytes", -1)) == stat.st_size
                and int(saved_metadata.get("verified_mtime_ns", -1)) == stat.st_mtime_ns
            )
            if cached_verification:
                verification = {
                    "sha256": saved_metadata["sha256"],
                    "bytes": stat.st_size,
                    "status": "VERIFICADO",
                }
            else:
                verification = verify_raw_file(existing)
                saved_metadata.update(
                    {
                        **verification,
                        "verified_mtime_ns": stat.st_mtime_ns,
                        "verified_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    }
                )
                metadata_path.write_text(
                    json.dumps(saved_metadata, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            return existing, {
                **source,
                **saved_metadata,
                **verification,
                "local_path": str(existing),
                "cache_status": "REUTILIZADO",
            }

        if offline and not existing:
            raise SourceError(
                f"La fuente {source_id} no está en caché y ANUARIO_OFFLINE está activo."
            )

        if mode != "http" or not exact_url:
            raise SourceError(
                f"La fuente {source_id} requiere adquisición {mode or 'manual'}; "
                "coloca el archivo crudo en la ruta indicada por la figura."
            )
        path, response_metadata = self._download_http(source_id, source)
        verification = verify_raw_file(path)
        metadata = {
            **source,
            **verification,
            "verified_mtime_ns": path.stat().st_mtime_ns,
            "verified_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "local_path": str(path),
            **response_metadata,
            "cache_status": "DESCARGADO_Y_VERIFICADO",
        }
        (path.parent / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return path, metadata

    def _download_http(
        self, source_id: str, source: dict[str, str]
    ) -> tuple[Path, dict[str, str]]:
        url = source["exact_url"].strip()
        filename = source.get("filename", "").strip() or Path(url).name or f"{source_id}.bin"
        staging = self.project_root / "data" / "raw" / source_id / "staging"
        staging.mkdir(parents=True, exist_ok=True)
        partial = staging / f"{filename}.part"
        staged_complete = False
        if partial.is_file():
            try:
                verify_raw_file(partial)
                staged_complete = True
            except SourceError:
                staged_complete = False

        if staged_complete:
            print(f"  Reutiliza descarga temporal verificada: {partial.name}")
            response_metadata = {
                "downloaded_at": datetime.fromtimestamp(
                    partial.stat().st_mtime, tz=timezone.utc
                ).isoformat(timespec="seconds"),
                "response_url": url,
                "content_type": "",
                "source_last_modified": "",
            }
        else:
            request = urllib.request.Request(
                url, headers={"User-Agent": "AnuarioEstadistico2026/0.1"}
            )
            print(f"  Descarga: {url}")
            with urllib.request.urlopen(request, timeout=120) as response, partial.open(
                "wb"
            ) as stream:
                total = int(response.headers.get("Content-Length") or 0)
                response_metadata = {
                    "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "response_url": response.geturl(),
                    "content_type": response.headers.get("Content-Type", ""),
                    "source_last_modified": response.headers.get("Last-Modified", ""),
                }
                downloaded = 0
                last_percent = -1
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    stream.write(chunk)
                    downloaded += len(chunk)
                    percent = int(downloaded * 100 / total) if total else 0
                    if total and percent // 5 != last_percent // 5:
                        print(f"  Progreso: {percent:3d}% ({downloaded:,}/{total:,} bytes)")
                        last_percent = percent
                    elif not total:
                        print(f"  Progreso: {downloaded:,} bytes", end="\r", file=sys.stdout)

        digest = sha256_path(partial)
        object_key = digest
        full_candidate = (
            self.project_root / "data" / "raw" / source_id / "objects" / digest / filename
        )
        if os.name == "nt" and len(str(full_candidate)) >= 248:
            object_key = digest[:20]
        final_dir = self.project_root / "data" / "raw" / source_id / "objects" / object_key
        final_dir.mkdir(parents=True, exist_ok=True)
        final = final_dir / filename
        if not final.exists():
            shutil.move(str(partial), str(final))
        else:
            partial.unlink(missing_ok=True)
        return final, response_metadata
