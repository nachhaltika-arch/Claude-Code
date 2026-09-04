# -*- coding: utf-8 -*-
"""Eine hochgeladene HTML-Datei wird zu einer bearbeitbaren Seite.

**Der Anlass (27.08.2026, Bitte David):** „ich möchte auch html seiten
hochladen können". Ging bisher nirgends — `POST /api/pages/templates/upload`
nimmt `.zip` und `.grapesjs` und lehnt eine einzelne `.html` ab, und es legt
ohnehin nur **Vorlagen** an, keine Seiten.

**Was hier passiert und warum getrennt vom Endpunkt.** Eine fremde HTML-Datei
ist kein sauberer Eingabewert: Sie bringt ein ganzes Dokument mit — Kopf,
Stile, Skripte, womöglich eingebettete Rahmen. Was davon in unser System
darf, ist eine Entscheidung, keine Formatfrage. Sie steht deshalb hier, an
einer Stelle, mit Begründung.

**Entfernt wird, was ausgeführt würde — und es wird gemeldet.**

    <script>        Code, der im Browser jedes Betrachters läuft
    on*-Attribute    dasselbe, nur versteckt (`onclick`, `onload`, …)
    <iframe>         lädt fremde Inhalte nach, die wir nicht kennen
    javascript:      dieselbe Ausführung, als Adresse getarnt

Der Rückgabewert nennt jede Sorte, die entfernt wurde. **Still zu entfernen
wäre schlimmer als abzulehnen:** Wer eine Seite hochlädt und sie danach nicht
wiedererkennt, sucht den Fehler bei sich.

> Der Grund ist nicht Misstrauen gegen David — er ist Admin und lädt eigene
> Dateien hoch. Der Grund ist, dass eine gespeicherte Seite später
> **veröffentlicht** wird, und ab da führt fremdes Skript im Browser jedes
> Besuchers aus.
"""
import logging
import re

logger = logging.getLogger(__name__)

#: Was aus dem Dateinamen wird, wenn kein Name angegeben ist.
_UNSAUBER = re.compile(r"[^a-z0-9]+")


def slug_aus(text: str) -> str:
    """Ein Bezeichner für die Adresse — klein, ohne Umlaute, ohne Leerzeichen."""
    ersetzt = (text or "").lower()
    for alt, neu in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        ersetzt = ersetzt.replace(alt, neu)
    ersetzt = _UNSAUBER.sub("-", ersetzt).strip("-")
    return ersetzt[:200] or "seite"


def einlesen(quelltext: str) -> dict:
    """Zerlegt ein HTML-Dokument in seine Teile.

    Gibt zurück: `html`, `css`, `titel`, `beschreibung` und `entfernt`
    (die Liste dessen, was herausgenommen wurde, in Klartext).
    """
    from bs4 import BeautifulSoup

    suppe = BeautifulSoup(quelltext or "", "html.parser")
    entfernt = []

    # ── Skripte ──────────────────────────────────────────────────────
    skripte = suppe.find_all("script")
    if skripte:
        for s in skripte:
            s.decompose()
        entfernt.append(f"{len(skripte)} Skriptblock(e)")

    # ── Eingebettete Rahmen ──────────────────────────────────────────
    rahmen = suppe.find_all(["iframe", "object", "embed"])
    if rahmen:
        for r in rahmen:
            r.decompose()
        entfernt.append(f"{len(rahmen)} eingebettete(r) Rahmen")

    # ── Ereignis-Attribute und javascript:-Adressen ──────────────────
    #
    # **Diese Schleife ist der Grund, warum hier nicht mit einem Muster
    # gearbeitet wird.** `onclick` in einer Zeichenkette zu suchen trifft
    # auch das Wort in einem Fließtext; der Baum weiss, was ein Attribut ist
    # und was Text.
    ereignisse = 0
    adressen = 0
    for element in suppe.find_all(True):
        for name in [a for a in element.attrs if a.lower().startswith("on")]:
            del element[name]
            ereignisse += 1
        for name in ("href", "src", "action"):
            wert = element.get(name)
            if isinstance(wert, str) and wert.strip().lower().startswith("javascript:"):
                del element[name]
                adressen += 1
    if ereignisse:
        entfernt.append(f"{ereignisse} Ereignis-Attribut(e)")
    if adressen:
        entfernt.append(f"{adressen} javascript:-Adresse(n)")

    # ── Titel und Beschreibung aus dem Kopf ──────────────────────────
    titel = ""
    if suppe.title and suppe.title.string:
        titel = suppe.title.string.strip()[:200]
    beschreibung = ""
    marke = suppe.find("meta", attrs={"name": "description"})
    if marke and marke.get("content"):
        beschreibung = str(marke["content"]).strip()[:300]

    # ── Stile einsammeln ─────────────────────────────────────────────
    #
    # Sie wandern in `css_content`, damit der Editor sie als Stile sieht und
    # nicht als Text mitten im Rumpf.
    stile = []
    for stil in suppe.find_all("style"):
        stile.append(stil.get_text())
        stil.decompose()

    # ── Rumpf ────────────────────────────────────────────────────────
    #
    # Nur der Inhalt von `<body>`. Kopfzeilen, `<html>` und `<head>` gehören
    # nicht in eine Seite, die unser System einbettet — sonst stehen zwei
    # Dokumente ineinander.
    rumpf = suppe.body
    html = rumpf.decode_contents() if rumpf else str(suppe)

    return {
        "html": html.strip(),
        "css": "\n\n".join(s.strip() for s in stile if s.strip()),
        "titel": titel,
        "beschreibung": beschreibung,
        "entfernt": entfernt,
    }


def meldung(entfernt: list) -> str:
    """Ein Satz darüber, was fehlt — oder eine leere Zeichenkette.

    Er geht an den Hochladenden zurück. Ohne ihn sucht er den Unterschied
    zwischen Datei und Seite bei sich.
    """
    if not entfernt:
        return ""
    return ("Beim Einlesen entfernt, weil es im Browser jedes Besuchers "
            "ausgefuehrt wuerde: " + ", ".join(entfernt) + ".")
