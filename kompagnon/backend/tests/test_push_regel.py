"""Der Push wartet, solange ein Lauf noch läuft.

Die Regel in `.claude/settings.json` pusste bisher nach **jedem** Bash-Schritt.
Der Workflow hat `cancel-in-progress` — jeder neue Push bricht den laufenden
Lauf ab. Am 18.08.2026 endeten zwei Läufe so, einer mitten in Playwright.

Das Tückische daran: Ein abgebrochener Lauf ist nicht rot, sondern grau. Er
sagt nichts. Wer auf „nicht rot" schaut, hält den Stand für geprüft.

Geprüft wird hier gegen ein Wegwerf-Repository und ein vorgetäuschtes `gh`
— kein Netz, kein echter Push.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

SKRIPT = Path(__file__).resolve().parents[3] / "scripts" / "push-wenn-ruhig.sh"


def _repo(tmp_path: Path, zweig: str = "staging") -> Path:
    """Ein Repository mit Gegenstück, damit `@{u}` etwas findet."""
    fern = tmp_path / "fern.git"
    subprocess.run(["git", "init", "--bare", "-q", str(fern)], check=True)

    arbeit = tmp_path / "arbeit"
    subprocess.run(["git", "clone", "-q", str(fern), str(arbeit)], check=True)
    for schluessel, wert in (("user.email", "test@example.com"), ("user.name", "Test")):
        subprocess.run(["git", "-C", str(arbeit), "config", schluessel, wert], check=True)

    (arbeit / "datei.txt").write_text("eins\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(arbeit), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(arbeit), "commit", "-qm", "erster"], check=True)
    subprocess.run(["git", "-C", str(arbeit), "branch", "-M", zweig], check=True)
    subprocess.run(["git", "-C", str(arbeit), "push", "-qu", "origin", zweig], check=True)
    return arbeit


def _gh_attrappe(tmp_path: Path, zustand: str) -> dict:
    """Ein `gh`, das immer denselben Laufzustand meldet."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    (bin_dir / "gh").write_text(f'#!/bin/sh\necho "{zustand}"\n', encoding="utf-8")
    os.chmod(bin_dir / "gh", 0o755)
    return {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"}


def _lauf(arbeit: Path, umgebung: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(SKRIPT)], cwd=arbeit, env=umgebung,
        capture_output=True, text=True, timeout=30,
    )


def _unversandter_commit(arbeit: Path) -> None:
    (arbeit / "datei.txt").write_text("zwei\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(arbeit), "commit", "-qam", "zweiter"], check=True)


def _ferne_spitze(arbeit: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(arbeit), "rev-parse", "origin/staging"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


@pytest.mark.skipif(not shutil.which("git"), reason="ohne git nicht prüfbar")
def test_bei_laufendem_lauf_wird_nicht_gepusht(tmp_path):
    arbeit = _repo(tmp_path)
    vorher = _ferne_spitze(arbeit)
    _unversandter_commit(arbeit)

    ergebnis = _lauf(arbeit, _gh_attrappe(tmp_path, "in_progress"))

    assert "wartet" in ergebnis.stdout, ergebnis.stdout + ergebnis.stderr
    assert _ferne_spitze(arbeit) == vorher, "Es wurde trotzdem gepusht"


@pytest.mark.skipif(not shutil.which("git"), reason="ohne git nicht prüfbar")
def test_ist_die_bahn_frei_wird_gepusht(tmp_path):
    arbeit = _repo(tmp_path)
    vorher = _ferne_spitze(arbeit)
    _unversandter_commit(arbeit)

    _lauf(arbeit, _gh_attrappe(tmp_path, "completed"))

    assert _ferne_spitze(arbeit) != vorher, "Der Commit blieb liegen"


@pytest.mark.skipif(not shutil.which("git"), reason="ohne git nicht prüfbar")
def test_auf_einem_anderen_zweig_passiert_nichts(tmp_path):
    arbeit = _repo(tmp_path, zweig="main")

    ergebnis = _lauf(arbeit, _gh_attrappe(tmp_path, "completed"))

    assert ergebnis.stdout.strip() == "", ergebnis.stdout


@pytest.mark.skipif(not shutil.which("git"), reason="ohne git nicht prüfbar")
def test_ohne_offene_commits_passiert_nichts(tmp_path):
    arbeit = _repo(tmp_path)

    ergebnis = _lauf(arbeit, _gh_attrappe(tmp_path, "completed"))

    assert ergebnis.stdout.strip() == "", ergebnis.stdout


@pytest.mark.skipif(not shutil.which("git"), reason="ohne git nicht prüfbar")
def test_ohne_gh_wird_gepusht_statt_blockiert(tmp_path):
    """Ein liegengebliebener Commit ist schlimmer als ein abgebrochener Lauf."""
    arbeit = _repo(tmp_path)
    vorher = _ferne_spitze(arbeit)
    _unversandter_commit(arbeit)

    ohne_gh = {**os.environ, "PATH": "/usr/bin:/bin"}
    _lauf(arbeit, ohne_gh)

    assert _ferne_spitze(arbeit) != vorher
