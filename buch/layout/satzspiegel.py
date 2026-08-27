# -*- coding: utf-8 -*-
"""Der Satzspiegel des Buchs — eine Quelle für beide Ausgaben.

Die Werte stammen aus `satzmuster.py`, also aus dem Layout, das Manuel bereits
gesehen und in `Satzmuster-170x240.pdf` abgenommen hat. Sie stehen hier ein
zweites Mal, weil `satzmuster.py` eine **Zeichnung** ist: ein Canvas-Skript ohne
Umbruch, das feste Beispielseiten malt. Für zweihundert Seiten braucht es einen
Fluss, und der kommt aus Platypus.

**Was hier nicht neu erfunden wird:** die Maße. Wer sie ändert, ändert sie im
Buchkonzept Teil 1.2 zuerst und zieht beide Dateien nach.

Zwei Abweichungen von `BUCH-03`, beide bewusst:

* **Fließtext 10 pt auf 13 pt Zeilenabstand**, nicht 10,5 auf 1,45. Das
  Satzmuster ist auf einem 13-Punkt-Raster gebaut, an dem Marginalien,
  Tabellen und Stufenmarken ausgerichtet sind. 10,5 auf 1,45 ergäbe 15,2 pt
  und zerschlüge das Raster. `B4.1.3` sagt ausdrücklich, dass die korrigierte
  Satzmuster-Fassung zu übernehmen ist.
* **Noto Sans auch im Fließtext.** `BUCH-03` schreibt es so vor, und es ist die
  einzige Schrift, deren Lizenz für Print und EPUB geprüft ist (`B6.4`, SIL
  OFL, `assets/schriften/OFL.txt`). `satzmuster.py` setzte DejaVu Serif — dort
  ausdrücklich als **Platzhalter** vermerkt.
"""
from pathlib import Path

from reportlab.lib.colors import Color, HexColor
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

WURZEL = Path(__file__).resolve().parent.parent.parent
SCHRIFTEN = WURZEL / "assets" / "schriften"

# ── Format und Satzspiegel (Buchkonzept 1.2) ─────────────────────────
SEITE_BREIT, SEITE_HOCH = 170 * mm, 240 * mm
BUND, HAUPT, STEG, MARG, AUSSEN = 20 * mm, 95 * mm, 5 * mm, 35 * mm, 15 * mm
KOPF, SATZ, FUSS = 20 * mm, 190 * mm, 30 * mm
RASTER = 13                      # Grundlinienraster in Punkt

#: Bildschirmfassung: A4, ein Satzspiegel ohne Marginalspalte.
A4_BREIT, A4_HOCH = 210 * mm, 297 * mm
A4_RAND = 20 * mm

# ── A4 als Buchformat (Ziel `druck-a4`) ──────────────────────────────
# **Nicht dasselbe wie `bildschirm`.** Die Bildschirmfassung ist ein
# Lesedokument: ein Block, kein Bund, keine Marginalspalte. `druck-a4` ist der
# Satzspiegel des Satzmusters, nur auf A4 aufgezogen — gespiegelte Ränder,
# Marginalspalte, Kolumnentitel, Vakatseiten, 10 pt auf 13 pt.
#
# **Nicht proportional vergrößert.** 210/170 = 1,235; eine mitskalierte
# Hauptspalte wäre 117 mm breit, und eine mitskalierte Schrift stünde bei
# 12,35 pt. Wer den Schriftgrad mitzieht, ändert das Schriftbild des Buchs,
# das Manuel abgenommen hat. Also bleibt der Grad bei 10 pt, die Spalte wächst
# nur maßvoll, und der gewonnene Platz geht an Marginalspalte und Ränder —
# dorthin, wo A4 ihn braucht.
#
#     170 × 240      A4 (210 × 297)
#     Bund     20  →  25   der Block ist dicker, der Bund frisst mehr
#     Haupt    95  → 115   ≈ 64 Zeichen bei 10 pt, gute Leseweite
#     Steg      5  →   6
#     Marg     35  →  45   die Marginalie darf zweizeilig laufen
#     Außen    15  →  19
#              ---     ---
#             170     210
#
# **Die Höhe rastert exakt.** Der 170er-Satzspiegel hat 190 mm = 538,6 pt, also
# 41,4 Zeilen zu 13 pt — er endet zwischen zwei Zeilen. Auf A4 ist das
# vermeidbar: 51 Zeilen × 13 pt = 663 pt = 233,90 mm gehen glatt auf.
A4B_BUND, A4B_HAUPT, A4B_STEG, A4B_MARG, A4B_AUSSEN = (
    25 * mm, 115 * mm, 6 * mm, 45 * mm, 19 * mm)
A4B_ZEILEN = 51
A4B_SATZ = A4B_ZEILEN * RASTER              # 663 pt
A4B_KOPF = 25 * mm
A4B_FUSS = A4_HOCH - A4B_KOPF - A4B_SATZ    # 38,10 mm — Fuß größer als Kopf

# ── Farbe ────────────────────────────────────────────────────────────
# Innenteil einfarbig (Variante B des Buchkonzepts). Die Marke erscheint im
# Druck als Grauwert; die Bildschirmfassung darf sie farbig zeigen.
TEAL = HexColor("#004F59")
TEAL_HELL = HexColor("#008EAA")
GELB = HexColor("#FAE600")
G15 = Color(.88, .88, .88)
G30 = Color(.72, .72, .72)
G60 = Color(.42, .42, .42)
G80 = Color(.22, .22, .22)
SCHWARZ = Color(0, 0, 0)

# ── Schriften ────────────────────────────────────────────────────────
#: Name in ReportLab → Datei in `assets/schriften`.
SCHNITTE = {
    "Buch": "NotoSans-Regular.ttf",
    "Buch-F": "NotoSans-Bold.ttf",
    "Buch-K": "NotoSans-Italic.ttf",
    "Buch-FK": "NotoSans-BoldItalic.ttf",
    "Buch-Black": "NotoSans-Black.ttf",
    "Buch-Med": "NotoSans-Medium.ttf",
}


def schriften_laden() -> None:
    """Die Schriften einbetten — und lautstark scheitern, wenn eine fehlt.

    **Der häufigste Fehler dieser Baustrecke** ist laut `BUCH-03`, dass das
    Werkzeug eine Schriftdatei nicht findet und **stillschweigend** eine
    Systemschrift einsetzt: Das PDF entsteht, sieht falsch aus, und die
    Druckerei meldet fehlende Einbettung. Deshalb hier ein Abbruch mit Namen
    statt eines Ersatzes.
    """
    for name, datei in SCHNITTE.items():
        pfad = SCHRIFTEN / datei
        if not pfad.exists():
            raise FileNotFoundError(
                f"Schriftschnitt fehlt: {pfad}. Ohne ihn würde ReportLab still "
                "eine Systemschrift einsetzen — das PDF wäre unbrauchbar.")
        pdfmetrics.registerFont(TTFont(name, str(pfad)))
    pdfmetrics.registerFontFamily(
        "Buch", normal="Buch", bold="Buch-F", italic="Buch-K",
        boldItalic="Buch-FK")


def masse(ziel: str) -> dict:
    """Seitenmaße und Spalten für ein Ausgabeziel.

    `druck` setzt den Buchsatzspiegel mit Marginalspalte, `bildschirm` eine
    A4-Seite ohne sie — am Bildschirm gibt es keinen Bund, und eine 35 mm
    breite Spalte neben 95 mm Text verschenkt dort nur Platz. `druck-a4` ist
    derselbe Buchsatzspiegel auf A4, für alle, die das Buch als A4-Band wollen.

    Wer ein Ziel hinzufügt, ändert nur diese Funktion: Alles andere — Stile,
    Umsetzer, Seitenvorlagen, Marginalien — liest ausschließlich hier.
    """
    if ziel == "druck-a4":
        return {
            "seite": (A4_BREIT, A4_HOCH),
            "haupt": A4B_HAUPT, "marg": A4B_MARG, "steg": A4B_STEG,
            "innen": A4B_BUND, "aussen": A4B_AUSSEN,
            "kopf": A4B_KOPF, "satz": A4B_SATZ, "fuss": A4B_FUSS,
            "grundschrift": 10, "raster": RASTER,
            "marginalspalte": True,
        }
    if ziel == "druck":
        return {
            "seite": (SEITE_BREIT, SEITE_HOCH),
            "haupt": HAUPT, "marg": MARG, "steg": STEG,
            "innen": BUND, "aussen": AUSSEN,
            "kopf": KOPF, "satz": SATZ, "fuss": FUSS,
            "grundschrift": 10, "raster": RASTER,
            "marginalspalte": True,
        }
    return {
        "seite": (A4_BREIT, A4_HOCH),
        "haupt": A4_BREIT - 2 * A4_RAND, "marg": 0, "steg": 0,
        "innen": A4_RAND, "aussen": A4_RAND,
        "kopf": A4_RAND, "satz": A4_HOCH - 2 * A4_RAND, "fuss": A4_RAND,
        "grundschrift": 11, "raster": 15.5,
        "marginalspalte": False,
    }
