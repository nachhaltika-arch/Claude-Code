# -*- coding: utf-8 -*-
"""Die Frist eines konkreten Projekts — aus Ständen, nicht aus Annahmen (L-166).

`services/bauzeit.py` rechnet mit Daten. Hier kommen die Daten aus der
Datenbank: Wann welcher Mitwirkungspunkt einging, wann wir die beiden
Freigaben vorgelegt haben, und wie viele Werktage Bauzeit das gekaufte Paket
zusagt.

**Warum das eine eigene Stelle ist.** Dieselbe Ableitung wird im Kundenkonto
und im Innendienst gebraucht. Zwei Ableitungen desselben Datums sind zwei, die
auseinanderlaufen können — und bei einer zugesagten Frist ist das der
Unterschied zwischen einem Nachweis und einem Streit.
"""
from datetime import date, datetime

import pytest

from services import bauzeit, bauzeit_projekt


@pytest.fixture
def projekt(app, kunde_user):
    """Ein leeres Projekt am Betrieb des Kunden."""
    from database import SessionLocal, Project, MitwirkungStand

    db = SessionLocal()
    try:
        p = (db.query(Project).filter(Project.lead_id == kunde_user.lead_id).first())
        if not p:
            p = Project(lead_id=kunde_user.lead_id, status="phase_1")
            db.add(p); db.commit(); db.refresh(p)
        db.query(MitwirkungStand).filter_by(project_id=p.id).delete()
        db.commit()
        return p.id
    finally:
        db.close()


def _setze(projekt_id, kennung, erledigt_am=None, vorgelegt_am=None):
    from database import SessionLocal, MitwirkungStand

    db = SessionLocal()
    try:
        stand = (db.query(MitwirkungStand)
                 .filter_by(project_id=projekt_id, kennung=kennung).first())
        if not stand:
            stand = MitwirkungStand(project_id=projekt_id, kennung=kennung)
            db.add(stand)
        stand.erledigt_am = erledigt_am
        stand.vorgelegt_am = vorgelegt_am
        db.commit()
    finally:
        db.close()


def _projekt(projekt_id):
    from database import SessionLocal, Project

    db = SessionLocal()
    try:
        return db, db.query(Project).filter(Project.id == projekt_id).first()
    except Exception:
        db.close()
        raise


def test_ohne_vollstaendige_mitwirkung_gibt_es_kein_bauzeitende(projekt):
    """**Kein geratenes Datum.** Solange etwas fehlt, läuft keine Frist — und
    ein angezeigtes Ende wäre eine Zusage, die niemand gegeben hat."""
    _setze(projekt, "M1", erledigt_am=datetime(2026, 9, 1, 10, 0))

    db, p = _projekt(projekt)
    try:
        stand = bauzeit_projekt.frist_stand(db, p)
    finally:
        db.close()

    assert stand["beginn"] is None
    assert stand["ende"] is None
    assert stand["offene_punkte"], "welche fehlen, gehört dazu"


def test_liegen_alle_punkte_vor_beginnt_die_frist_am_letzten_eingang(projekt):
    from services import mitwirkung as kat

    db, p = _projekt(projekt)
    try:
        punkte = [x.kennung for x in kat.gilt_fuer(set())
                  if x.wirkung == kat.FRISTBEGINN]
    finally:
        db.close()
    for i, k in enumerate(punkte):
        _setze(projekt, k, erledigt_am=datetime(2026, 9, 1 + i, 9, 0))

    db, p = _projekt(projekt)
    try:
        stand = bauzeit_projekt.frist_stand(db, p, heute=date(2026, 9, 20))
    finally:
        db.close()

    assert stand["beginn"] == bauzeit.naechster_werktag(
        date(2026, 9, len(punkte))).isoformat()
    assert stand["ende"], "mit vollständiger Mitwirkung ist das Ende berechenbar"
    assert stand["pause_werktage"] == 0


def test_eine_verspaetete_freigabe_schiebt_das_ende_nach_hinten(projekt):
    """Der Kern von K3: Vorlage am 07.09., Frist bis 14.09., freigegeben am
    17.09. — drei Werktage Ruhezeit, drei Werktage später fertig."""
    from services import mitwirkung as kat

    for k in [x.kennung for x in kat.gilt_fuer(set()) if x.wirkung == kat.FRISTBEGINN]:
        _setze(projekt, k, erledigt_am=datetime(2026, 9, 1, 9, 0))

    db, p = _projekt(projekt)
    try:
        ohne = bauzeit_projekt.frist_stand(db, p, heute=date(2026, 9, 20))
    finally:
        db.close()

    _setze(projekt, "M7", vorgelegt_am=datetime(2026, 9, 7, 9, 0),
           erledigt_am=datetime(2026, 9, 17, 15, 0))

    db, p = _projekt(projekt)
    try:
        mit = bauzeit_projekt.frist_stand(db, p, heute=date(2026, 9, 20))
    finally:
        db.close()

    assert mit["pause_werktage"] == 3
    assert mit["ende"] > ohne["ende"], "die Ruhezeit muss das Ende verschieben"
    m7 = next(f for f in mit["freigaben"] if f["kennung"] == "M7")
    assert m7["frist_bis"] == "2026-09-14"
    assert m7["werktage"] == 3
    assert m7["laeuft_noch"] is False


def test_eine_offene_vorlage_waechst_bis_heute(projekt):
    """Solange niemand freigibt, wächst die Ruhezeit — sonst zeigte das Konto
    ein Ende, das mit jedem Tag falscher wird und trotzdem gleich bleibt."""
    from services import mitwirkung as kat

    for k in [x.kennung for x in kat.gilt_fuer(set()) if x.wirkung == kat.FRISTBEGINN]:
        _setze(projekt, k, erledigt_am=datetime(2026, 9, 1, 9, 0))
    _setze(projekt, "M8", vorgelegt_am=datetime(2026, 9, 7, 9, 0))

    db, p = _projekt(projekt)
    try:
        stand = bauzeit_projekt.frist_stand(db, p, heute=date(2026, 9, 17))
    finally:
        db.close()

    m8 = next(f for f in stand["freigaben"] if f["kennung"] == "M8")
    assert m8["laeuft_noch"] is True
    assert m8["werktage"] == 3


def test_die_bauzeit_kommt_aus_dem_gekauften_paket(projekt):
    """Websprint Start und Websprint Neubau haben nicht dieselbe Bauzeit. Eine
    fest verdrahtete Zahl gäbe dem einen Kunden die Frist des anderen."""
    db, p = _projekt(projekt)
    try:
        werktage = bauzeit_projekt.bauzeit_werktage(db, p)
    finally:
        db.close()

    assert werktage >= 1


# ── Was beim Bauen auffiel und nicht gesucht war ──────────────────────

def test_ein_projekt_mit_mitwirkungsstaenden_laesst_sich_loeschen(projekt):
    """**Der Fund vom 06.09.2026.** `mitwirkung_stand` hing seit L-159
    (04.09.) ohne `ON DELETE CASCADE` an `projects`. Ein Projekt, zu dem auch
    nur ein Mitwirkungspunkt eingetragen war, ließ sich nicht mehr löschen —
    `ForeignKeyViolation`, und zwar überall, wo Projekte aufgeräumt werden.

    Aufgefallen ist es nicht durch Suchen, sondern weil diese Testdatei
    Stände hinterließ, die ein anderer Test wegräumen wollte. Dieselbe Klasse
    wie bei `UserSession` zwei Tage zuvor: Eine neue Tabelle bekommt einen
    Fremdschlüssel, und niemand fragt, was beim Löschen der Gegenseite
    passiert. Der Test hält es fest, damit die nächste Tabelle es nicht
    wiederholt.
    """
    from database import SessionLocal, MitwirkungStand, Project
    from datetime import datetime

    _setze(projekt, "M1", erledigt_am=datetime(2026, 9, 1, 10, 0))

    db = SessionLocal()
    try:
        db.query(Project).filter(Project.id == projekt).delete()
        db.commit()
        assert db.query(MitwirkungStand).filter_by(project_id=projekt).count() == 0, \
            "die Stände gehen mit dem Projekt — sie haben ohne es keinen Sinn"
    finally:
        db.close()
