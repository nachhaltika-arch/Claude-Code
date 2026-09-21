#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ein Durchlauf über den ganzen Trichter, am laufenden System gemessen.

    kompagnon/backend/venv/bin/python scripts/funnel-test.py start
    …/python scripts/funnel-test.py bestaetigen --link <URL aus Mail 1>
    …/python scripts/funnel-test.py bericht     --link <URL aus Mail 2>
    …/python scripts/funnel-test.py stand

Ausgeführt wird er mit `/funneltest` (`.claude/commands/funneltest.md`); der
Befehl holt die beiden Mail-Links aus dem Postfach und liest die Anzeigenseite.

**Wozu.** Das Repo misst Stufen: `systemdurchlauf.py` den Quelltext,
`durchlauf-laufzeit.py` die Seiten, `/kampagne` die Zahlen von gestern. Was
fehlte, ist der eine Lauf, der die Kette **einmal ganz durchgeht** — von der
Form eines Anzeigenklicks bis zum ausgelieferten PDF. Am 12. und 13.09. wurde
das von Hand gemacht, und beide Male fand es einen Fehler, den kein Test hatte
(der PDF-Dateiname, die zweite Mail). Von Hand heißt: nur, wenn jemand daran
denkt.

**Was er nicht ist.** Kein Ersatz für die Tests und kein Urteil über die
Analysequalität. Er sagt, ob die **Kette** trägt, nicht ob die Zahl im Bericht
stimmt.

**Er erzeugt echte Daten.** Produktiv entstehen eine Anfrage, ein Lead, zwei
Mails und ein Brevo-Kontakt. Sie werden nicht aufgeräumt — erkennbar an der
Testadresse, und der Bericht nennt am Ende die Nummern (Entscheidung David,
20.09.2026). Wer das nicht will, nimmt `--ziel staging`.

**Drei Klassen, nie zwei** (Hausregel aus `docs/kampagne/pruefverfahren.md`):
Jeder Punkt ist **gemessen**, **angenommen** oder **nicht erhoben**. Was nicht
erhoben wurde, wird nie als „in Ordnung" ausgewiesen — und nie als Null.

**Zwei Fallen, die beim Bau schon zugeschlagen haben und hier stehen, damit
niemand sie für Befunde hält:**

* **Der Lead wird über die Domain wiederverwendet** (`routers/widget.py:252`),
  und die UTM-Felder werden nie überschrieben — Erstkontakt gewinnt
  (15.09.2026). Ein zweiter Lauf auf dieselbe Testdomain legt also **keinen**
  neuen Lead an. Das ist richtig so und kein Fehlschlag.
* **Die Bestätigungsseite verlangt eine echte Bedienung:** ein Formular mit
  signiertem Beleg und mindestens `BELEG_MINDESTALTER_S` Sekunden zwischen
  Ausgabe und Absenden (`services/widget_report.py:73`). Dieser Lauf wartet
  sie ab. Damit prüft er die **Mechanik** der Bestätigung, nicht den Schutz
  vor Postfach-Scannern — der ist genau das, was hier umgangen wird.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import pathlib
import re
import sys
import time
from dataclasses import dataclass
from typing import Any

try:
    import requests
except ModuleNotFoundError:  # pragma: no cover - Hinweis statt Absturz
    sys.exit("Fehlt: requests. Starte mit kompagnon/backend/venv/bin/python — "
             "das System-Python hat es nicht (Fund vom 15.09.2026).")

WURZEL = pathlib.Path(__file__).resolve().parents[1]
ABLAGE = WURZEL / ".funneltest"
LANDINGPAGE_DATEI = WURZEL / "docs" / "landingpage" / "websprint-landingpage.html"

#: Die drei Adressen je Ziel. Staging hat **keine** eigene Landingpage — die
#: Seite liegt bei Mittwald und zeigt immer auf das Produktivsystem. Deshalb
#: steht dort `None` und die Stufe gilt als nicht erhoben, nicht als grün.
ZIELE = {
    "produktiv": {
        "api": "https://api.kompagnon.group",
        "frontend": "https://kas.kompagnon.group",
        "landingpage": "https://websprint.kompagnon.eu/",
    },
    "staging": {
        "api": "https://kompagnon-backend-staging.onrender.com",
        "frontend": "https://kompagnon-frontend-staging.onrender.com",
        "landingpage": None,
    },
}

#: Die Analyse läuft im Hintergrund. 300 s sind reichlich: Der längste
#: gemessene Lauf lag bei 62 s (12.09.), die PageSpeed-Zeitgrenze bei 120 s.
ANALYSE_GEDULD_S = 300
ANALYSE_TAKT_S = 5

#: Etwas mehr als `BELEG_MINDESTALTER_S` (2 s) in `services/widget_report.py`.
BELEG_WARTEN_S = 3

ABRUF_ZEITGRENZE_S = 30

KLASSEN = ("gemessen", "angenommen", "nicht erhoben")


@dataclass(frozen=True)
class Befund:
    """Eine Zeile des Berichts. Unveränderlich — wer etwas ändert, baut neu."""

    stufe: str
    punkt: str
    klasse: str
    ergebnis: str
    beleg: str = ""

    @property
    def ist_bestanden(self) -> bool:
        return self.klasse == "gemessen" and self.ergebnis.startswith("ok")


def messung(stufe: str, punkt: str, ok: bool, text: str, beleg: str = "") -> Befund:
    return Befund(stufe, punkt, "gemessen", ("ok — " if ok else "FEHLT — ") + text, beleg)


def nicht_erhoben(stufe: str, punkt: str, grund: str) -> Befund:
    return Befund(stufe, punkt, "nicht erhoben", grund)


# ---------------------------------------------------------------- Werkzeuge


def hole(methode: str, adresse: str, **kw) -> tuple[Any, str]:
    """(Antwort, Fehlertext). Genau eins von beiden ist gesetzt.

    Ein Netzfehler ist hier **kein** Befund über das System, sondern eine
    nicht erhobene Messung — deshalb wird er zurückgegeben statt geworfen.
    """
    try:
        antwort = requests.request(methode, adresse, timeout=ABRUF_ZEITGRENZE_S, **kw)
        return antwort, ""
    except requests.RequestException as fehler:
        return None, f"{type(fehler).__name__}: {fehler}"


def sha256(inhalt: bytes) -> str:
    return hashlib.sha256(inhalt).hexdigest()


def jetzt() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def lauf_id() -> str:
    return datetime.datetime.now().strftime("%Y%m%d-%H%M")


def zustand_lesen(kennung: str | None) -> dict:
    """Den jüngsten Lauf lesen, oder den benannten. Fehlt er, bricht es ab."""
    ABLAGE.mkdir(exist_ok=True)
    if kennung:
        datei = ABLAGE / f"lauf-{kennung}.json"
    else:
        laeufe = sorted(ABLAGE.glob("lauf-*.json"))
        if not laeufe:
            sys.exit("Kein Lauf gefunden. Zuerst: funnel-test.py start")
        datei = laeufe[-1]
    if not datei.exists():
        sys.exit(f"Kein Lauf unter {datei}")
    return json.loads(datei.read_text(encoding="utf-8"))


def zustand_schreiben(zustand: dict) -> pathlib.Path:
    """Immer eine **neue** Fassung schreiben, nie die alte verändern."""
    ABLAGE.mkdir(exist_ok=True)
    datei = ABLAGE / f"lauf-{zustand['lauf']}.json"
    neu = {**zustand, "geschrieben": jetzt()}
    datei.write_text(json.dumps(neu, indent=2, ensure_ascii=False), encoding="utf-8")
    return datei


def befunde_anhaengen(zustand: dict, neue: list[Befund]) -> dict:
    """Neuer Zustand mit angehängten Befunden — das Original bleibt."""
    bisher = zustand.get("befunde", [])
    return {**zustand, "befunde": bisher + [b.__dict__ for b in neue]}


# ------------------------------------------------------- Stufe 2: Landingpage


def stufe_landingpage(ziel: dict, klickadresse: str) -> list[Befund]:
    """Die Seite so aufrufen, wie ein Anzeigenklick sie aufruft."""
    if not ziel["landingpage"]:
        return [nicht_erhoben("2 Landingpage", "Seite",
                              "Staging hat keine eigene Landingpage — "
                              "die Seite liegt bei Mittwald und zeigt auf produktiv")]

    antwort, fehler = hole("GET", klickadresse)
    if fehler:
        return [nicht_erhoben("2 Landingpage", "Seite", fehler)]

    inhalt = antwort.content
    befunde = [messung("2 Landingpage", "Antwort", antwort.status_code == 200,
                       f"HTTP {antwort.status_code}, {len(inhalt)} Bytes",
                       klickadresse)]

    if LANDINGPAGE_DATEI.exists():
        gleich = sha256(inhalt) == sha256(LANDINGPAGE_DATEI.read_bytes())
        befunde.append(messung(
            "2 Landingpage", "gleich der Repo-Fassung", gleich,
            f"live {sha256(inhalt)[:12]}…, Repo {sha256(LANDINGPAGE_DATEI.read_bytes())[:12]}…",
            "docs/landingpage/websprint-landingpage.html"))
    else:
        befunde.append(nicht_erhoben("2 Landingpage", "gleich der Repo-Fassung",
                                     f"{LANDINGPAGE_DATEI} fehlt"))

    text = inhalt.decode("utf-8", "replace")
    # **`<kompagnon-audit>`, nicht mehr `audit-widget.html`** (21.09.2026):
    # Die Seite bindet das Widget seither als Web Component ein, nicht als
    # iframe. Wer hier weiter nach dem alten Namen sucht, meldet ein fehlendes
    # Widget auf einer Seite, die es traegt.
    for name, muster in (("Widget eingebettet", "kompagnon-audit"),
                         ("Pixel", "fbq("),
                         ("GA4", "gtag(")):
        treffer = text.count(muster)
        befunde.append(messung("2 Landingpage", name, treffer > 0,
                               f"{treffer}× „{muster}“"))

    # **Die Seite liefert statisch nur rund 930 Zeichen Markup aus**; alles
    # andere hängt sich zur Laufzeit aus zehn Inline-Skripten ein (17.09.2026).
    # Die Sprungmarke steht deshalb **maskiert** in der JSON-Vorlage, nicht als
    # `id="analyse"` im Quelltext. Wer nur die unmaskierte Form sucht, meldet
    # eine fehlende Sprungmarke auf einer Seite, die sie hat — am 21.09.2026
    # genau so passiert. Dass sie wirkt, ist am 17.09. im Browser gemessen
    # (`scrollY` 953 nach dem Laden); von außen ist nur ihr Vorhandensein
    # prüfbar.
    roh = text.count('id="analyse"')
    maskiert = text.count('id=\\"analyse\\"')
    befunde.append(messung(
        "2 Landingpage", "Sprungmarke #analyse", roh + maskiert > 0,
        f"{roh}× roh, {maskiert}× maskiert in der Vorlage, "
        f"{text.count('#analyse')}× als Ziel"))
    return befunde


# --------------------------------------------------- Stufe 3: Widget und Config


def serverweg_befund(ziel: dict) -> Befund:
    """Ob der Serverweg meldebereit ist — steht in `/health`, nicht im Widget.

    Die Widget-Konfiguration enthält **keinen** Schlüssel `meta`; sie ist
    bewusst auf Anzeigewerte beschränkt. Wer sie danach fragt, bekommt `None`
    und meldet einen Ausfall, den es nicht gibt (21.09.2026).
    """
    antwort, fehler = hole("GET", f"{ziel['api']}/health")
    if fehler or antwort.status_code != 200:
        return nicht_erhoben("3 Widget", "Serverweg bereit",
                             fehler or f"/health antwortet {antwort.status_code}")
    meta = antwort.json().get("meta") or {}
    return messung("3 Widget", "Serverweg bereit", bool(meta.get("bereit")),
                   f"bereit={meta.get('bereit')}, Token {meta.get('token_laenge')} "
                   f"Zeichen, Pixel aus {meta.get('pixel_quelle')!r}",
                   f"{ziel['api']}/health")


def stufe_widget(ziel: dict) -> tuple[list[Befund], dict]:
    """Was das geladene Widget vom Server bekommt — Stufe 3 des Trichters."""
    antwort, fehler = hole("GET", f"{ziel['api']}/api/widget/config")
    if fehler:
        return [nicht_erhoben("3 Widget", "Konfiguration", fehler)], {}
    if antwort.status_code != 200:
        return [messung("3 Widget", "Konfiguration", False,
                        f"HTTP {antwort.status_code}")], {}

    config = antwort.json()
    check_plus = config.get("check_plus") or {}
    # **Das Feld heißt `facebook_pixel_id`.** Nach `pixel_id` gefragt, kam
    # `None` — und der Lauf meldete produktiv „Pixelkennung leer", während die
    # Kennung dastand (21.09.2026). Dieselbe Klasse wie `check_plus.kauf_url`
    # am 17.09.: nach dem erwarteten Namen gefragt statt nach der Feldliste.
    befunde = [
        messung("3 Widget", "Konfiguration", True, "HTTP 200",
                f"{ziel['api']}/api/widget/config"),
        messung("3 Widget", "Pixelkennung", bool(config.get("facebook_pixel_id")),
                str(config.get("facebook_pixel_id") or "leer")),
        messung("3 Widget", "Datenschutzlink", bool(config.get("privacy_url")),
                str(config.get("privacy_url") or "leer")),
        messung("3 Widget", "Check PLUS verkäuflich", bool(check_plus.get("verfuegbar")),
                f"verfuegbar={check_plus.get('verfuegbar')}"),
    ]
    befunde.append(serverweg_befund(ziel))

    datei, fehler = hole("GET", f"{ziel['frontend']}/embed/audit-widget.html")
    if fehler:
        befunde.append(nicht_erhoben("3 Widget", "ausgelieferte Datei", fehler))
        return befunde, config

    text = datei.text
    for name, muster in (("Analyse begonnen", "kpg-analyse-begonnen"),
                         ("Lead-Empfänger", "kpg-audit-lead"),
                         ("Ereigniskennung", "eventID")):
        befunde.append(messung("3 Widget", name, muster in text,
                               f"{text.count(muster)}× „{muster}“",
                               f"{ziel['frontend']}/embed/audit-widget.html"))
    return befunde, config


# ------------------------------------------------------------ Stufe 5: Lead


def stufe_lead(ziel: dict, anfrage: dict) -> tuple[list[Befund], dict]:
    """Das Formular absenden — genau das, was das Widget im Browser tut."""
    antwort, fehler = hole("POST", f"{ziel['api']}/api/widget/audit", json=anfrage)
    if fehler:
        return [nicht_erhoben("5 Lead", "Absenden", fehler)], {}

    if antwort.status_code == 429:
        return [Befund("5 Lead", "Absenden", "nicht erhoben",
                       f"Kontingent erschöpft (429): {antwort.text[:120]}")], {}
    if antwort.status_code != 200:
        return [messung("5 Lead", "Absenden", False,
                        f"HTTP {antwort.status_code}: {antwort.text[:160]}")], {}

    daten = antwort.json()
    befunde = [
        messung("5 Lead", "Absenden", True,
                f"HTTP 200, Anfrage {daten.get('request_id')}"),
        messung("5 Lead", "Analyse angestoßen", daten.get("status") == "pending",
                f"status={daten.get('status')}"),
    ]
    return befunde, daten


def stufe_analyse(ziel: dict, poll_token: str) -> tuple[list[Befund], dict]:
    """Warten, bis die Analyse fertig ist — und messen, wie lange das dauert."""
    begonnen = time.monotonic()
    letzter = {}
    while time.monotonic() - begonnen < ANALYSE_GEDULD_S:
        antwort, fehler = hole("GET", f"{ziel['api']}/api/widget/teaser/{poll_token}")
        if fehler:
            return [nicht_erhoben("6 Analyse", "Ergebnis", fehler)], {}
        if antwort.status_code != 200:
            return [messung("6 Analyse", "Ergebnis", False,
                            f"HTTP {antwort.status_code}")], {}
        letzter = antwort.json()
        stand = letzter.get("status")
        if stand == "completed":
            dauer = round(time.monotonic() - begonnen, 1)
            return [
                messung("6 Analyse", "fertig", True, f"nach {dauer} s"),
                messung("6 Analyse", "Punktzahl", letzter.get("total_score") is not None,
                        f"{letzter.get('total_score')} Punkte"),
            ], letzter
        if stand == "failed":
            return [messung("6 Analyse", "fertig", False,
                            f"failed: {letzter.get('fehler')}")], letzter
        time.sleep(ANALYSE_TAKT_S)

    return [nicht_erhoben("6 Analyse", "fertig",
                          f"nach {ANALYSE_GEDULD_S} s noch "
                          f"„{letzter.get('status')}“")], letzter


# ------------------------------------------------- Stufe 8: Bestätigungsklick


def stufe_bestaetigen(link: str) -> list[Befund]:
    """Die Seite aus Mail 1 aufrufen, warten, und das Formular abschicken."""
    seite, fehler = hole("GET", link)
    if fehler:
        return [nicht_erhoben("8 Bestätigung", "Seite", fehler)]
    if seite.status_code != 200:
        return [messung("8 Bestätigung", "Seite", False, f"HTTP {seite.status_code}")]

    befunde = [messung("8 Bestätigung", "Seite", True,
                       f"HTTP 200, {len(seite.content)} Bytes", seite.url)]

    # **Kein Formular ist nicht dasselbe wie ein kaputtes Formular.** Eine
    # schon bestätigte Anfrage zeigt eine Hinweisseite; ein verbrauchter Link
    # ebenso. Beides als „FEHLT" zu führen, wäre ein Fehlalarm bei jedem
    # zweiten Anlauf derselben Phase.
    if 'id="kpg-form"' not in seite.text:
        befunde.append(nicht_erhoben(
            "8 Bestätigung", "Gestenbeleg",
            "die Seite zeigt kein Formular — bereits bestätigt oder Link "
            f"verbraucht: „{sichtbarer_anfang(seite.text, 90)}“"))
        return befunde

    # **Nicht im Feld, sondern am Knopf.** Das Feld `nachweis` wird bewusst
    # leer ausgeliefert; erst ein Ereignis mit `isTrusted === true` kopiert
    # den Wert aus `data-nachweis` hinein (`services/widget_report.py`,
    # Skript am Ende von `aktionsseite`). Wer hier nach `value="…"` sucht,
    # findet nichts und hält den Schutz für einen Defekt — am 20.09.2026
    # genau so passiert.
    treffer = re.search(r'data-nachweis="([^"]+)"', seite.text)
    if not treffer:
        befunde.append(messung("8 Bestätigung", "Gestenbeleg", False,
                               "kein `data-nachweis` am Knopf"))
        return befunde
    befunde.append(messung("8 Bestätigung", "Gestenbeleg", True,
                           "am Knopf vorhanden, wird maschinell eingesetzt"))

    ziel_form = re.search(r'<form[^>]+action="([^"]+)"', seite.text)
    adresse = ziel_form.group(1) if ziel_form else link

    # Die Seite verlangt Mindestalter; wer sofort abschickt, sieht aus wie ein
    # Postfach-Scanner und wird zu Recht abgewiesen.
    time.sleep(BELEG_WARTEN_S)

    antwort, fehler = hole("POST", adresse, data={"nachweis": treffer.group(1)})
    if fehler:
        befunde.append(nicht_erhoben("8 Bestätigung", "Absenden", fehler))
        return befunde

    # **Nicht am Wortlaut messen.** Der erste Entwurf suchte „bestätigt" im
    # Text; die Erfolgsseite sagt aber „Wir haben Ihnen gerade eine zweite
    # E-Mail geschickt" (20.09.2026). Der belastbare Unterschied ist ein
    # anderer: Wird die Geste abgewiesen, kommt **das Formular zurück** —
    # samt `data-nachweis` (`routers/widget.py`, `_geste_fehlt`).
    zurueck_zum_formular = "data-nachweis" in antwort.text
    bestaetigt = antwort.status_code == 200 and not zurueck_zum_formular
    befunde.append(messung("8 Bestätigung", "Absenden", bestaetigt,
                           f"HTTP {antwort.status_code}, "
                           f"{len(antwort.content)} Bytes"
                           + (" — Formular kam zurück" if zurueck_zum_formular else ""),
                           sichtbarer_anfang(antwort.text)))
    return befunde


def sichtbarer_anfang(html: str, zeichen: int = 120) -> str:
    """Was auf der Seite steht — als Beleg, nicht als Prüfkriterium."""
    ohne_skript = re.sub(r"(?s)<(script|style).*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", ohne_skript)
    return " ".join(text.split())[:zeichen]


# -------------------------------------------- Stufen 10 und 11: Bericht, PDF


def stufe_bericht(link: str, kaufweg_erwartet: bool = True) -> list[Befund]:
    """Berichtsseite und PDF — das, was beim Kunden ankommt.

    `kaufweg_erwartet` kommt aus Stufe 3: Steht Check PLUS auf dem Ziel nicht
    verkäuflich, **kann** kein Zahllink auf der Seite stehen. Das als Mangel
    zu melden wäre ein Fehlalarm aus der eigenen Bauart — auf Staging tritt er
    bei jedem Lauf auf.
    """
    seite, fehler = hole("GET", link)
    if fehler:
        return [nicht_erhoben("10 Bericht", "Seite", fehler)]

    # **Der Link aus der Mail ist nicht die Berichtsadresse.** Brevo zählt
    # Klicks über `…sendibt2.com/tr/cl/…` und leitet weiter; wer „/pdf" an
    # den Link aus der Mail hängt, fragt den Klickzähler nach einem PDF
    # (20.09.2026). Maßgeblich ist die Adresse, auf der die Weiterleitung
    # landet — und die ist zugleich der Beleg, dass sie zu uns führt.
    echte_adresse = seite.url

    befunde = [messung("10 Bericht", "Seite", seite.status_code == 200,
                       f"HTTP {seite.status_code}, {len(seite.content)} Bytes",
                       echte_adresse)]
    if seite.status_code == 200:
        befunde.append(messung("10 Bericht", "Angebot", "Websprint" in seite.text,
                               f"{seite.text.count('Websprint')}× „Websprint“"))
        treffer = seite.text.count("stripe.com")
        if kaufweg_erwartet:
            befunde.append(messung("10 Bericht", "Kaufweg", treffer > 0,
                                   f"{treffer}× „stripe.com“"))
        else:
            befunde.append(nicht_erhoben(
                "10 Bericht", "Kaufweg",
                f"Check PLUS ist auf diesem Ziel nicht verkäuflich (Stufe 3) — "
                f"{treffer}× „stripe.com“ gefunden, ohne Aussagewert"))

    pdf_adresse = echte_adresse.split("?")[0].rstrip("/") + "/pdf"
    pdf, fehler = hole("GET", pdf_adresse)
    if fehler:
        befunde.append(nicht_erhoben("11 PDF", "Auslieferung", fehler))
        return befunde

    befunde.extend(pdf_befunde(pdf, pdf_adresse))
    return befunde


def pdf_befunde(pdf, adresse: str) -> list[Befund]:
    """Die Kopfzeile ist der Fund vom 12.09. — deshalb steht sie hier einzeln."""
    if pdf.status_code != 200:
        return [messung("11 PDF", "Auslieferung", False, f"HTTP {pdf.status_code}")]

    kopf = pdf.headers.get("content-disposition", "")
    try:
        kopf.encode("ascii")
        rein = True
    except UnicodeEncodeError:
        rein = False

    return [
        messung("11 PDF", "Auslieferung", True,
                f"HTTP 200, {len(pdf.content)} Bytes", adresse),
        messung("11 PDF", "ist ein PDF", pdf.content[:4] == b"%PDF",
                pdf.content[:8].decode("latin-1")),
        messung("11 PDF", "Kopfzeile rein ASCII", rein, kopf[:160]),
        messung("11 PDF", "Name in beiden Formen",
                "filename=" in kopf and "filename*=UTF-8''" in kopf, kopf[:160]),
        messung("11 PDF", "Seiten", pdf.content.count(b"/Type /Page") > 0,
                f"{pdf.content.count(b'/Type /Page')} Seitenobjekte"),
    ]


# ------------------------------------------------- Rückblick aus dem System


def stufe_stand(ziel: dict, request_id: Any, konto: str, wort: str) -> list[Befund]:
    """Die zweite, unabhängige Sicht: was der Server selbst über die Anfrage weiß.

    Ohne Zugangsdaten läuft sie **nicht** und gilt als nicht erhoben — nicht
    als in Ordnung (dieselbe Regel wie in `durchlauf-laufzeit.py`).
    """
    if not (konto and wort):
        return [nicht_erhoben("12 Rückblick", "Zustand der Anfrage",
                              "keine Zugangsdaten (FUNNELTEST_KONTO/FUNNELTEST_WORT)")]

    anmeldung, fehler = hole("POST", f"{ziel['api']}/api/auth/login",
                             json={"email": konto, "password": wort})
    if fehler or anmeldung.status_code != 200:
        grund = fehler or f"HTTP {anmeldung.status_code}"
        return [nicht_erhoben("12 Rückblick", "Anmeldung", grund)]

    marke = anmeldung.json().get("access_token") or anmeldung.json().get("token")
    if not marke:
        return [nicht_erhoben("12 Rückblick", "Anmeldung", "kein Token in der Antwort")]

    liste, fehler = hole("GET", f"{ziel['api']}/api/acquisition/widget/requests",
                         headers={"Authorization": f"Bearer {marke}"})
    if fehler or liste.status_code != 200:
        grund = fehler or f"HTTP {liste.status_code}"
        return [nicht_erhoben("12 Rückblick", "Anfragenliste", grund)]

    zeilen = liste.json().get("requests", [])
    meine = next((z for z in zeilen if z.get("id") == request_id), None)
    if meine is None:
        return [messung("12 Rückblick", "Anfrage gefunden", False,
                        f"Anfrage {request_id} steht nicht in den letzten "
                        f"{len(zeilen)} Zeilen")]

    return [
        messung("12 Rückblick", "Anfrage gefunden", True, f"Anfrage {request_id}"),
        messung("12 Rückblick", "Mail 1 versandt", bool(meine.get("verify_sent")),
                f"verify_sent={meine.get('verify_sent')}"),
        messung("12 Rückblick", "bestätigt", bool(meine.get("verified")),
                f"verified_at={meine.get('verified_at')}"),
        messung("12 Rückblick", "Mail 2 versandt", bool(meine.get("report_sent")),
                f"report_sent={meine.get('report_sent')}"),
        messung("12 Rückblick", "Bericht geöffnet", bool(meine.get("report_opened")),
                f"report_opened={meine.get('report_opened')}"),
        messung("12 Rückblick", "Analyse", meine.get("analyse_status") == "completed",
                f"analyse_status={meine.get('analyse_status')}"),
        Befund("12 Rückblick", "Bestätigung verdächtig?", "gemessen",
               f"ok — bestaetigung_verdaechtig={meine.get('bestaetigung_verdaechtig')}, "
               f"Dauer {meine.get('verify_dauer_s')} s",
               "dieser Lauf bedient das Formular maschinell — ein Ja ist hier erwartet"),
    ]


# --------------------------------------------------------------- Ausgabe


def ausgeben(befunde: list[Befund]) -> None:
    breite = max((len(b.punkt) for b in befunde), default=10)
    stufe = ""
    for b in befunde:
        if b.stufe != stufe:
            stufe = b.stufe
            print(f"\n  {stufe}")
        zeichen = {"gemessen": "  ", "angenommen": "~ ", "nicht erhoben": "? "}[b.klasse]
        print(f"   {zeichen}{b.punkt.ljust(breite)}  {b.ergebnis}")


def zusammenfassen(befunde: list[Befund]) -> str:
    gemessen = [b for b in befunde if b.klasse == "gemessen"]
    offen = [b for b in befunde if b.klasse == "nicht erhoben"]
    fehlt = [b for b in gemessen if not b.ist_bestanden]
    return (f"{len(gemessen) - len(fehlt)} von {len(gemessen)} gemessenen Punkten ok, "
            f"{len(fehlt)} fehlen, {len(offen)} nicht erhoben")


def als_befunde(zustand: dict) -> list[Befund]:
    return [Befund(**z) for z in zustand.get("befunde", [])]


def letzte_je_punkt(befunde: list[Befund]) -> list[Befund]:
    """Je Punkt nur die jüngste Messung — für die Bilanz, nicht fürs Protokoll.

    Eine Phase darf wiederholt werden (`--lauf`), und das Protokoll behält
    jeden Versuch. Die Bilanz darf das nicht: Sonst zählt ein Lauf, der beim
    zweiten Anlauf durchging, den ersten Fehlschlag für immer mit.
    """
    nach_punkt = {(b.stufe, b.punkt): b for b in befunde}
    return list(nach_punkt.values())


# --------------------------------------------------------------- Die Phasen


def anfrage_bauen(args, kennung: str) -> dict:
    """Die Nutzlast, die auch das Widget schickt — mit erkennbaren Testwerten."""
    zeitmarke = int(time.time())
    fbclid = f"kpgfunnel{kennung.replace('-', '')}"
    return {
        "email": args.adresse,
        "website_url": args.domain,
        "consent_marketing": True,
        "consent_tracking": "1",
        "referrer": "https://www.facebook.com/",
        "page_url": f"https://websprint.kompagnon.eu/?fbclid={fbclid}",
        "fbclid": fbclid,
        "fbc": f"fb.1.{zeitmarke}.{fbclid}",
        "fbp": f"fb.1.{zeitmarke}.{zeitmarke}",
        "utm_source": "funneltest",
        "utm_medium": "paid_social",
        "utm_campaign": "websprint-kampagne",
        "utm_content": f"funneltest-{kennung}",
        "utm_term": "selbsttest",
    }


def phase_start(args) -> int:
    ziel = ZIELE[args.ziel]
    kennung = lauf_id()
    anfrage = anfrage_bauen(args, kennung)
    klickadresse = (f"{ziel['landingpage']}?fbclid={anfrage['fbclid']}"
                    f"&utm_source={anfrage['utm_source']}"
                    f"&utm_medium={anfrage['utm_medium']}"
                    f"&utm_campaign={anfrage['utm_campaign']}"
                    f"&utm_content={anfrage['utm_content']}"
                    f"&utm_term={anfrage['utm_term']}#analyse"
                    ) if ziel["landingpage"] else ""

    print(f"Funnel-Test {kennung} gegen {args.ziel} — Adresse {args.adresse}, "
          f"Domain {args.domain}")

    befunde = stufe_landingpage(ziel, klickadresse)
    widget_befunde, config = stufe_widget(ziel)
    befunde += widget_befunde

    lead_befunde, daten = stufe_lead(ziel, anfrage)
    befunde += lead_befunde

    meta = config.get("meta") or {}
    zustand = {
        "lauf": kennung, "ziel": args.ziel, "begonnen": jetzt(),
        "adresse": args.adresse, "domain": args.domain,
        "klickadresse": klickadresse,
        # Was das Ziel überhaupt kann — spätere Stufen messen daran, statt
        # eine fehlende Einrichtung als Mangel zu melden.
        "konfiguration": {
            "pixel": bool(config.get("pixel_id")),
            "meta_bereit": bool(meta.get("bereit")),
            "check_plus": bool((config.get("check_plus") or {}).get("verfuegbar")),
        },
        "request_id": daten.get("request_id"),
        "poll_token": daten.get("poll_token"),
    }

    if daten.get("poll_token"):
        analyse_befunde, teaser = stufe_analyse(ziel, daten["poll_token"])
        befunde += analyse_befunde
        zustand = {**zustand, "teaser": teaser}

    zustand = befunde_anhaengen(zustand, befunde)
    datei = zustand_schreiben(zustand)

    ausgeben(befunde)
    print(f"\n  {zusammenfassen(befunde)}")
    print(f"  Lauf: {datei.relative_to(WURZEL)}")
    print(f"\n  Weiter: Mail 1 an {args.adresse} abwarten, dann\n"
          f"  funnel-test.py bestaetigen --link <Link aus der Mail>")
    return 0


def phase_pruefen(args) -> int:
    """Stufen 2 und 3 allein — ohne Formularabsendung, also ohne neue Daten.

    Zwei Zwecke: die Vorprüfung vor einem produktiven Lauf, und das Nachmessen
    eines Laufs, dessen Prüfung sich als falsch herausgestellt hat. Die Bilanz
    nimmt je Punkt die jüngste Messung, die ältere bleibt im Protokoll stehen.
    """
    if args.ziel:
        ziel, zustand = ZIELE[args.ziel], None
        klickadresse = ziel["landingpage"] or ""
    else:
        zustand = zustand_lesen(args.lauf)
        ziel = ZIELE[zustand["ziel"]]
        klickadresse = zustand.get("klickadresse", "")

    befunde = stufe_landingpage(ziel, klickadresse)
    widget_befunde, config = stufe_widget(ziel)
    befunde += widget_befunde

    if zustand is not None:
        neue_konfig = {**zustand.get("konfiguration", {}),
                       "check_plus": bool((config.get("check_plus") or {}).get("verfuegbar")),
                       "pixel": bool(config.get("facebook_pixel_id"))}
        zustand_schreiben(befunde_anhaengen({**zustand, "konfiguration": neue_konfig},
                                            befunde))

    ausgeben(befunde)
    print(f"\n  {zusammenfassen(befunde)}")
    return 0


def phase_bestaetigen(args) -> int:
    zustand = zustand_lesen(args.lauf)
    befunde = stufe_bestaetigen(args.link)
    zustand = befunde_anhaengen({**zustand, "mail1_link": args.link}, befunde)
    zustand_schreiben(zustand)
    ausgeben(befunde)
    print(f"\n  {zusammenfassen(befunde)}")
    print("\n  Weiter: Mail 2 abwarten, dann\n"
          "  funnel-test.py bericht --link <Link aus der Mail>")
    return 0


def phase_bericht(args) -> int:
    zustand = zustand_lesen(args.lauf)
    kaufweg = bool(zustand.get("konfiguration", {}).get("check_plus", True))
    befunde = stufe_bericht(args.link, kaufweg_erwartet=kaufweg)
    zustand = befunde_anhaengen({**zustand, "mail2_link": args.link}, befunde)
    zustand_schreiben(zustand)
    ausgeben(befunde)
    print(f"\n  {zusammenfassen(befunde)}")
    return 0


def phase_stand(args) -> int:
    import os

    zustand = zustand_lesen(args.lauf)
    ziel = ZIELE[zustand["ziel"]]
    befunde = stufe_stand(ziel, zustand.get("request_id"),
                          os.environ.get("FUNNELTEST_KONTO", ""),
                          os.environ.get("FUNNELTEST_WORT", ""))
    zustand = befunde_anhaengen(zustand, befunde)
    zustand_schreiben(zustand)
    ausgeben(befunde)

    alle = letzte_je_punkt(als_befunde(zustand))
    print(f"\n  Dieser Abschnitt: {zusammenfassen(befunde)}")
    print(f"  Ganzer Lauf:      {zusammenfassen(alle)}")
    offen = [b for b in alle if not b.ist_bestanden]
    if offen:
        print("\n  Nicht ok:")
        for b in offen:
            print(f"   - {b.stufe} · {b.punkt}: {b.ergebnis}")
    return 0


def main() -> int:
    heute = datetime.date.today().isoformat()
    teiler = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    unter = teiler.add_subparsers(dest="phase", required=True)

    start = unter.add_parser("start", help="Stufen 2 bis 6")
    start.add_argument("--ziel", choices=sorted(ZIELE), default="produktiv")
    start.add_argument("--domain", default="nachhaltika.de",
                       help="die zu analysierende Seite (Vorgabe: die eigene)")
    start.add_argument("--adresse", default=f"nachhaltika+funnel-{heute}@gmail.com",
                       help="Empfängeradresse; +Alias hält den Lauf erkennbar")
    start.set_defaults(fn=phase_start)

    pruef = unter.add_parser("pruefen",
                             help="Stufen 2 und 3 allein — ohne neue Daten")
    pruef.add_argument("--ziel", choices=sorted(ZIELE),
                       help="freistehende Vorprüfung; ohne Angabe wird der "
                            "letzte Lauf nachgemessen")
    pruef.add_argument("--lauf")
    pruef.set_defaults(fn=phase_pruefen)

    best = unter.add_parser("bestaetigen", help="Stufe 8 — Klick aus Mail 1")
    best.add_argument("--link", required=True)
    best.add_argument("--lauf")
    best.set_defaults(fn=phase_bestaetigen)

    ber = unter.add_parser("bericht", help="Stufen 10 und 11 — Seite und PDF")
    ber.add_argument("--link", required=True)
    ber.add_argument("--lauf")
    ber.set_defaults(fn=phase_bericht)

    stand = unter.add_parser("stand", help="Stufe 12 — Rückblick aus dem System")
    stand.add_argument("--lauf")
    stand.set_defaults(fn=phase_stand)

    args = teiler.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
