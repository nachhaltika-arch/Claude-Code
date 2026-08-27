#!/usr/bin/env python3
"""Prototyp: erzeugt Anhang B aus `audit_criteria.py`.

Das ist die Vorstufe von `scripts/standard-export.py` aus BUCH-F2. Es zeigt,
was sich heute schon erzeugen laesst — und was nicht.

ERZEUGBAR (Daten im Katalog):
    Kategorien, Kriterien, Punktwerte, Erhebungsart, Klassenanwendbarkeit,
    Summen, Stufenschwellen, anwendbare Maxima je Klasse.

NICHT ERZEUGBAR (steckt als Bedingung in `audit_scoring.py`):
    Die Punktabstufungen selbst. Genau das ist Befund N2 — und der Grund,
    warum BUCH-F1 vor BUCH-F2 kommt.
"""
import importlib.util
import sys
from pathlib import Path

QUELLE = Path(sys.argv[1] if len(sys.argv) > 1 else "audit_criteria.py")
ZIEL = Path(sys.argv[2] if len(sys.argv) > 2 else "anhang-b-schwellen.md")

BUCHCODE = {
    "recht_compliance": "L", "sicherheit": "S", "performance": "P",
    "barrierefreiheit": "B", "seo": "E", "design": "D",
    "conversion": "C", "inhalt": "I",
}
KAPITEL = {
    "recht_compliance": 5, "sicherheit": 6, "performance": 7,
    "barrierefreiheit": 8, "seo": 9, "design": 10,
    "conversion": 11, "inhalt": 12,
}
BUCHTITEL = {
    "recht_compliance": "Recht und Compliance",
    "sicherheit": "Sicherheit und Datenschutz",
    "performance": "Ladezeit und Stabilität",
    "barrierefreiheit": "Barrierefreiheit",
    "seo": "Auffindbarkeit",
    "design": "Gestaltung",
    "conversion": "Nutzerführung und Anfragen",
    "inhalt": "Inhalt und Substanz",
}

# 🔴 Die Katalogbezeichnungen sind Arbeitstitel mit Fachjargon ("Primär-CTA",
# "Klarheit above the fold", "Title & Meta-Description"). Das Buch benutzt
# durchgehend deutsche Bezeichnungen. Diese Tabelle gehoert NICHT hierher,
# sondern als Feld `buch_label` an das Criterion — genau wie `buch_code`.
# Solange sie hier steht, ist sie eine zweite Wahrheit. Siehe BUCH-F2.
BUCH_LABEL = {
    "rc_impressum": "Impressum", "rc_datenschutz": "Datenschutzerklärung",
    "rc_cookie": "Einwilligung für Cookies und Tracking",
    "rc_bfsg": "Barrierefreiheitserklärung", "rc_formular_dsgvo": "Kontaktformular",
    "si_ssl": "Verschlüsselungszertifikat",
    "si_redirect": "Erzwungene Weiterleitung auf HTTPS",
    "si_header": "Sicherheitsheader", "si_drittanbieter": "Fremde Dienste ohne Einwilligung",
    "tp_lcp": "Ladezeit des Hauptinhalts", "tp_cls": "Layoutstabilität",
    "tp_inp": "Reaktionszeit auf Eingaben", "tp_mobile": "Mobiler Gesamtwert",
    "tp_bilder": "Bildoptimierung",
    "bf_lighthouse": "Gesamtwert der Barrierefreiheitsprüfung",
    "bf_kontrast": "Farbkontraste", "bf_alt": "Alternativtexte für Bilder",
    "bf_semantik": "Semantik und Struktur", "bf_tastatur": "Tastaturbedienung",
    "se_meta": "Seitentitel und Kurzbeschreibung",
    "se_struktur": "Überschriften und Textumfang",
    "se_index": "Auffindbarkeit für Suchmaschinen",
    "se_schema": "Strukturierte Daten", "se_lokal": "Lokale Signale",
    "se_links": "Keine defekten Verweise", "se_ki_lesbar": "Lesbarkeit für KI-Systeme",
    "dg_aktualitaet": "Visuelle Aktualität", "dg_typografie": "Typografie und Lesbarkeit",
    "dg_farbsystem": "Farbsystem und Konsistenz", "dg_bildqualitaet": "Bildqualität und Echtheit",
    "dg_mobil": "Mobile Darstellung",
    "cv_klarheit": "Klarheit im ersten Bildschirmausschnitt",
    "cv_cta": "Die erwartete Hauptreaktion", "cv_kontakt": "Kontaktwege",
    "cv_vertrauen": "Vertrauenssignale", "cv_angebot": "Klarheit des Angebots",
    "ih_leistungsseiten": "Eigene Leistungsseiten", "ih_aktualitaet": "Aktualität",
    "ih_textqualitaet": "Textqualität",
}

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
    schreib("<!-- Erzeugt mit scripts/standard-export.py (Prototyp) -->")
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
        p = BUCHCODE[kat.key]
        summe = sum(c.max_points for c in kat.criteria)
        anzahl = len(kat.criteria)
        schreib(f"| {KAPITEL[kat.key]} | {BUCHTITEL[kat.key]} | "
                f"{p}1–{p}{anzahl} | {summe} | {anzahl} |")
    gesamt = sum(c.max_points for c in ac.all_criteria())
    schreib(f"| | **Summe** | | **{gesamt}** | "
            f"**{sum(1 for _ in ac.all_criteria())}** |")
    schreib("")

    # --- B.4 Alle Kriterien ----------------------------------------------
    schreib("## B.4 Alle Kriterien im Einzelnen")
    schreib("")
    for kat in ac.CATALOGUE:
        p = BUCHCODE[kat.key]
        summe = sum(c.max_points for c in kat.criteria)
        schreib(f"### {BUCHTITEL[kat.key]} — {summe} Punkte · Kapitel {KAPITEL[kat.key]}")
        schreib("")
        schreib("| Code | Kriterium | P | Erhebung | Gilt für |")
        schreib("|---|---|---|---|---|")
        for i, c in enumerate(kat.criteria, 1):
            schreib(f"| **{p}{i}** | {BUCH_LABEL.get(c.key, c.label)} | {c.max_points} | "
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
