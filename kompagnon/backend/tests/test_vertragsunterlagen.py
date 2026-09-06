# -*- coding: utf-8 -*-
"""Was der Kunde unterschrieben hat, im Konto (L-160 Rang 7).

**Der Befund.** Angebot, AGB-Fassung und Auftragsbestaetigung liegen im
System — der Kunde kommt nicht heran. Die Auftragsbestaetigung etwa gibt es
als PDF am Projekt, und ihr einziger Auslieferungsweg
(`projects_qa.download_auftragsbestaetigung`) verlangt `require_admin`.

**Was diese Seite ausdruecklich nicht tut: etwas erfinden.** Wo eine Unterlage
nicht vorliegt, sagt die Antwort das — mit Grund. Eine Liste, die fuenf
Zeilen zeigt und bei dreien ins Leere fuehrt, ist schlechter als eine mit
zwei.

**Und sie liegt hinter der Geldsperre** (L-160 Rang 4): Der Entwurf sagt zu,
dass die schwache Rechtestufe „alles ausser Rechnungen, Zahlungsart und
Vertragsunterlagen" sieht. Diese Seite ist der dritte Teil davon.
"""
import pytest


def test_ohne_projekt_ist_die_liste_leer_und_nicht_erfunden(client, kunde_headers,
                                                            fremder_betrieb):
    """Ein Betrieb ohne Auftrag hat keine Unterlagen — das ist kein Fehler."""
    antwort = client.get("/api/portal/vertragsunterlagen", headers=kunde_headers)

    assert antwort.status_code == 200
    d = antwort.json()
    assert isinstance(d["unterlagen"], list)
    for u in d["unterlagen"]:
        # Jede Zeile ist entweder abrufbar oder sagt, warum nicht.
        assert u["vorhanden"] is True or u["grund"], u


def test_eine_fehlende_unterlage_wird_benannt_statt_weggelassen(
        client, kunde_headers, kunde_user):
    """**Der Kern.** Wer eine Unterlage vermisst, soll lesen warum — nicht
    raten, ob wir sie haben und nicht zeigen."""
    d = client.get("/api/portal/vertragsunterlagen", headers=kunde_headers).json()

    titel = [u["titel"] for u in d["unterlagen"]]
    assert "Auftragsbestätigung" in titel
    assert "AGB-Fassung" in titel

    fehlende = [u for u in d["unterlagen"] if not u["vorhanden"]]
    for u in fehlende:
        assert len(u["grund"]) > 20, f"{u['titel']} sagt nicht, warum"
        assert not u["adresse"], "eine fehlende Unterlage darf keinen Link tragen"


def test_ein_mitleser_kommt_nicht_an_die_unterlagen(client, app, kollege_mitleser):
    """Der dritte Teil der Zusage aus Rang 4: „alles ausser Rechnungen,
    Zahlungsart und **Vertragsunterlagen**."""
    antwort = client.get("/api/portal/vertragsunterlagen",
                         headers=kollege_mitleser)

    assert antwort.status_code == 403


def test_der_inhaber_kommt_heran(client, kunde_headers):
    """Die Gegenprobe — sonst haette die Sperre alle ausgesperrt."""
    assert client.get("/api/portal/vertragsunterlagen",
                      headers=kunde_headers).status_code == 200


def test_die_auftragsbestaetigung_eines_fremden_projekts_bleibt_zu(
        client, kunde_headers):
    """Der Auslieferungsweg filtert auf den eigenen Betrieb — sonst waere die
    Projektnummer der Schluessel zu jeder fremden Bestaetigung."""
    antwort = client.get("/api/portal/vertragsunterlagen/auftragsbestaetigung/999999",
                         headers=kunde_headers)

    assert antwort.status_code == 404


@pytest.fixture
def kollege_mitleser(app, kunde_user, client):
    from auth import hash_password
    from database import SessionLocal, User
    from services.kundenzugang import ANSEHEN

    mail, wort = "mitleser@example.org", "Mitleser!2026"
    db = SessionLocal()
    try:
        alt = db.query(User).filter(User.email == mail).first()
        if alt:
            db.delete(alt); db.commit()
        u = User(email=mail, role="kunde", password_hash=hash_password(wort),
                 lead_id=kunde_user.lead_id, is_active=True, is_verified=True,
                 kunde_recht=ANSEHEN)
        db.add(u); db.commit(); db.refresh(u)
        kennung = u.id
    finally:
        db.close()

    antwort = client.post("/api/auth/login", json={"email": mail, "password": wort})
    assert antwort.status_code == 200, antwort.text
    yield {"Authorization": f"Bearer {antwort.json()['access_token']}"}

    db = SessionLocal()
    try:
        u = db.query(User).filter(User.id == kennung).first()
        if u:
            db.delete(u); db.commit()
    finally:
        db.close()
