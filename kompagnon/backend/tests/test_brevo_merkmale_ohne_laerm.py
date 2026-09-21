# -*- coding: utf-8 -*-
"""Vorhandene Merkmale erzeugen keine Fehlerzeilen mehr.

**Der Fund vom 20.09.2026, aus dem Durchlauf und nicht aus einem Test.**
Der erste echte Lead nach dem Einrichten der Listen lief sauber durch — und
hinterliess dabei **neun** Zeilen auf ERROR-Ebene:

    services.brevo_service - ERROR - Brevo POST
    /contacts/attributes/normal/WEBSITE: HTTP 400 — Attribute name must be unique

Das ist der Normalfall. `ensure_attribute` faengt ihn seit jeher ab, aber
`_request` hat ihn eine Ebene tiefer bereits als Fehler protokolliert. Je
uebertragenem Kontakt neun rote Zeilen fuer „alles in Ordnung".

**Warum das mehr ist als Schoenheit.** Genau dieses Protokoll war vierzehn
Tage lang die einzige Stelle, an der der stille Brevo-Ausfall zu sehen
gewesen waere. Ein Protokoll, das im Normalbetrieb rot ist, macht den
echten Fehler unsichtbar — dieselbe Klasse wie ein Waechter, der immer
gruen ist, nur andersherum.

**Und billiger ist es auch:** ein Lesezugriff statt neun Schreibversuchen.
"""
import logging

import httpx
import pytest

from services.brevo_service import BrevoError, BrevoService

MERKMALE = (("WEBSITE", "text"), ("ANALYSE_SCORE", "float"),
            ("UTM_SOURCE", "text"))


def _service(handler):
    return BrevoService(api_key="test-key", transport=httpx.MockTransport(handler))


def test_vorhandene_merkmale_werden_nicht_noch_einmal_angelegt(caplog):
    versuche = []

    def handler(request):
        if request.method == "GET":
            return httpx.Response(200, json={"attributes": [
                {"name": "WEBSITE"}, {"name": "ANALYSE_SCORE"},
                {"name": "UTM_SOURCE"}]})
        versuche.append(str(request.url))
        return httpx.Response(400, json={"message": "Attribute name must be unique"})

    with caplog.at_level(logging.ERROR, logger="services.brevo_service"):
        with _service(handler) as brevo:
            brevo.ensure_attributes(MERKMALE)

    assert versuche == [], f"Es wurde trotzdem angelegt: {versuche}"
    assert not caplog.records, f"Fehlerzeilen im Normalfall: {caplog.text}"


def test_fehlende_merkmale_werden_angelegt(caplog):
    """Die positive Zusicherung daneben. Ohne sie waere ein
    `ensure_attributes`, das **nie** etwas anlegt, von einem richtigen nicht
    zu unterscheiden — und der erste Kontakt mit unbekanntem Merkmal wird
    von Brevo vollstaendig abgewiesen, nicht nur das Merkmal."""
    angelegt = []

    def handler(request):
        if request.method == "GET":
            return httpx.Response(200, json={"attributes": [{"name": "WEBSITE"}]})
        angelegt.append(request.url.path.rsplit("/", 1)[-1])
        return httpx.Response(201, json={})

    with _service(handler) as brevo:
        brevo.ensure_attributes(MERKMALE)

    assert angelegt == ["ANALYSE_SCORE", "UTM_SOURCE"]


def test_die_vorhandenen_werden_einmal_gelesen_nicht_je_merkmal():
    """Sonst waere aus neun Schreibversuchen nur neun Lesezugriffe geworden."""
    gelesen = []

    def handler(request):
        if request.method == "GET":
            gelesen.append(str(request.url))
            return httpx.Response(200, json={"attributes": []})
        return httpx.Response(201, json={})

    with _service(handler) as brevo:
        brevo.ensure_attributes(MERKMALE)

    assert len(gelesen) == 1, f"{len(gelesen)} Lesezugriffe statt einem"


def test_ein_echter_fehlschlag_bleibt_sichtbar(caplog):
    """Der Laerm verschwindet, die Meldung nicht. Ein Merkmal, das sich
    wirklich nicht anlegen laesst, muss eine Spur hinterlassen — sonst waere
    aus dem zu lauten Protokoll ein stummes geworden."""
    def handler(request):
        if request.method == "GET":
            return httpx.Response(200, json={"attributes": []})
        return httpx.Response(403, json={"message": "Not allowed"})

    with caplog.at_level(logging.WARNING, logger="services.brevo_service"):
        with _service(handler) as brevo:
            brevo.ensure_attributes(MERKMALE)

    assert caplog.records, "Ein echter Fehlschlag hinterlaesst keine Spur."
    assert "WEBSITE" in caplog.text


def test_ohne_lesbare_merkmalsliste_wird_es_nicht_still():
    """Antwortet der Lesezugriff mit einem Fehler, darf die Uebertragung
    nicht einfach ohne Merkmale weiterlaufen — dann wiese Brevo den ganzen
    Kontakt ab, und der Grund staende nirgends."""
    def handler(request):
        return httpx.Response(401, json={"message": "Key not found"})

    with _service(handler) as brevo:
        with pytest.raises(BrevoError):
            brevo.ensure_attributes(MERKMALE)
