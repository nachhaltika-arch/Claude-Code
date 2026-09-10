# -*- coding: utf-8 -*-
"""Ob der Meta-Meldeweg abgehen kann — von aussen sichtbar (09.09.2026).

**Der Anlass.** Am 09.09. liess sich die Frage „ist der Zugangstoken gesetzt?"
von aussen nicht beantworten. `meta_conversions.verfuegbar()` gab es seit dem
Vortag, aber **kein Endpunkt rief es auf**. Fuer Stripe, die Uploads, den
Browserlauf, die Dateiablage und die AGB-Fassung steht der Zustand laengst in
`/health` — ausgerechnet fuer den Weg, an dem eine bezahlte Kampagne haengt,
nicht. Dieselbe Lehre wie dort: **Ein Dashboard zeigt die Einstellung, nicht
den Zustand des Prozesses.**

**Gemeldet wird nie der Wert.** Ein Zugangstoken auf einer offenen Route waere
schlimmer als gar keine Auskunft. Ja/Nein und Laenge genuegen: Wer beim
Einfuegen die Haelfte verliert, sieht es an der Laenge — ein CAPI-Token ist
gut 200 Zeichen lang, steht dort 30, ist etwas abgeschnitten.

**Warum eine Abwesenheits-Pruefung hier nicht reicht.** „Der Token steht nicht
in der Antwort" waere auch dann gruen, wenn die Auskunft gar nichts meldet.
Neben jeder solchen Zusicherung steht deshalb eine positive.
"""
import pytest

from services import meta_conversions as mc


@pytest.fixture(autouse=True)
def saubere_umgebung(monkeypatch):
    """Kein Wert aus der echten Umgebung faellt in einen Test hinein."""
    for name in ("META_CAPI_ACCESS_TOKEN", "META_PIXEL_ID", "META_TEST_EVENT_CODE"):
        monkeypatch.delenv(name, raising=False)


class TestZustand:
    """`meta_conversions.zustand(db)` — die Auskunft fuer `/health`."""

    def test_ohne_token_ist_der_weg_nicht_bereit(self):
        z = mc.zustand()
        assert z["token_gesetzt"] is False
        assert z["token_laenge"] == 0
        assert z["bereit"] is False

    def test_mit_token_und_pixel_ist_er_bereit(self, monkeypatch):
        monkeypatch.setenv("META_CAPI_ACCESS_TOKEN", "EAA" + "x" * 200)
        monkeypatch.setenv("META_PIXEL_ID", "1363198722345965")
        z = mc.zustand()
        assert z["token_gesetzt"] is True
        assert z["token_laenge"] == 203
        assert z["pixel_gesetzt"] is True
        assert z["bereit"] is True

    def test_token_allein_genuegt_nicht(self, monkeypatch):
        # Ohne Datensatz gibt es kein Ziel — Meta wuerde die Meldung ablehnen.
        monkeypatch.setenv("META_CAPI_ACCESS_TOKEN", "EAA" + "x" * 200)
        z = mc.zustand()
        assert z["token_gesetzt"] is True
        assert z["pixel_gesetzt"] is False
        assert z["bereit"] is False

    def test_pixel_allein_genuegt_nicht(self, monkeypatch):
        monkeypatch.setenv("META_PIXEL_ID", "1363198722345965")
        z = mc.zustand()
        assert z["pixel_gesetzt"] is True
        assert z["bereit"] is False

    def test_der_token_steht_nirgends_in_der_antwort(self, monkeypatch):
        """Die eigentliche Zusicherung — `/health` ist eine offene Route."""
        geheim = "EAAgeheimerWert" + "z" * 190
        monkeypatch.setenv("META_CAPI_ACCESS_TOKEN", geheim)
        z = mc.zustand()
        # Abwesenheit …
        assert geheim not in repr(z)
        assert "geheimerWert" not in repr(z)
        # … und die positive Probe daneben: die Auskunft sagt trotzdem etwas.
        assert z["token_gesetzt"] is True
        assert z["token_laenge"] == len(geheim)

    def test_woher_die_pixelnummer_kommt(self, monkeypatch):
        """Sonst sucht jemand in der Datenbank, was in Render steht."""
        assert mc.zustand()["pixel_quelle"] == ""
        monkeypatch.setenv("META_PIXEL_ID", "1363198722345965")
        assert mc.zustand()["pixel_quelle"] == "umgebung"

    def test_pixel_aus_den_einstellungen(self):
        """Der Regelfall produktiv: die Nummer steht im Werkzeug, nicht in Render."""
        class Db:
            pass

        # `_pixel_id` liest ueber `app_settings.get`; hier wird die Quelle
        # ersetzt, nicht das Ergebnis behauptet.
        import services.app_settings as ae
        alt = ae.get
        ae.get = lambda db, key, default="": (
            "1363198722345965" if key == "widget_facebook_pixel_id" else default)
        try:
            z = mc.zustand(Db())
        finally:
            ae.get = alt
        assert z["pixel_gesetzt"] is True
        assert z["pixel_quelle"] == "einstellung"

    def test_testereignis_wird_gemeldet(self, monkeypatch):
        """Laeuft die Kampagne noch im Probebetrieb, gehoert das in die Auskunft."""
        assert mc.zustand()["testereignis"] is False
        monkeypatch.setenv("META_TEST_EVENT_CODE", "TEST12345")
        assert mc.zustand()["testereignis"] is True
