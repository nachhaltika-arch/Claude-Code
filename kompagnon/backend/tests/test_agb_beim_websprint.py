# -*- coding: utf-8 -*-
"""Welcher AGB-Fassung der Websprint-Kaeufer zugestimmt hat (L-181).

**Der Befund vom 06.09.2026.** `services/agb.py` nennt es „den Punkt, den fast
alle vergessen": Aendern sich die AGB, muss nachweisbar bleiben, **welche
Fassung** der Kaeufer akzeptiert hat — sonst belegt die Zustimmung nur, dass
jemand irgendwann irgendetwas angehakt hat. Der **Shop** macht das richtig
(`bestellungen.terms_version`). Beim **Websprint** ueber Stripe kamen `agb`
und `terms_version` **null Mal** vor. Das ist der teurere der beiden Wege: ein
Websprint kostet 3.500 bis 12.900 € netto, ein Buch 49 €.

**Die Fassung bestimmt der Server, nicht der Browser.** Sie wandert beim
Anlegen der Kassensitzung in die Stripe-Metadaten und kommt mit dem Rueckruf
zurueck. Kaeme sie aus dem Aufruf, koennte der Absender bestimmen, welcher
Fassung er zugestimmt haben will.

**Ohne hinterlegte Fassung wird nicht gesperrt, sondern vermerkt.** Der Shop
sperrt — dort ist es richtig, weil es dort AGB fuer digitale Produkte geben
muss. Beim Websprint wuerde dieselbe Sperre den Verkauf **sofort** anhalten,
und geschriebene AGB gibt es bis heute nicht (`inhalte/rechtstexte.js` fuehrt
neun Gliederungspunkte mit `ausstehend: true`). Erst messen und festhalten,
dann sperren — in dieser Reihenfolge.
"""
import pytest


def test_die_fassung_wandert_in_die_kassensitzung(monkeypatch):
    """Was beim Kauf galt, steht in den Metadaten — nicht das, was heute gilt."""
    from services import agb, zahlungsweg

    monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")

    merkmale = zahlungsweg.merkmale_mit_agb({"package": "websprint_neubau"})

    assert merkmale["agb_fassung"] == "2026-09-01"
    assert merkmale["package"] == "websprint_neubau", "die anderen bleiben"
    assert agb.fassung() == "2026-09-01"


def test_ohne_hinterlegte_fassung_steht_die_luecke_da(monkeypatch):
    """**Nicht raten und nicht erfinden.** Ein leeres Feld ist die ehrliche
    Antwort; eine erfundene Kennung waere ein Nachweis ueber nichts."""
    from services import zahlungsweg

    monkeypatch.delenv("AGB_FASSUNG", raising=False)

    merkmale = zahlungsweg.merkmale_mit_agb({"package": "websprint_neubau"})

    assert merkmale["agb_fassung"] == ""


def test_das_projekt_traegt_die_fassung_und_den_zeitpunkt(app):
    """Am Projekt, nicht am Betrieb: Der Auftrag ist der Vertrag."""
    from datetime import datetime

    from database import Project, SessionLocal

    db = SessionLocal()
    try:
        p = Project(status="phase_1", agb_fassung="2026-09-01",
                    agb_akzeptiert_am=datetime.utcnow())
        db.add(p); db.commit(); db.refresh(p)
        kennung = p.id
        assert p.agb_fassung == "2026-09-01"
        assert p.agb_akzeptiert_am is not None
    finally:
        db.close()

    db = SessionLocal()
    try:
        db.query(Project).filter(Project.id == kennung).delete()
        db.commit()
    finally:
        db.close()


def test_der_gesundheitsbericht_nennt_die_fehlende_fassung(client, monkeypatch):
    """**Sichtbar statt gesperrt.** Solange keine AGB hinterlegt sind, soll das
    an derselben Stelle stehen wie die Stripe-Schluessel — sonst faellt es
    beim ersten Streit auf, nicht vorher."""
    monkeypatch.delenv("AGB_FASSUNG", raising=False)

    d = client.get("/health").json()

    assert "agb" in d
    assert d["agb"]["fassung_gesetzt"] is False
    assert d["agb"]["wofuer"], "ohne Begründung ist eine Anzeige ein Rätsel"


def test_mit_fassung_meldet_der_bericht_sie(client, monkeypatch):
    monkeypatch.setenv("AGB_FASSUNG", "2026-09-01")

    d = client.get("/health").json()

    assert d["agb"]["fassung_gesetzt"] is True
    assert d["agb"]["fassung"] == "2026-09-01"
