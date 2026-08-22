"""Der Bestand schwach geschuetzter Routen — gemessen, nicht geschaetzt (L-67).

**Was hier festgehalten wird.** Am 22.08.2026 wurde jede Route unter `/api/`
an der **geladenen Anwendung** durchgegangen: 466 insgesamt, davon 369 mit
einer Rollen- oder Rechtepruefung, 46 mit nur „irgendwer ist angemeldet" und
51 ganz ohne Anmeldepruefung (die sind Gegenstand von L-51).

Die 46 sind **einzeln geprueft** und bleiben mit Grund:

| Bereich | Zahl | Grund |
|---|---|---|
| `academy` | 14 | Kundenweg. Jede Route filtert auf `current_user.id`; die Zertifikatsausstellung nimmt keine Nutzerkennung entgegen. |
| `portal` | 7 | Kundenweg. Fuenf nehmen **gar keine** Fremdkennung entgegen, zwei pruefen den eigenen Betrieb. |
| `auth` | 7 | Eigene Daten. Keine einzige nimmt eine Fremdkennung entgegen — sie koennen nur den Angemeldeten treffen. |
| `assistant` | 5 | Kundenweg aus dem Portal; die drei mit Kennung pruefen, die zwei ohne koennen nichts Fremdes treffen. |
| `projects` | 3 | `eigenes_projekt_pruefen` beziehungsweise Rollenzweig. |
| `leads` | 2 | Betriebs-Eigentum wird geprueft. |
| `audit` | 2 | `_audit_oder_404` — Einmal-Token **oder** Anmeldung; das ist der Berichtsweg des Kunden. |
| `geo-payments` | 2 | Seit dem 22.08. `eigenes_projekt_pruefen`. |
| `usercards` | 1 | `_check_kunde_access`. |
| `tickets` | 1 | filtert auf `current_user.email`. |
| `invoices` | 1 | filtert auf `current_user.email`. |
| `versand` | 1 | Ein Ja/Nein zum automatischen Versand, kein Kundendatum — siehe unten. |

**Warum diese Zahl bewacht wird.** Sie ist dreimal gewandert: von „166" ueber
„120" auf 85 und schliesslich 46 — und die ersten beiden Zahlen waren zu
hoch, weil eine Sperre am **Router** haengen kann, waehrend die Signatur
schwach aussieht. Ohne Wache waechst so ein Bestand mit jeder neuen Route
zurueck, und niemand merkt es, weil nichts rot wird.

Der Test scheitert bewusst auch, wenn die Zahl **faellt**: Dann ist etwas
geschlossen worden, und die Tabelle oben gehoert nachgezogen. Eine Zahl, die
niemand mehr nachfuehrt, ist keine Messung mehr.
"""
import importlib.util
import pathlib

import pytest


#: Stand vom 22.08.2026, an der geladenen Anwendung gemessen.
ERWARTET = 46

#: Wo die 46 liegen duerfen. Ein neuer Bereich ist ein Befund, keine Zahl.
ERLAUBTE_BEREICHE = {
    "academy", "portal", "auth", "assistant", "projects", "leads",
    "audit", "geo-payments", "usercards", "tickets", "invoices", "versand",
}


def _werkzeug():
    pfad = (pathlib.Path(__file__).resolve().parent.parent.parent.parent
            / "tools" / "schwacher-zugriffsschutz.py")
    if not pfad.exists():
        pytest.skip(f"Werkzeug nicht gefunden: {pfad}")
    spec = importlib.util.spec_from_file_location("wz", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _schwache_routen():
    wz = _werkzeug()
    from main import app

    heraus = []
    for route in wz.alle_routen(app):
        pfad = getattr(route, "path", "")
        if not pfad.startswith("/api/"):
            continue
        namen = wz.namen(route.dependant)
        if namen & wz.STARK or not (namen & wz.SCHWACH):
            continue
        heraus.append(pfad)
    return heraus


def test_der_bestand_ist_nicht_gewachsen():
    """Waechst er, ist eine neue Route ohne Rollenpruefung hinzugekommen."""
    schwach = _schwache_routen()

    assert len(schwach) <= ERWARTET, (
        f"{len(schwach)} statt {ERWARTET} schwach geschuetzte Routen. "
        f"Neu hinzugekommen und ungeprueft:\n  " + "\n  ".join(sorted(schwach)))


def test_und_die_zahl_stimmt_noch():
    """Faellt sie, gehoert die Tabelle im Kopf dieser Datei nachgezogen —
    sonst steht dort bald eine Begruendung fuer etwas, das es nicht mehr gibt.
    """
    schwach = _schwache_routen()

    assert len(schwach) == ERWARTET, (
        f"{len(schwach)} statt {ERWARTET}. Wurde etwas geschlossen? Dann "
        f"`ERWARTET` und die Tabelle im Kopf dieser Datei anpassen.")


def test_sie_liegen_nur_in_geprueften_bereichen():
    """Ein neuer Bereich ist ein Befund, keine Zahl."""
    bereiche = {p.split("/")[2] for p in _schwache_routen() if len(p.split("/")) > 2}

    assert bereiche <= ERLAUBTE_BEREICHE, (
        f"Ungeprueft: {sorted(bereiche - ERLAUBTE_BEREICHE)}")
