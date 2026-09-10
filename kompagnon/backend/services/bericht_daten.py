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

#: Die beiden Leistungsgrenzen des Relaunch, wörtlich aus dem
#: Leistungsverzeichnis `docs/produkte/ws-rel-01.md`. Sie stehen hier und
#: nicht im Datensatz, weil es dafür keine Spalte gibt und zwei Spalten für
#: zwei Beschriftungen mehr kosten als sie tragen. Damit sie nicht vom Blatt
#: abdriften, prüft `test_relaunch_eckdaten` beide gegen das Blatt.
SEITENUMFANG = "bis 6 Seiten"
KORREKTURSCHLEIFEN = "1 enthalten"

#: Ab dieser Punktzahl braucht eine Seite keinen Relaunch mehr — die
#: Abnahmezusage des Standards (G1) nennt sie als Untergrenze. Oberhalb
#: davon bleibt die Angebotsbegründung leer.
GARANTIEPUNKTE = 85

#: Wo das Portrait des Ansprechpartners im Frontend liegt. Es wird auf der
#: Berichtsseite höchstens 168 px breit und rund beschnitten dargestellt —
#: die Datei ist deshalb 500 px breit (trägt auch Retina) und wiegt 58 kB
#: statt der 2,5 MB des Originals. Wer sie austauscht, achte auf beides:
#: Die Seite wird oft am Handy aus einer E-Mail geöffnet.
PORTRAIT_DATEI = "/team/m_vonschaumburg-lippe.jpg"

#: Die zubuchbaren Leistungen, wörtlich aus dem Leistungsverzeichnis
#: `docs/produkte/ws-rel-01.md`, Abschnitt 3 („Zusatzleistungen").
#:
#: **Warum hier und nicht im Katalog** — L-29 sagt: Preise kommen aus
#: `products`. Diese sieben sind dort nicht, weil sie keine kaufbaren
#: Produkte sind: Es gibt keine Kasse, keinen Auftragsweg und keine
#: Auftragsbestätigung dafür. Sie in den Katalog zu legen, hiesse sieben
#: Zeilen anzulegen, die nichts auslösen — und L-29 schützt vor einer
#: zweiten Preisquelle, nicht vor einer Preisliste.
#:
#: Abdriften ist trotzdem möglich, deshalb prüft
#: `test_zusatzleistungen_stehen_so_im_blatt` jede Zeile gegen das Blatt.
ZUSATZLEISTUNGEN = (
    ("Jede weitere Seite über 6 hinaus", "290 €"),
    ("Texterstellung statt Übernahme, je Seite", "350 €"),
    ("Fotoproduktion vor Ort, halber Tag", "890 €"),
    ("Rechtstexte über Partnerkanzlei", "ab 250 €"),
    ("GEO/GAIO Add-on", "1.200 €"),
    ("Pflege Basic ab Abnahme", "79 €/Mon."),
    ("Pflege Pro ab Abnahme", "149 €/Mon."),
)

#: Der Ablauf, aus derselben Quelle (Abschnitt 4, „Ablauf und Termine").
#: Das Blatt führt sieben Zeilen (Phase 0 bis 6); Abnahmeaudit und Go-Live
#: stehen hier zusammen, weil sie für den Kunden ein Schritt sind — sechs
#: Spalten, wie die Überschrift sagt.
ABLAUF = (
    {"tage": "Phase 0", "titel": "Auftrag",
     "text": "Auftragserteilung und Anforderung Ihrer Unterlagen."},
    {"tage": "Tag 0", "titel": "Fristbeginn",
     "text": "Ihre Mitwirkungsleistungen liegen vollständig vor."},
    {"tage": "Tag 1–6", "titel": "Struktur und Rohaufbau",
     "text": "Seitenplan umgesetzt, Komponenten stehen."},
    {"tage": "Tag 7–10", "titel": "Inhalte und Bilder",
     "text": "Texte überarbeitet, Bildmaterial aufbereitet, Feinaufbau."},
    {"tage": "Tag 11–12", "titel": "Ihre Korrekturschleife",
     "text": "Kundenvorschau, eine Schleife ist enthalten."},
    {"tage": "Tag 13–14", "titel": "Abnahme und Go-Live",
     "text": "Abnahmeaudit, DNS-Umstellung, Protokoll, Einweisung."},
)


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


def _kaufweg(roh, rueckfall: str) -> str:
    """Eine Kaufadresse — oder der Kalender.

    Der Wert kommt aus einer Einstellung im Werkzeug und landet in einem
    `href` auf einer Seite, die ein Kunde oeffnet. `javascript:` und `data:`
    gehoeren dort nicht hin; dieselbe Schranke wie in
    `check_plus_angebot._sichere_adresse`.
    """
    wert = (roh or "").strip()
    if wert.startswith(("https://", "http://", "/")):
        return wert
    if wert:
        logger.warning("Kaufadresse verworfen (Schema): %r", wert[:40])
    return rueckfall


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
    **Am 10.09.2026 korrigiert.** Hier stand der rohe Wert aus dem Befund,
    und der ist eine Kennung: `detect_blockers` legt `"kein_impressum"` ab,
    nicht den Satz dazu. Auf der Berichtsseite las ein Kunde damit
    „kein_impressum. keine_datenschutzerklaerung." — Datenbankinhalt in
    einem roten Kasten auf einer Verkaufsseite.

    Die Übersetzung gab es die ganze Zeit: `BLOCKER_LABELS` im Katalog, seit
    es die K.-o.-Kriterien gibt. Die alte Berichtsmail benutzt sie
    (`widget_report._blocker_block`), die neue Seite hatte sie schlicht nicht
    mitbekommen. Gefunden in der Trichter-Vorschau, nicht produktiv.

    Eine unbekannte Kennung wird **weggelassen**, nicht durchgereicht: Ein
    neuer Blocker ohne Text ist ein Fehler im Katalog, und ein Kunde soll ihn
    nicht buchstabieren müssen.
    """
    from services.audit_criteria import BLOCKER_LABELS
    from services.widget_report import _json_field

    gruende = _json_field(getattr(audit, "blockers", None), [])
    if not gruende:
        return ""

    texte = []
    for grund in gruende:
        if isinstance(grund, dict):
            text = grund.get("text") or grund.get("label") or grund.get("titel") or ""
        else:
            text = BLOCKER_LABELS.get(str(grund), "")
        if text:
            texte.append(str(text).rstrip(".") + ".")
    return " ".join(texte)


def _faq(abnahmepunkte: str) -> list:
    """Die sechs Fragen über dem Ansprechpartner (Vorgabe David, 10.09.2026).

    Jede Antwort ist gegen `docs/produkte/ws-rel-01.md` geprüft. **Drei
    davon standen im Entwurf anders**, und zwar so, dass sie mehr versprachen
    als der Vertrag hergibt:

    1. **Hosting.** Der Entwurf sagte „Sie können Ihr bestehendes Hosting
       behalten." Im Leistungsverzeichnis steht unter 3.2 die *Einrichtung*
       des Hostings samt SSL und Weiterleitungen als enthaltene Leistung —
       und in der Merkmalsliste „Hosting, SSL, Weiterleitungen, Umstellung
       der Domain". Beides nebeneinander liest sich widersprüchlich. Die
       Antwort sagt jetzt, was im Vertrag steht.

    2. **Barrierefreiheitserklärung.** Der Entwurf versprach, sie technisch
       korrekt einzubauen. Sie steht **nicht** im Leistungsumfang — dort
       stehen „Grundlagen der Barrierefreiheit: Kontraste, Tastatur,
       Semantik". Der Audit-Katalog führt sie als eigenes Kriterium
       (`rc_bfsg`). Entweder gehört sie in die Merkmalsliste, oder sie darf
       hier nicht zugesagt werden; bis das entschieden ist, steht sie nicht
       da. **Gemeldet an David am 10.09.2026.**

    3. **„mindestens 96 Punkte".** Dieselbe Zahl wie im Angebotskasten und
       dasselbe Problem: Der Standard nennt 85. Der Satz erscheint nur,
       wenn eine Abnahmezusage eingetragen ist, und nennt dann deren Zahl.
    """
    nicht_gefaellt = "Eine Korrekturschleife ist enthalten, jede weitere kostet 290 € netto."
    if abnahmepunkte:
        nicht_gefaellt += (f" Erreicht das Abnahmeaudit nicht mindestens "
                           f"{abnahmepunkte} Punkte, wird ohne Aufpreis nachgearbeitet.")

    return [
        {"frage": "Wer schreibt die Texte?",
         "antwort": "Ihre bestehenden Texte werden übernommen, gekürzt und für "
                    "Suche und Lesbarkeit strukturiert. Texterstellung von Grund "
                    "auf ist zubuchbar."},
        {"frage": "Was, wenn ich Inhalte spät liefere?",
         "antwort": "Die 14 Werktage beginnen erst, wenn Ihre Unterlagen "
                    "vollständig vorliegen. Ein späterer Start kostet keinen "
                    "Aufpreis, verschiebt aber den Abnahmetermin."},
        {"frage": "Wer hostet, was kostet der Betrieb danach?",
         "antwort": "Einrichtung des Hostings, SSL und die Weiterleitungen Ihrer "
                    "bisherigen Adressen sind enthalten. Wartung, Updates und "
                    "Überwachung danach sind als monatliche Position zubuchbar, "
                    "nicht Pflicht."},
        {"frage": "Was passiert mit meinen Google-Rankings?",
         "antwort": "Alle bestehenden Adressen werden erfasst und, wo nötig, per "
                    "301 weitergeleitet. Titel und Beschreibungen werden ergänzt, "
                    "nicht ausgetauscht."},
        {"frage": "Wer haftet für die Rechtstexte?",
         "antwort": "Einwilligungswerkzeug und Formulareinwilligung bauen wir "
                    "technisch korrekt ein. Die inhaltliche Prüfung von Impressum "
                    "und Datenschutzerklärung gehört in eine Kanzlei und ist nicht "
                    "enthalten — die Vermittlung über unsere Partnerkanzlei schon."},
        {"frage": "Was, wenn mir das Ergebnis nicht gefällt?",
         "antwort": nicht_gefaellt},
    ]


def _portrait(eingestellt: str) -> str:
    """Die Bildadresse des Ansprechpartners — mit Datei als Rückfall.

    **Warum eine Datei und nicht nur eine Einstellung.** Das Feld gibt es
    seit dem 10.09.2026; bis dahin war es nirgends einzutragen, und unter
    „Ihr Ansprechpartner" stand ein Name ohne Gesicht. Eine Einstellung
    allein hätte das nur halb gelöst: Sie lebt in der Datenbank, muss in
    jeder Umgebung noch einmal gesetzt werden und ist nach einem Umzug
    wieder leer. Das Bild liegt deshalb im Frontend und wird von dort
    ausgeliefert — es ist einfach da.

    **Die Adresse zeigt aufs Frontend, nicht auf diesen Server.** Der
    Bericht kommt von `api.…`, das Bild von `kas.…`; wer hier einen
    relativen Pfad einsetzt, bekommt eine 404 vom Backend. `public_base_url`
    liefert in jeder Umgebung die richtige — auf Staging die von Staging.

    Eine Einstellung schlägt die Datei: Wer einen anderen Ansprechpartner
    einträgt, bekommt ihn.
    """
    from services.base_urls import public_base_url
    from services.check_plus_angebot import _sichere_adresse

    if eingestellt:
        sicher = _sichere_adresse(eingestellt)
        if sicher:
            return sicher
    return f"{public_base_url()}{PORTRAIT_DATEI}"


def _angebotsbegruendung(punkte: int, vorgabe: str) -> str:
    """Warum ausgerechnet dieses Paket — abgeleitet, nicht behauptet.

    Der Entwurf schlug hier vor: „Ihre Seite ist älter als vier Jahre und in
    Teilen rechtlich offen, die Inhalte tragen aber noch." Der Satz liest
    sich wie ein Befund und ist keiner: Das Alter der Seite wird nirgends
    erhoben, und für einen Betrieb, dessen Seite drei Monate alt ist, steht
    dort schlicht etwas Falsches. Ein falscher Satz über die eigene Seite
    kostet mehr Vertrauen, als ein Verkaufssatz einbringt.

    Dieselbe Bewegung — „genau dafür ist das gebaut" — lässt sich aus der
    Messung machen, die direkt darüber steht. Die Punktzahl **wurde**
    erhoben, sie ist im Bericht aufgeschlüsselt, und der Kunde kann sie
    nachrechnen.

    Oberhalb der Zusage aus dem Standard (``GARANTIEPUNKTE``) bleibt der
    Satz weg: Wer 88 Punkte hat, braucht keinen Relaunch, und ihm einen zu
    begründen wäre der zweite falsche Satz.

    ``vorgabe`` schlägt beides — wer einen eigenen Satz einträgt, bekommt ihn.
    """
    if vorgabe:
        return vorgabe
    if not punkte or punkte >= GARANTIEPUNKTE:
        return ""
    return (f"Ihre Seite erreicht heute {punkte} von 100 Punkten; die "
            f"fehlenden {100 - punkte} stehen oben einzeln im Bericht. "
            f"Genau dafür ist dieses Paket gebaut — nicht für einen Neubau, "
            f"den Sie nicht brauchen.")


def aufbauen(db, audit, einstellungen: dict = None) -> dict:
    """Alle Felder der Vorlage — einmal, aus einer Hand."""
    einstellungen = einstellungen or {}
    items = _feld(audit, "item_scores")
    sources = _feld(audit, "item_sources")
    belege = _feld(audit, "item_belege")

    from services.widget_report import termin_url

    termin = termin_url(einstellungen.get("widget_booking_url", ""))
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

    # ── Die drei Eckdaten des Angebots ────────────────────────────────
    # **Am 10.09.2026 ausgetauscht** (Entwurf „Bericht Conversion v2",
    # Vorgabe David). Hier standen Bauzeit, Festpreis, Zahlbetrag und
    # Zahlungsweise — vier Felder, von denen **zwei Preise waren**. Direkt
    # darunter steht der Festpreis noch einmal, gross und einzeln. Wer die
    # Spalte von links nach rechts liest, sieht „3.500 netto · 4.165 brutto"
    # und danach noch einmal „3.500 netto" und muss selbst herausfinden,
    # dass das ein Preis ist und nicht drei.
    #
    # Die Zahlungsweise ist damit nicht verschwunden: Sie steht jetzt im
    # Kleingedruckten unter dem Knopf, zusammen mit dem Zahlbetrag brutto —
    # dort, wo man sie liest, bevor man kauft, und nicht als Kopfzahl.
    #
    # Bauzeit kommt aus dem Datensatz. Die beiden Grenzen stehen im
    # Leistungsverzeichnis `docs/produkte/ws-rel-01.md`: „bis 6 Seiten"
    # (Zeile 2.1/2.2) und „Enthalten ist eine Korrekturschleife. Jede
    # weitere Schleife: 290 € netto." Beide sind **keine Preise**, deshalb
    # faellt L-29 hier nicht — aber sie koennen vom Blatt abdriften,
    # deshalb prueft `test_relaunch_eckdaten` sie gegen das Blatt selbst.
    # Satz und Code gehoeren zusammen: Ein Nachlass ohne Code, den man
    # eintippen kann, ist eine Ankuendigung ohne Weg. Fehlt einer von
    # beiden, bleibt der Kasten weg — statt halb dazustehen.
    rabattsatz = (einstellungen.get("bericht_rabattsatz") or "").strip()
    rabattcode = (einstellungen.get("bericht_rabattcode") or "").strip()
    if not (rabattsatz and rabattcode):
        rabattsatz = rabattcode = ""

    eckdaten = []
    if relaunch.get("delivery_days"):
        eckdaten.append({"label": "Bauzeit", "wert": f"{relaunch['delivery_days']} Werktage"})
    eckdaten.append({"label": "Seitenumfang", "wert": SEITENUMFANG})
    eckdaten.append({"label": "Korrekturschleife", "wert": KORREKTURSCHLEIFEN})

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
        # Der Bruttobetrag stand bis zum 10.09.2026 als vierte Kopfzahl
        # neben dem Nettopreis. Er gehoert dorthin, wo er gebraucht wird:
        # ins Kleingedruckte unter dem Kaufknopf, direkt vor der Kasse.
        "zahlbetrag": (_geld(relaunch["price_brutto"]) + " brutto"
                       if relaunch.get("price_brutto") else ""),

        # Check PLUS steht nur da, wenn es das Produkt gibt.
        # Ebenfalls schlichte Zeichenketten: die Vorlage schreibt `{{ c }}`.
        "checkPlus": list(check.get("features") or []),
        # **Leer, und das ist der Befund.** „Wenn Sie mehr brauchen" ist im
        # Entwurf die Liste der zubuchbaren Leistungen — GEO, Pflege,
        # Texterstellung. Hier stand zuerst Check PLUS, also dasselbe
        # Angebot ein zweites Mal, zwei Kaesten untereinander. Verkäuflich
        # (`status = live`) ist im Katalog ausser den beiden Websprints
        # nichts; solange das so ist, faellt der Abschnitt weg statt sich
        # selbst zu wiederholen.
        "zusatz": [{"name": name, "preis": preis}
                   for name, preis in ZUSATZLEISTUNGEN],

        # Redaktionelle Bloecke (Vorgabe David, 10.09.2026). Sie standen
        # seit dem Umbau der Seite in der Vorlage und waren leer — der
        # Abschnitt fiel damit weg. Dritter Fall desselben Musters an einem
        # Tag: gebaut, nicht angeschlossen.
        "faq": _faq(einstellungen.get("bericht_abnahmepunkte", "")),
        "ablauf": list(ABLAUF),

        # Schalter. Alle drei aus, und jeder aus einem eigenen Grund —
        # siehe Kopftext.
        # ── Drei Zusagen des Entwurfs ohne Deckung, alle aus ──────────
        # **Rabatt.** „25 % fuer die ersten 25 Kunden" samt Code-Feld steht
        # im Entwurf; im Katalog gibt es weder den Nachlass noch ein
        # Rabattfeld im Bestellformular. Ein Preisversprechen, das die Kasse
        # nicht kennt, ist ein Anruf, kein Verkauf.
        "rabattsatz": rabattsatz,
        # **Der Code steht nicht mehr fest in der Vorlage.** Bis heute war
        # „WS25" an zwei Stellen der Vorlage einbetoniert. Wer in Stripe
        # einen anderen Promo-Code anlegt, haette auf der Seite weiter den
        # alten gelesen — und der Kunde einen Code eingegeben, den die Kasse
        # nicht kennt. Jetzt kommt er aus derselben Einstellung wie der Satz.
        "rabattcode": rabattcode,
        # **Der Rabattpreis wird gerechnet, nicht eingetragen** (Entwurf v2
        # fuehrt ihn als eigenes Feld mit 2.625 € netto). Zwei Zahlen von
        # Hand zu pflegen ist die Bauart, aus der L-29 entstand: Wer den
        # Festpreis aendert und den Rabattpreis vergisst, hat einen Nachlass
        # von 25 % auf einen Preis, den es nicht mehr gibt.
        "preisRabatt": _rabattpreis(relaunch.get("price_netto"), rabattsatz),
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
        "angebotsbegruendung": _angebotsbegruendung(
            punkte, einstellungen.get("bericht_angebotsbegruendung", "")),
        "befundText": "",
        # **Knappheit.** „Zwei Sprint-Plaetze im Oktober frei" ist eine
        # Aussage ueber die eigene Auslastung. Sie muss stimmen, wenn sie
        # dasteht — deshalb eine Einstellung, kein fester Satz.
        "knappheit": einstellungen.get("bericht_knappheit", ""),

        "zeigeVergleich": False,
        "zeigeVergleichsbilder": False,
        "zeigeSticky": True,

        # ── Die Kaufwege (Wunsch David, 10.09.2026) ───────────────────
        # Der Entwurf trug zwei feste Stripe-Zahllinks im `href`. Ein
        # Kaufweg im Quelltext ist dieselbe Falle wie ein Preis im
        # Quelltext (L-29): Er wandert nicht mit, wenn das Konto wechselt.
        #
        # **Eine Adresse je Produkt, nicht je Ort.** Check PLUS wird im
        # Teaser und im Bericht angeboten; beide lesen dieselbe Einstellung.
        # Zwei waeren zwei Wahrheiten, und die zweite waere irgendwann alt.
        #
        # **Ohne Adresse fuehrt der Knopf in den Kalender** — nicht ins
        # Leere. Wer kaufen will und keinen Kaufweg findet, soll wenigstens
        # einen Termin bekommen.
        # Der Terminkalender. **Hier und nicht in `bericht_seite`**: Die
        # Kaufwege fallen darauf zurueck, also muss er gebildet sein, bevor
        # sie entstehen — an zwei Stellen berechnet waere er zwei Werte.
        "terminUrl": termin,
        "kaufUrlRelaunch": _kaufweg(einstellungen.get("bericht_kauf_relaunch_url"),
                                    termin),
        "kaufUrlCheckPlus": _kaufweg(einstellungen.get("widget_check_plus_url"),
                                     termin),

        "logoUrl": einstellungen.get("bericht_logo_url", ""),
        "ohneLogo": not einstellungen.get("bericht_logo_url", ""),
        "portraitUrl": _portrait(einstellungen.get("bericht_portrait_url", "")),
    }
