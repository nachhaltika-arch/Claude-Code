"""
Berichtsseite und E-Mail-Texte für Anfragen aus dem Einbett-Widget.

Der Bericht wird serverseitig als eigenständige HTML-Seite gerendert, damit der
Empfänger ihn ohne Login und ohne die React-Anwendung öffnen kann. Grundlage
sind dieselben gespeicherten Daten wie im Tool — Katalog, Punkte, Quellen.

Farben und Schriften kommen aus ``services.brand`` und damit aus derselben CI
wie das Tool. Vorher standen hier zwei erfundene Hex-Werte.
"""
import html
import json
import os
from typing import Optional

from services import brand
# Die beiden Adressen liegen in ``services.base_urls`` — hier weiter
# importiert, weil die Berichtslinks unten sie brauchen und Aufrufer sie
# seit jeher über dieses Modul beziehen.
from services.base_urls import _erste_gesetzte, api_base_url, public_base_url  # noqa: F401
from services.mail_layout import knopf, rahmen, wortmarke
from services.audit_criteria import (
    BLOCKER_LABELS,
    CATALOGUE,
    SOURCE_LABELS,
    Criterion,
    Source,
)
from services.audit_industry_profiles import massstab_fuer

# Herkunft eines Werts. Die Farben folgen der CI-Statuspalette statt der
# früheren freien Töne — gemessen ist Erfolg, abgeleitet und Einschätzung
# sind die beiden Teal-Stufen, nicht erhoben bleibt stumm.
SOURCE_MARKS = {
    Source.MEASURED.value: ("●", brand.SUCCESS),
    Source.DERIVED.value: ("◐", brand.MID),
    Source.AI.value: ("◇", brand.DARK),
    Source.NOT_COLLECTED.value: ("○", brand.TEXT_30),
}


def report_url(token: str) -> str:
    return f"{api_base_url()}/api/widget/report/{token}"


def confirm_url(token: str) -> str:
    return f"{api_base_url()}/api/widget/confirm/{token}"


def verify_url(token: str) -> str:
    return f"{api_base_url()}/api/widget/verify/{token}"


def gestenbeleg(token: str) -> str:
    """Der Wert, den die Seite erst bei einer echten Geste mitschickt.

    Aus dem Token abgeleitet, damit der Server ihn ohne gespeicherten Zustand
    nachrechnen kann — und nicht rateabar, weil ``SECRET_KEY`` einfliesst.
    Fehlt der Schlüssel, wird nicht etwa alles durchgewunken: Dann ergibt sich
    ein anderer, ebenso stabiler Wert, und die Prüfung greift weiter.
    """
    import hashlib
    import hmac

    schluessel = os.getenv("SECRET_KEY", "kompagnon-widget").encode()
    return hmac.new(schluessel, token.encode(), hashlib.sha256).hexdigest()[:32]


# Terminkalender — das Ziel des Knopfes im Bericht.
#
# Ohne „/u/0/": das Stück steht für das Google-Konto dessen, der die Adresse
# kopiert hat. Bei einem Besucher, der in mehreren Konten angemeldet ist,
# kann der Link damit ins Leere laufen.
STANDARD_TERMIN_URL = (
    "https://calendar.google.com/calendar/appointments/schedules/"
    "AcZssZ0cu63n4TldbKN5xijyccSTDAmXIVezWUqsBQVWmCTLo7l1mSYRWwauMcIqS7HcZwXSedN5LUAt"
)


def termin_url(eingestellt: str = "") -> str:
    """Wohin der Knopf im Bericht führt.

    Bewusst **nicht** dieselbe Einstellung wie der CTA im Widget: Das Widget
    schickt einen Besucher, der gerade seine Punktzahl gesehen hat, auf die
    Angebotsseite. Der Bericht erreicht jemanden, der seine Adresse bestätigt,
    den Bericht geöffnet und die Mängel gelesen hat — mit dem ist ein Termin
    der nächste Schritt, kein weiteres Formular.

    Eine gemeinsame Einstellung hatte den Effekt, dass der Wert im Tool
    (`widget_checkout_url`) den Kalender überschrieb und der Bericht wieder
    auf die Startseite zeigte.

    Geprüft wird das Schema: Der Wert kommt aus einer Eingabemaske und landet
    in einem ``href``.
    """
    wert = (eingestellt or "").strip()
    if wert.lower().startswith(("http://", "https://")):
        return wert
    return STANDARD_TERMIN_URL


def _json_field(raw, fallback):
    try:
        return json.loads(raw) if raw else fallback
    except (json.JSONDecodeError, TypeError):
        return fallback


def _esc(value) -> str:
    return html.escape(str(value or ""))


def _wortmarke(farbe: str = brand.WHITE, gelb: str = brand.YELLOW) -> str:
    """KOMPAGNON als Schriftzug — siehe ``mail_layout.wortmarke``."""
    return wortmarke(farbe, gelb)


# ═══════════════════════════════════════════════════════════════════
# Berichtsseite
# ═══════════════════════════════════════════════════════════════════

def _kategorien(items: dict, sources: dict) -> list:
    """Punkte je Kategorie — nur über die tatsächlich erhobenen Kriterien.

    Nicht erhobene Kriterien zählen weder in den Zähler noch in den Nenner.
    Sonst sähe eine Kategorie, die mangels API-Schlüssel gar nicht geprüft
    wurde, aus wie eine, die durchgefallen ist.
    """
    ergebnis = []
    for category in CATALOGUE:
        erhoben = [c for c in category.criteria
                   if sources.get(c.key, Source.NOT_COLLECTED.value)
                   != Source.NOT_COLLECTED.value]
        punkte = sum(int(items.get(c.key, 0) or 0) for c in erhoben)
        maximum = sum(c.max_points for c in erhoben)
        ergebnis.append({
            "kategorie": category,
            "punkte": punkte,
            "maximum": maximum,
            "anteil": round(punkte / maximum * 100) if maximum else 0,
        })
    return ergebnis


def _balken(anteil: int, farbe: str, hoehe: int = 8,
            spur: str = brand.BORDER) -> str:
    """Ein Fortschrittsbalken aus zwei divs.

    Bewusst kein SVG und kein Bild: das hier wird auch gedruckt und in
    E-Mail-Vorschauen gerendert, und zwei divs überleben beides.
    """
    breite = max(0, min(100, anteil))
    return (f'<div style="background:{spur};border-radius:{hoehe}px;'
            f'height:{hoehe}px;overflow:hidden">'
            f'<div style="background:{farbe};width:{breite}%;height:{hoehe}px;'
            f'border-radius:{hoehe}px"></div></div>')


def _kategorie_uebersicht(kategorien: list) -> str:
    """Die sechs Kategorien auf einen Blick, bevor es ins Detail geht."""
    zeilen = []
    for eintrag in kategorien:
        if not eintrag["maximum"]:
            continue
        farbe = brand.score_colour(eintrag["anteil"])
        zeilen.append(
            f'<div style="margin:0 0 16px">'
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:baseline;margin:0 0 6px">'
            f'<span style="font-size:14px;font-weight:700;color:{brand.TEXT}">'
            f'{_esc(eintrag["kategorie"].label)}</span>'
            f'<span style="font-family:{brand.FONT_MONO};font-size:13px;'
            f'color:{brand.TEXT_60}">{eintrag["punkte"]}/{eintrag["maximum"]}</span>'
            f'</div>{_balken(eintrag["anteil"], farbe)}</div>'
        )
    if not zeilen:
        return ""
    return (f'<section style="margin:32px 0">'
            f'<h2 style="font-size:17px;font-weight:900;color:{brand.DARK};'
            f'margin:0 0 16px">Die Bereiche im Überblick</h2>'
            f'{"".join(zeilen)}</section>')


def _hinweis(crit: Criterion, klasse: str) -> str:
    """Was neben dem Kriterium steht — der Maßstab der Klasse, sonst der Katalog.

    Der Katalog-Hinweis beschreibt, was allgemein geprüft wird; der Maßstab aus
    `audit_industry_profiles` sagt, woran diese Branche gemessen wird. Wo es
    beides gibt, gewinnt der genauere: Ein Ingenieurbüro führt Seiten je
    Fachgebiet, nicht je Gewerk.
    """
    return massstab_fuer(crit.key, klasse or "") or crit.hint


def _criteria_rows(kategorien: list, items: dict, sources: dict,
                   klasse: str = "") -> str:
    """Jedes Kriterium einzeln, gruppiert nach Kategorie."""
    blocks = []
    for eintrag in kategorien:
        category = eintrag["kategorie"]
        rows = []
        for crit in category.criteria:
            source = sources.get(crit.key, Source.NOT_COLLECTED.value)
            mark, colour = SOURCE_MARKS.get(source, ("○", brand.TEXT_30))
            not_collected = source == Source.NOT_COLLECTED.value
            value = "–" if not_collected else f"{int(items.get(crit.key, 0) or 0)}/{crit.max_points}"
            rows.append(
                f'<tr style="border-top:1px solid {brand.BORDER};'
                f'opacity:{"0.55" if not_collected else "1"}">'
                f'<td style="padding:10px 8px;color:{colour};font-size:15px">{mark}</td>'
                f'<td style="padding:10px 8px">'
                f'<div style="font-weight:700;color:{brand.TEXT}">{_esc(crit.label)}</div>'
                f'<div style="font-size:12px;color:{brand.TEXT_60};margin-top:2px">'
                f'{_esc(_hinweis(crit, klasse))}</div></td>'
                f'<td style="padding:10px 8px;text-align:right;white-space:nowrap;'
                f'font-family:{brand.FONT_MONO};font-size:13px;color:{brand.TEXT}">'
                f'{value}</td>'
                f'<td style="padding:10px 8px;font-size:12px;color:{brand.TEXT_60};'
                f'white-space:nowrap">'
                f'{_esc(SOURCE_LABELS.get(Source(source), source))}</td></tr>'
            )

        blocks.append(
            f'<section style="margin:28px 0">'
            f'<div style="background:{brand.DARK};color:{brand.WHITE};'
            f'padding:10px 14px;border-radius:6px 6px 0 0;display:flex;'
            f'justify-content:space-between;align-items:baseline">'
            f'<span style="font-size:14px;font-weight:900;letter-spacing:.02em">'
            f'{_esc(category.label)}</span>'
            f'<span style="font-family:{brand.FONT_MONO};font-size:13px;'
            f'color:{brand.YELLOW}">{eintrag["punkte"]}/{eintrag["maximum"]}</span></div>'
            # Vier Spalten, zwei davon umbruchfrei: auf einem schmalen Telefon
            # schöbe die Tabelle sonst die ganze Seite zur Seite. Sie rollt
            # in ihrem eigenen Kasten, der Rest der Seite bleibt stehen.
            f'<div style="overflow-x:auto;-webkit-overflow-scrolling:touch">'
            f'<table style="width:100%;border-collapse:collapse;font-size:13px;'
            f'background:{brand.WHITE};border:1px solid {brand.BORDER};'
            f'border-top:none;border-radius:0 0 6px 6px">'
            f'{"".join(rows)}</table></div></section>'
        )
    return "".join(blocks)


def _blocker_block(blockers: list) -> str:
    if not blockers:
        return ""
    entries = "".join(
        f'<li style="margin-bottom:4px">{_esc(BLOCKER_LABELS.get(b, b))}</li>'
        for b in blockers)
    return (
        f'<div style="background:{brand.ERROR_BG};border-left:4px solid {brand.ERROR};'
        f'padding:16px 20px;margin:24px 0;border-radius:0 8px 8px 0">'
        f'<strong style="color:{brand.ERROR};font-size:15px">'
        f'Rechtliche Ausschlusskriterien</strong>'
        f'<p style="margin:6px 0 0;font-size:13px;color:{brand.TEXT_60}">Diese Punkte '
        f'begrenzen die Bewertung unabhängig vom erreichten Score.</p>'
        f'<ul style="margin:10px 0 0 18px;font-size:13px;color:{brand.TEXT}">'
        f'{entries}</ul></div>'
    )


def _liste(titel: str, werte: list) -> str:
    if not werte:
        return ""
    entries = "".join(
        f'<li style="margin-bottom:8px;line-height:1.6">{_esc(v)}</li>' for v in werte)
    return (f'<section style="margin:28px 0">'
            f'<h2 style="font-size:17px;font-weight:900;color:{brand.DARK};'
            f'margin:0 0 10px">{titel}</h2>'
            f'<ul style="margin:0;padding-left:20px;font-size:14px;'
            f'color:{brand.TEXT}">{entries}</ul></section>')


def _angebot_block(token: str, cta_url: str = "") -> str:
    """PDF-Abruf und Angebot — beide erst hier, hinter dem Klick aus der Mail.

    Genau ein gelber Knopf auf der Seite, so will es die CI. Gelb bekommt das
    PDF: dafür ist der Empfänger hergekommen. Das Angebot steht als heller
    Knopf darunter — es soll dastehen, aber nicht die Hand führen.
    """
    if not token:
        return ""
    return (
        f'<section style="background:{brand.DARK};border-radius:10px;'
        f'padding:28px 24px;margin:32px 0">'
        f'<h2 style="margin:0 0 8px;font-size:18px;font-weight:900;'
        f'color:{brand.WHITE}">Diesen Bericht mitnehmen</h2>'
        f'<p style="margin:0 0 20px;font-size:14px;line-height:1.6;'
        f'color:{brand.WHITE};opacity:.85">Alle Kriterien mit Bewertung und '
        f'Empfehlungen als PDF — zum Ablegen oder Weitergeben.</p>'
        f'<a href="{report_url(token)}/pdf" style="display:inline-block;'
        f'background:{brand.YELLOW};color:{brand.DARK};text-decoration:none;'
        f'font-weight:900;padding:13px 24px;border-radius:6px;font-size:14px">'
        f'PDF herunterladen</a>'
        f'<div style="margin-top:24px;padding-top:20px;'
        f'border-top:1px solid rgba(255,255,255,.2)">'
        # Der Knopf führt in den Terminkalender, nicht auf ein Formular. Der
        # Text muss das ansagen — ein „Webseite anfragen", das einen Kalender
        # öffnet, überrascht an der falschen Stelle.
        f'<p style="margin:0 0 14px;font-size:14px;line-height:1.6;'
        f'color:{brand.WHITE}">Sie möchten die Punkte nicht selbst abarbeiten? '
        f'Wir gehen sie in einem kostenlosen Erstgespräch durch und sagen '
        f'Ihnen, was davon sich lohnt.</p>'
        f'<a href="{termin_url(cta_url)}" target="_blank" rel="noopener" '
        f'style="display:inline-block;'
        f'background:transparent;color:{brand.WHITE};text-decoration:none;'
        f'font-weight:700;padding:11px 22px;border-radius:6px;font-size:14px;'
        f'border:2px solid {brand.WHITE}">Jetzt Termin vereinbaren →</a>'
        f'</div></section>'
    )


def _einordnung(audit) -> str:
    """Wogegen bewertet wurde — vor der Punktzahl, nicht danach.

    Der Empfänger kennt uns nicht. Bevor er eine Zahl über seine Arbeit liest,
    muss er sehen, dass sein Geschäft verstanden wurde; sonst liest er die Zahl
    als Urteil eines Fremden. Genau daran ist der Bericht am 14.08. gescheitert,
    der einen Kandidatenauftritt an Handwerksleistungen maß.
    """
    from services.audit_industry_map import KLASSEN

    branche = (getattr(audit, "erkannte_branche", "") or "").strip()
    klasse = KLASSEN.get(getattr(audit, "branchenklasse", "") or "")
    if not branche and not klasse:
        return ""

    if klasse and klasse.schluessel == "K6":
        text = (f"Eingeordnet als: {branche or klasse.bezeichnung}. Der "
                f"Homepage Standard ist auf Betriebe zugeschnitten — die "
                f"angebotsbezogenen Kriterien gelten hier nicht und zählen "
                f"nicht mit.")
    elif klasse:
        text = (f"Bewertet als {branche or klasse.bezeichnung} — Maßstab: "
                f"{klasse.bezeichnung}.")
    else:
        text = f"Bewertet als {branche}."

    return (f'<div style="margin-top:14px;font-size:13px;line-height:1.6;'
            f'opacity:.85;max-width:60ch">{_esc(text)}</div>')


def render_report_page(audit, company: str = "", token: str = "",
                       cta_url: str = "") -> str:
    """Vollständiger Bericht als eigenständige HTML-Seite.

    Hier steht auch das Angebot. Es stand vorher in der ersten E-Mail — die
    aber an eine Adresse ging, von der niemand wusste, ob sie dem Anfordernden
    gehört. Auf dieser Seite ist der Empfänger nachweislich selbst.
    """
    items = _json_field(getattr(audit, "item_scores", None), {})
    sources = _json_field(getattr(audit, "item_sources", None), {})
    blockers = _json_field(getattr(audit, "blockers", None), [])
    issues = _json_field(getattr(audit, "top_issues", None), [])
    recommendations = _json_field(getattr(audit, "recommendations", None), [])

    kategorien = _kategorien(items, sources)
    branchenklasse = getattr(audit, "branchenklasse", "") or ""
    score = int(getattr(audit, "total_score", 0) or 0)
    coverage = int(getattr(audit, "coverage", 0) or 0)
    titel = company or audit.website_url

    zusammenfassung = ""
    if getattr(audit, "ai_summary", None):
        zusammenfassung = (
            f'<p style="font-size:15px;line-height:1.7;color:{brand.TEXT};'
            f'margin:24px 0;max-width:62ch">{_esc(audit.ai_summary)}</p>')

    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Website-Analyse {_esc(titel)}</title>
<style>
  body {{ margin:0; background:{brand.SURFACE};
         font-family:{brand.FONT_SANS}; color:{brand.TEXT};
         -webkit-font-smoothing:antialiased; }}
  a {{ color:{brand.MID}; }}
  .wrap {{ max-width:780px; margin:0 auto; padding:0 20px 64px; }}
  .head {{ background:{brand.DARK}; color:{brand.WHITE};
          padding:32px 28px; border-radius:0 0 12px 12px; }}
  @media print {{ body {{ background:#fff; }} .wrap {{ max-width:none; }} }}
</style></head>
<body>
<div class="wrap">
  <header class="head">
    {_wortmarke()}
    <div style="font-size:11px;letter-spacing:.14em;text-transform:uppercase;
                opacity:.7;margin-top:4px">Homepage Standard</div>
    <h1 style="margin:16px 0 2px;font-size:26px;font-weight:900;
               line-height:1.15">{_esc(titel)}</h1>
    <div style="font-size:13px;opacity:.75">{_esc(audit.website_url)}</div>
    {_einordnung(audit)}

    <div style="margin-top:26px;display:flex;align-items:baseline;gap:16px;
                flex-wrap:wrap">
      <span style="font-family:{brand.FONT_MONO};font-size:52px;font-weight:700;
                   line-height:1;color:{brand.YELLOW}">{score}<span
         style="font-size:20px;opacity:.7">/100</span></span>
      <span style="display:inline-block;border:1px solid rgba(255,255,255,.4);
                   border-radius:999px;padding:5px 14px;font-size:14px;
                   font-weight:700">{_esc(audit.level)}</span>
    </div>
    <div style="margin-top:16px">
      {_balken(score, brand.YELLOW, hoehe=10, spur="rgba(255,255,255,.18)")}
    </div>
    <div style="font-size:12px;opacity:.75;margin-top:10px">
      {coverage}% der Kriterien konnten geprüft werden</div>
  </header>

  {_blocker_block(blockers)}
  {zusammenfassung}
  {_kategorie_uebersicht(kategorien)}
  {_liste("Die größten Probleme", issues)}
  {_liste("Empfohlene nächste Schritte", recommendations)}
  {_angebot_block(token, cta_url)}

  <h2 style="font-size:17px;font-weight:900;color:{brand.DARK};
             margin:36px 0 6px">Alle Kriterien im Einzelnen</h2>
  <p style="font-size:12px;color:{brand.TEXT_60};margin:0 0 4px">
    <span style="color:{brand.SUCCESS}">●</span> gemessen &nbsp;
    <span style="color:{brand.MID}">◐</span> abgeleitet &nbsp;
    <span style="color:{brand.DARK}">◇</span> KI-Einschätzung &nbsp;
    <span style="color:{brand.TEXT_30}">○</span> nicht erhoben
    (zählt nicht in die Bewertung)</p>
  {_criteria_rows(kategorien, items, sources, branchenklasse)}

  <footer style="margin-top:44px;padding-top:20px;
                 border-top:1px solid {brand.BORDER};
                 font-size:12px;color:{brand.TEXT_60}">
    Erstellt am {audit.created_at.strftime('%d.%m.%Y') if audit.created_at else ''} ·
    KOMPAGNON Homepage Standard ·
    <a href="{public_base_url()}">kompagnon.eu</a>
  </footer>
</div></body></html>"""


# ═══════════════════════════════════════════════════════════════════
# E-Mail-Texte
# ═══════════════════════════════════════════════════════════════════

FUSS_WIDGET = ("Sie erhalten diese E-Mail, weil für diese Adresse eine "
               "Website-Analyse angefordert wurde. Es folgt nichts weiter, "
               "wenn Sie nicht reagieren.")


def _shell(inner: str) -> str:
    """Rahmen für jede Widget-Mail — gemeinsam mit den übrigen Mails.

    Der Rahmen stand hier und nur hier; die Mail an einen Bestandskunden hatte
    gar keinen. Er liegt jetzt in ``mail_layout`` und wird von beiden Wegen
    genutzt. Widget-eigen bleibt der Fußtext.
    """
    return rahmen(inner, FUSS_WIDGET)


def _mail_knopf(url: str, text: str) -> str:
    """Der eine gelbe Knopf der Mail."""
    return knopf(url, text)


def _katalog_umfang() -> str:
    """Umfang der Prüfung in Worten — aus dem Katalog, nicht eingetippt.

    Hier stand „42 Kriterien"; der Katalog führt 38 bewertete. Eine Zahl, die
    der Empfänger im Bericht nachzählen kann, muss stimmen.
    """
    kriterien = sum(len(cat.criteria) for cat in CATALOGUE)
    kurz = [cat.label.split(" (")[0].split(" & ")[0] for cat in CATALOGUE]
    return f"{kriterien} Kriterien aus {', '.join(kurz[:-1])} und {kurz[-1]}"


def verify_email(company: str, verify_token: str) -> tuple:
    """Die erste Mail: nur die Frage, ob die Adresse stimmt.

    Sie geht an eine Adresse, die niemand geprüft hat — die Eingabe im Widget
    muss dem Eintragenden nicht gehören. Deshalb steht hier nichts über die
    Website drin: keine Punktzahl, keine Mängel, kein Link zum Bericht. Nur
    dass etwas angefordert wurde, und die Möglichkeit, das zu bestätigen.

    Wer nicht klickt, bekommt nie einen Bericht und hat von uns genau diese
    eine Nachricht gesehen.
    """
    inner = f"""
<h1 style="margin:0 0 12px;font-size:21px;font-weight:900;line-height:1.25;
           color:{brand.DARK}">Bitte bestätigen Sie kurz Ihre Adresse</h1>
<p style="margin:0;font-size:15px;line-height:1.7;color:{brand.TEXT}">
Für diese E-Mail-Adresse wurde eine Website-Analyse von
<strong>{_esc(company)}</strong> nach dem KOMPAGNON Homepage Standard
angefordert. Bevor wir etwas verschicken, möchten wir wissen, dass die
Adresse wirklich Ihnen gehört.</p>
{_mail_knopf(verify_url(verify_token), 'Analyse bestätigen')}
<p style="margin:0 0 14px;font-size:14px;line-height:1.7;color:{brand.TEXT_60}">
Nach dem Klick schicken wir Ihnen den Link zum vollständigen Bericht — mit
{_katalog_umfang()}, jeweils mit Bewertung und Empfehlung.</p>
<p style="margin:0;padding:14px 16px;background:{brand.SURFACE};
          border-radius:8px;font-size:13px;line-height:1.6;color:{brand.TEXT_60}">
Haben Sie das nicht angefordert? Dann ignorieren Sie diese E-Mail einfach.
Ohne Ihre Bestätigung schicken wir nichts weiter und melden uns nicht von
selbst.</p>"""
    return (f"Bitte bestätigen: Website-Analyse für {company}", _shell(inner))


def report_ready_email(company: str, token: str,
                       confirm_token: Optional[str] = None) -> tuple:
    """Betreff und HTML für die erste Mail — die Einladung zum Bericht.

    Hier stand einmal der fertige Bericht: Punktzahl, die größten Mängel, ein
    Verkaufsknopf und das PDF im Anhang. Das Problem daran ist, wer ihn bekam.
    Die Adresse im Widget muss dem Eintragenden nicht gehören — wer die eines
    Wettbewerbers einträgt, ließ dort einen Werbebrief zustellen, den niemand
    bestellt hatte (§ 7 UWG), samt fremder Bewertung der eigenen Seite.

    Diese Mail nennt deshalb weder Punktzahl noch Mängel und wirbt nicht. Sie
    sagt, dass etwas angefordert wurde, und bietet den Bericht an. Wer sie
    nicht bestellt hat, ignoriert sie und hat nichts erfahren. Der Klick ist
    zugleich der Nachweis, dass die Adresse dem Empfänger gehört.
    """
    consent_html = ""
    if confirm_token:
        consent_html = (
            f'<p style="margin:24px 0 0;padding-top:18px;'
            f'border-top:1px solid {brand.BORDER};font-size:13px;line-height:1.6;'
            f'color:{brand.TEXT_60}">Beim Anfordern wurde zugestimmt, dass wir '
            f'zu der Analyse Kontakt aufnehmen dürfen. Falls Sie das waren, '
            f'bestätigen Sie es bitte einmalig: '
            f'<a href="{confirm_url(confirm_token)}" style="color:{brand.MID};'
            f'font-weight:700">Kontaktaufnahme bestätigen</a>. '
            f'Ohne diese Bestätigung melden wir uns nicht.</p>'
        )

    inner = f"""
<h1 style="margin:0 0 12px;font-size:21px;font-weight:900;line-height:1.25;
           color:{brand.DARK}">Ihre Website-Analyse ist fertig</h1>
<p style="margin:0;font-size:15px;line-height:1.7;color:{brand.TEXT}">
Danke für die Bestätigung. Hier ist der vollständige Bericht zu
<strong>{_esc(company)}</strong> — {_katalog_umfang()}.</p>
{_mail_knopf(report_url(token), 'Bericht ansehen')}
<p style="margin:0;font-size:14px;line-height:1.7;color:{brand.TEXT_60}">
Im Bericht sehen Sie zu jedem Kriterium, ob es gemessen, abgeleitet oder
eingeschätzt wurde — und was konkret zu tun ist. Dort lässt er sich auch als
PDF herunterladen.</p>
{consent_html}"""
    return f"Ihre Website-Analyse für {company} ist fertig", _shell(inner)


def confirmation_page(confirmed: bool) -> str:
    """Bestätigungsseite nach Klick auf den Marketing-Double-Opt-in."""
    if confirmed:
        return _hinweisseite(
            "✓", brand.SUCCESS, "Danke — Bestätigung erhalten",
            "Wir dürfen Sie jetzt zu Ihrer Website-Analyse kontaktieren. "
            "Sie können dem jederzeit formlos widersprechen.")
    return _hinweisseite(
        "!", brand.WARN, "Link nicht mehr gültig",
        "Dieser Bestätigungslink ist unbekannt oder wurde bereits verwendet.")


def verification_page(verified: bool, bereits: bool = False) -> str:
    """Seite nach dem Klick auf die Adressbestätigung.

    Sie muss ansagen, was als Nächstes passiert — der Bericht steht hier
    bewusst noch nicht, er kommt per Mail.
    """
    if not verified:
        return _hinweisseite(
            "!", brand.WARN, "Link nicht mehr gültig",
            "Dieser Bestätigungslink ist unbekannt. Bitte fordern Sie die "
            "Analyse im Widget erneut an.")
    if bereits:
        return _hinweisseite(
            "✓", brand.SUCCESS, "Schon bestätigt",
            "Diese Adresse ist bereits bestätigt. Die E-Mail mit dem Link zum "
            "Bericht ist unterwegs — sehen Sie bitte in Ihrem Postfach nach.")
    return _hinweisseite(
        "✓", brand.SUCCESS, "Danke — der Bericht ist unterwegs",
        "Wir haben Ihnen gerade eine zweite E-Mail geschickt. Darin ist der "
        "Link zum vollständigen Bericht mit allen geprüften Kriterien.")


def aktionsseite(titel: str, text: str, knopf: str, ziel: str,
                 nachweis: str = "", hinweis: str = "") -> str:
    """Seite mit einem Knopf, der die Bestätigung erst auslöst.

    Der Link in der E-Mail führt nur hierher und verändert nichts. Gmail und
    Sicherheits-Gateways rufen Links in Mails automatisch ab; als der
    Endpunkt beim Aufruf noch selbst bestätigte, kam die Berichts-Mail
    fünfzehn Sekunden nach der ersten, ohne Zutun eines Menschen.

    Nur POST zu verlangen reichte nicht — in vier Testläufen bestätigte sich
    jede Anfrage weiterhin von allein, es wurde also tatsächlich abgeschickt.
    Deshalb die zweite Hürde: Das Feld ``nachweis`` ist im ausgelieferten
    HTML **leer**. Sein Wert steht in einem ``data``-Attribut am Knopf und
    wandert erst dann ins Feld, wenn jemand den Knopf wirklich anfasst —
    ``pointerdown`` oder Tastendruck. Wer das Formular blind abschickt, wer
    kein JavaScript ausführt und wer die Seite nur rendert, ohne sie zu
    bedienen, schickt ein leeres Feld und erreicht nichts.

    Preis: Ohne JavaScript lässt sich nicht bestätigen. Der Weg hierher führt
    über ein JavaScript-Widget, insofern ist das keine neue Anforderung.
    """
    warnung = ""
    if hinweis:
        warnung = (f'<p style="margin:0 0 20px;padding:12px 14px;'
                   f'background:{brand.WARN_BG};border-radius:8px;font-size:13px;'
                   f'line-height:1.6;color:{brand.WARN}">{hinweis}</p>')

    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>{titel}</title></head>
<body style="margin:0;background:{brand.SURFACE};font-family:{brand.FONT_SANS};
             display:flex;align-items:center;justify-content:center;
             min-height:100vh;padding:20px">
<div style="background:{brand.WHITE};border-radius:12px;max-width:460px;
            width:100%;overflow:hidden">
  <div style="background:{brand.DARK};padding:20px 28px">{_wortmarke()}</div>
  <div style="padding:32px 28px;text-align:center">
    <h1 style="font-size:20px;font-weight:900;margin:0 0 10px;
               color:{brand.DARK}">{titel}</h1>
    <p style="font-size:14px;color:{brand.TEXT_60};line-height:1.7;
              margin:0 0 24px">{text}</p>
    {warnung}
    <form method="post" action="{ziel}" style="margin:0" id="kpg-form">
      <input type="hidden" name="nachweis" id="kpg-nachweis" value="">
      <button type="submit" id="kpg-knopf" data-nachweis="{nachweis}"
              style="display:inline-block;border:0;cursor:pointer;
              background:{brand.YELLOW};color:{brand.DARK};font-weight:900;
              font-size:15px;font-family:inherit;padding:14px 28px;
              border-radius:6px">{knopf}</button>
    </form>
    <noscript><p style="margin:18px 0 0;font-size:13px;color:{brand.ERROR}">
      Für die Bestätigung wird JavaScript benötigt.</p></noscript>
  </div>
</div>
<script>
  /* Der Nachweis wandert erst bei einer echten Geste ins Formular. Ein
     Dienst, der die Seite nur abruft oder das Formular blind abschickt,
     sendet ein leeres Feld — und bestätigt damit nichts. */
  (function () {{
    var knopf = document.getElementById('kpg-knopf');
    var feld = document.getElementById('kpg-nachweis');
    function belegen() {{ feld.value = knopf.getAttribute('data-nachweis'); }}
    ['pointerdown', 'mousedown', 'touchstart', 'keydown'].forEach(function (art) {{
      knopf.addEventListener(art, belegen);
    }});
  }})();
</script>
</body></html>"""


def _hinweisseite(zeichen: str, farbe: str, title: str, text: str) -> str:
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>{title}</title></head>
<body style="margin:0;background:{brand.SURFACE};font-family:{brand.FONT_SANS};
             display:flex;align-items:center;justify-content:center;
             min-height:100vh;padding:20px">
<div style="background:{brand.WHITE};border-radius:12px;max-width:440px;
            width:100%;overflow:hidden">
  <div style="background:{brand.DARK};padding:20px 28px">{_wortmarke()}</div>
  <div style="padding:32px 28px;text-align:center">
    <div style="width:52px;height:52px;margin:0 auto 18px;border-radius:50%;
                background:{farbe};color:{brand.WHITE};font-size:26px;
                font-weight:900;line-height:52px">{zeichen}</div>
    <h1 style="font-size:20px;font-weight:900;margin:0 0 10px;
               color:{brand.DARK}">{title}</h1>
    <p style="font-size:14px;color:{brand.TEXT_60};line-height:1.7;margin:0">
      {text}</p>
  </div>
</div></body></html>"""
