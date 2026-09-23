# -*- coding: utf-8 -*-
"""Erst die Adresse der Website, dann — vielleicht — die eigene.

**Der Anlass (Entwurf David, 21.09.2026).** Das Formular fragte bisher alles
auf einmal: Website, E-Mail, Telefon, Haekchen. Der Entwurf dreht das um —
„Eine Adresse. Mehr braucht es nicht." Der Punktwert kommt sofort, die E-Mail
erst, wenn jemand den ausfuehrlichen Befund will.

**Was diese Datei festhaelt, ist die Verschiebung des Abschlusses.** Nicht die
Optik, sondern die drei Stellen, an denen sich dadurch die Bedeutung aendert:

* `POST /api/widget/audit` heisst jetzt **„Analyse gestartet"**, nicht „Lead".
  Er nimmt eine Anfrage ohne E-Mail an.
* Der Lead entsteht in `POST /api/widget/bericht-anfordern/{poll_token}` —
  dort greift die Adressgrenze, dort entsteht der Bestaetigungs-Token, und
  dort meldet der Serverweg an Meta.
* **Ohne Adresse geht keine Mail hinaus**, auch nicht wenn die Analyse fertig
  wird. Sonst ginge eine Bestaetigungsbitte an die leere Zeichenkette.

**Die Reihenfolge der beiden Ereignisse ist offen** — die Analyse kann fertig
sein, bevor jemand tippt, oder umgekehrt. Beide Wege muessen dieselbe Mail
ausloesen, und genau einmal.
"""
import pytest

from routers.widget import BerichtAnfrage, WidgetAuditRequest, _enforce_limits
from database import SessionLocal, WidgetRequest


# ── Schritt 1: die Analyse braucht keine Adresse mehr ─────────────────

def test_die_anfrage_darf_ohne_adresse_kommen():
    """Das Feld ist leer vorbelegt — sonst scheiterte schon das Einlesen."""
    nutzlast = WidgetAuditRequest(website_url="https://example.com")
    assert nutzlast.email == ""


def test_eine_falsche_adresse_bleibt_ein_fehler():
    """Leer heisst „noch nicht", nicht „egal"."""
    nutzlast = WidgetAuditRequest(website_url="https://example.com",
                                  email="kein-at-zeichen")
    assert nutzlast.email == "kein-at-zeichen"   # geprueft wird im Endpunkt


# ── Die Mengengrenzen: was ohne Adresse noch bremst ───────────────────

def test_ohne_adresse_greifen_die_ip_grenzen_weiter(monkeypatch):
    """**Die adressbezogene Bremse entfaellt, die anderen bleiben.**

    Ohne diese Zusicherung waere die Lockerung unsichtbar: Der Aufruf ginge
    durch, und niemand wuesste, ob noch irgendetwas zaehlt.
    """
    import routers.widget as w

    gezaehlt = []

    def falsches_zaehlen(db, seit, *bedingungen):
        gezaehlt.append(bedingungen)
        return 0

    monkeypatch.setattr(w, "_zaehle", falsches_zaehlen)
    _enforce_limits(None, "203.0.113.7", "")

    # Zwei IP-Abfragen (Stunde, Tag) und zwei Gesamtabfragen, keine ueber die
    # Adresse — die haette eine Bedingung mitgegeben.
    mit_bedingung = [b for b in gezaehlt if b]
    ohne_bedingung = [b for b in gezaehlt if not b]
    assert len(mit_bedingung) == 2, gezaehlt
    assert len(ohne_bedingung) == 2, gezaehlt


def test_mit_adresse_greift_die_adressgrenze_wieder(monkeypatch):
    import routers.widget as w

    gezaehlt = []
    monkeypatch.setattr(w, "_zaehle",
                        lambda db, seit, *b: gezaehlt.append(b) or 0)
    _enforce_limits(None, "203.0.113.7", "kunde@example.com")

    assert len([b for b in gezaehlt if b]) >= 3, gezaehlt


# ── Schritt 2: dort entsteht der Lead ─────────────────────────────────

def test_der_zweite_schritt_verlangt_eine_gueltige_adresse():
    nutzlast = BerichtAnfrage(email="kunde@example.com")
    assert nutzlast.email == "kunde@example.com"
    assert nutzlast.consent_marketing is False


def test_der_zweite_schritt_nimmt_die_klickkennungen_erneut_entgegen():
    """Sie stehen **nicht** an der Anfrage (L-192: nur das Ob, nie die
    Kennung) — also schickt das Widget sie mit, wenn es den Abschluss meldet.
    Ohne sie ordnet Meta die Meldung niemandem zu."""
    felder = set(BerichtAnfrage.model_fields)
    for name in ("fbclid", "fbc", "fbp", "consent_tracking", "page_url"):
        assert name in felder, f"{name} fehlt im zweiten Schritt"


def test_telefon_und_anrufwunsch_gehoeren_in_den_zweiten_schritt():
    """Im Entwurf steht das Telefonfeld am Ergebnis, nicht am Anfang."""
    felder = set(BerichtAnfrage.model_fields)
    assert "telefon" in felder and "anruf_gewuenscht" in felder


# ── Keine Post ohne Adresse ───────────────────────────────────────────

def test_die_fertige_analyse_schickt_ohne_adresse_keine_mail(monkeypatch):
    """**Der Fall, der ohne diese Sperre eine Mail an `''` ausloeste.**"""
    import routers.audit as a

    gesendet = []
    monkeypatch.setattr("services.email.send_email",
                        lambda *args, **kw: gesendet.append(args) or True)

    db = SessionLocal()
    try:
        row = WidgetRequest(email="", website_url="https://ohne-adresse.example",
                            audit_id=987654321, verify_token="v-ohne",
                            report_token="r-ohne", poll_token="p-ohne")
        db.add(row)
        db.commit()
        a._notify_widget_requester(db, 987654321)
        db.refresh(row)
        assert row.verify_sent_at is None
        assert not gesendet
    finally:
        db.query(WidgetRequest).filter(
            WidgetRequest.poll_token == "p-ohne").delete()
        db.commit()
        db.close()


def test_der_endpunkt_ist_eingehaengt():
    """Sonst waere alles oben richtig und von aussen nicht erreichbar —
    `gebaut_nicht_angeschlossen`."""
    from main import app

    pfade = app.openapi()["paths"]
    assert "/api/widget/bericht-anfordern/{poll_token}" in pfade
    assert "post" in pfade["/api/widget/bericht-anfordern/{poll_token}"]
