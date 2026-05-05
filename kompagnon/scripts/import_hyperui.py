"""
One-time import script: HyperUI MIT-licensed Tailwind sections → KAS library.

Source: https://github.com/markmead/hyperui  (MIT, © Mark Mead)
Run-Ablauf (lokal, nicht zur Backend-Laufzeit):

    git clone --depth 1 https://github.com/markmead/hyperui.git /tmp/hyperui
    python kompagnon/scripts/import_hyperui.py

Schreibt Templates nach `kompagnon/frontend/src/components/library/external/hyperui/`
+ Manifest `index.json`. Beim nächsten Backend-Start liest seed_component_library
diese Templates zusätzlich zu den 41 KAS-Eigen-Templates ein.

Lizenz-Attribution liegt als Kommentar in jedem HTML-File und im Manifest.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from datetime import date

# ── Pfade
SCRIPT_DIR  = Path(__file__).resolve().parent
REPO_ROOT   = SCRIPT_DIR.parent.parent
HYPERUI_DIR = Path("/tmp/hyperui")
TARGET_DIR  = REPO_ROOT / "kompagnon" / "frontend" / "src" / "components" / "library" / "external" / "hyperui"

# ── Mapping HyperUI-Kategorie → KAS-Kategorie + section_key-Hint + Beschreibung.
# Was nicht hier steht, wird übersprungen (z.B. buttons, polls — UI-Bausteine, keine Sections).
CATEGORY_MAP: dict[str, tuple[str, str, str]] = {
    "headers":           ("NAV",   "header_nav",     "Navbar/Header-Variante mit Logo, Nav-Links und CTA"),
    "ctas":              ("CTA",   "cta_final",      "Call-to-Action-Section, finale Conversion"),
    "feature-grids":     ("LEIST", "service_grid",   "Feature/Service-Grid mit Icons + Beschreibung"),
    "pricing":           ("LEIST", "offer_stack",    "Pricing-Tabelle / Hormozi-Wertbox"),
    "team-sections":     ("TRUST", "team",           "Team-/Mitarbeiter-Vorstellung mit Fotos"),
    "footers":           ("FOOT",  "footer_legal",   "Footer mit Pflicht-Links + Kontakt"),
    "contact-forms":     ("CTA",   "contact_form",   "Kontakt-Formular-Section mit Tel/Mail"),
    "logo-clouds":       ("TRUST", "trust_strip",    "Logo-Cloud — Innung / Hersteller / Bewertungen"),
    "faqs":              ("INFO",  "faq",            "FAQ-Section, Accordion oder 2-Spalten-Layout"),
    "banners":           ("CTA",   "urgency_block",  "Promo/Urgency-Banner"),
    "newsletter-signup": ("CTA",   "cta_inline",     "Newsletter-Signup-Section"),
    "sections":          ("HERO",  "hero_minimal",   "Allgemeine Marketing-Section"),
    "stats":             ("TRUST", "fallstudien_3",  "Stats-Block mit Zahlen / KPI"),
}

# Pro Kategorie max. so viele Templates importieren — beschränkt Wachstum.
MAX_PER_CATEGORY = 10

BODY_RE = re.compile(r"<body[^>]*>(?P<inner>.*)</body>", re.DOTALL | re.IGNORECASE)


def extract_body(html: str) -> str:
    """Extract <body>-Inner-HTML; Fallback: ganzer String wenn kein body-Tag."""
    m = BODY_RE.search(html)
    return m.group("inner").strip() if m else html.strip()


def main() -> int:
    if not HYPERUI_DIR.is_dir():
        print(f"ERR: HyperUI-Repo nicht gefunden unter {HYPERUI_DIR}", file=sys.stderr)
        print("Vorher klonen:  git clone --depth 1 https://github.com/markmead/hyperui.git /tmp/hyperui", file=sys.stderr)
        return 1

    examples_root = HYPERUI_DIR / "public" / "examples" / "marketing"
    if not examples_root.is_dir():
        print(f"ERR: examples-Ordner nicht gefunden: {examples_root}", file=sys.stderr)
        return 1

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()

    components: list[dict] = []
    for hu_cat, (kas_cat, section_hint, hint_text) in CATEGORY_MAP.items():
        cat_dir = examples_root / hu_cat
        if not cat_dir.is_dir():
            print(f"WARN: Kategorie nicht im Repo: {hu_cat}", file=sys.stderr)
            continue

        # Light-Versionen (skip *-dark.html), numerisch sortiert
        light_files = sorted(
            (f for f in cat_dir.glob("*.html") if not f.stem.endswith("-dark")),
            key=lambda f: (len(f.stem), f.stem),
        )[:MAX_PER_CATEGORY]

        for idx, html_file in enumerate(light_files, start=1):
            try:
                raw = html_file.read_text(encoding="utf-8")
            except Exception as exc:
                print(f"WARN: Lesefehler {html_file}: {exc}", file=sys.stderr)
                continue
            body = extract_body(raw)
            if not body or len(body) < 50:
                continue
            slug = f"hu-{hu_cat}-{idx}"
            attribution_header = (
                f"<!--\n"
                f"  Source:   HyperUI marketing/{hu_cat}/{html_file.name}\n"
                f"  License:  MIT (https://github.com/markmead/hyperui/blob/main/LICENSE)\n"
                f"  Author:   Mark Mead\n"
                f"  Imported: {today}\n"
                f"-->\n"
            )
            (TARGET_DIR / f"{slug}.html").write_text(attribution_header + body, encoding="utf-8")
            components.append({
                "slug":            slug,
                "name":            f"HyperUI · {hu_cat.replace('-', ' ').title()} #{idx}",
                "category":        kas_cat,
                "section_hint":    section_hint,   # KAS section_catalog-Key
                "tags":            [hu_cat, "hyperui", "open-source", "mit", "tailwind"],
                "slots":           [],             # External: HTML wird as-is genutzt, keine Slots
                "ki_prompt_hint":  hint_text,
                "preview_note":    f"HyperUI-{hu_cat} (MIT). Tailwind-only — keine eigenen Slots.",
                "source":          "hyperui",
            })

    manifest = {
        "_source":      "HyperUI",
        "_repo":        "https://github.com/markmead/hyperui",
        "_license":     "MIT",
        "_attribution": "Mark Mead — HyperUI",
        "_imported_at": today,
        "_max_per_category": MAX_PER_CATEGORY,
        "components":   components,
    }
    (TARGET_DIR / "index.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"OK: {len(components)} Templates nach {TARGET_DIR.relative_to(REPO_ROOT)} geschrieben")
    return 0


if __name__ == "__main__":
    sys.exit(main())
