# -*- coding: utf-8 -*-
"""Eine Zahlung, die zu keinem Vorgang gehoert, erreicht einen Menschen.

**Der Stand nach dem 14.09.2026.** Die Weiche `zahlungsweg.von_uns` verhindert
seit gestern, dass ein Kauf ueber den Check-PLUS-Zahllink als Websprint
verbucht wird und dem Kaeufer ein Website-Projekt anlegt. Was sie nicht kann:
den Vorgang zu Ende bringen. Das Geld kommt an, zuordnen laesst es sich hier
nicht — und **erfahren** hat es bisher nur das Protokoll.

**Warum das nicht reicht.** Ein `logger.error` in Render liest jemand, der
danach sucht. Niemand sucht nach etwas, von dem er nichts weiss. Genau diese
Form hatte der Vorfall vom 17.08.2026: Ein Job verschickte vier Monate lang
Mails, und es stand alles im Protokoll. Waehrend einer laufenden Kampagne ist
ein unbemerkter Zahlungseingang der teuerste Fall — der Kaeufer hat bezahlt
und wartet.

Die Glocke gibt es seit L-18 und sie ist ausdruecklich dafuer gebaut: „Wer
eine vierte Quelle hinzufuegt, ruft `melden`."
"""
from database import SessionLocal
from modelle_meldungen import Benachrichtigung
from routers.payments import _handle_successful_payment
from services import benachrichtigungen


class _Buchhalter:
    """Eine Sitzung, die jeden Zugriff meldet — wie in `test_zahlungsweg`."""

    def __init__(self):
        self.benutzt = []

    def execute(self, *_a, **_k):
        self.benutzt.append("execute")
        raise AssertionError("Die Datenbank wurde angefasst")

    def add(self, *_a, **_k):
        self.benutzt.append("add")
        raise AssertionError("Es wurde etwas angelegt")

    def rollback(self, *_a, **_k):
        self.benutzt.append("rollback")


def _fremde_sitzung(kennung="cs_live_zahllink_1"):
    return {"id": kennung, "metadata": {}, "amount_total": 29631,
            "customer_details": {"email": "kaeufer@example.org"}}


def _meldungen(db, kennung):
    return (db.query(Benachrichtigung)
            .filter(Benachrichtigung.art == "zahlung",
                    Benachrichtigung.hinweis.like(f"%{kennung}%"))
            .all())


def _aufraeumen(db, kennung):
    for zeile in _meldungen(db, kennung):
        db.delete(zeile)
    db.commit()


def test_die_glocke_kennt_die_art(app):
    """Ohne Eintrag in `ARTEN` legt `melden` sie zwar ab, meldet aber einen
    Programmierfehler ins Protokoll — und die Liste, die sagt was es gibt,
    wuerde luegen."""
    assert "zahlung" in benachrichtigungen.ARTEN


def test_eine_unzuordenbare_zahlung_erzeugt_eine_meldung(app):
    kennung = "cs_live_test_meldung"
    db = SessionLocal()
    try:
        _aufraeumen(db, kennung)
        _handle_successful_payment(_fremde_sitzung(kennung), _Buchhalter())

        gefunden = _meldungen(db, kennung)
        assert len(gefunden) == 1, "Die Zahlung bleibt unbemerkt"
        assert "29631" in gefunden[0].hinweis or "296,31" in gefunden[0].hinweis, (
            "Ohne Betrag sagt die Meldung nicht, worum es geht")
    finally:
        _aufraeumen(db, kennung)
        db.close()


def test_derselbe_vorgang_meldet_sich_nur_einmal(app):
    """Stripe stellt bei Zweifeln erneut zu. Zwei Glocken fuer eine Zahlung
    sind schlimmer als eine: Wer zweimal dasselbe liest, glaubt beim dritten
    Mal keiner Meldung mehr."""
    kennung = "cs_live_test_doppelt"
    db = SessionLocal()
    try:
        _aufraeumen(db, kennung)
        _handle_successful_payment(_fremde_sitzung(kennung), _Buchhalter())
        _handle_successful_payment(_fremde_sitzung(kennung), _Buchhalter())

        assert len(_meldungen(db, kennung)) == 1
    finally:
        _aufraeumen(db, kennung)
        db.close()


def test_ein_echter_websprint_kauf_meldet_nichts(app):
    """**Die Gegenprobe.** Eine Meldung, die bei jeder Zahlung anschlaegt,
    waere in den Tests oben gruen und im Betrieb wertlos."""
    kennung = "cs_live_test_echt"
    db = SessionLocal()
    try:
        _aufraeumen(db, kennung)
        sitzung = {"id": kennung, "metadata": {"package": "starter",
                                               "customer_email": "k@example.de"},
                   "amount_total": 416500}
        try:
            _handle_successful_payment(sitzung, _Buchhalter())
        except AssertionError:
            pass          # Der Pfad laeuft weiter — genau das ist erwuenscht.

        assert _meldungen(db, kennung) == []
    finally:
        _aufraeumen(db, kennung)
        db.close()


def test_die_meldung_zerreisst_den_vorgang_nicht(app, monkeypatch):
    """Scheitert die Glocke, darf der Webhook trotzdem nicht 500 antworten —
    die Zahlung ist wichtiger als ihre Meldung (dieselbe Lehre wie bei der
    Willkommensmail am 26.08.2026)."""
    def kaputt(*_a, **_k):
        raise RuntimeError("Glocke defekt")

    monkeypatch.setattr(benachrichtigungen, "melden", kaputt)

    _handle_successful_payment(_fremde_sitzung("cs_live_test_kaputt"),
                               _Buchhalter())


def test_die_glocke_zeigt_jede_art_mit_eigenem_zeichen():
    """**Sonst faellt die neue Art auf den Punkt zurueck** und sieht aus wie
    etwas, das jemand vergessen hat einzutragen — der Kommentar in
    `Glocke.jsx` sagt das seit dem 01.09.2026, und beim naechsten Mal wird es
    wieder jemand uebersehen. Deshalb prueft es hier eine Zeile.

    Geprueft wird die **ganze** Liste, nicht nur die neue Art: Ein Waechter,
    der nur den heutigen Fall kennt, ist beim uebernaechsten wieder blind.
    """
    import pathlib

    glocke = (pathlib.Path(__file__).resolve().parents[2]
              / "frontend" / "src" / "components" / "Layout" / "Glocke.jsx")
    assert glocke.exists(), glocke
    quelle = glocke.read_text(encoding="utf-8")
    sinnbild = quelle.split("const SINNBILD = {", 1)[1].split("};", 1)[0]

    fehlend = [art for art in benachrichtigungen.ARTEN if f"{art}:" not in sinnbild]
    assert not fehlend, f"Ohne eigenes Zeichen in der Glocke: {fehlend}"
