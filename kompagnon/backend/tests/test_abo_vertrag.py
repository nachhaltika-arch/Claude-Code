# -*- coding: utf-8 -*-
"""Welches Pflege-Abo gilt — die zweite Hälfte von L-101.

**Was auf dem Spiel steht.** ABO-PRO sagt zwei Stunden je Monat und Kunde zu.
Ohne Vertragsobjekt war jede Restzahl geraten, und deshalb gab
`abo_stunden.monatsstand()` bis zum 01.09.2026 nur den **Verbrauch** aus. Jetzt
gibt es den Vertrag — und damit drei Regeln, deren Verletzung jeweils Geld
kostet, ohne aufzufallen.

**Die teuerste ist die dritte.** Ein Wechsel von ABO-BAS auf ABO-PRO darf die
bestehende Zeile nicht überschreiben: Wird der Juli später noch einmal
aufgerufen, muss das Kontingent gelten, das **im Juli** galt. Überschrieben
rechnete die Vergangenheit still mit dem Abo von heute, und eine Überschreitung
von damals wäre danach keine mehr.
"""
import pytest

from services import abo_vertrag
from services.abo_stunden import (KONTINGENT_ABO_PRO_STUNDEN, AboZeitFehler,
                                  eintragen, monatsstand)

BETRIEB_NAME = "Dachdecker Vertrag-Nur-Im-Test"

pytestmark = pytest.mark.usefixtures("app")


@pytest.fixture()
def db(app):
    from database import SessionLocal
    sitzung = SessionLocal()
    try:
        yield sitzung
    finally:
        sitzung.close()


@pytest.fixture()
def betrieb(db):
    from database import Lead, TimeTracking

    from modelle_abo import AboVertrag

    lead = Lead(company_name=BETRIEB_NAME)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    kennung = lead.id
    try:
        yield kennung
    finally:
        db.query(AboVertrag).filter(AboVertrag.lead_id == kennung).delete()
        db.query(TimeTracking).filter(TimeTracking.lead_id == kennung).delete()
        db.query(Lead).filter(Lead.id == kennung).delete()
        db.commit()


# ── Der Normalfall ───────────────────────────────────────────────────

def test_mit_vertrag_steht_die_restzahl_da(db, betrieb):
    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                        start_monat="2026-08")
    eintragen(db, lead_id=betrieb, stunden=0.5, wer="Test", monat="2026-08")

    stand = monatsstand(db, lead_id=betrieb, monat="2026-08")

    assert stand["verbraucht"] == 0.5
    assert stand["kontingent_stunden"] == KONTINGENT_ABO_PRO_STUNDEN
    assert stand["verbleibend_stunden"] == 1.0
    assert stand["ueberzogen"] is False
    assert stand["abo"]["produkt"] == "ABO-PRO"


def test_eine_ueberschreitung_wird_gezeigt_und_nicht_auf_null_gekappt(
        db, betrieb):
    """**Auf Null zu begrenzen versteckte genau den Fall, für den das
    Kontingent gebaut ist.** Wer 3,5 Stunden auf
    1,5 zugesagte bucht, soll −2,0 lesen und nicht 0 — die Null sähe aus wie
    „gerade aufgebraucht"."""
    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                        start_monat="2026-08")
    eintragen(db, lead_id=betrieb, stunden=3.5, wer="Test", monat="2026-08")

    stand = monatsstand(db, lead_id=betrieb, monat="2026-08")

    assert stand["verbleibend_stunden"] == -2.0
    assert stand["ueberzogen"] is True


def test_abo_bas_hat_ein_kleineres_kontingent_und_nicht_gar_keins(db, betrieb):
    """**Am 01.09.2026 richtiggestellt.** Hier stand, ABO-BAS sage keine
    Änderungsstunden zu — das kam aus dem Lagebild-Text. Das Datenblatt
    nennt in Position 5 **30 Minuten je Monat**.

    Der Unterschied ist teuer: Mit einem Kontingent von 0,0 wäre **jede**
    Minute eines Basic-Kunden eine Überschreitung gewesen, und wir hätten
    berechnet, was im Preis steht.
    """
    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-BAS",
                        start_monat="2026-08")
    eintragen(db, lead_id=betrieb, stunden=0.25, wer="Test", monat="2026-08")

    stand = monatsstand(db, lead_id=betrieb, monat="2026-08")

    assert stand["abo"] is not None
    assert stand["kontingent_stunden"] == 0.5
    assert stand["verbleibend_stunden"] == 0.25
    assert stand["ueberzogen"] is False, "eine Viertelstunde ist im Preis"
    assert stand["hinweis"] == ""


def test_ein_monat_vor_dem_vertrag_hat_kein_kontingent(db, betrieb):
    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                        start_monat="2026-08")

    stand = monatsstand(db, lead_id=betrieb, monat="2026-07")

    assert stand["abo"] is None
    assert "kein Pflege-Abo" in stand["hinweis"]


def test_ein_monat_nach_dem_ende_hat_kein_kontingent(db, betrieb):
    v = abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                            start_monat="2026-01")
    abo_vertrag.beenden(db, vertrag_id=v.id, end_monat="2026-08")

    assert monatsstand(db, lead_id=betrieb, monat="2026-08")["abo"] is not None
    assert monatsstand(db, lead_id=betrieb, monat="2026-09")["abo"] is None


# ── Die drei Regeln ──────────────────────────────────────────────────

def test_zwei_vertraege_duerfen_sich_nicht_ueberlappen(db, betrieb):
    """Zwei gültige Verträge für denselben Monat verdoppelten das Kontingent —
    und niemand sähe es, weil beide für sich richtig aussehen."""
    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                        start_monat="2026-08")

    with pytest.raises(AboZeitFehler, match="bereits ein Vertrag"):
        abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-BAS",
                            start_monat="2026-09")


def test_ein_wechsel_beendet_den_alten_und_laesst_die_vergangenheit_stehen(
        db, betrieb):
    """**Die teuerste Regel.** Der Juli muss mit dem Abo rechnen, das im Juli
    galt — nicht mit dem von heute."""
    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-BAS",
                        start_monat="2026-07")
    eintragen(db, lead_id=betrieb, stunden=1.0, wer="Test", monat="2026-07")

    abo_vertrag.wechseln(db, lead_id=betrieb, produkt="ABO-PRO",
                         ab_monat="2026-08")

    juli = monatsstand(db, lead_id=betrieb, monat="2026-07")
    august = monatsstand(db, lead_id=betrieb, monat="2026-08")

    assert juli["abo"]["produkt"] == "ABO-BAS"
    assert juli["kontingent_stunden"] == 0.5
    assert juli["ueberzogen"] is True, "eine Stunde auf 30 Minuten ist zu viel"
    assert august["abo"]["produkt"] == "ABO-PRO"
    assert august["kontingent_stunden"] == KONTINGENT_ABO_PRO_STUNDEN

    alle = abo_vertrag.vertraege(db, betrieb)
    assert len(alle) == 2, "der alte Vertrag bleibt stehen, er wird beendet"
    assert {v.produkt: v.end_monat for v in alle} == {
        "ABO-BAS": "2026-07", "ABO-PRO": None}


def test_hoechstens_ein_laufender_vertrag(db, betrieb):
    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                        start_monat="2026-08")
    laufende = [v for v in abo_vertrag.vertraege(db, betrieb)
                if v.end_monat is None]
    assert len(laufende) == 1

    abo_vertrag.wechseln(db, lead_id=betrieb, produkt="ABO-BAS",
                         ab_monat="2026-10")
    laufende = [v for v in abo_vertrag.vertraege(db, betrieb)
                if v.end_monat is None]
    assert len(laufende) == 1, "ein Wechsel darf keine zweite offene Zusage lassen"


def test_ein_wechsel_im_startmonat_wird_abgelehnt(db, betrieb):
    """Sonst entstünden zwei Verträge, die im selben Monat beginnen — welcher
    dann gilt, entschiede die Sortierung und nicht die Sache."""
    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-BAS",
                        start_monat="2026-08")
    with pytest.raises(AboZeitFehler, match="Folgemonat"):
        abo_vertrag.wechseln(db, lead_id=betrieb, produkt="ABO-PRO",
                             ab_monat="2026-08")


def test_ein_ende_vor_dem_beginn_wird_abgelehnt(db, betrieb):
    with pytest.raises(AboZeitFehler, match="vor dem Beginn"):
        abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-PRO",
                            start_monat="2026-08", end_monat="2026-07")


def test_ein_unbekanntes_abo_wird_abgelehnt(db, betrieb):
    with pytest.raises(AboZeitFehler, match="Unbekanntes Abo"):
        abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-GOLD",
                            start_monat="2026-08")


def test_der_jahreswechsel_rechnet_richtig(db, betrieb):
    """Der Vormonat des Januar ist der Dezember des Vorjahrs — der Ort, an dem
    eine Monatsrechnung von Hand gern danebenliegt."""
    abo_vertrag.anlegen(db, lead_id=betrieb, produkt="ABO-BAS",
                        start_monat="2025-11")
    abo_vertrag.wechseln(db, lead_id=betrieb, produkt="ABO-PRO",
                         ab_monat="2026-01")

    alt = [v for v in abo_vertrag.vertraege(db, betrieb)
           if v.produkt == "ABO-BAS"][0]
    assert alt.end_monat == "2025-12"


# ── Eine Quelle für die Kontingente ──────────────────────────────────

def test_die_kontingente_kommen_aus_abo_stunden():
    """Zwei Orte für dieselbe Zahl sind ein Ort, an dem sie abweicht."""
    from services import abo_stunden

    assert abo_vertrag.KONTINGENT["ABO-PRO"] is \
        abo_stunden.KONTINGENT_ABO_PRO_STUNDEN
    assert abo_vertrag.KONTINGENT["ABO-BAS"] is \
        abo_stunden.KONTINGENT_ABO_BAS_STUNDEN


# ── Die Endpunkte ────────────────────────────────────────────────────

def test_die_routen_verlangen_den_innendienst(client, betrieb):
    """Pflegestunden und Verträge eines fremden Betriebs sind Geschäftsdaten."""
    assert client.get(f"/api/leads/{betrieb}/abo-vertrag").status_code in (401, 403)
    assert client.post(f"/api/leads/{betrieb}/abo-vertrag",
                       json={"produkt": "ABO-PRO"}).status_code in (401, 403)


def test_ein_vertrag_laesst_sich_ueber_den_endpunkt_abschliessen(
        client, auth_headers, betrieb):
    antwort = client.post(f"/api/leads/{betrieb}/abo-vertrag",
                          json={"produkt": "ABO-PRO", "start_monat": "2026-08"},
                          headers=auth_headers)
    assert antwort.status_code == 200, antwort.text
    assert antwort.json()["laeuft"] is True

    liste = client.get(f"/api/leads/{betrieb}/abo-vertrag",
                       headers=auth_headers).json()
    assert liste["laufend"]["produkt"] == "ABO-PRO"
    assert liste["abos"]["ABO-PRO"] == KONTINGENT_ABO_PRO_STUNDEN


def test_ein_fremder_vertrag_wird_nicht_beendet(client, auth_headers, betrieb):
    """**Erst prüfen, dann schreiben.** Der erste Entwurf beendete zuerst und
    antwortete danach mit 404 — der Vertrag wäre beendet gewesen, und der
    Aufrufer hätte gelesen, es gebe ihn nicht."""
    from database import Lead, SessionLocal

    from modelle_abo import AboVertrag

    sitzung = SessionLocal()
    try:
        fremder = Lead(company_name="Fremder Betrieb Vertragstest")
        sitzung.add(fremder)
        sitzung.commit()
        sitzung.refresh(fremder)
        vertrag = abo_vertrag.anlegen(sitzung, lead_id=fremder.id,
                                      produkt="ABO-PRO", start_monat="2026-08")
        vertrag_id, fremd_id = vertrag.id, fremder.id
    finally:
        sitzung.close()

    try:
        antwort = client.patch(
            f"/api/leads/{betrieb}/abo-vertrag/{vertrag_id}",
            json={"end_monat": "2026-09"}, headers=auth_headers)
        assert antwort.status_code == 404

        sitzung = SessionLocal()
        try:
            unberuehrt = sitzung.query(AboVertrag).filter(
                AboVertrag.id == vertrag_id).first()
            assert unberuehrt.end_monat is None, \
                "der fremde Vertrag darf nicht beendet worden sein"
        finally:
            sitzung.close()
    finally:
        sitzung = SessionLocal()
        try:
            sitzung.query(AboVertrag).filter(
                AboVertrag.lead_id == fremd_id).delete()
            sitzung.query(Lead).filter(Lead.id == fremd_id).delete()
            sitzung.commit()
        finally:
            sitzung.close()
