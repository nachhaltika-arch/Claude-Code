"""Die Häufigkeit der zwanzig Befunde — und der Nenner, an dem sie haengt (C7).

**Der Fehler, den dieser Test verhindert.** Wer die Vorkommen durch die Zahl
**aller** Pruefungen teilt, zaehlt jede ausgefallene Messung als „Befund liegt
nicht vor". Das ergibt zu niedrige Haeufigkeiten — und die stuenden dann
gedruckt in einem Kapitel, dessen Titel „die zwanzig **haeufigsten** Fehler"
lauten soll.

§ 3.5 der Bewertungslogik sagt es fuer den Score bereits: Nicht erhoben faellt
aus Zaehler **und** Nenner. Hier gilt dieselbe Regel.
"""
from services.audit_criteria import Source
from services.befund_haeufigkeit import BEFUNDE, haeufigkeit

GEMESSEN = Source.MEASURED.value
NICHT_ERHOBEN = Source.NOT_COLLECTED.value
NICHT_ANWENDBAR = Source.NOT_APPLICABLE.value


def _befund(ergebnis: list, nummer: int) -> dict:
    return next(e for e in ergebnis if e["nummer"] == nummer)


def test_eine_ausgefallene_messung_zaehlt_in_keiner_richtung():
    # Arrange — drei Pruefungen: eine mit Befund, eine ohne, eine ausgefallen.
    pruefungen = [
        ({"rc_impressum": 0}, {"rc_impressum": GEMESSEN}),
        ({"rc_impressum": 6}, {"rc_impressum": GEMESSEN}),
        ({"rc_impressum": 0}, {"rc_impressum": NICHT_ERHOBEN}),
    ]

    # Act
    eins = _befund(haeufigkeit(pruefungen), 1)

    # Assert
    assert eins["nenner"] == 2, "Die ausgefallene Messung gehoert nicht in den Nenner."
    assert eins["zaehler"] == 1
    assert eins["anteil"] == 50, (
        "Ueber alle drei geteilt waeren es 33 % — eine zu niedrige Haeufigkeit, "
        "erzeugt durch eine Messung, die es nie gab."
    )


def test_nicht_anwendbar_faellt_ebenso_heraus():
    """K6 hat keine lokalen Signale — das ist kein bestandener Befund."""
    # Arrange
    pruefungen = [
        ({"se_lokal": 0}, {"se_lokal": GEMESSEN}),
        ({"se_lokal": 0}, {"se_lokal": NICHT_ANWENDBAR}),
    ]

    # Act
    neun = _befund(haeufigkeit(pruefungen), 9)

    # Assert
    assert neun["nenner"] == 1
    assert neun["zaehler"] == 1


def test_ohne_pruefungen_gibt_es_keine_quote():
    """Null Prozent waere eine Aussage. Ohne Nenner gibt es keine."""
    # Arrange / Act
    ergebnis = haeufigkeit([])

    # Assert
    assert all(e["anteil"] is None for e in ergebnis)
    assert all(e["nenner"] == 0 for e in ergebnis)


def test_die_beiden_nicht_ableitbaren_befunde_bekommen_keine_zahl():
    """Befund 5 und 10 haben kein Kriterium, das sie allein traegt.

    Eine erfundene Zuordnung waere schlimmer als eine Luecke — sie saehe aus
    wie eine Erhebung.
    """
    # Arrange
    pruefungen = [({"ih_aktualitaet": 0}, {"ih_aktualitaet": GEMESSEN})]

    # Act
    ergebnis = haeufigkeit(pruefungen)

    # Assert
    for nummer in (5, 10):
        eintrag = _befund(ergebnis, nummer)
        assert eintrag["anteil"] is None
        assert eintrag["vorbehalt"], "Ohne Zahl muss der Grund dastehen."


def test_es_sind_zwanzig_und_jeder_hat_einen_titel():
    assert len(BEFUNDE) == 20
    assert [b.nummer for b in BEFUNDE] == list(range(1, 21))
    assert all(b.titel for b in BEFUNDE)


def test_jede_zuordnung_zeigt_auf_ein_kriterium_das_es_gibt():
    """Ein Tippfehler im Schluessel wuerde sonst still eine Null-Quote erzeugen."""
    from services.audit_criteria import find_criterion

    # Arrange / Act
    fehlend = [b.nummer for b in BEFUNDE
               if b.kriterium and find_criterion(b.kriterium) is None]

    # Assert
    assert not fehlend, f"Unbekanntes Kriterium bei Befund {fehlend}"


def test_wo_die_zahl_den_befund_nicht_allein_traegt_steht_ein_vorbehalt():
    """Befund 9 misst drei Dinge, gemeint ist eins. Das muss dastehen."""
    for nummer in (6, 9, 11, 13, 16, 18, 19, 20):
        assert _befund(haeufigkeit([]), nummer)["vorbehalt"], (
            f"Befund {nummer} braucht einen Vorbehalt — sonst liest sich eine "
            "Obergrenze wie eine Messung."
        )
