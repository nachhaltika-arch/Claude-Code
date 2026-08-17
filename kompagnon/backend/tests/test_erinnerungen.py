"""
Wann eine automatische Erinnerung faellig ist — und wann nicht mehr.

Anlass ist ein Vorfall vom 17.08.2026: ``job_check_missing_materials`` schickte
die Material-Erinnerung an **jedes** Projekt in ``phase_2``, dessen Start mehr
als fuenf Tage her war — **jeden Morgen aufs Neue**, ohne jede Sperre. Ein
Betrieb hat sie ueber 135 Tage taeglich bekommen.

Der Briefing-Job direkt darunter hatte die Sperre (Nachschlagen in
``communications`` ueber ``template_key``), dieser nicht. Beide benutzen jetzt
dieselbe Entscheidung, und die steht hier — als reine Funktion, ohne Datenbank,
damit sie ueberhaupt pruefbar ist.
"""
from automations.erinnerungen import (
    BRIEFING_STUFEN,
    MATERIAL_STUFEN,
    faellige_erinnerung,
)


# ── Der Vorfall ────────────────────────────────────────────────────────

def test_material_erinnerung_geht_genau_einmal_raus():
    # Arrange — der Betrieb aus dem Vorfall: Projektstart 135 Tage her
    bereits = set()

    # Act
    erste = faellige_erinnerung(135, MATERIAL_STUFEN, bereits)
    bereits.add(erste)
    zweite = faellige_erinnerung(135, MATERIAL_STUFEN, bereits)

    # Assert
    assert erste == "material_reminder"
    assert zweite is None, "am Folgetag darf nichts mehr rausgehen"


def test_material_erinnerung_bleibt_auch_nach_hundert_tagen_still():
    bereits = {"material_reminder"}

    for tag in (6, 30, 135, 400):
        assert faellige_erinnerung(tag, MATERIAL_STUFEN, bereits) is None


def test_material_erinnerung_kommt_nicht_zu_frueh():
    for tag in (0, 1, 4):
        assert faellige_erinnerung(tag, MATERIAL_STUFEN, set()) is None


def test_material_erinnerung_ab_tag_fuenf():
    assert faellige_erinnerung(5, MATERIAL_STUFEN, set()) == "material_reminder"


# ── Die gestaffelte Variante (Briefing) ────────────────────────────────

def test_briefing_waehlt_die_hoechste_erreichte_stufe():
    # An Tag 14 gehoert die Tag-14-Vorlage raus, nicht die von Tag 3
    assert faellige_erinnerung(14, BRIEFING_STUFEN, set()) == "briefing_reminder_day_14"


def test_briefing_durchlaeuft_die_stufen_der_reihe_nach():
    bereits = set()

    for tag, erwartet in ((3, "briefing_reminder_day_3"),
                          (7, "briefing_reminder_day_7"),
                          (14, "briefing_reminder_day_14")):
        stufe = faellige_erinnerung(tag, BRIEFING_STUFEN, bereits)
        assert stufe == erwartet
        bereits.add(stufe)

    assert faellige_erinnerung(90, BRIEFING_STUFEN, bereits) is None


def test_briefing_wiederholt_eine_erledigte_stufe_nicht():
    # Wer die Tag-14-Mail hat, bekommt sie an Tag 15 nicht noch einmal —
    # und faellt auch nicht auf eine niedrigere Stufe zurueck.
    bereits = {"briefing_reminder_day_14"}

    assert faellige_erinnerung(15, BRIEFING_STUFEN, bereits) is None
    assert faellige_erinnerung(200, BRIEFING_STUFEN, bereits) is None


def test_briefing_vor_der_ersten_stufe_still():
    assert faellige_erinnerung(2, BRIEFING_STUFEN, set()) is None


# ── Randfaelle ─────────────────────────────────────────────────────────

def test_ohne_stufen_passiert_nichts():
    assert faellige_erinnerung(999, (), set()) is None


def test_negative_laufzeit_loest_nichts_aus():
    # Ein Startdatum in der Zukunft darf keine Erinnerung ausloesen
    assert faellige_erinnerung(-3, MATERIAL_STUFEN, set()) is None


def test_unbekannte_laufzeit_loest_nichts_aus():
    assert faellige_erinnerung(None, MATERIAL_STUFEN, set()) is None


def test_bereits_gesendet_darf_auch_eine_liste_sein():
    # Der Aufrufer liest die Werte aus der Datenbank — als Liste, nicht als Menge
    assert faellige_erinnerung(135, MATERIAL_STUFEN, ["material_reminder"]) is None


def test_die_eingabe_wird_nicht_veraendert():
    bereits = {"material_reminder"}
    kopie = set(bereits)

    faellige_erinnerung(135, MATERIAL_STUFEN, bereits)

    assert bereits == kopie
