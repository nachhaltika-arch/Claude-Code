"""
Der Rahmen, den jede KOMPAGNON-Mail trägt.

Die Widget-Mails waren gestaltet — Marke, Knopf, Outlook-feste Tabellen. Die
Mail an einen Bestandskunden, wenn sein Audit fertig ist, bestand dagegen aus
nacktem ``<h2>`` ohne Rahmen und ohne Marke. Zwei Wege, zwei Anmutungen, ein
Absender.

Der Rahmen steht jetzt an einer Stelle. Was sich je Anlass unterscheidet, ist
der Fußtext: Warum diese Mail ankommt, ist bei einer angeforderten Analyse
etwas anderes als bei einem laufenden Projekt.
"""
from services import brand
from services.mail_layout import knopf, rahmen


def test_der_rahmen_haelt_die_breite_auch_in_outlook():
    # Arrange & Act — Outlook auf Windows rendert mit der Word-Engine und
    # ignoriert max-width auf einem div; die Mail lief dort über die volle
    # Fensterbreite.
    html = rahmen("<p>Inhalt</p>", "Fußtext")

    # Assert
    assert "<table" in html
    assert "max-width:560px" in html
    assert 'role="presentation"' in html


def test_der_inhalt_steht_im_rahmen():
    html = rahmen("<p>Ein Satz</p>", "Fußtext")

    assert "<p>Ein Satz</p>" in html


def test_der_fusstext_wird_uebernommen():
    # Arrange — er begründet, warum die Mail ankommt, und das ist je Anlass
    # verschieden
    html = rahmen("<p>x</p>", "Sie erhalten diese Mail zu Ihrem Projekt.")

    # Assert
    assert "zu Ihrem Projekt" in html


def test_der_rahmen_traegt_die_marke():
    html = rahmen("<p>x</p>", "Fußtext")

    assert brand.DARK in html
    assert "KOMPAGNON" in html


def test_der_knopf_zeigt_auf_sein_ziel():
    # Act
    html = knopf("https://example.de/bericht", "Bericht ansehen")

    # Assert
    assert 'href="https://example.de/bericht"' in html
    assert "Bericht ansehen" in html
    assert brand.YELLOW in html


def test_die_widget_mails_nutzen_denselben_rahmen():
    # Arrange — sonst driften die beiden Wege wieder auseinander
    from services.widget_report import report_ready_email

    _, html = report_ready_email(company="Referenz GmbH", token="abc")

    # Assert
    assert "max-width:560px" in html
    assert 'role="presentation"' in html
    assert brand.DARK in html
