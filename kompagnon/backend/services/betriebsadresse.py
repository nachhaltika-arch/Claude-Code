"""Anschrift und Öffnungszeiten eines Betriebs (L-15, L-99, L-105).

**Warum es dieses Modul gibt.** Am 24.08.2026 sollte der SEO/GEO-Agent einen
Knopf bekommen. Er ließ sich nicht anschließen: `CompanyData` verlangt
``street``, ``postal_code`` und ``opening_hours``, und diese Felder gab es im
Datenmodell nicht. Der Agent war nie anzuschließen, weil seine Eingabe nie
existierte.

Die Umwandlung steht hier und nicht im Router, weil **drei** Stellen sie
brauchen werden: der Agent, die `llms.txt`-Erzeugung und die
`schema.org/LocalBusiness`-Auszeichnung (beides L-99). Eine zweite Fassung
davon wäre genau die Doppelführung, an der L-62 gescheitert ist.
"""
import json
from typing import Optional

#: Was eine Anschrift vollständig macht — aus `schema.org/PostalAddress`
#: plus den Öffnungszeiten, die `LocalBusiness` verlangt.
PFLICHTFELDER = ("street", "postal_code", "city", "opening_hours")


def oeffnungszeiten_lesen(roh: Optional[str]) -> dict:
    """JSON-Text zu einem Verzeichnis — kaputte Eingaben ergeben `{}`.

    **Kein Eintrag heißt „nicht erhoben", nicht „geschlossen".** Ein leeres
    Verzeichnis ist deshalb die richtige Antwort und keine Behauptung.

    Ein Feld aus der Oberfläche darf keine Route zerlegen: Was sich nicht als
    Verzeichnis lesen lässt, gilt als nicht erhoben.
    """
    if not roh:
        return {}
    try:
        gelesen = json.loads(roh)
    except (ValueError, TypeError):
        return {}
    return gelesen if isinstance(gelesen, dict) else {}


def adresse_vollstaendig(betrieb) -> bool:
    """Reicht es für `LocalBusiness` und den SEO-Agenten?"""
    return all(
        str(getattr(betrieb, feld, "") or "").strip()
        for feld in PFLICHTFELDER
    )


def als_company_data(betrieb, leistungen: Optional[list] = None) -> dict:
    """Der Betrieb in der Form, die `POST /api/agents/{id}/seo` verlangt.

    **Nichts wird erfunden.** Fehlt die Anschrift, bleibt das Feld leer — eine
    geratene Adresse in einer `schema.org`-Auszeichnung wäre eine Behauptung
    über einen fremden Betrieb, und sie sähe genauso aus wie eine geprüfte.
    """
    def wert(feld: str) -> str:
        return str(getattr(betrieb, feld, "") or "").strip()

    return {
        "company_name": wert("company_name"),
        # **Strasse und Hausnummer sind hier zwei Spalten, dort ein Feld.**
        # `Lead` fuehrt `street` und `house_number` getrennt (das faellt beim
        # Lesen leicht durchs Raster — der erste Anlauf am 24.08.2026 haette
        # beinahe eine zweite `street`-Spalte angelegt). `CompanyData` und
        # `schema.org/PostalAddress.streetAddress` wollen eine Zeile.
        "street": " ".join(
            teil for teil in (wert("street"), wert("house_number")) if teil
        ),
        "postal_code": wert("postal_code"),
        "city": wert("city"),
        "country": "DE",
        "phone": wert("phone"),
        "email": wert("email"),
        "website": wert("website_url"),
        "services": list(leistungen or []),
        "opening_hours": oeffnungszeiten_lesen(getattr(betrieb, "opening_hours", None)),
    }
