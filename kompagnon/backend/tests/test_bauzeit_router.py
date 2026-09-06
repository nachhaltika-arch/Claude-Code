# -*- coding: utf-8 -*-
"""Der Weg, auf dem eine Vorlage in die Akte kommt (L-166, K3).

**Warum es diesen Weg überhaupt gibt.** Die Ruhezeit, die der Angebotsfuß
zusagt, entsteht aus der Spanne zwischen Vorlage und Freigabe. Die Freigabe
trägt der Kunde ein (`POST /api/portal/mitwirkung/M7`); die **Vorlage** kann
nur von uns kommen — wir legen den Bauplan vor, nicht er.

**Und warum er einen Knopf hat.** Ein Endpunkt ohne Aufrufer ist die
häufigste Fehlerklasse dieses Projekts: sechsmal allein zwischen dem 4. und
6. September. Ein Vorlagedatum, das niemand eintragen kann, wäre eine leere
Spalte mit einer schönen Rechnung dahinter.
"""
from datetime import date, datetime

import pytest


@pytest.fixture
def projekt(app, kunde_user):
    from database import SessionLocal, Project, MitwirkungStand

    db = SessionLocal()
    try:
        p = db.query(Project).filter(Project.lead_id == kunde_user.lead_id).first()
        if not p:
            p = Project(lead_id=kunde_user.lead_id, status="phase_1")
            db.add(p); db.commit(); db.refresh(p)
        db.query(MitwirkungStand).filter_by(project_id=p.id).delete()
        db.commit()
        return p.id
    finally:
        db.close()


def test_der_innendienst_traegt_die_vorlage_ein(client, mitarbeiter_headers,
                                                kunde_user, projekt):
    antwort = client.post(f"/api/bauzeit/{kunde_user.lead_id}/vorlage/M7",
                          json={}, headers=mitarbeiter_headers)

    assert antwort.status_code == 200
    d = antwort.json()
    assert d["kennung"] == "M7"
    assert d["vorgelegt_am"]
    assert d["frist_bis"], "die Fünf-Werktage-Frist gehört in die Antwort"


def test_nur_die_beiden_freigaben_koennen_vorgelegt_werden(
        client, mitarbeiter_headers, kunde_user, projekt):
    """**M3 legt niemand vor.** „Logo und Bilder" liefert der Kunde; ein
    Vorlagedatum daran wäre eine Ruhezeit für etwas, das nie gestockt hat."""
    antwort = client.post(f"/api/bauzeit/{kunde_user.lead_id}/vorlage/M3",
                          json={}, headers=mitarbeiter_headers)

    assert antwort.status_code == 400


def test_die_zweite_vorlage_verschiebt_den_zeitpunkt_nicht(
        client, mitarbeiter_headers, kunde_user, projekt):
    """Sonst könnte ein zweiter Klick die Frist des Kunden verlängern —
    zu unseren Gunsten und ohne dass es jemand sieht."""
    erst = client.post(f"/api/bauzeit/{kunde_user.lead_id}/vorlage/M7",
                       json={}, headers=mitarbeiter_headers).json()
    nochmal = client.post(f"/api/bauzeit/{kunde_user.lead_id}/vorlage/M7",
                          json={}, headers=mitarbeiter_headers).json()

    assert erst["vorgelegt_am"] == nochmal["vorgelegt_am"]


def test_ein_kunde_kommt_an_die_vorlage_nicht_heran(client, kunde_headers,
                                                    kunde_user, projekt):
    """Wer seine eigene Vorlage datieren könnte, könnte sich die Ruhezeit
    wegrechnen, die er selbst verursacht hat."""
    antwort = client.post(f"/api/bauzeit/{kunde_user.lead_id}/vorlage/M7",
                          json={}, headers=kunde_headers)

    assert antwort.status_code in (401, 403)


def test_der_innendienst_sieht_denselben_stand_wie_der_kunde(
        client, mitarbeiter_headers, kunde_headers, kunde_user, projekt):
    """**Zwei Ableitungen desselben Datums sind zwei, die auseinanderlaufen
    können.** Im Streit über eine zugesagte Frist ist das genau der Fall, der
    nicht eintreten darf."""
    client.post(f"/api/bauzeit/{kunde_user.lead_id}/vorlage/M8", json={},
                headers=mitarbeiter_headers)

    innen = client.get(f"/api/bauzeit/{kunde_user.lead_id}",
                       headers=mitarbeiter_headers).json()
    aussen = client.get("/api/portal/mitwirkung", headers=kunde_headers).json()

    assert innen["frist"] == aussen["frist"]


def test_ohne_projekt_gibt_es_keine_frist_und_keinen_absturz(
        client, mitarbeiter_headers, fremder_betrieb):
    antwort = client.get(f"/api/bauzeit/{fremder_betrieb}",
                         headers=mitarbeiter_headers)

    assert antwort.status_code == 200
    assert antwort.json()["frist"] is None
