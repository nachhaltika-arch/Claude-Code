"""Die Befunde vieler Seiten zu einem Befund je Kriterium zusammenfassen.

**Der Vertrag.** `audit_scoring` liest feste Schluessel — `forms.total`,
`contact.tel_link`, `services.service_page_count` und ein Dutzend mehr. Diese
Datei liefert **dieselben Schluessel in derselben Form**, nur ueber alle
geprueften Seiten statt ueber die Startseite. Die Bewertung bleibt dadurch
unberuehrt; was sich aendert, ist die Grundlage, auf der sie rechnet.

**Jede Zusammenfassung ist eine Entscheidung.** Es gibt keine allgemeine Regel
dafuer, wie aus zwanzig Befunden einer wird — sie haengt daran, was das
Kriterium behauptet:

* **Irgendwo genuegt** (`beliebig`): „Es gibt eine Telefonnummer", „es gibt ein
  Zertifikat", „ein Tracker ist im Einsatz". Eine Nummer im Impressum ist eine
  Nummer. Ein Tracker auf der Kontaktseite ist ein Tracker — und genau der
  wurde bisher uebersehen.
* **Aufsummieren** (`summe`): Formulare, Bilder, Woerter. Zwei Formulare auf
  zwei Seiten sind zwei Formulare.
* **Ueberall oder gar nicht** (`alle`): `all_consent` heisst „**jedes**
  Formular hat einen Einwilligungshaken". Das ist die einzige Familie, in der
  eine zusaetzliche Seite die Bewertung **verschlechtern** kann — und das ist
  richtig so: ein Formular ohne Haken ist ein Formular ohne Haken, egal auf
  welcher Seite es steht.
* **Vereinigen** (`vereinigung`): Leistungsseiten, Zertifikatsbegriffe,
  Dienste. Dieselbe Leistung auf drei Seiten verlinkt ist eine Leistung.

Wo Anteile stehen (`modern_share`, `lazy_share`), werden sie **neu aus den
Summen gerechnet**, nicht aus Anteilen gemittelt: Der Mittelwert von 100 % bei
einem Bild und 0 % bei neunzig Bildern ist 50 % und damit eine Luege.
"""
from typing import List


def _sammle(befunde: List[dict], schluessel: str) -> List[dict]:
    """Alle erhobenen Teilbefunde zu einem Block, Ausfaelle uebergangen."""
    return [b[schluessel] for b in befunde
            if isinstance(b.get(schluessel), dict) and b[schluessel].get("collected")]


def _beliebig(teile: List[dict], *namen) -> dict:
    return {name: any(bool(t.get(name)) for t in teile) for name in namen}


def _summe(teile: List[dict], *namen) -> dict:
    return {name: sum(int(t.get(name) or 0) for t in teile) for name in namen}


def _vereinigung(teile: List[dict], name: str) -> list:
    gesehen = []
    for t in teile:
        for wert in t.get(name) or []:
            if wert not in gesehen:
                gesehen.append(wert)
    return gesehen


def _anteil(zaehler: int, nenner: int) -> int:
    return round(zaehler / nenner * 100) if nenner else 0


def consent(befunde: List[dict]) -> dict:
    """Ein Consent-Tool auf irgendeiner Seite ist ein Consent-Tool."""
    teile = _sammle(befunde, "consent")
    if not teile:
        return {"collected": False}
    return {
        "collected": True,
        **_beliebig(teile, "cmp_detected", "mentions_cookie_only"),
        "cmp_names": _vereinigung(teile, "cmp_names"),
    }


def third_parties(befunde: List[dict]) -> dict:
    """Dienste ueber alle Seiten vereinigt — hier lag die groesste Luecke.

    Ein Kartendienst oder ein Analysewerkzeug laedt oft **nur** auf der
    Kontaktseite. Wer nur die Startseite prueft, bescheinigt Datensparsamkeit,
    die es nicht gibt.
    """
    teile = _sammle(befunde, "third_parties")
    if not teile:
        return {"collected": False}
    dienste = _vereinigung(teile, "services")
    return {
        "collected": True,
        "services": sorted(dienste),
        "tracking_services": sorted(_vereinigung(teile, "tracking_services")),
        "external_fonts": any(t.get("external_fonts") for t in teile),
        "maps_embedded": any(t.get("maps_embedded") for t in teile),
        "count": len(dienste),
    }


def forms(befunde: List[dict]) -> dict:
    """Formulare aller Seiten. `all_consent` gilt nur, wenn es ueberall gilt.

    **`total` zaehlt Vorkommen, nicht verschiedene Formulare.** Ein
    Newsletter-Feld im Fussbereich erscheint auf 25 Seiten und wird 25-mal
    gezaehlt — an `kompagnon.eu` gemessen: 27 Vorkommen auf 25 Seiten. Das ist
    hingenommen und nicht uebersehen: `audit_scoring` nutzt `total` nur als
    Schranke (`> 0`) und bewertet danach `all_consent` und `with_consent`. Auf
    diese beiden wirkt die Vervielfachung nicht — ein Formular ohne
    Einwilligungshaken bleibt eines ohne Haken, ob es einmal oder 25-mal
    dasteht. Wer `total` je als „so viele verschiedene Formulare hat die
    Website" liest, liest es falsch.
    """
    teile = _sammle(befunde, "forms")
    if not teile:
        return {"collected": False}
    zahlen = _summe(teile, "total", "secure_action", "post_method", "with_consent")
    gesamt = zahlen["total"]
    return {
        "collected": True,
        **zahlen,
        "all_secure": gesamt > 0 and zahlen["secure_action"] == gesamt,
        "all_consent": gesamt > 0 and zahlen["with_consent"] == gesamt,
    }


def contact(befunde: List[dict]) -> dict:
    """Kontaktwege, irgendwo gefunden.

    `form_field_count` ist die Ausnahme: gefragt ist das **schlankste**
    Formular der Website, nicht die Summe. Ein Betrieb mit einem
    Drei-Feld-Formular auf `/kontakt` hat einen kurzen Weg, auch wenn woanders
    ein langes Angebotsformular steht.
    """
    teile = _sammle(befunde, "contact")
    if not teile:
        return {"collected": False}

    felder = [t["form_field_count"] for t in teile
              if isinstance(t.get("form_field_count"), int)]
    kleinstes = min(felder) if felder else None

    return {
        "collected": True,
        **_beliebig(teile, "tel_link", "mailto_link", "form", "form_is_lean",
                    "response_time_stated", "oeffnungszeiten", "terminbuchung",
                    "anfahrt", "ansprechperson", "retourenweg", "servicekontakt"),
        "form_field_count": kleinstes,
    }


def trust(befunde: List[dict]) -> dict:
    """Vertrauenssignale, irgendwo gefunden.

    `signal_count` wird aus den zusammengefassten Einzelsignalen **neu
    gezaehlt**, nicht aufsummiert: Dieselbe Innungsmitgliedschaft auf fuenf
    Seiten ist ein Signal, nicht fuenf.
    """
    teile = _sammle(befunde, "trust")
    if not teile:
        return {"collected": False}

    namen = {name for t in teile for name in t
             if name not in ("collected", "zertifikate", "zertifikat_begriffe",
                             "signal_count")}
    signale = _beliebig(teile, *sorted(namen))
    begriffe = _vereinigung(teile, "zertifikat_begriffe")

    return {
        "collected": True,
        **signale,
        "zertifikate": bool(begriffe),
        "zertifikat_begriffe": begriffe,
        "signal_count": sum(1 for v in signale.values() if v) + bool(begriffe),
    }


def services(befunde: List[dict]) -> dict:
    """Leistungsseiten ueber alle Seiten, je Pfad einmal.

    Bisher zaehlten nur die **Links** der Startseite. Eine Leistungsseite, die
    nur aus dem Fussbereich einer Unterseite verlinkt ist, war unsichtbar.
    """
    teile = _sammle(befunde, "services")
    if not teile:
        return {"collected": False}

    je_pfad: dict = {}
    for t in teile:
        for seite in t.get("seiten") or []:
            pfad = seite.get("pfad")
            if pfad:
                je_pfad.setdefault(pfad, set()).update(seite.get("begriffe") or [])

    seiten = [{"pfad": p, "begriffe": sorted(b)} for p, b in sorted(je_pfad.items())]
    return {
        "collected": True,
        "service_page_count": len(seiten),
        "seiten": seiten,
        "pages": [s["pfad"] for s in seiten[:12]],
    }


def freshness(befunde: List[dict]) -> dict:
    """Das **neueste** Jahr gewinnt — ein alter Blogbeitrag macht die Seite
    nicht veraltet, ein aktuelles Datum irgendwo macht sie aktuell."""
    teile = _sammle(befunde, "freshness")
    if not teile:
        return {"collected": False}
    jahre = [t["copyright_year"] for t in teile if isinstance(t.get("copyright_year"), int)]
    return {
        "collected": True,
        "copyright_year": max(jahre) if jahre else None,
        **_beliebig(teile, "copyright_current", "has_dated_content", "mentions_update"),
    }


def shop(befunde: List[dict]) -> dict:
    teile = _sammle(befunde, "shop")
    if not teile:
        return {"collected": False}
    zeichen = _vereinigung(teile, "signals")
    return {"collected": True, "is_shop": bool(zeichen), "signals": zeichen}


def cta(befunde: List[dict]) -> dict:
    """Handlungsaufforderungen aller Seiten, aufsummiert.

    Anders als bei den Leistungsseiten wird hier **nicht** entdoppelt: Ein
    „Jetzt anfragen" auf jeder Unterseite ist tatsaechlich auf jeder Seite ein
    Angebot zu handeln, und genau das bewertet das Kriterium.
    """
    teile = _sammle(befunde, "cta")
    if not teile:
        return {"collected": False}
    elemente = [e for t in teile for e in (t.get("elemente") or [])]
    return {
        "collected": True,
        "cta_count": sum(int(t.get("cta_count") or 0) for t in teile),
        "elemente": elemente[:40],
        "examples": [e.get("text") for e in elemente[:5]],
        "has_cta": bool(elemente),
    }


def images(befunde: List[dict]) -> dict:
    """Bilder aller Seiten. Anteile werden aus den Summen neu gerechnet."""
    teile = _sammle(befunde, "images")
    if not teile:
        return {"collected": False}

    zahlen = _summe(teile, "total", "modern_format", "legacy_format",
                    "lazy_loading", "with_dimensions", "sampled", "oversized")
    gesamt = zahlen["total"]
    return {
        "collected": True,
        **zahlen,
        "modern_share": _anteil(zahlen["modern_format"], gesamt),
        "lazy_share": _anteil(zahlen["lazy_loading"], gesamt),
        "dimension_share": _anteil(zahlen["with_dimensions"], gesamt),
    }


def shop_legal_markers(befunde: List[dict]) -> dict:
    """AGB, Widerruf, Versand — irgendwo auf der Website genuegt."""
    teile = [b["shop_legal_markers"] for b in befunde
             if isinstance(b.get("shop_legal_markers"), dict)]
    if not teile:
        return {}
    namen = {n for t in teile for n in t}
    return {n: any(bool(t.get(n)) for t in teile) for n in sorted(namen)}


#: Block → Zusammenfassung. Was hier nicht steht, bleibt Sache der Startseite.
ZUSAMMENFASSUNGEN = {
    "consent": consent,
    "third_parties": third_parties,
    "forms": forms,
    "contact": contact,
    "trust": trust,
    "services": services,
    "freshness": freshness,
    "shop": shop,
    "cta": cta,
    "images": images,
}


def fasse_zusammen(befunde: List[dict]) -> dict:
    """Alle Bloecke auf einmal, plus die Summen, die keinen Block haben."""
    ergebnis = {name: fn(befunde) for name, fn in ZUSAMMENFASSUNGEN.items()}
    ergebnis["shop_legal_markers"] = shop_legal_markers(befunde)
    ergebnis["word_count"] = sum(int(b.get("word_count") or 0) for b in befunde)
    return ergebnis
