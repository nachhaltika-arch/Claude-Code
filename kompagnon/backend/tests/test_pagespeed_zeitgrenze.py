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
"""
from services.audit_pagespeed import API_KEY_ENV_VARS, PSI_TIMEOUT

#: Der langsamste Lauf der Messung vom 28.08.2026 (nachhaltika.de, mobil).
GEMESSEN_LANGSAMSTER = 22.9

#: Der Lauf, der zuvor in die alte Grenze lief.
GEMESSEN_ABBRUCH = 30.2


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
