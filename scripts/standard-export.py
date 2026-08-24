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

**Was sich weiterhin nicht erzeugen lässt:** die Punktabstufungen selbst. Sie
stecken als Bedingung in `audit_scoring.py` — das ist BUCH-F1, und der Grund,
warum F1 vor F2 kommt.
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

    # --- B.7 Fehlt noch ---------------------------------------------------
    schreib("## B.7 🔴 Was in diesem Anhang noch fehlt")
    schreib("")
    schreib("**Die Punktabstufungen je Kriterium.** Sie stehen derzeit nicht als "
            "Daten im Katalog, sondern als Bedingungen im Bewertungscode und "
            "lassen sich deshalb nicht erzeugen. Sobald `BUCH-F1` sie überführt "
            "hat, erscheinen sie hier automatisch.")
    schreib("")
    schreib("**Die deutschen Kriterienbezeichnungen** stehen derzeit im Skript "
            "statt im Katalog. Sie gehören als Feld `buch_label` an das Kriterium — "
            "sonst gibt es zwei Wahrheiten über denselben Namen.")
    schreib("")
    schreib("**Bis dahin stehen die Abstufungen in den Kapiteln 5 bis 12** — "
            "dort von Hand aus dem Bewertungscode übertragen und damit "
            "ungeschützt gegen die nächste Änderung.")
    schreib("")

    ZIEL.write_text("\n".join(zeilen), encoding="utf-8")
    print(f"{ZIEL} geschrieben — {len(zeilen)} Zeilen")


if __name__ == "__main__":
    main()
