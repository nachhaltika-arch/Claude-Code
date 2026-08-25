#!/usr/bin/env python3
"""Die erzeugten Tabellen im Buchmanuskript aus dem Katalog schreiben.

    python3 scripts/buch-bloecke.py [--pruefen]

**Der Befund vom 25.08.2026.** Rund fünfzig Tabellen im Manuskript tragen die
Zeile „ERZEUGT aus `generiert/…` — nicht von Hand ändern." **Diese Dateien gibt
es nicht, und kein Skript hat sie je geschrieben.** Die Tabellen wurden von Hand
gepflegt und trugen dabei einen Vermerk, der das Gegenteil behauptet — die
gefährlichste Form der Dokumentation: eine, der man glaubt.

Nachweisbar veraltet waren dadurch mindestens zwei Angaben:

* **B4 Semantik und Struktur** stand als „abgeleitet", seit S2.1 ist es gemessen.
* **D2 Typografie und Lesbarkeit** stand als „Einschätzung", seit S1.2 wird es
  gemessen — das Kapitel erklärte dem Leser eine Einschätzung, die keine ist.

**Was hier erzeugt wird.** Die Kriterientabellen der acht Kategorien, die
Klassenmaxima und die Liste der Kriterien, die ohne Betrieb dahinter entfallen.
Bei allen dreien steht jeder Wert im Katalog, und keiner trägt Buchsprache, die
verlorengehen könnte.

**Was ausdrücklich nicht erzeugt wird: die Punktabstufungen in den Kapiteln.**
Der erste Anlauf hat sie erzeugt — und dabei Text vernichtet, der mehr wusste
als der Katalog. Das Buch schrieb „Restlaufzeit 30 Tage oder mehr", der Katalog
nur „läuft nicht in Kürze ab"; das Buch nannte bei L3 und S1 die Deckelregel in
derselben Zeile. Erzeugen hätte beides gegen blassere Sätze getauscht. **Wo die
Handschrift genauer ist als die Quelle, gehört die Genauigkeit in die Quelle —
nicht die Handschrift überschrieben.** Drei Bedingungen im Katalog sind deshalb
am 25.08. an die Buchsprache angeglichen worden (Einwilligungswerkzeug statt
Consent-Tool, 30 Tage statt „in Kürze", Darstellungsanweisung statt Viewport).

Die Abstufungstabellen der Kapitel bleiben Handarbeit. Dieses Skript tut dort
zweierlei: Es berichtigt ihren Vermerk — sie behaupteten, erzeugt zu sein — und
es **prüft ihre Punktwerte** gegen den Katalog. Die Wortwahl bleibt dem Autor,
die Zahlen nicht.

`--pruefen` schreibt nichts und meldet nur, ob eine Datei abweicht.
"""
import importlib.util
import re
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
BUCH = (WURZEL / "docs" / "Buch" / "Buch - Kompagnon - Homepage Standard v2"
        / "Vollständige dokumentation Buch V2")
EXPORT = WURZEL / "scripts" / "standard-export.py"

#: Kategorie-Schlüssel → Name in der Marke. Nur `recht_compliance` weicht ab.
SLUG = {"recht_compliance": "recht"}

#: Die Marke steht in Kapitel 3 ueber zwei Zeilen und sonst ueber eine.
#: Deshalb wird nur ihr Anfang erkannt und dann bis zum `-->` gelesen.
#:
#: **Beide Schreibweisen.** Erkannt wird auch der berichtigte Vermerk „VON HAND
#: gepflegt". Ohne das haette dieses Skript beim ersten Lauf alle Vermerke
#: umgeschrieben — und beim zweiten seine eigenen Marken nicht mehr gefunden:
#: Die Nachrechnung der Punktwerte waere ab dann **still ausgefallen**, und die
#: Ausgabe haette „0 Abweichungen" gemeldet. Dieselbe Fehlerklasse, die im
#: Lagebild fuenfmal steht (gebaut, nicht angeschlossen) — hier beim eigenen
#: Werkzeug, beim zweiten Probelauf aufgefallen.
MARKE = re.compile(
    r"^<!-- (?:ERZEUGT aus generiert/|VON HAND gepflegt: )(?P<name>[a-z_-]+)")


def _laden():
    """Das Exportskript mitbenutzen statt seine Regeln zu wiederholen.

    Es liest seine Pfade aus `sys.argv`; waehrend des Imports bekommt es
    deshalb eine leere Befehlszeile — sonst haelt es `--pruefen` fuer den
    Pfad zum Katalog.
    """
    merker, sys.argv = sys.argv, sys.argv[:1]
    try:
        spec = importlib.util.spec_from_file_location("export", EXPORT)
        modul = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modul)
        return modul, modul.laden(modul.QUELLE)
    finally:
        sys.argv = merker


def _bereich(codes) -> str:
    """`C1, C2, C3, C4, C5` → `C1–C5`. Zusammenhängende Nummern zusammenziehen."""
    stuecke, lauf = [], []
    for code in codes:
        nummer = int(code[1:])
        if lauf and nummer == int(lauf[-1][1:]) + 1 and code[0] == lauf[-1][0]:
            lauf.append(code)
            continue
        if lauf:
            stuecke.append(lauf)
        lauf = [code]
    if lauf:
        stuecke.append(lauf)
    return ", ".join(s[0] if len(s) == 1 else f"{s[0]}–{s[-1]}" for s in stuecke)


def kriterientabelle(ac, export, kategorie) -> list:
    zeilen = ["| Code | Kriterium | Punkte | Erhebung | Gilt für |",
              "|---|---|---|---|---|"]
    for krit in kategorie.criteria:
        zeilen.append(f"| {krit.buch_code} | {krit.buch_name} | {krit.max_points} | "
                      f"{export.ERHEBUNG[krit.source.value]} | {export.gilt_fuer(krit)} |")
    return zeilen


def klassenmaxima(ac) -> list:
    zeilen = ["| Klasse | Maximum | Es entfallen |", "|---|---|---|"]
    for klasse in ("K1", "K2", "K3", "K4", "K5", "K6"):
        weg = [c for c in ac.all_criteria() if not ac.ist_anwendbar(c.key, klasse)]
        if not weg:
            entfaellt = "—"
        else:
            gruppen = []
            for bedingung in ("assumes_business", "assumes_local"):
                teil = [c for c in weg if getattr(c, bedingung)
                        and (bedingung == "assumes_business" or not c.assumes_business)]
                if teil:
                    punkte = sum(c.max_points for c in teil)
                    gruppen.append(f"{_bereich([c.buch_code for c in teil])} ({punkte} P)")
            entfaellt = " und ".join(gruppen)
        zeilen.append(f"| {klasse} | **{ac.anwendbares_maximum(klasse)}** | {entfaellt} |")
    return zeilen


def anwendbarkeit(ac) -> list:
    """Was ohne Betrieb dahinter entfällt — die Tabelle in Kapitel 4."""
    weg = [c for c in ac.all_criteria() if c.assumes_business]
    zeilen = ["| Kriterium | Punkte |", "|---|---|"]
    for krit in weg:
        zeilen.append(f"| {krit.buch_name} | {krit.max_points} |")
    zeilen.append(f"| **Summe** | **{sum(c.max_points for c in weg)}** |")
    return zeilen


def erhebungsarten(ac) -> list:
    """Wie viele Kriterien und Punkte auf jede Erhebungsart entfallen.

    Diese Tabelle in Abschnitt 3.4 stand bis zum 25.08.2026 auf 28/4/7 — dem
    Stand vor S1. Sie ist der Satz, mit dem das Buch dem Leser verspricht, er
    koenne einer Einschaetzung widersprechen; eine falsche Zahl darin trifft
    genau dieses Versprechen.
    """
    kriterien, punkte = {}, {}
    for krit in ac.all_criteria():
        art = krit.source.value
        kriterien[art] = kriterien.get(art, 0) + 1
        punkte[art] = punkte.get(art, 0) + krit.max_points
    zeilen = ["| Kennzeichnung | Kriterien | Punkte |", "|---|---|---|"]
    for art, name in (("gemessen", "gemessen"), ("abgeleitet", "abgeleitet"),
                      ("einschaetzung", "Einschätzung")):
        zeilen.append(f"| **{name}** | {kriterien.get(art, 0)} | {punkte.get(art, 0)} |")
    return zeilen


def bauplan(ac, export) -> dict:
    """Marke → Tabellenzeilen. Was hier fehlt, wird nicht erzeugt."""
    plan = {"klassenmaxima": klassenmaxima(ac), "anwendbarkeit": anwendbarkeit(ac),
            "erhebungsarten": erhebungsarten(ac)}
    for kategorie in ac.CATALOGUE:
        name = SLUG.get(kategorie.key, kategorie.key)
        plan[f"kriterien-{name}"] = kriterientabelle(ac, export, kategorie)
    return plan


def tabelle_unter(zeilen: list, ab: int) -> list:
    """Alle Tabellenzeilen unter einer Marke — auch mehrere Tabellen.

    `si_drittanbieter` hat einen erklärenden Satz und danach **zwei** Tabellen.
    Gesucht sind die Punktwerte, nicht die Form, also wird bis zur nächsten
    Überschrift oder Merkspalte gelesen.
    """
    gefunden = []
    for zeile in zeilen[ab + 1:]:
        text = zeile.strip()
        if text.startswith("|"):
            gefunden.append(zeile)
        elif text.startswith(("#", ":::", "<!--")):
            break
    return gefunden


PUNKTSPALTE = re.compile(r"^\|\s*\*{0,2}(\d+)\*{0,2}\s*\|")


def punkte_pruefen(zeilen: list, krit) -> str:
    """Nennt die handgepflegte Tabelle dieselben Punktwerte wie der Katalog?

    Geprüft werden **Zahlen, nicht Sätze**: die höchste Stufe muss die
    Punktzahl des Kriteriums sein, die niedrigste null, und keine Zeile darf
    einen Wert nennen, den es im Katalog nicht gibt. Damit bleibt dem Autor
    seine Sprache und dem Katalog die Hoheit über die Bewertung.
    """
    gefunden = {int(t.group(1)) for t in
                (PUNKTSPALTE.match(z) for z in zeilen) if t}
    if not gefunden:
        return ""
    erlaubt = {s.punkte for s in krit.abstufung.stufen}
    if krit.abstufung.art in ("SUMME", "ANTEIL"):
        # Ergebnistabelle: jede Punktzahl von null bis zum Maximum ist möglich.
        erlaubt = set(range(krit.max_points + 1))
    if max(gefunden) != krit.max_points:
        return (f"höchste Stufe {max(gefunden)}, Katalog sagt {krit.max_points}")
    fremd = sorted(gefunden - erlaubt)
    if fremd:
        return f"nennt Punktwerte, die es nicht gibt: {fremd}"
    return ""


#: Der berichtigte Vermerk fuer alles, was **nicht** erzeugt wird.
#:
#: Ein Block, der „nicht von Hand aendern" sagt, obwohl ihn niemand erzeugt,
#: ist schlimmer als einer ohne Vermerk: Er haelt jeden davon ab, ihn
#: nachzufuehren — und niemand fuehrt ihn nach.
HANDVERMERK_ABSTUFUNG = (
    "<!-- VON HAND gepflegt: {name}. Die Abstufung ist eine {art}; ihre "
    "Ergebnistabelle haengt an der Zahl der Teilpruefungen und am Runden, "
    "beides steht in audit_scoring.py. Gegen Anhang B pruefen. -->")
HANDVERMERK = (
    "<!-- VON HAND gepflegt: {name}. Wird von keinem Skript erzeugt — der "
    "Vermerk „ERZEUGT\" war falsch. Gegen Anhang B pruefen. -->")


def datei_bearbeiten(pfad: Path, plan: dict, kriterien: dict) -> tuple:
    text = pfad.read_text(encoding="utf-8")
    zeilen = text.split("\n")
    geaendert, ungedeckt, geprueft = [], [], []

    i = 0
    while i < len(zeilen):
        treffer = MARKE.match(zeilen[i])
        if not treffer:
            i += 1
            continue
        name = treffer.group("name")
        # Die Marke kann ueber mehrere Zeilen gehen — bis zum schliessenden Pfeil.
        markenende = i
        while markenende < len(zeilen) and "-->" not in zeilen[markenende]:
            markenende += 1

        if name not in plan:
            # Nicht erzeugbar: den falschen Vermerk berichtigen, die Tabelle
            # darunter unberuehrt lassen — aber ihre Zahlen pruefen.
            schluessel = name.removeprefix("abstufung-")
            krit = kriterien.get(schluessel) if name.startswith("abstufung-") else None
            if krit is not None:
                vermerk = HANDVERMERK_ABSTUFUNG.format(
                    name=name, art=krit.abstufung.art)
                fehler = punkte_pruefen(tabelle_unter(zeilen, markenende), krit)
                geprueft.append(name)
                if fehler:
                    ungedeckt.append(f"{name}: {fehler}")
            else:
                vermerk = HANDVERMERK.format(name=name)
                ungedeckt.append(name)
            if zeilen[i:markenende + 1] != [vermerk]:
                zeilen[i:markenende + 1] = [vermerk]
                geaendert.append(name + " (Vermerk berichtigt)")
                markenende = i
            i = markenende + 1
            continue

        # Die Tabelle steht nach einer Leerzeile unter der Marke.
        start = markenende + 1
        while start < len(zeilen) and not zeilen[start].strip():
            start += 1
        ende = start
        while ende < len(zeilen) and zeilen[ende].lstrip().startswith("|"):
            ende += 1
        if ende == start:
            ungedeckt.append(f"{name} (keine Tabelle darunter)")
            i = markenende + 1
            continue

        if zeilen[start:ende] != plan[name]:
            zeilen[start:ende] = plan[name]
            geaendert.append(name)
            ende = start + len(plan[name])
        i = ende

    neuer_text = "\n".join(zeilen)
    if neuer_text != text and "--pruefen" not in sys.argv:
        pfad.write_text(neuer_text, encoding="utf-8")
    return geaendert, ungedeckt, geprueft, neuer_text != text


def main() -> int:
    export, ac = _laden()
    plan = bauplan(ac, export)
    kriterien = {c.key: c for c in ac.all_criteria()}

    abweichungen, nachgerechnet = 0, 0
    for pfad in sorted(BUCH.glob("*.md")):
        geaendert, ungedeckt, geprueft, anders = datei_bearbeiten(
            pfad, plan, kriterien)
        nachgerechnet += len(geprueft)
        if geaendert:
            print(f"{pfad.name}: {', '.join(geaendert)}")
        for name in ungedeckt:
            print(f"  ⚠ {pfad.name}: {name}")
        abweichungen += 1 if anders else 0

    print(f"{nachgerechnet} handgepflegte Abstufungstabellen nachgerechnet")
    if "--pruefen" in sys.argv:
        print(f"Prüfung: {abweichungen} Datei(en) weichen vom Katalog ab")
        return 1 if abweichungen else 0
    print(f"{abweichungen} Datei(en) geschrieben")
    return 0


if __name__ == "__main__":
    sys.exit(main())
