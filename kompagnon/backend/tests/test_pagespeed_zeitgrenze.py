# -*- coding: utf-8 -*-
"""Die PageSpeed-Zeitgrenze hat Spielraum ueber dem gemessenen Normalfall (L-126).

**Der Anlass, und er faengt mit einem Irrtum an.** Am 28.08.2026 fielen
`tp_lcp`, `tp_cls`, `tp_mobile` und die `bf_*` in vier von acht auswertbaren
Pruefungen aus. Vermutet wurde ein fehlender PageSpeed-Schluessel — nachgesehen
wurde nur `GOOGLE_PAGESPEED_API_KEY`. Der Dienst traegt ihn aber als
`PAGESPEED_API_KEY`, und `audit_pagespeed.api_key()` liest **beide**
Schreibweisen; genau davor warnt L-35 seit dem 27.08. woertlich.

**Die wirkliche Ursache stand danach in der Uhr.** Gemessen vom
Produktivdienst aus, mit beiden Kategorien wie im echten Aufruf: 4,8 s bis
22,9 s, und ein Lauf endete bei 30,2 s — der alten Grenze. Zwischen Normalfall
und Grenze lag kein Spielraum.

**Warum ein Test darauf und nicht nur ein Kommentar.** Eine Zeitgrenze ist
eine Zahl, die niemand anfasst und jeder senkt, wenn ein Lauf mal haengt. Der
Test haelt die Begruendung an der Zahl fest: Wer sie unter den gemessenen
Normalfall druecken will, muss diese Datei aendern und liest dabei, warum.

**Was er ausdruecklich nicht kann:** Er sagt nichts darueber, ob Google heute
schnell ist. Ein Test, der eine fremde API befragt, wird rot, wenn diese kurz
haengt — und ein Tor, das aus fremden Gruenden rot wird, wird abgeschaltet.
Die Messung gegen die Wirklichkeit gehoert in ein Werkzeug, nicht in die CI.

── Nachtrag vom 05.09.2026 ───────────────────────────────────────────

**Auch 60 Sekunden haben nicht gereicht.** Ein Prueflauf auf Staging (Audit 4,
neovendo.de) mit gesetztem Schluessel:

    08:38:37  Seite im Browser geladen
    08:39:39  PageSpeed fehlgeschlagen fuer https://neovendo.de/ (mobile):
    08:40:11  Audit 4: 83/100, Abdeckung 81%, 108,4s

Der Abbruch kam auf die Sekunde mit der Grenze. Der Faktor zwei ueber dem
**damals** gemessenen Normalfall war also kein Spielraum, sondern eine
Momentaufnahme: neovendo.de ist schwerer als nachhaltika.de.

**Und die Warnung verschwieg ihren Grund.** Hinter dem Doppelpunkt stand
nichts, weil `str()` einer `httpx.ReadTimeout` leer ist. Deshalb hielt am
04.09. noch jeder den fehlenden Schluessel fuer die Ursache — obwohl der Typ
in `collection_notes` die ganze Zeit mitlief. Dieselbe Fehlerklasse hat
`test_fehler_ohne_text.py` fuer die KI-Sichtbarkeit laengst festgehalten; hier
war sie nicht angewandt.

**Die Grenze steht jetzt bei 120 s** — gleichauf mit den Unterseiten, unter
der gemeinsamen Grenze von 200 s, und der Abruf laeuft parallel zu allen
anderen Erhebungen. Ob es reicht, sagt der naechste Lauf; reicht es nicht,
steht der Grund jetzt im Protokoll.
"""
import logging

import httpx
import pytest

from services import audit_pagespeed as psi
from services.audit_pagespeed import API_KEY_ENV_VARS, PSI_TIMEOUT

#: Der langsamste Lauf der Messung vom 28.08.2026 (nachhaltika.de, mobil).
GEMESSEN_LANGSAMSTER = 22.9

#: Der Lauf, der zuvor in die alte Grenze lief.
GEMESSEN_ABBRUCH = 30.2

#: Der Abbruch vom 05.09.2026 — diesmal an der 60-Sekunden-Grenze
#: (Audit 4 auf Staging, neovendo.de, mobil, mit gesetztem Schluessel).
GEMESSEN_ABBRUCH_2 = 60.0


def test_die_zeitgrenze_liegt_deutlich_ueber_dem_gemessenen_normalfall():
    """Faktor zwei ueber dem langsamsten gemessenen Lauf, nicht knapp darueber."""
    assert PSI_TIMEOUT >= 2 * GEMESSEN_LANGSAMSTER, (
        f"{PSI_TIMEOUT}s laesst zu wenig Luft ueber {GEMESSEN_LANGSAMSTER}s")


def test_die_alte_grenze_haette_den_beobachteten_abbruch_nicht_verhindert():
    """Die Gegenprobe — sonst waere die neue Zahl nur eine andere Zahl."""
    assert GEMESSEN_ABBRUCH > 30.0, "sonst belegt der Fall nichts"
    assert PSI_TIMEOUT > GEMESSEN_ABBRUCH


def test_beide_schreibweisen_des_schluessels_werden_gelesen():
    """Der Irrtum, der zu dieser Messung gefuehrt hat, bleibt festgehalten.

    Auf Render heisst die Variable `PAGESPEED_API_KEY`; wer nur den langen
    Namen abfragt, schliesst auf einen fehlenden Schluessel und schickt
    jemanden ein Google-Cloud-Projekt anlegen, das es nicht braucht.
    """
    assert set(API_KEY_ENV_VARS) == {
        "GOOGLE_PAGESPEED_API_KEY", "PAGESPEED_API_KEY"}


# ── Nachtrag 05.09.2026 ──────────────────────────────────────────────

def test_auch_die_zweite_grenze_ist_gerissen():
    """Der Faktor zwei von damals war eine Momentaufnahme, kein Spielraum.

    Ohne diese Gegenprobe stuende die neue Zahl genauso unbegruendet da wie
    die alte — und die naechste schwere Seite risse sie wieder.
    """
    assert PSI_TIMEOUT > GEMESSEN_ABBRUCH_2, (
        f"{PSI_TIMEOUT}s ist nicht mehr als die Grenze, an der am 05.09. "
        f"abgebrochen wurde")


def test_pagespeed_ist_nicht_die_engste_grenze_im_feld():
    """**Der eigentliche Konstruktionsfehler.**

    Der Abruf laeuft parallel zu allen anderen Erhebungen. Die Unterseiten
    duerfen 120 s brauchen, das ganze Feld 200 — und ausgerechnet der
    langsamste Abruf war mit 60 s am kuerzesten angebunden.
    """
    from services.audit_runner import COLLECTION_TIMEOUT, UNTERSEITEN_TIMEOUT

    assert PSI_TIMEOUT >= UNTERSEITEN_TIMEOUT
    assert PSI_TIMEOUT < COLLECTION_TIMEOUT, (
        "Die eigene Grenze muss vor der gemeinsamen greifen — sonst reisst "
        "die gemeinsame und **alle** Erhebungen fallen aus")


def test_sie_passt_ins_gesamtbudget():
    """Ein Audit hat 240 s; die KI-Bewertung danach bekommt 100."""
    from routers.audit import AUDIT_TOTAL_TIMEOUT_SEC

    assert PSI_TIMEOUT + 100 < AUDIT_TOTAL_TIMEOUT_SEC


@pytest.mark.anyio
async def test_eine_zeitueberschreitung_nennt_ihren_typ(monkeypatch, caplog):
    """**Die Zeile, die den Fund um eine Woche verzoegert hat.**

    `str(httpx.ReadTimeout(""))` ist leer. Im Protokoll stand woertlich
    „PageSpeed fehlgeschlagen fuer …:" — eine Warnung ohne Grund. Solange sie
    so aussah, hielt jeder den fehlenden Schluessel fuer die Ursache.
    """
    class Kaputt:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, *a, **k):
            raise httpx.ReadTimeout("")

    monkeypatch.setattr(psi.httpx, "AsyncClient", lambda **k: Kaputt())

    with caplog.at_level(logging.WARNING):
        ergebnis = await psi.fetch_pagespeed("https://beispiel.de", "mobile")

    assert "ReadTimeout" in caplog.text, "Der Typ fehlt — die Meldung sagt nichts"
    assert "beispiel.de" in caplog.text
    assert ergebnis["collected"] is False
    assert "ReadTimeout" in ergebnis["detail"]


@pytest.mark.anyio
async def test_eine_ausnahme_mit_text_verliert_ihn_nicht(monkeypatch, caplog):
    """Die Gegenprobe: Wo eine Meldung da ist, bleibt sie stehen."""
    class Kaputt:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, *a, **k):
            raise ValueError("Adresse nicht aufloesbar")

    monkeypatch.setattr(psi.httpx, "AsyncClient", lambda **k: Kaputt())

    with caplog.at_level(logging.WARNING):
        await psi.fetch_pagespeed("https://beispiel.de", "mobile")

    assert "ValueError" in caplog.text
    assert "Adresse nicht aufloesbar" in caplog.text
