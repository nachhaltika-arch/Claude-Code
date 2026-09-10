#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Alle Ansichten des Trichters nebeneinander — lokal, ohne Deploy.

**Wozu.** Bis heute war der einzige Weg, eine Änderung an Widget, Teaser,
Berichtsseite oder Mail zu sehen: committen, pushen, warten, bis Render den
Staging-Server neu gebaut hat, und dort einen Durchlauf starten. Das dauert
je nach Auslastung zwischen einer und sieben Minuten, kostet einen CI-Lauf
und macht Staging währenddessen für einen ruhigen Test unbrauchbar. Eine
falsche Zeile im Kleingedruckten wurde so erst produktiv sichtbar.

**Was gezeigt wird.** Die echten Erzeugnisse, nicht Nachbauten: Das Widget
ist die ausgelieferte Datei, die Berichtsseite kommt aus
`services/bericht_seite.rendern`, die Mails aus denselben Funktionen, die
sie auch verschicken. Was hier steht, steht auch beim Kunden — der einzige
Unterschied sind die Daten, und die sind erkennbar erfunden.

**Was NICHT geprüft wird.** Ob die Analyse richtig misst, ob Mails ankommen,
ob Stripe zahlt. Die Vorschau zeigt Oberflächen, keine Abläufe. Wer hier
etwas Grünes sieht, hat den Trichter nicht getestet, sondern angesehen.

    python3 scripts/trichter-vorschau.py

Danach http://127.0.0.1:8973 im Browser.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import webbrowser
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(WURZEL, "kompagnon", "backend")
EMBED = os.path.join(WURZEL, "kompagnon", "frontend", "public", "embed")

sys.path.insert(0, BACKEND)
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

PORT = 8973

# Die Landingpage liegt als fertiger Export vor und hat keine versionierte
# Quelle (L-20) — sie wird gezeigt, wie sie ist. Sie kommt nicht aus dem
# Frontend-Verzeichnis: Sie wird nicht von Render ausgeliefert, sondern von
# Hand zu Mittwald hochgeladen. Deshalb liegt sie unter `docs/`, wo klar
# ist, dass sie hier nur einen Verlauf hat und keinen Ausgang.
LANDINGPAGE = os.environ.get("LANDINGPAGE") or os.path.join(
    WURZEL, "docs", "landingpage", "websprint-landingpage.html")


# ══════════════════════════════════════════════════════════════════════
# Erfundene Daten — als solche erkennbar
# ══════════════════════════════════════════════════════════════════════

class Audit:
    """Ein Befund, wie ihn die Analyse liefert. Die Werte sind erfunden.

    Bewusst **nicht** rund: 61 Punkte mit ungleich verteilten Kategorien
    zeigen Balken in unterschiedlichen Längen. Ein glatter Musterdatensatz
    zeigt eine Seite, die es so nie gibt.
    """

    id = 1
    company_name = "Musterbetrieb Heizung & Sanitär GmbH"
    website_url = "https://www.musterbetrieb-beispiel.de"
    status = "completed"
    level = "Homepage Standard Bronze"
    seiten_geprueft = 6
    seiten_gefunden = 9
    error_message = None

    def __init__(self, punkte: int = 61):
        werte, quellen, abdeckung, erreicht = wertungen(punkte)
        # **Die Kopfzahl ist die Summe, nicht der Wunsch.** Wenn sich die
        # Zielpunktzahl aus dem Katalog nicht genau treffen laesst, steht
        # oben, was unten zusammenkommt — sonst widerspricht der Bericht
        # sich selbst, und niemand weiss, welche Zahl gilt.
        self.total_score = erreicht
        self.coverage = abdeckung
        self.item_scores = werte
        self.item_sources = quellen
        self.item_belege = {}
        self.top_issues = json.dumps(MAENGEL)
        self.blockers = json.dumps(BLOCKER)
        self.erkannte_branche = "Heizung, Sanitär, Klima"
        self.branchenklasse = "handwerk"


#: Anteil der Kriterien, der **nicht erhoben** wird. 78 % Abdeckung ist der
#: heutige Produktivzustand (der PageSpeed-Schlüssel arbeitet nicht), und
#: „nicht erhoben" muss in der Vorschau sichtbar sein: Es ist etwas anderes
#: als Null, und die Seite stellt es anders dar.
NICHT_ERHOBEN_JEDES = 4


def wertungen(ziel: int):
    """Einzelwertungen aus dem **echten** Katalog, auf die Zielpunktzahl gebracht.

    **Warum nicht abgetippt.** Die erste Fassung dieser Vorschau erfand
    Kennungen wie `impressum_vorhanden`; der Katalog führt `rc_impressum`.
    Damit fand die Berichtsseite zu keinem einzigen Kriterium etwas — die
    Kategorien blieben leer, die Maßnahmentabelle hatte eine Zeile, und die
    Vorschau zeigte eine Seite, die es so nie gibt. Eine Vorschau mit
    erfundenen Schlüsseln prüft nichts.

    Der Mix ist bewusst ungleich: volle, halbe und leere Wertungen
    nebeneinander, dazu jedes vierte Kriterium ohne Ergebnis. Ein
    gleichmäßig gefüllter Befund zeigt Balken, die alle gleich aussehen.
    """
    from services.audit_criteria import all_criteria

    kriterien = list(all_criteria())
    gemessen = [k for i, k in enumerate(kriterien) if i % NICHT_ERHOBEN_JEDES != 3]

    # **Eine hohe Punktzahl setzt eine hohe Abdeckung voraus.** Bei 78 %
    # erhobenen Kriterien sind rechnerisch höchstens 80 Punkte erreichbar —
    # die Abnahmezusage über 85 ist damit heute unerreichbar (L-165). Das
    # ist keine Eigenart der Vorschau, sondern der Produktivzustand. Wer
    # hier trotzdem 88 einstellt, bekommt vollständige Abdeckung dazu, statt
    # eine Zahl, die der Befund nicht trägt.
    if sum(k.max_points for k in gemessen) < ziel:
        gemessen = kriterien

    # Ein festes Muster statt Zufall: dieselbe Punktzahl ergibt immer
    # denselben Befund, sonst springt die Vorschau bei jedem Neuladen.
    muster = (1.0, 0.0, 0.5, 1.0, 0.34, 0.0, 0.67, 0.5)
    werte = {}
    for i, k in enumerate(gemessen):
        werte[k.key] = int(round(k.max_points * muster[i % len(muster)]))

    # Auf die Zielpunktzahl nachziehen — je Durchgang ein Punkt, damit sich
    # die Abweichung über den ganzen Befund verteilt und nicht ein Kriterium
    # den Rest schluckt.
    hoechst = {k.key: k.max_points for k in gemessen}
    for _ in range(sum(hoechst.values()) + 1):
        stand = sum(werte.values())
        if stand == ziel:
            break
        richtung = 1 if stand < ziel else -1
        geaendert = False
        for schluessel in werte:
            neu_wert = werte[schluessel] + richtung
            if 0 <= neu_wert <= hoechst[schluessel]:
                werte[schluessel] = neu_wert
                geaendert = True
                if sum(werte.values()) == ziel:
                    break
        if not geaendert:
            break

    quellen = {k.key: getattr(k.source, "value", str(k.source)) for k in gemessen}
    abdeckung = round(100 * len(gemessen) / len(kriterien))
    return werte, quellen, abdeckung, sum(werte.values())


MAENGEL = [
    {"titel": "Kein Einwilligungswerkzeug erkannt",
     "beschreibung": "Ohne Einwilligung dürfen keine Analyse-Dienste laden.",
     "schwere": "hoch"},
    {"titel": "Keine Erklärung zur Barrierefreiheit",
     "beschreibung": "Seit 2025 für viele Betriebe Pflicht.",
     "schwere": "mittel"},
    {"titel": "Bilder ohne Alternativtexte",
     "beschreibung": "Screenreader lesen nichts vor, Suchmaschinen sehen nichts.",
     "schwere": "mittel"},
    {"titel": "Keine strukturierten Daten",
     "beschreibung": "Der Betrieb erscheint nicht als Unternehmen in der Suche.",
     "schwere": "mittel"},
    {"titel": "Tastaturbedienung nicht möglich",
     "beschreibung": "Wer keine Maus benutzt, kommt durch das Menü nicht hindurch.",
     "schwere": "hoch"},
]

#: **Kennungen, keine Sätze.** `detect_blockers` legt genau diese Zeichen-
#: ketten ab; die lesbaren Fassungen stehen in `BLOCKER_LABELS`. Die erste
#: Fassung dieser Vorschau erfand hier Wörterbücher mit fertigen Texten —
#: und verdeckte damit genau den Fehler, den sie dann doch gefunden hat:
#: Die Berichtsseite reichte die Kennung ungeübersetzt an den Kunden durch.
BLOCKER = ["tracking_ohne_consent", "cookies_ohne_consent"]


# ══════════════════════════════════════════════════════════════════════
# Der Katalog — aus `startphase.py`, nicht aus dieser Datei
# ══════════════════════════════════════════════════════════════════════

def katalog() -> dict:
    """Die Produktzeilen, wie die Startphase sie anlegt.

    **Warum nicht abgetippt.** Preise und Leistungen stehen an genau einer
    Stelle (L-29). Eine Vorschau mit eigenen Zahlen zeigt ein Angebot, das
    es nicht gibt — und wäre damit gefährlicher als keine Vorschau.
    """
    from startphase import produkt_vorlage

    return {p["slug"]: p for p in produkt_vorlage()}


class KatalogDb:
    """Gerade genug Datenbank, dass die Berichtsseite ihre Produkte findet."""

    def __init__(self):
        self.zeilen = katalog()

    def execute(self, sql, params=None):
        slug = (params or {}).get("s")
        treffer = self.zeilen.get(slug)
        if treffer:
            treffer = {k: treffer.get(k) for k in (
                "slug", "name", "price_netto", "price_brutto",
                "delivery_days", "features")}

        class Ergebnis:
            def mappings(self_):
                class M:
                    def first(self__):
                        return treffer
                return M()
        return Ergebnis()

    def rollback(self):
        pass

    def query(self, *a, **k):
        raise NotImplementedError(
            "Die Vorschau hat keine Datenbank — diese Ansicht braucht eine.")

    def commit(self):
        pass


# ══════════════════════════════════════════════════════════════════════
# Die Regler
# ══════════════════════════════════════════════════════════════════════

#: Was sich oben in der Leiste einstellen lässt. Jeder Regler schaltet
#: etwas, das auf der Kundenseite eine **Aussage** ist — deshalb steht
#: neben jedem, was er behauptet.
REGLER = [
    {"name": "punkte", "label": "Punktzahl", "typ": "zahl", "vorgabe": "61",
     "hinweis": "Ab 85 verschwindet die Angebotsbegründung: Wer so weit ist, "
                "braucht keinen Relaunch."},
    {"name": "rabatt", "label": "Rabatt", "typ": "schalter", "vorgabe": "",
     "hinweis": "25 % / WS25 — der Code muss in Stripe existieren."},
    {"name": "abnahme", "label": "Abnahmezusage", "typ": "zahl", "vorgabe": "",
     "hinweis": "Punktzahl, ab der ohne Aufpreis nachgearbeitet wird. Leer = keine Zusage."},
    {"name": "knappheit", "label": "Freie Plätze", "typ": "schalter", "vorgabe": "",
     "hinweis": "Zwei Sprint-Plätze im Oktober frei — muss stimmen, solange es dasteht."},
    {"name": "kaufwege", "label": "Kaufknöpfe", "typ": "schalter", "vorgabe": "an",
     "hinweis": "Aus: die Knöpfe führen in den Terminkalender statt zu Stripe."},
]

KAUF_RELAUNCH = "https://buy.stripe.com/aFa8wP8FR6WZdsG0no9Zm00"
KAUF_CHECK = "https://buy.stripe.com/eVq8wP9JV4ORdsGgmm9Zm01"


def einstellungen_aus(regler: dict) -> dict:
    """Die Regler in genau die Einstellungen, die auch produktiv gelesen werden."""
    an = lambda name: bool(regler.get(name))  # noqa: E731
    werte = {
        "widget_booking_url": "https://kalender.example/kompagnon/20-minuten",
        "bericht_abnahmepunkte": (regler.get("abnahme") or "").strip(),
        "bericht_knappheit": ("Zwei Sprint-Plätze im Oktober frei"
                              if an("knappheit") else ""),
    }
    if an("rabatt"):
        werte["bericht_rabattsatz"] = "25 % Rabatt für die ersten 25 Kunden"
        werte["bericht_rabattcode"] = "WS25"
    if an("kaufwege"):
        werte["bericht_kauf_relaunch_url"] = KAUF_RELAUNCH
        werte["widget_check_plus_url"] = KAUF_CHECK
    return werte


# ══════════════════════════════════════════════════════════════════════
# Die Ansichten
# ══════════════════════════════════════════════════════════════════════

def ansicht_bericht(regler: dict) -> bytes:
    from services import bericht_seite

    punkte = int(regler.get("punkte") or 61)
    seite = bericht_seite.rendern(
        KatalogDb(), Audit(punkte), token="vorschau-token",
        einstellungen=einstellungen_aus(regler))
    return seite.encode("utf-8")


def ansicht_mail_bestaetigung(regler: dict) -> bytes:
    from services import widget_report

    _betreff, html = widget_report.verify_email(
        Audit.company_name, "vorschau-verify-token")
    return _mailrahmen("E-Mail 1 — Bitte bestätigen Sie Ihre Adresse",
                       _betreff, html)


def ansicht_mail_bericht(regler: dict) -> bytes:
    from services import mail_vorlagen, widget_report

    _betreff, html = mail_vorlagen.audit_fertig_mail(
        Audit.company_name, widget_report.report_url("vorschau-token"))
    return _mailrahmen("E-Mail 2 — Ihre Analyse ist fertig", _betreff, html)


def ansicht_mail_erinnerung(regler: dict) -> bytes:
    from services import lead_nachfassen

    _betreff, html = lead_nachfassen.erinnerung_bericht_mail(
        Audit.company_name, "vorschau-token")
    return _mailrahmen("E-Mail 3 — Erinnerung, drei Tage später",
                       _betreff, html)


def _mailrahmen(titel: str, betreff, html) -> bytes:
    """Eine Mail im Postfach-Rahmen — mit Betreff, so wie sie ankommt.

    Der Betreff ist die Hälfte der Wirkung und stand bisher nirgends zum
    Nachlesen.
    """
    if isinstance(betreff, (list, tuple)):
        betreff = betreff[0]
    kopf = (
        f'<div style="font:14px/1.5 system-ui;background:#F0F4F5;'
        f'padding:14px 18px;border-bottom:1px solid #D5E0E2">'
        f'<div style="font-size:11px;letter-spacing:.12em;text-transform:uppercase;'
        f'color:#4A5A5C;font-weight:700">{titel}</div>'
        f'<div style="margin-top:6px"><strong>Betreff:</strong> {betreff}</div>'
        f'<div style="color:#4A5A5C">Von: KOMPAGNON &lt;info@kompagnon.eu&gt;</div>'
        f"</div>")
    return (kopf + (html or "")).encode("utf-8")


def ansicht_widget(regler: dict, auto: bool = False) -> bytes:
    """Die ausgelieferte Widget-Datei, auf die Vorschau gerichtet.

    ``auto`` füllt das Formular und schickt es ab, damit man den Teaser
    sieht, ohne jedes Mal zu tippen. Das Skript wird **angehängt**, nicht
    eingebaut: Was oberhalb steht, ist Zeichen für Zeichen die Datei, die
    auf fremden Seiten liegt.
    """
    with open(os.path.join(EMBED, "audit-widget.html"), encoding="utf-8") as f:
        html = f.read()

    basis = f"http://127.0.0.1:{PORT}"
    html = html.replace("<body", f'<body data-api="{basis}"', 1)

    if auto:
        html += """
<script>
/* Nur in der Vorschau: füllt das Formular und schickt es ab. */
(function () {
  function tippen(el, wert) {
    if (!el) return;
    el.value = wert;
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }
  function los() {
    /* Die beiden Felder heissen im ausgelieferten Widget so. Wer sie
       umbenennt, sieht hier ein leeres Formular statt eines Teasers —
       besser als ein Teaser mit Werten, die nicht aus dem Formular kamen. */
    var url = document.getElementById('kpg-url');
    var mail = document.getElementById('kpg-email');
    var f = url && url.form ? url.form : document.querySelector('form');
    if (!url || !mail || !f) return setTimeout(los, 120);
    tippen(url, 'https://www.musterbetrieb-beispiel.de');
    tippen(mail, 'vorschau@example.org');
    setTimeout(function () { f.requestSubmit ? f.requestSubmit() : f.submit(); }, 200);
  }
  setTimeout(los, 400);
})();
</script>"""
    return html.encode("utf-8")


def ansicht_landingpage(regler: dict) -> bytes:
    if not os.path.exists(LANDINGPAGE):
        return _hinweisseite(
            "Landingpage nicht gefunden",
            f"Erwartet unter <code>{LANDINGPAGE}</code>. Die Seite hat keine "
            "versionierte Quelle (L-20) — sie liegt als fertiger Export unter "
            "<code>docs/landingpage/</code> und wird von Hand zu Mittwald "
            "hochgeladen. Eine andere Datei zeigen: "
            "<code>LANDINGPAGE=/pfad/zur/datei.html python3 "
            "scripts/trichter-vorschau.py</code>")
    with open(LANDINGPAGE, "rb") as f:
        return f.read()


def _hinweisseite(titel: str, text: str) -> bytes:
    return (f'<div style="font:15px/1.7 system-ui;padding:40px;max-width:60ch">'
            f'<h1 style="font-size:20px">{titel}</h1><p>{text}</p></div>'
            ).encode("utf-8")


ANSICHTEN = [
    {"schluessel": "landingpage", "titel": "1 · Landingpage",
     "unter": "websprint.kompagnon.eu", "bauer": ansicht_landingpage,
     "hinweis": "Fertiger Export, keine versionierte Quelle (L-20). "
                "Änderungen hier ersetzen die Datei, die hochgeladen wird."},
    {"schluessel": "widget", "titel": "2 · Widget, Formular",
     "unter": "eingebettet auf der Landingpage", "bauer": ansicht_widget,
     "hinweis": "Die ausgelieferte Datei, gegen diese Vorschau als Server."},
    {"schluessel": "teaser", "titel": "3 · Widget, Ergebnis",
     "unter": "nach der Analyse", "bauer": lambda r: ansicht_widget(r, auto=True),
     "hinweis": "Das Formular wird automatisch abgeschickt. Die Analyse ist "
                "erfunden — geprüft wird die Darstellung, nicht die Messung."},
    {"schluessel": "mail-bestaetigung", "titel": "4 · E-Mail 1",
     "unter": "Adresse bestätigen", "bauer": ansicht_mail_bestaetigung,
     "hinweis": "Enthält bewusst nichts über die Website — die Adresse ist "
                "zu diesem Zeitpunkt ungeprüft."},
    {"schluessel": "mail-bericht", "titel": "5 · E-Mail 2",
     "unter": "Analyse ist fertig", "bauer": ansicht_mail_bericht,
     "hinweis": "Geht erst nach dem Klick in E-Mail 1 heraus."},
    {"schluessel": "bericht", "titel": "6 · Berichtsseite",
     "unter": "die Verkaufsseite", "bauer": ansicht_bericht,
     "hinweis": "Die Regler oben wirken auf diese Ansicht."},
    {"schluessel": "mail-erinnerung", "titel": "7 · E-Mail 3",
     "unter": "Erinnerung nach 3 Tagen", "bauer": ansicht_mail_erinnerung,
     "hinweis": "Nur an bestätigte Adressen, die den Bericht nicht geöffnet haben."},
]


# ══════════════════════════════════════════════════════════════════════
# Der Server
# ══════════════════════════════════════════════════════════════════════

def api_config(regler: dict) -> dict:
    from services import check_plus_angebot

    zeile = katalog().get("check_plus") or {}
    e = einstellungen_aus(regler)
    angebot = None
    if zeile:
        angebot = check_plus_angebot.aus_zeile(
            {**zeile, "status": "live"}, e.get("widget_check_plus_url", ""))
    return {
        "privacy_url": "https://www.kompagnon.eu/datenschutz",
        "checkout_url": e["widget_booking_url"],
        "headline": "",
        "criteria_count": len(katalog_kriterien()),
        "facebook_pixel_id": "",
        "check_plus": angebot,
    }


def katalog_kriterien():
    from services.audit_criteria import all_criteria

    return list(all_criteria())


def api_teaser(regler: dict) -> dict:
    befund = Audit(int(regler.get("punkte") or 61))
    return {
        "status": "completed",
        "website_url": Audit.website_url,
        "company_name": Audit.company_name,
        "total_score": befund.total_score,
        "level": Audit.level,
        "coverage": befund.coverage,
        "seiten_geprueft": Audit.seiten_geprueft,
        "seiten_gefunden": Audit.seiten_gefunden,
        "top_issues": MAENGEL[:3],
        "blocker_count": len(BLOCKER),
        "email_sent": True,
        "bestaetigung_versandt": True,
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    # ── Antworten ────────────────────────────────────────────────────
    def _senden(self, koerper: bytes, typ="text/html; charset=utf-8", code=200):
        self.send_response(code)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(len(koerper)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(koerper)

    def _json(self, daten, code=200):
        self._senden(json.dumps(daten).encode("utf-8"),
                     "application/json; charset=utf-8", code)

    def _regler(self):
        frage = urllib.parse.urlparse(self.path).query
        roh = urllib.parse.parse_qs(frage)
        return {k: v[0] for k, v in roh.items() if v and v[0]}

    # ── Wege ─────────────────────────────────────────────────────────
    def do_OPTIONS(self):
        self._senden(b"", code=204)

    def do_POST(self):
        pfad = urllib.parse.urlparse(self.path).path
        laenge = int(self.headers.get("Content-Length") or 0)
        if laenge:
            self.rfile.read(laenge)
        if pfad == "/api/widget/audit":
            self._json({"poll_token": "vorschau-token", "status": "pending"})
        elif pfad.startswith("/api/widget/bestaetigung/"):
            self._json({"versandt": True})
        else:
            self._json({"detail": "In der Vorschau nicht vorgesehen."}, 404)

    def do_GET(self):
        pfad = urllib.parse.urlparse(self.path).path
        regler = self._regler()

        if pfad == "/":
            return self._senden(index_seite(regler))
        if pfad == "/api/widget/config":
            return self._json(api_config(regler))
        if pfad.startswith("/api/widget/teaser/"):
            return self._json(api_teaser(regler))
        if pfad.startswith("/ansicht/"):
            schluessel = pfad[len("/ansicht/"):].strip("/")
            for a in ANSICHTEN:
                if a["schluessel"] == schluessel:
                    try:
                        return self._senden(a["bauer"](regler))
                    except Exception as fehler:  # noqa: BLE001
                        import traceback
                        return self._senden(_fehlerseite(a["titel"], fehler,
                                                         traceback.format_exc()),
                                            code=500)
            return self._senden(_hinweisseite("Unbekannte Ansicht", schluessel), code=404)

        return self._senden(_hinweisseite("Nicht gefunden", pfad), code=404)


def _fehlerseite(titel: str, fehler: Exception, spur: str) -> bytes:
    """Ein Fehler in der Vorschau wird gezeigt, nicht verschluckt.

    Eine leere Kachel wäre die schlechteste Rückmeldung: Sie sieht aus wie
    „hier ist nichts vorgesehen" und ist in Wahrheit ein Absturz.
    """
    import html as _h
    return (
        f'<div style="font:14px/1.6 ui-monospace,Menlo,monospace;padding:28px">'
        f'<h1 style="font:900 18px system-ui;color:#B3261E">'
        f"{_h.escape(titel)} lässt sich nicht bauen</h1>"
        f'<p style="font:15px/1.6 system-ui">{_h.escape(str(fehler))}</p>'
        f'<pre style="white-space:pre-wrap;background:#F0F4F5;padding:14px;'
        f'border-radius:6px;font-size:12px">{_h.escape(spur)}</pre></div>'
    ).encode("utf-8")


# ══════════════════════════════════════════════════════════════════════
# Die Übersicht
# ══════════════════════════════════════════════════════════════════════

def index_seite(regler: dict) -> bytes:
    frage = urllib.parse.urlencode(regler)
    ansichten = [{"schluessel": a["schluessel"], "titel": a["titel"],
                  "unter": a["unter"], "hinweis": a["hinweis"]}
                 for a in ANSICHTEN]
    gebaut = datetime.now().strftime("%d.%m.%Y, %H:%M")
    return VORLAGE.replace("__ANSICHTEN__", json.dumps(ansichten, ensure_ascii=False)) \
                  .replace("__REGLER__", json.dumps(REGLER, ensure_ascii=False)) \
                  .replace("__WERTE__", json.dumps(regler, ensure_ascii=False)) \
                  .replace("__FRAGE__", frage) \
                  .replace("__GEBAUT__", gebaut) \
                  .encode("utf-8")


VORLAGE = """<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trichter — Vorschau</title>
<style>
  :root { --dunkel:#004F59; --mittel:#008EAA; --gelb:#FAE600; --ink:#000;
          --grau:#4A5A5C; --linie:#D5E0E2; --flaeche:#F0F4F5; }
  * { box-sizing:border-box }
  body { margin:0; font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;
         color:var(--ink); background:var(--flaeche); height:100vh;
         display:grid; grid-template-columns:264px 1fr; }
  aside { background:#fff; border-right:1px solid var(--linie); overflow-y:auto;
          display:flex; flex-direction:column }
  aside h1 { margin:0; padding:18px 18px 6px; font-size:15px; font-weight:900;
             color:var(--dunkel); letter-spacing:-.01em }
  aside .stand { padding:0 18px 14px; font-size:11.5px; color:var(--grau) }
  nav a { display:block; padding:11px 18px; text-decoration:none; color:var(--ink);
          border-left:3px solid transparent }
  nav a:hover { background:var(--flaeche) }
  nav a.an { background:var(--flaeche); border-left-color:var(--gelb); font-weight:700 }
  nav a small { display:block; color:var(--grau); font-weight:400; font-size:11.5px;
                margin-top:2px }
  .regler { border-top:1px solid var(--linie); padding:14px 18px; margin-top:auto }
  .regler h2 { margin:0 0 10px; font-size:11px; letter-spacing:.12em;
               text-transform:uppercase; color:var(--grau) }
  .regler label { display:block; margin-bottom:12px; font-size:12.5px }
  .regler label b { display:block; font-weight:700; margin-bottom:3px }
  .regler input[type=number], .regler input[type=text] {
      width:100%; padding:6px 8px; border:1px solid var(--linie); border-radius:5px;
      font:inherit }
  .regler .zeile { display:flex; gap:8px; align-items:center }
  .regler small { display:block; color:var(--grau); font-size:11px; margin-top:3px;
                  line-height:1.45 }
  main { display:flex; flex-direction:column; min-width:0 }
  .leiste { background:#fff; border-bottom:1px solid var(--linie); padding:10px 16px;
            display:flex; gap:14px; align-items:center; flex-wrap:wrap }
  .leiste .titel { font-weight:900; color:var(--dunkel) }
  .leiste .hinweis { color:var(--grau); font-size:12.5px; flex:1; min-width:200px }
  .geraete button { border:1px solid var(--linie); background:#fff; padding:5px 11px;
                    border-radius:5px; font:inherit; cursor:pointer }
  .geraete button.an { background:var(--dunkel); color:#fff; border-color:var(--dunkel) }
  .buehne { flex:1; overflow:auto; display:flex; justify-content:center;
            padding:18px; background:var(--flaeche) }
  iframe { border:1px solid var(--linie); background:#fff; border-radius:8px;
           width:100%; height:100%; }
  .rahmen { background:#fff; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,.08);
            height:100%; transition:width .15s }
</style></head>
<body>
<aside>
  <h1>Trichter — Vorschau</h1>
  <div class="stand">lokal · Stand __GEBAUT__</div>
  <nav id="nav"></nav>
  <div class="regler">
    <h2>Regler</h2>
    <form id="regler"></form>
  </div>
</aside>
<main>
  <div class="leiste">
    <span class="titel" id="titel"></span>
    <span class="hinweis" id="hinweis"></span>
    <span class="geraete" id="geraete"></span>
  </div>
  <div class="buehne"><div class="rahmen" id="rahmen"><iframe id="rahmenInhalt"></iframe></div></div>
</main>
<script>
var ANSICHTEN = __ANSICHTEN__;
var REGLER = __REGLER__;
var WERTE = __WERTE__;
var FRAGE = "__FRAGE__";

var GERAETE = [
  { name: "Desktop", breite: "100%" },
  { name: "Tablet",  breite: "834px" },
  { name: "Mobil",   breite: "390px" }
];
var geraet = 0;
var aktuell = location.hash.slice(1) || ANSICHTEN[0].schluessel;

function frage() {
  var p = new URLSearchParams();
  REGLER.forEach(function (r) {
    var el = document.querySelector('[name="' + r.name + '"]');
    if (!el) return;
    var wert = el.type === "checkbox" ? (el.checked ? "an" : "") : el.value.trim();
    if (wert) p.set(r.name, wert);
  });
  return p.toString();
}

function zeichneNav() {
  document.getElementById("nav").innerHTML = ANSICHTEN.map(function (a) {
    return '<a href="#' + a.schluessel + '" class="' +
      (a.schluessel === aktuell ? "an" : "") + '">' + a.titel +
      "<small>" + a.unter + "</small></a>";
  }).join("");
}

function zeichneRegler() {
  document.getElementById("regler").innerHTML = REGLER.map(function (r) {
    var wert = WERTE[r.name] !== undefined ? WERTE[r.name] : r.vorgabe;
    var eingabe;
    if (r.typ === "schalter") {
      eingabe = '<span class="zeile"><input type="checkbox" name="' + r.name + '"' +
        (wert ? " checked" : "") + "> <span>zeigen</span></span>";
    } else {
      eingabe = '<input type="number" min="0" max="100" name="' + r.name +
        '" value="' + (wert || "") + '" placeholder="leer">';
    }
    return "<label><b>" + r.label + "</b>" + eingabe +
      "<small>" + r.hinweis + "</small></label>";
  }).join("");
  document.getElementById("regler").addEventListener("input", laden);
}

function zeichneGeraete() {
  document.getElementById("geraete").innerHTML = GERAETE.map(function (g, i) {
    return '<button data-i="' + i + '" class="' + (i === geraet ? "an" : "") +
      '">' + g.name + "</button>";
  }).join(" ");
  document.getElementById("geraete").onclick = function (e) {
    if (!e.target.dataset.i) return;
    geraet = +e.target.dataset.i;
    zeichneGeraete();
    document.getElementById("rahmen").style.width = GERAETE[geraet].breite;
  };
}

function laden() {
  var a = ANSICHTEN.filter(function (x) { return x.schluessel === aktuell; })[0]
        || ANSICHTEN[0];
  document.getElementById("titel").textContent = a.titel;
  document.getElementById("hinweis").textContent = a.hinweis;
  var q = frage();
  document.getElementById("rahmenInhalt").src =
    "/ansicht/" + a.schluessel + (q ? "?" + q : "");
  zeichneNav();
  history.replaceState(null, "", "#" + aktuell);
}

window.addEventListener("hashchange", function () {
  aktuell = location.hash.slice(1) || ANSICHTEN[0].schluessel;
  laden();
});

zeichneRegler();
zeichneGeraete();
document.getElementById("rahmen").style.width = GERAETE[geraet].breite;
laden();
</script>
</body></html>"""


def main():
    fehlend = [a["titel"] for a in ANSICHTEN
               if a["schluessel"] == "landingpage" and not os.path.exists(LANDINGPAGE)]
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    adresse = f"http://127.0.0.1:{PORT}"
    print(f"Trichter-Vorschau läuft:  {adresse}")
    print(f"Ansichten: {', '.join(a['schluessel'] for a in ANSICHTEN)}")
    if fehlend:
        print(f"Hinweis: {', '.join(fehlend)} fehlt auf der Platte.")
    print("Beenden mit Strg+C.")
    if "--kein-browser" not in sys.argv:
        webbrowser.open(adresse)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nbeendet.")


if __name__ == "__main__":
    main()
