"""Wann ein Firmenname noch keiner ist.

**Warum es das gibt.** Am 17.08.2026 hiess in der Betriebsliste jeder Eintrag
wie seine Domain — `alkozei.de`, `andovski.de`, `example.com`. Das sah nach
fehlender Datenpflege aus und war eine Zeile Code.

Der Domainimport legt einen Betrieb mit der Domain als `company_name` an, als
Platzhalter, bis der echte Name da ist. Kurz darauf liest der
Impressum-Schritt den echten Namen aus — und verwirft ihn:

    if data_imp.get(field) and not getattr(lead, field, None):

Zu diesem Zeitpunkt ist `company_name` gefuellt. Mit dem Platzhalter. Also
gilt das Feld als erledigt. `enrich_lead` machte denselben Fehler, nur
freundlicher: Es prueft auf leer und auf „Unbekannt" — an die Domain hat
niemand gedacht.

Ein Platzhalter, der sich wie ein Wert verhaelt, verhindert genau das, wofuer
er da war. Diese Datei sagt an einer Stelle, was ein Platzhalter ist.
"""
import re

#: Was ausdruecklich als „noch kein Name" gilt.
UNBEKANNT = frozenset({"unbekannt", "unknown", "n/a", "-", "–"})

#: Sieht aus wie eine blanke Domain: keine Leerzeichen, endet auf eine
#: Top-Level-Domain aus Buchstaben.
_DOMAINFORM = re.compile(r"^[a-z0-9][a-z0-9\-.]*\.[a-z]{2,}$")


def _blank(wert) -> str:
    return (wert or "").strip().lower().removeprefix("www.")


def ist_platzhalter(name, website_url=None) -> bool:
    """Ist dieser Firmenname bloss ein Platzhalter?

    Platzhalter sind: nichts, „Unbekannt", die eigene Domain — und alles, was
    die Form einer Domain hat. Letzteres deckt auch die verrutschten Faelle
    ab: `nachhaltika.denachhaltika.de` stand so in der Liste.

    Ein Name mit Leerzeichen ist nie ein Platzhalter, auch nicht mit Punkt:
    „Fa. Krause" bleibt ein Name.
    """
    sauber = _blank(name)
    if not sauber:
        return True
    if sauber in UNBEKANNT:
        return True

    if website_url:
        domain = _blank(re.sub(r"^https?://", "", website_url).split("/")[0])
        if domain and sauber == domain:
            return True

    return bool(_DOMAINFORM.match(sauber))


def uebernehmen(vorhanden, gefunden, website_url=None):
    """Der gefundene Name — oder ``None``, wenn nichts zu tun ist.

    Uebernommen wird nur, wenn der vorhandene Eintrag ein Platzhalter ist und
    der gefundene keiner. Wer von Hand einen Namen gepflegt hat, behaelt ihn.
    """
    if not (gefunden or "").strip():
        return None
    if not ist_platzhalter(vorhanden, website_url):
        return None
    if ist_platzhalter(gefunden, website_url):
        return None
    return gefunden.strip()
