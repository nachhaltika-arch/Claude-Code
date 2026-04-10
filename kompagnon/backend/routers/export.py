"""
Export-Router: ZIP-Download aller Seiten eines Projekts.
Jede Seite wird als eigenständige HTML-Datei mit eingebettetem CSS exportiert.
"""
import io
import re
import zipfile
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from routers.auth_router import require_any_auth

router = APIRouter(prefix="/api/projects", tags=["export"])


def _slugify(name: str) -> str:
    s = name.lower()
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "seite"


def _build_full_html(page_name: str, html: str, css: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_name}</title>
  <style>
{css}
  </style>
</head>
<body>
{html}
</body>
</html>"""


@router.get("/{project_id}/export-zip")
def export_project_zip(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """
    Gibt alle gespeicherten Seiten des Projekts als ZIP-Datei zurück.
    Jede Seite = eine HTML-Datei mit eingebettetem CSS.
    """
    row = db.execute(
        text("SELECT lead_id, company_name FROM projects WHERE id = :id"),
        {"id": project_id},
    ).fetchone()
    if not row:
        raise HTTPException(404, "Projekt nicht gefunden")

    lead_id = row[0]
    company_name = row[1] or ""
    if not lead_id:
        raise HTTPException(400, "Projekt hat keinen verknüpften Lead")

    pages = db.execute(
        text("""
            SELECT page_name, gjs_html, gjs_css, position
            FROM sitemap_pages
            WHERE lead_id = :lid AND gjs_html IS NOT NULL AND gjs_html != ''
            ORDER BY position
        """),
        {"lid": lead_id},
    ).fetchall()

    if not pages:
        raise HTTPException(
            404,
            "Keine Seiten mit Inhalt gefunden. "
            "Bitte zuerst Seiten im GrapesJS-Editor bearbeiten und speichern.",
        )

    buf = io.BytesIO()
    used_slugs: dict[str, int] = {}
    redirects_lines = []

    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for page in pages:
            slug = _slugify(page.page_name)

            if slug in used_slugs:
                used_slugs[slug] += 1
                slug = f"{slug}-{used_slugs[slug]}"
            else:
                used_slugs[slug] = 0

            html_content = _build_full_html(
                page.page_name,
                page.gjs_html or "",
                page.gjs_css or "",
            )

            is_startseite = page.position == 0 or slug in (
                "startseite",
                "home",
                "index",
            )
            if is_startseite:
                filename = "index.html"
                redirects_lines.append("/  /index.html  200")
            else:
                filename = f"{slug}/index.html"
                redirects_lines.append(f"/{slug}  /{slug}/index.html  200")

            zf.writestr(filename, html_content)

        redirects_lines.append("/*  /index.html  200")
        zf.writestr("_redirects", "\n".join(redirects_lines))

        readme_lines = [
            f"# Website-Export — Projekt #{project_id}",
            f"Erstellt: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            "",
            "## Enthaltene Seiten",
        ]
        for page in pages:
            slug = _slugify(page.page_name)
            readme_lines.append(f"- {page.page_name} → /{slug}/")
        readme_lines += [
            "",
            "## Netlify-Import",
            "Diese ZIP-Datei kann direkt in Netlify als manuelles Deploy hochgeladen werden.",
        ]
        zf.writestr("README.md", "\n".join(readme_lines))

    buf.seek(0)

    filename_safe = re.sub(r"[^a-z0-9-]", "", _slugify(company_name or f"projekt-{project_id}"))
    filename = f"website-{filename_safe}-{datetime.now().strftime('%Y%m%d')}.zip"

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
