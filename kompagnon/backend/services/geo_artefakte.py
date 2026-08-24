"""GEO/GAIO-Artefakte für die Kundenseite — den Anfang macht `llms.txt` (L-99).

**Warum es das gibt.** Das Systempaket (12.900 €) verspricht einen
GEO/GAIO-Layer: `llms.txt`, `schema.org`-Auszeichnung und Ground Page. In
`main.py` steht das Produkt ausdrücklich auf `draft`, **weil** diese Leistung
nicht ausgeliefert wird. `services/qa_scanner.py` **prüft** seit dem 16.08.,
ob eine fremde Seite eine `llms.txt` hat — **erzeugt** wurde nie eine. Das ist
die Unterscheidung, die L-58 nicht trifft: dort ging es ums Messen, hier ums
Herstellen.

**Warum erst am 24.08.2026.** Der Erzeuger braucht Anschrift und
Öffnungszeiten. `opening_hours` gab es bis zu diesem Tag nicht (L-15) — und
genau daran hing auch der SEO-Agent, der nie angeschlossen werden konnte.

**Was `llms.txt` ist** (llmstxt.org): eine Markdown-Datei im
Wurzelverzeichnis, die einem Sprachmodell in wenigen Zeilen sagt, worum es auf
dieser Seite geht — H1 mit dem Namen, ein Zitatblock als Zusammenfassung, dann
Abschnitte. Keine Auszeichnung für Suchmaschinen, sondern eine Auskunft für
Modelle. Sie ersetzt kein `schema.org`; beides steht nebeneinander.

**Nichts wird erfunden.** Fehlt eine Angabe, fehlt die Zeile. Eine geratene
Adresse in einer Datei, die Modelle als Quelle lesen, wäre schlimmer als gar
keine Datei — dieselbe Regel wie bei `lead_quellen.rechtsgrundlage` und bei
`betriebsadresse.als_company_data`.
"""
from typing import Optional

from services.betriebsadresse import oeffnungszeiten_lesen


def _wert(betrieb, feld: str) -> str:
    return str(getattr(betrieb, feld, "") or "").strip()


def _anschrift(betrieb) -> str:
    """`Hauptstraße 12, 56070 Koblenz` — oder leer, wenn etwas fehlt.

    **Alles oder nichts.** Eine halbe Anschrift („56070", ohne Straße) ist für
    ein Modell schlechter als keine: Sie sieht aus wie eine Angabe.
    """
    strasse = " ".join(t for t in (_wert(betrieb, "street"),
                                   _wert(betrieb, "house_number")) if t)
    ort = " ".join(t for t in (_wert(betrieb, "postal_code"),
                               _wert(betrieb, "city")) if t)
    if not strasse or not _wert(betrieb, "postal_code") or not _wert(betrieb, "city"):
        return ""
    return f"{strasse}, {ort}"


def _zusammenfassung(betrieb) -> str:
    """Ein Satz: Was macht dieser Betrieb, und wo?"""
    gewerk = _wert(betrieb, "trade")
    ort = _wert(betrieb, "city")
    name = _wert(betrieb, "company_name")
    if gewerk and ort:
        return f"{name} ist ein Fachbetrieb für {gewerk} in {ort}."
    if gewerk:
        return f"{name} ist ein Fachbetrieb für {gewerk}."
    if ort:
        return f"{name} ist ein Handwerksbetrieb in {ort}."
    return f"{name} ist ein Handwerksbetrieb."


def _seitenzeile(seite: dict, basis: str) -> str:
    name = str(seite.get("page_name") or "").strip()
    slug = str(seite.get("slug") or "").strip().strip("/")
    if not name:
        return ""
    ziel = f"{basis}/{slug}" if basis and slug else (f"/{slug}" if slug else "")
    zweck = str(seite.get("zweck") or "").strip()
    if not ziel:
        return f"- {name}" + (f": {zweck}" if zweck else "")
    return f"- [{name}]({ziel})" + (f": {zweck}" if zweck else "")


def llms_txt(betrieb, seiten: Optional[list] = None) -> str:
    """Die `llms.txt` für einen Betrieb — leer, wenn die Grundlage fehlt.

    Ohne Namen gibt es keine Datei: Eine `llms.txt`, die nicht sagt, um wen es
    geht, sagt einem Modell nichts und belegt trotzdem eine Adresse, die als
    beantwortet gilt.
    """
    if betrieb is None:
        return ""
    name = _wert(betrieb, "company_name")
    if not name:
        return ""

    basis = _wert(betrieb, "website_url").rstrip("/")
    zeilen = [f"# {name}", "", f"> {_zusammenfassung(betrieb)}", ""]

    # ── Kontakt: nur, was tatsächlich hinterlegt ist ──────────────────
    kontakt = []
    anschrift = _anschrift(betrieb)
    if anschrift:
        kontakt.append(f"- Anschrift: {anschrift}")
    if _wert(betrieb, "phone"):
        kontakt.append(f"- Telefon: {_wert(betrieb, 'phone')}")
    if _wert(betrieb, "email"):
        kontakt.append(f"- E-Mail: {_wert(betrieb, 'email')}")
    if kontakt:
        zeilen += ["## Kontakt", ""] + kontakt + [""]

    # ── Öffnungszeiten ───────────────────────────────────────────────
    zeiten = oeffnungszeiten_lesen(getattr(betrieb, "opening_hours", None))
    if zeiten:
        zeilen += ["## Öffnungszeiten", ""]
        zeilen += [f"- {tage} {zeit}".rstrip() for tage, zeit in zeiten.items()]
        zeilen += [""]

    # ── Seiten ───────────────────────────────────────────────────────
    eintraege = [z for z in (_seitenzeile(s, basis) for s in (seiten or [])) if z]
    if eintraege:
        zeilen += ["## Seiten", ""] + eintraege + [""]

    return "\n".join(zeilen).rstrip() + "\n"


def local_business_jsonld(betrieb) -> str:
    """`schema.org/LocalBusiness` als JSON-LD — leer, wenn die Grundlage fehlt.

    Das zweite der drei Artefakte, die das Systempaket verspricht. Es gehört
    in den `<head>` und **nicht** in eine eigene Datei: Anders als `llms.txt`,
    die ein Modell direkt abruft, wird JSON-LD beim Laden der Seite mitgelesen.

    **Dieselbe Regel wie überall hier: nichts erfinden.** Eine `PostalAddress`
    ohne Straße ist für eine Suchmaschine schlechter als gar keine — sie sieht
    aus wie eine Angabe und ist keine. Deshalb fällt der ganze Adressblock
    weg, sobald ein Teil fehlt, statt ihn halb zu füllen.

    `openingHours` folgt der schema.org-Schreibweise „Mo-Do 08:00-17:00" —
    genau die Form, in der die Öffnungszeiten ohnehin eingegeben werden
    (`utils/oeffnungszeiten.js`). Ein Eintrag ohne Zeit („Sa nach
    Vereinbarung") bleibt als Text stehen; er ist für einen Menschen richtig
    und für die Maschine unschädlich.
    """
    import json

    if betrieb is None:
        return ""
    name = _wert(betrieb, "company_name")
    if not name:
        return ""

    daten = {"@context": "https://schema.org", "@type": "LocalBusiness",
             "name": name}

    for feld, schluessel in (("website_url", "url"), ("phone", "telephone"),
                             ("email", "email")):
        if _wert(betrieb, feld):
            daten[schluessel] = _wert(betrieb, feld)

    anschrift = _anschrift(betrieb)
    if anschrift:
        strasse, _, _ort = anschrift.partition(", ")
        daten["address"] = {
            "@type": "PostalAddress",
            "streetAddress": strasse,
            "postalCode": _wert(betrieb, "postal_code"),
            "addressLocality": _wert(betrieb, "city"),
            "addressCountry": "DE",
        }

    zeiten = oeffnungszeiten_lesen(getattr(betrieb, "opening_hours", None))
    if zeiten:
        daten["openingHours"] = [
            f"{tage} {zeit}".strip() for tage, zeit in zeiten.items()
        ]

    return json.dumps(daten, ensure_ascii=False, indent=2)
