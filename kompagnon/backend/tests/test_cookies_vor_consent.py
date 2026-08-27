# -*- coding: utf-8 -*-
"""Die Deckelregel, die der Katalog seit jeher nennt und niemand erhob.

**Der Stand bis zum 26.08.2026.** `cookies_ohne_consent` steht in
`BLOCKING_MAJOR` — sie deckelt die Note. Erhoben wurde sie nie:
`detect_consent` liest HTML und erkennt ein Consent-Werkzeug an seiner
**Signatur**. Ob tatsächlich Cookies vor der Einwilligung gesetzt werden,
sieht dabei niemand. Die Regel blieb trotzdem stehen — sie zu entfernen,
weil die Messung fehlt, hieße den Maßstab nach der Erhebungslage zu richten.
`NICHT_ERHOBENE_BLOCKER` hielt das sichtbar.

**Seit dem Browserlauf geht es.** Er klickt kein Banner an. Was danach im
Kontext steht, steht dort ohne Zustimmung.

**Gewertet wird nur, was keine Notwendigkeitsausnahme haben kann.** Ob ein
Cookie technisch notwendig ist, hängt von der Seite ab — ein Warenkorb darf
vor der Einwilligung gesetzt werden, und das kann von außen niemand
entscheiden. `_ga`, `_fbp`, `IDE` gehören zu Messung und Werbung; dafür gibt
es diese Ausnahme nicht. Der Preis für eine Aussage, die hält, ist, dass sie
weniger sagt.

**Und ohne Browserlauf wird nichts behauptet.** Dann steht `collected: False`
— nicht „keine Verfolger gefunden". Wer nicht nachgesehen hat, sagt nicht,
dass nichts da war.
"""
import pytest

from services import seitenbrowser
from services.audit_runner import _cookies_vor_consent
from services.audit_scoring import detect_blockers


def _lauf(cookies):
    return {"wie": "browser", "html": "<html/>", "cookies": cookies}


class TestWasGewertetWird:
    @pytest.mark.parametrize("name", [
        "_ga", "_ga_7XKLM2P", "_gid", "_gcl_au", "__utma",
        "_fbp", "IDE", "test_cookie", "_hjSessionUser_123",
        "_clck", "_pk_id.1.abcd", "bcookie", "ttwid",
    ])
    def test_ein_verfolger_wird_erkannt(self, name):
        """Verglichen wird auf **Praefix**: Google haengt die
        Grundstuecksnummer an (`_ga_XXXXXXX`), Hotjar zaehlt durch. Wer auf
        Gleichheit prueft, findet die Haelfte nicht."""
        assert seitenbrowser.verfolger_darunter([{"name": name}]) == [name]

    @pytest.mark.parametrize("name", [
        "PHPSESSID", "csrftoken", "warenkorb", "cookie_consent",
        "sessionid", "XSRF-TOKEN", "wordpress_logged_in_abc",
    ])
    def test_was_notwendig_sein_koennte_wird_nicht_gewertet(self, name):
        """Der Preis fuer eine Aussage, die haelt: Sie sagt weniger. Ein
        Sitzungscookie **kann** notwendig sein, und das von aussen zu
        beurteilen waere geraten."""
        assert seitenbrowser.verfolger_darunter([{"name": name}]) == []

    def test_doppelte_werden_einmal_genannt(self):
        assert seitenbrowser.verfolger_darunter(
            [{"name": "_ga"}, {"name": "_ga"}]) == ["_ga"]

    def test_ein_kaputter_eintrag_reisst_nichts_mit(self):
        assert seitenbrowser.verfolger_darunter(
            [None, {}, {"name": None}, {"name": "_ga"}]) == ["_ga"]

    def test_ohne_cookies_ist_es_leer(self):
        assert seitenbrowser.verfolger_darunter([]) == []
        assert seitenbrowser.verfolger_darunter(None) == []


class TestDerBefund:
    def test_verfolger_vor_der_einwilligung_sind_ein_verstoss(self):
        befund = _cookies_vor_consent(_lauf([{"name": "_ga"},
                                             {"name": "PHPSESSID"}]))

        assert befund["collected"] is True
        assert befund["verstoss"] is True
        assert befund["verfolger"] == ["_ga"]
        assert befund["anzahl"] == 2

    def test_nur_notwendige_sind_keiner(self):
        befund = _cookies_vor_consent(_lauf([{"name": "PHPSESSID"}]))

        assert befund["collected"] is True
        assert befund["verstoss"] is False

    def test_ohne_browserlauf_wird_nichts_behauptet(self):
        """`collected: False` — nicht `verstoss: False`. Das waere die
        Behauptung, nachgesehen zu haben."""
        befund = _cookies_vor_consent(
            {"wie": "nicht", "grund": "AUDIT_BROWSER steht nicht auf true"})

        assert befund["collected"] is False
        assert "verstoss" not in befund
        assert "AUDIT_BROWSER" in befund["grund"]


class TestDerDeckel:
    def _fakten(self, cookies_block):
        return {"legal": {}, "tls": {}, "third_parties": {}, "consent": {},
                "cookies_vor_consent": cookies_block}

    def test_ein_verstoss_deckelt(self):
        blocker = detect_blockers(self._fakten(
            {"collected": True, "verstoss": True, "verfolger": ["_ga"]}))

        assert "cookies_ohne_consent" in blocker

    def test_ohne_verstoss_deckelt_nichts(self):
        blocker = detect_blockers(self._fakten(
            {"collected": True, "verstoss": False, "verfolger": []}))

        assert "cookies_ohne_consent" not in blocker

    def test_ohne_erhebung_deckelt_ebenfalls_nichts(self):
        """Die alte Lage, wenn kein Browser lief: genannt, nicht gemessen.
        Aus einer fehlenden Messung einen Deckel zu machen waere schlimmer
        als gar keine Messung."""
        blocker = detect_blockers(self._fakten({"collected": False}))

        assert "cookies_ohne_consent" not in blocker

    def test_und_ein_fehlender_block_ebenfalls_nicht(self):
        blocker = detect_blockers({"legal": {}, "tls": {},
                                    "third_parties": {}, "consent": {}})

        assert "cookies_ohne_consent" not in blocker
