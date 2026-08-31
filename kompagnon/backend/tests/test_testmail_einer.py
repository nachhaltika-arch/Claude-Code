"""Es gibt genau **einen** Weg, eine Testmail zu verschicken (L-105).

**Der Befund vom 31.08.2026.** Es gab zwei:

* `POST /api/automations/test-email?recipient=…` — verschickt wirklich, wird
  von der Einstellungsseite gerufen.
* `POST /api/admin/settings/test-email` — tat **nichts** und antwortete
  „Test-E-Mail wird gesendet (nicht implementiert)". Gerufen hat ihn niemand.

Ein zweiter Weg, der nur so tut, ist schlimmer als kein zweiter: Wer ihn
findet, haelt den Versand fuer angestossen und sucht den Fehler danach beim
Mailversand — oder beim Empfaenger.

**Warum ein Waechter und keine blosse Loeschung.** Genau dieser Fall ist im
Bestand schon einmal vorgekommen (`POST /{id}/abnahme`, am 26.08.2026
entfernt, mit demselben Muster gesichert): Ein Platzhalter kommt zurueck, weil
jemand die Luecke sieht und sie „schnell" fuellt — mit einer Antwort statt mit
einer Handlung.

**Gemessen wird ueber `openapi()`, nicht ueber `app.routes`.** Letzteres kennt
unter Starlette 1.4 nur die oberste Ebene; eine Abwesenheits-Zusicherung
darauf ist immer erfuellt. Daneben steht die **positive** Gegenprobe: Der
arbeitende Weg muss da sein, sonst prueft dieser Test einen leeren Suchbereich.
"""
import main

PLATZHALTER = "/api/admin/settings/test-email"
ARBEITEND = "/api/automations/test-email"


def _pfade():
    return main.app.openapi()["paths"]


def test_der_platzhalter_ist_nicht_zurueckgekommen():
    assert PLATZHALTER not in _pfade(), (
        "Der Platzhalter ist wieder da. Er antwortet, ohne zu handeln — wenn "
        "hier ein Endpunkt stehen soll, muss er eine Mail verschicken."
    )


def test_und_der_arbeitende_weg_ist_noch_da():
    """Die positive Zusicherung neben der Abwesenheit.

    Ohne sie waere der Test oben auch dann gruen, wenn **beide** Wege
    verschwinden — und dann gaebe es gar keine Testmail mehr.
    """
    pfade = _pfade()
    assert ARBEITEND in pfade, "der arbeitende Weg fehlt"
    assert "post" in pfade[ARBEITEND]


def test_es_gibt_keinen_dritten_weg():
    """Kein weiterer Pfad, der nach Testmail aussieht.

    Zwei waren schon einer zu viel; die naechste Verdopplung soll auffallen,
    bevor jemand den falschen findet.
    """
    treffer = sorted(p for p in _pfade() if "test-email" in p or "test-mail" in p)
    assert treffer == [ARBEITEND], f"unerwartete Testmail-Pfade: {treffer}"
