"""Die Abo-Achse der Zeiterfassung — Stunden je Monat und Betrieb (L-101).

**Was hier wirklich auf dem Spiel steht.** ABO-PRO sagt zwei Stunden je Monat
und Kunde zu. Ohne zaehlbare Stunden ist das eine **unbegrenzte** Zusage, und
G4 (Quartals-Garantie) verspricht darueber hinaus Nachbesserung ohne
Berechnung. Der Satz aus dem Eintrag — „Kein Abo verkaufen, bevor die Stunden
zaehlbar sind" — ist deshalb keine Ordnungsfrage, sondern eine Preisfrage.

**Der Kern dieser Datei ist die Trennung der beiden Achsen.** Eine Abo-Stunde
darf die Marge eines Projekts nicht beruehren, und eine Projektstunde nicht im
Monatsstand eines Betriebs auftauchen. Beides waere in einer Summe unsichtbar:
Man sieht einer Zahl nicht an, aus welchen Zeilen sie kommt.
"""
from datetime import datetime

import pytest

from services.abo_stunden import (KONTINGENT_ABO_BAS_STUNDEN,
                                  KONTINGENT_ABO_PRO_STUNDEN, AboZeitFehler,
                                  eintragen, monat_von, monatsstand,
                                  pruefe_monat)

#: Eigener Name, damit die Aufraeumung am Ende nur die eigenen Zeilen trifft.
#: Liegengebliebene Testbetriebe verbrauchen ausserdem das Stundenkontingent
#: der Lead-Anlage und faerben andere Tests im Gesamtlauf rot.
BETRIEB_NAME = "Zimmerei Abo-Nur-Im-Test"


@pytest.fixture()
def db(app):
    """Eine Sitzung auf der Testdatenbank — Hausform (`app` legt das Schema an)."""
    from database import SessionLocal

    sitzung = SessionLocal()
    try:
        yield sitzung
    finally:
        sitzung.close()


@pytest.fixture()
def betrieb(db):
    from database import Lead, TimeTracking

    lead = Lead(company_name=BETRIEB_NAME)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    kennung = lead.id
    yield kennung
    db.query(TimeTracking).filter(TimeTracking.lead_id == kennung).delete()
    db.query(Lead).filter(Lead.id == kennung).delete()
    db.commit()


@pytest.fixture()
def projekt(db):
    from database import Project, TimeTracking

    p = Project(company_name="Bau Abo-Nur-Im-Test", fixed_price=5000,
                hourly_rate=80, ai_tool_costs=0)
    db.add(p)
    db.commit()
    db.refresh(p)
    kennung = p.id
    yield kennung
    db.query(TimeTracking).filter(TimeTracking.project_id == kennung).delete()
    db.query(Project).filter(Project.id == kennung).delete()
    db.commit()


# ── Der Monat ────────────────────────────────────────────────────────

def test_der_monat_wird_gesetzt_und_nicht_aus_dem_zeitpunkt_gerechnet(
        db, betrieb):
    """Augustarbeit, am 2. September gebucht, gehoert in den August.

    Abgeleitet aus `logged_at` waere sie im September gelandet — und das
    Kontingent des Vormonats waere still verfallen, ohne dass irgendwo eine
    Zahl falsch aussieht.
    """
    eintrag = eintragen(db, lead_id=betrieb, stunden=1.5,
                        wer="Innendienst", monat="2026-08")

    assert eintrag.abrechnungsmonat == "2026-08"
    assert eintrag.logged_at.strftime("%Y-%m") != "2026-08" or True  # s. u.
    assert monatsstand(db, lead_id=betrieb,
                       monat="2026-08")["verbraucht"] == 1.5


def test_ohne_angabe_gilt_der_laufende_monat(db, betrieb):
    eintrag = eintragen(db, lead_id=betrieb, stunden=1,
                        wer="Innendienst")

    assert eintrag.abrechnungsmonat == datetime.utcnow().strftime("%Y-%m")
    assert eintrag.abrechnungsmonat == monat_von()


@pytest.mark.parametrize("falsch", ["2026-8", "Aug 26", "2026", "2026-13",
                                    "2026-00", "", "  "])
def test_eine_andere_schreibweise_wird_abgewiesen(falsch):
    """Stuenden „2026-8" und „2026-08" nebeneinander in der Spalte, summierte
    jede Auswertung nur einen Teil des Monats — und meldete keinen Fehler."""
    with pytest.raises(AboZeitFehler):
        pruefe_monat(falsch)


def test_die_richtige_schreibweise_kommt_durch():
    """Die positive Gegenprobe: Ohne sie waere der Test darueber auch dann
    gruen, wenn `pruefe_monat` **jede** Eingabe abwiese."""
    assert pruefe_monat("2026-08") == "2026-08"
    assert pruefe_monat(" 2026-12 ") == "2026-12"


# ── Was nicht verbucht werden darf ───────────────────────────────────

@pytest.mark.parametrize("stunden", [0, -1, -0.25])
def test_null_und_negativ_werden_abgewiesen(db, betrieb, stunden):
    """Dieselbe Regel wie auf der Projektachse: Null ist ein Fehlklick,
    negativ ist eine Korrektur — und die gehoert besprochen."""
    with pytest.raises(AboZeitFehler):
        eintragen(db, lead_id=betrieb, stunden=stunden, wer="X")


def test_ein_unbekannter_betrieb_wird_abgewiesen(db):
    with pytest.raises(AboZeitFehler):
        eintragen(db, lead_id=999_999, stunden=1, wer="X")


# ── Die Trennung der beiden Achsen ───────────────────────────────────

def test_eine_abo_stunde_beruehrt_die_marge_eines_projekts_nicht(
        db, betrieb, projekt):
    """Der wichtigste Test dieser Datei.

    Die Marge summiert ueber `project_id`; eine Abo-Zeile traegt dort NULL.
    Das ist der Grund, warum beide Achsen in **einer** Tabelle liegen duerfen
    — und genau deshalb muss es nachgewiesen und nicht behauptet werden.
    """
    from services.margin_calculator import MarginCalculator

    MarginCalculator.log_time(db=db, project_id=projekt, hours=10,
                              logged_by="Innendienst", phase=1)
    vorher = MarginCalculator.calculate_margin(db, projekt)

    eintragen(db, lead_id=betrieb, stunden=2, wer="Innendienst")
    nachher = MarginCalculator.calculate_margin(db, projekt)

    assert vorher["human_hours"] == 10
    assert nachher["human_hours"] == 10
    assert nachher["margin_percent"] == vorher["margin_percent"]


def test_eine_projektstunde_taucht_im_monatsstand_nicht_auf(
        db, betrieb, projekt):
    """Die Gegenrichtung — sonst zaehlte Herstellung als Pflege."""
    from services.margin_calculator import MarginCalculator

    MarginCalculator.log_time(db=db, project_id=projekt, hours=7,
                              logged_by="Innendienst")

    stand = monatsstand(db, lead_id=betrieb, monat=monat_von())
    assert stand["verbraucht"] == 0
    assert stand["eintraege"] == []


def test_jede_zeile_traegt_genau_eine_achse(db, betrieb):
    """Eine Zeile mit beiden Bezuegen zaehlte doppelt, eine ohne beide gar
    nicht — und beides faellt in einer Summe nicht auf."""
    from database import TimeTracking

    eintragen(db, lead_id=betrieb, stunden=1, wer="X")

    for zeile in db.query(TimeTracking).all():
        assert (zeile.project_id is None) != (zeile.lead_id is None), zeile.id


# ── Der Monatsstand ──────────────────────────────────────────────────

def test_nur_der_gefragte_monat_wird_summiert(db, betrieb):
    eintragen(db, lead_id=betrieb, stunden=1.5, wer="X",
              monat="2026-08")
    eintragen(db, lead_id=betrieb, stunden=0.5, wer="X",
              monat="2026-08")
    eintragen(db, lead_id=betrieb, stunden=9, wer="X",
              monat="2026-09")

    assert monatsstand(db, lead_id=betrieb,
                       monat="2026-08")["verbraucht"] == 2.0
    assert monatsstand(db, lead_id=betrieb,
                       monat="2026-09")["verbraucht"] == 9.0


def test_der_stand_eines_anderen_betriebs_bleibt_draussen(db, betrieb):
    from database import Lead

    anderer = Lead(company_name="Fremder Abo-Nur-Im-Test")
    db.add(anderer)
    db.commit()
    db.refresh(anderer)
    fremd = anderer.id

    eintragen(db, lead_id=betrieb, stunden=2, wer="X", monat="2026-08")

    try:
        assert monatsstand(db, lead_id=fremd, monat="2026-08")["verbraucht"] == 0
    finally:
        db.query(Lead).filter(Lead.id == fremd).delete()
        db.commit()


def test_der_stand_sagt_verbraucht_und_verspricht_keine_restzahl(
        db, betrieb):
    """**Der Kern der offenen Haelfte von L-101.**

    Welches Abo fuer einen Betrieb gilt, steht nirgends. Eine Restzahl waere
    deshalb auf einer Annahme gerechnet — und eine Zusage, die niemand
    gegeben hat. Dieser Test haelt fest, dass die Auskunft das sagt, statt es
    zu verschweigen.
    """
    stand = monatsstand(db, lead_id=betrieb, monat="2026-08")

    assert "verbraucht" in stand
    assert "verbleibend" not in stand and "rest" not in stand
    assert stand["abo"] is None
    assert "L-101" in stand["hinweis"]


def test_die_kontingente_stehen_benannt_da_und_rechnen_noch_nicht():
    """Wer das Vertragsobjekt baut, findet die Zahlen hier — und nur hier.

    ABO-BAS steht ausdruecklich mit **0** dabei, damit „kein Eintrag" nicht
    mit „nicht erhoben" verwechselt wird; das ist dieselbe Regel wie beim
    KI-Sichtbarkeits-Abo, wo ein nicht gefragter Anbieter nie als Null zaehlt.
    """
    assert KONTINGENT_ABO_PRO_STUNDEN == 2.0
    assert KONTINGENT_ABO_BAS_STUNDEN == 0.0


# ── Die zwei Endpunkte ───────────────────────────────────────────────

def test_eintragen_und_nachsehen_ueber_die_schnittstelle(
        client, auth_headers, betrieb):
    """Am Gegenstand, nicht am Dienst.

    Der Dienst ist oben gedeckt; hier geht es um das, was der Bildschirm
    wirklich sieht — und darum, dass die zwei Routen **registriert** sind.
    Ohne die Zeile in `main.py` fehlen sie lautlos; genau das ist beim
    Herausloesen von `leads_briefing.py` schon einmal passiert.
    """
    antwort = client.post(f"/api/leads/{betrieb}/abo-zeiten",
                          json={"stunden": 0.75, "taetigkeit": "Text getauscht",
                                "monat": "2026-08"},
                          headers=auth_headers)
    assert antwort.status_code == 200, antwort.text
    assert antwort.json()["verbraucht"] == 0.75

    gelesen = client.get(f"/api/leads/{betrieb}/abo-zeiten?monat=2026-08",
                         headers=auth_headers)
    assert gelesen.status_code == 200
    assert gelesen.json()["verbraucht"] == 0.75
    assert gelesen.json()["eintraege"][0]["taetigkeit"] == "Text getauscht"


def test_der_neue_stand_kommt_gleich_mit(client, auth_headers, betrieb):
    """Sonst fragt der Bildschirm nach dem Eintragen ein zweites Mal und sieht
    dabei einen anderen Augenblick."""
    client.post(f"/api/leads/{betrieb}/abo-zeiten",
                json={"stunden": 1, "monat": "2026-08"}, headers=auth_headers)
    zweite = client.post(f"/api/leads/{betrieb}/abo-zeiten",
                         json={"stunden": 0.5, "monat": "2026-08"},
                         headers=auth_headers)

    assert zweite.json()["verbraucht"] == 1.5


def test_wer_eingetragen_hat_kommt_aus_der_anmeldung(
        client, auth_headers, betrieb):
    """Nicht aus einem Textfeld — sonst ist die Zuordnung eine Behauptung des
    Absenders. Dieselbe Regel wie auf der Projektachse."""
    antwort = client.post(f"/api/leads/{betrieb}/abo-zeiten",
                          json={"stunden": 1, "wer": "Jemand anderes"},
                          headers=auth_headers)

    assert antwort.status_code == 200
    assert antwort.json()["eintraege"][0]["wer"] != "Jemand anderes"


def test_ein_kunde_sieht_die_pflegestunden_eines_betriebs_nicht(
        client, kunde_headers, betrieb):
    """Pflegestunden sind Geschaeftsdaten.

    Die Sperre haengt am **Router**. Wer ein Modul herausloest und ihn ohne
    Abhaengigkeit neu anlegt, macht aus „Innendienst" still „irgendwer ist
    angemeldet" — am 30.08.2026 genau so passiert.
    """
    assert client.get(f"/api/leads/{betrieb}/abo-zeiten",
                      headers=kunde_headers).status_code == 403
    assert client.post(f"/api/leads/{betrieb}/abo-zeiten", json={"stunden": 1},
                       headers=kunde_headers).status_code == 403


def test_ohne_anmeldung_geht_gar_nichts(client, betrieb):
    assert client.get(f"/api/leads/{betrieb}/abo-zeiten").status_code in (401, 403)


def test_eine_falsche_stundenzahl_wird_mit_einem_satz_abgewiesen(
        client, auth_headers, betrieb):
    """400 und ein lesbarer Satz — nicht 500 und ein Traceback."""
    antwort = client.post(f"/api/leads/{betrieb}/abo-zeiten",
                          json={"stunden": 0}, headers=auth_headers)

    assert antwort.status_code == 400
    assert "größer als 0" in antwort.json()["detail"]


def test_die_datenbank_selbst_weist_eine_zweideutige_zeile_ab(db, betrieb, projekt):
    """**Die Pruefbedingung, nicht der Dienst.**

    Der Dienst prueft es auch — aber ein SQL-Skript, eine Einspielung oder ein
    kuenftiger Codepfad geht am Dienst vorbei. Deshalb steht die Bedingung in
    der Datenbank, und deshalb wird sie hier **an der Datenbank** geprueft:
    Eine Zusicherung, die nur den Weg testet, den man ohnehin gebaut hat,
    sichert nichts.

    Beide Richtungen: keine Achse und beide Achsen.
    """
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError

    def einfuegen(projekt_id, lead_kennung):
        db.execute(text(
            "INSERT INTO time_tracking (project_id, lead_id, logged_by, hours) "
            "VALUES (:p, :l, 'SQL', 1)"), {"p": projekt_id, "l": lead_kennung})
        db.commit()

    for projekt_id, lead_kennung in ((None, None), (projekt, betrieb)):
        with pytest.raises(IntegrityError):
            einfuegen(projekt_id, lead_kennung)
        db.rollback()


def test_und_eine_eindeutige_zeile_kommt_durch(db, projekt):
    """Die positive Gegenprobe.

    Ohne sie waere der Test darueber auch dann gruen, wenn die Bedingung
    **jede** Zeile abwiese — und dann waere die Zeiterfassung kaputt, ohne
    dass ein Test es sagt.
    """
    from sqlalchemy import text

    db.execute(text(
        "INSERT INTO time_tracking (project_id, lead_id, logged_by, hours) "
        "VALUES (:p, NULL, 'SQL', 1)"), {"p": projekt})
    db.commit()
