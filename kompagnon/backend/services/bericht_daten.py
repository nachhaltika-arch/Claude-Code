# -*- coding: utf-8 -*-
"""Die Daten der Berichtsseite — aus Befund und Katalog (L-191, 10.09.2026).

**Was hier entsteht und was nicht.** Diese Datei fuellt den Datenvertrag der
Vorlage `vorlagen/bericht.html`: 63 Platzhalter, neun Listen. Sie **rechnet
nichts neu**. Punkte, Kategorien und Kriterien kommen aus `widget_report`,
die Massnahmen aus `audit_massnahmen`, Preis und Leistungen aus der
Katalogzeile. Eine zweite Rechnung waere eine zweite Wahrheit — genau L-29,
nur mit Punkten statt Preisen.

**Drei Abschnitte bleiben leer, und das ist kein Versehen.**

* **Vorher-nachher.** Der Entwurf zeigt drei Schieberegler mit
  Referenzbildern. Es gibt keine — die Bildplaetze im Export sind leer. Der
  Abschnitt haengt an `zeigeVergleichsbilder` und bleibt aus, bis Bilder da
  sind.
* **Branchenschnitt.** `zeigeVergleich` und `kat.schnittPos` zeichnen „den
  Schnitt vergleichbarer Betriebe". Diesen Wert gibt es im System nirgends
  (L-190). Einen zu erfinden waere schlimmer als keinen zu zeigen: Er stuende
  als Messung im Bericht beim Kunden.
* **FAQ und Ablauf.** Redaktionelle Texte, die es noch nicht gibt. Leere
  Listen schalten ihre Abschnitte ab, statt eine Ueberschrift ohne Inhalt
  stehen zu lassen.
"""
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

#: Ab welchem Anteil eine Kategorie gruen, gelb oder rot ist. Dieselben
#: Schwellen wie im Teaser — zwei Skalen fuer dieselbe Zahl waeren eine
#: Einladung zum Missverstaendnis.
SCHWELLE_GUT = 70
SCHWELLE_MITTEL = 50

#: Wie lange ein Angebot gilt — aus dem Angebotsbaukasten.
ANGEBOT_GUELTIG_TAGE = 30


def _farbe(anteil: int) -> str:
    from services import brand

    if anteil >= SCHWELLE_GUT:
        return brand.SUCCESS
    if anteil >= SCHWELLE_MITTEL:
        return brand.WARN
    return brand.ERROR


def _kategorien(audit, items, sources, belege) -> list:
    """Kategorien und ihre Kriterien in der Form, die die Vorlage erwartet."""
    from services import brand
    from services.audit_criteria import Source
    from services.widget_report import AUSSER_WERTUNG, SOURCE_MARKS
    from services.widget_report import _kategorien as roh_kategorien

    ergebnis = []
    for eintrag in roh_kategorien(items, sources):
        kategorie = eintrag["kategorie"]
        zeilen = []
        for crit in kategorie.criteria:
            quelle = sources.get(crit.key, Source.NOT_COLLECTED.value)
            zeichen, farbe = SOURCE_MARKS.get(quelle, ("○", brand.TEXT_30))
            nicht_erhoben = quelle in AUSSER_WERTUNG
            zeilen.append({
                "label": crit.label,
                # „–" statt „0/3": **Nicht erhoben ist nicht null.** Eine 0
                # hiesse geprueft und nicht erfuellt.
                "value": "–" if nicht_erhoben
                         else f"{int(items.get(crit.key, 0) or 0)}/{crit.max_points}",
                "mark": zeichen,
                "markFarbe": farbe,
                "hint": crit.hint or "",
                "quelle": "" if nicht_erhoben else (belege.get(crit.key) or ""),
                # Nicht erhobene Zeilen treten zurueck, verschwinden aber
                # nicht: Wer sie weglaesst, verschweigt eine Messluecke.
                "opacity": "0.55" if nicht_erhoben else "1",
            })
        ergebnis.append({
            "label": kategorie.label,
            "wert": f"{eintrag['punkte']}/{eintrag['maximum']}",
            "breite": f"{eintrag['anteil']}%",
            "farbe": _farbe(eintrag["anteil"]),
            # **Text, kein Wahrheitswert.** Die Vorlage setzt das Feld an
            # zwei Stellen ein: als Bedingung *und* als sichtbaren Zusatz
            # neben der Punktzahl. Ein `True` stand dort als „true".
            # Leer heisst: alles gemessen, es gibt nichts zu sagen — und
            # der Zusatz entfaellt mitsamt seinem Trenner.
            "geprueft": ("" if eintrag["erhoben"] == eintrag["kriterien"]
                         else f"{eintrag['erhoben']} von {eintrag['kriterien']} erhoben"),
            # Der Branchenschnitt fehlt im System (L-190) — leer heisst: kein
            # Strich. Erfundene Vergleichswerte stuenden als Messung da.
            "schnittPos": "",
            "kriterien": zeilen,
        })
    return ergebnis


def _rabattpreis(netto, satz: str) -> str:
    """Der Preis nach Nachlass — oder leer, wenn es keinen gibt.

    Der Satz kommt als Text aus einer Einstellung („25 % Rabatt fuer die
    ersten 25 Kunden"). Gerechnet wird mit der ersten Prozentzahl darin;
    steht keine drin, gibt es keinen Rabattpreis. **Leer ist die sichere
    Antwort:** Ein falsch gelesener Satz darf keinen erfundenen Preis
    erzeugen.
    """
    import re

    if not netto or not satz:
        return ""
    treffer = re.search(r"(\d{1,2})\s*%", str(satz))
    if not treffer:
        return ""
    prozent = int(treffer.group(1))
    if not 0 < prozent < 100:
        return ""
    return _geld(float(netto) * (100 - prozent) / 100) + " netto"


def _groesste_luecken(roh, anzahl: int = 4) -> list:
    """Die groessten Luecken — als **Fehlbetrag**, nicht als Gewinn.

    Sortiert nach dem Abstand zum Maximum. Ein Kriterium mit 0 von 4 steht
    vor einem mit 1 von 2, obwohl der naechste Schritt dort vielleicht mehr
    braechte: Gefragt ist, wo am meisten fehlt.
    """
    mit_luecke = [m for m in roh if (m.maximum - m.erreicht) > 0]
    mit_luecke.sort(key=lambda m: m.maximum - m.erreicht, reverse=True)
    return [{"name": m.label, "punkte": f"−{m.maximum - m.erreicht}"}
            for m in mit_luecke[:anzahl]]


def _massnahmen_roh(audit, items, sources) -> list:
    """Was der Relaunch am Ergebnis aendert — gelesen, nicht formuliert.

    `audit_massnahmen` leitet die Saetze aus den Abstufungen am Kriterium ab
    (BUCH-F1/L-111). Sie stehen damit in Bericht, Buch und Bewertung gleich
    — und koennen nicht auseinanderlaufen.
    """
    try:
        from services import audit_massnahmen
    except Exception as fehler:  # noqa: BLE001
        logger.warning("Massnahmen nicht ladbar: %s", fehler)
        return []

    try:
        return list(audit_massnahmen.massnahmen(items, sources))
    except Exception as fehler:  # noqa: BLE001
        logger.warning("Massnahmen nicht berechenbar: %s: %s",
                       type(fehler).__name__, fehler)
        return []


def _massnahmen(roh) -> list:
    """Die Rohliste in die Form der Vorlage."""
    ergebnis = []
    for m in roh:
        ergebnis.append({
            "titel": m.label,
            # Der Ist-Stand in der Sprache des Katalogs: „3 von 6 Punkten".
            "befund": f"{m.erreicht} von {m.maximum} Punkten",
            # **Der naechste Schritt, nicht der weiteste** — so leitet
            # `audit_massnahmen` ihn ab, und so steht er hier.
            "detail": m.schritt,
            "punkte": f"+{m.schritt_gewinn}" if m.schritt_gewinn else "",
        })
    return ergebnis


def _produkt(db, slug: str) -> dict:
    from sqlalchemy import text as _text

    try:
        zeile = db.execute(_text(
            "SELECT slug, name, price_netto, price_brutto, delivery_days, features "
            "  FROM products WHERE slug = :s"), {"s": slug}).mappings().first()
    except Exception as fehler:  # noqa: BLE001
        db.rollback()
        logger.warning("Produkt %s nicht lesbar: %s", slug, fehler)
        return {}
    return dict(zeile) if zeile else {}


def _geld(wert) -> str:
    try:
        return f"{float(wert):,.2f}".replace(",", "#").replace(".", ",").replace("#", ".") + " €"
    except (TypeError, ValueError):
        return ""


def _feld(audit, name: str) -> dict:
    """Ein JSON-Feld des Befunds — auch wenn es schon ausgepackt ist.

    `widget_report._json_field` parst **nur Zeichenketten** und gibt fuer
    einen bereits ausgepackten `dict` den Rueckfall zurueck, also `{}`.
    Produktiv ist die Spalte Text, dort faellt das nie auf; beim ersten
    Trockenlauf mit einem echten Woerterbuch stand die halbe Seite leer.
    Ein Umweg, der nur bei einer Attrappe auftritt, ist trotzdem einer.
    """
    from services.widget_report import _json_field

    roh = getattr(audit, name, None)
    if isinstance(roh, dict):
        return roh
    return _json_field(roh, {})


def _einordnung_satz(audit) -> str:
    """Wogegen bewertet wurde — als **Text**, nicht als Markup.

    `widget_report._einordnung` liefert fertiges HTML fuer die alte Seite.
    Die Vorlagensprache schuetzt jeden Wert; roh eingesetzt stuende hier ein
    `<div style=…>` im Fliesstext. Statt eine Ausnahme in die Sprache zu
    bauen, wird der Satz entkleidet — die Gestaltung kommt aus der Vorlage.
    """
    import re

    try:
        from services.widget_report import _einordnung

        roh = _einordnung(audit) or ""
    except Exception as fehler:  # noqa: BLE001
        logger.warning("Einordnung nicht bildbar: %s", fehler)
        return ""
    text = re.sub(r"<[^>]+>", " ", roh)
    return re.sub(r"\s+", " ", text).strip()


def _erhebungssatz(audit) -> str:
    """Wie viel ueberhaupt gemessen werden konnte — oder gar nichts."""
    anteil = getattr(audit, "coverage", None)
    if not anteil:
        return ""
    return f"{int(anteil)} % der Kriterien konnten geprüft werden."


def _rechtsbefund(audit) -> str:
    """Die Ausschlussgruende in einem Satz — oder leer.

    **Leer heisst: kein roter Kasten.** Der Entwurf behauptete dort konkrete
    Maengel; ein Bericht, der einem Betrieb ohne Befund einen vorhaelt, ist
    schlimmer als einer ohne Kasten.
    """
    from services.widget_report import _json_field

    gruende = _json_field(getattr(audit, "blockers", None), [])
    if not gruende:
        return ""
    texte = [str(g.get("text") or g.get("label") or g) if isinstance(g, dict) else str(g)
             for g in gruende]
    return " ".join(t.rstrip(".") + "." for t in texte if t)


def aufbauen(db, audit, einstellungen: dict = None) -> dict:
    """Alle Felder der Vorlage — einmal, aus einer Hand."""
    einstellungen = einstellungen or {}
    items = _feld(audit, "item_scores")
    sources = _feld(audit, "item_sources")
    belege = _feld(audit, "item_belege")

    punkte = int(getattr(audit, "total_score", 0) or 0)
    kategorien = _kategorien(audit, items, sources, belege)
    massnahmen_roh = _massnahmen_roh(audit, items, sources)
    massnahmen = _massnahmen(massnahmen_roh)
    relaunch = _produkt(db, "websprint_relaunch")
    check = _produkt(db, "check_plus")

    # **Schlichte Zeichenketten, keine Objekte.** Die Vorlage schreibt im
    # Leistungsumfang `{{ l }}`, nicht `{{ l.name }}` — mit einem Woerterbuch
    # stand dort dessen Python-Darstellung. Die Schleife ueber `luecken`
    # benutzt dieselbe Laufvariable `l`, aber mit `.name`/`.punkte`; wer nur
    # eine der beiden ansieht, baut die andere falsch.
    leistungen = list(relaunch.get("features") or [])

    eckdaten = []
    if relaunch.get("delivery_days"):
        eckdaten.append({"label": "Bauzeit", "wert": f"{relaunch['delivery_days']} Werktage"})
    if relaunch.get("price_netto"):
        eckdaten.append({"label": "Festpreis", "wert": _geld(relaunch["price_netto"]) + " netto"})
    if relaunch.get("price_brutto"):
        eckdaten.append({"label": "Zahlbetrag", "wert": _geld(relaunch["price_brutto"]) + " brutto"})
    eckdaten.append({"label": "Zahlung", "wert": "vollständig bei Auftragserteilung"})

    return {
        "firma": getattr(audit, "company_name", "") or getattr(audit, "website_url", ""),
        "datum": datetime.utcnow().strftime("%d.%m.%Y"),
        "punkte": punkte,
        "luecke": max(0, 100 - punkte),
        "produktName": relaunch.get("name") or "Websprint Relaunch",
        "preis": _geld(relaunch.get("price_netto")) + " netto" if relaunch else "",
        "bauzeit": relaunch.get("delivery_days") or "",
        "ctaLabel": "Angebot ansehen",

        # Wogegen bewertet wurde — derselbe Satz wie im heutigen Bericht.
        # Der Entwurf hatte hier ein festes Urteil („Die Inhalte Ihrer Seite
        # sind im Kern verwendbar"), das fuer eine Seite mit 20 Punkten
        # falsch waere.
        "einordnung": _einordnung_satz(audit),
        # Statt „78 % der Kriterien konnten geprueft werden" der wirkliche
        # Erhebungsgrad. Ohne Wert kein Satz — eine erfundene Quote waere
        # eine Aussage ueber die Guete des eigenen Berichts.
        "erhebungssatz": _erhebungssatz(audit),
        # Der rote Kasten kommt aus den Ausschlussgruenden. Kein Befund,
        # kein Kasten: Der Entwurf behauptete dort konkrete Maengel („kein
        # Consent-Tool erkannt, 0 von 4 Punkten"), die niemand gemessen hat.
        "rechtsbefund": _rechtsbefund(audit),

        "kategorien": kategorien,
        "massnahmen": massnahmen,
        # **Was fehlt, nicht was es bringt** (Entwurf v2, 10.09.2026). Die
        # erste Fassung zeigte hier den Punktgewinn des naechsten Schritts
        # („+3"). Der Entwurf zeigt die **fehlenden** Punkte („−4") — und
        # beantwortet damit die Frage, die der Betrieb stellt: „Was fehlt
        # mir?" statt „Was bekomme ich?". Dieselbe Rechnung, andere
        # Blickrichtung; erfunden wird nichts.
        "luecken": _groesste_luecken(massnahmen_roh),
        "leistungen": leistungen,
        "eckdaten": eckdaten,

        # Check PLUS steht nur da, wenn es das Produkt gibt.
        # Ebenfalls schlichte Zeichenketten: die Vorlage schreibt `{{ c }}`.
        "checkPlus": list(check.get("features") or []),
        "zusatz": ([{"name": check.get("name") or "Check PLUS",
                     "preis": _geld(check.get("price_netto")) + " netto"}]
                   if check else []),

        # Redaktionelle Bloecke — leer heisst: Abschnitt aus.
        "faq": [],
        "ablauf": [],

        # Schalter. Alle drei aus, und jeder aus einem eigenen Grund —
        # siehe Kopftext.
        # ── Drei Zusagen des Entwurfs ohne Deckung, alle aus ──────────
        # **Rabatt.** „25 % fuer die ersten 25 Kunden" samt Code-Feld steht
        # im Entwurf; im Katalog gibt es weder den Nachlass noch ein
        # Rabattfeld im Bestellformular. Ein Preisversprechen, das die Kasse
        # nicht kennt, ist ein Anruf, kein Verkauf.
        "rabattsatz": einstellungen.get("bericht_rabattsatz", ""),
        # **Der Rabattpreis wird gerechnet, nicht eingetragen** (Entwurf v2
        # fuehrt ihn als eigenes Feld mit 2.625 € netto). Zwei Zahlen von
        # Hand zu pflegen ist die Bauart, aus der L-29 entstand: Wer den
        # Festpreis aendert und den Rabattpreis vergisst, hat einen Nachlass
        # von 25 % auf einen Preis, den es nicht mehr gibt.
        "preisRabatt": _rabattpreis(relaunch.get("price_netto"),
                                    einstellungen.get("bericht_rabattsatz", "")),
        # **Abnahmezusage.** Der Entwurf sagt 96 Punkte, der
        # Angebotsbaukasten sagt unter G1 mindestens 85. Zwei Zahlen fuer
        # dieselbe Garantie — welche gilt, ist eine Entscheidung.
        "abnahmepunkte": einstellungen.get("bericht_abnahmepunkte", ""),
        # **Abmahn-Groessenordnung.** Der Entwurf traegt an dieser Stelle
        # selbst den Hinweis „Quelle bitte ergaenzen — Zahl erst
        # veroeffentlichen, wenn belegt".
        "zeigeAbmahnhinweis": bool(einstellungen.get("bericht_abmahnhinweis")),

        # Stufe und Gültigkeit — beides steht im Befund bzw. im Baukasten.
        "stufe": getattr(audit, "level", "") or "",
        "gueltigBis": (datetime.utcnow() + timedelta(days=ANGEBOT_GUELTIG_TAGE)
                       ).strftime("%d.%m.%Y"),
        "checkPlusPreis": (_geld(check.get("price_netto")) + " netto") if check else "",
        "checkPlusTage": check.get("delivery_days") or "",

        # ── Drei Aussagen ueber die Seite des Kunden, alle leer ────────
        # Der Entwurf traegt sie als Beispieltext: „Ihre Seite ist aelter
        # als vier Jahre und in Teilen rechtlich offen", „Ihre Website
        # macht auf den ersten Blick einen zeitgemaessen Eindruck". Beides
        # liest sich wie ein Befund und ist keiner — fuer einen Betrieb mit
        # 20 Punkten waere der erste Satz schlicht falsch. Sie bleiben leer,
        # bis jemand sie **aus der Analyse** ableitet.
        "angebotsbegruendung": "",
        "befundText": "",
        # **Knappheit.** „Zwei Sprint-Plaetze im Oktober frei" ist eine
        # Aussage ueber die eigene Auslastung. Sie muss stimmen, wenn sie
        # dasteht — deshalb eine Einstellung, kein fester Satz.
        "knappheit": einstellungen.get("bericht_knappheit", ""),

        "zeigeVergleich": False,
        "zeigeVergleichsbilder": False,
        "zeigeSticky": True,

        "logoUrl": einstellungen.get("bericht_logo_url", ""),
        "ohneLogo": not einstellungen.get("bericht_logo_url", ""),
        "portraitUrl": einstellungen.get("bericht_portrait_url", ""),
    }
