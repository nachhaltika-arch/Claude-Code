#!/usr/bin/env python3
"""Die Artboards eines Betriebs als Dateien ausgeben — Vorstufe zum Canvas.

    python scripts/canvas-export.py <lead_id> [--nach VERZEICHNIS]

Schreibt `Main.dc.html`, `Styleguide.dc.html`, je ein `Wireframe<id>.dc.html`
und `Design<id>.dc.html` sowie `canvas.json`. Aus diesen Dateien entsteht in
Claude Code der Canvas; bearbeitet kommen sie ueber
`POST /api/design-canvas/{lead_id}/import` zurueck.

**Warum ein Skript und kein Knopf.** Ein Canvas wird nicht vom Server
veroeffentlicht, sondern in Claude Code. Der Server kann die Dateien liefern —
das tut `GET /api/design-canvas/{lead_id}` —, aber jemand muss sie dorthin
tragen. Dieses Skript ist dieser Weg, wenn man ohnehin an der Datenbank sitzt.
"""
import argparse
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "kompagnon" / "backend"))


def main() -> int:
    zerleger = argparse.ArgumentParser(description=__doc__)
    zerleger.add_argument("lead_id", type=int)
    zerleger.add_argument("--nach", default="canvas-export",
                          help="Zielverzeichnis (wird angelegt)")
    args = zerleger.parse_args()

    from database import Lead, Project, SessionLocal
    from routers.sitemap import SitemapPage
    from services.design_canvas import baue

    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == args.lead_id).first()
        if not lead:
            print(f"Betrieb {args.lead_id} gibt es nicht.", file=sys.stderr)
            return 1

        seiten = [{
            "id": z.id, "parent_id": z.parent_id, "position": z.position,
            "page_name": z.page_name, "page_type": z.page_type, "zweck": z.zweck,
            "ziel_keyword": z.ziel_keyword, "cta_text": z.cta_text,
            "cta_ziel": z.cta_ziel, "status": z.status, "mockup_html": z.mockup_html,
        } for z in db.query(SitemapPage)
                      .filter(SitemapPage.lead_id == args.lead_id)
                      .order_by(SitemapPage.position, SitemapPage.id).all()]

        project = (db.query(Project).filter(Project.lead_id == args.lead_id)
                     .order_by(Project.id.desc()).first())
        ergebnis = baue(lead=lead, seiten=seiten, project=project)
    finally:
        db.close()

    ziel = pathlib.Path(args.nach)
    ziel.mkdir(parents=True, exist_ok=True)
    for name, quelle in ergebnis["files"].items():
        (ziel / name).write_text(quelle, encoding="utf-8")
    (ziel / "canvas.json").write_text(
        json.dumps(ergebnis["canvas"], indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"{len(ergebnis['files'])} Artboards nach {ziel}/ — "
          f"Betrieb: {lead.company_name}")
    for name in sorted(ergebnis["files"]):
        print(f"  {name}")
    return 0


if __name__ == "__main__":
    os.environ.setdefault("SKIP_MIGRATIONS", "1")
    raise SystemExit(main())
