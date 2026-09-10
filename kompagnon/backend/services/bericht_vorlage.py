# -*- coding: utf-8 -*-
"""Die Vorlagensprache der Berichtsseite (L-191, 10.09.2026).

Der Entwurf kommt aus einem Gestaltungswerkzeug und bringt eine sehr kleine
eigene Sprache mit — drei Formen, mehr nicht:

    {{ feld }}                              Wert einsetzen, geschuetzt
    {{ obj.feld }}                          verschachtelt
    <sc-for list="{{ liste }}" as="x">…</sc-for>
    <sc-if value="{{ flag }}">…</sc-if>
    <sc-raw-td …>                           heisst im Ergebnis <td …>

**Warum nachbauen und nicht in Zeichenkettenverkettung uebersetzen.** Der
Entwurf ist Davids Gestaltung und wird sich aendern. Wer ihn beim Einbauen
aufloest, macht jede spaetere Aenderung zur Programmieraufgabe. So bleibt
die Datei eine Vorlage, die man austauschen kann — und die Rueckfrage
lautet „welche Felder hast du benutzt?" statt „wo im Code steht das jetzt?".

**Schuetzen ist die Vorgabe.** Auf der Seite stehen Firmenname und
Website-Adresse aus dem Widget, also Fremdeingaben. Es gibt hier bewusst
**keine** Form fuer rohes HTML: Wer sie braeuchte, soll erst begruenden,
warum — und dann eine eigene bekommen, statt dass jedes Feld sie hat.

**Was diese Datei nicht ist.** Keine allgemeine Vorlagensprache. Sie kann
genau das, was der Entwurf benutzt, und faellt auf, wenn er mehr benutzt:
`test_keine_sc_reste_im_ergebnis` prueft, dass nichts Unverstandenes
durchrutscht.
"""
import html
import re

#: Die Elemente, die der Export nur umbenannt hat, damit sein eigener Editor
#: sie nicht als Tabelle behandelt. Im Ergebnis heissen sie wieder normal.
ROH_ELEMENTE = ("table", "thead", "tbody", "tr", "td", "th")

_FELD = re.compile(r"\{\{\s*([A-Za-z_][\w.]*)\s*\}\}")
_BLOCK = re.compile(r"<sc-(for|if)\b([^>]*)>", re.S)
_LIST_ATTR = re.compile(r'list\s*=\s*"\{\{\s*([\w.]+)\s*\}\}"')
_AS_ATTR = re.compile(r'as\s*=\s*"(\w+)"')
_VALUE_ATTR = re.compile(r'value\s*=\s*"\{\{\s*([\w.]+)\s*\}\}"')


def _wert(pfad: str, daten: dict):
    """Ein Feld aus den Daten holen — `a.b.c` laeuft die Kette entlang."""
    stelle = daten
    for teil in pfad.split("."):
        if isinstance(stelle, dict) and teil in stelle:
            stelle = stelle[teil]
        else:
            return None
    return stelle


def _text(wert) -> str:
    """Ein Wert als geschuetzter Text. `None` ist leer, nicht „None"."""
    if wert is None or wert is False:
        return ""
    if wert is True:
        return "true"
    return html.escape(str(wert), quote=True)


def _ende_finden(vorlage: str, name: str, ab: int) -> int:
    """Das schliessende Tag zu einem Block — **verschachtelt gezaehlt**.

    Ohne diese Zaehlung endete die aeussere Schleife am ersten inneren
    `</sc-for>`; im Entwurf steckt `kat.kriterien` in `kategorien`, der Fall
    kommt also wirklich vor.
    """
    auf = re.compile(r"<sc-%s\b" % name)
    zu = re.compile(r"</sc-%s>" % name)
    tiefe = 1
    stelle = ab
    while tiefe:
        naechstes_auf = auf.search(vorlage, stelle)
        naechstes_zu = zu.search(vorlage, stelle)
        if not naechstes_zu:
            raise ValueError("Unbeendeter Block <sc-%s>" % name)
        if naechstes_auf and naechstes_auf.start() < naechstes_zu.start():
            tiefe += 1
            stelle = naechstes_auf.end()
        else:
            tiefe -= 1
            stelle = naechstes_zu.end()
            if not tiefe:
                return naechstes_zu.start(), naechstes_zu.end()
    raise ValueError("Unbeendeter Block <sc-%s>" % name)


def rendern(vorlage: str, daten: dict) -> str:
    """Vorlage mit Daten fuellen."""
    treffer = _BLOCK.search(vorlage)
    if not treffer:
        return _felder_setzen(_roh_umbenennen(vorlage), daten)

    art, attribute = treffer.group(1), treffer.group(2)
    inhalt_ab = treffer.end()
    inhalt_bis, block_bis = _ende_finden(vorlage, art, inhalt_ab)

    vorher = vorlage[:treffer.start()]
    inhalt = vorlage[inhalt_ab:inhalt_bis]
    nachher = vorlage[block_bis:]

    if art == "for":
        pfad = _LIST_ATTR.search(attribute)
        name = _AS_ATTR.search(attribute)
        eintraege = _wert(pfad.group(1), daten) if pfad else None
        stuecke = []
        for eintrag in (eintraege or []):
            umgebung = dict(daten)
            if name:
                umgebung[name.group(1)] = eintrag
            stuecke.append(rendern(inhalt, umgebung))
        mitte = "".join(stuecke)
    else:
        pfad = _VALUE_ATTR.search(attribute)
        mitte = rendern(inhalt, daten) if (pfad and _wert(pfad.group(1), daten)) else ""

    return rendern(vorher, daten) + mitte + rendern(nachher, daten)


def _felder_setzen(text: str, daten: dict) -> str:
    return _FELD.sub(lambda m: _text(_wert(m.group(1), daten)), text)


def _roh_umbenennen(text: str) -> str:
    for name in ROH_ELEMENTE:
        text = text.replace("<sc-raw-%s" % name, "<%s" % name)
        text = text.replace("</sc-raw-%s>" % name, "</%s>" % name)
    return text
