# -*- coding: utf-8 -*-
"""Ein verlorener Lead hinterlaesst eine Spur (L-174, zweiter Teil).

**Der Befund.** Die fuenf Fremdaufrufe — Facebook, LinkedIn, Google,
Postkarte, Telefon — fingen jeden Fehler ab und antworteten mit
`{"ok": True}`. Der Systemdurchlauf vom 06.09.2026 hat sie als Familie des
P0 gemeldet, mit dem Zusatz: „Es kann Absicht sein."

**Beim Nachsehen war es das teilweise — und der eigentliche Schaden lag
woanders.** `webhook_log` wird **nur im Erfolgsfall** beschrieben: Die Zeile
steht mitten im geglueckten Pfad. Ein Aufruf, der scheiterte, stand nirgends
ausser in einer Protokollzeile im Server-Log. Der Innendienst sieht unter
„Fremdaufrufe" also nur die geglueckten — die Liste sagt „alles gut", waehrend
Interessenten aus bezahlten Anzeigen verloren gehen.

**Warum hier trotzdem 200 bleibt und nicht 5xx kommt.** Was diese Zweige
fangen, sind ueberwiegend **Formatfehler**: Ein Portal aendert den Aufbau
seiner Nachricht, `body.get(...)` greift ins Leere. Eine Wiederholung
scheitert dann genauso — sie erzeugt nur Last, und Facebook schaltet einen
Rueckruf ab, der dauerhaft Fehler liefert. Anders als bei Stripe (L-174) ist
die Wiederholung hier also **kein** Heilmittel; die Sichtbarkeit ist es.
"""
import pytest
from sqlalchemy import text


@pytest.fixture
def protokoll_leer(app):
    from database import SessionLocal

    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM webhook_log WHERE source LIKE 'test-%'"))
        db.commit()
    finally:
        db.close()


def _zeilen(quelle):
    from database import SessionLocal

    db = SessionLocal()
    try:
        return db.execute(text(
            "SELECT source, email, company, fehler FROM webhook_log "
            "WHERE source = :s"), {"s": quelle}).fetchall()
    finally:
        db.close()


def test_ein_gescheiterter_fremdaufruf_steht_im_protokoll(protokoll_leer):
    """**Der Kern.** Vorher stand er nirgends — jetzt sieht der Innendienst,
    dass ein Aufruf kam und nichts daraus wurde."""
    from routers.webhooks import protokolliere_fehlschlag

    protokolliere_fehlschlag("test-facebook", "Aufbau unerwartet: 'entry'")

    zeilen = _zeilen("test-facebook")
    assert len(zeilen) == 1
    assert zeilen[0].fehler, "der Grund gehoert dazu, nicht nur die Tatsache"
    assert "entry" in zeilen[0].fehler


def test_eine_geglueckte_zeile_traegt_keinen_fehler(protokoll_leer):
    """**Die Gegenprobe.** Sonst waere jede Zeile eine Fehlermeldung, und die
    Unterscheidung, um die es hier geht, waere keine."""
    from routers.webhooks import protokolliere_eingang

    protokolliere_eingang("test-telefon", "kunde@example.org", "Muster GmbH")

    zeilen = _zeilen("test-telefon")
    assert len(zeilen) == 1
    assert not zeilen[0].fehler


def test_das_protokoll_gibt_den_fehler_auch_heraus(client, mitarbeiter_headers,
                                                   protokoll_leer):
    """Eine Spalte, die niemand liest, ist keine Spur. Der Innendienstblick
    muss sie mitbringen — sonst ist es dieselbe Klasse wie der Befund selbst."""
    from routers.webhooks import protokolliere_fehlschlag

    protokolliere_fehlschlag("test-google", "Zeitueberschreitung")

    antwort = client.get("/api/webhooks/log", headers=mitarbeiter_headers)

    assert antwort.status_code == 200
    treffer = [z for z in antwort.json() if z.get("source") == "test-google"]
    assert treffer and treffer[0].get("fehler") == "Zeitueberschreitung"


def test_kein_fremdaufruf_verschluckt_seinen_fehler_noch():
    """**Waechter am Syntaxbaum.** Jeder `except`-Zweig der fuenf Aufrufe muss
    den Fehlschlag festhalten, bevor er antwortet. Der naechste Aufruf, den
    jemand hinzufuegt, ist von den Faellen oben nicht erfasst — und genau so
    ist diese Stelle beim ersten Mal entstanden.
    """
    import ast
    from pathlib import Path

    quelle = (Path(__file__).resolve().parent.parent
              / "routers" / "webhooks.py").read_text(encoding="utf-8")
    baum = ast.parse(quelle)

    gesucht = {"webhook_facebook", "webhook_linkedin", "webhook_google",
               "webhook_postkarte", "webhook_telefon"}
    ohne_spur = []
    for knoten in ast.walk(baum):
        if not isinstance(knoten, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if knoten.name not in gesucht:
            continue
        for zweig in [k for k in ast.walk(knoten)
                      if isinstance(k, ast.ExceptHandler)]:
            aufrufe = {getattr(a.func, "id", "") for a in ast.walk(zweig)
                       if isinstance(a, ast.Call)}
            if "protokolliere_fehlschlag" not in aufrufe:
                ohne_spur.append(f"{knoten.name}:{zweig.lineno}")

    assert not ohne_spur, (
        f"Diese Abfangzweige antworten, ohne den Fehlschlag festzuhalten: "
        f"{ohne_spur}. Ein verlorener Lead muss eine Spur hinterlassen.")
