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

**Was gemessen wird, je Seite, je Theme, je Rolle:**

    Antwortcode         — kam ueberhaupt etwas?
    Netzfehler          — welche API-Anfragen der Seite gaben 4xx/5xx?
    Konsolenfehler      — was hat der Browser selbst beanstandet?
    Sichtbarer Text     — steht etwas da, oder ist die Seite leer?
    Kleinster Kontrast  — WCAG AA, gerechnet am gerenderten Text
    Text unter 12 px    — Anteil, gewichtet nach Zeichenmenge
    Bildschirmfoto      — je Theme eines, zum Nachsehen

**Hell und Dunkel zaehlen gleich** (Entscheidung David, 04.09.2026). Jede
Seite wird zweimal aufgebaut: einmal mit `data-theme="light"`, einmal mit
`"dark"`. Das ist nicht doppelte Arbeit, sondern die einzige Art, die Frage zu
beantworten — der Dunkelmodus tauscht Tokens, und was nicht als Token
vorliegt, bleibt stehen. Am 28.08.2026 stand `--brand-primary-mid` im dunklen
Satz auf einem Wert mit Kontrast **2.18**; das Token wird an 78 Stellen als
`color:` gesetzt, und niemandem war es aufgefallen.

**Alle Rollen, nacheinander** (dieselbe Entscheidung). Was eine Rolle sieht,
ist eine andere Frage als was es gibt: Dieselbe Adresse kann fuer den Admin
eine Liste sein und fuer den Kunden eine leere Seite. Die Zugangsdaten kommen
aus der Umgebung, eine je Rolle:

    export DURCHLAUF_KONTO_ADMIN=…      DURCHLAUF_WORT_ADMIN=…
    export DURCHLAUF_KONTO_MITARBEITER=… DURCHLAUF_WORT_MITARBEITER=…
    export DURCHLAUF_KONTO_KUNDE=…       DURCHLAUF_WORT_KUNDE=…

Ohne Zugangsdaten laeuft die Rolle nicht und wird als **nicht gemessen**
gefuehrt — nicht als in Ordnung.

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

#: Die Rollen aus `services/rollen.py`. Sie stehen hier als Namen, weil das
#: Skript sonst das Backend importieren muesste — die Liste wird von
#: `tools/durchlauf/rollen.py` gegen die Wahrheit geprueft, und ein
#: Auseinanderlaufen ist dort ein Befund.
ROLLEN = ("superadmin", "admin", "mitarbeiter", "kunde")

#: Hell und Dunkel zaehlen gleich.
THEMES = ("light", "dark")

#: WCAG AA fuer Fliesstext. Grosse Schrift (ab 24 px, oder 18.66 px fett)
#: darf auf 3.0 — das rechnet die Messung im Browser mit.
AA_TEXT = 4.5
AA_GROSS = 3.0

#: Ab hier gilt Text als lesbar — dieselbe Grenze wie
#: `tools/schriftgroessen_messen.py` (Lighthouse), damit zwei Messungen
#: desselben Hauses nicht zwei Wahrheiten liefern.
KLEIN_PX = 12



#: Wird im Browser ausgefuehrt und liefert Kontrast und Schriftgroessen der
#: **sichtbaren** Textknoten. Gerechnet wird gegen den ersten deckenden
#: Hintergrund darueber — dieselbe Regel wie in `tools/bedienbarkeit_messen.py`.
#: Text auf Bild oder Verlauf bleibt hier unentscheidbar und wird gezaehlt,
#: nicht geraten: Eine Vermutung waere schlimmer als eine Luecke.
MESSKRIPT = """
(() => {
  const alsRgb = (f) => {
    const m = (f || '').match(/rgba?\\(([^)]+)\\)/);
    if (!m) return null;
    const t = m[1].split(',').map(x => parseFloat(x));
    if (t.length > 3 && t[3] < 0.999) return null;
    return t.slice(0, 3);
  };
  const leucht = (rgb) => {
    const k = rgb.map(v => { v /= 255; return v <= 0.03928 ? v / 12.92
      : Math.pow((v + 0.055) / 1.055, 2.4); });
    return 0.2126 * k[0] + 0.7152 * k[1] + 0.0722 * k[2];
  };
  const kontrast = (a, b) => {
    const [h, d] = [leucht(a), leucht(b)].sort((x, y) => y - x);
    return (h + 0.05) / (d + 0.05);
  };
  const grund = (el) => {
    let k = el;
    while (k && k !== document.documentElement) {
      const f = alsRgb(getComputedStyle(k).backgroundColor);
      if (f) return f;
      k = k.parentElement;
    }
    return alsRgb(getComputedStyle(document.body).backgroundColor) || [255,255,255];
  };
  let zeichen = 0, klein = 0, schlimmster = 99, unentscheidbar = 0;
  const verstoesse = [];
  for (const el of document.querySelectorAll('body *')) {
    if (el.children.length) continue;
    const text = (el.textContent || '').trim();
    if (!text) continue;
    const kasten = el.getBoundingClientRect();
    if (!kasten.width || !kasten.height) continue;
    const stil = getComputedStyle(el);
    const px = parseFloat(stil.fontSize) || 0;
    zeichen += text.length;
    if (px < KLEIN_PX_PLATZHALTER) klein += text.length;
    const vorn = alsRgb(stil.color);
    if (!vorn) { unentscheidbar += text.length; continue; }
    const wert = kontrast(vorn, grund(el));
    const fett = (parseInt(stil.fontWeight, 10) || 400) >= 700;
    const gross = px >= 24 || (px >= 18.66 && fett);
    const schwelle = gross ? AA_GROSS_PLATZHALTER : AA_TEXT_PLATZHALTER;
    if (wert < schlimmster) schlimmster = wert;
    if (wert < schwelle) {
      verstoesse.push({ wert: Math.round(wert * 100) / 100, px, schwelle,
        text: text.slice(0, 40) });
    }
  }
  return { zeichen, klein, unentscheidbar,
    schlimmster: Math.round(schlimmster * 100) / 100,
    verstoesse: verstoesse.sort((a, b) => a.wert - b.wert).slice(0, 5) };
})()
"""

def seitenliste() -> tuple[list[str], list[str]]:
    """Die festen Routen aus `App.jsx` — mit aufgeloester Verschachtelung.

    **Warum die Verschachtelung zaehlt.** Der erste Entwurf haengte jede
    relative Route pauschal unter `/app` und meldete darauf `/app/kas-website`
    und `/app/notifications` als „Seite nicht gefunden". Beide gibt es —
    unter `/app/settings/`. Der Befund war ein Fehler der Messung, und er
    haette als Systemfehler in der Lueckenliste gestanden.

    Gelesen wird deshalb der Rahmen: `<Route path="x">` ohne Selbstschluss
    oeffnet eine Ebene, `</Route>` schliesst sie. Das ist keine vollstaendige
    JSX-Auswertung, aber es folgt derselben Regel wie React Router.

    Routen mit `:token` oder `:id` brauchen einen echten Datensatz; sie mit
    erfundenen Werten aufzurufen misst die Fehlerseite, nicht die Seite. Sie
    werden uebersprungen und als **nicht gemessen** ausgewiesen.
    """
    if not APP_JSX.exists():
        return [], []
    text = APP_JSX.read_text(encoding="utf-8")
    fest: list[str] = []
    offen: list[str] = []
    stapel: list[str] = []
    i = 0
    while i < len(text):
        if text.startswith("</Route>", i):
            if stapel:
                stapel.pop()
            i += 8
            continue
        if not text.startswith("<Route", i):
            i += 1
            continue
        # Das Tag endet beim ersten ">" ausserhalb geschweifter Klammern:
        # `element={<X />}` enthaelt selbst ">"-Zeichen.
        tiefe, j = 0, i
        while j < len(text):
            z = text[j]
            if z == "{":
                tiefe += 1
            elif z == "}":
                tiefe -= 1
            elif z == ">" and tiefe == 0:
                break
            j += 1
        tag = text[i:j]
        selbstschluss = tag.rstrip().endswith("/")
        treffer = re.search(r'path="([^"]*)"', tag)
        pfad = treffer.group(1) if treffer else ""
        eltern = [t for t in stapel if t]
        if pfad.startswith("/"):
            voll = pfad
        elif pfad in ("", "*"):
            voll = "/" + "/".join(eltern) if eltern else "/"
        else:
            voll = "/" + "/".join(eltern + [pfad.strip("/")])
        voll = re.sub(r"/+", "/", voll)
        if treffer:
            (offen if (":" in voll or "*" in voll) else fest).append(voll)
        if not selbstschluss:
            stapel.append(pfad.strip("/") if pfad and not pfad.startswith("/")
                          else pfad.strip("/"))
        i = j + 1
    return sorted(dict.fromkeys(fest)), sorted(dict.fromkeys(offen))


def _befund(kennung, ebene, titel, beleg, einzelheiten, vorschlag, gegenstand):
    return dict(kennung=kennung, ebene=ebene, titel=titel, beleg=beleg,
                einzelheiten=einzelheiten, vorschlag=vorschlag, gegenstand=gegenstand)


def _anmelden(seite, basis: str, konto: str, wort: str) -> bool:
    """Meldet sich an. Gibt zurueck, ob es geklappt hat — nicht, ob es lief."""
    seite.goto(f"{basis}/login", wait_until="networkidle", timeout=60_000)
    seite.fill("input[type=email]", konto)
    seite.fill("input[type=password]", wort)
    seite.click("button[type=submit]")
    seite.wait_for_url(lambda u: "/login" not in u, timeout=30_000)
    return True


def _theme_setzen(seite, theme: str) -> None:
    """Schaltet die Oberflaeche um — ueber denselben Weg wie der Schalter.

    `ThemeContext.jsx` merkt sich die Wahl im Speicher des Browsers und setzt
    `data-theme` am Wurzelelement. Beides wird hier gesetzt: das Attribut,
    damit die Regeln sofort greifen, und der Speicher, damit ein Neuaufbau der
    Seite dabei bleibt.
    """
    seite.evaluate(
        "(t) => { try { localStorage.setItem('theme', t); } catch (e) {} "
        "document.documentElement.setAttribute('data-theme', t); }", theme)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--basis", default=os.environ.get("DURCHLAUF_BASIS", STAGING))
    p.add_argument("--rollen", default=",".join(ROLLEN),
                   help="Rollen, die gemessen werden (Vorgabe: alle)")
    p.add_argument("--themes", default=",".join(THEMES))
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
    themes = [t.strip() for t in args.themes.split(",") if t.strip()]
    BILDER.mkdir(parents=True, exist_ok=True)

    befunde: list[dict] = []
    gemessen: list[dict] = []
    ohne_zugang: list[str] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        for rolle in [r.strip() for r in args.rollen.split(",") if r.strip()]:
            konto = os.environ.get(f"DURCHLAUF_KONTO_{rolle.upper()}", "")
            wort = os.environ.get(f"DURCHLAUF_WORT_{rolle.upper()}", "")
            if not (konto and wort):
                ohne_zugang.append(rolle)
                continue

            kontext = browser.new_context(
                viewport={"width": args.breite, "height": 900})
            seite = kontext.new_page()
            konsole: list[str] = []
            netz: list[str] = []
            seite.on("console", lambda m: konsole.append(f"{m.type}: {m.text[:160]}")
                     if m.type == "error" else None)
            seite.on("response", lambda r: netz.append(f"{r.status} {r.url[:110]}")
                     if r.status >= 400 else None)

            try:
                _anmelden(seite, args.basis, konto, wort)
            except Exception as fehler:                      # noqa: BLE001
                befunde.append(_befund(
                    f"laufzeit/anmeldung/{rolle}", "browser",
                    f"Die Anmeldung als `{rolle}` ist gescheitert",
                    f"{args.basis}/login — {type(fehler).__name__}: {str(fehler)[:150]}",
                    "Alles, was diese Rolle sieht, ist damit **nicht gemessen**. Der "
                    "Bericht fuehrt es als offen, nicht als in Ordnung.",
                    "P1", f"Anmeldung {rolle}"))
                kontext.close()
                continue

            for theme in themes:
                for pfad in fest:
                    konsole.clear()
                    netz.clear()
                    eintrag = {"rolle": rolle, "theme": theme, "pfad": pfad}
                    try:
                        antwort = seite.goto(f"{args.basis}{pfad}",
                                             wait_until="networkidle", timeout=45_000)
                        _theme_setzen(seite, theme)
                        seite.wait_for_timeout(800)
                        code = antwort.status if antwort else 0
                        text = (seite.inner_text("body") or "").strip()
                        mess = seite.evaluate(
                            MESSKRIPT
                            .replace("KLEIN_PX_PLATZHALTER", str(KLEIN_PX))
                            .replace("AA_GROSS_PLATZHALTER", str(AA_GROSS))
                            .replace("AA_TEXT_PLATZHALTER", str(AA_TEXT)))
                        name = (pfad.strip("/").replace("/", "_") or "start")
                        bild = BILDER / f"{rolle}_{theme}_{name}.png"
                        seite.screenshot(path=str(bild))
                        eintrag |= {"code": code, "zeichen": len(text),
                                    "bild": bild.name, "konsole": len(konsole),
                                    "netz": len(netz),
                                    "kontrast_schlimmster": mess.get("schlimmster"),
                                    "verstoesse": len(mess.get("verstoesse", [])),
                                    "anteil_klein": (
                                        round(100 * mess.get("klein", 0)
                                              / max(1, mess.get("zeichen", 1)), 1))}

                        if code >= 400:
                            befunde.append(_befund(
                                f"laufzeit/antwortcode{pfad}", "browser",
                                f"`{pfad}` antwortet mit {code} ({rolle})",
                                f"GET {args.basis}{pfad} → {code}, Rolle {rolle}",
                                "Die Seite ist im Browser nicht erreichbar.",
                                "P0", pfad))
                        elif len(text) < args.mindesttext:
                            befunde.append(_befund(
                                f"laufzeit/leer{pfad}/{rolle}", "browser",
                                f"`{pfad}` zeigt als `{rolle}` nur {len(text)} Zeichen",
                                f"GET {args.basis}{pfad} → {code}, Theme {theme}, "
                                f"sichtbarer Text {len(text)} Zeichen",
                                "Die Bruchstelle zwischen Ebene 3 und 4: Der Dienst "
                                "antwortet, das Frontend baut, und im Browser steht "
                                "nichts. **Bei einer Rolle, die die Seite nicht sehen "
                                "soll, ist eine leere Seite die falsche Antwort** — "
                                "richtig waere eine Erklaerung oder eine Umleitung.",
                                "P1", pfad))
                        if mess.get("verstoesse"):
                            schlimmster = mess["verstoesse"][0]
                            befunde.append(_befund(
                                f"kontrast/{theme}{pfad}", "optik",
                                (f"`{pfad}` im {theme}-Modus: {len(mess['verstoesse'])} "
                                 f"Textstelle(n) unter WCAG AA, schlimmste "
                                 f"{schlimmster['wert']}:1"),
                                (f"{args.basis}{pfad}, Theme {theme}, Rolle {rolle} — "
                                 f"„{schlimmster['text']}“ bei {schlimmster['px']} px, "
                                 f"Schwelle {schlimmster['schwelle']}"),
                                "Gemessen wird die berechnete Textfarbe gegen den ersten "
                                "deckenden Hintergrund darueber — nicht Token gegen "
                                "Token. Eine Farbe kann als Token bestehen und auf der "
                                "Seite trotzdem auf dem falschen Grund landen. "
                                "**Hell und Dunkel zaehlen gleich.**",
                                "P1", f"{pfad}#{theme}"))
                        if eintrag["anteil_klein"] > 15:
                            befunde.append(_befund(
                                f"schriftgroesse{pfad}", "optik",
                                (f"`{pfad}`: {eintrag['anteil_klein']} % des Textes "
                                 f"stehen unter {KLEIN_PX} px"),
                                f"{args.basis}{pfad}, Rolle {rolle}, gewichtet nach "
                                f"Zeichenmenge",
                                f"Grenze wie bei `tools/schriftgroessen_messen.py` "
                                f"({KLEIN_PX} px, Lighthouse). Gewichtet nach Zeichen, "
                                "nicht nach Fundstellen — ein kleiner Wert in jeder "
                                "Tabellenzeile wiegt anders als einer in einer Fussnote.",
                                "P2", pfad))
                        if netz:
                            befunde.append(_befund(
                                f"laufzeit/netzfehler{pfad}/{rolle}", "browser",
                                f"`{pfad}` laedt als `{rolle}` {len(netz)} Anfrage(n) "
                                f"mit Fehlercode",
                                " · ".join(sorted(set(netz))[:4]),
                                "Die Seite baut sich auf, aber ein Teil ihrer Daten "
                                "kommt nicht an. Im Betrieb unsichtbar, weil die "
                                "Oberflaeche trotzdem erscheint.",
                                "P1", pfad))
                        if konsole:
                            befunde.append(_befund(
                                f"laufzeit/konsole{pfad}/{rolle}", "browser",
                                f"`{pfad}` meldet als `{rolle}` {len(konsole)} "
                                f"Konsolenfehler",
                                " · ".join(sorted(set(konsole))[:3]),
                                "Nicht jeder Konsolenfehler ist ein Mangel — jeder ist "
                                "eine Frage.",
                                "P2", pfad))
                    except Exception as fehler:                  # noqa: BLE001
                        eintrag |= {"code": 0, "fehler": type(fehler).__name__}
                        befunde.append(_befund(
                            f"laufzeit/laedt-nicht{pfad}/{rolle}", "browser",
                            f"`{pfad}` laedt nicht ({rolle}, {theme})",
                            f"GET {args.basis}{pfad} — {type(fehler).__name__}: "
                            f"{str(fehler)[:130]}",
                            "Zeitueberschreitung oder Absturz beim Aufbau.",
                            "P0", pfad))
                    gemessen.append(eintrag)
            kontext.close()
        browser.close()

    heute = datetime.date.today().isoformat()
    ZIEL.mkdir(parents=True, exist_ok=True)
    datei = ZIEL / f"laufzeit-{heute}.json"
    datei.write_text(json.dumps({
        "datum": heute, "basis": args.basis, "themes": themes,
        "rollen_gemessen": sorted({e["rolle"] for e in gemessen}),
        "rollen_ohne_zugang": ohne_zugang,
        "gemessen_anzahl": len(gemessen), "gemessen": gemessen,
        "nicht_gemessen": offen, "befunde": befunde,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(datei.relative_to(WURZEL))
    print(f"{len(gemessen)} Messungen ({len(fest)} Seiten × {len(themes)} Themes × "
          f"{len({e['rolle'] for e in gemessen})} Rollen), {len(offen)} Routen mit "
          f"Platzhalter uebersprungen, {len(befunde)} Befunde", file=sys.stderr)
    if ohne_zugang:
        print(f"NICHT GEMESSEN — ohne Zugangsdaten: {', '.join(ohne_zugang)} "
              f"(DURCHLAUF_KONTO_<ROLLE> / DURCHLAUF_WORT_<ROLLE> setzen)",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
