"""
Berichtsseite und E-Mail-Texte für Anfragen aus dem Einbett-Widget.

Der Bericht wird serverseitig als eigenständige HTML-Seite gerendert, damit der
Empfänger ihn ohne Login und ohne die React-Anwendung öffnen kann. Grundlage
sind dieselben gespeicherten Daten wie im Tool — Katalog, Punkte, Quellen.
"""
import html
import json
import os
from typing import Optional

from services.audit_criteria import (
    BLOCKER_LABELS,
    CATALOGUE,
    SOURCE_LABELS,
    Source,
)

SOURCE_MARKS = {
    Source.MEASURED.value: ("●", "#16A34A"),
    Source.DERIVED.value: ("◐", "#2563EB"),
    Source.AI.value: ("◇", "#7C3AED"),
    Source.NOT_COLLECTED.value: ("○", "#9CA3AF"),
}

BRAND_DARK = "#0F2E2B"
BRAND_ACCENT = "#F5C518"


def public_base_url() -> str:
    return os.getenv("PUBLIC_BASE_URL", os.getenv(
        "FRONTEND_URL", "https://kompagnon-frontend.onrender.com")).rstrip("/")


def api_base_url() -> str:
    return os.getenv("API_BASE_URL", "https://claude-code-znq2.onrender.com").rstrip("/")


def report_url(token: str) -> str:
    return f"{api_base_url()}/api/widget/report/{token}"


def confirm_url(token: str) -> str:
    return f"{api_base_url()}/api/widget/confirm/{token}"


def _json_field(raw, fallback):
    try:
        return json.loads(raw) if raw else fallback
    except (json.JSONDecodeError, TypeError):
        return fallback


def _esc(value) -> str:
    return html.escape(str(value or ""))


# ═══════════════════════════════════════════════════════════════════
# Berichtsseite
# ═══════════════════════════════════════════════════════════════════

def _criteria_rows(items: dict, sources: dict) -> str:
    blocks = []
    for category in CATALOGUE:
        collected = [c for c in category.criteria
                     if sources.get(c.key, Source.NOT_COLLECTED.value)
                     != Source.NOT_COLLECTED.value]
        score = sum(int(items.get(c.key, 0) or 0) for c in collected)
        maximum = sum(c.max_points for c in collected)

        rows = []
        for crit in category.criteria:
            source = sources.get(crit.key, Source.NOT_COLLECTED.value)
            mark, colour = SOURCE_MARKS.get(source, ("○", "#9CA3AF"))
            not_collected = source == Source.NOT_COLLECTED.value
            value = "–" if not_collected else f"{int(items.get(crit.key, 0) or 0)}/{crit.max_points}"
            rows.append(
                f'<tr style="opacity:{"0.55" if not_collected else "1"}">'
                f'<td style="padding:6px 8px;color:{colour}">{mark}</td>'
                f'<td style="padding:6px 8px">{_esc(crit.label)}'
                f'<div style="font-size:11px;color:#6b7280">{_esc(crit.hint)}</div></td>'
                f'<td style="padding:6px 8px;text-align:right;font-variant-numeric:tabular-nums">'
                f'{value}</td>'
                f'<td style="padding:6px 8px;font-size:11px;color:#6b7280">'
                f'{_esc(SOURCE_LABELS.get(Source(source), source))}</td></tr>'
            )

        blocks.append(
            f'<section style="margin:22px 0">'
            f'<h3 style="margin:0 0 6px;font-size:15px">{_esc(category.label)} '
            f'<span style="float:right;font-variant-numeric:tabular-nums">{score}/{maximum}</span></h3>'
            f'<table style="width:100%;border-collapse:collapse;font-size:13px">'
            f'{"".join(rows)}</table></section>'
        )
    return "".join(blocks)


def render_report_page(audit, company: str = "") -> str:
    """Vollständiger Bericht als eigenständige HTML-Seite."""
    items = _json_field(getattr(audit, "item_scores", None), {})
    sources = _json_field(getattr(audit, "item_sources", None), {})
    blockers = _json_field(getattr(audit, "blockers", None), [])
    issues = _json_field(getattr(audit, "top_issues", None), [])
    recommendations = _json_field(getattr(audit, "recommendations", None), [])

    blocker_html = ""
    if blockers:
        entries = "".join(
            f"<li>{_esc(BLOCKER_LABELS.get(b, b))}</li>" for b in blockers)
        blocker_html = (
            '<div style="background:#FDECEA;border-left:4px solid #B02418;'
            'padding:14px 18px;margin:18px 0;border-radius:6px">'
            '<strong>Rechtliche Ausschlusskriterien</strong>'
            '<p style="margin:6px 0;font-size:13px">Diese Punkte begrenzen die '
            'Bewertung unabhängig vom erreichten Score.</p>'
            f'<ul style="margin:6px 0 0 18px;font-size:13px">{entries}</ul></div>'
        )

    def _list(title, values):
        if not values:
            return ""
        entries = "".join(f"<li style='margin-bottom:4px'>{_esc(v)}</li>" for v in values)
        return (f'<h3 style="font-size:15px;margin:22px 0 6px">{title}</h3>'
                f'<ul style="margin:0 0 0 18px;font-size:13px">{entries}</ul>')

    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Website-Analyse {_esc(company or audit.website_url)}</title></head>
<body style="margin:0;background:#f5f5f3;font-family:system-ui,-apple-system,sans-serif;color:#111">
<div style="max-width:760px;margin:0 auto;padding:0 18px 60px">
  <header style="background:{BRAND_DARK};color:#fff;padding:26px 24px;border-radius:0 0 10px 10px">
    <div style="font-size:12px;letter-spacing:.12em;text-transform:uppercase;opacity:.75">
      KOMPAGNON · Homepage Standard</div>
    <h1 style="margin:8px 0 2px;font-size:22px">{_esc(company or audit.website_url)}</h1>
    <div style="font-size:13px;opacity:.8">{_esc(audit.website_url)}</div>
    <div style="margin-top:18px;display:flex;align-items:baseline;gap:14px">
      <span style="font-size:40px;font-weight:800;color:{BRAND_ACCENT}">
        {audit.total_score}<span style="font-size:18px;opacity:.7">/100</span></span>
      <span style="font-size:15px">{_esc(audit.level)}</span>
    </div>
    <div style="font-size:12px;opacity:.75;margin-top:6px">
      {getattr(audit, "coverage", 0)}% der Kriterien konnten geprüft werden</div>
  </header>

  {blocker_html}

  <p style="font-size:14px;line-height:1.6">{_esc(audit.ai_summary)}</p>
  {_list("Die größten Probleme", issues)}
  {_list("Empfohlene nächste Schritte", recommendations)}

  <h2 style="font-size:17px;margin:30px 0 4px">Alle Kriterien im Einzelnen</h2>
  <p style="font-size:12px;color:#6b7280;margin:0 0 8px">
    ● gemessen &nbsp; ◐ abgeleitet &nbsp; ◇ KI-Einschätzung &nbsp; ○ nicht erhoben
    (zählt nicht in die Bewertung)</p>
  {_criteria_rows(items, sources)}

  <footer style="margin-top:40px;padding-top:18px;border-top:1px solid #ddd;
                 font-size:12px;color:#6b7280">
    Erstellt am {audit.created_at.strftime('%d.%m.%Y') if audit.created_at else ''} ·
    KOMPAGNON Homepage Standard ·
    <a href="{public_base_url()}" style="color:{BRAND_DARK}">kompagnon.de</a>
  </footer>
</div></body></html>"""


# ═══════════════════════════════════════════════════════════════════
# E-Mail-Texte
# ═══════════════════════════════════════════════════════════════════

def _shell(inner: str) -> str:
    return f"""<!doctype html><html><head><meta charset="utf-8"></head>
<body style="margin:0;background:#f5f5f3;font-family:system-ui,sans-serif">
<div style="max-width:560px;margin:32px auto;background:#fff;border-radius:10px;overflow:hidden">
<div style="background:{BRAND_DARK};padding:22px 26px;color:#fff">
  <div style="font-size:11px;letter-spacing:.12em;text-transform:uppercase;opacity:.75">
    KOMPAGNON</div></div>
<div style="padding:26px">{inner}</div>
<div style="padding:16px 26px;border-top:1px solid #eee;font-size:11px;color:#888">
  Sie erhalten diese E-Mail, weil auf einer unserer Seiten eine Website-Analyse
  für diese Adresse angefordert wurde.
</div></div></body></html>"""


def report_email(company: str, score: int, level: str, token: str,
                 issues: Optional[list] = None,
                 confirm_token: Optional[str] = None) -> tuple:
    """Betreff und HTML für die Berichts-Mail."""
    issue_html = ""
    if issues:
        entries = "".join(f"<li style='margin-bottom:5px'>{_esc(i)}</li>" for i in issues[:3])
        issue_html = (f'<p style="margin:16px 0 6px"><strong>Die drei größten '
                      f'Punkte:</strong></p><ul style="margin:0 0 0 18px;font-size:14px">'
                      f'{entries}</ul>')

    consent_html = ""
    if confirm_token:
        consent_html = (
            f'<p style="margin-top:22px;padding-top:16px;border-top:1px solid #eee;'
            f'font-size:13px;color:#555">Sie haben zugestimmt, dass wir Sie zu Ihrer '
            f'Analyse kontaktieren dürfen. Bitte bestätigen Sie das einmalig: '
            f'<a href="{confirm_url(confirm_token)}" style="color:{BRAND_DARK}">'
            f'Kontaktaufnahme bestätigen</a>.</p>'
        )

    inner = f"""
<h2 style="margin:0 0 10px;font-size:19px">Ihre Website-Analyse ist fertig</h2>
<p style="font-size:14px;line-height:1.6">Wir haben <strong>{_esc(company)}</strong>
nach dem KOMPAGNON Homepage Standard geprüft — 42 Kriterien aus Recht, Sicherheit,
Performance, Barrierefreiheit, SEO, Design, Conversion und Inhalt.</p>
<div style="background:#f5f5f3;border-radius:8px;padding:16px;margin:18px 0;text-align:center">
  <div style="font-size:34px;font-weight:800;color:{BRAND_DARK}">{score}<span
     style="font-size:16px;opacity:.6">/100</span></div>
  <div style="font-size:14px;color:#555">{_esc(level)}</div>
</div>
{issue_html}
<p style="margin:22px 0"><a href="{report_url(token)}"
   style="display:inline-block;background:{BRAND_ACCENT};color:{BRAND_DARK};
          text-decoration:none;font-weight:700;padding:12px 22px;border-radius:6px">
   Vollständigen Bericht ansehen</a></p>
<p style="font-size:13px;color:#555">Im Bericht sehen Sie zu jedem Kriterium, ob es
gemessen, abgeleitet oder eingeschätzt wurde — und was konkret zu tun ist.</p>
{consent_html}"""
    return f"Ihre Website-Analyse für {company}: {score}/100", _shell(inner)


def confirmation_page(confirmed: bool) -> str:
    """Bestätigungsseite nach Klick auf den Double-Opt-in-Link."""
    if confirmed:
        title, text = ("Danke — Bestätigung erhalten",
                       "Wir dürfen Sie jetzt zu Ihrer Website-Analyse kontaktieren. "
                       "Sie können dem jederzeit formlos widersprechen.")
    else:
        title, text = ("Link nicht mehr gültig",
                       "Dieser Bestätigungslink ist unbekannt oder wurde bereits verwendet.")
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>{title}</title></head>
<body style="margin:0;background:#f5f5f3;font-family:system-ui,sans-serif;
             display:flex;align-items:center;justify-content:center;min-height:100vh">
<div style="background:#fff;border-radius:10px;padding:34px;max-width:440px;text-align:center">
  <h1 style="font-size:19px;margin:0 0 10px;color:{BRAND_DARK}">{title}</h1>
  <p style="font-size:14px;color:#555;line-height:1.6;margin:0">{text}</p>
</div></body></html>"""
