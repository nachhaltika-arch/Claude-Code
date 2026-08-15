"""
Die Mail, die ein Kunde bekommt, wenn sein Audit fertig ist.

Sie bestand aus vier Zeilen nacktem HTML — ``<h2>Ihr Audit-Bericht ist
bereit</h2>`` ohne Rahmen, ohne Marke, ohne Knopf — während der Empfänger
einer Widget-Analyse eine gestaltete Mail bekam. Derselbe Absender, zwei
Anmutungen.

Sie hatte noch einen zweiten Mangel: Ohne Adresse zum Bericht enthielt sie
gar keinen Weg zum Ergebnis, kündigte es aber an.
"""
from services import brand
from services.mail_vorlagen import audit_fertig_mail


def test_betreff_nennt_den_betrieb():
    betreff, _ = audit_fertig_mail("Referenz GmbH", "https://example.de/b/1")

    assert "Referenz GmbH" in betreff


def test_die_mail_traegt_den_gemeinsamen_rahmen():
    _, html = audit_fertig_mail("Referenz GmbH", "https://example.de/b/1")

    assert "max-width:560px" in html
    assert brand.DARK in html


def test_der_bericht_ist_einen_klick_entfernt():
    _, html = audit_fertig_mail("Referenz GmbH", "https://example.de/b/1")

    assert 'href="https://example.de/b/1"' in html


def test_ohne_adresse_wird_kein_bericht_versprochen():
    # Arrange & Act — vorher kündigte die Mail einen Bericht an und ließ den
    # Empfänger ohne jeden Weg dorthin stehen
    _, html = audit_fertig_mail("Referenz GmbH", "")

    # Assert
    assert "melden uns" in html.lower() or "melden wir uns" in html.lower()
    assert "href=\"\"" not in html


def test_der_firmenname_wird_maskiert():
    # Arrange — der Name kommt aus einer fremden Website
    _, html = audit_fertig_mail('Müller & Co <script>alert(1)</script>',
                                "https://example.de/b/1")

    # Assert
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
