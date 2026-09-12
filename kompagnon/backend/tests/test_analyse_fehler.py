# -*- coding: utf-8 -*-
"""Warum eine Analyse scheiterte — in der Sprache des Besuchers (L-184).

**Der Satz, der bisher stand**, lautete bei *jedem* Fehlschlag gleich:

    Die Seite war nicht erreichbar. Bitte die Adresse prüfen oder in ein
    paar Minuten erneut versuchen.

Bei einer Zeitüberschreitung unseres eigenen Laufs ist das falsch. Bei
`ConnectTimeout` — dem gemessenen Hauptfall aus L-183, der Hoster nimmt aus
dem Rechenzentrum Frankfurt keine Verbindung an — ist es **doppelt** falsch:
Die Seite läuft, die Adresse stimmt, und der Besucher wird losgeschickt,
einen Fehler zu suchen, den es bei ihm nicht gibt.

**Nur ein einziger Fall rechtfertigt „bitte die Adresse prüfen":** wenn der
Name sich nicht auflösen lässt. Dann ist es wirklich ein Tippfehler, und dann
ist der Hinweis hilfreich statt abwälzend.

**Die Rohmeldung bleibt drinnen.** Dem Besucher gegenüber ist Zurückhaltung
richtig — er soll nicht `ConnectTimeout` lesen. Deshalb geht nach draußen
nur ein Schlüssel, und der Text dazu steht im Widget. Die Meldung selbst
bleibt in `error_message` und in der Anfrageliste, wo sie hingehört.
"""
import re
from pathlib import Path

import pytest

from services.analyse_fehler import (ADRESSE_UNBEKANNT, NICHT_ERREICHBAR,
                                     UNBEKANNT, ZEITGRENZE, kategorie)


class TestAdresseUnbekannt:
    """Der einzige Fall, in dem der Besucher wirklich etwas prüfen kann."""

    @pytest.mark.parametrize("meldung", [
        "ConnectError: [Errno -2] Name or service not known",
        "ConnectError: [Errno 8] nodename nor servname provided",
        "gaierror: [Errno -5] No address associated with hostname",
        "ConnectError: getaddrinfo failed",
    ])
    def test_ein_nicht_aufloesbarer_name(self, meldung):
        assert kategorie(meldung) == ADRESSE_UNBEKANNT


class TestNichtErreichbar:
    """Der gemessene Hauptfall — L-183, der Zielhost sperrt uns aus."""

    @pytest.mark.parametrize("meldung", [
        "ConnectTimeout: ",
        "ConnectTimeout: timed out",
        "ConnectError: [Errno 111] Connection refused",
        "ConnectionError: Verbindung abgebrochen",
    ])
    def test_die_verbindung_kommt_nicht_zustande(self, meldung):
        assert kategorie(meldung) == NICHT_ERREICHBAR

    def test_connect_timeout_ohne_meldungstext(self):
        """`str()` einer httpx-Zeitüberschreitung ist oft leer — siehe L-165."""
        assert kategorie("ConnectTimeout:") == NICHT_ERREICHBAR


class TestZeitgrenze:
    def test_die_gesamtgrenze_des_audits(self):
        meldung = "Timeout: Audit konnte nicht in 240s abgeschlossen werden."
        assert kategorie(meldung) == ZEITGRENZE

    @pytest.mark.parametrize("meldung", [
        "ReadTimeout: ",
        "TimeoutError: ",
        "PoolTimeout: ",
    ])
    def test_die_lesegrenzen_zaehlen_auch_dazu(self, meldung):
        assert kategorie(meldung) == ZEITGRENZE


class TestUnbekannt:
    """Was nicht einzuordnen ist, bekommt keinen erfundenen Grund."""

    @pytest.mark.parametrize("meldung", [
        "KeyError: 'lighthouseResult'",
        "ValueError: irgendetwas",
        "",
        None,
    ])
    def test_ohne_zuordnung_bleibt_es_unbekannt(self, meldung):
        assert kategorie(meldung) == UNBEKANNT


class TestKeinRatenNachErwartung:
    """Die Reihenfolge der Prüfung darf das Ergebnis nicht verfälschen.

    `ConnectError` trägt **beide** Fälle: den Tippfehler und die Sperre. Wer
    nur auf den Typnamen sieht, ordnet die Hälfte falsch ein — deshalb
    entscheidet hier der Meldungstext, und der Test hält beide Richtungen
    nebeneinander.
    """

    def test_connect_error_mit_namensfehler_ist_adresse(self):
        assert kategorie("ConnectError: Name or service not known") == ADRESSE_UNBEKANNT

    def test_connect_error_ohne_namensfehler_ist_erreichbarkeit(self):
        assert kategorie("ConnectError: Connection refused") == NICHT_ERREICHBAR

    def test_gross_und_kleinschreibung_aendert_nichts(self):
        assert kategorie("connecttimeout: TIMED OUT") == NICHT_ERREICHBAR


class TestNurSchluesselNachDraussen:
    def test_die_rohmeldung_steht_in_keiner_kategorie(self):
        """Ein Schlüssel ist kein Durchreichen der Ausnahme."""
        for schluessel in ALLE:
            assert " " not in schluessel
            assert schluessel.islower()


ALLE = (ADRESSE_UNBEKANNT, NICHT_ERREICHBAR, ZEITGRENZE, UNBEKANNT)

WIDGET = (Path(__file__).resolve().parents[2]
          / "frontend" / "public" / "embed" / "audit-widget.html")


def _widget_block(quelle: str, grund: str):
    """Der **gelesene** Text zu genau diesem Schlüssel — oder ``None``.

    Zwei eigene Fehler stecken in dieser Funktion, beide beim ersten Anlauf
    gemacht und beide vom Wächter selbst aufgedeckt:

    **An der Wortgrenze, nicht am Teilstring.** ``split("unbekannt:")``
    landete mitten in ``adresse_unbekannt:``. Vier Schlüssel, von denen einer
    im anderen steckt, verzeihen keine Suche ohne Anker.

    **Zusammengesetzte Zeichenketten erst zusammensetzen.** Im Widget steht
    ``'… und melden ' + 'uns per E-Mail.'`` — „melden uns" kommt im Quelltext
    also gar nicht vor. Wer den Rohtext durchsucht, prüft die Formatierung
    und nicht die Aussage.
    """
    treffer = re.search(rf"(?:^|[\s{{,]){re.escape(grund)}:\s*(.*?)(?:^\s*\w+:|^\s*}};)",
                        quelle, re.S | re.M)
    if not treffer:
        return None
    return "".join(re.findall(r"'([^']*)'", treffer.group(1)))


class TestDreiListenDriftenNichtAuseinander:
    """Schlüssel stehen an drei Orten — Klassierer, Mail, Widget.

    Drei Listen desselben Inhalts laufen auseinander, sobald eine wächst.
    Fällt eine zurück, sieht niemand einen Fehler: Der Besucher bekommt den
    Rückfalltext, und der klingt plausibel. Genau diese Sorte hält kein Test
    auf, der nur eine Seite prüft.
    """

    def test_das_widget_kennt_jeden_grund(self):
        quelle = WIDGET.read_text(encoding="utf-8")
        fehlend = [g for g in ALLE if _widget_block(quelle, g) is None]
        assert fehlend == [], f"Im Widget fehlt ein Text für: {fehlend}"

    def test_die_mail_kennt_jeden_grund(self):
        from services.widget_report import FEHLSCHLAG_TEXTE
        fehlend = [g for g in ALLE if g not in FEHLSCHLAG_TEXTE]
        assert fehlend == [], f"In der Mail fehlt ein Text für: {fehlend}"

    def test_und_keine_der_listen_hat_einen_grund_zu_viel(self):
        """Die positive Gegenprobe: kein Text ohne Klassierer dahinter."""
        from services.widget_report import FEHLSCHLAG_TEXTE
        assert set(FEHLSCHLAG_TEXTE) == set(ALLE)

    def test_die_zusage_steht_in_beiden_oder_in_keinem(self):
        """„Wir melden uns" muss im Widget und in der Mail gleich fallen.

        Sagt das Widget eine Mail zu, die nicht kommt, ist das schlimmer als
        gar keine Zusage — der Besucher wartet dann zum zweiten Mal
        vergeblich.
        """
        from services.widget_report import FEHLSCHLAG_TEXTE
        quelle = WIDGET.read_text(encoding="utf-8")
        for grund in ALLE:
            block = _widget_block(quelle, grund)
            assert block is not None, f"kein Widget-Text für {grund}"
            im_widget = "melden uns" in block
            im_brief = "melden uns" in " ".join(FEHLSCHLAG_TEXTE[grund])
            assert im_widget == im_brief, (
                f"{grund}: Widget sagt {im_widget}, Mail sagt {im_brief}")
