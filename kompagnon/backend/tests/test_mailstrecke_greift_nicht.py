"""Die Mailstrecke greift heute für keinen Lead-Weg — **absichtlich** (L-62).

**Der Befund, am 21.08.2026 beim Schliessen von L-59 gemessen.**
`AUTO_SEQUENCE_SOURCES` in `routers/leads.py` entscheidet, wer nach dem
Anlegen automatisch eine E-Mail-Strecke bekommt. Fünf der acht Werte werden
**nirgends geschrieben**: `landing_page`, `llm_landing`, `webhook_facebook`,
`webhook_linkedin`, `webhook_google`. Die Webhooks schreiben `facebook`,
`linkedin`, `google`, `postkarte`, `telefon`.

Und selbst `postkarte`, das in beiden Listen steht, greift nicht:
`_upsert_lead` schreibt mit rohem SQL und läuft an `create_lead` vorbei — dem
einzigen Ort, an dem die Liste überhaupt gelesen wird.

**Warum dieser Test die Lücke festhält, statt sie zu schliessen.** Die Listen
anzugleichen hiesse, ab dem nächsten Deploy Betrieben Mails zu schicken, die
heute keine bekommen — darunter Kaltakquise. Das berührt die Rechtsgrundlage
aus L-59 und ist Davids Entscheidung, keine Aufräumarbeit.

**Wozu er dann gut ist:** Er verhindert, dass jemand die Listen beim
Aufräumen „in Ordnung bringt" und damit unbemerkt einen Massenversand
auslöst. Wird er rot, ist das kein Fehler — es ist die Frage, ob die
Entscheidung gefallen ist. Wer ihn anpasst, hat sie getroffen.
"""
import re

import pytest


def _quelle(name: str) -> str:
    import pathlib

    return (pathlib.Path(__file__).resolve().parent.parent / name).read_text(encoding="utf-8")


def ausloeser() -> set:
    """Die Werte, bei denen `create_lead` eine Strecke startet."""
    treffer = re.search(r"AUTO_SEQUENCE_SOURCES = \{(.*?)\}", _quelle("routers/leads.py"), re.S)
    assert treffer, "AUTO_SEQUENCE_SOURCES nicht gefunden — hat sich der Aufbau geaendert?"
    return set(re.findall(r'"([a-z_]+)"', treffer.group(1)))


def webhook_werte() -> set:
    """Die Herkunftswerte, die die Webhooks tatsaechlich schreiben."""
    quelle = _quelle("routers/webhooks.py")
    aufrufe = re.findall(r'_upsert_lead\(\s*["\']([a-z_]+)["\']', quelle)
    assert aufrufe, "keine _upsert_lead-Aufrufe gefunden"
    return set(aufrufe)


def test_fuenf_ausloeser_werden_nirgends_geschrieben():
    """Solange das gilt, laeuft fuer diese Wege keine Strecke."""
    ins_leere = ausloeser() - webhook_werte() - {
        # Diese beiden schreibt der Bestellweg bzw. das Widget wirklich.
        "stripe_checkout", "landing_audit",
    }

    assert ins_leere == {"landing_page", "llm_landing", "webhook_facebook",
                         "webhook_linkedin", "webhook_google"}, (
        f"Die Liste hat sich geaendert: {sorted(ins_leere)}. Wenn das Absicht "
        f"war, ist L-62 entschieden — dann gehoert dieser Test angepasst und "
        f"die Entscheidung in die Lueckenliste.")


def test_die_webhooks_gehen_ohnehin_am_ausloeser_vorbei():
    """Der zweite Grund, aus dem nichts geschieht.

    `_upsert_lead` schreibt mit rohem SQL. Selbst ein Wert, der in beiden
    Listen steht — `postkarte` —, loest nichts aus, weil die Liste nur in
    `create_lead` gelesen wird.
    """
    quelle = _quelle("routers/webhooks.py")

    assert "AUTO_SEQUENCE_SOURCES" not in quelle
    assert "INSERT INTO leads" in quelle, (
        "Schreibt `_upsert_lead` nicht mehr mit rohem SQL, koennte die Strecke "
        "jetzt greifen — dann ist L-62 zu pruefen, bevor jemand deployt.")


@pytest.mark.parametrize("wert", ["postkarte", "telefon", "facebook",
                                  "linkedin", "google"])
def test_kein_webhook_weg_startet_heute_eine_strecke(wert):
    """Die Zusammenfassung des Befunds: Von fuenf Lead-Wegen bekommt kein
    einziger die automatische Strecke — und niemand merkt es, weil das
    Ausbleiben einer Mail nichts protokolliert."""
    quelle = _quelle("routers/webhooks.py")

    assert "start_sequence" not in quelle and "sequence" not in quelle.lower(), (
        f"Ein Webhook startet jetzt eine Strecke ({wert}?). Das ist die "
        f"Entscheidung aus L-62 — sie beruehrt die Rechtsgrundlage bei "
        f"Kaltakquise und gehoert vor dem Deploy geklaert.")
