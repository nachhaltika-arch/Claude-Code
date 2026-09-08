# -*- coding: utf-8 -*-
"""Ein mitkopiertes Leerzeichen darf keine Zahlung kosten (08.09.2026).

**Der Anlass.** Beim Kontowechsel auf WEBSPRINT werden sechs Stripe-Werte von
Hand aus dem Stripe-Dashboard nach Render kopiert. Ein Zeilenumbruch oder ein
Leerzeichen am Ende ist dabei der haeufigste Fehlgriff — und er ist unsichtbar,
weil ein Eingabefeld ihn nicht anzeigt.

**Warum das schlimmer ist als ein normaler Fehler.** `stripe_modus.modus_von`
trimmt intern, bevor es `sk_live_` prueft. Die Diagnose meldet also
*„Stripe laeuft im Modus live, wie fuer produktiv vorgesehen"* — waehrend
`stripe.api_key` den ungetrimmten Wert bekommt und **jede** Anfrage mit einem
Authentifizierungsfehler zurueckkommt. Eine Anzeige, die Entwarnung gibt,
waehrend die Sache kaputt ist, kostet mehr Zeit als gar keine Anzeige.

Bis heute trimmte genau **eine** von zwoelf Lesestellen (`shop.py`). Das war
der schlechteste aller Zustaende: Der Shop haette funktioniert und alles
andere nicht — also haette niemand den Schluessel verdaechtigt.
"""
import pathlib
import re

BACKEND = pathlib.Path(__file__).resolve().parent.parent

#: Ein `os.getenv` auf eine Stripe-Variable, dem **kein** `.strip()` folgt.
#: Der Blick geht bis zum Zeilenende, weil `.strip()` unmittelbar dahinter
#: steht, wenn es da ist.
OHNE_TRIMMEN = re.compile(
    r'getenv\(\s*"(?:SHOP_)?STRIPE_[A-Z_0-9]+"[^)]*\)(?!\s*\.strip\(\))')


def _quelldateien():
    for pfad in BACKEND.rglob("*.py"):
        teile = pfad.parts
        if "tests" in teile or "venv" in teile or "__pycache__" in teile:
            continue
        yield pfad


def _funde(text: str) -> list:
    return [t.group(0) for t in OHNE_TRIMMEN.finditer(text)]


def test_jede_stripe_variable_wird_getrimmt_gelesen():
    funde = []
    for pfad in _quelldateien():
        for treffer in _funde(pfad.read_text(encoding="utf-8")):
            funde.append(f"{pfad.relative_to(BACKEND)}: {treffer}")

    assert not funde, (
        "Diese Stripe-Variablen werden ohne .strip() gelesen — ein "
        "mitkopiertes Leerzeichen bricht sie stumm:\n  " + "\n  ".join(funde))


def test_der_pruefer_findet_eine_ungetrimmte_stelle():
    """Die positive Gegenprobe.

    Ohne sie waere der Test oben auch dann gruen, wenn der Ausdruck gar
    nichts mehr trifft — etwa weil jemand die Schreibweise geaendert hat.
    """
    schlecht = 'stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")'
    assert len(_funde(schlecht)) == 1


def test_der_pruefer_laesst_eine_getrimmte_stelle_in_ruhe():
    gut = 'stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "").strip()'
    assert _funde(gut) == []


def test_der_pruefer_greift_nur_bei_stripe():
    # Eine Regel, die jede Umgebungsvariable erfasst, waere nicht mehr
    # durchsetzbar — und wuerde beim naechsten unbeteiligten Fund abgeschaltet.
    assert _funde('os.getenv("BREVO_API_KEY", "")') == []
