# -*- coding: utf-8 -*-
"""
Wir liefern uns selbst aus, was wir verkaufen (L-121).

**Der Befund vom 25.08.2026.** Der neue Prüfer `geo_auslieferung` an den
eigenen Adressen: keine `llms.txt`, keine strukturierten Daten, keine
`robots.txt`. Genau die Artefakte, die GEO-01 für 1.200 € an Kundenseiten
ausliefert.

**Warum ein Test und nicht nur ein Datensatz.** Beim ersten Anlauf hießen die
Felder `zip_code` und `titel` statt `postal_code` und `page_name` — die
Erzeuger melden das nicht, sie **lassen weg**. Anschrift und Seitenliste
fielen stillschweigend heraus, und die Datei sah trotzdem fertig aus.
"""
from services.kompagnon_profil import BETRIEB, eigenes_profil


def test_die_eigene_llms_txt_ist_vollstaendig():
    datei, _ = eigenes_profil()

    assert datei.startswith("# KOMPAGNON communications BP GmbH")
    assert "Marienfelder Straße 52, 56070 Koblenz" in datei, (
        "die Anschrift faellt heraus — vermutlich stimmen die Feldnamen nicht")
    assert "hallo@kompagnon.group" in datei
    assert "Website-Check" in datei, "die Seitenliste faellt heraus"


def test_die_strukturierten_daten_tragen_die_anschrift():
    _, jsonld = eigenes_profil()

    assert '"@type": "LocalBusiness"' in jsonld
    assert "Marienfelder" in jsonld
    assert '"postalCode": "56070"' in jsonld


def test_die_quelle_ist_die_titelei():
    """Firmierung und Anschrift stehen im rechtlich geprüften Dokument.

    Wer sie ändert, ändert sie dort zuerst — sonst laufen zwei Stände
    auseinander, und einer davon steht gedruckt im Buch.
    """
    import pathlib

    titelei = (pathlib.Path(__file__).resolve().parents[3] / "docs" / "Buch"
               / "Buch - Kompagnon - Homepage Standard v2"
               / "Vollständige dokumentation Buch V2" / "TITELEI.md")
    text = titelei.read_text(encoding="utf-8")

    assert BETRIEB.company_name in text
    assert BETRIEB.street in text and BETRIEB.postal_code in text


def test_der_kas_deploy_liefert_beides_mit():
    """Ein Erzeuger ohne Auslieferung ist genau die Lücke von L-99."""
    import inspect

    from routers import kas_router

    quelle = inspect.getsource(kas_router.deploy_kas_pages)
    assert "eigenes_profil" in quelle
    assert "zusatzdateien" in quelle
    assert "pruefe_auslieferung" in quelle, "niemand sieht nach, ob es ankam"
