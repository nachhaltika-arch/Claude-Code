# -*- coding: utf-8 -*-
"""Die allgemeine Suche im Werkzeug (Wunsch David, 06.09.2026).

**Der Befund.** Es gab **keine**. Wer einen Betrieb suchte, ging auf die
Betriebsliste und filterte dort; wer ein Projekt suchte, auf die Pipeline. Die
Frage „wo ist Firma Müller?" hatte je nach Gegenstand eine andere Antwort.

**Was sie durchsucht, und warum genau das.** Betriebe, Projekte und Zugänge —
die drei Dinge, die der Innendienst wirklich sucht. Audits und Tickets hängen
an einem Betrieb; wer ihn gefunden hat, ist da.

**Sie ist Innendienst.** Eine Volltextsuche ueber den Bestand ist das genaue
Gegenteil dessen, was ein Kundenkonto darf.
"""
import pytest


def test_ohne_anmeldung_gibt_es_keine_suche(client):
    assert client.get("/api/suche?q=test").status_code in (401, 403)


def test_ein_kunde_darf_den_bestand_nicht_durchsuchen(client, kunde_headers):
    """**Der wichtigste Test dieser Datei.** Eine Volltextsuche ueber alle
    Betriebe in der Hand eines Kunden waere ein Datenleck mit Suchfeld."""
    assert client.get("/api/suche?q=a", headers=kunde_headers).status_code == 403


def test_der_innendienst_findet_einen_betrieb_am_namen(client, mitarbeiter_headers,
                                                       kunde_user):
    antwort = client.get("/api/suche?q=Pytest", headers=mitarbeiter_headers)

    assert antwort.status_code == 200
    treffer = antwort.json()["treffer"]
    betriebe = [t for t in treffer if t["art"] == "betrieb"]
    assert betriebe, "der Testbetrieb wurde nicht gefunden"
    assert betriebe[0]["titel"]
    assert betriebe[0]["ziel"].startswith("/app/"), "ohne Ziel ist ein Treffer nutzlos"


def test_zu_kurze_eingaben_liefern_nichts(client, mitarbeiter_headers):
    """**Ein Buchstabe ist keine Suche, sondern ein Tastendruck.** Ohne
    Untergrenze liefe bei jedem Zeichen eine Abfrage ueber drei Tabellen."""
    d = client.get("/api/suche?q=a", headers=mitarbeiter_headers).json()

    assert d["treffer"] == []
    assert d["hinweis"], "der Nutzer soll lesen, warum nichts kommt"


def test_die_menge_ist_gedeckelt(client, mitarbeiter_headers):
    """Eine Suche, die alles herausgibt, ist ein Ausleseweg."""
    d = client.get("/api/suche?q=e", headers=mitarbeiter_headers).json()
    d2 = client.get("/api/suche?q=gmbh", headers=mitarbeiter_headers).json()

    assert len(d["treffer"]) <= 30
    assert len(d2["treffer"]) <= 30


def test_jeder_treffer_sagt_was_er_ist(client, mitarbeiter_headers, kunde_user):
    """Eine Liste aus Namen ohne Art laesst offen, ob „Müller" der Betrieb,
    das Projekt oder der Zugang ist."""
    d = client.get("/api/suche?q=Pytest", headers=mitarbeiter_headers).json()

    for t in d["treffer"]:
        assert t["art"] in ("betrieb", "projekt", "zugang")
        assert t["titel"] and t["ziel"]


def test_die_suche_gibt_keine_kennwoerter_heraus(client, mitarbeiter_headers,
                                                 kunde_user):
    roh = client.get("/api/suche?q=Pytest", headers=mitarbeiter_headers).text.lower()

    for verboten in ("password_hash", "totp_secret", "customer_token"):
        assert verboten not in roh
