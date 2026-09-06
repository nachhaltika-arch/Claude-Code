# -*- coding: utf-8 -*-
"""Kein Dienst ruft sich selbst unter `localhost` (L-178).

**Der Fund vom 06.09.2026 — beim Nachpruefen des Systemdurchlaufs, nicht vom
Lauf gemeldet.** Der Durchlauf verwies die Stelle auf das **geschlossene**
L-156 („`BACKEND_URL` steht in keinem Blueprint"), und fuer `shop.py` stimmt
die Ablage: Dort steht seit dem 04.09. `_backend_adresse()` mit
`api_base_url()` als Rueckfall.

`routers/projects_anlegen.py` trug aber eine **zweite, halbe Fassung** davon,
und ihr Rueckfall war `http://localhost:8000`. Der Go-Live-Schritt ruft
`POST {backend_url}/api/audit/start` gegen sich selbst. `BACKEND_URL` steht
seit L-156 **bewusst** in keinem Blueprint, weil `services/base_urls.py`
die Frage beantwortet — produktiv ging der Aufruf also an localhost, `httpx`
warf, der `except` schrieb eine Warnung, und das **Abnahmeaudit entstand
nicht**. Zugesagt ist es im Angebot als „Abnahmeaudit mit schriftlichem
Protokoll".

**Ein Textabgleich, der auf einen geschlossenen Eintrag zeigt, ist kein
Urteil.** Haette ich die Ablage uebernommen, waere der Befund unter „schon
erledigt" verschwunden.
"""
import ast
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent


def _localhost_ruecfaelle(datei: Path):
    """`os.getenv("...URL", "http://localhost...")` — ein Rueckfall, der
    produktiv ins Leere zeigt."""
    baum = ast.parse(datei.read_text(encoding="utf-8"))
    treffer = []
    for k in ast.walk(baum):
        if not (isinstance(k, ast.Call) and isinstance(k.func, ast.Attribute)
                and k.func.attr == "getenv" and len(k.args) == 2):
            continue
        vorgabe = k.args[1]
        if (isinstance(vorgabe, ast.Constant) and isinstance(vorgabe.value, str)
                and ("localhost" in vorgabe.value or "127.0.0.1" in vorgabe.value)):
            treffer.append(f"{datei.name}:{k.lineno} {ast.unparse(k)[:70]}")
    return treffer


def test_der_go_live_schritt_ruft_nicht_mehr_localhost():
    """Der gemessene Fall."""
    assert not _localhost_ruecfaelle(BACKEND / "routers" / "projects_anlegen.py")


@pytest.mark.parametrize("datei", sorted(
    (BACKEND / "routers").glob("*.py")), ids=lambda p: p.name)
def test_kein_router_faellt_auf_localhost_zurueck(datei):
    """**Die Familie, nicht nur der Fall.** So ist die Stelle beim ersten Mal
    entstanden: als Kopie einer anderen, die es genauso machte. `shop.py` ist
    am 04.09. repariert worden, diese hier blieb stehen — ein Waechter ueber
    alle Router faengt die dritte."""
    assert not _localhost_ruecfaelle(datei)


def test_die_richtige_antwort_ist_self_base_url_und_nicht_api_base_url(monkeypatch):
    """**Beim Bauen korrigiert.** Mein erster Wurf verlangte hier
    `api_base_url()` — falsch, und die Funktion sagt es selbst: „Nicht fuer
    Aufrufe dieses Servers an sich selbst. Dafuer gibt es `self_base_url()`."

    Der Unterschied ist kein Feinschliff. `api_base_url()` nimmt den **Weg
    ueber das oeffentliche Netz** an die eigene Maschine; `self_base_url()`
    den internen Hostnamen samt `PORT`, den Render je Dienst selbst setzt.
    Genau diese Verwechslung steht in der Doku von `self_base_url` als
    Anlass — `leads.py` und `webhooks.py` hatten sie vor
    `projects_anlegen.py`.
    """
    from services.base_urls import self_base_url

    monkeypatch.setenv("RENDER_INTERNAL_HOSTNAME", "kompagnon-backend-fra")
    monkeypatch.setenv("PORT", "10000")

    assert self_base_url() == "http://kompagnon-backend-fra:10000", (
        "auf Render zaehlt der interne Name **mit Port** — ohne ihn geht die "
        "Anfrage auf 80, wo niemand hoert")


def test_der_go_live_schritt_benutzt_die_gemeinsame_ableitung():
    """Eine Reparatur, die nur `localhost` entfernt, koennte die naechste
    halbe Fassung sein. Dieser Test verlangt die **eine** Stelle."""
    quelle = (BACKEND / "routers" / "projects_anlegen.py").read_text(encoding="utf-8")

    assert "self_base_url" in quelle
    assert 'os.getenv(\n                        "BACKEND_URL"' not in quelle
