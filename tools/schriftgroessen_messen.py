#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wie viel Text ist wirklich zu klein? (L-17, Gruppe Lesbarkeit)

    kompagnon/backend/venv/bin/python tools/schriftgroessen_messen.py

**Warum es dieses Werkzeug braucht.** Am 28.08.2026 stand im Lagebild
„1.072 Stellen mit 9 bis 11 Pixeln"; am 29.08. nachgezählt waren es 1.082. Nur
ist das eine **Code-Zahl, keine Lighthouse-Zahl**: Gezählt werden
Stilangaben im Quelltext. Eine Angabe, die einmal vorkommt, zählt dort genauso
viel wie eine, die in jeder Tabellenzeile steht.

**Lighthouse zählt anders, und darauf kommt es an.** Die Prüfung „Document
uses legible font sizes" nimmt den **gerenderten** Text und gewichtet ihn nach
**Menge**: Sie besteht, wenn der überwiegende Teil der Zeichen mindestens
12 px groß ist. Eine Entscheidung über tausend Fundstellen auf die Code-Zahl
zu stützen hieße, das Falsche zu messen — es können zwanzig Stellen sein, die
99 % des Textes tragen, oder tausend, die zusammen 3 % ausmachen.

**Gemessen wird deshalb hier:** je Textknoten die berechnete Schriftgröße und
die Länge des sichtbaren Textes, aufsummiert je Größe.

**Was ausdrücklich nicht mitzählt** — jede Ausnahme hat einen Grund, sonst
wird die Liste zum Ablagefach:

* unsichtbarer Text (`display:none`, `visibility:hidden`, Größe null) — er
  wird nicht gelesen und von Lighthouse nicht gewertet;
* Text in `<script>`, `<style>`, `<noscript>` — das ist kein Text für Menschen;
* reiner Leerraum zwischen Elementen.

**Angemeldet wird mit den lokalen Zugangsdaten**, weil die Werkzeugseiten
hinter der Anmeldung liegen. Ohne Anmeldung misst man die Login-Seite und hält
das Ergebnis für das Werkzeug.
"""
import json
import sys

# Die Seiten, auf die es ankommt: die dichtesten aus der Code-Zählung vom
# 29.08. plus zwei, die ein Innendienst wirklich den ganzen Tag ansieht.
# **Die Routen liegen unter `/app/…`, nicht an der Wurzel.** Der erste Anlauf
# am 29.08.2026 nahm `/dashboard` und lief fuenfmal in die 404-Seite. Aufgefallen
# ist es nur daran, dass alle fuenf Seiten fast **gleich viele** Zeichen
# lieferten (~176) — eine Zahl, die kein Dashboard hat. Ohne diesen Verdacht
# haette das Ergebnis „0 % zu kleiner Text" geheissen, und es waere die
# Fehlerseite gewesen.
SEITEN = [
    ("Übersicht", "/app/dashboard"),
    ("Betriebe", "/app/betriebe"),
    ("Leads", "/app/leads"),
    ("Projekte", "/app/projects"),
    ("Deals", "/app/deals"),
    ("Kunden", "/app/customers"),
]

#: Wenn **eine** Seite auffallend wenig Text traegt, ist meist die Route falsch
#: und nicht die Seite leer. Darunter wird gewarnt statt gezaehlt.
MINDESTZEICHEN = 400

ZUGANG = ("admin@kompagnon.local", "lokal-admin-2026")
#: **`localhost`, nicht `127.0.0.1`.** Fuer CORS sind das zwei verschiedene
#: Herkuenfte, und `main.py` erlaubt nur `http://localhost:3000`. Ueber die
#: Zahlenadresse geladen, scheitert jede API-Anfrage — die Oberflaeche zeigt
#: „Verbindungsfehler", und man misst die Login-Seite statt des Werkzeugs.
BASIS = "http://localhost:3000"

#: Ab hier gilt Text als lesbar. Lighthouse zieht die Grenze bei 12 px.
GRENZE = 12

#: Das Skript im Browser. Es liefert je Schriftgröße die Zeichenzahl.
ERHEBUNG = """
() => {
  const zaehler = {};
  const lauf = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let knoten;
  while ((knoten = lauf.nextNode())) {
    const text = (knoten.nodeValue || '').replace(/\\s+/g, ' ').trim();
    if (!text) continue;

    const eltern = knoten.parentElement;
    if (!eltern) continue;
    if (['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(eltern.tagName)) continue;

    const stil = window.getComputedStyle(eltern);
    if (stil.display === 'none' || stil.visibility === 'hidden') continue;
    // Ein Element ohne Fläche wird nicht gelesen.
    const kasten = eltern.getBoundingClientRect();
    if (kasten.width === 0 || kasten.height === 0) continue;

    const px = Math.round(parseFloat(stil.fontSize));
    // **Navigation und Inhalt getrennt.** Die Seitenleiste steht auf jeder
    // Seite; ohne die Trennung misst man sie sechsmal und haelt das Ergebnis
    // fuer eine Aussage ueber die Seiten. `<main>` ist die Grenze — es kam
    // mit `OeffentlicheSeite`/`AppLayout` (L-17, Gruppe Tastatur).
    const bereich = eltern.closest('main') ? 'inhalt' : 'rahmen';
    zaehler[bereich] = zaehler[bereich] || {};
    zaehler[bereich][px] = (zaehler[bereich][px] || 0) + text.length;
  }
  return zaehler;
}
"""


def _anmelden(seite):
    """Anmelden und warten, bis die App steht."""
    seite.goto(f"{BASIS}/login", wait_until="networkidle")
    seite.fill('input[type="email"]', ZUGANG[0])
    seite.fill('input[type="password"]', ZUGANG[1])
    seite.click('button[type="submit"]')
    seite.wait_for_url(lambda u: "/login" not in u, timeout=20_000)


def messen():
    from playwright.sync_api import sync_playwright

    gesamt = {}
    je_seite = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        # Ein fester Ausschnitt: Auf einem schmalen Fenster verschwinden
        # Spalten, und dann misst man eine andere Seite als die gemeinte.
        kontext = browser.new_context(viewport={"width": 1440, "height": 900})
        seite = kontext.new_page()

        try:
            _anmelden(seite)
        except Exception as fehler:                      # noqa: BLE001
            print(f"Anmeldung gescheitert: {fehler}", file=sys.stderr)
            browser.close()
            return None, None

        for name, pfad in SEITEN:
            try:
                seite.goto(f"{BASIS}{pfad}", wait_until="networkidle",
                           timeout=30_000)
                seite.wait_for_timeout(1200)   # Nachladende Listen
                zaehler = seite.evaluate(ERHEBUNG)
            except Exception as fehler:                  # noqa: BLE001
                # Eine Seite, die nicht lädt, wird **ausgewiesen** und nicht
                # als 0 gezählt — sonst sieht ein Ausfall aus wie ein Ergebnis.
                je_seite.append((name, pfad, None, str(fehler)[:80]))
                continue

            inhalt = {int(k): v for k, v in
                      (zaehler.get("inhalt") or {}).items()}
            rahmen = {int(k): v for k, v in
                      (zaehler.get("rahmen") or {}).items()}
            zeichen = sum(inhalt.values()) + sum(rahmen.values())

            # Der Riegel gegen die Fehlerseite: Sie traegt rund 176 Zeichen
            # und keinen kleinen Text — als Ergebnis gelesen hiesse das
            # „alles in Ordnung".
            if zeichen < MINDESTZEICHEN:
                je_seite.append((name, pfad, None,
                                 f"nur {zeichen} Zeichen — Route pruefen"))
                continue

            je_seite.append((name, pfad, (inhalt, rahmen), ""))
            for px, n in inhalt.items():
                gesamt[px] = gesamt.get(px, 0) + n

        browser.close()

    return gesamt, je_seite


def bericht(gesamt, je_seite):
    def anteil(werte):
        summe = sum(werte.values())
        klein = sum(n for px, n in werte.items() if px < GRENZE)
        return summe, klein, (klein * 100 / summe if summe else 0)

    print("\nJe Seite — Anteil Text unter 12 px, Inhalt und Rahmen getrennt\n")
    print(f"  {'Seite':<15}{'Pfad':<17}{'Inhalt':>18}{'Rahmen':>18}")
    for name, pfad, werte, fehler in je_seite:
        if werte is None:
            print(f"  {name:<15}{pfad:<17} nicht erhoben ({fehler})")
            continue
        inhalt, rahmen = werte
        i_s, i_k, i_p = anteil(inhalt)
        r_s, r_k, r_p = anteil(rahmen)
        print(f"  {name:<15}{pfad:<17}"
              f"{i_k:>6}/{i_s:<5} {i_p:4.0f} %"
              f"{r_k:>7}/{r_s:<5} {r_p:4.0f} %")

    if not gesamt:
        print("\nKein Inhalt erhoben — kein Ergebnis. Ist die lokale "
              "Datenbank befüllt?")
        return

    summe, klein, prozent = anteil(gesamt)
    print(f"\nNur der Inhaltsbereich, über alle Seiten: {klein} von {summe} "
          f"Zeichen unter {GRENZE} px = {prozent:.1f} %\n")
    print("Nach Größe:\n")
    for px in sorted(gesamt):
        n = gesamt[px]
        marke = "  ← zu klein" if px < GRENZE else ""
        print(f"  {px:>3} px  {n:>7} Zeichen  ({n * 100 / summe:4.1f} %)"
              f"{marke}")


if __name__ == "__main__":
    gesamt, je_seite = messen()
    if gesamt is None:
        sys.exit(1)
    bericht(gesamt, je_seite)
    print("\nRohwerte:", json.dumps(gesamt, sort_keys=True))
