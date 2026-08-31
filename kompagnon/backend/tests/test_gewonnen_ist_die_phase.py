"""„Gewonnen" wird ueber die Phase gezaehlt, nicht ueber den Status (L-26).

**Warum es diesen Waechter gibt.** Die Umstellung ist am 19.08.2026 gemacht
worden — in `automations.py`, mit einer ausfuehrlichen Begruendung im Code:
Ein Betrieb, den jemand im Bildschirm auf „Kunde" setzt, bekommt
`lifecycle_phase = 'kunde'`, aber nicht `status = 'won'`. Wer auf den Status
zaehlt, uebersieht ihn.

**Vier Stellen sind damals stehengeblieben** — drei in `routers/campaigns.py`
und eine in der Diagnoseauskunft `routers/projects.py`;
und eine davon speist den Block „Betriebe nach Herkunft" auf dem Dashboard.
Die Gewinnquote dort war seither zu niedrig. Gefunden am 31.08.2026 — nicht
beim Lesen, sondern beim Durchgehen der Endpunkte ohne Aufrufer (L-105):
`GET /api/leads/quellen/wirkung` rechnet dieselbe Frage richtig und wird von
niemandem gerufen; der Vergleich zeigte den Rest.

**Eine Korrektur, die niemand bewacht, kommt zurueck** — diese hier ist der
Beweis dafuer, denn sie war schon einmal gemacht.

**Gezaehlt wird im Quelltext, und die Ausnahmen stehen mit Grund dabei.** Ein
Test, der die Zahl aus der Datenbank liest, braucht Daten in genau der
Konstellation; ein Test, der die Spalte im SQL sucht, findet den Fehler auch
in einer Abfrage, die heute nie ausgefuehrt wird.

**Gesucht wird das Zaehlen, nicht das Wort.** Der erste Entwurf am 31.08.2026
verbot jedes `status = 'won'` und meldete elf Stellen, von denen **keine** ein
Fehler war: Die Zuordnung von Status zu Phase muss den Status lesen, das
Setzen beim Zahlungseingang schreibt ihn, und ein Seed legt ihn an. Der Mangel
ist eng: eine **Kennzahl**, die ueber den Status summiert. Deshalb muss ein
`COUNT(` oder `SUM(` in derselben Zeile stehen.

Dieselbe Lehre wie an den Vortagen, nur andersherum: Wer zu breit sucht, misst
das Wort und nicht die Sache — und eine Liste aus elf Fehlalarmen wird
abgeschaltet, nicht gelesen.
"""
import pathlib
import re

BACKEND = pathlib.Path(__file__).resolve().parent.parent

#: Stellen, an denen `status = 'won'` richtig ist — jede nachgesehen.
AUSNAHMEN = {
    # Rueckfall auf `usercards`, wenn `leads` leer ist. Die Tabelle hat keine
    # `lifecycle_phase`; der Zweig laeuft nur in einer leeren Umgebung.
    "routers/automations.py",
}

#: Eine **Kennzahl** ueber den Status: `COUNT`/`SUM` und `status='won'`
#: in derselben Zeile. Alles andere — zuordnen, setzen, filtern, seeden —
#: darf und muss den Status nennen.
MUSTER = re.compile(r"(?:COUNT|SUM)\s*\([^\n]*status\s*=?=\s*['\"]won['\"]"
                    r"|status\s*=?=\s*['\"]won['\"][^\n]*\)\s*(?:AS|as)\s")


def _quelldateien():
    for pfad in BACKEND.rglob("*.py"):
        teile = set(pfad.parts)
        if teile & {"venv", ".venv", "__pycache__", "tests", "tools"}:
            continue
        yield pfad


def test_keine_kennzahl_zaehlt_ueber_den_status():
    fund = []
    for pfad in _quelldateien():
        rel = pfad.relative_to(BACKEND).as_posix()
        if rel in AUSNAHMEN:
            continue
        # **Zeilenweise, nicht ueber den gekuerzten Text.** Der erste Anlauf
        # schnitt die Kommentarzeilen heraus und zaehlte die Fundstelle
        # danach — die gemeldete Zeilennummer zeigte auf eine Importzeile, in
        # der das Wort gar nicht vorkommt. Eine Meldung mit falscher Adresse
        # kostet mehr Zeit als keine.
        for nr, zeile in enumerate(pfad.read_text(encoding="utf-8").splitlines(), 1):
            if zeile.lstrip().startswith("#"):
                continue      # Kommentare beschreiben genau diesen Fehler
            if MUSTER.search(zeile):
                fund.append(f"{rel}:{nr}  {zeile.strip()[:70]}")

    assert fund == [], (
        "Hier wird wieder ueber den Status gezaehlt statt ueber die Phase — "
        f"L-26 kommt zurueck: {fund}"
    )


def test_und_die_kampagnen_zaehlen_wirklich_ueber_die_phase():
    """Die positive Gegenprobe.

    Der Test oben waere auch dann gruen, wenn jemand die drei Abfragen
    ersatzlos loescht — dann gaebe es die Kennzahl gar nicht mehr.
    """
    text = (BACKEND / "routers" / "campaigns.py").read_text(encoding="utf-8")
    treffer = re.findall(r"lifecycle_phase\s*=\s*'kunde'", text)
    assert len(treffer) >= 3, (
        f"nur {len(treffer)} der drei Kampagnen-Abfragen zaehlen ueber die Phase"
    )


def test_die_ausnahmen_gelten_noch():
    """Eine Ausnahmeliste, die niemand nachrechnet, wird zum Loch.

    Steht eine Datei hier, enthaelt das Muster aber nicht mehr, gehoert sie
    gestrichen — sonst deckt sie eines Tages einen echten Fund.
    """
    veraltet = []
    for rel in AUSNAHMEN:
        pfad = BACKEND / rel
        if not pfad.exists():
            veraltet.append(f"{rel}: Datei gibt es nicht mehr")
        elif not MUSTER.search(pfad.read_text(encoding="utf-8")):
            veraltet.append(f"{rel}: zaehlt gar nicht mehr ueber den Status")
    assert veraltet == [], veraltet
