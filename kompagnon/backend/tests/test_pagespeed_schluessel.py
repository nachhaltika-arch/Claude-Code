"""Wer den PageSpeed-Schlüssel liest — und unter welchem Namen.

In Render heißt die Variable ``PAGESPEED_API_KEY``, im Code hieß sie
``GOOGLE_PAGESPEED_API_KEY``. Am 11.08. wurde das in
``services/audit_pagespeed.py`` repariert, indem dort beide Schreibweisen
gelten. Sieben weitere Stellen lasen weiter allein den langen Namen und sahen
den gesetzten Schlüssel deshalb nicht.

Der Schaden ist leise: PageSpeed v5 antwortet auch ohne Schlüssel, nur mit
einem winzigen Kontingent. Es scheitert also nichts — die Messung fällt nur
unter Last aus, und die Betriebsdiagnose meldete derweil „gesetzt".
"""
import io
import tokenize
from pathlib import Path

from services import audit_pagespeed


# ── Die Auflösung selbst ──────────────────────────────────────────────

def test_der_lange_name_gilt(monkeypatch):
    # Arrange
    monkeypatch.setenv("GOOGLE_PAGESPEED_API_KEY", "lang")
    monkeypatch.delenv("PAGESPEED_API_KEY", raising=False)

    # Act / Assert
    assert audit_pagespeed.api_key() == "lang"


def test_der_name_aus_render_gilt_ebenso(monkeypatch):
    """Der Name, unter dem der Schlüssel tatsächlich in Render steht."""
    # Arrange
    monkeypatch.delenv("GOOGLE_PAGESPEED_API_KEY", raising=False)
    monkeypatch.setenv("PAGESPEED_API_KEY", "kurz")

    # Act / Assert
    assert audit_pagespeed.api_key() == "kurz"


def test_ohne_schluessel_bleibt_es_beim_leeren_text(monkeypatch):
    # Arrange
    monkeypatch.delenv("GOOGLE_PAGESPEED_API_KEY", raising=False)
    monkeypatch.delenv("PAGESPEED_API_KEY", raising=False)

    # Act / Assert — kein None, die Aufrufer prüfen auf Wahrheitswert
    assert audit_pagespeed.api_key() == ""


# ── Und alle, die ihn brauchen ────────────────────────────────────────

# **Warum dieser Teil am 24.08.2026 umgeschrieben wurde (L-98).** Er prüfte
# vorher, ob jedes Modul den Namen ``pagespeed_api_key`` aus derselben Stelle
# importiert. Das war eine Aussage über einen *Bezeichner*, nicht über das
# Verhalten — und sie hat drei Dinge verfehlt:
#
# * Sie hielt vier tote Importe am Leben. ``routers/leads.py``,
#   ``routers/projects.py``, ``automations/scheduler.py`` und zwei weitere
#   importierten den Namen und benutzten ihn nirgends; entfernen hätte den
#   Wächter rot gemacht.
# * Sie sah nicht, **wohin** der Schlüssel danach ging. Sechs Stellen hängten
#   ihn an die URL, wo ``httpx`` ihn ins Protokoll schrieb.
# * Ihre Liste war handgepflegt und unvollständig: ``lead_enrichment`` und
#   ``projects_anlegen`` bauten die Adresse per f-String zusammen und kamen in
#   keiner Suche nach ``params["key"]`` vor.
#
# Dieselbe Klasse wie L-96: ein Wächter, der misst, aber nicht das, was er zu
# messen vorgibt. Jetzt wird der Quelltext selbst gelesen, und die Liste der
# geprüften Dateien fällt dabei ab, statt gepflegt zu werden.

BACKEND = Path(__file__).resolve().parent.parent

#: Wo der Schlüssel hingehört — und die einzige Stelle, die ihn kennt.
EINE_STELLE = "services/audit_pagespeed.py"

#: Wer PageSpeed überhaupt aufruft. Nicht gepflegt, sondern gefunden.
PSI_MERKMALE = ("pagespeedonline", "runPagespeed", "PSI_ENDPOINT")

#: Formen, in denen der Schlüssel in einer URL landet.
SCHLUESSEL_IN_URL = (
    'params["key"]',
    "params['key']",
    '"key": api_key',
    '"key": pagespeed',
    "&key=",
    "?key=",
)


def _quelldateien():
    """Jede Backend-Quelle — ohne venv, ohne Tests, ohne Fremdcode."""
    for pfad in BACKEND.rglob("*.py"):
        teile = pfad.relative_to(BACKEND).parts
        if "venv" in teile or "tests" in teile or "__pycache__" in teile:
            continue
        yield pfad


def _codezeilen(text: str) -> str:
    """Nur, was ausgeführt wird — ohne Kommentare und Dokumentationsblöcke.

    Ohne diesen Schnitt meldete der Wächter seine eigene Doku: Sowohl
    ``audit_pagespeed`` als auch ``protokoll_schwaerzung`` *beschreiben* den
    Befund von L-98 und zitieren dabei die verräterische URL. Eine
    Ausnahmeliste dafür wäre wieder handgepflegt gewesen — und handgepflegte
    Listen sind genau der Fehler, den dieser Wächter ersetzt.

    Einzeilige Zeichenketten bleiben stehen: Dort steckt der f-String-Fall
    (``f"&key={api_key}"``), der zwei der sechs Stellen versteckt hat. Ein
    dreifach zitierter Block mit einem echten Aufruf darin würde durchrutschen
    — dafür gibt es keinen Fall, und die Alternative wäre, die eigene Doku
    dauerhaft als Befund zu melden.
    """
    stuecke = []
    for zeichen in tokenize.generate_tokens(io.StringIO(text).readline):
        if zeichen.type == tokenize.COMMENT:
            continue
        roh = zeichen.string.lstrip("rbfuRBFU")
        if zeichen.type == tokenize.STRING and roh[:3] in ('"""', "'''"):
            continue
        stuecke.append(zeichen.string)
    return "\n".join(stuecke)


def _psi_dateien():
    for pfad in _quelldateien():
        code = _codezeilen(pfad.read_text(encoding="utf-8"))
        if any(m in code for m in PSI_MERKMALE):
            yield pfad, code


def test_es_gibt_ueberhaupt_psi_aufrufer_zu_pruefen():
    """Ein Wächter, der nichts findet, ist grün und wertlos."""
    # Act
    gefunden = list(_psi_dateien())

    # Assert — am 24.08.2026 waren es sieben Dateien; unter drei stimmt der
    # Suchbegriff nicht mehr, nicht der Code.
    assert len(gefunden) >= 3, [p.name for p, _ in gefunden]


def test_kein_aufrufer_haengt_den_schluessel_an_die_url():
    """Der eigentliche Befund von L-98 — und der, der sechsmal vorkam."""
    # Act
    schuldige = []
    for pfad, text in _psi_dateien():
        rel = pfad.relative_to(BACKEND).as_posix()
        for form in SCHLUESSEL_IN_URL:
            if form in text:
                schuldige.append(f"{rel}: {form}")

    # Assert
    assert not schuldige, (
        "Schlüssel steht wieder in der URL — httpx protokolliert sie "
        f"vollständig (L-98): {schuldige}"
    )


def test_jeder_aufrufer_holt_die_kopfzeile_an_derselben_stelle():
    """Keine zweite Auflösung im Code — sonst driftet sie wieder auseinander."""
    # Act
    ohne = [
        pfad.relative_to(BACKEND).as_posix()
        for pfad, text in _psi_dateien()
        if pfad.relative_to(BACKEND).as_posix() != EINE_STELLE
        and "auth_headers" not in text
    ]

    # Assert
    assert not ohne, f"ruft PageSpeed ohne die gemeinsame Kopfzeile: {ohne}"


def test_die_kopfzeile_traegt_den_schluessel_aus_render(monkeypatch):
    """Der alte Fehler eine Ebene höher: In Render gesetzt, hier unsichtbar."""
    # Arrange — so, wie es produktiv steht
    monkeypatch.delenv("GOOGLE_PAGESPEED_API_KEY", raising=False)
    monkeypatch.setenv("PAGESPEED_API_KEY", "der-echte-schluessel")

    # Act / Assert
    assert audit_pagespeed.auth_headers() == {
        "X-Goog-Api-Key": "der-echte-schluessel"
    }
