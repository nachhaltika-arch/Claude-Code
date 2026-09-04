# -*- coding: utf-8 -*-
"""Stufen fuer Hell und Dunkel, Kontrast und Lesbarkeit.

**Was hier absichtlich nicht steht.** Die Kontrastrechnung der Tokens gibt es
schon — `utils/kontrast.js` mit `tokenKontrast.test.js` und
`tokenKontrastPaare.test.js`, und sie ist gruendlicher als alles, was hier
entstehen wuerde: Sie kennt die **ausdrueckliche Paarliste** statt eines
Kreuzprodukts, weil ein Kontrasttest ueber Paare, die es nicht gibt, ein
Fehlalarm-Erzeuger ist. Der Durchlauf ruft sie auf (`werkzeuge.py`), statt sie
nachzubauen.

Hier stehen die Fragen, die diese Tests **nicht** beantworten:

    tokens_ohne_dunkelfassung() → Farbe nur im Hellsatz — im Dunkelmodus bleibt sie hell
    farbe_statt_token()         → harter Farbwert im Bauteil, geht beim Umschalten nicht mit
    fehlende_textalternativen() → Bild ohne Alternativtext, Eingabefeld ohne Beschriftung

Schriftgroessen und gerenderter Kontrast stehen bewusst **nicht** hier —
dafuer gibt es `tools/schriftgroessen_messen.py` und
`tools/bedienbarkeit_messen.py`, die am Browser messen. Warum das ein
Unterschied ist, steht weiter unten im Abschnitt „Lesbarkeit".

**Der Massstab ist WCAG AA** (Entscheidung David, 04.09.2026): Fließtext
4,5:1, grosse Schrift und Bedienelemente 3:1. Derselbe Massstab, den der
Homepage-Standard bei Kunden anlegt — das eigene Werkzeug sollte ihn
bestehen. **Eine Mindestschriftgroesse gehoert nicht dazu**: WCAG kennt keine;
die Richtlinie verlangt, dass Text sich auf 200 % vergroessern laesst (1.4.4).
Die 12-px-Grenze des Projekts stammt von Lighthouse und ist eine eigene
Entscheidung — sie wird als solche gefuehrt, nicht als Norm.

**Hell und Dunkel zaehlen gleich** (dieselbe Entscheidung). Ein Befund im
Dunkelmodus ist kein Hinweis, sondern ein Befund: Wer das Werkzeug abends
benutzt, benutzt es ganz.
"""
from __future__ import annotations

import pathlib
import re

from .befund import Befund, WURZEL, kurz

FRONTEND = WURZEL / "kompagnon" / "frontend" / "src"
TOKENS = FRONTEND / "styles" / "tokens.css"

#: WCAG AA. Die Zahlen stehen hier, damit sie an einer Stelle stehen.
AA_TEXT = 4.5
AA_GROSS = 3.0


def _js_dateien() -> list[pathlib.Path]:
    return [p for p in FRONTEND.rglob("*")
            if p.suffix in (".js", ".jsx") and "node_modules" not in p.parts
            and not p.name.endswith(".test.js")]


# ── Hell und Dunkel: was beim Umschalten stehen bleibt ──────────────────────

_BLOCK = re.compile(r'^(:root|\[data-theme="(?:dark|light)"\]|@media[^{]*)\s*\{', re.M)
_TOKEN = re.compile(r"^\s*(--[a-z0-9-]+)\s*:\s*([^;]+);", re.M)
#: Ein Farbwert — Hexcode, rgb()/rgba() oder hsl(). Verweise auf andere Tokens
#: (`var(--x)`) zaehlen nicht: Sie erben die Fassung des Ziels.
_FARBWERT = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")


def _bloecke() -> dict[str, dict[str, str]]:
    """Die Tokenbloecke aus `tokens.css`, nach ihrer Bedingung getrennt."""
    if not TOKENS.exists():
        return {}
    text = TOKENS.read_text(encoding="utf-8")
    grenzen = [(m.start(), m.group(1).strip()) for m in _BLOCK.finditer(text)]
    ergebnis: dict[str, dict[str, str]] = {}
    for i, (start, name) in enumerate(grenzen):
        ende = grenzen[i + 1][0] if i + 1 < len(grenzen) else len(text)
        schluessel = ("dunkel" if "dark" in name else
                      "hell" if "light" in name else
                      "wurzel")
        ergebnis.setdefault(schluessel, {}).update(
            {t: w.strip() for t, w in _TOKEN.findall(text[start:ende])})
    return ergebnis


def tokens_ohne_dunkelfassung() -> tuple[list[Befund], str]:
    """Farbtokens, die der Dunkelsatz nicht ueberschreibt.

    **Was dabei passiert.** Der Hellsatz steht in `:root` und gilt immer; der
    Dunkelsatz ueberschreibt, was anders sein muss. Ein Farbtoken, das er
    auslaesst, behaelt im Dunkelmodus seinen hellen Wert — eine helle Flaeche
    oder eine helle Schrift mitten in einer dunklen Oberflaeche. Sichtbar wird
    das nur, wenn jemand umschaltet und hinsieht.

    **Nicht jedes ausgelassene Token ist ein Fehler.** Ein Gelb, das in beiden
    Faellen dasselbe Gelb sein soll, gehoert ausgelassen. Deshalb wird je
    Token gefragt, ob es ueberhaupt irgendwo als Farbe benutzt wird, und der
    Befund sagt: *nachsehen*, nicht *reparieren*.
    """
    bloecke = _bloecke()
    if not bloecke:
        return [], "kompagnon/frontend/src/styles/tokens.css nicht gefunden"
    wurzel = bloecke.get("wurzel", {})
    dunkel = set(bloecke.get("dunkel", {}))

    farbtokens = {t: w for t, w in wurzel.items() if _FARBWERT.search(w)}
    fehlend = sorted(t for t in farbtokens if t not in dunkel)

    # Wie oft wird das Token ueberhaupt benutzt? Ein ungenutztes ist kein Thema.
    text_frontend = ""
    for datei in _js_dateien() + list(FRONTEND.rglob("*.css")):
        if "node_modules" in datei.parts:
            continue
        try:
            text_frontend += datei.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            pass
    benutzt = [(t, text_frontend.count(f"var({t})")) for t in fehlend]
    benutzt = [(t, n) for t, n in benutzt if n > 0]

    notiz = (f"{len(farbtokens)} Farbtokens im Hellsatz, {len(dunkel)} im Dunkelsatz; "
             f"{len(fehlend)} ohne Dunkelfassung, davon {len(benutzt)} tatsaechlich benutzt")
    if not benutzt:
        return [], notiz

    benutzt.sort(key=lambda p: -p[1])
    oben = ", ".join(f"`{t}` ({n}×)" for t, n in benutzt[:10])
    return [Befund(
        kennung="theme/tokens-ohne-dunkelfassung",
        ebene="optik",
        titel=(f"{len(benutzt)} benutzte Farbtokens haben keine Dunkelfassung — "
               f"sie bleiben beim Umschalten hell"),
        beleg=f"kompagnon/frontend/src/styles/tokens.css — {oben}",
        einzelheiten=(
            "Der Hellsatz in `:root` gilt immer; der Dunkelsatz ueberschreibt nur, "
            "was anders sein soll. Was er auslaesst, bleibt hell — eine helle Flaeche "
            "oder helle Schrift mitten in einer dunklen Oberflaeche, und niemand sieht "
            "es, solange niemand umschaltet. **Nicht jedes davon ist ein Fehler:** Ein "
            "Gelb, das in beiden Faellen dasselbe sein soll, gehoert ausgelassen. Die "
            "Frage je Token lautet: absichtlich gleich, oder vergessen? Was absichtlich "
            "gleich ist, gehoert mit einem Kommentar daneben — dann ist es beim "
            "naechsten Mal keine Frage mehr."
        ),
        vorschlag="P2",
        gegenstand="Farbtokens ohne Dunkelfassung",
    )], notiz


_HARTE_FARBE = re.compile(
    r"\b(color|backgroundColor|background|borderColor|fill|stroke)\s*:\s*"
    r"['\"](#[0-9a-fA-F]{3,8}|rgba?\([^)]*\))['\"]")


def farbe_statt_token() -> tuple[list[Befund], str]:
    """Farben, die im Bauteil festgeschrieben sind statt aus einem Token zu kommen.

    **Das ist die eigentliche Dunkelmodus-Falle.** Ein `color: '#0f172a'` in
    einer Komponente schaltet nicht um: Der Dunkelmodus tauscht Tokens, nicht
    Zeichenketten. Die Flaeche darunter wird dunkel, die Schrift bleibt fast
    schwarz — und das Ergebnis ist nicht bloss haesslich, sondern unlesbar.
    L-32 hat das fuer den Online-Fertig-Editor einmal aufgeraeumt: dort waren
    es 39 Vorkommen in 21 Dateien.

    Gemeldet wird **je Datei**, damit sich eine Vorschau oder ein bewusst
    festes Markenbild einmal quittieren laesst.
    """
    treffer: dict[str, list[int]] = {}
    for datei in _js_dateien():
        try:
            text = datei.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for fund in _HARTE_FARBE.finditer(text):
            zeile = text.count("\n", 0, fund.start()) + 1
            treffer.setdefault(kurz(datei), []).append(zeile)

    gesamt = sum(len(z) for z in treffer.values())
    notiz = f"{gesamt} feste Farbwerte in {len(treffer)} Dateien"
    if not treffer:
        return [], notiz

    befunde = [Befund(
        kennung="theme/farbe-statt-token",
        ebene="optik",
        titel=(f"{gesamt} feste Farbwerte in {len(treffer)} Dateien gehen beim "
               f"Umschalten nicht mit"),
        beleg=("haeufigste: " + ", ".join(
            f"{pathlib.Path(d).name} ({len(z)}×)"
            for d, z in sorted(treffer.items(), key=lambda p: -len(p[1]))[:8])),
        einzelheiten=(
            "Der Dunkelmodus tauscht **Tokens**, keine Zeichenketten. Jede dieser "
            "Farben bleibt beim Umschalten stehen. **Das ist eine Entscheidung, nicht "
            "tausend:** Entweder die Oberflaeche wird durchgaengig auf Tokens gezogen "
            "— dann ist der Dunkelmodus belastbar —, oder es wird festgehalten, welche "
            "Bereiche bewusst nur hell gedacht sind. Der heutige Zustand ist der "
            "dritte Fall: Es ist nicht entschieden, und man sieht es erst beim "
            "Umschalten. Die schlimmsten Dateien stehen einzeln darunter."
        ),
        vorschlag="P1",
        gegenstand="feste Farbwerte im Frontend",
    )]
    for datei, zeilen in sorted(treffer.items(), key=lambda p: -len(p[1]))[:6]:
        if len(zeilen) < 25:
            continue
        befunde.append(Befund(
            kennung=f"theme/farbe-statt-token/{datei}",
            ebene="optik",
            titel=(f"{pathlib.Path(datei).name}: {len(zeilen)} feste Farbwerte, "
                   f"die beim Umschalten nicht mitgehen"),
            beleg=f"{datei} — Zeile {', '.join(str(z) for z in zeilen[:8])}",
            einzelheiten=(
                "Der Dunkelmodus tauscht **Tokens**, keine Zeichenketten. Eine Farbe, "
                "die als `'#…'` im Bauteil steht, bleibt beim Umschalten stehen: Die "
                "Flaeche wird dunkel, die Schrift bleibt fast schwarz. Das ist nicht "
                "nur haesslich, es ist unlesbar — und im Hellmodus faellt es nie auf. "
                "**Ausnahmen sind haeufig und berechtigt**: eine Markenvorschau, ein "
                "Diagramm mit eigener Farbskala, ein Bild in Bildpunkten. Die gehoeren "
                "quittiert. Der Rest gehoert an `var(--token)`. Wie L-32, wo dieselbe "
                "Aufraeumarbeit 39 Vorkommen in 21 Dateien betraf."
            ),
            vorschlag="P2",
            gegenstand=datei,
        ))
    return befunde, notiz


# ── Lesbarkeit ──────────────────────────────────────────────────────────────

# ── Lesbarkeit: bewusst **nicht** hier ─────────────────────────────────────
#
# Der erste Entwurf hatte eine Stufe „Schriftgroessen unter 14 px im
# Quelltext". Sie zaehlte 2.633 Fundstellen in 192 Dateien und war in zwei
# Punkten falsch.
#
# **Erstens die Zahl.** 14 px ist keine WCAG-Anforderung — die Richtlinie
# kennt keine absolute Mindestgroesse, sondern verlangt, dass Text sich auf
# 200 % vergroessern laesst (1.4.4). Eine Norm zu zitieren, die das nicht
# sagt, waere in einem Haus, das Website-Audits verkauft, der teuerste Fehler
# von allen. Das Projekt zieht die Grenze bei **12 px**, wie Lighthouse.
#
# **Zweitens die Messstelle.** `tools/schriftgroessen_messen.py` misst am
# **gerenderten** Text und gewichtet nach Zeichenmenge: Ein 11er in einer
# Fussnote wiegt anders als einer in jeder Tabellenzeile. Sein Docstring sagt
# den Satz, der diese Stufe erledigt — „eine Entscheidung ueber tausend
# Fundstellen auf die Code-Zahl zu stuetzen" misst das Falsche.
#
# Der Durchlauf ruft deshalb das Werkzeug auf (siehe `werkzeuge.py`), statt
# es schlechter nachzubauen.


_IMG_OHNE_ALT = re.compile(r"<img\b(?![^>]*\balt\s*=)[^>]*>")
_INPUT = re.compile(r"<input\b[^>]*>")


def fehlende_textalternativen() -> tuple[list[Befund], str]:
    """Bilder ohne Alternativtext und Eingabefelder ohne Beschriftung.

    Die zwei Faelle, die eine Textmessung sicher sagen kann. Ob eine
    vorhandene Alternative **gut** ist, sagt sie nicht — das ist Urteil und
    steht in der Pruefliste.
    """
    ohne_alt: dict[str, list[int]] = {}
    ohne_label: dict[str, list[int]] = {}
    for datei in _js_dateien():
        if datei.suffix != ".jsx":
            continue
        try:
            text = datei.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for fund in _IMG_OHNE_ALT.finditer(text):
            ohne_alt.setdefault(kurz(datei), []).append(
                text.count("\n", 0, fund.start()) + 1)
        for fund in _INPUT.finditer(text):
            marke = fund.group(0)
            if ("aria-label" in marke or "aria-labelledby" in marke
                    or "placeholder" in marke or "id=" in marke
                    or 'type="hidden"' in marke):
                continue
            ohne_label.setdefault(kurz(datei), []).append(
                text.count("\n", 0, fund.start()) + 1)

    befunde = []
    for sammlung, art, titel, warum in (
        (ohne_alt, "bild-ohne-alt", "Bild(er) ohne Alternativtext",
         "Ein Bild ohne `alt` ist fuer eine Vorlesehilfe nicht vorhanden. Ist das "
         "Bild reine Zierde, gehoert `alt=\"\"` hin — das ist die Aussage „hier ist "
         "nichts zu lesen\" und etwas anderes als ein fehlendes Attribut."),
        (ohne_label, "feld-ohne-beschriftung", "Eingabefeld(er) ohne Beschriftung",
         "Ein Feld ohne `id`, `aria-label` oder Platzhalter hat fuer eine Vorlesehilfe "
         "keinen Namen. Der Nutzer hoert „Eingabefeld\" und nichts weiter."),
    ):
        for datei, zeilen in sorted(sammlung.items(), key=lambda p: -len(p[1]))[:6]:
            befunde.append(Befund(
                kennung=f"barrierefreiheit/{art}/{datei}",
                ebene="frontend",
                titel=f"{pathlib.Path(datei).name}: {len(zeilen)} {titel}",
                beleg=f"{datei} — Zeile {', '.join(str(z) for z in zeilen[:8])}",
                einzelheiten=warum + " Massstab WCAG AA.",
                vorschlag="P2",
                gegenstand=f"{art}/{datei}",
            ))
    notiz = (f"{sum(len(z) for z in ohne_alt.values())} Bilder ohne alt, "
             f"{sum(len(z) for z in ohne_label.values())} Felder ohne Beschriftung")
    return befunde, notiz
