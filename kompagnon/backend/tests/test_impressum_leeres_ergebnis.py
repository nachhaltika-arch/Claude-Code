"""Wenn nichts extrahiert wurde, muss man sehen, woran es lag.

`gleichstrom.de` am 17.08.2026: Der Sucher liefert 229 Zeichen mit allem
darin — „Gleichstrom GmbH, Mainzer Str. 439, 55411 Bingen, Registergericht …
Geschäftsführer Alexander Neumann". Die Auswertung gibt trotzdem
`{'success': True, 'data': {}}` zurück. Also hat die KI geantwortet und nichts
gefunden.

Warum, ließ sich nicht feststellen: Der lokale Schlüssel ist leer, die
Render-Logs sind von hier nicht lesbar, und die Antwort verriet nichts über
sich selbst.

Deshalb trägt ein leeres Ergebnis jetzt seine eigene Begründung: wie lang der
Text war und was das Modell tatsächlich geantwortet hat. Das ist derselbe
Grundsatz wie den ganzen Tag — ein Fehlschlag, der nicht sagt, was schiefging,
kostet beim nächsten Mal dieselbe Stunde.
"""
import asyncio

import pytest


IMPRESSUM = ("Gleichstrom | Impressum Impressum Gleichstrom GmbH Mainzer Str. 439 "
             "55411 Bingen info@gleichstrom.de Registergericht Handelsregister B "
             "des Amtsgerichts Mainz Registernummer HRB 52438 "
             "Geschäftsführer Alexander Neumann")


class _Antwort:
    def __init__(self, text):
        self.content = [type('Block', (), {'text': text})()]


def _ki(monkeypatch, antworttext):
    from services import impressum_scraper

    async def kein_netz(url):
        return IMPRESSUM

    monkeypatch.setattr(impressum_scraper, 'fetch_impressum_text', kein_netz)

    class _Nachrichten:
        def create(self, **kwargs):
            return _Antwort(antworttext)

    class _Client:
        def __init__(self, *a, **k):
            self.messages = _Nachrichten()

    monkeypatch.setattr(impressum_scraper, 'Anthropic', _Client)


def test_ein_leeres_ergebnis_nennt_die_rohantwort(app, monkeypatch):
    """Der Fall gleichstrom: geantwortet, aber alle Felder leer."""
    from services.impressum_scraper import extract_contact_from_impressum

    _ki(monkeypatch, '{"company_name": "", "street": "", "city": ""}')

    ergebnis = asyncio.run(extract_contact_from_impressum('https://gleichstrom.de'))

    assert ergebnis['success'] is True
    assert ergebnis['data'] == {}
    assert 'gleichstrom' not in ergebnis.get('roh_antwort', '').lower() or True
    assert ergebnis['roh_antwort'].startswith('{"company_name"')
    assert ergebnis['text_laenge'] == len(IMPRESSUM)


def test_bei_einem_treffer_gibt_es_keine_rohantwort(app, monkeypatch):
    """Wer etwas findet, muss sich nicht erklären."""
    from services.impressum_scraper import extract_contact_from_impressum

    _ki(monkeypatch, '{"company_name": "Gleichstrom", "city": "Bingen"}')

    ergebnis = asyncio.run(extract_contact_from_impressum('https://gleichstrom.de'))

    assert ergebnis['data']['company_name'] == 'Gleichstrom'
    assert 'roh_antwort' not in ergebnis


def test_ein_nicht_zeichenkettiger_wert_kippt_nichts(app, monkeypatch):
    """Antwortet das Modell mit einer Zahl, darf das nicht die Auswertung werfen.

    `v.strip()` auf einem int wäre ein AttributeError — und der landete im
    äußeren `except`, das jeden Fehler zu „Extraktion fehlgeschlagen" macht.
    """
    from services.impressum_scraper import extract_contact_from_impressum

    _ki(monkeypatch, '{"company_name": "Gleichstrom", "postal_code": 55411}')

    ergebnis = asyncio.run(extract_contact_from_impressum('https://gleichstrom.de'))

    assert ergebnis['success'] is True
    assert ergebnis['data']['company_name'] == 'Gleichstrom'
    assert ergebnis['data']['postal_code'] == '55411'
