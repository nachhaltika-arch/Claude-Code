# -*- coding: utf-8 -*-
"""Der Serverweg findet seine Pixel-ID auch ohne uebergebene Sitzung.

**Der Befund vom 17.09.2026.** Im Events Manager kam `PageView` ueber Browser
und Server an, `Lead` nur ueber den Browser. `/health` meldete gleichzeitig
`meta.bereit: true` — Token gesetzt, Pixel gesetzt. Beides stimmte, und
trotzdem meldete der Serverweg nichts.

**Die Ursache war eine fehlende Sitzung, kein fehlender Wert.** Die Pixel-ID
steht produktiv nicht in der Umgebung, sondern in den Widget-Einstellungen
(`/health`: `pixel_quelle: "einstellung"`). `_pixel_id` liest sie von dort —
aber nur mit einer Datenbanksitzung. `sende_lead` laeuft als
Hintergrundauftrag und bekam keine, also gab `_pixel_id` einen leeren String
zurueck und die Funktion brach ab:

    2026-09-17 16:03:34 - services.meta_conversions - INFO -
    Meta CAPI: kein Token oder keine Pixel-ID — nichts gesendet.

`/health` dagegen fragt **mit** Sitzung und fand dieselbe Nummer. Zwei Wege
zur selben Auskunft, einer davon blind — und der blinde war der, der sendet.

**Warum keine Sitzung durchgereicht wird.** `get_db` schliesst im `finally`,
und Hintergrundaufgaben laufen nach der Antwort. Eine mitgegebene Sitzung
waere dann geschlossen. Das Haus loest das anderswo schon so:
`widget_crm.uebertrage_anfrage` oeffnet sich eine eigene ("Laeuft als
Hintergrundauftrag und oeffnet deshalb eine eigene Sitzung").
"""
import os

import pytest

from services import meta_conversions as mc


@pytest.fixture
def ohne_umgebungsvariable(monkeypatch):
    """Produktiv steht die Nummer **nicht** in der Umgebung — genau der Fall,
    in dem der Fehler auftrat. Mit gesetzter Variable haette ihn nie jemand
    bemerkt, denn dann greift der erste Zweig und die Sitzung ist egal."""
    monkeypatch.delenv("META_PIXEL_ID", raising=False)


def test_die_umgebung_gewinnt_weiterhin(monkeypatch):
    """Die Reihenfolge bleibt: Wer den Serverweg auf einen anderen Datensatz
    legen muss, tut das ohne Datenbankeingriff."""
    monkeypatch.setenv("META_PIXEL_ID", "999888777")
    assert mc._pixel_id(None) == "999888777"
    assert mc._pixel_id("eine kaputte sitzung") == "999888777"


def test_ohne_umgebung_und_ohne_sitzung_wird_die_einstellung_gelesen(
        app, ohne_umgebungsvariable, monkeypatch):
    """**Der Kern.** Frueher gab `_pixel_id(None)` hier einen leeren String
    zurueck — und der Serverweg schwieg, obwohl die Nummer eingetragen war.
    """
    from database import SessionLocal
    from services import app_settings

    db = SessionLocal()
    try:
        app_settings.set_many(db, {"widget_facebook_pixel_id": "1234567890"})
        db.commit()
    finally:
        db.close()

    assert mc._pixel_id(None) == "1234567890", (
        "Ohne Sitzung findet der Serverweg seine Pixel-ID nicht — genau der "
        "Fehler vom 17.09.2026.")


def test_eine_uebergebene_sitzung_wird_weiterhin_benutzt(
        app, ohne_umgebungsvariable):
    """Positiv daneben: Der Weg mit Sitzung bleibt unberuehrt. Ohne diese
    Zusicherung waere die obige auch dann gruen, wenn die Funktion die
    uebergebene Sitzung ignoriert und immer eine neue oeffnet — was bei jedem
    Aufruf aus einem Endpunkt eine Sitzung zu viel waere."""
    from database import SessionLocal
    from services import app_settings

    db = SessionLocal()
    try:
        app_settings.set_many(db, {"widget_facebook_pixel_id": "5550001111"})
        db.commit()
        assert mc._pixel_id(db) == "5550001111"
    finally:
        db.close()


def test_ohne_eingetragene_nummer_bleibt_es_leer(app, ohne_umgebungsvariable):
    """Kein Rueckfall auf irgendeinen Wert. Eine erfundene Datensatznummer
    waere schlimmer als keine: Meta nimmt die Meldung an und ordnet sie einem
    fremden Konto zu."""
    from database import SessionLocal
    from services import app_settings

    db = SessionLocal()
    try:
        app_settings.set_many(db, {"widget_facebook_pixel_id": ""})
        db.commit()
    finally:
        db.close()

    assert mc._pixel_id(None) == ""


def test_der_lead_wird_ohne_sitzung_eingereiht(app):
    """**Die Stelle, an der es auffiel.** Der Router reicht keine Sitzung
    durch — und das soll so bleiben, weil sie zum Ausfuehrungszeitpunkt des
    Hintergrundauftrags geschlossen waere. Der Test haelt fest, dass niemand
    auf die naheliegende, aber falsche Reparatur verfaellt.
    """
    import pathlib
    import re

    quelle = pathlib.Path("routers/widget.py").read_text(encoding="utf-8")

    # **Nicht am ersten Vorkommen schneiden.** `meta_conversions.sende_lead`
    # steht auch in einem Kommentar weiter oben ("Siehe ..."); ein Schnitt
    # dort prueft Fliesstext statt Code. (Selbst hineingelaufen, 17.09.2026 —
    # zum dritten Mal an diesem Tag derselbe Fehler.)
    stelle = quelle.index("add_task(\n            meta_conversions.sende_lead")
    aufruf = quelle[stelle:stelle + 500]

    assert not re.search(r"\bdb\s*=\s*db\b", aufruf), (
        "Dem Hintergrundauftrag wird eine Sitzung mitgegeben. Sie ist zum "
        "Ausfuehrungszeitpunkt geschlossen (`get_db` schliesst im `finally`) "
        "— die Funktion oeffnet sich selbst eine.")

    # Positiv daneben: Der Aufruf existiert ueberhaupt und traegt die Kennung,
    # ohne die Meta den Lead zweimal zaehlt.
    assert "event_id=" in aufruf, "Der Aufruf gibt keine event_id mit."
