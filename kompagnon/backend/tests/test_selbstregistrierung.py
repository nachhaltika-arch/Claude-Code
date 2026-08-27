# -*- coding: utf-8 -*-
"""Wer sich selbst registriert, bekommt auch eine Bestätigungsmail.

**Entscheidung David, 27.08.2026:** „ja ich möchte das sich kunden auch
öffentlich selbstregistrieren können." Die Registrierung bleibt also — und
muss dafür erst einmal funktionieren.

**Was beim Nachsehen herauskam.** `POST /api/auth/register` legte ein Konto
an, erzeugte einen `email_verify_token` und antwortete „Konto erstellt. Bitte
E-Mail bestaetigen." **Gesendet wurde nie etwas.** Der Token lag in der
Datenbank, und niemand bekam ihn je zu sehen.

Dazu drei weitere Dinge, die alle dieselbe Form haben:

1. `POST /api/auth/verify-email` hatte **keinen einzigen Aufrufer** — weder
   in der Oberfläche noch in den E2E-Tests.
2. Die Oberfläche sagte etwas **anderes** als das Backend: „Sie koennen sich
   jetzt anmelden" gegen „Bitte E-Mail bestaetigen". Beide Sätze standen
   nebeneinander, einer musste falsch sein.
3. Das Formular ist öffentlich und schrieb **ungedrosselt** Zeilen in die
   Datenbank.

> Ein Satz, der eine Handlung ankündigt, die nicht stattfindet, ist schlimmer
> als gar kein Satz: Er beendet die Suche. Wer „Bitte E-Mail bestätigen"
> liest, sucht im Spam-Ordner — nicht im Quelltext.
"""
import inspect
import secrets

import pytest

from services import registrierungsschutz


def _adresse() -> str:
    return f"pytest-selbst-{secrets.token_hex(6)}@example.com"


@pytest.fixture()
def briefkasten(monkeypatch):
    """Fängt den Versand ab — mit der echten Unterschrift von `send_email`."""
    from services import email as echt

    gesendet = []

    def doppel(to_email: str, subject: str, html_body: str,
               text_body: str = "", db=None, attachments=None) -> bool:
        gesendet.append({"an": to_email, "betreff": subject,
                         "inhalt": html_body, "text": text_body})
        return True

    assert inspect.signature(doppel) == inspect.signature(echt.send_email)
    monkeypatch.setattr("services.email.send_email", doppel)
    return gesendet


@pytest.fixture(autouse=True)
def ohne_drosselung():
    """Der Zähler ist prozessweit — sonst färben sich die Tests gegenseitig."""
    registrierungsschutz.zuruecksetzen()
    yield
    registrierungsschutz.zuruecksetzen()


def _aufraeumen(adresse: str) -> None:
    from database import SessionLocal, User

    db = SessionLocal()
    try:
        db.query(User).filter(User.email == adresse).delete()
        db.commit()
    finally:
        db.close()


# ── Die Mail, die nie kam ─────────────────────────────────────────────

def test_registrierung_verschickt_eine_bestaetigungsmail(client, briefkasten):
    adresse = _adresse()
    try:
        antwort = client.post("/api/auth/register", json={
            "email": adresse, "password": "pytest-pytest-pytest",
            "first_name": "Erika", "last_name": "Musterfrau"})
        assert antwort.status_code == 200, antwort.text[:300]

        assert len(briefkasten) == 1, f"{len(briefkasten)} Mails statt einer"
        assert briefkasten[0]["an"] == adresse
    finally:
        _aufraeumen(adresse)


def test_die_mail_traegt_den_token_aus_der_datenbank(client, briefkasten):
    """Nicht irgendeinen Link — **den**, der das Konto freischaltet."""
    from database import SessionLocal, User

    adresse = _adresse()
    try:
        client.post("/api/auth/register", json={
            "email": adresse, "password": "pytest-pytest-pytest",
            "first_name": "Erika", "last_name": "Musterfrau"})

        db = SessionLocal()
        try:
            token = db.query(User).filter(
                User.email == adresse).first().email_verify_token
        finally:
            db.close()

        assert token, "Kein Token am Konto"
        assert token in briefkasten[0]["inhalt"], "Der Token steht nicht im Link"
    finally:
        _aufraeumen(adresse)


def test_der_link_aus_der_mail_bestaetigt_das_konto(client, briefkasten):
    """Am Endpunkt gemessen: Der Weg aus der Mail führt wirklich irgendwohin."""
    import re

    from database import SessionLocal, User

    adresse = _adresse()
    try:
        client.post("/api/auth/register", json={
            "email": adresse, "password": "pytest-pytest-pytest",
            "first_name": "Erika", "last_name": "Musterfrau"})

        treffer = re.search(r"/e-mail-bestaetigen\?token=([A-Za-z0-9_\-]+)",
                            briefkasten[0]["inhalt"])
        assert treffer, briefkasten[0]["inhalt"][:400]

        bestaetigt = client.post(
            f"/api/auth/verify-email?token={treffer.group(1)}")
        assert bestaetigt.status_code == 200, bestaetigt.text[:300]

        db = SessionLocal()
        try:
            konto = db.query(User).filter(User.email == adresse).first()
            assert konto.is_verified is True
            assert konto.email_verify_token is None, (
                "Der Token gilt weiter — er ist ein Einmalschluessel")
        finally:
            db.close()
    finally:
        _aufraeumen(adresse)


def test_ein_zweiter_versuch_mit_demselben_token_scheitert(client, briefkasten):
    import re

    adresse = _adresse()
    try:
        client.post("/api/auth/register", json={
            "email": adresse, "password": "pytest-pytest-pytest",
            "first_name": "Erika", "last_name": "Musterfrau"})
        token = re.search(r"token=([A-Za-z0-9_\-]+)",
                          briefkasten[0]["inhalt"]).group(1)

        assert client.post(f"/api/auth/verify-email?token={token}").status_code == 200
        assert client.post(f"/api/auth/verify-email?token={token}").status_code == 400
    finally:
        _aufraeumen(adresse)


# ── Die Antwort sagt, was wirklich passiert ───────────────────────────

def test_die_antwort_kuendigt_keine_mail_an_die_ausbleibt(client, monkeypatch):
    """Scheitert der Versand, darf die Antwort nicht „prüfen Sie Ihr Postfach"
    sagen — sonst sucht der Mensch im Spam-Ordner statt sich zu melden."""
    monkeypatch.setattr("services.email.send_email",
                        lambda *a, **k: False)

    adresse = _adresse()
    try:
        antwort = client.post("/api/auth/register", json={
            "email": adresse, "password": "pytest-pytest-pytest",
            "first_name": "Erika", "last_name": "Musterfrau"})

        assert antwort.status_code == 200, antwort.text[:300]
        daten = antwort.json()
        # Das Konto entsteht trotzdem — es an einer Mail scheitern zu lassen
        # waere schlimmer.
        assert daten["user_id"]
        assert daten["mail_versandt"] is False
        assert "postfach" not in daten["message"].lower()
    finally:
        _aufraeumen(adresse)


def test_bei_erfolg_sagt_sie_es_auch(client, briefkasten):
    """Die Gegenprobe — sonst waere der Test oben auch grün, wenn die Antwort
    **nie** von einer Mail spräche."""
    adresse = _adresse()
    try:
        daten = client.post("/api/auth/register", json={
            "email": adresse, "password": "pytest-pytest-pytest",
            "first_name": "Erika", "last_name": "Musterfrau"}).json()

        assert daten["mail_versandt"] is True
        assert "postfach" in daten["message"].lower()
    finally:
        _aufraeumen(adresse)


# ── Die Drosselung ────────────────────────────────────────────────────

def test_nach_zu_vielen_versuchen_ist_schluss(client, briefkasten):
    """Ein öffentliches Formular, das Zeilen schreibt, braucht eine Grenze."""
    angelegt = []
    try:
        for _ in range(registrierungsschutz.HOECHSTENS):
            adresse = _adresse()
            angelegt.append(adresse)
            antwort = client.post("/api/auth/register", json={
                "email": adresse, "password": "pytest-pytest-pytest",
                "first_name": "Erika", "last_name": "Musterfrau"})
            assert antwort.status_code == 200, antwort.text[:200]

        adresse = _adresse()
        angelegt.append(adresse)
        zuviel = client.post("/api/auth/register", json={
            "email": adresse, "password": "pytest-pytest-pytest",
            "first_name": "Erika", "last_name": "Musterfrau"})

        assert zuviel.status_code == 429, zuviel.text[:200]
    finally:
        for a in angelegt:
            _aufraeumen(a)


def test_die_drosselung_zaehlt_je_herkunft_nicht_global(client, briefkasten):
    """Sonst sperrt ein einzelner Angreifer alle anderen mit aus.

    Das waere kein Schutz, sondern der Ausfall, den er herbeiführen wollte.
    """
    registrierungsschutz.zuruecksetzen()
    for _ in range(registrierungsschutz.HOECHSTENS):
        registrierungsschutz.vermerken("10.0.0.1")

    assert registrierungsschutz.zu_viele("10.0.0.1") is True
    assert registrierungsschutz.zu_viele("10.0.0.2") is False


def test_ohne_erkennbare_herkunft_wird_nicht_gesperrt():
    """Fehlt die Adresse, ist die Frage nicht beantwortbar — und eine
    unbeantwortbare Frage darf niemanden aussperren."""
    assert registrierungsschutz.zu_viele("") is False
    assert registrierungsschutz.zu_viele(None) is False
