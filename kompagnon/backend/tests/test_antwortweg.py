# -*- coding: utf-8 -*-
"""Eine Antwort auf unsere Mail muss irgendwo ankommen.

**Der Befund vom 27.08.2026.** Am 26.08. wurde der Posteingang gebaut:
`POST /api/posteingang/brevo/{secret}` nimmt Kundenmails entgegen, legt sie
als `Message` ab und meldet sie über die Glocke. Der Weg ist richtig gebaut
und vollständig getestet.

Nur führt keine Mail dorthin.

Jede ausgehende Mail trägt `From: KOMPAGNON <noreply@kompagnon.group>` und
**keinen** `Reply-To`. Wer im Mailprogramm auf „Antworten" klickt, schreibt
an `noreply@` — eine Adresse, die niemand liest. Der Text unter jeder
Nachricht sagt dabei wörtlich: „antworten Sie direkt auf diese E-Mail."

Das ist die Bauart, die in diesem Bestand am häufigsten vorkommt: gebaut,
aber nicht angeschlossen. Der Posteingang hätte nach dem MX-Eintrag
dagestanden und **nie etwas empfangen** — und niemand hätte es gemerkt, weil
Stille dort genau wie „keine Rückfragen" aussieht.

**Warum die Rückadresse aus der Umgebung kommt und nicht fest im Programm
steht.** Sie existiert erst, wenn David den MX-Eintrag gesetzt hat. Stünde
sie schon jetzt fest im Quelltext, gingen Antworten an eine Domain, die keine
Mail annimmt — der Kunde bekäme einen Unzustellbarkeitsbericht. Ohne die
Variable bleibt es beim heutigen Verhalten; das ist schlechter als das Ziel,
aber besser als ein Rückläufer.
"""
import pytest

from services import antwortadresse


@pytest.fixture()
def ohne_adresse(monkeypatch):
    monkeypatch.delenv(antwortadresse.SCHALTER, raising=False)


@pytest.fixture()
def mit_adresse(monkeypatch):
    monkeypatch.setenv(antwortadresse.SCHALTER, "posteingang@kompagnon.group")


# ── Die Adresse selbst ────────────────────────────────────────────────

def test_ohne_variable_gibt_es_keine_rueckadresse(ohne_adresse):
    assert antwortadresse.rueckadresse() == ""


def test_mit_variable_kommt_sie_heraus(mit_adresse):
    assert antwortadresse.rueckadresse() == "posteingang@kompagnon.group"


@pytest.mark.parametrize("murks", ["kein-at-zeichen", "@ohne-name.de",
                                   "zwei@@at.de", "   "])
def test_eine_unbrauchbare_adresse_wird_nicht_verschickt(monkeypatch, murks):
    """Lieber keine Rückadresse als eine kaputte.

    Ein `Reply-To`, das kein Mailprogramm versteht, lässt die Antwort
    irgendwo landen — und die Absicht sah dabei erfüllt aus.
    """
    monkeypatch.setenv(antwortadresse.SCHALTER, murks)
    assert antwortadresse.rueckadresse() == ""


# ── Der Weg durch Brevo ───────────────────────────────────────────────

def test_brevo_bekommt_die_rueckadresse(monkeypatch, mit_adresse):
    from services import brevo_mail

    monkeypatch.setenv("BREVO_API_KEY", "pytest-schluessel")
    gesehen = {}

    class _Antwort:
        status_code = 201

        @staticmethod
        def json():
            return {}

    def _post(url, json=None, headers=None, timeout=None):
        gesehen.update(json or {})
        return _Antwort()

    monkeypatch.setattr(brevo_mail.httpx, "post", _post)

    erfolg, _ = brevo_mail.send(to_email="chef@betrieb.de", subject="Hallo",
                                html_body="<p>Text</p>")

    assert erfolg is True
    assert gesehen.get("replyTo") == {"email": "posteingang@kompagnon.group"}


def test_ohne_rueckadresse_steht_das_feld_nicht_im_aufruf(
        monkeypatch, ohne_adresse):
    """Ein leeres `replyTo` wäre etwas anderes als gar keines — Brevo lehnt es ab."""
    from services import brevo_mail

    monkeypatch.setenv("BREVO_API_KEY", "pytest-schluessel")
    gesehen = {}

    class _Antwort:
        status_code = 201

        @staticmethod
        def json():
            return {}

    monkeypatch.setattr(brevo_mail.httpx, "post",
                        lambda url, json=None, headers=None, timeout=None:
                        (gesehen.update(json or {}), _Antwort())[1])

    brevo_mail.send(to_email="chef@betrieb.de", subject="Hallo",
                    html_body="<p>Text</p>")

    assert "replyTo" not in gesehen


# ── Der Weg durch SMTP ────────────────────────────────────────────────

def test_smtp_setzt_die_kopfzeile(mit_adresse):
    from services.email import _build_message

    nachricht = _build_message(subject="Hallo", sender="KOMPAGNON <noreply@x.de>",
                               to_email="chef@betrieb.de",
                               html_body="<p>Text</p>", text_body="",
                               attachments=None)

    assert nachricht["Reply-To"] == "posteingang@kompagnon.group"


def test_smtp_mit_anhang_setzt_sie_auch(mit_adresse):
    """Der Anhangzweig baut eine **andere** Nachricht.

    Genau an dieser Verzweigung ist am 26.08. schon einmal etwas verloren
    gegangen; zwei Zweige, eine Zusicherung.
    """
    from services.email import _build_message

    nachricht = _build_message(subject="Hallo", sender="KOMPAGNON <noreply@x.de>",
                               to_email="chef@betrieb.de",
                               html_body="<p>Text</p>", text_body="",
                               attachments=[("A.pdf", b"%PDF-1.4", "pdf")])

    assert nachricht["Reply-To"] == "posteingang@kompagnon.group"


def test_ohne_adresse_traegt_die_nachricht_keine_kopfzeile(ohne_adresse):
    from services.email import _build_message

    nachricht = _build_message(subject="Hallo", sender="KOMPAGNON <noreply@x.de>",
                               to_email="chef@betrieb.de",
                               html_body="<p>Text</p>", text_body="",
                               attachments=None)

    assert nachricht["Reply-To"] is None


# ── Was unter der Mail steht ──────────────────────────────────────────

def test_der_hinweis_verspricht_nur_was_eingerichtet_ist(ohne_adresse):
    """„Antworten Sie direkt auf diese E-Mail" — solange das nicht geht,
    soll es auch nicht dastehen."""
    from routers.messages import _email_wrapper

    text = _email_wrapper("Guten Tag", "Heizung Meier GmbH")

    assert "direkt auf diese E-Mail" not in text
    # Die Gegenprobe: Ein Weg zur Antwort wird trotzdem genannt.
    assert "Kundenportal" in text


def test_mit_eingerichtetem_posteingang_darf_es_dastehen(mit_adresse):
    from routers.messages import _email_wrapper

    text = _email_wrapper("Guten Tag", "Heizung Meier GmbH")

    assert "direkt auf diese E-Mail" in text
