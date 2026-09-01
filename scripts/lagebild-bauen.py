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

#: Lücken, deren Zustand sich nicht aus der Tabellenform ablesen lässt.
#: Jede braucht einen Grund — sonst wird die Liste zum Ablagefach.
HANDGESETZT = {
    # (b) ist gebaut, aber nie gegen einen echten Dienst gelaufen. Weder
    # „offen" noch „geschlossen" trifft das.
    "L-58": "teilweise",

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
                             # scheitert ab dem Stichtag mit der
                             # Arbeitsanweisung im Text.
}


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
