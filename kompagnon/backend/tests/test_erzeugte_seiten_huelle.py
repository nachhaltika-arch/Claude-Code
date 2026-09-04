# -*- coding: utf-8 -*-
"""Die Hülle jeder erzeugten Seite — `lang` und `<title>`.

**Warum ausgerechnet diese zwei (26.08.2026).** Sie sind `html-has-lang` und
`document-title`, zwei der acht Lighthouse-Kriterien, die **unser eigenes
Audit bei Kunden prüft** (`audit_pagespeed.A11Y_AUDIT_GROUPS`, Gruppe
„screenreader"). L-17 führt beide seit dem 21.08. als offen. Beim Nachmessen
zeigte sich: Im Werkzeug halten sie — `public/index.html` trägt beides. In den
**erzeugten** Seiten nicht überall.

**Der Fund:** `routers.agents._json_to_html` baut die Kundenseite aus dem
Briefing und schrieb `<html>` ohne `lang` und einen Kopf ohne `<title>`.
Ein Screenreader wählt ohne `lang` die Aussprache nach der Voreinstellung des
Benutzers — deutsche Texte in englischer Aussprache sind unverständlich, nicht
bloß unschön. Ohne `<title>` sagt der Browser-Tab nichts, die Vorlesehilfe
kündigt die Seite nicht an, und die Suchmaschine hat keine Überschrift.

**Eine Seite, die wir für einen Kunden bauen, muss bestehen, was wir bei ihm
messen.** Sonst verkauft das Werkzeug einen Maßstab, den es selbst reißt.

**Warum ein Wächter und nicht nur eine Korrektur:** Es gibt neun Stellen im
Backend, die eine vollständige HTML-Hülle erzeugen. Acht waren richtig, eine
nicht — und niemand hätte die neunte bemerkt. Wer eine zehnte hinzufügt,
bekommt hier eine Antwort statt eines stillen Mangels.
"""
import re
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parent.parent

#: Stellen, die eine HTML-Hülle erzeugen, ohne eine **Seite** zu sein.
#: Jede ist nachgesehen worden.
AUSGENOMMEN = {
    # Der Editor erwartet genau diesen Kopf; die `support.js`-Zeile wird zur
    # Laufzeit ersetzt. Ein Artboard ist kein Dokument, sondern ein Ausschnitt.
    "services/canvas_artboards.py",
    # Mails. `<title>` erscheint in keinem Mailprogramm; `lang` prueft der
    # eigene Test unten, aber ohne Titelpflicht.
    "services/email.py",
    "services/mail_layout.py",
}

#: Dateien, die HTML nur **lesen** oder als Beispiel zitieren.
KEINE_ERZEUGER = {"services/geo_auslieferung.py", "routers/component_library_ki.py"}

MUSTER_HTML = re.compile(r"<html\b[^>]*>", re.IGNORECASE)


def _quelldateien():
    for ordner in ("routers", "services"):
        yield from sorted((WURZEL / ordner).glob("*.py"))


def _huellen(pfad: Path):
    """Jede `<html …>`-Stelle mit ihrer Zeilennummer."""
    # **Ohne Kommentare.** `services/html_seite.py` erklaert in einer
    # Zeile, warum `<html>` und `<head>` **nicht** uebernommen werden —
    # und wurde dafuer als „erzeugte Seite ohne Sprachangabe" gemeldet
    # (27.08.2026). Zeichenketten bleiben stehen; in ihnen steht das
    # HTML, um das es hier geht.
    from tools.adressen import ohne_python_kommentare

    text = ohne_python_kommentare(pfad.read_text(encoding="utf-8"))
    for treffer in MUSTER_HTML.finditer(text):
        yield text[:treffer.start()].count("\n") + 1, treffer.group(0), text


def _zu_pruefen():
    for pfad in _quelldateien():
        kurz = f"{pfad.parent.name}/{pfad.name}"
        if kurz in KEINE_ERZEUGER:
            continue
        for zeile, tag, text in _huellen(pfad):
            yield kurz, zeile, tag, text


def test_jede_erzeugte_seite_nennt_ihre_sprache():
    """`html-has-lang`. Ohne `lang` rät die Vorlesehilfe die Aussprache."""
    ohne = [f"{kurz}:{zeile} {tag}"
            for kurz, zeile, tag, _ in _zu_pruefen()
            if "lang=" not in tag.lower()
            and kurz not in AUSGENOMMEN]

    assert ohne == [], ("Erzeugte Seiten ohne Sprachangabe:\n  "
                        + "\n  ".join(ohne))


def test_auch_die_mails_nennen_ihre_sprache():
    """Getrennt gefuehrt, weil Mails keinen Titel brauchen — eine Sprache
    aber sehr wohl: Vorlesehilfen gibt es auch im Mailprogramm."""
    ohne = [f"{kurz}:{zeile} {tag}"
            for kurz, zeile, tag, _ in _zu_pruefen()
            if "lang=" not in tag.lower()
            and kurz in {"services/email.py", "services/mail_layout.py"}]

    assert ohne == [], "Mail-Vorlagen ohne Sprachangabe:\n  " + "\n  ".join(ohne)


def test_jede_erzeugte_seite_hat_einen_titel():
    """`document-title`. Gesucht wird im **selben Ausdruck**, nicht in der
    ganzen Datei — sonst deckt ein Titel an einer Stelle einen fehlenden an
    einer anderen zu."""
    ohne = []
    for kurz, zeile, _tag, text in _zu_pruefen():
        if kurz in AUSGENOMMEN:
            continue
        # Der Kopf endet spaetestens am `</head>`; dazwischen muss der Titel
        # stehen. Fehlt `</head>`, nehmen wir 1.500 Zeichen als Fenster —
        # jede der vorhandenen Huellen ist kuerzer.
        beginn = text.index("<html", sum(len(z) + 1 for z in
                                         text.split("\n")[:zeile - 1]))
        ende = text.find("</head>", beginn)
        fenster = text[beginn:ende if ende != -1 else beginn + 1500]
        if "<title" not in fenster.lower():
            ohne.append(f"{kurz}:{zeile}")

    assert ohne == [], ("Erzeugte Seiten ohne <title>:\n  "
                        + "\n  ".join(ohne))


class TestDieKundenseiteAusDemBriefing:
    """`_json_to_html` genauer — es ist die Seite, die beim Kunden landet."""

    def _seite(self, ctx=None):
        from routers.agents import _json_to_html

        return _json_to_html({"hero_headline": "Wärmepumpe vom Fachbetrieb",
                              "hero_subline": "Beratung in 24 Stunden",
                              "about_text": "Seit 1998 in Koblenz."},
                             ctx if ctx is not None else {})

    def test_sie_nennt_deutsch_als_sprache(self):
        assert 'lang="de"' in self._seite()

    def test_der_titel_kommt_aus_dem_betrieb(self):
        """Der Firmenname ist das, was ein Mensch im Tab sucht."""
        seite = self._seite({"company_name": "Mustermann Sanitär GmbH"})

        assert "<title>Mustermann Sanitär GmbH</title>" in seite

    def test_ohne_firmennamen_nimmt_er_die_ueberschrift(self):
        """Ein Titel, der die Hauptüberschrift wiederholt, ist besser als
        keiner — und besser als „Unbenannt“."""
        assert "<title>Wärmepumpe vom Fachbetrieb</title>" in self._seite()

    @pytest.mark.parametrize("spitz", ["<script>alert(1)</script>",
                                       'Mustermann " & Söhne'])
    def test_der_titel_wird_maskiert(self, spitz):
        """Der Firmenname kommt aus einem Briefing, also von aussen.

        Ohne Maskierung schriebe ein `<` im Namen den Kopf der Seite um —
        dieselbe Klasse wie jede andere Einschleusung, nur an einer Stelle,
        an der man sie selten sucht.
        """
        seite = self._seite({"company_name": spitz})

        assert "<script>" not in seite.split("</head>")[0]
        assert "&lt;" in seite or "&amp;" in seite

    def test_ohne_alles_bleibt_die_huelle_gueltig(self):
        """Ein leeres Briefing darf keinen Kopf ohne Titel erzeugen."""
        from routers.agents import _json_to_html

        seite = _json_to_html({}, {})

        assert 'lang="de"' in seite
        assert re.search(r"<title>.+</title>", seite)
