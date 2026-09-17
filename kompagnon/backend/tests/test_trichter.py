# -*- coding: utf-8 -*-
"""Der Trichter als Zusammenfassung, nicht als Zeilenliste (L-192).

**Der Befund vom 10.09.2026.** Jede Zeile in `widget_requests` traegt alle
Stufen als Zeitstempel, und `GET /api/acquisition/widget/requests` gibt sie
einzeln aus. Was fehlte, war die Zusammenfassung: von den Anfragen wie viele
Analysen, wie viele Bestaetigungen, wie viele geoeffnete Berichte. Ohne sie
steht nach zwei Wochen Budget nicht fest, **welche Stufe leckt** — und die
Entscheidung ueber die naechste Kampagne faellt auf Gefuehl statt auf Zahlen.

**Zwei Regeln, die hier haerter wiegen als die Rechnung selbst.**

1. **Was nicht erhoben ist, wird nicht als Null gemeldet.** Die Klicks auf
   die Anzeige stehen bei Meta, die gebuchten Termine im Google-Kalender —
   beides erfaehrt dieses System nicht. Eine `0` an dieser Stelle laese sich
   als „niemand hat geklickt" lesen und waere eine Falschaussage ueber den
   Erfolg der Kampagne. Sie werden deshalb getrennt gefuehrt, mit Grund.
2. **Eine Quote aus drei Anfragen ist keine Quote.** Die Auswertung sagt
   selbst, wenn die Grundgesamtheit zu klein ist. Ohne diesen Hinweis liest
   jemand „33 % Abbruch" und entscheidet danach — bei n = 3.
"""
from datetime import datetime, timedelta

import pytest

from database import SessionLocal
from modelle_audit import AuditResult
from modelle_widget import WidgetRequest
from services import trichter


JETZT = datetime(2026, 9, 14, 12, 0, 0)


@pytest.fixture
def db(app):
    sitzung = SessionLocal()
    try:
        sitzung.query(WidgetRequest).delete()
        sitzung.commit()
        yield sitzung
    finally:
        sitzung.rollback()
        sitzung.close()


def _analyse(db, status="completed"):
    zeile = AuditResult(company_name="Beispiel GmbH", status=status,
                        website_url="https://example.de")
    db.add(zeile)
    db.commit()
    db.refresh(zeile)
    return zeile


def _anfrage(db, bis="angefragt", alter_tage=1, **abweichung):
    """Eine Anfrage, die genau bis zu einer Stufe gekommen ist."""
    stufen = ["angefragt", "analyse_fertig", "bestaetigung_angefragt",
              "bestaetigt", "bericht_versendet", "bericht_geoeffnet"]
    weit = stufen.index(bis)
    erzeugt = JETZT - timedelta(days=alter_tage)
    analyse = _analyse(db, "completed" if weit >= 1 else "failed")

    werte = {
        "email": "kunde@example.de",
        "website_url": "https://example.de",
        "audit_id": analyse.id,
        "created_at": erzeugt,
        "verify_sent_at": erzeugt if weit >= 2 else None,
        "verified_at": erzeugt if weit >= 3 else None,
        "report_sent_at": erzeugt if weit >= 4 else None,
        "report_confirmed_at": erzeugt if weit >= 5 else None,
    }
    werte.update(abweichung)
    zeile = WidgetRequest(**werte)
    db.add(zeile)
    db.commit()
    db.refresh(zeile)
    return zeile


def _stufe(ergebnis, schluessel):
    for eintrag in ergebnis["stufen"]:
        if eintrag["schluessel"] == schluessel:
            return eintrag
    raise AssertionError(f"Stufe {schluessel!r} fehlt")


class TestZaehlung:
    def test_jede_stufe_zaehlt_wer_sie_erreicht_hat(self, db):
        _anfrage(db, bis="angefragt")
        _anfrage(db, bis="bestaetigt")
        _anfrage(db, bis="bericht_geoeffnet")

        ergebnis = trichter.auswerten(db, tage=30, jetzt=JETZT)

        assert ergebnis["grundgesamtheit"] == 3
        assert _stufe(ergebnis, "angefragt")["anzahl"] == 3
        assert _stufe(ergebnis, "analyse_fertig")["anzahl"] == 2
        assert _stufe(ergebnis, "bestaetigt")["anzahl"] == 2
        assert _stufe(ergebnis, "bericht_versendet")["anzahl"] == 1
        assert _stufe(ergebnis, "bericht_geoeffnet")["anzahl"] == 1

    def test_der_zeitraum_schneidet_ab(self, db):
        _anfrage(db, bis="bestaetigt", alter_tage=2)
        _anfrage(db, bis="bestaetigt", alter_tage=40)

        ergebnis = trichter.auswerten(db, tage=30, jetzt=JETZT)

        assert ergebnis["grundgesamtheit"] == 1

    def test_ohne_anfragen_bleibt_die_quote_leer(self, db):
        """**Nicht 0 %.** Null Prozent hiesse „geprueft und niemand kam
        durch"; hier ist gar nichts gemessen worden."""
        ergebnis = trichter.auswerten(db, tage=30, jetzt=JETZT)

        assert ergebnis["grundgesamtheit"] == 0
        assert _stufe(ergebnis, "bestaetigt")["anteil_gesamt"] is None
        assert _stufe(ergebnis, "bestaetigt")["anzahl"] == 0


class TestQuoten:
    def test_anteil_an_der_vorstufe_und_am_ganzen(self, db):
        for _ in range(4):
            _anfrage(db, bis="bestaetigung_angefragt")
        _anfrage(db, bis="bestaetigt")

        ergebnis = trichter.auswerten(db, tage=30, jetzt=JETZT)
        stufe = _stufe(ergebnis, "bestaetigt")

        assert stufe["anzahl"] == 1
        assert stufe["anteil_gesamt"] == 20.0
        assert stufe["anteil_vorstufe"] == 20.0

    def test_die_erste_stufe_hat_keine_vorstufe(self, db):
        _anfrage(db)
        ergebnis = trichter.auswerten(db, tage=30, jetzt=JETZT)

        assert _stufe(ergebnis, "angefragt")["anteil_vorstufe"] is None
        assert _stufe(ergebnis, "angefragt")["anteil_gesamt"] == 100.0


class TestWasNichtErhobenIst:
    def test_klicks_und_termine_stehen_getrennt_mit_grund(self, db):
        _anfrage(db, bis="bericht_geoeffnet")
        ergebnis = trichter.auswerten(db, tage=30, jetzt=JETZT)

        schluessel = {e["schluessel"] for e in ergebnis["nicht_erhoben"]}
        assert schluessel == {"anzeigenklicks", "termine"}
        for eintrag in ergebnis["nicht_erhoben"]:
            assert eintrag["grund"], "Ohne Grund ist eine Leerstelle ein Rätsel"

    def test_sie_tauchen_nicht_als_stufe_mit_null_auf(self, db):
        """Die Regel aus L-165 und dem Audit: 0 heisst „geprueft und nicht
        erfuellt", fehlend heisst „nicht erhoben". Wer die Termine als
        Stufe mit `anzahl: 0` fuehrte, behauptete, es habe niemand gebucht."""
        ergebnis = trichter.auswerten(db, tage=30, jetzt=JETZT)

        schluessel = {e["schluessel"] for e in ergebnis["stufen"]}
        assert "termine" not in schluessel
        assert "anzeigenklicks" not in schluessel


class TestGrundgesamtheit:
    def test_wenige_anfragen_werden_als_zu_wenig_gemeldet(self, db):
        _anfrage(db)
        ergebnis = trichter.auswerten(db, tage=30, jetzt=JETZT)

        assert ergebnis["zu_wenig_daten"] is True

    def test_genug_anfragen_nicht(self, db):
        for _ in range(trichter.MINDESTZAHL):
            _anfrage(db)
        ergebnis = trichter.auswerten(db, tage=30, jetzt=JETZT)

        assert ergebnis["zu_wenig_daten"] is False


class TestHerkunft:
    def test_anfragen_aus_der_anzeige_werden_getrennt_gezaehlt(self, db):
        _anfrage(db, aus_anzeige=True)
        _anfrage(db, aus_anzeige=False)

        ergebnis = trichter.auswerten(db, tage=30, jetzt=JETZT)

        assert ergebnis["grundgesamtheit"] == 2
        assert ergebnis["aus_anzeige"] == 1

    def test_nur_die_anzeige_laesst_sich_getrennt_auswerten(self, db):
        _anfrage(db, bis="bestaetigt", aus_anzeige=True)
        _anfrage(db, bis="angefragt", aus_anzeige=False)

        ergebnis = trichter.auswerten(db, tage=30, jetzt=JETZT, nur_anzeige=True)

        assert ergebnis["grundgesamtheit"] == 1
        assert _stufe(ergebnis, "bestaetigt")["anzahl"] == 1


# ═══════════════════════════════════════════════════════════════════
# Woher die Anfrage kam — am Endpunkt gemessen, nicht am Quelltext
# ═══════════════════════════════════════════════════════════════════
#
# **Die Lehre vom 13.09.2026.** Der Umlaut-Fix war damals am Helfer belegt
# und am Erzeugnis nicht: 16 Tests prueften die Rechenfunktion, keiner fuhr
# die Route. Ein Test, der nur nachsieht, ob `aus_anzeige=` im Quelltext
# **vorkommt**, waere derselbe Fehler — er bliebe gruen, wenn die Zeile
# danebenlaege oder der Wert nie ankaeme. Deshalb faehrt der Test hier den
# Endpunkt und sieht in der Zeile nach, die dabei entsteht.


@pytest.fixture
def ohne_echte_analyse(monkeypatch):
    """Der Endpunkt stoesst sonst einen kostenpflichtigen Lauf an."""
    import routers.audit as audit_router

    async def keine_analyse(*_a, **_k):
        return {"id": None}

    monkeypatch.setattr(audit_router, "start_audit", keine_analyse)
    return True


def _widget_anfrage(client, db, **zusatz):
    rumpf = {"email": f"trichter{zusatz.pop('n', 1)}@example.de",
             "website_url": "https://example.de"}
    rumpf.update(zusatz)
    antwort = client.post("/api/widget/audit", json=rumpf)
    assert antwort.status_code == 200, antwort.text
    return (db.query(WidgetRequest)
            .order_by(WidgetRequest.id.desc()).first())


def test_mit_klickkennung_gilt_die_anfrage_als_aus_der_anzeige(
        client, db, ohne_echte_analyse):
    zeile = _widget_anfrage(client, db, n=1, fbclid="TestKlick14Sep2026")

    assert zeile.aus_anzeige is True


def test_ohne_klickkennung_nicht(client, db, ohne_echte_analyse):
    """**Die Gegenprobe.** Eine Herkunft, die immer wahr ist, saehe im Test
    darueber richtig aus und machte jede Kampagnenauswertung wertlos."""
    zeile = _widget_anfrage(client, db, n=2)

    assert zeile.aus_anzeige is False


def test_die_klickkennung_selbst_wird_nicht_gespeichert(
        client, db, ohne_echte_analyse):
    """**Datensparsamkeit, und sie kostet hier nichts.** Fuer die Frage
    „welche Stufe leckt bei der Kampagne" genuegt *ob* geklickt wurde. Die
    Kennung selbst ist eine Kennung — sie an eine Mailadresse zu heften,
    waere mehr, als die Auswertung braucht."""
    kennung = "TestKlick14Sep2026Einmalig"
    zeile = _widget_anfrage(client, db, n=3, fbclid=kennung)

    gespeichert = " ".join(str(getattr(zeile, feld) or "") for feld in
                           ("referrer", "user_agent", "website_url", "email"))
    assert kennung not in gespeichert


# ═══════════════════════════════════════════════════════════════════
# Der Endpunkt — und ob ihn ueberhaupt jemand aufruft
# ═══════════════════════════════════════════════════════════════════


def test_die_auskunft_verlangt_eine_anmeldung(client):
    """Sie nennt Geschäftszahlen. Ohne Anmeldung stünde die Ausbeute jeder
    Kampagne im offenen Netz."""
    assert client.get("/api/acquisition/widget/trichter").status_code in (401, 403)


def test_die_auskunft_liefert_stufen_und_leerstellen(client, auth_headers):
    antwort = client.get("/api/acquisition/widget/trichter", headers=auth_headers)

    assert antwort.status_code == 200
    daten = antwort.json()
    assert [s["schluessel"] for s in daten["stufen"]] == \
        [s for s, _n, _f in trichter.STUFEN]
    assert {e["schluessel"] for e in daten["nicht_erhoben"]} == \
        {"anzeigenklicks", "termine"}


def test_ein_unsinniger_zeitraum_wird_begrenzt(client, auth_headers):
    """Eingaben an der Systemgrenze werden geprüft, nicht durchgereicht."""
    kurz = client.get("/api/acquisition/widget/trichter?tage=0",
                      headers=auth_headers).json()
    lang = client.get("/api/acquisition/widget/trichter?tage=99999",
                      headers=auth_headers).json()

    assert kurz["zeitraum_tage"] == 7
    assert lang["zeitraum_tage"] == 365


def test_die_oberflaeche_ruft_die_auswertung_auf():
    """**Die Klasse, die dieses Projekt fuenfmal getroffen hat:** ein
    Endpunkt ohne Knopf. `webhook_actions` liess sich setzen und wurde nie
    gelesen, `meta_conversions.verfuegbar()` rief niemand auf. Eine
    Auswertung, die im Werkzeug nicht vorkommt, waere derselbe Fehler — und
    wuerde als „gebaut" gemeldet."""
    import pathlib

    seite = (pathlib.Path(__file__).resolve().parents[2]
             / "frontend" / "src" / "pages" / "AkquiseWidget.jsx")
    assert seite.exists(), seite
    assert "/api/acquisition/widget/trichter" in seite.read_text(encoding="utf-8"), (
        "Die Auswertung ist gebaut, aber keine Seite ruft sie auf")


# ═══════════════════════════════════════════════════════════════════
# Der Vertriebsplan daneben — angenommen, nicht gemessen (15.09.2026)
# ═══════════════════════════════════════════════════════════════════
#
# **Woher die Zahlen stammen.** Der Vertriebsplan vom 15.09.2026 rechnet
# einen Monat durch: rund 60 echte Leads, davon rund 42 zugestellte Scores
# (20 bis 40 Prozent gehen im Double-Opt-in verloren), daraus rund 4
# Gespraeche, daraus rund 2 Check PLUS und daraus 0 bis 1 Relaunch.
#
# **Keine dieser Zahlen ist gemessen.** Der Plan sagt das selbst und nennt
# sie ANGENOMMEN. Die Entscheidung E17 desselben Plans verlangt, die
# Herkunft ueberall auszuweisen — und genau hier wird es ernst: Neben
# gemessenen Stufen sieht eine angenommene Zahl aus wie eine gemessene.
#
# **Drei Klassen, sauber getrennt:**
#   gemessen       aus widget_requests, mit Zeitstempel je Zeile
#   angenommen     aus dem Vertriebsplan, auf die gemessene Basis gerechnet
#   nicht erhoben  Anzeigenklicks (Meta) und Termine (Google-Kalender)
#
# Die dritte Klasse ist die, die man am leichtesten zur Null macht.


class TestErwartung:
    def test_die_erwartung_nennt_ihre_herkunft(self, db):
        ergebnis = trichter.auswerten(db, tage=30, jetzt=JETZT)

        for eintrag in ergebnis["angenommen"]:
            assert eintrag["herkunft"], "Eine Annahme ohne Quelle ist eine Behauptung"
            assert eintrag["art"] == "angenommen"

    def test_gemessene_stufen_sind_als_gemessen_ausgewiesen(self, db):
        _anfrage(db)
        ergebnis = trichter.auswerten(db, tage=30, jetzt=JETZT)

        assert all(s["art"] == "gemessen" for s in ergebnis["stufen"])

    def test_die_annahmen_rechnen_auf_der_gemessenen_basis(self, db):
        """Nicht die Planzahl anzeigen, sondern was der Plan **bei diesen**
        Zahlen erwarten liesse. Sonst steht neben 3 gemessenen Berichten eine
        60 aus dem Plan, und niemand weiss, worauf sie sich bezieht."""
        for _ in range(20):
            _anfrage(db, bis="bericht_versendet")

        ergebnis = trichter.auswerten(db, tage=30, jetzt=JETZT)
        gespraech = next(e for e in ergebnis["angenommen"]
                         if e["schluessel"] == "gespraech")

        assert gespraech["erwartet"] == 2.0
        assert gespraech["basis"] == "bericht_versendet"

    def test_ohne_basis_bleibt_die_erwartung_leer(self, db):
        """**Nicht 0.** Null hiesse „der Plan erwartet keinen Termin"; richtig
        ist „es gibt nichts, worauf sich die Quote beziehen koennte"."""
        ergebnis = trichter.auswerten(db, tage=30, jetzt=JETZT)

        for eintrag in ergebnis["angenommen"]:
            assert eintrag["erwartet"] is None

    def test_der_doi_verlust_wird_gegen_die_messung_gehalten(self, db):
        """Die **einzige** Planquote, die sich heute pruefen laesst: Der Plan
        rechnet mit 20 bis 40 Prozent Verlust im Double-Opt-in."""
        for _ in range(10):
            _anfrage(db, bis="bestaetigung_angefragt")
        for _ in range(10):
            _anfrage(db, bis="bestaetigt")

        ergebnis = trichter.auswerten(db, tage=30, jetzt=JETZT)
        stufe = _stufe(ergebnis, "bestaetigt")

        assert stufe["erwartet_von"] == 60.0
        assert stufe["erwartet_bis"] == 80.0
        assert stufe["anteil_vorstufe"] == 50.0
        assert stufe["unter_erwartung"] is True

    def test_im_erwarteten_bereich_wird_nicht_gewarnt(self, db):
        for _ in range(10):
            _anfrage(db, bis="bestaetigt")

        ergebnis = trichter.auswerten(db, tage=30, jetzt=JETZT)
        assert _stufe(ergebnis, "bestaetigt")["unter_erwartung"] is False

    def test_ohne_vorstufe_wird_nicht_gewarnt(self, db):
        """Sonst meldet eine leere Ansicht „unter Erwartung" — und die erste
        Zahl, die jemand sieht, ist ein Alarm ueber nichts."""
        ergebnis = trichter.auswerten(db, tage=30, jetzt=JETZT)
        assert _stufe(ergebnis, "bestaetigt")["unter_erwartung"] is False
