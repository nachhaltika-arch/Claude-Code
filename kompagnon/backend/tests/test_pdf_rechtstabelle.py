"""
Kein Text darf über seine Spalte hinauslaufen.

Gesehen im Bericht vom 2026-08-15, Seite 2: „seit 14.05.2024 (zuvor TMG § 5)"
lief über die 25 mm breite Spalte und druckte sich über „Alle kommerziellen
Websites" in der Nachbarspalte — beide Angaben unlesbar, im Dokument, das der
Kunde als Erstes in die Hand bekommt.

Die Ursache ist eine Eigenheit von reportlab: Ein roher Zeichenketten-Wert in
einer Tabellenzelle bricht nicht um, er läuft weiter. Nur ein ``Paragraph``
bricht. Der Test misst deshalb jede Zelle und verlangt einen Paragraph überall
dort, wo der Text seine Spalte nicht ausfüllt — auch für Zeilen, die erst
später dazukommen.
"""
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Paragraph

from services import pdf_generator as pg


# Innenabstand links und rechts aus BASE_TABLE_STYLE
INNENABSTAND = 6 + 6
SCHRIFTGROESSE = 9


def _passt_roh(text: str, spaltenbreite: float, fett: bool = False) -> bool:
    schrift = pg.FONT_BOLD if fett else pg.FONT_NORMAL
    return stringWidth(text, schrift, SCHRIFTGROESSE) <= spaltenbreite - INNENABSTAND


def test_die_ddg_zeile_laeuft_nicht_in_die_nachbarspalte():
    # Arrange — die Zelle, die den Fehler zeigte
    text = pg.LEGAL_ROWS[0][1]
    breite = pg.LEGAL_COL_WIDTHS[1]

    # Act & Assert — sie ist zu breit für ihre Spalte, also muss sie umbrechen
    assert not _passt_roh(text, breite), \
        "Der Text passt inzwischen roh — dann ist dieser Test gegenstandslos"
    zelle = pg.rechtstabelle_zellen()[1][1]
    assert isinstance(zelle, Paragraph)


def test_keine_zelle_der_rechtstabelle_laeuft_ueber():
    # Arrange
    zellen = pg.rechtstabelle_zellen()

    # Act & Assert
    for z, zeile in enumerate(zellen):
        for s, zelle in enumerate(zeile):
            if isinstance(zelle, Paragraph):
                continue  # bricht um, kann nicht überlaufen
            assert _passt_roh(str(zelle), pg.LEGAL_COL_WIDTHS[s], fett=(z == 0)), \
                f"Zeile {z}, Spalte {s}: „{zelle}“ ist breiter als ihre Spalte"


def test_die_spaltenbreiten_passen_auf_die_seite():
    # Arrange — A4 mit 20 mm Rand links und rechts
    nutzbar = 210 * mm - 40 * mm

    # Act & Assert
    assert sum(pg.LEGAL_COL_WIDTHS) <= nutzbar


def test_der_inhalt_der_tabelle_bleibt_vollstaendig():
    # Arrange & Act
    zellen = pg.rechtstabelle_zellen()

    # Assert — Kopfzeile plus sechs Rechtsgrundlagen, nichts gekürzt
    assert len(zellen) == len(pg.LEGAL_ROWS) + 1
    assert "DDG" in str(pg.LEGAL_ROWS[0][0])
    assert "TMG" in str(pg.LEGAL_ROWS[0][1]), \
        "Der Hinweis auf das abgelöste TMG darf nicht wegoptimiert werden"
