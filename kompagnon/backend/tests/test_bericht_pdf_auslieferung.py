# -*- coding: utf-8 -*-
"""Schritt 9 des Trichters: das PDF, wie der Kunde es bekommt (13.09.2026).

**Der Anlass ist eine Lücke zwischen zwei grünen Dingen.** Am 12.09. kam das
PDF des Berichts mit einem Latin-1-`ü` in der Kopfzeile heraus; behoben wurde
das in `f1a3ffb` über `services/dateinamen.py`, und 16 Tests halten den
Helfer. Gefunden hat den Fehler aber **kein Test**, sondern ein einmaliger
Durchlauf von Hand — und danach fuhr wieder keiner die Route.

Nachgesehen: Von allen Tests holt **keiner** ein 200 von
`/api/widget/report/{token}/pdf`. Der einzige, der sie überhaupt anfasst,
prüft ein 404 (`test_widget_einwilligung.py::test_pdf_haengt_am_selben_token`).

**Was dieser Test zusätzlich hält — gemessen, nicht behauptet.** Hier stand
zuerst, das Entfernen von `anhang_kopfzeile` aus dieser Route ließe „jeden
Test grün". Das war falsch: `TestKeinHandbau` liest den Quelltext und schlägt
sofort an. Die Grenze liegt woanders, und sie wurde mit zwei Proben gesucht:

* Aufruf entfernt → alte Tests **rot**, dieser auch. Kein Zugewinn.
* Name **vor** dem Helfer beschädigt (`name.encode("ascii", "replace")`,
  aus `Ingenieurbüro` wird `Ingenieurb?ro`) → alle 16 alten Tests **grün**,
  dieser **rot**.

Dort liegt der Zugewinn: Die alten Tests prüfen, dass der Helfer richtig
rechnet und dass die Route ihn im Quelltext *nennt*. Ob das, was am Ende über
die Leitung geht, den Namen noch trägt, prüft keiner von ihnen — und ob die
Route überhaupt ein PDF liefert, ebenfalls nicht. Ein 503 aus dem
PDF-Erzeuger wäre bis heute von keinem Test bemerkt worden.

**Der Name ist mit Absicht unangenehm.** `Ingenieurbüro Groß & Söhne "Wärme"`
trägt drei Umlaute, ein `ß` und ein Anführungszeichen. Die Umlaute sind der
Fehler vom 12.09., das Anführungszeichen ist der schwerere Fall: `company_name`
kommt aus dem Scraper, also von einer fremden Seite, und ein Anführungszeichen
darin beendet die Zeichenkette der Kopfzeile.
"""
import json

import pytest

from database import AuditResult, SessionLocal, WidgetRequest

#: Drei Umlaute, ein Eszett, ein Anführungszeichen — der Fall vom 12.09. plus
#: der Einschleusungsfall in einem Namen.
FIRMA = 'Ingenieurbüro Groß & Söhne "Wärme"'

TOKEN = "pdf-auslieferung-berichts-token"


def _einzelbewertungen():
    """Wertungen aus dem **echten** Katalog, als JSON-Zeichenkette.

    Zwei Fallen, beide in dieser Sitzung erst ausgelöst und dann behoben:

    Eine Analyse ohne `item_scores` lässt den PDF-Erzeuger abbrechen
    (*„stammt aus dem früheren Katalog"*), die Route antwortet mit 503 — der
    erste Lauf dieses Tests war genau deshalb rot.

    Und die Spalten sind `Text` (siehe `modelle_audit.py`): Aus der Datenbank
    kommen **Zeichenketten**, keine Wörterbücher. `_parse_json_field` gibt
    für ein Wörterbuch `[]` zurück — dieselbe Verweigerung, nur schwerer zu
    sehen. Die Kennungen kommen deshalb aus `all_criteria()` und nicht aus
    dem Gedächtnis: Erfundene Schlüssel wie `impressum_vorhanden` (der
    Katalog führt `rc_impressum`) ergeben einen Bericht, der zu keinem
    Kriterium etwas findet und trotzdem 200 liefert.
    """
    from services.audit_criteria import all_criteria

    kriterien = list(all_criteria())
    werte = {k.key: k.max_points for k in kriterien}
    quellen = {k.key: getattr(k.source, "value", str(k.source)) for k in kriterien}
    return json.dumps(werte), json.dumps(quellen), sum(werte.values())


@pytest.fixture
def analyse_mit_umlaut():
    """Eine fertige Analyse samt Widget-Anfrage — der Stand nach dem Klick."""
    werte, quellen, punkte = _einzelbewertungen()
    db = SessionLocal()
    try:
        audit = AuditResult(
            website_url="https://ingenieurbuero.example",
            company_name=FIRMA,
            status="completed",
            total_score=punkte,
            level="Homepage Standard Bronze",
            item_scores=werte,
            item_sources=quellen,
            item_belege=json.dumps({}),
            coverage=100,
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)
        audit_id = audit.id

        db.add(WidgetRequest(
            email="umlaut@firma-xy.de",
            website_url="https://ingenieurbuero.example",
            report_token=TOKEN,
            poll_token="pdf-auslieferung-poll-token",
            audit_id=audit_id,
        ))
        db.commit()
    finally:
        db.close()

    yield audit_id

    db = SessionLocal()
    try:
        db.query(WidgetRequest).filter(
            WidgetRequest.report_token == TOKEN).delete()
        db.query(AuditResult).filter(AuditResult.id == audit_id).delete()
        db.commit()
    finally:
        db.close()


class TestDasPdfKommtAn:
    """Erst das Erzeugnis — ohne 200 sagt jede Kopfzeilenprüfung nichts."""

    def test_die_route_liefert_ein_pdf(self, client, analyse_mit_umlaut):
        # Act
        r = client.get(f"/api/widget/report/{TOKEN}/pdf")

        # Assert
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/pdf")
        # Der Rumpf, nicht die Länge: Ein 503 mit Fehlertext wäre auch „nicht leer".
        assert r.content[:5] == b"%PDF-"


class TestDieKopfzeileUeberlebtDenNamen:
    """Der Fehler vom 12.09., gemessen an der ausgelieferten Antwort."""

    @pytest.fixture
    def kopfzeile(self, client, analyse_mit_umlaut):
        r = client.get(f"/api/widget/report/{TOKEN}/pdf")
        assert r.status_code == 200
        return r.headers["content-disposition"]

    def test_kein_rohbyte_ausserhalb_von_ascii(self, kopfzeile):
        """Genau der Fund vom 12.09.: `0xfc` in einem Feld, das nur ASCII darf."""
        kopfzeile.encode("ascii")  # wirft bei einem rohen Umlaut

    def test_der_rueckfall_ist_lesbar_umgeschrieben(self, kopfzeile):
        # `Ingenieurbro` wäre ein Tippfehler, `Ingenieurbuero` ist ein Name.
        assert 'filename="' in kopfzeile
        assert "Ingenieurbuero" in kopfzeile
        assert "Gross" in kopfzeile
        assert "Soehne" in kopfzeile

    def test_der_echte_name_steht_daneben(self, kopfzeile):
        # RFC 6266: `filename*` trägt den Namen, den der Kunde erwartet.
        assert "filename*=UTF-8''" in kopfzeile
        assert "Ingenieurb%C3%BCro" in kopfzeile

    def test_das_anfuehrungszeichen_beendet_die_zeichenkette_nicht(self, kopfzeile):
        """`company_name` kommt von einer fremden Seite — das hier ist die Schranke."""
        rueckfall = kopfzeile.split('filename="', 1)[1].split('"', 1)[0]
        assert rueckfall.endswith(".pdf"), rueckfall

    def test_es_ist_ein_anhang_und_keine_anzeige(self, kopfzeile):
        assert kopfzeile.startswith("attachment;")
