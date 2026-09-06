# -*- coding: utf-8 -*-
"""Zugaenge fuer Kollegen — ein Betrieb ist keine Person (L-160 Rang 4, K7).

**Der Befund.** Ein Betrieb hat genau ein Konto, und wer einem Kollegen Zugang
geben will, gibt sein Kennwort weiter. Die Routen zum Anlegen von Konten gibt
es (`/api/admin/users`), aber sie verlangen `manage_users` — also Innendienst.
Heute muss David jeden Zugang von Hand einrichten.

**Die zwei Rechtestufen kommen aus dem Entwurf `kundenkonto-neu`:**

* `ansehen` — alles ausser Rechnungen, Zahlungsart und Vertragsunterlagen.
* `alles` — zusaetzlich freigeben, Aenderungen anfordern und Zugaenge verwalten.

**Warum die Sperre mitgebaut wird und nicht spaeter.** Eine Rechtestufe, die
nirgends wirkt, ist eine Zusage ohne Gegenstand — genau die Fehlerklasse, die
zwischen dem 4. und 6. September sechsmal vorkam. Wer `ansehen` waehlt und
sein Buchhalter sieht trotzdem die Kontodaten, hat schlechter dagestanden als
ohne die Wahl.
"""
import pytest


KOLLEGE_MAIL = "kollege@example.org"
KOLLEGE_WORT = "Kollege!2026"


@pytest.fixture
def kollege(app, kunde_user):
    """Ein zweites Konto am selben Betrieb, mit der schwachen Stufe.

    **Mit Kennwort**, obwohl eine frische Einladung keines hat: Der Test
    prueft, was ein **angemeldeter** Mitleser darf, und die Anmeldung laeuft
    ueber denselben Weg wie im Betrieb. Ein von Hand gebauter Token waere ein
    zweiter Anmeldeweg — und damit ein zweiter, der falsch sein kann.
    """
    from auth import hash_password
    from database import SessionLocal, User
    from services.kundenzugang import ANSEHEN

    db = SessionLocal()
    try:
        vorhanden = db.query(User).filter(User.email == KOLLEGE_MAIL).first()
        if vorhanden:
            db.delete(vorhanden); db.commit()
        u = User(email=KOLLEGE_MAIL, role="kunde",
                 password_hash=hash_password(KOLLEGE_WORT),
                 lead_id=kunde_user.lead_id, is_active=True, is_verified=True,
                 first_name="Sabine", last_name="Kraus",
                 kunde_recht=ANSEHEN)
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


def _anmelden(client, app, email, wort=KOLLEGE_WORT):
    """Anmelden wie im Betrieb — ueber `/api/auth/login`."""
    antwort = client.post("/api/auth/login", json={"email": email, "password": wort})
    assert antwort.status_code == 200, antwort.text
    return {"Authorization": f"Bearer {antwort.json()['access_token']}"}


# ── Die Stufen selbst ─────────────────────────────────────────────────

def test_wer_keine_stufe_traegt_darf_alles():
    """**Der Bestand darf nicht ausgesperrt werden.** Jedes heutige
    Kundenkonto ist das des Vertragsinhabers; eine leere Spalte muss `alles`
    bedeuten. Andersherum haette das Ausrollen jeden Kunden auf die schwache
    Stufe gesetzt, ohne dass es jemand merkt."""
    from services.kundenzugang import ALLES, stufe_von

    class Konto:
        kunde_recht = None

    assert stufe_von(Konto()) == ALLES
    assert stufe_von(None) == ALLES


def test_die_schwache_stufe_sieht_kein_geld():
    from services.kundenzugang import ANSEHEN, ALLES, darf_geld_sehen

    assert darf_geld_sehen(ANSEHEN) is False
    assert darf_geld_sehen(ALLES) is True


def test_nur_die_starke_stufe_verwaltet_zugaenge():
    """Sonst koennte ein Mitleser sich selbst hochstufen."""
    from services.kundenzugang import ANSEHEN, ALLES, darf_verwalten

    assert darf_verwalten(ANSEHEN) is False
    assert darf_verwalten(ALLES) is True


# ── Der Weg durch das Portal ──────────────────────────────────────────

def test_der_inhaber_sieht_die_zugaenge_seines_betriebs(client, kunde_headers,
                                                        kollege):
    antwort = client.get("/api/portal/zugaenge", headers=kunde_headers)

    assert antwort.status_code == 200
    d = antwort.json()
    adressen = [z["email"] for z in d["zugaenge"]]
    assert "kollege@example.org" in adressen
    assert d["darf_verwalten"] is True
    # **Kein Kennwort und kein Token in der Liste** — sie steht auf einem
    # Bildschirm, den mehrere Personen sehen.
    for z in d["zugaenge"]:
        assert "password_hash" not in z and "token" not in z


def test_ein_mitleser_darf_die_liste_sehen_aber_nicht_aendern(
        client, app, kunde_user, kollege):
    kopf = _anmelden(client, app, "kollege@example.org")

    lesen = client.get("/api/portal/zugaenge", headers=kopf)
    assert lesen.status_code == 200
    assert lesen.json()["darf_verwalten"] is False

    einladen = client.post("/api/portal/zugaenge", headers=kopf,
                           json={"email": "noch-einer@example.org",
                                 "recht": "alles"})
    assert einladen.status_code == 403, (
        "wer nur ansehen darf, koennte sich sonst selbst hochstufen")


def test_ein_mitleser_kommt_nicht_an_die_zahlungsdaten(client, app, kollege):
    """**Die Sperre, ohne die die Stufe eine Behauptung waere.** Der Entwurf
    sagt zu: „sieht alles ausser Rechnungen, Zahlungsart und
    Vertragsunterlagen." Steht die Zusage im Konto und wirkt nicht, ist sie
    schlimmer als keine."""
    kopf = _anmelden(client, app, "kollege@example.org")

    antwort = client.get("/api/portal/zahlungen", headers=kopf)

    assert antwort.status_code == 403


def test_der_inhaber_kommt_weiterhin_an_die_zahlungsdaten(client, kunde_headers):
    """Die Gegenprobe — sonst haette die Sperre alle ausgesperrt."""
    assert client.get("/api/portal/zahlungen",
                      headers=kunde_headers).status_code == 200


def test_eine_einladung_legt_ein_konto_am_selben_betrieb_an(
        client, kunde_headers, kunde_user):
    from database import SessionLocal, User

    antwort = client.post("/api/portal/zugaenge", headers=kunde_headers,
                          json={"email": "neu@example.org", "recht": "ansehen"})
    try:
        assert antwort.status_code == 200
        db = SessionLocal()
        try:
            neu = db.query(User).filter(User.email == "neu@example.org").first()
            assert neu is not None
            assert neu.lead_id == kunde_user.lead_id, "fremder Betrieb waere ein Leck"
            assert neu.role == "kunde"
            assert neu.kunde_recht == "ansehen"
            # **Ohne Kennwort angelegt.** Es entsteht ueber den
            # Zuruecksetzen-Weg, den es schon gibt — ein zweiter Weg,
            # Kennwoerter zu vergeben, waere ein zweiter, der falsch sein kann.
            assert not neu.password_hash
        finally:
            db.close()
    finally:
        db = SessionLocal()
        try:
            u = db.query(User).filter(User.email == "neu@example.org").first()
            if u:
                db.delete(u); db.commit()
        finally:
            db.close()


def test_niemand_laedt_sich_in_einen_fremden_betrieb_ein(client, kunde_headers,
                                                         fremder_betrieb):
    """Der Betrieb kommt aus der Anmeldung, nicht aus dem Aufruf."""
    antwort = client.post("/api/portal/zugaenge", headers=kunde_headers,
                          json={"email": "fremd@example.org", "recht": "alles",
                                "lead_id": fremder_betrieb})

    from database import SessionLocal, User
    db = SessionLocal()
    try:
        neu = db.query(User).filter(User.email == "fremd@example.org").first()
        if neu:
            assert neu.lead_id != fremder_betrieb
            db.delete(neu); db.commit()
    finally:
        db.close()
    assert antwort.status_code in (200, 400, 403)
