# -*- coding: utf-8 -*-
"""Ohne bestätigte Adresse keine Anmeldung — aber niemand wird eingesperrt.

**Entscheidung David, 27.08.2026:** „mach den riegel für unbestätigte konten
rein."

Damit wird `is_verified` von einer Auskunft zu einer Sperre. Das ist die
richtige Richtung — ein Feld, auf das sich nichts stützt, ist Dekoration.
Gefährlich ist daran nur eines: **Ein Riegel sperrt zuverlässig auch die
Falschen aus.** Diese Datei prüft deshalb weniger den Riegel als die vier
Wege, die er offen lassen muss.

**Wer heute `is_verified=False` trägt — nachgezählt, nicht geschätzt:**

1. **Selbstregistrierte Konten.** Für die ist der Riegel gedacht; sie
   bestätigen über den Link aus der Mail.
2. **Eingeladene Kollegen** (`routers/betriebszugaenge.py`, L-127). Sie
   entstehen ohne Passwort und ohne Bestätigung; erst der Einladungslink
   macht das Konto benutzbar. **Ohne die Regel unten wäre jeder eingeladene
   Kollege ab heute ausgesperrt** — ein Riegel, der eine zwei Tage alte
   Funktion abschaltet.
3. **Konten aus der Zeit davor.** Wie viele es davon gibt, lässt sich von
   hier aus nicht messen (die Produktivdatenbank ist nicht abfragbar).
   Deshalb hebt eine Migration mit **festem Stichtag** alles an, was vorher
   entstanden ist. Nach dem Stichtag greift der Riegel.

**Die Regel, die (2) rettet und zugleich richtig ist:** Wer einen Link aus
seinem Postfach einlöst, hat bewiesen, dass ihm das Postfach gehört. Genau
das prüft eine Bestätigungsmail. `POST /reset-password` setzt deshalb
`is_verified = True` — für die Einladung und für „Passwort vergessen"
gleichermaßen.

> Ein Riegel ohne Ersatzschlüssel ist keine Sicherheitsmaßnahme, sondern ein
> Ausfall mit Ankündigung. Deshalb `POST /resend-verification`.
"""
import inspect
import secrets
from datetime import datetime, timedelta

import pytest

from services import registrierungsschutz


def _adresse() -> str:
    return f"pytest-riegel-{secrets.token_hex(6)}@example.com"


PASSWORT = "pytest-pytest-pytest"


@pytest.fixture(autouse=True)
def ohne_drosselung():
    registrierungsschutz.zuruecksetzen()
    yield
    registrierungsschutz.zuruecksetzen()


@pytest.fixture()
def briefkasten(monkeypatch):
    from services import email as echt

    gesendet = []

    def doppel(to_email: str, subject: str, html_body: str,
               text_body: str = "", db=None, attachments=None) -> bool:
        gesendet.append({"an": to_email, "betreff": subject,
                         "inhalt": html_body})
        return True

    assert inspect.signature(doppel) == inspect.signature(echt.send_email)
    monkeypatch.setattr("services.email.send_email", doppel)
    return gesendet


def _aufraeumen(adresse: str) -> None:
    from database import SessionLocal, User

    db = SessionLocal()
    try:
        db.query(User).filter(User.email == adresse).delete()
        db.commit()
    finally:
        db.close()


def _konto(adresse: str):
    from database import SessionLocal, User

    db = SessionLocal()
    try:
        k = db.query(User).filter(User.email == adresse).first()
        db.expunge(k) if k else None
        return k
    finally:
        db.close()


def _setze(adresse: str, **felder) -> None:
    from database import SessionLocal, User

    db = SessionLocal()
    try:
        k = db.query(User).filter(User.email == adresse).first()
        for name, wert in felder.items():
            setattr(k, name, wert)
        db.commit()
    finally:
        db.close()


# ── Der Riegel selbst ─────────────────────────────────────────────────

def test_unbestaetigt_kommt_nicht_durch(client, briefkasten):
    adresse = _adresse()
    try:
        client.post("/api/auth/register", json={
            "email": adresse, "password": PASSWORT,
            "first_name": "Erika", "last_name": "Musterfrau"})

        antwort = client.post("/api/auth/login",
                              json={"email": adresse, "password": PASSWORT})

        assert antwort.status_code == 403, antwort.text[:300]
    finally:
        _aufraeumen(adresse)


def test_die_meldung_sagt_was_zu_tun_ist(client, briefkasten):
    """Ein 403 ohne Weg heraus ist eine Sackgasse mit Statuscode."""
    adresse = _adresse()
    try:
        client.post("/api/auth/register", json={
            "email": adresse, "password": PASSWORT,
            "first_name": "Erika", "last_name": "Musterfrau"})

        text = client.post("/api/auth/login",
                           json={"email": adresse,
                                 "password": PASSWORT}).json()["detail"].lower()

        assert "best" in text, text            # „bestaetigen"
        assert "postfach" in text or "mail" in text, text
    finally:
        _aufraeumen(adresse)


def test_nach_der_bestaetigung_kommt_er_durch(client, briefkasten):
    """Die positive Gegenprobe. Ohne sie wäre der Riegel auch dann „grün",
    wenn er **alle** aussperrte."""
    import re

    adresse = _adresse()
    try:
        client.post("/api/auth/register", json={
            "email": adresse, "password": PASSWORT,
            "first_name": "Erika", "last_name": "Musterfrau"})
        token = re.search(r"token=([A-Za-z0-9_\-]+)",
                          briefkasten[0]["inhalt"]).group(1)
        client.post(f"/api/auth/verify-email?token={token}")

        antwort = client.post("/api/auth/login",
                              json={"email": adresse, "password": PASSWORT})

        assert antwort.status_code == 200, antwort.text[:300]
        assert antwort.json()["access_token"]
    finally:
        _aufraeumen(adresse)


def test_ein_falsches_passwort_bleibt_ein_falsches_passwort(client, briefkasten):
    """Der Riegel darf nicht verraten, ob es die Adresse gibt.

    Stünde er **vor** der Passwortpruefung, unterschiede sich die Antwort auf
    eine unbekannte Adresse (401) von der auf eine bekannte, unbestaetigte
    (403) — und wer das ausnutzt, kann Adressen durchprobieren.
    """
    adresse = _adresse()
    try:
        client.post("/api/auth/register", json={
            "email": adresse, "password": PASSWORT,
            "first_name": "Erika", "last_name": "Musterfrau"})

        falsch = client.post("/api/auth/login",
                             json={"email": adresse, "password": "ganz-falsch-hier"})
        unbekannt = client.post("/api/auth/login",
                                json={"email": "gibt-es-nicht@example.com",
                                      "password": "ganz-falsch-hier"})

        assert falsch.status_code == 401
        assert unbekannt.status_code == 401
        assert falsch.json()["detail"] == unbekannt.json()["detail"]
    finally:
        _aufraeumen(adresse)


# ── Wen der Riegel nicht aussperren darf ──────────────────────────────

def test_wer_einen_link_aus_seinem_postfach_einloest_ist_bestaetigt(
        client, briefkasten):
    """**Der Weg, der die Einladung rettet (L-127).**

    Ein eingeladener Kollege entsteht ohne Passwort und mit
    `is_verified=False`. Er kommt ueber den Einladungslink herein — und wer
    einen Link aus seinem Postfach einloest, hat bewiesen, dass ihm das
    Postfach gehoert. Genau das prueft eine Bestaetigungsmail auch.
    """
    from auth import generate_reset_token
    from database import SessionLocal, User

    adresse = _adresse()
    token = generate_reset_token()
    db = SessionLocal()
    try:
        db.add(User(
            email=adresse, password_hash=None,
            first_name="Eingeladene", last_name="Kollegin",
            role="kunde", is_active=True, is_verified=False,
            password_reset_token=token,
            password_reset_expires=datetime.utcnow() + timedelta(days=7)))
        db.commit()
    finally:
        db.close()

    try:
        gesetzt = client.post("/api/auth/reset-password",
                              json={"token": token, "new_password": PASSWORT})
        assert gesetzt.status_code == 200, gesetzt.text[:300]

        # Und damit kommt sie herein — ohne je eine Bestaetigungsmail
        # gesehen zu haben.
        antwort = client.post("/api/auth/login",
                              json={"email": adresse, "password": PASSWORT})
        assert antwort.status_code == 200, antwort.text[:300]

        assert _konto(adresse).is_verified is True
    finally:
        _aufraeumen(adresse)


def test_vom_innendienst_angelegte_konten_sind_bestaetigt(client, auth_headers):
    """`POST /api/admin/users` setzt `is_verified=True` — hier festgehalten,
    damit es niemand beim Aufraeumen entfernt."""
    adresse = _adresse()
    try:
        antwort = client.post("/api/admin/users", json={
            "email": adresse, "first_name": "Neuer", "last_name": "Kollege",
            "role": "mitarbeiter"}, headers=auth_headers)
        assert antwort.status_code == 200, antwort.text[:300]

        assert _konto(adresse).is_verified is True
    finally:
        _aufraeumen(adresse)


def test_der_stichtag_steht_fest_und_liegt_in_der_vergangenheit():
    """Die Migration hebt an, was **vor** dem Stichtag entstanden ist.

    Ein gleitender Stichtag („alles aelter als 30 Tage") wuerde bei jedem
    Serverstart neue Konten mitnehmen — und der Riegel waere nach einem Monat
    lautlos wieder offen.
    """
    from services.rollen import RIEGEL_STICHTAG

    assert RIEGEL_STICHTAG == "2026-08-28"


def test_die_migration_hebt_nur_altbestand_an():
    """Am Text der Migration gemessen: Sie muss den Stichtag nennen.

    Ohne ihn wuerde `UPDATE users SET is_verified = true WHERE is_verified =
    false` bei **jedem** Start jede frische Registrierung freischalten — die
    Migration liefe dem Riegel hinterher und haette ihn abgeschafft.
    """
    import inspect

    import migrations_runtime
    from services.rollen import RIEGEL_STICHTAG

    quelle = inspect.getsource(migrations_runtime.run_migrations)
    zeilen = [z for z in quelle.splitlines()
              if "is_verified" in z and "UPDATE users" in z.replace("'", "")]
    assert zeilen, "Keine Migration fuer den Altbestand gefunden"
    zusammen = quelle[quelle.index("is_verified") - 400:]
    assert RIEGEL_STICHTAG in zusammen, (
        "Die Migration nennt den Stichtag nicht — sie wuerde jede neue "
        "Registrierung freischalten")


# ── Der Ersatzschlüssel ───────────────────────────────────────────────

def test_die_bestaetigungsmail_laesst_sich_erneut_anfordern(client, briefkasten):
    adresse = _adresse()
    try:
        client.post("/api/auth/register", json={
            "email": adresse, "password": PASSWORT,
            "first_name": "Erika", "last_name": "Musterfrau"})
        briefkasten.clear()

        antwort = client.post("/api/auth/resend-verification",
                              json={"email": adresse})

        assert antwort.status_code == 200, antwort.text[:300]
        assert len(briefkasten) == 1
        assert briefkasten[0]["an"] == adresse
    finally:
        _aufraeumen(adresse)


def test_das_erneute_anfordern_verraet_keine_adressen(client, briefkasten):
    """Gleiche Antwort für „gibt es nicht", „schon bestätigt" und „gesendet".

    Sonst ist der Endpunkt ein Verzeichnis: Wer eine Adresse durchprobiert,
    liest an der Antwort ab, ob sie bei uns liegt.
    """
    adresse = _adresse()
    try:
        client.post("/api/auth/register", json={
            "email": adresse, "password": PASSWORT,
            "first_name": "Erika", "last_name": "Musterfrau"})
        _setze(adresse, is_verified=True)
        briefkasten.clear()

        unbekannt = client.post("/api/auth/resend-verification",
                                json={"email": "gibt-es-nicht@example.com"})
        bestaetigt = client.post("/api/auth/resend-verification",
                                 json={"email": adresse})

        assert unbekannt.status_code == bestaetigt.status_code == 200
        assert unbekannt.json() == bestaetigt.json()
        # Und in keinem der beiden Faelle geht etwas hinaus.
        assert briefkasten == []
    finally:
        _aufraeumen(adresse)


def test_auch_das_erneute_anfordern_ist_gedrosselt(client, briefkasten):
    """Sonst ist es ein Knopf, mit dem jeder ein fremdes Postfach flutet."""
    adresse = _adresse()
    try:
        client.post("/api/auth/register", json={
            "email": adresse, "password": PASSWORT,
            "first_name": "Erika", "last_name": "Musterfrau"})

        for _ in range(registrierungsschutz.HOECHSTENS):
            client.post("/api/auth/resend-verification", json={"email": adresse})

        zuviel = client.post("/api/auth/resend-verification",
                             json={"email": adresse})
        assert zuviel.status_code == 429, zuviel.text[:200]
    finally:
        _aufraeumen(adresse)
