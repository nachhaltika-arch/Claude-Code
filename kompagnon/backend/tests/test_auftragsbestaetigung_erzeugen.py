# -*- coding: utf-8 -*-
"""Die Auftragsbestaetigung wird **erzeugt**, nicht nur berechnet.

**Der Befund (27.08.2026, erster echter Testkauf).** Im Protokoll des ersten
echten Kaufs stand mitten in der sonst gelungenen Kette:

    Auftragsbestaetigung PDF Fehler: ParagraphStyle() got multiple values
    for keyword argument 'fontName'

Ein gewoehnlicher Python-Fehler — doppeltes Schluesselwort. Er tritt bei
**jedem** Aufruf auf. Damit ist seit dem Einbau der Funktion nie eine
Auftragsbestaetigung entstanden.

**Zwei Gruende, warum es niemand gesehen hat, und beide sind lehrreich:**

1. Im Zahlungspfad steht der Aufruf in einem `except Exception`, das nur
   protokolliert. Das ist richtig so — eine kaputte Beilage darf keinen Kauf
   kippen. Nur sieht dann eben niemand hin.

2. **Es gibt zwei Tests zu dieser Datei, und beide pruefen die
   Preisermittlung *um* das PDF herum.** Erzeugt hat das Dokument keiner.
   Dieselbe Luecke wie beim StripeObject am selben Abend: geprueft wurde
   alles ausser dem Gegenstand.

Diese Datei erzeugt das Dokument deshalb wirklich.
"""
import pytest

from services.auftragsbestaetigung_pdf import generate_auftragsbestaetigung


PAKET = {
    "name": "Websprint Relaunch",
    "brutto": 4165.00,
    "netto": 3500.00,
    "mwst": 665.00,
    "leistungen": ["Eingangsaudit nach Homepage-Standard",
                   "Aufbau im Komponentensystem"],
}


def _erzeugen(**abweichung) -> bytes:
    felder = {
        "session_id": "cs_test_beispiel",
        "customer_name": "Erika Muster",
        "customer_email": "kaeuferin@example.org",
        "company_name": "Testbetrieb GmbH",
        "paket": PAKET,
        "datum": "27.08.2026",
    }
    felder.update(abweichung)
    return generate_auftragsbestaetigung(**felder)


# ── Dass es ueberhaupt entsteht ───────────────────────────────────────

def test_es_entsteht_ein_pdf():
    """**Die Zusicherung, die gefehlt hat.** Sie haette den Fehler beim
    Schreiben gefunden statt beim Kaeufer."""
    daten = _erzeugen()

    assert isinstance(daten, bytes)
    assert daten[:5] == b"%PDF-", "Das ist keine PDF-Datei"
    assert len(daten) > 2000, f"Verdaechtig klein: {len(daten)} Bytes"


def test_ohne_firmennamen_geht_es_auch():
    """Ein Privatkaeufer hat keine Firma. Der Beleg muss trotzdem entstehen."""
    assert _erzeugen(company_name="")[:5] == b"%PDF-"


def test_umlaute_und_lange_namen_kippen_es_nicht():
    """Der haeufigste Weg, ein PDF zu sprengen: fremde Zeichen."""
    daten = _erzeugen(customer_name="Jürgen Müller-Straßberger",
                      company_name="Heizung & Sanitär Groß OHG")

    assert daten[:5] == b"%PDF-"


def test_ein_paket_ohne_leistungen_ist_kein_fehler():
    """Nicht jedes Produkt hat eine Aufzaehlung."""
    ohne = dict(PAKET, leistungen=[])

    assert _erzeugen(paket=ohne)[:5] == b"%PDF-"


# ── Und was darin stehen muss ─────────────────────────────────────────

def _inhalt() -> str:
    """Der Text des Belegs — abgegriffen, wo der Bericht fertig ist.

    Ueber `pdf_inhalt.inhalt_von`, dasselbe Werkzeug wie beim Kundenbericht
    (L-25): Es faengt die Flowable-Folge an `doc.build` ab und **erzeugt das
    PDF trotzdem**. Der Test geht damit denselben Weg wie der Betrieb und
    nicht einen kuerzeren.
    """
    from pdf_inhalt import inhalt_von

    return "\n".join(inhalt_von(_erzeugen))


def test_die_zahlen_stehen_im_dokument():
    """**Die Gegenprobe zum Erzeugen.** Ein PDF, das entsteht und die
    falschen Zahlen traegt, waere schlimmer als eines, das fehlt — es sieht
    aus wie ein Beleg. Genau das war L-29: eine feste Preisliste in dem
    Dokument, das der Kunde aufhebt.
    """
    text = _inhalt()

    # **Die Schreibweise ist die, die das Dokument heute wirklich benutzt**
    # (`4165.00 EUR`), nicht die, die ich fuer richtig halte. Ein Test, der
    # eine gewuenschte Formatierung behauptet, prueft nicht das Dokument,
    # sondern meine Meinung — und faerbt sich rot, ohne dass etwas kaputt
    # ist. Dass ein deutscher Beleg eigentlich `4.165,00 EUR` schreiben
    # sollte, ist eine eigene Frage und steht im Lagebild.
    for erwartet in ("4165.00", "3500.00", "665.00"):
        assert erwartet in text, f"{erwartet} fehlt im Beleg:\n{text[:400]}"


def test_der_paketname_steht_darin_und_nicht_die_kennung():
    assert "Websprint Relaunch" in _inhalt()


@pytest.mark.parametrize("wert", ["Erika Muster", "Testbetrieb GmbH"])
def test_der_kaeufer_steht_darin(wert):
    assert wert in _inhalt()
