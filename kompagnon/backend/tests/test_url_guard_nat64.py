# -*- coding: utf-8 -*-
"""Hinter NAT64 hielt der Adressschutz jede fremde Website fuer intern.

**Der Fund (26.08.2026, beim Durchlauf der Testreihe).**
`test_ratenbegrenzung` wurde ploetzlich rot: „Domain zeigt auf eine interne
Adresse". Die Pruefadresse `ganz-neu.de` loeste auf `64:ff9b::88f3:515c` auf.

Das ist keine interne Adresse, sondern **NAT64** (RFC 6052): Das Netz hat
kein IPv4, also verpackt der Aufloeser die echte IPv4 in die letzten 32 Bit
eines IPv6-Praefixes — `88f3:515c` ist `136.243.81.92`, ein Hetzner-Server.
Python setzt fuer dieses Praefix `is_reserved = True`, und `_is_public_ip`
lehnte deshalb ab.

**Warum das kein reines Testproblem ist.** Der Schutz urteilte ueber die
**Huelle** statt ueber das Ziel. In einem Netz mit DNS64 — Mobilfunk, viele
Firmennetze, dieser Entwicklungsrechner — haette die Analyse **jede**
Kundenwebsite abgelehnt, mit einer Begruendung, die das Gegenteil behauptet:
„zeigt auf eine interne Adresse". Wer das liest, sucht den Fehler beim
Kunden.

**Und es lockert nichts.** Die eingebettete Adresse wird nicht durchgewunken,
sondern **nach denselben Regeln** beurteilt wie jede IPv4. `64:ff9b::7f00:1`
traegt `127.0.0.1` — und bleibt gesperrt. Genau das prueft die zweite Klasse
hier, denn eine Ausnahme ohne Gegenprobe ist ein Loch mit Begruendung.
"""
import pytest

from services.url_guard import _is_public_ip
import ipaddress


def _ip(text):
    return ipaddress.ip_address(text)


class TestNat64WirdDurchschaut:
    def test_eine_echte_fremde_adresse_gilt_als_oeffentlich(self):
        """`64:ff9b::88f3:515c` traegt `136.243.81.92` — ein Server im Netz.

        Vorher: abgelehnt, weil Python das Praefix als `reserved` fuehrt.
        """
        assert _is_public_ip(_ip("64:ff9b::88f3:515c")) is True

    def test_auch_das_lokale_praefix_wird_gelesen(self):
        """RFC 6052 erlaubt neben `64:ff9b::/96` auch `64:ff9b:1::/48` fuer
        netzeigene Uebersetzer. Wer nur das erste kennt, sperrt im zweiten
        Netz wieder alles."""
        assert _is_public_ip(_ip("64:ff9b:1::88f3:515c")) is True


class TestEsBleibtEinSchutz:
    @pytest.mark.parametrize("adresse,gemeint", [
        ("64:ff9b::7f00:1", "127.0.0.1 — der eigene Rechner"),
        ("64:ff9b::a00:1", "10.0.0.1 — privates Netz"),
        ("64:ff9b::c0a8:1", "192.168.0.1 — Heimnetz"),
        ("64:ff9b::a9fe:a9fe", "169.254.169.254 — die Metadaten der Cloud"),
    ])
    def test_eine_verpackte_interne_adresse_bleibt_gesperrt(self, adresse,
                                                            gemeint):
        """Ohne diese Gegenprobe waere die Ausnahme ein Loch mit Begruendung:
        Wer `64:ff9b::a9fe:a9fe` abrufen darf, liest die Zugangsdaten des
        Servers aus dem Metadatendienst."""
        assert _is_public_ip(_ip(adresse)) is False, gemeint

    def test_und_gewoehnliche_adressen_urteilen_wie_bisher(self):
        assert _is_public_ip(_ip("127.0.0.1")) is False
        assert _is_public_ip(_ip("10.1.2.3")) is False
        assert _is_public_ip(_ip("136.243.81.92")) is True
        assert _is_public_ip(_ip("2606:4700:4700::1111")) is True
