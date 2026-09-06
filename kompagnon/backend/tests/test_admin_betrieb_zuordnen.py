# -*- coding: utf-8 -*-
"""Benutzer mit einem Betrieb verbinden — im Innendienst (Wunsch David, 06.09.2026).

**Der Befund.** `users.lead_id` entscheidet ueber alles im Kundenkonto: welchen
Betrieb jemand sieht, welche Mitwirkung, welche Rechnungen. Ueber die
Admin-Oberflaeche liess sich das Feld **weder setzen noch aendern** —
`AdminCreateUser` und `AdminUpdateUser` kennen es nicht, und die Liste zeigt
den Betrieb nicht einmal an. Wer einen Zugang nachtraeglich einem Betrieb
zuordnen musste, brauchte einen Datenbankzugriff.

**Die Zuordnung ist folgenreich, deshalb wird sie geprueft.** Eine falsche
`lead_id` gibt jemandem Einblick in einen fremden Betrieb — dieselbe Klasse
wie ein Rechtefehler, nur stiller.
"""
import pytest


@pytest.fixture
def zweiter_betrieb(app):
    from database import Lead, SessionLocal

    db = SessionLocal()
    try:
        vorhanden = db.query(Lead).filter(Lead.email == "zweit@example.org").first()
        if vorhanden:
            return vorhanden.id
        lead = Lead(company_name="Zweitbetrieb GmbH", email="zweit@example.org")
        db.add(lead); db.commit(); db.refresh(lead)
        return lead.id
    finally:
        db.close()


@pytest.fixture
def frischer_nutzer(app):
    from database import SessionLocal, User

    mail = "zuordnung@example.org"
    db = SessionLocal()
    try:
        alt = db.query(User).filter(User.email == mail).first()
        if alt:
            db.delete(alt); db.commit()
        u = User(email=mail, role="kunde", is_active=True)
        db.add(u); db.commit(); db.refresh(u)
        kennung = u.id
    finally:
        db.close()
    yield kennung
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.id == kennung).first()
        if u:
            db.delete(u); db.commit()
    finally:
        db.close()


def test_die_liste_nennt_den_betrieb_mit_namen(client, auth_headers, kunde_user):
    """**Eine Kennung ist keine Auskunft.** `lead_id: 34` sagt niemandem, um
    welchen Betrieb es geht — der Name schon."""
    antwort = client.get("/api/admin/users", headers=auth_headers)

    assert antwort.status_code == 200
    treffer = [u for u in antwort.json() if u["id"] == kunde_user.id]
    assert treffer, "der Kunde steht nicht in der Liste"
    assert treffer[0]["lead_id"] == kunde_user.lead_id
    assert treffer[0].get("betrieb"), "der Name des Betriebs fehlt"


def test_ein_nutzer_laesst_sich_einem_betrieb_zuordnen(client, auth_headers,
                                                       frischer_nutzer,
                                                       zweiter_betrieb):
    antwort = client.patch(f"/api/admin/users/{frischer_nutzer}",
                           json={"lead_id": zweiter_betrieb},
                           headers=auth_headers)

    assert antwort.status_code == 200
    assert antwort.json()["lead_id"] == zweiter_betrieb
    assert antwort.json()["betrieb"] == "Zweitbetrieb GmbH"


def test_die_zuordnung_laesst_sich_auch_wieder_loesen(client, auth_headers,
                                                      frischer_nutzer,
                                                      zweiter_betrieb):
    """**Sonst waere ein Fehlgriff dauerhaft.** `null` loest sie — und das ist
    etwas anderes als „Feld nicht mitgeschickt", was nichts aendern darf."""
    client.patch(f"/api/admin/users/{frischer_nutzer}",
                 json={"lead_id": zweiter_betrieb}, headers=auth_headers)

    geloest = client.patch(f"/api/admin/users/{frischer_nutzer}",
                           json={"lead_id": None}, headers=auth_headers)

    assert geloest.status_code == 200
    assert geloest.json()["lead_id"] is None


def test_ein_feld_das_nicht_mitkommt_aendert_nichts(client, auth_headers,
                                                    frischer_nutzer,
                                                    zweiter_betrieb):
    """**Der Unterschied zwischen „nicht gesetzt" und „auf leer gesetzt".**
    Wer nur die Rolle aendert, darf nicht nebenbei die Betriebszuordnung
    verlieren."""
    client.patch(f"/api/admin/users/{frischer_nutzer}",
                 json={"lead_id": zweiter_betrieb}, headers=auth_headers)

    danach = client.patch(f"/api/admin/users/{frischer_nutzer}",
                          json={"position": "Buchhaltung"}, headers=auth_headers)

    assert danach.json()["lead_id"] == zweiter_betrieb


def test_ein_unbekannter_betrieb_wird_abgewiesen(client, auth_headers,
                                                 frischer_nutzer):
    """Eine Kennung, die es nicht gibt, waere ein Zugang ins Nichts — und
    faellt erst auf, wenn sich jemand anmeldet und eine leere Seite sieht."""
    antwort = client.patch(f"/api/admin/users/{frischer_nutzer}",
                           json={"lead_id": 999999}, headers=auth_headers)

    assert antwort.status_code == 400


def test_beim_anlegen_laesst_sich_der_betrieb_gleich_mitgeben(client, auth_headers,
                                                              zweiter_betrieb):
    from database import SessionLocal, User

    mail = "neu-mit-betrieb@example.org"
    try:
        antwort = client.post("/api/admin/users", headers=auth_headers,
                              json={"email": mail, "role": "kunde",
                                    "lead_id": zweiter_betrieb})
        assert antwort.status_code == 200
        assert antwort.json()["user"]["lead_id"] == zweiter_betrieb
    finally:
        db = SessionLocal()
        try:
            u = db.query(User).filter(User.email == mail).first()
            if u:
                db.delete(u); db.commit()
        finally:
            db.close()


def test_die_betriebsliste_steht_zur_auswahl_bereit(client, auth_headers):
    """**Ohne Liste keine Zuordnung.** Der Innendienst kennt die Kennung nicht
    auswendig; er sucht den Namen."""
    antwort = client.get("/api/admin/betriebe", headers=auth_headers)

    assert antwort.status_code == 200
    d = antwort.json()
    assert isinstance(d, list)
    if d:
        assert "id" in d[0] and "name" in d[0]
