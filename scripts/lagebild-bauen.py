#!/usr/bin/env python3
"""Baut das KOMPAGNON-Lagebild aus der Lückenliste.

    python3 scripts/lagebild-bauen.py

**Warum als Skript und nicht von Hand.** Das Lagebild ist Davids
Entscheidungsgrundlage; ein Stand von gestern sieht aus wie einer von heute.
Es muss also nach jeder geschlossenen Lücke neu entstehen — und dann muss es
billig sein, sonst unterbleibt es.

**Die Zahlen zählt dieses Skript, nicht ein Mensch.** Am 22.08.2026 stand im
Kopf „7 von 11 Modulen grün"; gezählt waren es sechs. Jede Kennzahl hier
stammt aus den Daten, die darunter stehen. Auch die Zählweise selbst gehört
festgehalten: Bei den Dateigrößen (L-25) war die alte Methode nicht notiert,
und deshalb ließ sich nicht sagen, ob eine Zahl gestiegen war oder nur anders
gemessen wurde.

**Wahrheitsquelle ist `docs/soll-ist-analyse.md` § 3.** Das Lagebild ist ihre
Ansicht, nicht ihr Zwilling: Wer eine Lücke schließt, schreibt sie dort fort
und lässt danach dieses Skript laufen.

Ergebnis: `docs/lagebild/kompagnon-lagebild.html` — diese Datei wird als
Artifact veröffentlicht (derselbe Pfad hält dieselbe URL).
"""
import ast
import collections
import json
import pathlib
import re
import subprocess
import sys

WURZEL = pathlib.Path(__file__).resolve().parent.parent
QUELLE = WURZEL / "docs" / "soll-ist-analyse.md"
VORLAGE = WURZEL / "docs" / "lagebild" / "vorlage.html"
PLANDATEN = WURZEL / "docs" / "lagebild" / "plan.json"
ZIEL = WURZEL / "docs" / "lagebild" / "kompagnon-lagebild.html"

#: Wer eine Lücke schließen kann — Wunsch David, 07.09.2026.
#:
#: **Warum das ins Lagebild gehört.** Die Liste beantwortete bisher „was ist
#: offen", nicht „was kann ich davon selbst anstoßen". Zwischen einem Punkt,
#: den ein Nachmittag Programmierarbeit erledigt, und einem, der auf eine
#: Kanzlei, einen Fremdzugang oder eine Produktentscheidung wartet, liegt für
#: die Planung alles — und in der bisherigen Ansicht sahen beide gleich aus.
#:
#: Drei Werte, und die Grenze zwischen ihnen ist scharf:
#:
#:   system  Reine Arbeit am Code. Niemand muss vorher etwas entscheiden,
#:           freischalten, schreiben oder bezahlen.
#:   extern  Der Schlüssel liegt außerhalb: eine Entscheidung, eine
#:           Rechtsberatung, ein Zugang zu einem Fremdsystem, ein Inhalt, den
#:           jemand verfassen muss, oder Geld.
#:   beides  Ein Teil ist gebaut oder baubar, ein anderer wartet draußen.
#:           Diese sind die gefährlichsten: Sie sehen nach Arbeit aus, und die
#:           Arbeit endet vor der Ziellinie.
#:
#: **Ohne Eintrag gilt `system`** — die Vorgabe ist die ehrlichere: Wer eine
#: externe Abhängigkeit hat, weiß es und schreibt sie hin; wer keine hat,
#: soll nicht dadurch eine bekommen, dass jemand die Liste nicht gepflegt hat.
ZUSTAENDIGKEIT = {
    # ── Recht und Vertrag ─────────────────────────────────────────────
    "L-148": ("extern", "Anwaltliche Einordnung des maschinell erzeugten Codes. "
                        "Kein Code ändert daran etwas."),
    "L-149": ("extern", "Lizenztext des Studio-SDK lesen und gegen unseren "
                        "Gebrauch halten — juristische Prüfung."),
    "L-100": ("beides", "Gebaut ist die Strecke. Draußen warten: die vier "
                        "R2-Werte, die Workbook-Datei im Bucket und AGB samt "
                        "Widerrufsbelehrung von der Kanzlei (ORDERS_05)."),

    # ── Kampagne und Trichter (10.09.2026) ────────────────────────────
    "L-183": ("extern", "Der Hoster von kompagnon.eu sperrt das Render-"
                        "Rechenzentrum. Kein Code ändert daran etwas — die "
                        "Sperre muss dort gelöst werden."),
    "L-185": ("extern", "Die Erinnerung an den Bericht laeuft. Offen ist nur "
                        "die Entscheidung, ob die Zusage in der "
                        "Bestaetigungsmail geaendert wird — ohne sie darf an "
                        "unbestaetigte Adressen nichts gehen."),
    "L-186": ("extern", "Ein Wert in den Widget-Einstellungen: die Adresse "
                        "der Datenschutzerklärung. Kein Code."),
    "L-187": ("beides", "Verdrahtet ist alles. Draußen warten drei "
                        "Entscheidungen: draft auf live, Kaufweg (Zahllink "
                        "oder Shop) und die AGB-Fassung, ohne die der Shop "
                        "jede Bestellung abweist."),
    "L-188": ("extern", "Die Landingpage liegt nicht in diesem Repo. Der "
                        "fertige Block ist geschrieben, einsetzen muss ihn, "
                        "wer die Seite pflegt."),
    "L-189": ("beides", "Senden kann erst die Landingpage (L-188); das "
                        "Markieren als Schlüsselereignis geschieht in GA4."),
    "L-190": ("beides", "Zu entscheiden ist, wer den Branchenvergleich "
                        "erhebt — von Hand im Gespräch oder gerechnet. "
                        "Danach ist es Arbeit am Code."),
    "L-193": ("extern", "Zwei Stripe-Objekte im Dashboard: den doppelten "
                        "Preis archivieren, die tote ID entfernen."),
    "L-194": ("beides", "Drei Fundstellen im Code geben die Auswahl frei; "
                        "welche Zahlarten dann gelten, steht im Stripe-"
                        "Dashboard und ist eine Geschäftsentscheidung."),

    # ── Zugänge, Werte, Fremddienste ──────────────────────────────────
    "L-115": ("extern", "`CORS_ALLOWED_ORIGINS` an den Render-Diensten "
                        "ergänzen, sobald BUCH-08 eine Adresse hat."),
    "L-103": ("extern", "Ohne Zugang zum Google-Projekt nicht prüfbar — die "
                        "neue Schnittstelle muss dort erst freigeschaltet sein."),
    "L-146": ("extern", "Drei Tabellen produktiv fallen lassen. Die "
                        "Produktivdatenbank ist von hier nicht abfragbar."),
    "L-58":  ("extern", "`OPENAI_API_KEY` und `PERPLEXITY_API_KEY` fehlen, und "
                        "es gibt keine Ausgabengrenze — eine Geldfrage."),
    "L-85":  ("extern", "Hängt an denselben Schlüsseln wie L-58: Gebaut und "
                        "belegt ist die Rechnung, nicht die Erhebung."),
    "L-126": ("extern", "Die Zahlen liegen in der Produktivdatenbank, die von "
                        "hier nicht abfragbar ist."),
    "L-14":  ("extern", "Fachliche Beurteilung durch David — und die Daten "
                        "hängen an derselben Sperre wie L-126."),

    # ── Entscheidungen, die keine Programmierfrage sind ────────────────
    "L-114": ("extern", "Elf Befunde am Maßstab warten auf eine "
                        "Produktentscheidung, nicht auf Code."),
    "L-142": ("extern", "Neu zu entscheiden, sobald ein Kunde danach fragt — "
                        "vorher wäre jeder Bau Vorrat."),
    "L-143": ("extern", "Wunsch, aber die Reihenfolge steht: L-144 vor L-142 "
                        "vor diesem. Vorher gibt es keinen Speicher."),
    "L-144": ("extern", "Neu zu entscheiden, sobald das erste Tracking-Skript "
                        "auf eine Kundenseite kommt."),
    "L-16":  ("extern", "Neu zu entscheiden, sobald eine Kundenseite eine "
                        "Anordnung braucht, die die zwei Wireframes nicht hergeben."),
    "L-21":  ("extern", "Neu zu entscheiden, sobald ein Kunde Werbung "
                        "beauftragt — und dann lautet die Frage „selbst "
                        "schalten oder vermitteln?“"),
    "L-23":  ("extern", "Neu zu entscheiden, sobald eine Kundenseite eine "
                        "Komponente braucht, die der Katalog nicht hat."),
    "L-20":  ("extern", "Das Produktivprotokoll beantwortet die Frage in einer "
                        "Minute — schließen entscheidet David."),
    "L-182": ("extern", "Entscheiden, welcher der vier Datenblatt-Ordner gilt. "
                        "Die anderen entfernen ist danach ein Handgriff."),
    "L-60":  ("extern", "Lehrplan und Inhalte — jemand muss sie verfassen und "
                        "verantworten. Ausgedachte Schulungen wären schlimmer "
                        "als keine Akademie."),
    "L-171": ("extern", "Ein Kauf über die Kasse mit echter Karte, danach "
                        "erstatten. Das kann nur ein Mensch mit Karte."),

    # ── Beides: gebaut bis zur Grenze, dahinter wartet etwas ───────────
    "L-165": ("beides", "Der PageSpeed-Schlüssel ist produktiv gesetzt "
                        "(am 07.09. an `/health` nachgemessen). Was bleibt, "
                        "ist die Produktentscheidung aus K1: Zusage "
                        "zuschneiden oder die fehlenden Kriterien erheben."),
    "L-179": ("beides", "Erst zu klären, ob `website_content` produktiv "
                        "überhaupt existiert — dafür braucht es die "
                        "Produktivdatenbank. Danach ist es Code."),
    "L-95":  ("beides", "Messen und benennen ist Code; die Löschung der 174 "
                        "Zeilen wäre eine Entscheidung."),
    "L-106": ("beides", "Die Zusammenlegung zu Ende bringen ist Code — sie "
                        "fallen zu lassen verändert Daten und gehört zu L-105."),
    "L-154": ("beides", "Zwei der drei Kriterien sind im Code zu berichtigen; "
                        "was „einwilligungspflichtig“ heißen soll, ist eine "
                        "Produktentscheidung."),

    # Alles Übrige ist reine Arbeit am Code — siehe Vorgabe oben.
}

#: Lücken, deren Zustand sich nicht aus der Tabellenform ablesen lässt.
#: Jede braucht einen Grund — sonst wird die Liste zum Ablagefach.
HANDGESETZT = {
    # (b) ist gebaut, aber nie gegen einen echten Dienst gelaufen. Weder
    # „offen" noch „geschlossen" trifft das.
    "L-58": "teilweise",

    # Die Erinnerung an den bereitliegenden Bericht laeuft (10.09.2026).
    # Die Erinnerung an die **Bestaetigung** — dort faellt der groesste Teil
    # weg — ist bewusst nicht gebaut: Die vorausgegangene Mail sagt zu, sich
    # ohne Bestaetigung nicht von selbst zu melden. Das zu aendern ist eine
    # Entscheidung ueber das eigene Wort, keine Programmierarbeit.
    "L-185": "teilweise",

    # ── terminiert: entschieden, datiert, von einem Test gehalten ──────
    #
    # **Warum es diesen vierten Zustand gibt** (Entscheidung 01.09.2026).
    # Das Lagebild ist Davids Entscheidungsgrundlage. „Offen" hiess bis hier
    # zweierlei: *braucht eine Entscheidung* und *ist entschieden, faellig
    # ist es spaeter*. Beides in einem Topf macht die Liste laenger, als die
    # Arbeit ist — und der eigentliche Schaden ist, dass die echten offenen
    # Punkte darin untergehen.
    #
    # **Ein Eintrag darf nur hierher, wenn drei Dinge stimmen:** Die
    # Entscheidung ist gefallen und steht im Eintrag; es gibt ein Datum oder
    # eine benannte Bedingung; und ein Test wird rot, wenn der Termin
    # eintritt oder die Annahme faellt. Ohne den dritten Punkt waere
    # „terminiert" nur ein leiseres Wort fuer vergessen.
    "L-114": "terminiert",   # Fassung 2027.1; `tests/test_abstufungen_*`
                             # beziffern den verschluckten Schritt und werden
                             # rot, wenn einer dazukommt oder wegfaellt.
    "L-81": "terminiert",    # 27.09.2026; `tests/test_perplexity_altform_termin.py`
    "L-154": "terminiert",   # Fassung 2027.1 § 8; `tests/test_massstabsfragen_2027_1.py`
                             # scheitert ab dem Stichtag mit der
                             # Arbeitsanweisung im Text.
}


def produkte_lesen() -> list:
    """Der Produktkatalog — aus den Seeds gelesen, nicht abgeschrieben.

    **Der Anlass (07.09.2026, Wunsch David).** Der Produktabschnitt des
    Lagebilds zeigte „Starter 1.500 €, KOMPAGNON 2.000 €, Premium 2.800 €" —
    die Pakete, die seit **L-97 (23.08.)** durch die Websprint-Linie ersetzt
    sind. Zwei Wochen lang stand in Davids Entscheidungsgrundlage ein
    Sortiment, das es nicht mehr gibt.

    **Warum aus `migrations_runtime.py` und nicht aus den Datenblaettern.**
    Die Seeds sind das, was **produktiv in `products` steht** — und aus dieser
    Tabelle zieht die Stripe-Sitzung ihren Betrag. Die Datenblaetter sagen,
    was gelten *soll*; die Seeds, was gilt. Fuer eine Lagebeurteilung zaehlt
    das Zweite. (Wo beide auseinandergehen, ist das ein Befund fuer sich —
    siehe L-182.)

    **Die Abos stehen nicht in `products`** und kommen deshalb aus
    `services/abo_stunden.py`, das GEO-Add-on aus `services/dazubuchen.py`.
    Drei Quellen, aber jede ist die, aus der auch der Code rechnet.
    """
    quelle = (WURZEL / "kompagnon" / "backend" / "migrations_runtime.py").read_text(encoding="utf-8")
    muster = re.compile(
        r"\('(?P<slug>[a-z_0-9]+)',\s*\n?\s*'(?P<name>[^']+)',\s*\n?\s*"
        r"'(?P<kurz>[^']*)',\s*\n?\s*"
        r"(?P<brutto>[\d.]+|\{[^}]+\}), (?P<netto>[\d.]+|\{[^}]+\}), (?P<steuer>\d+|\{[^}]+\}), "
        r"'(?P<art>\w+)', (?P<tage>\d+), '(?P<status>\w+)'", re.S)

    heraus = []
    for t in muster.finditer(quelle):
        d = t.groupdict()
        # Werte, die im Seed als Platzhalter stehen (Buchpreise kommen aus
        # `services/buch_preise.py`), werden **nicht geraten**.
        zahl = lambda w: None if w.startswith("{") else float(w)  # noqa: E731
        heraus.append({
            "slug": d["slug"], "name": d["name"], "kurz": d["kurz"],
            "brutto": zahl(d["brutto"]), "netto": zahl(d["netto"]),
            "tage": int(d["tage"]), "art": d["art"], "status": d["status"],
            "einheit": "Werktage",
        })

    # ── Die Pflege-Abos: nicht in `products`, sondern im Abrechnungsdienst ──
    abo = (WURZEL / "kompagnon" / "backend" / "services" / "abo_stunden.py").read_text(encoding="utf-8")
    def abo_wert(name):
        t = re.search(rf"^{name} = (\d+)", abo, re.M)
        return int(t.group(1)) / 100 if t else None
    satz = re.search(r"^STEUERSATZ_ABO = ([\d.]+)", abo, re.M)
    steuer = float(satz.group(1)) if satz else 19.0
    for slug, name, konstante, kurz in (
        ("abo_bas", "Pflege Basic", "PREIS_ABO_BAS_NETTO_CENT",
         "Sieben Positionen: Hosting, Aktualisierungen, Sicherung, 30 Min. Änderungen, Re-Audit jährlich"),
        ("abo_pro", "Pflege Pro", "PREIS_ABO_PRO_NETTO_CENT",
         "Neun Positionen: zusätzlich 90 Min. Änderungen, Monatsbericht, Re-Audit quartalsweise, 4-Stunden-Reaktion"),
    ):
        netto = abo_wert(konstante)
        heraus.append({
            "slug": slug, "name": name, "kurz": kurz,
            "netto": netto,
            "brutto": round(netto * (1 + steuer / 100), 2) if netto else None,
            "tage": 0, "art": "monatlich", "status": "live", "einheit": "",
        })

    # ── Das GEO-Add-on: im Buchungskatalog ──
    dz = (WURZEL / "kompagnon" / "backend" / "services" / "dazubuchen.py").read_text(encoding="utf-8")
    g = re.search(r"^GEO_NETTO_CENT = (\d+)", dz, re.M)
    if g:
        netto = int(g.group(1)) / 100
        heraus.append({
            "slug": "geo_01", "name": "GEO/GAIO Add-on",
            "kurz": "llms.txt, schema.org, Ground Page, Nachschau nach der Veröffentlichung",
            "netto": netto, "brutto": round(netto * (1 + steuer / 100), 2),
            "tage": 10, "art": "once", "status": "live", "einheit": "Werktage",
        })
    return heraus


def _status(text: str, aufwand: str) -> str:
    """offen · teilweise · geschlossen — aus Durchstreichung und Aufwand.

    Ein durchgestrichener Titel heißt erledigt; steht daneben trotzdem ein
    Aufwand, ist ein Rest offen geblieben.
    """
    durchgestrichen = text.lstrip().startswith("~~")
    hat_aufwand = aufwand not in ("—", "-", "")
    if durchgestrichen and hat_aufwand:
        return "teilweise"
    if durchgestrichen or not hat_aufwand:
        return "geschlossen"
    return "offen"


def _herkunft(id_: str, text: str, beleg: str) -> str:
    """Woher der Befund stammt — die Frage, die David gestellt hat."""
    zusammen = (text + " " + beleg).lower()
    if "hubspot" in zusammen:
        return "HubSpot-Audit 19.08.2026"
    if "memberspot" in zusammen:
        return "Memberspot-Audit 19.08.2026"
    if "herstellerdoku" in beleg.lower():
        return "Herstellerdoku"
    if "stand-" in beleg:
        return "Tagesbericht " + beleg.replace("`", "")
    if "entscheidung" in beleg.lower():
        return "Entscheidung David"
    if "wc -l" in beleg:
        return "Zählung im Repo"
    if any(w in beleg.lower() for w in ("test", ".py", ".js", ".yml")):
        return "Am Code gemessen"
    return "Soll-Ist-Analyse"


def _titel(text: str) -> str:
    ohne = re.sub(r"~~", "", text)
    fett = re.match(r"\s*\*\*(.+?)\*\*", ohne)
    roh = fett.group(1) if fett else ohne
    roh = re.sub(r"[`*]", "", roh).strip()
    return (roh[:110] + "…") if len(roh) > 110 else roh


def _fliesstext(text: str, grenze: int = 460) -> str:
    s = re.sub(r"<br>", " ", text)
    s = re.sub(r"~~", "", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"`(.+?)`", r"\1", s)
    s = re.sub(r"\s+", " ", s).strip()
    return (s[:grenze].rsplit(" ", 1)[0] + " …") if len(s) > grenze else s


def _spalten(zeile: str) -> list:
    """Eine Markdown-Tabellenzeile in ihre Spalten zerlegen.

    Zerlegt an `|`, aber **nicht** an `\\|` — ein maskiertes Pipe gehoert zum
    Zelleninhalt (etwa in `` `ls -1 \\| wc -l` ``). Daran scheiterte der
    fruehere Ausdruck, und der Eintrag fiel stumm aus dem Lagebild.
    """
    roh = re.split(r"(?<!\\)\|", zeile.strip())
    # Vor dem ersten und nach dem letzten `|` steht nichts.
    return [feld.strip() for feld in roh[1:-1]]


def luecken_lesen() -> list:
    """Abschnitt 3 der Soll-Ist-Analyse als Liste von Einträgen."""
    text = QUELLE.read_text(encoding="utf-8")
    prio, heraus, fehlerhaft, uebersprungen = None, [], [], []

    for zeile in text.splitlines():
        kopf = re.match(r"^### (P[0-3]) — (.+)$", zeile)
        if kopf:
            prio = (kopf.group(1), kopf.group(2))
            continue

        # **Maskierte Pipes.** Ein Beleg wie `` `ls -1 \| wc -l` `` traegt ein
        # `\|` mitten in der Zeile. Der fruehere Ausdruck verlangte fuer die
        # letzten beiden Spalten `[^|]*` und passte darauf nicht — L-80 fiel
        # dadurch **stillschweigend aus dem Lagebild**, von Anfang an. Ein
        # Werkzeug, das Eintraege verschluckt statt sich zu beschweren, ist
        # schlimmer als eines, das gar nicht laeuft: Die Zahl sieht richtig aus.
        # Deshalb wird jetzt an unmaskierten Pipes zerlegt.
        # **Zwei Schreibweisen fuer dieselbe Sache.** 84 Eintraege beginnen
        # mit `| L-NN |`, achtzehn mit `| ~~L-NN~~ |` — dort ist die Kennung
        # selbst durchgestrichen, nicht nur der Titel. Bis zum 24.08.2026
        # fragte diese Stelle nur nach `| L-`, und die achtzehn fielen
        # **stillschweigend** heraus: Das Lagebild zeigte 84 Luecken, es sind
        # 102. Achtzehn abgeschlossene Arbeiten waren damit unsichtbar,
        # darunter L-36 mit acht Commits.
        #
        # Dasselbe Muster wie bei L-80 (siehe oben) und L-84: nicht die Daten
        # waren falsch, sondern die Form, in der das Werkzeug sie erwartete.
        # **Ein Leser, der Zeilen ueberspringt, die er nicht erkennt, muss das
        # sagen** — deshalb zaehlt `uebersprungen` unten mit und meldet sich.
        if not prio:
            continue
        if not (zeile.startswith("| L-") or zeile.startswith("| ~~L-")):
            if zeile.startswith("|") and "L-" in zeile[:14]:
                uebersprungen.append(zeile[:44])
            continue
        felder = _spalten(zeile)
        if len(felder) != 4:
            fehlerhaft.append(zeile[:40])
            continue
        reihe = felder

        id_, inhalt, aufwand, beleg = reihe
        aufwand, beleg = aufwand.strip(), beleg.strip()

        # `~~L-36~~` und `L-36` sind dieselbe Luecke. Die Kennung wird auf die
        # nackte Form gebracht, damit Verweise, Plandaten und Meilensteine sie
        # wiederfinden — die Durchstreichung ist eine Aussage ueber den
        # Zustand, kein Teil des Namens.
        id_ = id_.strip("~").strip()

        # Bei einigen Einträgen steht der Beleg in der Aufwandsspalte
        # („34 Tests"). Das sind erledigte; die Spalten wurden dort anders
        # befüllt, und ohne diese Korrektur zählt das Skript sie als offen.
        if re.match(r"^\d+ Tests$", aufwand):
            beleg, aufwand = aufwand, "—"

        heraus.append({
            "id": id_,
            "prio": prio[0],
            "bereich": prio[1],
            "aufwand": aufwand if aufwand not in ("—", "-", "") else "",
            "beleg": re.sub(r"`", "", beleg),
            "status": HANDGESETZT.get(id_, _status(inhalt, aufwand)),
            # Wer sie schliessen kann (07.09.2026) — siehe `ZUSTAENDIGKEIT`.
            "zustaendig": ZUSTAENDIGKEIT.get(id_, ("system", ""))[0],
            "zustaendig_grund": ZUSTAENDIGKEIT.get(id_, ("system", ""))[1],
            "titel": _titel(inhalt),
            "text": _fliesstext(inhalt),
            # Der **ungekuerzte** Zelleninhalt, nur zum Pruefen. Siehe die
            # Widerspruchsmeldung unten: `text` ist auf 460 Zeichen gekuerzt,
            # und genau dahinter stand die Schliessmeldung von L-85.
            "_roh": inhalt,
            "herkunft": _herkunft(id_, inhalt, beleg),
            "datum": next(iter(re.findall(r"20\d\d-\d\d-\d\d", inhalt)), ""),
        })

    if uebersprungen:
        print(f"  ⚠ {len(uebersprungen)} Zeilen sehen nach einer Luecke aus, "
              f"passen aber in keine bekannte Form: {uebersprungen[:3]}",
              file=sys.stderr)

    # **Widerspruch zwischen Text und Zaehlung melden.** L-84 war am 22.08.
    # vollstaendig geschlossen, trug die Schliessmeldung im Text — und stand
    # trotzdem als „offen" im Lagebild, weil beim Fortschreiben die
    # Durchstreichung fehlte und die Aufwandsspalte stehenblieb. Solche
    # Eintraege verfaelschen jede Zahl, die jemand aus dem Lagebild abliest.
    #
    # „teilweise" ist hier kein Widerspruch: Ein Eintrag darf sagen, dass ein
    # Teil geschlossen ist. Gemeldet wird nur „offen" trotz Schliessmeldung.
    #
    # **Am ungekuerzten Inhalt pruefen, nicht am Anzeigetext.** Der erste
    # Anlauf las `e["text"]` — und der ist auf 460 Zeichen gekuerzt. Bei L-85
    # stand die Schliessmeldung an Zeichen 1.100: Der Waechter sah sie nie und
    # meldete nichts, waehrend der Eintrag als „offen" mitzaehlte. Derselbe
    # Fehler wie der, den er verhindern soll — das Werkzeug mass enger als der
    # Befund reicht.
    widersprueche = [
        e["id"] for e in heraus
        if e["status"] == "offen"
        and re.search(r"Geschlossen(\s+am)?\s+2\d{3}", e["_roh"], re.I)
    ]
    if widersprueche:
        print("  Hinweis: Diese Eintraege nennen ein Schliessdatum, zaehlen aber "
              "als offen — fehlt die Durchstreichung oder steht noch ein "
              f"Aufwand darin? {', '.join(widersprueche)}")

    if fehlerhaft:
        # **Nicht still weitermachen.** Genau das war der Fehler: Ein
        # verschluckter Eintrag faellt niemandem auf, weil die Gesamtzahl
        # weiter plausibel aussieht.
        raise SystemExit(
            "Diese Zeilen der Lueckenliste lassen sich nicht lesen — "
            "sie fehlten sonst im Lagebild:\n  " + "\n  ".join(fehlerhaft))

    heraus.sort(key=lambda e: (e["prio"], e["id"]))
    return heraus


def module_gruen() -> int:
    """Wie viele Modulkarten in der Vorlage grün stehen — gezählt, nicht geglaubt."""
    return VORLAGE.read_text(encoding="utf-8").count('ampel:"a-gruen"')


def pakete_live() -> int:
    """Wie viele Produkte auf einer frischen Datenbank verkaeuflich waeren.

    Hier stand bis zum 24.08.2026 eine feste **3** — richtig, solange der
    Katalog Starter, KOMPAGNON und Premium fuehrte und alle drei live waren.
    Mit dem Websprint-Wechsel (L-97) wurden es zwei, und die Zahl im Lagebild
    blieb stehen. Genau der Fall, vor dem [[feedback_lagebild_nachfuehren]]
    warnt: eine Zahl von Hand, die niemand nachfuehrt, weil niemand merkt,
    dass sie veraltet ist.

    Gezaehlt wird an der Vorlage in `main.py` — der versionierten Quelle fuer
    eine frische Datenbank. **Das ist ausdruecklich nicht der Live-Zustand:**
    Im Produkteditor laesst sich ein Paket jederzeit umschalten, ohne dass
    diese Datei sich aendert. Was hier steht, ist der Auslieferungsstand.
    """
    quelle = (WURZEL / "kompagnon" / "backend" / "main.py").read_text(encoding="utf-8")
    baum = ast.parse(quelle)
    for knoten in ast.walk(baum):
        if (isinstance(knoten, ast.Assign)
                and any(getattr(z, "id", "") == "SEED" for z in knoten.targets)):
            return sum(1 for e in ast.literal_eval(knoten.value)
                       if e.get("status") == "live")
    return 0


def zahlen_block(luecken: list) -> str:
    z = collections.Counter(e["status"] for e in luecken)
    p0 = sum(1 for e in luecken if e["prio"] == "P0" and e["status"] != "geschlossen")
    gruen = module_gruen()

    felder = [
        (p0, "P0 · sofort", True),
        (z["offen"], "offen", False),
        (z["terminiert"], "terminiert", False),
        (z["teilweise"], "teilweise", False),
        (z["geschlossen"], "geschlossen", False),
        (f'{gruen}<span style="font-size:19px">/11</span>', "Module grün", False),
        (pakete_live(), "Pakete live", False),
    ]
    zeilen = "\n".join(
        f'      <div class="zahl{" dringend" if warn else ""}">'
        f'<div class="n">{wert}</div><div class="b">{name}</div></div>'
        for wert, name, warn in felder
    )
    return f'<div class="zahlen">\n{zeilen}\n    </div>'


def meilensteine_bewerten(plan: dict, luecken: list) -> dict:
    """Je Meilenstein: welche Luecke haelt ihn noch auf.

    **Warum das Lagebild Termine ueberhaupt kennen sollte (24.08.2026).** Es
    beantwortete bisher „was ist offen", nicht „was verschiebt sich dadurch".
    Davids Projektplan KW35–52 nennt sieben Meilensteine mit Datum; die
    Verbindung zwischen ihnen und der Lueckenliste stand nirgends.

    **Die Bewertung ist bewusst zweigeteilt.** Was an einer Luecke haengt,
    kann das Lagebild messen — es kennt ihren Status. Was an Anwalt,
    Steuerberater oder einer Referenzmessung haengt, kann es **nicht** messen
    und behauptet es auch nicht: Diese Punkte stehen als `extern` daneben und
    bleiben stehen, bis jemand sie von Hand streicht. Ein Meilenstein ohne
    offene Luecke ist deshalb „technisch frei", nicht „erreicht".
    """
    status = {e["id"]: e["status"] for e in luecken}
    for m in plan.get("meilensteine", []):
        offen = [i for i in m.get("luecken", [])
                 if status.get(i) != "geschlossen"]
        m["offen"] = offen
        m["frei"] = not offen
    return plan


def plan_bereinigen(plan: dict, luecken: list) -> dict:
    """Erledigtes aus dem Arbeitsplan nehmen — beim Bauen, nicht von Hand.

    **Der Befund vom 24.08.2026.** `plan.json` stammt vom 22.08. und wurde
    seither nicht nachgefuehrt: **18 von 40 Eintraegen** waren geschlossen und
    standen trotzdem als offene Arbeit im Lagebild — darunter L-34 (der
    Umzug nach Frankfurt) unter „blockiert", obwohl er einen Tag zuvor
    vollzogen wurde. Ein Plan, der Erledigtes als Vorhaben zeigt, ist
    schlimmer als keiner: Er sieht aus wie eine Arbeitsliste.

    Statt die Datei jedes Mal von Hand zu putzen, faellt Geschlossenes hier
    beim Bauen heraus. Damit kann sie nicht mehr veralten — sie darf
    Eintraege enthalten, die laengst zu sind, sie erscheinen nur nicht mehr.

    Unbekannte Kennungen (etwa `L-25a` als Teilschritt einer Luecke) bleiben
    stehen: Sie haben keinen Status, ueber den sich entscheiden liesse, und
    stillschweigend zu verschwinden waere die schlechtere Annahme.
    """
    status = {e["id"]: e["status"] for e in luecken}
    entfernt = []
    bereinigt = {}
    for bereich, eintraege in plan.items():
        if not isinstance(eintraege, list):
            bereinigt[bereich] = eintraege
            continue
        behalten = []
        for e in eintraege:
            if bereich == "meilensteine":
                behalten.append(e)
            elif status.get(e.get("id")) == "geschlossen":
                entfernt.append(e["id"])
            else:
                behalten.append(e)
        bereinigt[bereich] = behalten
    if entfernt:
        print(f"  Plan: {len(entfernt)} geschlossene Eintraege ausgeblendet "
              f"({', '.join(entfernt[:6])}{' …' if len(entfernt) > 6 else ''})")
    return bereinigt


def stand() -> str:
    kurz = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                          cwd=WURZEL, capture_output=True, text=True).stdout.strip()
    datum = subprocess.run(["git", "log", "-1", "--format=%cd", "--date=format:%d.%m.%Y"],
                           cwd=WURZEL, capture_output=True, text=True).stdout.strip()
    return f"STAND {datum} · staging @ {kurz or 'unbekannt'}"


def main() -> int:
    if not QUELLE.exists() or not VORLAGE.exists():
        print(f"Fehlt: {QUELLE if not QUELLE.exists() else VORLAGE}", file=sys.stderr)
        return 2

    luecken = luecken_lesen()
    if not luecken:
        print("Keine Lücken gelesen — hat sich die Tabellenform geändert?", file=sys.stderr)
        return 2

    seite = VORLAGE.read_text(encoding="utf-8")
    plan = json.loads(PLANDATEN.read_text(encoding="utf-8")) if PLANDATEN.exists() else {
        "phasen": [], "blockiert": [], "spaeter": []}
    plan = plan_bereinigen(plan, luecken)
    plan = meilensteine_bewerten(plan, luecken)

    ersetzungen = {
        "/*__LUECKEN__*/[]": json.dumps(luecken, ensure_ascii=False),
        "/*__PLAN__*/{}": json.dumps(plan, ensure_ascii=False),
        "/*__PRODUKTE__*/[]": json.dumps(produkte_lesen(), ensure_ascii=False),
        "<!--__ZAHLEN__-->": zahlen_block(luecken),
        "<!--__STAND__-->": stand(),
    }
    for platzhalter, wert in ersetzungen.items():
        if platzhalter not in seite:
            print(f"Platzhalter fehlt in der Vorlage: {platzhalter}", file=sys.stderr)
            return 2
        seite = seite.replace(platzhalter, wert, 1)

    ZIEL.write_text(seite, encoding="utf-8")

    z = collections.Counter(e["status"] for e in luecken)
    p0 = sum(1 for e in luecken if e["prio"] == "P0" and e["status"] != "geschlossen")
    print(f"{ZIEL.relative_to(WURZEL)} — {len(luecken)} Lücken: "
          f"{z['offen']} offen, {z['teilweise']} teilweise, "
          f"{z['terminiert']} terminiert, {z['geschlossen']} geschlossen "
          f"· P0 offen: {p0} · Module grün: {module_gruen()}/11")
    print("Jetzt als Artifact veröffentlichen (derselbe Pfad hält dieselbe URL).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
