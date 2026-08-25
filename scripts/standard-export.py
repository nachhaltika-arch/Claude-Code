#!/usr/bin/env python3
"""Anhang B des Buchs aus `audit_criteria.py` erzeugen (BUCH-F2, S5.4).

    python3 scripts/standard-export.py

**Warum erzeugt und nicht gepflegt.** Am 24.08.2026 wich die Spezifikation in
sechs Punkten vom Katalog ab, und die Regel „Änderungen am Maßstab erfolgen
hier zuerst" war in **null von sechs** Fällen befolgt worden. Ein Verfahren,
das an Aufmerksamkeit hängt, hat sich in diesem Projekt zweimal als
unzuverlässig erwiesen — deshalb Weg B aus S4.8: erzeugen.

**Was gegenüber dem Prototyp anders ist.** Er führte vier eigene Tabellen —
`BUCHCODE`, `BUCH_LABEL`, `KAPITEL`, `BUCHTITEL` — und vermerkte selbst:
„Diese Tabelle gehört NICHT hierher … solange sie hier steht, ist sie eine
zweite Wahrheit." Sie stehen jetzt als `buch_code`, `buch_label` und
`buch_kapitel` am Katalog; dieses Skript hat keine eigene Zuordnung mehr.

**Seit BUCH-F1 (25.08.2026) erscheinen auch die Punktabstufungen hier.** Sie
steckten bis dahin als Bedingung in `audit_scoring.py` und liessen sich nicht
auslesen; das Buch hat seine Tabellen deshalb plausibel konstruiert. Jetzt
stehen sie als Daten am Kriterium — Abschnitt B.7 druckt sie.
"""
import importlib.util
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
QUELLE = Path(sys.argv[1]) if len(sys.argv) > 1 else (
    WURZEL / "kompagnon" / "backend" / "services" / "audit_criteria.py")
ZIEL = Path(sys.argv[2]) if len(sys.argv) > 2 else (
    WURZEL / "docs" / "Buch" / "Buch - Kompagnon - Homepage Standard v2"
    / "ANHANG-B-Schwellentabellen.md")



ERHEBUNG = {"gemessen": "gemessen", "abgeleitet": "abgeleitet",
            "einschaetzung": "Einschätzung"}


def laden(pfad: Path):
    """Direkt ueber den Pfad importieren — `services/__init__.py` zieht sonst
    Datenbankmodule mit und das Skript braucht keine Datenbank."""
    spec = importlib.util.spec_from_file_location("ac", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def gilt_fuer(krit) -> str:
    if krit.assumes_business and krit.assumes_local:
        return "K1, K2, K3, K5"
    if krit.assumes_business:
        return "alle außer K6"
    if krit.assumes_local:
        return "K1, K2, K3, K5"
    return "alle Klassen"


def abstufungsblock(schreib, krit) -> None:
    """Die Punktabstufung eines Kriteriums, so wie sie im Buch steht.

    Vier der fünf Arten bekommen eine Tabelle. Die eingeschätzten Kriterien
    bekommen ihr Rubric — dort gibt es keine Schwelle, sondern den Maßstab, den
    das Modell anlegt. Ihn hier zu drucken ist der Punkt: Kapitel 10 druckte
    die Merkmale bisher mit dem Vorbehalt, sie seien „meine Zusammenstellung,
    nicht aus dem Code extrahiert".
    """
    a = krit.abstufung
    schreib(f"**{krit.buch_code} · {krit.buch_name} — {krit.max_points} "
            f"{'Punkt' if krit.max_points == 1 else 'Punkte'}**")
    schreib("")

    if a.art == "KI":
        schreib("Eingeschätzt nach diesem Maßstab:")
        schreib("")
        for zeile in (krit.rubric or "").strip().splitlines():
            schreib("> " + zeile if zeile.strip() else ">")
        schreib("")
        return

    if a.art == "ANTEIL":
        schreib(f"Anteilig: Der gemessene Anteil wird auf {krit.max_points} "
                f"{'Punkt' if krit.max_points == 1 else 'Punkte'} umgerechnet "
                "und kaufmännisch gerundet.")
        schreib("")
        return

    ueberschrift = ("| Punkte | Teilprüfung |" if a.art == "SUMME"
                    else "| Punkte | Bedingung |")
    if a.art == "SUMME":
        schreib("Die Teilprüfungen addieren sich:")
        schreib("")
    schreib(ueberschrift)
    schreib("|---|---|")
    for stufe in a.stufen:
        vorzeichen = "+" if a.art == "SUMME" else ""
        schreib(f"| {vorzeichen}{stufe.punkte} | {stufe.bedingung} |")
    schreib("")


def main() -> None:
    ac = laden(QUELLE)
    zeilen = []
    schreib = zeilen.append

    schreib("<!-- ERZEUGT aus audit_criteria.py — nicht von Hand ändern. -->")
    schreib("<!-- Erzeugt mit scripts/standard-export.py -->")
    schreib("")
    schreib("# Anhang B — Der Katalog auf einen Blick")
    schreib("")
    schreib(f"Fassung des Standards: **{getattr(ac, 'VERSION', '2026.2')}** · "
            f"**{sum(1 for _ in ac.all_criteria())} Kriterien** in "
            f"**{len(ac.CATALOGUE)} Kategorien** · "
            f"**{sum(c.max_points for c in ac.all_criteria())} Rohpunkte**")
    schreib("")
    schreib("Alle Zahlen dieses Anhangs stammen aus dem Prüfkatalog der Software "
            "und sind nicht von Hand eingetragen. Weicht eine Angabe im Fließtext "
            "des Buchs von diesem Anhang ab, gilt dieser Anhang.")
    schreib("")
    schreib("---")
    schreib("")

    # --- B.1 Stufen -------------------------------------------------------
    schreib("## B.1 Die fünf Stufen")
    schreib("")
    schreib("| Ab Wert | Stufe |")
    schreib("|---|---|")
    for grenze, name in ac.LEVELS:
        schreib(f"| {grenze} | {name} |")
    schreib("")
    schreib("Der Wert wird auf 0 bis 100 normiert: "
            "`erreichte Punkte ÷ anwendbare Punkte × 100`, kaufmännisch gerundet.")
    schreib("")

    # --- B.2 Anwendbare Maxima -------------------------------------------
    schreib("## B.2 Ihr anwendbares Maximum")
    schreib("")
    schreib("| Klasse | Maximum |")
    schreib("|---|---|")
    for kl in ("K1", "K2", "K3", "K4", "K5", "K6"):
        schreib(f"| {kl} | {ac.anwendbares_maximum(kl)} |")
    schreib("")

    # --- B.3 Kategorien ---------------------------------------------------
    schreib("## B.3 Die acht Kategorien")
    schreib("")
    schreib("| Kap. | Kategorie | Codes | Punkte | Kriterien |")
    schreib("|---|---|---|---|---|")
    for kat in ac.CATALOGUE:
        p = kat.criteria[0].buch_code[0]
        summe = sum(c.max_points for c in kat.criteria)
        anzahl = len(kat.criteria)
        schreib(f"| {kat.buch_kapitel} | {kat.buch_name} | "
                f"{p}1–{p}{anzahl} | {summe} | {anzahl} |")
    gesamt = sum(c.max_points for c in ac.all_criteria())
    schreib(f"| | **Summe** | | **{gesamt}** | "
            f"**{sum(1 for _ in ac.all_criteria())}** |")
    schreib("")

    # --- B.4 Alle Kriterien ----------------------------------------------
    schreib("## B.4 Alle Kriterien im Einzelnen")
    schreib("")
    for kat in ac.CATALOGUE:
        p = kat.criteria[0].buch_code[0]
        summe = sum(c.max_points for c in kat.criteria)
        schreib(f"### {kat.buch_name} — {summe} Punkte · Kapitel {kat.buch_kapitel}")
        schreib("")
        schreib("| Code | Kriterium | P | Erhebung | Gilt für |")
        schreib("|---|---|---|---|---|")
        for i, c in enumerate(kat.criteria, 1):
            schreib(f"| **{p}{i}** | {c.buch_name} | {c.max_points} | "
                    f"{ERHEBUNG[c.source.value]} | {gilt_fuer(c)} |")
        schreib("")

    # --- B.5 Ausschlusskriterien -----------------------------------------
    schreib("## B.5 Die Ausschlusskriterien")
    schreib("")
    schreib("Diese Befunde begrenzen die Stufe unabhängig von der Punktzahl.")
    schreib("")
    schreib("| Befund | Höchste erreichbare Stufe |")
    schreib("|---|---|")
    schreib("| Kein erreichbares Impressum | Nicht konform |")
    schreib("| Keine erreichbare Datenschutzerklärung | Nicht konform |")
    schreib("| Kein gültiges Verschlüsselungszertifikat | Nicht konform |")
    schreib("| Tracking ohne Einwilligung | Bronze |")
    schreib("| Cookies vor der Einwilligung gesetzt | Bronze |")
    schreib("")

    # --- B.6 Erhebungsarten ----------------------------------------------
    from collections import Counter
    zaehler = Counter(c.source.value for c in ac.all_criteria())
    punkte = Counter()
    for c in ac.all_criteria():
        punkte[c.source.value] += c.max_points
    schreib("## B.6 Wie erhoben wird")
    schreib("")
    schreib("| Erhebungsart | Kriterien | Punkte |")
    schreib("|---|---|---|")
    for art in ("gemessen", "abgeleitet", "einschaetzung"):
        schreib(f"| {ERHEBUNG[art]} | {zaehler[art]} | {punkte[art]} |")
    schreib(f"| **Summe** | **{sum(zaehler.values())}** | **{sum(punkte.values())}** |")
    schreib("")

    # --- B.7 Punktabstufungen (BUCH-F1) -----------------------------------
    schreib("## B.7 Wie die Punkte je Kriterium vergeben werden")
    schreib("")
    schreib("Diese Tabellen stammen aus derselben Quelle wie die Bewertung. "
            "Was hier steht, entscheidet über die Punkte — nicht eine "
            "Beschreibung davon.")
    schreib("")
    for kat in ac.CATALOGUE:
        schreib(f"### {kat.buch_name}")
        schreib("")
        for krit in kat.criteria:
            abstufungsblock(schreib, krit)
    schreib("")

    ZIEL.write_text("\n".join(zeilen), encoding="utf-8")
    print(f"{ZIEL} geschrieben — {len(zeilen)} Zeilen")

    spezifikation_fuellen(ac)


# ── Die Spezifikation (S4.1, S4.4) ────────────────────────────────────

SPEZIFIKATION = (WURZEL / "docs" / "Audit"
                 / "2026-08-14-bewertungslogik-homepage-standard-2026-2.md")


def _block(name: str, zeilen: list) -> str:
    anfang = (f"<!-- ERZEUGT: {name} — nicht von Hand ändern, "
              f"siehe scripts/standard-export.py -->")
    return "\n".join([anfang, *zeilen, f"<!-- /ERZEUGT: {name} -->"])


def _gewichtung(ac) -> list:
    """§ 1 — die Kategorien mit Punkten und Kennungsbereich."""
    zeilen = ["", "| # | Kategorie | P | Kriterien |", "|---|---|---|---|"]
    for nr, kat in enumerate(ac.CATALOGUE, start=1):
        codes = [k.buch_code for k in kat.criteria]
        zeilen.append(f"| {nr} | {kat.label} | {kat.max_points} | "
                      f"{codes[0]}–{codes[-1]} |")
    zeilen.append("| — | Infrastruktur-Befund | 0 | rein informativ |")
    gesamt = sum(k.max_points for k in ac.all_criteria())
    anzahl = sum(1 for _ in ac.all_criteria())
    zeilen.append(f"| | **Summe** | **{gesamt}** | {anzahl} Kriterien |")
    zeilen.append("")
    return zeilen


def _klassenmaxima(ac) -> list:
    """§ 2.4 — das anwendbare Maximum, gerechnet statt eingetragen."""
    zeilen = ["", "| Klasse | Maximum | Nicht anwendbar |", "|---|---|---|"]
    voll = ac.anwendbares_maximum("K1")
    for klasse in ("K1", "K2", "K3", "K4", "K5", "K6"):
        maximum = ac.anwendbares_maximum(klasse)
        # `ist_anwendbar` nimmt den **Schluessel**, nicht das Kriterium. Ein
        # erster Entwurf uebergab das Objekt und bekam ueberall „—" — die
        # Spalte haette dann verschwiegen, dass K6 acht Kriterien nicht
        # anwendet. Eine leere Spalte sieht aus wie eine Auskunft.
        fehlend = [k.buch_code for k in ac.all_criteria()
                   if not ac.ist_anwendbar(k.key, klasse)]
        weg = voll - maximum
        bemerkung = (", ".join(fehlend) + f" ({weg} P)") if fehlend else "—"
        zeilen.append(f"| {klasse} | {maximum} | {bemerkung} |")
    zeilen.append("")
    return zeilen


def spezifikation_fuellen(ac) -> None:
    """Trägt die abgeleiteten Blöcke in die Spezifikation ein (S4.8, Weg B).

    **Warum erzeugt.** Das 2026.2-Dokument setzt die Regel „Änderungen am
    Maßstab erfolgen hier zuerst" — sie wurde in **null von sechs** Fällen
    befolgt. Ein Verfahren, das an Aufmerksamkeit hängt, hat sich in diesem
    Projekt zweimal als unzuverlässig erwiesen.

    Ersetzt wird nur, was zwischen den Marken steht. Der Fließtext bleibt von
    Hand geschrieben — er erklärt, was die Zahlen bedeuten, und das kann kein
    Skript.
    """
    import re

    if not SPEZIFIKATION.exists():
        print(f"  ⚠ {SPEZIFIKATION} fehlt — Spezifikation nicht gefüllt")
        return

    text = SPEZIFIKATION.read_text(encoding="utf-8")
    for name, zeilen in (("gewichtung", _gewichtung(ac)),
                         ("klassenmaxima", _klassenmaxima(ac))):
        muster = re.compile(
            rf"<!-- ERZEUGT: {name} .*?<!-- /ERZEUGT: {name} -->", re.S)
        if not muster.search(text):
            print(f"  ⚠ Marke {name!r} fehlt in der Spezifikation")
            continue
        text = muster.sub(lambda _: _block(name, zeilen), text)

    SPEZIFIKATION.write_text(text, encoding="utf-8")
    print(f"{SPEZIFIKATION.name} — Blöcke gefüllt")


if __name__ == "__main__":
    main()
