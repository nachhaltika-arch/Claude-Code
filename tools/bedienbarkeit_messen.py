#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fokusreihenfolge und Kontrast am gerenderten Werkzeug (L-17).

    kompagnon/backend/venv/bin/python tools/bedienbarkeit_messen.py

**Warum es dieses Werkzeug braucht.** Von den vier Klassen in L-17 sind zwei
geschlossen (Schaltflächen ohne Namen, Formularfelder ohne Verknüpfung) und
eine ist seit dem 29.08. vermessen (Schriftgrößen). Für die beiden übrigen —
**Fokusreihenfolge** und **Kontrast** — gab es bis heute keine Zahl, sondern
einen Eindruck. Und Eindrücke widersprechen sich: Am 17.08.2026 stand auf der
Arbeitsliste, die Abschnittsüberschriften des Dashboards seien unsichtbar;
gemessen hatten sie 8.89 und bestanden. Unsichtbar waren die Beschriftungen
darunter mit 2.26.

**Was `utils/kontrast.js` schon kann und was hier dazukommt.** Dort werden die
**Design-Tokens** gegeneinander gerechnet — Paare, die jemand aufgeschrieben
hat. Das prüft die Palette, nicht die Seite. Hier wird gemessen, was
tatsächlich übereinander liegt: die berechnete Textfarbe gegen den ersten
deckenden Hintergrund darüber. Eine Farbe kann als Token bestehen und auf der
Seite trotzdem auf dem falschen Grund landen.

**Text auf Bild oder Verlauf wird seit dem 01.09.2026 gemessen statt
gemeldet.** Bis dahin ging die Erhebung den Baum hinauf und suchte den ersten
deckenden Hintergrund; fand sie ein Bild oder einen Verlauf, gab sie auf —
**20 % des Textes** standen als „unentscheidbar" da, gemeldet, aber nicht
gewertet. Aus zwei Farben ist das auch wirklich nicht entscheidbar. Aus den
**gerenderten Bildpunkten** schon: Die Seite wird ein zweites Mal abgelichtet,
diesmal mit unsichtbarem Text, und unter dem Kasten steht dann, was der Leser
hinter den Buchstaben hat.

**Gemessen wird der ungünstigste Punkt, nicht der durchschnittliche.** Ein
Verlauf ist an einem Ende hell und am anderen dunkel; ein Mittelwert bestünde,
während die Hälfte der Buchstaben unlesbar ist. Wer die schlechteste Stelle
besteht, besteht überall — die Aussage ist damit konservativ und nie zu
freundlich. `tests/test_kontrast_auf_bild.py` hält die Rechnung an selbst
erzeugten Bildern fest und prüft im Browser, dass Kasten und Bildabzug
denselben Ursprung haben; ohne das könnte die Rechnung stimmen und trotzdem
die Farben eines anderen Elements messen.

**„Unentscheidbar" bleibt es nur noch ohne Vordergrundfarbe** — und ein Kasten
außerhalb des Sichtfelds zählt weder als bestanden noch als gefallen: Was nicht
abgelichtet wurde, ist nicht gemessen, und eine Vermutung wäre schlimmer als
eine Lücke.

**Gewichtet nach Textmenge, wie bei den Schriftgrößen.** Ein Verstoß an einer
Stelle, die dreimal vorkommt, wiegt anders als einer in jeder Tabellenzeile.
Gezählt werden deshalb Zeichen, nicht Fundstellen — sonst entscheidet man über
eine Zahl, die das Falsche misst.

**Die Fokusreihenfolge wird an zwei Fragen gemessen, nicht an einer:**

1. **Springt der Fokus?** Die Tabulatorreihenfolge folgt dem DOM. Steht ein
   Element im Quelltext vor einem anderen, liegt auf dem Bildschirm aber
   darunter, springt der Fokus für einen sehenden Tastaturbenutzer hin und
   her (WCAG 2.4.3). Gezählt wird jeder **Rücksprung** nach oben, der nicht
   durch einen Zeilenwechsel erklärt ist.

   **Ein Rücksprung je Seite ist der Boden, nicht ein Rest** (gemessen am
   31.08.2026). Eine Seitenleiste über die volle Höhe erzwingt ihn: Wer ihr
   letztes Element verlässt, landet zwangsläufig weiter oben — vor der
   Umstellung bei der Glocke in der Kopfzeile (846 px), danach beim ersten
   Inhaltselement (785 px). Die Zahl ändert sich dadurch nicht, die
   **Reihenfolge** schon: Sie lautet jetzt Sprunglink → Kopfzeile →
   Navigation → Inhalt statt Navigation → Kopfzeile → Inhalt.

   Wer diese Zahl auf null bringen will, muss die Seitenleiste aufgeben, nicht
   den Quelltext umsortieren. Sechs Seiten, sechs Sprünge heisst also
   „sauber", nicht „sechs Mängel".
2. **Sieht man ihn überhaupt?** WCAG 2.4.7 verlangt eine sichtbare Marke.
   Geprüft wird, ob sich beim Fokussieren **irgendetwas** an `outline`,
   `box-shadow`, `border` oder `background` ändert. Ein Element, das sich
   nicht rührt, ist mit der Tastatur erreichbar und trotzdem unauffindbar.

**Was ausdrücklich nicht mitzählt** — jede Ausnahme hat einen Grund:

* unsichtbarer Text und Elemente ohne Fläche — sie werden nicht gelesen;
* Text in `<script>`, `<style>`, `<noscript>`;
* Elemente mit `tabindex="-1"`: Sie stehen absichtlich nicht in der Reihenfolge;
* Hintergründe hinter Bildern und Verläufen: Wo `background-image` liegt,
  lässt sich der Kontrast nicht aus zwei Farben ausrechnen. Diese Stellen
  werden **ausgewiesen**, nicht als bestanden gezählt. Eine Prüfung, die
  Unentscheidbares zu „in Ordnung" macht, ist schlimmer als keine.

**Angemeldet wird mit den lokalen Zugangsdaten**, weil die Werkzeugseiten
hinter der Anmeldung liegen. Ohne Anmeldung misst man die Login-Seite und hält
das Ergebnis für das Werkzeug — genau das ist am 29.08. beim Schwesterwerkzeug
passiert.
"""
import json
import sys

# Dieselben Seiten wie `schriftgroessen_messen.py`. **Dieselben, mit Absicht:**
# Zwei Werkzeuge, die verschiedene Seiten messen, ergeben zwei Lagebilder, die
# sich nicht vergleichen lassen.
SEITEN = [
    ("Übersicht", "/app/dashboard"),
    ("Betriebe", "/app/betriebe"),
    ("Leads", "/app/leads"),
    ("Projekte", "/app/projects"),
    ("Deals", "/app/deals"),
    ("Kunden", "/app/customers"),
]

#: Trägt eine Seite auffallend wenig Text, ist meist die Route falsch und
#: nicht die Seite leer. Derselbe Riegel wie bei den Schriftgrößen.
MINDESTZEICHEN = 400

ZUGANG = ("admin@kompagnon.local", "lokal-admin-2026")

#: `localhost`, nicht `127.0.0.1` — für CORS sind das zwei Herkünfte, und
#: `main.py` erlaubt nur die erste.
BASIS = "http://localhost:3000"

#: WCAG 2.1 AA. Große Schrift ab 24 px, oder ab 18.66 px fett.
AA_TEXT = 4.5
AA_GROSS = 3.0

#: Ein Rücksprung um weniger als das gilt als Zeilenwechsel und nicht als
#: Sprung: Nebeneinanderliegende Bedienelemente sind selten pixelgleich
#: ausgerichtet, und jede Abweichung als Fehler zu zählen hieße, Rauschen zu
#: messen. 24 px ist eine Zeilenhöhe.
ZEILENTOLERANZ = 24

ERHEBUNG_KONTRAST = """
() => {
  const leucht = (rgb) => {
    const [r, g, b] = rgb.map(w => {
      const a = w / 255;
      return a <= 0.03928 ? a / 12.92 : Math.pow((a + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const alsRgb = (s) => {
    const t = (s || '').match(/rgba?\\(([^)]+)\\)/);
    if (!t) return null;
    const teile = t[1].split(',').map(x => parseFloat(x.trim()));
    // Halbdurchsichtiges laesst sich nicht aus zwei Farben rechnen —
    // fuer den **Hintergrund** heisst das: weitersuchen, bis etwas Deckendes
    // kommt. Fuer die **Schrift** gilt das nicht mehr, siehe `alsRgba`.
    if (teile.length > 3 && teile[3] < 1) return null;
    return teile.slice(0, 3);
  };
  // Die Schriftfarbe **mit** ihrer Deckkraft.
  const alsRgba = (s) => {
    const t = (s || '').match(/rgba?\\(([^)]+)\\)/);
    if (!t) return null;
    const teile = t[1].split(',').map(x => parseFloat(x.trim()));
    return { rgb: teile.slice(0, 3),
             a: teile.length > 3 ? teile[3] : 1 };
  };
  // **Was der Browser wirklich zeichnet.** Halbdurchsichtige Schrift auf
  // einem deckenden Grund ergibt eine dritte Farbe — genau die sieht der
  // Leser, und genau gegen sie ist der Kontrast zu rechnen.
  //
  // **Der Befund vom 01.09.2026:** Bis dahin galt jede Schrift mit Alpha < 1
  // als „unentscheidbar" und fiel in denselben Zaehler wie Text auf Bildern.
  // Gemessen waren das **alle** 690 Zeichen der 21,5 % — kein einziges stand
  // auf einem Bild. Der Eintrag L-17 beschrieb damit die falsche Ursache,
  // und die richtige ist nicht unentscheidbar, sondern eine Zeile Rechnung.
  const ueberlagern = (vorn, alpha, hint) =>
    vorn.map((k, i) => Math.round(alpha * k + (1 - alpha) * hint[i]));
  const kontrast = (v, h) => {
    const a = leucht(v), b = leucht(h);
    const [hell, dunkel] = a > b ? [a, b] : [b, a];
    return Math.round(((hell + 0.05) / (dunkel + 0.05)) * 100) / 100;
  };

  // Der erste deckende Hintergrund ueber dem Element. Ein Verlauf oder ein
  // Bild macht die Stelle unentscheidbar — sie wird gemeldet, nicht gewertet.
  const grund = (el) => {
    let k = el;
    while (k && k !== document.documentElement) {
      const s = window.getComputedStyle(k);
      if (s.backgroundImage && s.backgroundImage !== 'none') return 'bild';
      const f = alsRgb(s.backgroundColor);
      if (f) return f;
      k = k.parentElement;
    }
    return [255, 255, 255];
  };

  const ergebnis = { bestanden: 0, gefallen: 0, unentscheidbar: 0,
                     ohneFarbe: 0, aufBildZeichen: 0,
                     faelle: {}, aufBild: [] };
  const lauf = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let knoten;
  while ((knoten = lauf.nextNode())) {
    const text = (knoten.nodeValue || '').replace(/\\s+/g, ' ').trim();
    if (!text) continue;
    const el = knoten.parentElement;
    if (!el) continue;
    if (['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(el.tagName)) continue;

    const s = window.getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    if (parseFloat(s.opacity) === 0) continue;
    const kasten = el.getBoundingClientRect();
    if (kasten.width === 0 || kasten.height === 0) continue;

    const px = parseFloat(s.fontSize);
    const fett = parseInt(s.fontWeight, 10) >= 700;
    const schwelle = (px >= 24 || (fett && px >= 18.66)) ? 3.0 : 4.5;

    const schrift = alsRgba(s.color);
    const hint = grund(el);
    // Deckend gezeichnet: die Schriftfarbe ueber ihrem Grund. Bei Alpha 1
    // ist das die Farbe selbst, sonst die Mischung, die der Leser sieht.
    const vorn = (schrift && hint !== 'bild')
      ? (schrift.a >= 1 ? schrift.rgb : ueberlagern(schrift.rgb, schrift.a, hint))
      : (schrift ? schrift.rgb : null);
    if (!vorn) {
      // Gar keine lesbare Farbangabe — etwa `currentColor` ohne Aufloesung.
      // Das ist der letzte wirklich unentscheidbare Rest.
      ergebnis.ohneFarbe += text.length;
      ergebnis.unentscheidbar += text.length;
      continue;
    }
    if (hint === 'bild') {
      // **Nicht mehr aufgeben, sondern den Kasten melden** (01.09.2026).
      // Aus zwei Farben ist Text auf einem Bild oder Verlauf wirklich nicht
      // entscheidbar — aus den **gerenderten Bildpunkten** schon. Hier wird
      // nur eingesammelt; gerechnet wird in Python, nachdem die Seite ein
      // zweites Mal ohne Text abgelichtet wurde.
      const k = el.getBoundingClientRect();
      ergebnis.aufBildZeichen += text.length;
      ergebnis.aufBild.push({
        x: Math.round(k.left), y: Math.round(k.top),
        w: Math.round(k.width), h: Math.round(k.height),
        farbe: vorn, schwelle: schwelle, laenge: text.length,
        beispiel: text.slice(0, 48),
      });
      continue;
    }

    const wert = kontrast(vorn, hint);
    if (wert >= schwelle) { ergebnis.bestanden += text.length; continue; }

    ergebnis.gefallen += text.length;
    // Je Farbpaar **eine** Zeile: Wer 1.000 Fundstellen liest, sucht die
    // Stelle; wer drei Paare liest, aendert drei Werte.
    const schluessel = `${s.color} auf rgb(${hint.join(',')}) — ${wert} < ${schwelle}`;
    const alt = ergebnis.faelle[schluessel] || { zeichen: 0, beispiel: '' };
    ergebnis.faelle[schluessel] = {
      zeichen: alt.zeichen + text.length,
      beispiel: alt.beispiel || text.slice(0, 48),
    };
  }
  return ergebnis;
}
"""

ERHEBUNG_FOKUS = """
() => {
  const WAEHLBAR = [
    'a[href]', 'button', 'input', 'select', 'textarea',
    '[tabindex]', '[contenteditable="true"]',
  ].join(',');

  const sichtbar = (el) => {
    const s = window.getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden') return false;
    const k = el.getBoundingClientRect();
    return k.width > 0 && k.height > 0;
  };

  const elemente = Array.from(document.querySelectorAll(WAEHLBAR))
    .filter(el => !el.disabled)
    .filter(el => el.getAttribute('tabindex') !== '-1')
    .filter(sichtbar);

  // ── Frage 1: springt der Fokus? ─────────────────────────────────
  // Die Reihenfolge oben ist die DOM-Reihenfolge, und der Tabulator folgt
  // ihr. Ein Ruecksprung nach oben, der groesser ist als eine Zeile, laesst
  // den Fokus fuer einen sehenden Nutzer huepfen.
  const spruenge = [];
  let vorher = null;
  for (const el of elemente) {
    const k = el.getBoundingClientRect();
    const y = k.top + window.scrollY;
    if (vorher !== null && y < vorher.y - TOLERANZ) {
      spruenge.push({
        von: vorher.name,
        nach: (el.tagName + (el.id ? '#' + el.id : '')).toLowerCase(),
        hoch: Math.round(vorher.y - y),
      });
    }
    vorher = { y, name: (el.tagName + (el.id ? '#' + el.id : '')).toLowerCase() };
  }

  // ── Frage 2: sieht man den Fokus? ───────────────────────────────
  // Verglichen wird der berechnete Stil vor und nach `focus()`. Aendert sich
  // an Umriss, Schatten, Rahmen oder Grund nichts, gibt es keine Marke.
  const MERKMALE = ['outlineStyle', 'outlineWidth', 'outlineColor',
                    'boxShadow', 'borderColor', 'borderWidth',
                    'backgroundColor'];
  const abdruck = (el) => {
    const s = window.getComputedStyle(el);
    return MERKMALE.map(m => s[m]).join('|');
  };

  const ohneMarke = [];
  const vorherAktiv = document.activeElement;
  for (const el of elemente) {
    const vor = abdruck(el);
    try { el.focus({ preventScroll: true }); } catch (e) { continue; }
    if (document.activeElement !== el) continue;   // nimmt keinen Fokus an
    const nach = abdruck(el);
    el.blur();
    if (vor === nach) {
      ohneMarke.push((el.tagName + (el.id ? '#' + el.id : '') +
                      (el.className && typeof el.className === 'string'
                       ? '.' + el.className.trim().split(/\\s+/)[0] : '')).toLowerCase());
    }
  }
  try { if (vorherAktiv && vorherAktiv.focus) vorherAktiv.focus(); } catch (e) {}

  return {
    erreichbar: elemente.length,
    spruenge: spruenge,
    ohne_marke: ohneMarke,
  };
}
"""


#: Der Stil, der den Text unsichtbar macht, ohne das Layout zu bewegen.
#: `color: transparent` laesst jede Flaeche, jeden Rand und jedes Bild stehen —
#: der Kasten des Textes liegt danach genau dort, wo er lag, und darunter ist
#: zu sehen, was der Leser hinter den Buchstaben hat.
TEXT_UNSICHTBAR = ("*,*::before,*::after{color:transparent!important;"
                   "text-shadow:none!important;"
                   "-webkit-text-fill-color:transparent!important}")


def _leuchtdichte(r: int, g: int, b: int) -> float:
    def kanal(w):
        w = w / 255.0
        return w / 12.92 if w <= 0.03928 else ((w + 0.055) / 1.055) ** 2.4
    return 0.2126 * kanal(r) + 0.7152 * kanal(g) + 0.0722 * kanal(b)


def _kontrast(a: tuple, b: tuple) -> float:
    la, lb = _leuchtdichte(*a[:3]), _leuchtdichte(*b[:3])
    hell, dunkel = (la, lb) if la > lb else (lb, la)
    return (hell + 0.05) / (dunkel + 0.05)


def _schlechtester_punkt(bild, kasten: dict, breite: int, hoehe: int):
    """Der Bildpunkt im Kasten, der am wenigsten Kontrast zur Schrift hat.

    **Der ungünstigste und nicht der durchschnittliche.** Ein Verlauf ist an
    einem Ende hell und am anderen dunkel; ein Mittelwert bestuende, waehrend
    die Haelfte der Buchstaben unlesbar ist. Wer die schlechteste Stelle
    besteht, besteht ueberall.
    """
    links = max(0, kasten["x"])
    oben = max(0, kasten["y"])
    rechts = min(breite, kasten["x"] + kasten["w"])
    unten = min(hoehe, kasten["y"] + kasten["h"])
    if rechts <= links or unten <= oben:
        return None                       # ausserhalb des Sichtfelds

    ausschnitt = bild.crop((links, oben, rechts, unten))
    # Die Farben zaehlen, nicht die Punkte: Ein Kasten von 400 x 20 hat 8.000
    # Punkte und meist ein Dutzend Farben.
    farben = ausschnitt.getcolors(maxcolors=1 << 16)
    if not farben:
        # Mehr Farben als die Grenze — ein Foto. Dann verkleinern; fuer den
        # schlechtesten Punkt genuegt die Naeherung nicht, deshalb wird hier
        # ohne Verkleinerung Punkt fuer Punkt gegangen.
        farben = [(1, f) for f in ausschnitt.getdata()]

    schrift = tuple(kasten["farbe"])
    return min(_kontrast(schrift, f[1]) for f in farben)


def _bild_kontraste(seite, kaesten: list) -> dict:
    """Text auf Bild oder Verlauf — aus den gerenderten Punkten entschieden.

    Gibt `{bestanden, gefallen, faelle}` in Zeichen zurueck, dieselbe Form wie
    die Erhebung im Browser.
    """
    from io import BytesIO

    from PIL import Image

    ergebnis = {"bestanden": 0, "gefallen": 0, "faelle": {}}
    if not kaesten:
        return ergebnis

    marke = seite.add_style_tag(content=TEXT_UNSICHTBAR)
    try:
        roh = seite.screenshot()
    finally:
        # Der Stil muss wieder weg: Dieselbe Seite wird gleich noch fuer die
        # Fokusmessung benutzt, und unsichtbarer Text verschoebe dort alles.
        seite.evaluate("(el) => el.remove()", marke)

    bild = Image.open(BytesIO(roh)).convert("RGB")
    breite, hoehe = bild.size

    for kasten in kaesten:
        wert = _schlechtester_punkt(bild, kasten, breite, hoehe)
        if wert is None:
            continue
        if wert >= kasten["schwelle"]:
            ergebnis["bestanden"] += kasten["laenge"]
            continue
        ergebnis["gefallen"] += kasten["laenge"]
        schluessel = (f"rgb({','.join(str(c) for c in kasten['farbe'])}) auf "
                      f"Bild/Verlauf — {round(wert, 2)} < {kasten['schwelle']}")
        alt = ergebnis["faelle"].get(schluessel, {"zeichen": 0, "beispiel": ""})
        ergebnis["faelle"][schluessel] = {
            "zeichen": alt["zeichen"] + kasten["laenge"],
            "beispiel": alt["beispiel"] or kasten["beispiel"],
        }
    return ergebnis


def _anmelden(seite):
    """Anmelden und warten, bis die App steht."""
    seite.goto(f"{BASIS}/login", wait_until="networkidle")
    seite.fill('input[type="email"]', ZUGANG[0])
    seite.fill('input[type="password"]', ZUGANG[1])
    seite.click('button[type="submit"]')
    seite.wait_for_url(lambda u: "/login" not in u, timeout=20_000)


def messen():
    from playwright.sync_api import sync_playwright

    je_seite = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        kontext = browser.new_context(viewport={"width": 1440, "height": 900})
        seite = kontext.new_page()

        try:
            _anmelden(seite)
        except Exception as fehler:                      # noqa: BLE001
            print(f"Anmeldung gescheitert: {fehler}", file=sys.stderr)
            browser.close()
            return None

        fokus_skript = ERHEBUNG_FOKUS.replace("TOLERANZ", str(ZEILENTOLERANZ))

        for name, pfad in SEITEN:
            try:
                seite.goto(f"{BASIS}{pfad}", wait_until="networkidle",
                           timeout=30_000)
                seite.wait_for_timeout(1200)
                kontrast = seite.evaluate(ERHEBUNG_KONTRAST)
                # **Der zweite Blick, bevor der Fokus gemessen wird.** Text auf
                # Bild oder Verlauf ist aus zwei Farben nicht entscheidbar —
                # aus den gerenderten Punkten schon. Der Abzug entsteht mit
                # unsichtbarem Text, damit unter dem Kasten steht, was der
                # Leser wirklich hinter den Buchstaben hat.
                aus_bild = _bild_kontraste(seite, kontrast.pop("aufBild", []))
                kontrast["bestanden"] += aus_bild["bestanden"]
                kontrast["gefallen"] += aus_bild["gefallen"]
                kontrast["faelle"].update(aus_bild["faelle"])
                fokus = seite.evaluate(fokus_skript)
            except Exception as fehler:                  # noqa: BLE001
                je_seite.append((name, pfad, None, None, str(fehler)[:80]))
                continue

            zeichen = (kontrast["bestanden"] + kontrast["gefallen"]
                       + kontrast["unentscheidbar"])
            if zeichen < MINDESTZEICHEN:
                je_seite.append((name, pfad, None, None,
                                 f"nur {zeichen} Zeichen — Route pruefen"))
                continue

            je_seite.append((name, pfad, kontrast, fokus, ""))

        browser.close()
    return je_seite


def bericht(je_seite):
    gemessen = [z for z in je_seite if z[2] is not None]
    if not gemessen:
        print("\nNichts erhoben — läuft die lokale Umgebung?")
        return

    print("\n── Kontrast am gerenderten Text (WCAG 2.1 AA) "
          "─────────────────────\n")
    print(f"  {'Seite':<13}{'Pfad':<17}{'gefallen':>12}{'unentscheidbar':>16}")
    for name, pfad, k, _f, fehler in je_seite:
        if k is None:
            print(f"  {name:<13}{pfad:<17} nicht erhoben ({fehler})")
            continue
        summe = k["bestanden"] + k["gefallen"] + k["unentscheidbar"]
        print(f"  {name:<13}{pfad:<17}"
              f"{k['gefallen']:>7}/{summe:<4}"
              f"{k['unentscheidbar']:>12}")

    gefallen = sum(z[2]["gefallen"] for z in gemessen)
    unklar = sum(z[2]["unentscheidbar"] for z in gemessen)
    summe = sum(z[2]["bestanden"] + z[2]["gefallen"] + z[2]["unentscheidbar"]
                for z in gemessen)
    print(f"\n  Über alle Seiten: {gefallen} von {summe} Zeichen unter der "
          f"Schwelle = {gefallen * 100 / summe:.1f} %")
    print(f"  Nicht entscheidbar (Bild oder Verlauf als Grund): {unklar} "
          f"Zeichen = {unklar * 100 / summe:.1f} %")

    # Nach Farbpaar zusammengefasst — das ist die Einheit, in der jemand
    # etwas ändert.
    paare = {}
    for _n, _p, k, _f, _e in gemessen:
        for schluessel, wert in k["faelle"].items():
            alt = paare.get(schluessel, {"zeichen": 0, "beispiel": ""})
            paare[schluessel] = {
                "zeichen": alt["zeichen"] + wert["zeichen"],
                "beispiel": alt["beispiel"] or wert["beispiel"],
            }
    if paare:
        print("\n  Nach Farbpaar, größtes zuerst:\n")
        for schluessel, wert in sorted(paare.items(),
                                       key=lambda x: -x[1]["zeichen"])[:12]:
            print(f"    {wert['zeichen']:>6} Zeichen  {schluessel}")
            print(f"{'':>13}„{wert['beispiel']}\"")

    print("\n── Fokus: Reihenfolge und Sichtbarkeit (WCAG 2.4.3 / 2.4.7) "
          "───────\n")
    print(f"  {'Seite':<13}{'erreichbar':>12}{'Sprünge':>10}{'ohne Marke':>13}")
    for name, _pfad, _k, f, fehler in je_seite:
        if f is None:
            continue
        print(f"  {name:<13}{f['erreichbar']:>12}{len(f['spruenge']):>10}"
              f"{len(f['ohne_marke']):>13}")

    erreichbar = sum(z[3]["erreichbar"] for z in gemessen)
    spruenge = sum(len(z[3]["spruenge"]) for z in gemessen)
    ohne = sum(len(z[3]["ohne_marke"]) for z in gemessen)
    print(f"\n  Über alle Seiten: {erreichbar} erreichbare Elemente, "
          f"{spruenge} Rücksprünge, {ohne} ohne sichtbare Fokusmarke "
          f"({ohne * 100 / erreichbar if erreichbar else 0:.1f} %)")

    arten = {}
    for _n, _p, _k, f, _e in gemessen:
        for eintrag in f["ohne_marke"]:
            arten[eintrag] = arten.get(eintrag, 0) + 1
    if arten:
        print("\n  Ohne Marke, nach Art:\n")
        for eintrag, n in sorted(arten.items(), key=lambda x: -x[1])[:12]:
            print(f"    {n:>4} ×  {eintrag}")


def main():
    je_seite = messen()
    if je_seite is None:
        return 1
    bericht(je_seite)
    if "--json" in sys.argv:
        print("\n" + json.dumps(je_seite, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
