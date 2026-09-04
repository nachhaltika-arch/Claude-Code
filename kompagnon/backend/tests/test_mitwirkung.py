# -*- coding: utf-8 -*-
"""Was wir vom Kunden brauchen — im Konto, mit Datum und Fristwirkung (L-159).

**Der Anlass.** Die Mitwirkungsleistungen M1 bis M11 stehen seit jeher im
Angebotsbaukasten und nirgends im Kundenkonto. Der Betrieb bekam gestaffelt
die Mail „Materialien fehlen" — ohne zu erfahren **welche**, und ohne den Stand
irgendwo nachsehen zu koennen.

**Und sie tragen die Frist.** Die Bauzeit beginnt an dem Werktag, an dem alle
Fristbeginn-Punkte vorliegen. Ohne festgehaltenes Eingangsdatum je Punkt ist
die Bauzeitgarantie entweder unverbindlich — dann ist sie keine Garantie — oder
ruinoes, dann zahlen wir fuer die Langsamkeit des Kunden (Blocker L6).
"""
import pytest

from services import mitwirkung as kat


# ── Der Katalog ───────────────────────────────────────────────────────

def test_der_katalog_traegt_den_wortlaut_aus_dem_angebot():
    """Kundensprache und Vertragssprache stehen nebeneinander — nicht in zwei
    Dateien, die auseinanderlaufen koennen."""
    m3 = kat.NACH_KENNUNG["M3"]

    assert m3.titel == "Logo und Bilder"
    assert "2.000 px" in m3.vertragstext
    assert m3.wirkung == kat.FRISTBEGINN


def test_die_beiden_freigaben_pausieren_die_frist_und_beginnen_sie_nicht():
    assert kat.NACH_KENNUNG["M7"].wirkung == kat.FRISTPAUSE
    assert kat.NACH_KENNUNG["M8"].wirkung == kat.FRISTPAUSE


def test_bedingte_punkte_erscheinen_nur_wenn_sie_gelten():
    """Eine Liste mit zehn Zeilen, von denen acht grau sind, ist eine Liste mit
    zehn Zeilen. Was nicht gilt, erscheint gar nicht."""
    ohne = {p.kennung for p in kat.gilt_fuer(set())}
    mit = {p.kennung for p in kat.gilt_fuer({"migration", "karriereseite"})}

    assert "M9" not in ohne and "M10" not in ohne
    assert "M9" in mit and "M10" in mit


def test_nur_fristbeginn_punkte_halten_den_start_auf():
    punkte = kat.gilt_fuer(set())
    offen = {p.kennung for p in kat.fristbeginn_offen(punkte, {"M4", "M6"})}

    assert offen == {"M1", "M2", "M3", "M5"}
    assert "M7" not in offen, "eine Freigabe kann keine Frist aufhalten, die noch nicht laeuft"
    assert "M11" not in offen, "die Rechnungsdaten haben keine Fristwirkung"


# ── Der Weg durch das Portal ──────────────────────────────────────────

@pytest.fixture
def kundenprojekt(app, kunde_user):
    """Ein Projekt am Betrieb des Kunden — sonst gibt es nichts anzuzeigen."""
    from database import SessionLocal, Project

    db = SessionLocal()
    try:
        vorhanden = (db.query(Project)
                     .filter(Project.lead_id == kunde_user.lead_id).first())
        if not vorhanden:
            vorhanden = Project(lead_id=kunde_user.lead_id, status="phase_1")
            db.add(vorhanden); db.commit(); db.refresh(vorhanden)
        db.query(__import__("database").MitwirkungStand).filter_by(
            project_id=vorhanden.id).delete()
        db.commit()
        return vorhanden.id
    finally:
        db.close()


def test_das_konto_zeigt_die_punkte_getrennt_nach_wirkung(client, kunde_headers, kundenprojekt):
    """Lieferungen vor dem Start und Freigaben mittendrin sind zwei Dinge.
    Gemischt sieht die Aufgabe doppelt so gross aus."""
    antwort = client.get("/api/portal/mitwirkung", headers=kunde_headers)

    assert antwort.status_code == 200
    d = antwort.json()
    assert [p["kennung"] for p in d["spaeter"]] == ["M7", "M8"]
    assert "M7" not in [p["kennung"] for p in d["punkte"]]
    assert d["start_moeglich"] is False


def test_ein_eingetragener_punkt_bekommt_datum_und_namen(client, kunde_headers, kundenprojekt):
    """Das Datum ist nicht Zierrat — aus ihm entsteht der Fristbeginn."""
    gesetzt = client.post("/api/portal/mitwirkung/M5", json={}, headers=kunde_headers)

    assert gesetzt.status_code == 200
    d = client.get("/api/portal/mitwirkung", headers=kunde_headers).json()
    m5 = next(p for p in d["punkte"] if p["kennung"] == "M5")
    assert m5["erledigt"] is True
    assert m5["erledigt_am"]
    assert "@" in m5["bestaetigt_von"], "wer es eingetragen hat, gehoert dazu"


def test_der_zweite_klick_verschiebt_den_eingang_nicht(client, kunde_headers, kundenprojekt):
    """Sonst haette der Fristbeginn zwei Antworten."""
    erst = client.post("/api/portal/mitwirkung/M5", json={}, headers=kunde_headers).json()
    nochmal = client.post("/api/portal/mitwirkung/M5", json={}, headers=kunde_headers).json()

    assert erst["erledigt_am"] == nochmal["erledigt_am"]


def test_der_start_ist_erst_moeglich_wenn_alle_fristpunkte_vorliegen(
        client, kunde_headers, kundenprojekt):
    offen = client.get("/api/portal/mitwirkung", headers=kunde_headers).json()
    for punkt in offen["punkte"]:
        client.post(f"/api/portal/mitwirkung/{punkt['kennung']}", json={},
                    headers=kunde_headers)

    danach = client.get("/api/portal/mitwirkung", headers=kunde_headers).json()

    assert danach["offen"] == 0
    assert danach["start_moeglich"] is True
    assert danach["erledigt"] == danach["gesamt"]


def test_ein_unbekannter_punkt_wird_abgewiesen(client, kunde_headers, kundenprojekt):
    antwort = client.post("/api/portal/mitwirkung/M99", json={}, headers=kunde_headers)

    assert antwort.status_code == 404
