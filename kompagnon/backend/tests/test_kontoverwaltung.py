# -*- coding: utf-8 -*-
'''Die Kontoverwaltung im Kundenkonto (06.09.2026).

**Zwei Stellen tragen hier Verantwortung, und beide haben Tests:**

1. *Die Sperrliste.* „Gerät abmelden" muss den Token wirklich entwerten —
   sonst ist der Knopf eine Lüge. Und sie muss eine **Ausschluss**liste
   bleiben: Eine Zulassungsliste hätte beim Ausrollen jeden ausgeloggt,
   dessen Token vorher ausgegeben wurde.
2. *Die Pflichtnachrichten.* Eine Freigabeanfrage mit Fünf-Tage-Frist oder
   eine Rechnung darf nicht abwählbar sein. Wer die Anfrage nie gesehen hat,
   weil er sie abbestellen konnte, hat die Frist nicht versäumt.
'''
from datetime import datetime, timedelta

import pytest

from services import benachrichtigungswahl as bw
from services import geraete

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
def nutzer(db):
    from database import User
    from modelle_konten import BenachrichtigungsWahl, UserSession

    u = User(email="konto-nur-im-test@kompagnon.local", role="kunde",
             is_active=True, is_verified=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    try:
        yield u.id
    finally:
        db.query(UserSession).filter(UserSession.user_id == u.id).delete()
        db.query(BenachrichtigungsWahl).filter(
            BenachrichtigungsWahl.user_id == u.id).delete()
        db.query(User).filter(User.id == u.id).delete()
        db.commit()


# ── Der Token wird nie im Klartext abgelegt ──────────────────────────

def test_der_token_steht_nur_als_hash_in_der_tabelle(db, nutzer):
    """**Die wichtigste Zusicherung.** Wer die Datenbank liest, darf damit
    keine gültige Anmeldung in die Hand bekommen."""
    from modelle_konten import UserSession

    geheim = "ein.sehr.geheimer.jwt.wert"
    geraete.anmeldung_merken(db, user_id=nutzer, token=geheim,
                             ip="1.2.3.4", user_agent="Test")

    zeile = db.query(UserSession).filter(UserSession.user_id == nutzer).first()

    assert zeile is not None
    assert geheim not in (zeile.token or "")
    assert len(zeile.token) == 64      # SHA-256, hexadezimal


# ── Die Sperre ───────────────────────────────────────────────────────

def test_ein_unbekannter_token_gilt_weiter(db, nutzer):
    """**Der Grund für die Ausschlussliste.**

    Eine Zulassungsliste („nur Token mit Zeile gelten") hätte beim Ausrollen
    jeden ausgeloggt, dessen Token vor der Änderung ausgegeben wurde —
    Kunden wie Innendienst, ohne Vorwarnung.
    """
    assert geraete.ist_abgemeldet(db, "token.den.niemand.kennt") is False


def test_ein_abgemeldeter_token_ist_gesperrt(db, nutzer):
    """Sonst wäre der Knopf eine Lüge."""
    from modelle_konten import UserSession

    geraete.anmeldung_merken(db, user_id=nutzer, token="abc",
                             ip="1.2.3.4", user_agent="Test")
    zeile = db.query(UserSession).filter(UserSession.user_id == nutzer).first()

    geraete.abmelden(db, user_id=nutzer, sitzung_id=zeile.id)

    assert geraete.ist_abgemeldet(db, "abc") is True


def test_eine_fremde_sitzung_laesst_sich_nicht_abmelden(db, nutzer):
    """Sonst könnte jeder jeden ausloggen, der eine Nummer errät."""
    from modelle_konten import UserSession

    geraete.anmeldung_merken(db, user_id=nutzer, token="abc",
                             ip="1.2.3.4", user_agent="Test")
    fremde = db.query(UserSession).filter(UserSession.user_id == nutzer).first()

    with pytest.raises(geraete.NichtGefunden):
        geraete.abmelden(db, user_id=nutzer + 99_000, sitzung_id=fremde.id)


def test_abmelden_loescht_die_zeile_nicht(db, nutzer):
    """Gelöscht wäre „von wo war mein Konto offen?" nicht mehr beantwortbar —
    und genau das fragt, wer einen Missbrauch vermutet."""
    from modelle_konten import UserSession

    geraete.anmeldung_merken(db, user_id=nutzer, token="abc",
                             ip="1.2.3.4", user_agent="Test")
    zeile = db.query(UserSession).filter(UserSession.user_id == nutzer).first()

    geraete.abmelden(db, user_id=nutzer, sitzung_id=zeile.id)

    assert db.query(UserSession).filter(UserSession.id == zeile.id).first() is not None


# ── Die Liste ────────────────────────────────────────────────────────

def test_die_liste_zeigt_den_token_nicht_und_kuerzt_die_adresse(db, nutzer):
    """Das letzte Glied der Adresse sagt einem Nutzer nichts und ist ein
    personenbezogenes Datum mehr, als die Auskunft braucht."""
    geraete.anmeldung_merken(db, user_id=nutzer, token="sehr.geheim",
                             ip="82.165.44.201", user_agent="Mozilla/5.0 (iPhone)")

    eintrag = geraete.liste(db, nutzer, aktueller_token="sehr.geheim")[0]

    assert "geheim" not in repr(eintrag)
    assert eintrag["netz"] == "82.165.44.x"
    assert eintrag["dieses_geraet"] is True
    assert "iPhone" in eintrag["geraet"]


def test_ein_anderes_geraet_ist_nicht_dieses(db, nutzer):
    geraete.anmeldung_merken(db, user_id=nutzer, token="woanders",
                             ip="1.2.3.4", user_agent="Test")

    eintrag = geraete.liste(db, nutzer, aktueller_token="hier")[0]

    assert eintrag["dieses_geraet"] is False


# ── Benachrichtigungen ───────────────────────────────────────────────

def test_ohne_einstellung_bekommt_der_kunde_alles(db, nutzer):
    """Sonst verschwände mit dieser Änderung stillschweigend Post."""
    assert all(a["an"] for a in bw.stand(db, nutzer))


def test_pflichtnachrichten_lassen_sich_nicht_abwaehlen(db, nutzer):
    """**Der Kern.** An der Freigabeanfrage hängt eine Frist von fünf
    Werktagen. Wer sie abbestellen könnte, hätte sie nicht versäumt — und
    dann steht Aussage gegen Aussage."""
    for schluessel in ("freigaben", "rechnungen", "konto"):
        with pytest.raises(bw.NichtAbwaehlbar):
            bw.setze(db, user_id=nutzer, schluessel=schluessel, an=False)


def test_jede_pflichtnachricht_sagt_warum(db, nutzer):
    """Eine gesperrte Auswahl ohne Begründung liest sich als Gängelung."""
    for art in bw.KATALOG:
        if not art.abwaehlbar:
            assert art.warum_pflicht, f"{art.schluessel} ohne Begründung"


def test_eine_abgewaehlte_nachricht_wirkt_auch_beim_versand(db, nutzer):
    """**Ein Schalter, den niemand fragt, ist eine Attrappe.**

    `moechte()` ist die Stelle, an der die Einstellung Wirkung bekommt.
    """
    assert bw.moechte(db, nutzer, "leistungsbericht") is True

    bw.setze(db, user_id=nutzer, schluessel="leistungsbericht", an=False)

    assert bw.moechte(db, nutzer, "leistungsbericht") is False
    # Pflichtnachrichten bleiben wahr, egal was in der Tabelle steht.
    assert bw.moechte(db, nutzer, "rechnungen") is True


def test_eine_unbekannte_art_wird_abgewiesen(db, nutzer):
    with pytest.raises(ValueError):
        bw.setze(db, user_id=nutzer, schluessel="erfunden", an=False)


def test_zweimal_setzen_ergibt_eine_zeile(db, nutzer):
    """Sonst stünde dieselbe Wahl mehrfach da und die letzte gewänne zufällig."""
    from modelle_konten import BenachrichtigungsWahl

    bw.setze(db, user_id=nutzer, schluessel="akademie", an=False)
    bw.setze(db, user_id=nutzer, schluessel="akademie", an=True)

    zeilen = (db.query(BenachrichtigungsWahl)
                .filter(BenachrichtigungsWahl.user_id == nutzer,
                        BenachrichtigungsWahl.schluessel == "akademie").all())

    assert len(zeilen) == 1
    assert bw.moechte(db, nutzer, "akademie") is True
