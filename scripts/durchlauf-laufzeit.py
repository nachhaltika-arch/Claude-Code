#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Die vierte Ebene: Was ist im Browser wirklich zu sehen?

    kompagnon/backend/venv/bin/python scripts/durchlauf-laufzeit.py
    …/python scripts/durchlauf-laufzeit.py --basis http://localhost:3000
    …/python scripts/durchlauf-laufzeit.py --konto mail@x.de --wort geheim

**Warum diese Stufe getrennt laeuft.** Die statischen Stufen
(`scripts/systemdurchlauf.py`) lesen Quelltext und laufen ueberall. Diese
hier braucht einen erreichbaren Dienst, einen Browser und — fuer alles
hinter der Anmeldung — ein Konto. Wer beides in ein Skript packt, hat am
Ende keines von beidem, weil der Lauf an der fehlenden Voraussetzung
scheitert und auch die billigen Messungen mitreisst.

**Was gemessen wird, je Seite:**

    Antwortcode         — kam ueberhaupt etwas?
    Netzfehler          — welche API-Anfragen der Seite gaben 4xx/5xx?
    Konsolenfehler      — was hat der Browser selbst beanstandet?
    Sichtbarer Text     — steht etwas da, oder ist die Seite leer?
    Bildschirmfoto      — zum Nachsehen, nicht zum Beweisen

**Die entscheidende Messung ist die vierte.** Ein Backend, das 200 liefert,
und ein Frontend, das baut, koennen zusammen eine leere Seite ergeben — genau
die Bruchstelle, die im Verbindungs-Check zwischen Ebene 3 und 4 liegt. Eine
Seite mit weniger als `--mindesttext` sichtbaren Zeichen gilt deshalb als
Befund, auch wenn alles andere gruen ist.

Ergebnis: `docs/durchlauf/laufzeit-<datum>.json` im selben Befundformat wie
die statischen Stufen; `scripts/systemdurchlauf.py --laufzeit <datei>` nimmt
es in den Bericht auf. Bildschirmfotos liegen unter `docs/durchlauf/bilder/`.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import re
import sys

WURZEL = pathlib.Path(__file__).resolve().parents[1]
ZIEL = WURZEL / "docs" / "durchlauf"
BILDER = ZIEL / "bilder"
APP_JSX = WURZEL / "kompagnon" / "frontend" / "src" / "App.jsx"

STAGING = "https://kompagnon-frontend-staging.onrender.com"


def seitenliste() -> list[str]:
    """Die festen Routen aus `App.jsx` — ohne Platzhalter.

    Routen mit `:token` oder `:id` brauchen einen echten Datensatz; sie hier
    mit erfundenen Werten aufzurufen misst die Fehlerseite, nicht die Seite.
    Sie werden deshalb uebersprungen und im Bericht als nicht gemessen
    gefuehrt.
    """
    if not APP_JSX.exists():
        return []
    text = APP_JSX.read_text(encoding="utf-8")
    roh = re.findall(r'path="([^"]+)"', text)
    fest, offen, eltern = [], [], "/app"
    for pfad in roh:
        if ":" in pfad or "*" in pfad:
            offen.append(pfad)
            continue
        if pfad.startswith("/"):
            fest.append(pfad)
        else:                       # verschachtelte Route unter /app
            fest.append(f"{eltern}/{pfad}".replace("//", "/"))
    return sorted(dict.fromkeys(fest)), sorted(dict.fromkeys(offen))


def _befund(kennung, ebene, titel, beleg, einzelheiten, vorschlag, gegenstand):
    return dict(kennung=kennung, ebene=ebene, titel=titel, beleg=beleg,
                einzelheiten=einzelheiten, vorschlag=vorschlag, gegenstand=gegenstand)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--basis", default=os.environ.get("DURCHLAUF_BASIS", STAGING))
    p.add_argument("--konto", default=os.environ.get("DURCHLAUF_KONTO", ""))
    p.add_argument("--wort", default=os.environ.get("DURCHLAUF_WORT", ""))
    p.add_argument("--mindesttext", type=int, default=120,
                   help="sichtbare Zeichen, unter denen eine Seite als leer gilt")
    p.add_argument("--breite", type=int, default=1440)
    p.add_argument("--grenze", type=int, default=0, help="nur die ersten N Seiten")
    args = p.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright fehlt — `pip install playwright && playwright install chromium`",
              file=sys.stderr)
        return 2

    fest, offen = seitenliste()
    if args.grenze:
        fest = fest[:args.grenze]
    BILDER.mkdir(parents=True, exist_ok=True)

    befunde: list[dict] = []
    gemessen: list[dict] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        kontext = browser.new_context(viewport={"width": args.breite, "height": 900})
        seite = kontext.new_page()

        angemeldet = False
        if args.konto and args.wort:
            try:
                seite.goto(f"{args.basis}/login", wait_until="networkidle", timeout=60_000)
                seite.fill("input[type=email]", args.konto)
                seite.fill("input[type=password]", args.wort)
                seite.click("button[type=submit]")
                seite.wait_for_url(lambda u: "/login" not in u, timeout=30_000)
                angemeldet = True
            except Exception as fehler:                      # noqa: BLE001
                befunde.append(_befund(
                    "laufzeit/anmeldung", "browser",
                    "Die Anmeldung im Durchlauf ist gescheitert",
                    f"{args.basis}/login — {type(fehler).__name__}: {str(fehler)[:180]}",
                    "Alles hinter der Anmeldung ist damit **nicht gemessen**. Der "
                    "Bericht fuehrt diese Seiten als offen, nicht als in Ordnung.",
                    "P0", "/login"))

        # **Die Horcher werden einmal angemeldet, nicht je Seite.** Wer sie in
        # der Schleife anmeldet, zaehlt auf Seite zehn die Fehler der Seiten
        # eins bis neun mit — eine Zahl, die mit jedem Aufruf waechst und
        # nichts misst.
        konsole: list[str] = []
        netz: list[str] = []
        seite.on("console", lambda m: konsole.append(f"{m.type}: {m.text[:160]}")
                 if m.type == "error" else None)
        seite.on("response", lambda r: netz.append(f"{r.status} {r.url[:110]}")
                 if r.status >= 400 else None)

        for pfad in fest:
            konsole.clear()
            netz.clear()
            eintrag = {"pfad": pfad}
            try:
                antwort = seite.goto(f"{args.basis}{pfad}", wait_until="networkidle",
                                     timeout=45_000)
                seite.wait_for_timeout(700)
                code = antwort.status if antwort else 0
                text = (seite.inner_text("body") or "").strip()
                name = pfad.strip("/").replace("/", "_") or "start"
                bild = BILDER / f"{name}.png"
                seite.screenshot(path=str(bild), full_page=False)
                eintrag |= {"code": code, "zeichen": len(text), "bild": bild.name,
                            "konsole": len(konsole), "netz": len(netz)}

                if code >= 400:
                    befunde.append(_befund(
                        f"laufzeit/antwortcode{pfad}", "browser",
                        f"`{pfad}` antwortet mit {code}",
                        f"GET {args.basis}{pfad} → {code}",
                        "Die Seite ist im Browser nicht erreichbar.", "P0", pfad))
                elif len(text) < args.mindesttext:
                    befunde.append(_befund(
                        f"laufzeit/leer{pfad}", "browser",
                        f"`{pfad}` laedt, zeigt aber nur {len(text)} Zeichen",
                        f"GET {args.basis}{pfad} → {code}, sichtbarer Text {len(text)} Zeichen"
                        + (", nicht angemeldet" if not angemeldet else ""),
                        "Genau die Bruchstelle zwischen Ebene 3 und 4: Der Dienst "
                        "antwortet, das Frontend baut, und im Browser steht nichts. "
                        "Ohne Anmeldung kann das die Weiterleitung sein — mit "
                        "Anmeldung ist es ein Befund.",
                        "P1" if not angemeldet else "P0", pfad))
                if netz:
                    befunde.append(_befund(
                        f"laufzeit/netzfehler{pfad}", "browser",
                        f"`{pfad}` laedt {len(netz)} Anfrage(n) mit Fehlercode",
                        " · ".join(sorted(set(netz))[:4]),
                        "Die Seite baut sich auf, aber ein Teil ihrer Daten kommt "
                        "nicht an. Solche Fehler sind im Betrieb unsichtbar, weil "
                        "die Oberflaeche trotzdem erscheint.", "P1", pfad))
                if konsole:
                    befunde.append(_befund(
                        f"laufzeit/konsole{pfad}", "browser",
                        f"`{pfad}` meldet {len(konsole)} Konsolenfehler",
                        " · ".join(sorted(set(konsole))[:3]),
                        "Der Browser selbst beanstandet etwas. Nicht jeder "
                        "Konsolenfehler ist ein Mangel — jeder ist eine Frage.",
                        "P2", pfad))
            except Exception as fehler:                      # noqa: BLE001
                eintrag |= {"code": 0, "fehler": type(fehler).__name__}
                befunde.append(_befund(
                    f"laufzeit/laedt-nicht{pfad}", "browser",
                    f"`{pfad}` laedt nicht",
                    f"GET {args.basis}{pfad} — {type(fehler).__name__}: {str(fehler)[:150]}",
                    "Zeitueberschreitung oder Absturz beim Aufbau.", "P0", pfad))
            gemessen.append(eintrag)

        browser.close()

    heute = datetime.date.today().isoformat()
    ZIEL.mkdir(parents=True, exist_ok=True)
    datei = ZIEL / f"laufzeit-{heute}.json"
    datei.write_text(json.dumps({
        "datum": heute, "basis": args.basis, "angemeldet": angemeldet,
        "gemessen": gemessen, "nicht_gemessen": offen, "befunde": befunde,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(datei.relative_to(WURZEL))
    print(f"{len(gemessen)} Seiten gemessen, {len(offen)} mit Platzhalter uebersprungen, "
          f"{len(befunde)} Befunde", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
