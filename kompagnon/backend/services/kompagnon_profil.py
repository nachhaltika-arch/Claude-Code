# -*- coding: utf-8 -*-
"""Die eigenen Betriebsdaten — für die eigene `llms.txt` (L-121).

**Der Befund vom 25.08.2026.** Mit dem neuen Prüfer `geo_auslieferung` an den
eigenen Adressen gemessen: Weder `kas.kompagnon.group` noch die
Produktivoberfläche hat eine `llms.txt`, strukturierte Daten oder auch nur eine
`robots.txt`. Genau die drei Artefakte, die GEO-01 für 1.200 € an Kundenseiten
ausliefert, fehlten an unseren eigenen.

**Warum es hier hakte, und nicht an der Technik.** Der Erzeuger und der
Auslieferungsweg stehen seit L-99. Sie hängen aber am **Betrieb eines
Projekts** — und die eigene Seite ist kein Projekt. Es fehlte nicht Code,
sondern ein Datensatz über uns selbst.

**Die Quelle ist belegt, nicht erfunden.** Firmierung und Anschrift stammen aus
der Titelei des Buchs (`TITELEI.md`, Zeile „Herausgeber"), also aus dem
Dokument, das für den Druck rechtlich geprüft wird. Wer sie ändert, ändert sie
dort zuerst.

**Was hier bewusst nicht steht:** Registergericht, Steuernummer und
Geschäftsführung. Eine `llms.txt` ist kein Impressum — sie sagt einem Modell,
wer wir sind und was wir anbieten. Pflichtangaben gehören auf die
Impressumsseite, und die ist ein eigener offener Punkt (Kapitel 16.3 B).
"""
from types import SimpleNamespace

#: Wie ein `Lead` aussieht, den die Artefakt-Erzeuger lesen. Bewusst dasselbe
#: Format wie ein Kundenbetrieb: Was für unsere Kunden gut genug ist, ist es
#: für uns auch — und es gibt keinen zweiten Erzeuger.
BETRIEB = SimpleNamespace(
    company_name="KOMPAGNON communications BP GmbH",
    website_url="https://kas.kompagnon.group",
    # Feldnamen wie am `Lead` — nachgesehen in `geo_artefakte`, nicht geraten:
    # `street` und `house_number` getrennt, `postal_code` statt `zip_code`.
    # Beim ersten Anlauf fielen Anschrift und Seiten stillschweigend heraus,
    # weil die Namen nicht passten — die Erzeuger melden das nicht, sie lassen
    # weg. Genau dafuer gibt es `test_kompagnon_profil`.
    street="Marienfelder Straße",
    house_number="52",
    postal_code="56070",
    city="Koblenz",
    email="hallo@kompagnon.group",
    phone="",
    trade="Websites für Handwerk und Mittelstand",
    opening_hours=None,
    usp=("Websites nach dem Homepage Standard — 39 Kriterien, 8 Kategorien, "
         "103 Punkte. Gebaut, gemessen und nachweisbar verbessert."),
)

#: Die Seiten, die ein Modell kennen soll. Kurz gehalten: Eine `llms.txt`, die
#: jede Unterseite aufzählt, ist ein Sitemap-Ersatz und keine Auskunft.
SEITEN = [
    {"page_name": "Der Homepage Standard", "slug": "",
     "zweck": "Der Prüfkatalog und was er misst"},
    {"page_name": "Website-Check", "slug": "check",
     "zweck": "Kostenlose Prüfung einer Website gegen den Standard"},
]


def eigenes_profil() -> tuple:
    """(`llms.txt`, JSON-LD) für die eigene Seite — über denselben Erzeuger."""
    from services.geo_artefakte import llms_txt, local_business_jsonld

    return llms_txt(BETRIEB, SEITEN), local_business_jsonld(BETRIEB)
