"""
Seed-Script fuer die Komponenten-Bibliothek (Step C des Online-Fertig-Redesigns).

Liest:
- kompagnon/frontend/src/components/library/index.json (Metadaten)
- kompagnon/frontend/src/components/library/{slug}.html (HTML-Templates)

Schreibt:
- DB-Tabelle component_library (siehe database.py:ComponentLibrary, Step A).

Idempotent: UPSERT auf slug. Wiederholte Laeufe aktualisieren bestehende
Eintraege ohne Duplikate.

Standalone-Aufruf:
    cd kompagnon/backend
    python -m seeds.seed_component_library

Auto-Aufruf beim Backend-Start: siehe main.py:_component_library_seed.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterator

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Pfad-Math: seeds/seed_component_library.py
#   .parent           -> seeds/
#   .parent.parent    -> backend/
#   .parent.parent.parent -> kompagnon/
# Dann frontend/src/components/library/.
#
# Funktioniert lokal und auf Render, weil das gesamte Repo gecloned wird —
# Render's "rootDir" beeinflusst nur die Run-/Build-Commands, der Code
# kann via .parent.parent... auf Geschwister-Verzeichnisse zugreifen.
LIBRARY_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "frontend" / "src" / "components" / "library"
)
INDEX_FILE = LIBRARY_DIR / "index.json"
# Externe Quellen (Open-Source-Bibliotheken, MIT-lizenziert): jede Quelle hat
# einen eigenen Sub-Ordner mit eigenem index.json + HTML-Files. Aktuell:
# external/hyperui (https://github.com/markmead/hyperui).
EXTERNAL_DIR = LIBRARY_DIR / "external"


class SeedSummary(dict):
    """Tally — wie viele Eintraege inserted/updated/skipped/errored sind."""

    def __init__(self) -> None:
        super().__init__(inserted=0, updated=0, skipped=0, errors=0)

    def total(self) -> int:
        return self["inserted"] + self["updated"]


def _iter_components() -> Iterator[tuple[dict, Path]]:
    """Liest die Manifeste und yieldet (component_dict, html_directory)-Tupel.

    Quellen:
      1. Haupt-Bibliothek (KAS-eigen): LIBRARY_DIR/index.json + LIBRARY_DIR/{slug}.html
      2. Externe Quellen (Open-Source, MIT): LIBRARY_DIR/external/{source}/index.json
         + LIBRARY_DIR/external/{source}/{slug}.html

    Pro Eintrag wird die zugehörige HTML-Directory mitgegeben, damit
    _read_html den richtigen Pfad nutzt.
    """
    # 1. Haupt-Bibliothek (KAS-eigen)
    if not INDEX_FILE.exists():
        logger.warning(
            f"seed_component_library: Haupt-Index fehlt: {INDEX_FILE} — "
            f"externe Quellen werden trotzdem geseedet falls vorhanden."
        )
    else:
        try:
            with INDEX_FILE.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            for comp in (data.get("components") or []):
                yield comp, LIBRARY_DIR
        except Exception as exc:
            logger.warning(f"seed_component_library: Haupt-Index nicht lesbar: {exc}")

    # 2. Externe Quellen (jeder Sub-Ordner unter library/external/)
    if EXTERNAL_DIR.is_dir():
        for source_dir in sorted(p for p in EXTERNAL_DIR.iterdir() if p.is_dir()):
            ext_index = source_dir / "index.json"
            if not ext_index.exists():
                continue
            try:
                with ext_index.open("r", encoding="utf-8") as fh:
                    ext_data = json.load(fh)
                ext_comps = ext_data.get("components") or []
                logger.info(
                    f"seed_component_library: external/{source_dir.name} → "
                    f"{len(ext_comps)} Eintraege"
                )
                for comp in ext_comps:
                    yield comp, source_dir
            except Exception as exc:
                logger.warning(
                    f"seed_component_library: external/{source_dir.name} "
                    f"konnte nicht gelesen werden: {exc}"
                )


def _read_html(slug: str, html_dir: Path = LIBRARY_DIR) -> str | None:
    """Liest das HTML-Template aus dem angegebenen Verzeichnis."""
    html_path = html_dir / f"{slug}.html"
    if not html_path.exists():
        logger.warning(f"seed_component_library: HTML-Datei fehlt: {html_path}")
        return None
    try:
        return html_path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.warning(f"seed_component_library: HTML-Lesefehler {slug}: {exc}")
        return None


def _upsert_component(db: Session, comp: dict, html: str) -> str:
    """
    UPSERT eines Bibliotheks-Eintrags ueber den slug.
    Returnt 'inserted' oder 'updated'.

    Postgres-spezifisch ueber ON CONFLICT(slug) DO UPDATE — die Migration
    in main.py legt slug als UNIQUE NOT NULL an.
    """
    sql = text("""
        INSERT INTO component_library
            (slug, name, category, tags, html_template, slots,
             ki_prompt_hint, preview_note)
        VALUES
            (:slug, :name, :category, CAST(:tags AS JSONB), :html_template,
             CAST(:slots AS JSONB), :ki_prompt_hint, :preview_note)
        ON CONFLICT (slug) DO UPDATE SET
            name           = EXCLUDED.name,
            category       = EXCLUDED.category,
            tags           = EXCLUDED.tags,
            html_template  = EXCLUDED.html_template,
            slots          = EXCLUDED.slots,
            ki_prompt_hint = EXCLUDED.ki_prompt_hint,
            preview_note   = EXCLUDED.preview_note
        RETURNING (xmax = 0) AS inserted
    """)

    params = {
        "slug":           comp["slug"],
        "name":           comp.get("name", comp["slug"]),
        "category":       comp.get("category", ""),
        "tags":           json.dumps(comp.get("tags") or []),
        "html_template":  html,
        "slots":          json.dumps(comp.get("slots") or []),
        "ki_prompt_hint": comp.get("ki_prompt_hint"),
        "preview_note":   comp.get("preview_note"),
    }

    row = db.execute(sql, params).fetchone()
    # xmax = 0 bedeutet: war ein INSERT (kein UPDATE)
    return "inserted" if (row and row[0]) else "updated"


def seed_component_library(db: Session) -> SeedSummary:
    """
    Befuellt component_library aus den HTML-Templates im Frontend-Repo.

    Wirft NICHT bei einzelnen Fehlern — pro Block wird in summary
    geloggt (skipped/errors). Heisst: Wenn z. B. ein Template umbenannt
    wurde aber index.json noch alten slug hat, laeuft der Rest durch.
    """
    summary = SeedSummary()

    if not LIBRARY_DIR.exists():
        logger.error(
            f"seed_component_library: Bibliotheks-Verzeichnis fehlt: {LIBRARY_DIR}. "
            f"Step B (HTML-Templates) muss vor Step C deployed sein."
        )
        return summary

    components = list(_iter_components())
    if not components:
        logger.info("seed_component_library: nichts zu seeden (leere Komponentenliste).")
        return summary

    logger.info(f"🌱 Component-Library Seed: {len(components)} Eintraege werden verarbeitet…")

    for comp, html_dir in components:
        slug = comp.get("slug")
        if not slug:
            logger.warning(f"seed_component_library: Eintrag ohne slug: {comp}")
            summary["skipped"] += 1
            continue

        html = _read_html(slug, html_dir)
        if html is None:
            summary["skipped"] += 1
            continue

        try:
            action = _upsert_component(db, comp, html)
            summary[action] += 1
        except Exception as exc:
            logger.warning(f"seed_component_library: UPSERT {slug} fehlgeschlagen: {exc}")
            summary["errors"] += 1
            db.rollback()
            continue

    try:
        db.commit()
    except Exception as exc:
        logger.error(f"seed_component_library: Commit fehlgeschlagen: {exc}", exc_info=True)
        db.rollback()
        summary["errors"] += summary.total()
        return summary

    logger.info(
        f"✓ Component-Library Seed fertig: "
        f"{summary['inserted']} neu, {summary['updated']} aktualisiert, "
        f"{summary['skipped']} uebersprungen, {summary['errors']} Fehler."
    )
    return summary


def main() -> None:
    """CLI-Entry-Point: python -m seeds.seed_component_library"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    from database import SessionLocal  # local import — only needed for CLI

    db = SessionLocal()
    try:
        summary = seed_component_library(db)
        print(
            f"Inserted: {summary['inserted']}  Updated: {summary['updated']}  "
            f"Skipped: {summary['skipped']}  Errors: {summary['errors']}"
        )
        if summary["errors"]:
            raise SystemExit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
