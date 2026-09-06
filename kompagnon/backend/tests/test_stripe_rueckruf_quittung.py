# -*- coding: utf-8 -*-
"""Was Stripe als Antwort bekommt, wenn die Verarbeitung scheitert (L-174).

**Der Befund vom 06.09.2026** (zweiter Systemdurchlauf, P0). `stripe_webhook`
fing an zwei Stellen jeden Fehler ab und antwortete trotzdem mit **200** —
`{"status": "error_logged"}`. Ein Rueckruf von aussen wertet 200 als
*verarbeitet* und liefert **nie wieder**. Scheitert die Verarbeitung, ist der
Vorgang endgueltig weg: Die Zahlung ist gebucht, das Projekt entsteht nicht,
und niemand erfaehrt es ausser einer Protokollzeile.

**Warum eine Wiederholung hier gefahrlos ist — nachgesehen, nicht vermutet.**
`_handle_successful_payment` traegt einen Idempotenz-Guard: Es sucht einen Lead
mit der Sitzungskennung in `notes` und bricht ab, wenn er existiert. Und der
**einzige** `db.commit()` des Hauptpfads steht am Ende von Schritt 3; alles
danach — Sequenz, Auftragsbestaetigung, Willkommensmail — faengt seine Fehler
selbst ab und wirft nicht nach oben. Wenn der aeussere Abfangzweig also
greift, ist **nichts** geschrieben, und die Wiederholung faengt sauber von
vorn an.

**Das Haus kennt die Regel schon** und befolgt sie eine Ebene hoeher: Fehlt
`STRIPE_WEBHOOK_SECRET`, antwortet derselbe Endpunkt mit **503** — „damit
Stripe Retry macht und der Fehler sichtbar bleibt". Nur die beiden
Verarbeitungszweige darunter taten es nicht.
"""
import json

import pytest


@pytest.fixture
def stripe_bereit(monkeypatch):
    """Ein Webhook mit gueltiger Signatur — die Pruefung selbst ist nicht der
    Gegenstand dieses Tests (dafuer gibt es `test_webhook_signaturen.py`)."""
    import routers.payments as p

    monkeypatch.setattr(p, "WEBHOOK_SECRET", "geheim", raising=False)
    return p


def _ereignis(monkeypatch, p, metadata):
    """`construct_event` durch eine feste Antwort ersetzen."""
    ereignis = {
        "type": "checkout.session.completed",
        "data": {"object": {"id": "cs_test_l174", "metadata": metadata,
                            "amount_total": 940100}},
    }
    monkeypatch.setattr(p.stripe.Webhook, "construct_event",
                        lambda *a, **k: ereignis)
    return ereignis


def test_scheitert_die_zahlungsverarbeitung_bekommt_stripe_einen_fehler(
        client, monkeypatch, stripe_bereit):
    """**Der Kern von L-174.** Vorher: 200 und der Vorgang ist weg. Jetzt: 5xx,
    Stripe wiederholt bis zu drei Tage, und der Fehlschlag steht sichtbar im
    Stripe-Protokoll statt nur in unserem Log."""
    p = stripe_bereit
    _ereignis(monkeypatch, p, {"customer_email": "kunde@example.org"})

    def kracht(*a, **k):
        raise RuntimeError("Datenbank weg")

    monkeypatch.setattr(p, "_handle_successful_payment", kracht)

    antwort = client.post("/api/payments/webhook", content=b"{}",
                          headers={"stripe-signature": "t=1,v1=egal"})

    assert antwort.status_code >= 500, (
        "Stripe wertet 200 als verarbeitet und liefert nie wieder — "
        "eine gescheiterte Verarbeitung muss 5xx bekommen")


def test_scheitert_der_abo_einzug_bekommt_stripe_ebenfalls_einen_fehler(
        client, monkeypatch, stripe_bereit):
    """Die zweite Stelle. Ein nicht vermerkter Einzug heisst: Stripe bucht ab,
    und bei uns steht der Vertrag weiter auf Rechnung."""
    p = stripe_bereit
    _ereignis(monkeypatch, p, {"abo_produkt": "ABO-PRO"})

    def kracht(*a, **k):
        raise RuntimeError("Vertrag nicht gefunden")

    monkeypatch.setattr(p, "_abo_einzug_eingerichtet", kracht)

    antwort = client.post("/api/payments/webhook", content=b"{}",
                          headers={"stripe-signature": "t=1,v1=egal"})

    assert antwort.status_code >= 500


def test_ein_gelungener_lauf_wird_weiter_mit_200_quittiert(
        client, monkeypatch, stripe_bereit):
    """**Die Gegenprobe, ohne die der Test nichts wert waere.** Ein Endpunkt,
    der immer 5xx sagt, besteht die beiden Tests oben auch — und Stripe
    wiederholte dann jeden erfolgreichen Vorgang, bis er aufgibt."""
    p = stripe_bereit
    _ereignis(monkeypatch, p, {"customer_email": "kunde@example.org"})
    monkeypatch.setattr(p, "_handle_successful_payment", lambda *a, **k: None)

    antwort = client.post("/api/payments/webhook", content=b"{}",
                          headers={"stripe-signature": "t=1,v1=egal"})

    assert antwort.status_code == 200
    assert antwort.json().get("status") == "ok"


def test_kein_abfangzweig_gibt_eine_antwort_zurueck():
    """**Ein Waechter am Syntaxbaum, nicht an Zeichenketten.** Die beiden
    Faelle oben pruefen die zwei Stellen, die es heute gibt; der naechste
    Zweig, den jemand hinzufuegt, ist von ihnen nicht erfasst — und genau so
    ist die Stelle beim ersten Mal entstanden.

    **Warum nicht `"error_logged" not in quelle`.** Genau so stand dieser Test
    im ersten Wurf, und er wurde rot: Die Zeichenkette steht jetzt im
    **Kommentar** daneben, der erklaert, was hier frueher stand. Ein Waechter,
    der Prosa mitzaehlt, zwingt den naechsten dazu, die Geschichte nicht
    aufzuschreiben. `ast` kennt keine Kommentare — er sieht nur, was laeuft.

    **Die Regel:** Ein `except`-Zweig in diesem Router darf kein Woerterbuch
    zurueckgeben. Ein `return {...}` aus einem Abfangzweig ist eine Antwort
    mit **HTTP 200**, ganz gleich, was darin steht — und ein Rueckruf von
    aussen liest daraus „verarbeitet" und liefert nie wieder. Wer dort
    antworten will, wirft eine `HTTPException`.
    """
    import ast
    from pathlib import Path

    quelle = (Path(__file__).resolve().parent.parent
              / "routers" / "payments.py").read_text(encoding="utf-8")

    treffer = [
        f"Zeile {k.lineno}: {ast.unparse(k)[:60]}"
        for knoten in ast.walk(ast.parse(quelle))
        if isinstance(knoten, ast.ExceptHandler)
        for k in ast.walk(knoten)
        if isinstance(k, ast.Return) and isinstance(k.value, ast.Dict)
    ]

    assert not treffer, (
        "Ein Abfangzweig quittiert einen Fehlschlag mit einer Antwort (HTTP "
        f"200). Bei einem Rueckruf von aussen heisst das: nie wieder "
        f"geliefert. {treffer}")
