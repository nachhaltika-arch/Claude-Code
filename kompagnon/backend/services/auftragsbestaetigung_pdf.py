"""
Auftragsbestätigung PDF Generator — KOMPAGNON Communications BP GmbH
Erstellt eine professionelle Auftragsbestätigung als PDF-Bytes via ReportLab.
"""
import os
import unicodedata
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont



def ablage_verzeichnis():
    """Wohin die Auftragsbestätigungen geschrieben werden.

    Lag fest verdrahtet unter `uploads/auftragsbestaetigungen` und folgte
    damit nicht dem eingehängten Datenträger — die PDFs waren nach jedem
    Deploy weg.
    """
    from services.dateiablage import upload_wurzel
    return upload_wurzel() / "auftragsbestaetigungen"

def _register_fonts():
    try:
        import reportlab
        font_path = os.path.join(os.path.dirname(reportlab.__file__), "fonts")
        pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(font_path, "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", os.path.join(font_path, "DejaVuSans-Bold.ttf")))
        return "DejaVu", "DejaVu-Bold"
    except Exception:
        return "Helvetica", "Helvetica-Bold"


def _euro(betrag) -> str:
    """Ein Betrag in deutscher Schreibweise: `4.165,00 EUR`.

    **Der Anlass (27.08.2026, David).** Das Dokument schrieb `4165.00 EUR` —
    englische Schreibweise, ohne Tausenderpunkt, in einer Auftragsbestaetigung
    einer deutschen GmbH an deutsche Handwerksbetriebe. Kein Fehler in der
    Zahl, aber einer im Beleg: Er sieht aus, als waere er nicht fuer den
    Empfaenger gemacht.

    **Ohne `locale`.** Das Modul haengt an dem, was im Betriebssystem des
    Servers installiert ist; `de_DE.UTF-8` fehlt in schlanken Containern, und
    `setlocale` wirkt prozessweit — es wuerde jede andere Zahlenausgabe
    desselben Dienstes mitveraendern. Zwei Zeilen Umstellen sind hier der
    ehrlichere Weg als eine globale Einstellung fuer eine Tabellenzelle.
    """
    ganz, _, nach = f"{float(betrag or 0):,.2f}".partition(".")
    return f"{ganz.replace(',', '.')},{nach} EUR"


def _steuerzeile(paket: dict) -> str:
    """„MwSt. 19 %" — mit dem Satz aus dem Produkt, nicht mit einem festen.

    Hier stand die Zahl **fest im Dokument**. Das Buch hat sieben Prozent; ein
    Beleg darueber haette „MwSt. 19 %" ausgewiesen und daneben den
    7-%-Betrag — eine falsche Angabe auf einem Steuerdokument. Dieselbe
    Bauart wie die feste Preisliste, die am 22.08.2026 aus derselben Datei
    verschwand (L-29).

    Fehlt der Satz, steht dort **kein Prozentwert** statt eines erfundenen.
    """
    satz = paket.get("steuersatz")
    if satz is None:
        return "MwSt."
    return f"MwSt. {satz:.0f} %" if float(satz) == int(satz) else f"MwSt. {satz} %"


def _clean_text(text):
    """Normalize Unicode text for PDF rendering."""
    if not text:
        return ""
    if not isinstance(text, str):
        text = str(text)
    return unicodedata.normalize("NFC", text)


# ── Die feste Preisliste stand hier bis zum 22.08.2026 (L-29) ────────
#
# `PAKETE = {"starter": {...1500.00...}, "kompagnon": {...2000.00...},
#            "premium": {...2800.00...}}`
#
# Dieselbe Bauart wie das laengst entfernte `PACKAGE_NAMES`, nur in dem
# Dokument, das der Kunde als **Beleg** bekommt. Der tatsaechlich gezahlte
# Betrag kam als `amount_eur` herein und wurde **nirgends benutzt**; jede
# Zahl im PDF stammte aus dieser Liste. Ein in `products` geaenderter Preis
# stand hier weiter alt da, und ein unbekanntes Paket bekam
# `PAKETE["kompagnon"]` — falscher Paketname, 2.000 EUR, falsch
# ausgewiesene Umsatzsteuer.
#
# Die Zahlen kommen jetzt von aussen herein: `services/paket_beleg.py` holt
# sie aus derselben Zeile, aus der auch abgerechnet wird. Die Darstellung
# holt nichts mehr selbst — sonst haette sie wieder ihre eigene Quelle, und
# genau das war der Fehler.


def generate_auftragsbestaetigung(
    session_id: str,
    customer_name: str,
    customer_email: str,
    company_name: str,
    paket: dict,
    datum: str,
) -> bytes:
    """Erstellt eine Auftragsbestätigung als PDF-Bytes.

    `paket` kommt aus `services/paket_beleg.py::paket_fuer_beleg` und traegt
    Name, Brutto, Netto, Umsatzsteuer und Leistungen. Diese Funktion holt
    **nichts** selbst — sonst haette die Darstellung wieder ihre eigene
    Preisquelle, und genau das war der Fehler (L-29).
    """
    mwst = paket["mwst"]

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=20*mm, bottomMargin=25*mm,
        leftMargin=25*mm, rightMargin=25*mm,
    )

    fn, fb = _register_fonts()

    KC_TEAL   = colors.HexColor("#008eaa")
    KC_DARK   = colors.HexColor("#1a2332")
    KC_GRAY   = colors.HexColor("#64748b")
    KC_LIGHT  = colors.HexColor("#f8f9fa")
    KC_GREEN  = colors.HexColor("#1D9E75")
    KC_WHITE  = colors.white
    KC_BORDER = colors.HexColor("#e2e8f0")

    def ps(name, **kw):
        """Ein Absatzformat mit Vorgaben, die der Aufrufer **ueberschreiben
        darf**.

        **Der Befund (27.08.2026, erster echter Testkauf).** Hier stand

            return ParagraphStyle(name, fontName=fn, textColor=KC_DARK, **kw)

        und drei Aufrufer unten geben genau diese beiden Namen noch einmal
        mit (`fontName=fb`, `textColor=KC_GRAY`). Python bricht bei einem
        doppelten Schluesselwort ab:

            TypeError: ParagraphStyle() got multiple values for
                       keyword argument 'fontName'

        Damit ist **nie eine Auftragsbestaetigung entstanden**, seit es diese
        Funktion gibt. Aufgefallen ist es nicht, weil der Fehler im
        Zahlungspfad in einem `except Exception` landet und dort nur
        protokolliert wird — richtig so, eine kaputte Beilage darf keinen
        Kauf kippen. Nur sieht dann eben niemand hin.

        **Und kein Test hat es gefunden**, obwohl es zwei zu dieser Datei
        gibt: Sie pruefen die *Preisermittlung* rund um das PDF. **Erzeugt**
        hat das Dokument keiner. Dieselbe Luecke wie beim StripeObject am
        selben Abend — geprueft wurde alles ausser dem Gegenstand.
        """
        vorgaben = {"fontName": fn, "textColor": KC_DARK}
        vorgaben.update(kw)             # der Aufrufer hat das letzte Wort
        return ParagraphStyle(name, **vorgaben)

    st_label   = ps("label",   fontSize=8,  fontName=fb, textColor=KC_GRAY,
                    spaceAfter=2, leading=10)
    st_value   = ps("value",   fontSize=10, spaceAfter=2, leading=13)
    st_section = ps("section", fontSize=11, fontName=fb, textColor=KC_TEAL,
                    spaceAfter=4, spaceBefore=8)
    st_item    = ps("item",    fontSize=9,  textColor=KC_GRAY, leading=14)
    st_right   = ps("right",   fontSize=9,  alignment=TA_RIGHT)

    def footer_cb(canvas_obj, doc_ref):
        canvas_obj.saveState()
        canvas_obj.setFont(fn, 7)
        canvas_obj.setFillColor(KC_GRAY)
        w, _ = A4
        canvas_obj.drawString(
            25*mm, 12*mm,
            _clean_text(
                "KOMPAGNON Communications BP GmbH  |  "
                "kompagnon.eu  |  info@kompagnon.eu"
            )
        )
        canvas_obj.drawRightString(
            w - 25*mm, 12*mm,
            _clean_text(f"Seite {doc_ref.page}")
        )
        canvas_obj.restoreState()

    story = []

    # ── HEADER-BALKEN ─────────────────────────────────────
    header_data = [[
        Paragraph(
            '<font color="white"><b>KOMPAGNON</b></font>',
            ParagraphStyle("hd", fontName=fb, fontSize=20, textColor=KC_WHITE)
        ),
        Paragraph(
            '<font color="white">Auftragsbestaetigung</font>',
            ParagraphStyle("hd2", fontName=fn, fontSize=11,
                           textColor=KC_WHITE, alignment=TA_RIGHT)
        ),
    ]]
    header_tbl = Table(header_data, colWidths=[90*mm, 75*mm])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), KC_TEAL),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 8*mm))

    # ── RECHNUNGS-METADATEN ───────────────────────────────
    short_id = (session_id[:24] + "...") if len(session_id) > 24 else session_id
    meta_data = [
        [
            Paragraph(_clean_text("AUFTRAGGEBER"),  st_label),
            Paragraph(_clean_text("BESTELLNUMMER"), st_label),
        ],
        [
            Paragraph(_clean_text(company_name or customer_name), st_value),
            Paragraph(_clean_text(short_id), st_value),
        ],
        [
            Paragraph(_clean_text(customer_name), st_value),
            Paragraph(_clean_text("DATUM"), st_label),
        ],
        [
            Paragraph(_clean_text(customer_email), st_value),
            Paragraph(_clean_text(datum), st_value),
        ],
    ]
    meta_tbl = Table(meta_data, colWidths=[95*mm, 70*mm])
    meta_tbl.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=KC_BORDER))
    story.append(Spacer(1, 5*mm))

    # ── ANREDE ────────────────────────────────────────────
    story.append(Paragraph(
        _clean_text("Sehr geehrte Damen und Herren,"),
        ps("body", fontSize=10, spaceAfter=4)
    ))
    story.append(Paragraph(
        _clean_text(
            "vielen Dank fuer Ihr Vertrauen! Wir freuen uns, "
            "Ihnen hiermit die Auftragsbestaetigung fuer Ihr "
            "neues Website-Projekt zu uebermitteln."
        ),
        ps("body2", fontSize=10, spaceAfter=8)
    ))

    # ── LEISTUNGSUMFANG ───────────────────────────────────
    story.append(Paragraph(
        _clean_text(f"Beauftragtes Paket: {paket['name']}"),
        st_section
    ))
    for item in paket["leistungen"]:
        story.append(Paragraph(_clean_text(f"  +  {item}"), st_item))

    story.append(Spacer(1, 6*mm))

    # ── PREISTABELLE ──────────────────────────────────────
    price_data = [
        [
            Paragraph(_clean_text("Leistung"),
                      ParagraphStyle("th",  fontName=fb, fontSize=9,
                                     textColor=KC_WHITE)),
            Paragraph(_clean_text("Betrag"),
                      ParagraphStyle("th2", fontName=fb, fontSize=9,
                                     textColor=KC_WHITE, alignment=TA_RIGHT)),
        ],
        [
            Paragraph(_clean_text(paket["name"]), st_value),
            Paragraph(_clean_text(_euro(paket['netto'])), st_right),
        ],
        [
            Paragraph(_clean_text("Nettobetrag"), st_label),
            Paragraph(_clean_text(_euro(paket['netto'])), st_right),
        ],
        [
            Paragraph(_clean_text(_steuerzeile(paket)), st_label),
            Paragraph(_clean_text(_euro(mwst)), st_right),
        ],
        [
            Paragraph(
                _clean_text("GESAMTBETRAG inkl. MwSt."),
                ParagraphStyle("total", fontName=fb, fontSize=11,
                               textColor=KC_WHITE)
            ),
            Paragraph(
                _clean_text(_euro(paket['brutto'])),
                ParagraphStyle("totalr", fontName=fb, fontSize=11,
                               textColor=KC_WHITE, alignment=TA_RIGHT)
            ),
        ],
    ]
    price_tbl = Table(price_data, colWidths=[120*mm, 45*mm])
    price_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), KC_TEAL),
        ("BACKGROUND",    (0, 4), (-1, 4), KC_GREEN),
        ("BACKGROUND",    (0, 2), (-1, 3), KC_LIGHT),
        ("GRID",          (0, 0), (-1, -1), 0.5, KC_BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    story.append(price_tbl)
    story.append(Spacer(1, 8*mm))

    # ── NÄCHSTE SCHRITTE ──────────────────────────────────
    story.append(Paragraph(_clean_text("Ihre naechsten Schritte"), st_section))
    # Die Lieferzeit stand frueher als letzter Punkt in der Leistungsliste
    # und wurde von dort abgelesen. Sie kommt jetzt aus `products.delivery_days`
    # — auf `features` angewandt haette das Ablesen „30 Tage Support" als
    # Lieferzeit ausgewiesen. Fehlt sie, behauptet der Beleg keine.
    tage = paket.get("lieferzeit_tage")
    steps = [
        "Sie erhalten in Kuerze eine E-Mail mit Ihren Zugangsdaten zum Kundenportal.",
        "Bitte fuellen Sie das Online-Briefing in Ihrem Kundenportal aus (ca. 10 Min.).",
        "Wir melden uns innerhalb von 24 Stunden fuer den Strategy Workshop.",
    ]
    if tage:
        steps.append(f"Ihre neue Website ist in {tage} Werktagen fertig.")
    for i, step in enumerate(steps, 1):
        story.append(Paragraph(
            _clean_text(f"{i}.  {step}"),
            ps(f"step{i}", fontSize=9, textColor=KC_GRAY,
               leftIndent=4, spaceAfter=4)
        ))

    story.append(Spacer(1, 8*mm))

    # ── UNTERSCHRIFT-PLATZHALTER ──────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=KC_BORDER))
    story.append(Spacer(1, 4*mm))

    sig_data = [
        [
            Paragraph(_clean_text("KOMPAGNON Communications BP GmbH"),
                      ps("sig1", fontSize=9, fontName=fb)),
            Paragraph(_clean_text("Auftraggeber"),
                      ps("sig2", fontSize=9, fontName=fb, alignment=TA_RIGHT)),
        ],
        [
            Paragraph(_clean_text(f"Ort, Datum: Koblenz, {datum}"),
                      ps("sig3", fontSize=8, textColor=KC_GRAY)),
            Paragraph(_clean_text("Ort, Datum: ____________________"),
                      ps("sig4", fontSize=8, textColor=KC_GRAY, alignment=TA_RIGHT)),
        ],
        [
            Paragraph(_clean_text("Unterschrift: ___________________________"),
                      ps("sig5", fontSize=8, textColor=KC_GRAY, spaceAfter=2)),
            Paragraph(_clean_text("Unterschrift: ___________________________"),
                      ps("sig6", fontSize=8, textColor=KC_GRAY,
                         spaceAfter=2, alignment=TA_RIGHT)),
        ],
    ]
    sig_tbl = Table(sig_data, colWidths=[82*mm, 82*mm])
    sig_tbl.setStyle(TableStyle([
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(sig_tbl)

    doc.build(story, onFirstPage=footer_cb, onLaterPages=footer_cb)
    return buffer.getvalue()


def save_auftragsbestaetigung(
    session_id: str,
    customer_name: str,
    customer_email: str,
    company_name: str,
    package_id: str,
    amount_eur: float,
    db=None,
) -> str:
    """
    Generiert PDF, speichert unter uploads/auftragsbestaetigungen/
    und gibt den Dateipfad zurück.

    Die Zahlen kommen aus der Produktzeile, sonst aus dem gezahlten Betrag
    (`paket_fuer_beleg`). Liegt beides nicht vor, wird **kein** Beleg
    erzeugt — ein Beleg mit erfundenen Zahlen waere schlechter als keiner.
    """
    from pathlib import Path

    from services.paket_beleg import paket_fuer_beleg

    paket = paket_fuer_beleg(db, package_id, amount_eur)

    datum     = datetime.now().strftime("%d.%m.%Y")
    pdf_bytes = generate_auftragsbestaetigung(
        session_id     = session_id,
        customer_name  = customer_name,
        customer_email = customer_email,
        company_name   = company_name,
        paket          = paket,
        datum          = datum,
    )

    upload_dir = ablage_verzeichnis()
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename  = f"AB-{datum.replace('.', '')}-{session_id[:8]}.pdf"
    file_path = upload_dir / filename
    file_path.write_bytes(pdf_bytes)

    return str(file_path)
