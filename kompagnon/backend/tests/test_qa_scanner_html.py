# -*- coding: utf-8 -*-
"""Der QA-Scanner misst das HTML, das die Erhebung schon hat (L-155).

**Der Anlass (04.09.2026).** `audit_runner._run_qa_scanner` uebergab dem
Scanner nur die **Adresse**; der lud die Seite mit `httpx` ein zweites Mal und
fuehrte kein JavaScript aus. Das gerenderte HTML aus dem Browserlauf (L-107,
seit 26.08. produktiv) erreichte ihn nie.

**Gefaehrlich war die Wechselwirkung.** Nach einem geglueckten Browserlauf
faellt `clientseitig` bewusst auf falsch zurueck, damit die inhaltsabhaengigen
Kriterien wieder zaehlen duerfen — und damit greift `nur_geruest` nicht mehr,
das sie vorher aus Zaehler und Nenner genommen hat. Fuer eine im Browser
aufgebaute Seite hielt der Bericht die Messung also fuer gueltig, obwohl der
Scanner nur die leere Huelle gesehen hatte.

Der Test faehrt den Beweis ueber eine **nicht aufloesbare Adresse**: Wer
trotzdem laedt, bekommt einen Fehler statt Messwerte.
"""
import asyncio

import pytest

from services.qa_scanner import run_full_qa

UNERREICHBAR = "https://diese-adresse-gibt-es-nicht.invalid"

GERENDERT = """<html lang="de"><head>
  <title>Heizung Bochum — Muster GmbH</title>
  <meta name="description" content="Waermepumpe und Bad aus einer Hand in Bochum.">
  <meta name="viewport" content="width=device-width">
</head><body>
  <h1>Waermepumpe in Bochum</h1><h2>Leistungen</h2>
  <img src="werkstatt.jpg" alt="Unsere Werkstatt">
  <img src="team.jpg" alt="Das Team">
</body></html>"""


def test_mit_uebergebenem_html_wird_die_seite_nicht_erneut_geladen():
    """Der Beweis: Die Adresse ist nicht aufloesbar. Kaeme trotzdem ein
    Ladeversuch, stuende hier ein Fehler statt einer Messung."""
    ergebnis = asyncio.run(run_full_qa(UNERREICHBAR, html=GERENDERT))

    assert "error" not in ergebnis
    assert ergebnis["checks"]["title_vorhanden"] is True
    assert ergebnis["checks"]["h1_genau_eins"] is True


def test_das_uebergebene_html_ist_die_messgrundlage():
    """Genau der Fall aus dem Eintrag: Die Huelle haette null Bilder, das
    gerenderte Dokument hat zwei."""
    ergebnis = asyncio.run(run_full_qa(UNERREICHBAR, html=GERENDERT))

    assert ergebnis["checks"]["bilder_inhalt"] == 2
    assert ergebnis["checks"]["alt_texte_quote"] == 100


def test_ohne_html_bleibt_es_beim_eigenen_ladeversuch():
    """Die alte Bauart bleibt erhalten — der Scanner wird auch ausserhalb der
    Erhebung aufgerufen und muss dort weiter selbst laden koennen."""
    ergebnis = asyncio.run(run_full_qa(UNERREICHBAR))

    assert "error" in ergebnis
    assert ergebnis["checks"] == {}


def test_leeres_html_gilt_nicht_als_uebergabe():
    """Ein leerer String ist keine Messgrundlage — dann soll der Scanner
    laden wie bisher, statt eine leere Seite zu vermessen."""
    ergebnis = asyncio.run(run_full_qa(UNERREICHBAR, html=""))

    assert "error" in ergebnis


# ── Der Weg durch den Runner ──────────────────────────────────────────

def test_der_runner_reicht_das_gerenderte_html_durch(monkeypatch):
    """Die Uebergabe nuetzt nichts, wenn die Erhebung sie nicht benutzt —
    das waere die sechste Wiederholung von „gebaut, nicht angeschlossen"."""
    from services import audit_runner
    import services.qa_scanner as scanner

    gesehen = {}

    async def _merke(url, company="", trade="", html=""):
        gesehen["html"] = html
        return {"checks": {"title_vorhanden": True}}

    monkeypatch.setattr(scanner, "run_full_qa", _merke)
    asyncio.run(audit_runner._run_qa_scanner(
        "https://muster.de", "Muster", "Heizung", html=GERENDERT))

    assert gesehen["html"] == GERENDERT


def test_die_uebergabe_ist_verpflichtend():
    """Ohne benanntes `html` bricht der Aufruf ab, statt still selbst zu
    laden. Eine vergessene Aufrufstelle soll auffallen."""
    from services import audit_runner

    with pytest.raises(TypeError):
        asyncio.run(audit_runner._run_qa_scanner("https://muster.de", "", ""))
