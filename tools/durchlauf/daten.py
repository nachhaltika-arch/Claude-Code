# -*- coding: utf-8 -*-
"""Stufen, die Modell, Migration und Wirklichkeit gegeneinanderhalten.

**Warum diese Ebene eine eigene Stufe braucht.** Eine Spalte im Modell ist
eine Behauptung ueber die Datenbank, keine Tatsache. Steht keine Migration
daneben, stimmt sie auf einer frisch erzeugten Datenbank (SQLAlchemy legt
alles an) und auf der gewachsenen produktiven nicht — dort fehlt die Spalte,
und der erste Zugriff endet in einem 500er, den kein Test findet, weil Tests
auf frischen Datenbanken laufen. L-86, L-93, L-106 und L-146 sind alle von
dieser Art.

    spalten_ohne_migration()      → Commit aendert das Modell, ruehrt keine Migration an
    sql_nennt_unbekannte_tabelle() → rohes SQL auf einer Tabelle, die kein Modell fuehrt
"""
from __future__ import annotations

import ast
import collections
import pathlib
import re

from .befund import Befund, WURZEL, kurz

BACKEND = WURZEL / "kompagnon" / "backend"
MIGRATIONEN = ("migrations_runtime.py", "migrations.py", "migrate.py")

_COLUMN = re.compile(r"^\s*(\w+)\s*=\s*Column\(", re.MULTILINE)
_TABELLE = re.compile(r'__tablename__\s*=\s*["\'](\w+)["\']')
_ADD_COLUMN = re.compile(
    r"ALTER\s+TABLE\s+(\w+)\s+ADD\s+COLUMN\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)", re.I)
_CREATE_TABLE = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)", re.I)


def _ohne_kommentare(text: str) -> str:
    """Der Quelltext ohne Kommentare — Docstrings bleiben stehen.

    Der erste Lauf meldete `files.py`, weil dort `# Delete from disk` steht.
    Ein Kommentar ist keine Anweisung; wer ihn mitliest, misst Prosa.
    """
    import io
    import tokenize

    teile = []
    try:
        for marke in tokenize.generate_tokens(io.StringIO(text).readline):
            if marke.type == tokenize.COMMENT:
                continue
            teile.append(marke.string if marke.type != tokenize.NL else "\n")
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return text
    return " ".join(teile)


def _modelle() -> list[pathlib.Path]:
    """Alle Dateien, die Tabellen definieren.

    `database.py` gehoert dazu: Dort steht unter anderem `projects`. Der erste
    Entwurf sah nur `modelle_*.py` und meldete deshalb `projects` als Tabelle,
    die kein Modell fuehrt — ein Fehlalarm aus einer zu engen Dateiliste.
    """
    treffer = sorted(BACKEND.glob("modelle_*.py")) + sorted(BACKEND.glob("models*.py"))
    for name in ("database.py",):
        datei = BACKEND / name
        if datei.exists():
            treffer.append(datei)
    return treffer


def _migrationstext() -> str:
    text = ""
    for name in MIGRATIONEN:
        datei = BACKEND / name
        if datei.exists():
            text += datei.read_text(encoding="utf-8")
    ordner = BACKEND / "migrations"
    if ordner.is_dir():
        for datei in ordner.rglob("*.py"):
            text += datei.read_text(encoding="utf-8")
    return text


def _tabellen_je_klasse(text: str) -> dict[str, list[str]]:
    """Tabellenname → Spalten, aus einer Modelldatei gelesen."""
    ergebnis: dict[str, list[str]] = {}
    try:
        baum = ast.parse(text)
    except SyntaxError:
        return ergebnis
    for knoten in baum.body:
        if not isinstance(knoten, ast.ClassDef):
            continue
        tabelle = ""
        spalten: list[str] = []
        for satz in knoten.body:
            if isinstance(satz, ast.Assign) and satz.targets:
                ziel = satz.targets[0]
                name = getattr(ziel, "id", "")
                if name == "__tablename__" and isinstance(satz.value, ast.Constant):
                    tabelle = satz.value.value
                elif (isinstance(satz.value, ast.Call)
                      and getattr(satz.value.func, "id", "") == "Column"):
                    spalten.append(name)
        if tabelle:
            ergebnis[tabelle] = spalten
    return ergebnis


def spalten_ohne_migration(commits: int = 60) -> list[Befund]:
    """Neue Modellspalten, zu denen im selben Commit keine Migration kam.

    **Der erste Entwurf dieser Stufe war falsch, und zwar auf lehrreiche
    Weise.** Er verglich alle Modellspalten gegen alle `ADD COLUMN`-Zeilen und
    meldete 15 Tabellen mit bis zu 31 „fehlenden" Migrationen. Nachgesehen war
    keine davon ein Mangel: Neue Datenbanken entstehen ueber die Modelle
    selbst, `migrations_runtime.py` traegt nur nach, was **spaeter** dazukam.
    Eine Spalte ohne `ADD COLUMN` ist also der Normalfall — sie war von Anfang
    an da. Die Messung verglich zwei Dinge, die nie gleich sein sollten.

    Die Frage, auf die es ankommt, ist eine andere und steht in der
    Projektregel schon: **Was ein Commit am Modell aendert, gehoert in
    denselben Commit auch in die Migration.** Genau das misst diese Fassung —
    sie geht die letzten `commits` Commits durch und meldet jeden, der eine
    `Column(`-Zeile hinzufuegt, ohne eine Migrationsdatei zu beruehren.

    Das ist billig, hat keine Fehlalarme aus der Vergangenheit, und es faengt
    den Fehler dort, wo er entsteht — statt Jahre spaeter einen Zustand zu
    beklagen, den niemand mehr zuordnen kann.
    """
    import subprocess

    try:
        roh = subprocess.run(
            ["git", "log", f"-{commits}", "--format=%H\t%s", "--name-only"],
            cwd=WURZEL, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return []
    if roh.returncode != 0:
        return []

    befunde = []
    geprueft = [0]          # Commits, die ueberhaupt ein Modell anfassen
    kennung = betreff = ""
    dateien: list[str] = []

    def pruefen(kennung: str, betreff: str, dateien: list[str]) -> None:
        modelle = [d for d in dateien
                   if "/modelle_" in d or d.endswith("/models.py")]
        if not modelle:
            return
        geprueft[0] += 1
        beruehrt_migration = any(
            "migration" in d or d.endswith("migrate.py") for d in dateien)
        if beruehrt_migration:
            return
        try:
            diff = subprocess.run(
                ["git", "show", kennung, "--unified=0", "--"] + modelle,
                cwd=WURZEL, capture_output=True, text=True, timeout=60).stdout
        except (OSError, subprocess.SubprocessError):
            return
        neue = [z for z in diff.splitlines()
                if z.startswith("+") and "= Column(" in z]
        if not neue:
            return
        namen = [z.lstrip("+").split("=")[0].strip() for z in neue][:6]
        befunde.append(Befund(
            kennung=f"modell-ohne-migration/{kennung[:9]}",
            ebene="datenbank",
            titel=(f"Commit {kennung[:9]} fuegt {len(neue)} Modellspalte(n) hinzu, "
                   f"ohne eine Migration anzufassen"),
            beleg=f"git show {kennung[:9]} — {', '.join(namen)} in "
                  f"{', '.join(pathlib.Path(m).name for m in modelle)}",
            einzelheiten=(
                f"Betreff: „{betreff[:90]}\". Auf einer frisch erzeugten Datenbank "
                "entsteht die Spalte ueber das Modell; auf der gewachsenen produktiven "
                "fehlt sie, bis eine Migration sie nachtraegt. Der erste Zugriff endet "
                "dort in einem 500er, den kein Test findet — Tests laufen auf frischen "
                "Datenbanken. **Zu pruefen, ob die Spalte produktiv existiert**, und "
                "die Migration nachzutragen. Familie L-86, L-93, L-106."
            ),
            vorschlag="P1",
            gegenstand=kennung[:9],
        ))

    for zeile in roh.stdout.splitlines():
        if "\t" in zeile and len(zeile.split("\t")[0]) == 40:
            pruefen(kennung, betreff, dateien) if kennung else None
            kennung, betreff = zeile.split("\t", 1)
            dateien = []
        elif zeile.strip():
            dateien.append(zeile.strip())
    if kennung:
        pruefen(kennung, betreff, dateien)
    # **Eine Null ohne Grundgesamtheit ist keine Aussage.** „Keine Befunde"
    # kann heissen: alles in Ordnung — oder die Messung hat nichts gesehen.
    notiz = (f"{geprueft[0]} der letzten {commits} Commits haben eine Modelldatei "
             f"geaendert; {len(befunde)} davon ohne Migration im selben Commit")
    return befunde, notiz


#: Der Tabellenname steht je nach Anweisung an anderer Stelle. Der erste
#: Entwurf nahm bei `UPDATE x SET feld` das **Feld** fuer die Tabelle und
#: meldete darauf 30 „unbekannte Tabellen" — darunter `status` und
#: `archived_at`. Drei getrennte Gruppen statt einer gemeinsamen.
_SCHREIBT_SQL = re.compile(
    r"INSERT\s+INTO\s+(\w+)|UPDATE\s+(\w+)\s+SET|DELETE\s+FROM\s+(\w+)", re.I)


def sql_nennt_unbekannte_tabelle() -> list[Befund]:
    """Rohes SQL, das eine Tabelle nennt, die kein Modell fuehrt.

    **Warum nicht jedes rohe SQL.** Der erste Entwurf meldete 41 Dateien —
    Scheduler, Auswertungen, Aufraeumarbeiten. Rohes SQL ist dort der richtige
    Weg, und eine Stufe, die es pauschal beanstandet, meldet Stil statt Fehler.

    Uebrig bleibt der Fall, der wirklich einer ist: eine Tabelle, die kein
    `__tablename__` im Repo fuehrt. Entweder ist der Name falsch geschrieben —
    dann scheitert die Anweisung erst zur Laufzeit —, oder die Tabelle ist
    ausserhalb der Modelle gewachsen und niemand weiss mehr, wer sie pflegt.
    """
    bekannt = set()
    for modell in _modelle():
        bekannt |= {t.lower() for t in _TABELLE.findall(
            modell.read_text(encoding="utf-8"))}
    for name in MIGRATIONEN:
        datei = BACKEND / name
        if datei.exists():
            bekannt |= {t.lower() for t in _CREATE_TABLE.findall(
                datei.read_text(encoding="utf-8"))}
    if not bekannt:
        return []

    treffer: dict[str, set[str]] = collections.defaultdict(set)
    for datei in BACKEND.rglob("*.py"):
        if ("venv" in datei.parts or "__pycache__" in datei.parts
                or "tests" in datei.parts or "migrations" in datei.parts
                or "tools" in datei.parts or datei.name in MIGRATIONEN):
            continue
        try:
            text = _ohne_kommentare(datei.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            continue
        for gruppen in _SCHREIBT_SQL.findall(text):
            tabelle = next((g for g in gruppen if g), "")
            if tabelle and tabelle.lower() not in bekannt:
                treffer[kurz(datei)].add(tabelle)

    befunde = []
    for datei, tabellen in sorted(treffer.items()):
        befunde.append(Befund(
            kennung=f"sql-unbekannte-tabelle/{datei}",
            ebene="datenbank",
            titel=f"{datei} schreibt auf {', '.join(sorted(tabellen))} — kein Modell fuehrt diese Tabelle",
            beleg=f"{datei} — INSERT/UPDATE/DELETE auf {', '.join(sorted(tabellen))}",
            einzelheiten=(
                "Entweder ist der Tabellenname falsch geschrieben — dann scheitert die "
                "Anweisung erst zur Laufzeit, an einer Stelle, die selten laeuft —, "
                "oder die Tabelle ist ausserhalb der Modelle entstanden und wird von "
                "keinem Werkzeug mitgefuehrt."
            ),
            vorschlag="P2",
            gegenstand=datei,
        ))
    return befunde
