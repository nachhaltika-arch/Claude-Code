# -*- coding: utf-8 -*-
"""Wer angerufen werden will, sagt es — und nur dann liegt eine Nummer da.

**Der Anlass (Wunsch David, 21.09.2026).** Das Widget fragt freiwillig nach
einer Rufnummer. Wer sie eintraegt, bekommt am selben Tag einen kurzen Anruf;
wer sie weglaesst, bekommt denselben Bericht per Mail.

**Was diese Datei festhaelt, ist die Reihenfolge der Pruefung.** Nicht die
Ziffernfolge entscheidet, sondern der Wunsch:

* Ein **Ja ohne Nummer** ist kein Fehler, sondern ein Nein. Wer den Haken
  setzt und das Feld leer laesst, darf daran keine Analyse verlieren — und
  eine Erlaubnis ohne erreichbare Nummer ist ohnehin gegenstandslos.
* Eine **Nummer ohne Ja** wird verworfen. Sie zu speichern waere eine
  Rufnummer auf Vorrat, und genau dafuer verlangt § 7 Abs. 2 Nr. 2 UWG die
  ausdrueckliche Einwilligung.

**Und eine zweite Zusicherung, die leicht verlorengeht:** Ohne Wunsch darf
auch **kein leeres** Merkmal nach Brevo gehen. Ein leeres `TELEFON` dort saehe
aus wie „Nummer angegeben, aber leer" — dieselbe Falle, die bei den
UTM-Merkmalen schon einmal stand.
"""
import pytest

from routers.widget import WidgetAuditRequest, _anrufwunsch
from services import widget_crm


def _nutzlast(**felder) -> WidgetAuditRequest:
    grund = {"email": "test@example.com", "website_url": "https://example.com"}
    return WidgetAuditRequest(**{**grund, **felder})


# ── Die Reihenfolge der Pruefung ──────────────────────────────────────

def test_nummer_mit_wunsch_wird_uebernommen_und_getrimmt():
    nummer, wunsch = _anrufwunsch(_nutzlast(telefon="  0170 1234567  ",
                                            anruf_gewuenscht=True))
    assert nummer == "0170 1234567"
    assert wunsch is True


def test_wunsch_ohne_nummer_wird_zum_nein_und_nicht_zum_fehler():
    """Der Fall, der das Formular kosten wuerde, wenn er ein Fehler waere."""
    nummer, wunsch = _anrufwunsch(_nutzlast(telefon="   ", anruf_gewuenscht=True))
    assert nummer == ""
    assert wunsch is False


def test_nummer_ohne_wunsch_wird_verworfen():
    """Eine Nummer ohne Erlaubnis ist eine Rufnummer auf Vorrat."""
    nummer, wunsch = _anrufwunsch(_nutzlast(telefon="0170 1234567",
                                            anruf_gewuenscht=False))
    assert nummer == ""
    assert wunsch is False


def test_ohne_angaben_steht_nichts_da():
    assert _anrufwunsch(_nutzlast()) == ("", False)


def test_eine_lange_nummer_passt_in_die_spalte():
    """`telefon` ist VARCHAR(64). Laenger darf nicht die Anfrage kippen."""
    nummer, wunsch = _anrufwunsch(_nutzlast(telefon="0" * 200,
                                            anruf_gewuenscht=True))
    assert len(nummer) == 64
    assert wunsch is True


# ── Der Weg nach Brevo ────────────────────────────────────────────────

class _BrevoAttrappe:
    """Faengt ab, was `uebertrage` an Brevo geben wuerde."""

    letzte_merkmale: dict = {}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def ensure_attributes(self, merkmale):
        type(self).letzte_merkmale = {}

    def create_contact(self, email, first_name, last_name, list_ids, attributes):
        type(self).letzte_merkmale = dict(attributes)


@pytest.fixture
def brevo_attrappe(monkeypatch):
    import services.brevo_service as echt

    monkeypatch.setattr(echt, "BrevoService", _BrevoAttrappe)
    _BrevoAttrappe.letzte_merkmale = {}
    return _BrevoAttrappe


def test_die_nummer_geht_als_merkmal_telefon_nach_brevo(brevo_attrappe):
    """Dort sieht David den Lead — eine Nummer nur in der eigenen Datenbank
    fuehrt zu keinem Anruf."""
    widget_crm.uebertrage("kunde@example.com", listen_id=5,
                          website="https://example.com", telefon="0651 9876543")

    assert brevo_attrappe.letzte_merkmale.get("TELEFON") == "0651 9876543"


def test_ohne_nummer_steht_kein_leeres_telefon_in_brevo(brevo_attrappe):
    widget_crm.uebertrage("kunde@example.com", listen_id=5,
                          website="https://example.com", telefon="")

    assert "TELEFON" not in brevo_attrappe.letzte_merkmale


def test_telefon_steht_in_der_merkmalsliste():
    """Sonst weist Brevo den **ganzen** Kontakt ab, nicht nur das Merkmal —
    `ensure_attributes` legt nur an, was hier steht."""
    assert ("TELEFON", "text") in widget_crm.MERKMALE
