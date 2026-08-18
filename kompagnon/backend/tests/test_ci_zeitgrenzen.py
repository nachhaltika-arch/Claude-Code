"""Kein CI-Job darf ohne Zeitgrenze laufen.

Am 17.08. hing `npx playwright install --with-deps chromium` im E2E-Job.
Ohne Zeitgrenze lief der Job sechs Stunden bis in GitHubs Notbremse, der
Deploy-Job wurde nie erreicht — ein haengender Download hat also den
gesamten Weg nach Staging blockiert, ohne dass irgendetwas rot wurde.

Die Zeitgrenze je Job ist die harte Sperre (GitHub bricht ab), die Grenze
je Versuch in ci-retry.sh die weiche (ein haengender Download wird
wiederholt statt abgewartet).
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
RETRY_SCRIPT = REPO_ROOT / "scripts" / "ci-retry.sh"

# Ein Job-Kopf steht auf genau zwei Leerzeichen Einrueckung unter `jobs:`.
JOB_HEADER = re.compile(r"^  ([a-z0-9][a-z0-9_-]*):\s*$")


def _jobs_mit_zeitgrenze() -> dict[str, bool]:
    """Liest ci.yml als Text — PyYAML steht in der CI nicht zur Verfuegung."""
    zeilen = CI_WORKFLOW.read_text(encoding="utf-8").splitlines()
    in_jobs = False
    jobs: dict[str, bool] = {}
    aktueller: str | None = None

    for zeile in zeilen:
        if zeile.startswith("jobs:"):
            in_jobs = True
            continue
        if not in_jobs:
            continue
        # Alles ohne Einrueckung beendet den jobs-Block.
        if zeile.strip() and not zeile.startswith(" "):
            break

        kopf = JOB_HEADER.match(zeile)
        if kopf:
            aktueller = kopf.group(1)
            jobs[aktueller] = False
            continue
        if aktueller and zeile.strip().startswith("timeout-minutes:"):
            jobs[aktueller] = True

    return jobs


def test_ci_datei_ist_vorhanden():
    assert CI_WORKFLOW.is_file(), f"CI-Datei fehlt: {CI_WORKFLOW}"


def test_jeder_ci_job_hat_eine_zeitgrenze():
    jobs = _jobs_mit_zeitgrenze()

    assert jobs, "Im Workflow wurde kein einziger Job gefunden"

    ohne_grenze = sorted(name for name, hat_grenze in jobs.items() if not hat_grenze)
    assert not ohne_grenze, (
        "Diese CI-Jobs haben keine timeout-minutes und koennen sechs Stunden "
        f"haengen: {', '.join(ohne_grenze)}"
    )


def test_playwright_installiert_ohne_rueckfrage():
    """`--with-deps` ruft apt-get; eine Rueckfrage dort haelt den Job an."""
    inhalt = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "playwright install --with-deps" in inhalt
    assert "DEBIAN_FRONTEND: noninteractive" in inhalt
    assert "NEEDRESTART_MODE: a" in inhalt


@pytest.mark.skipif(
    shutil.which("timeout") is None and shutil.which("gtimeout") is None,
    reason="weder timeout noch gtimeout vorhanden (macOS ohne coreutils)",
)
def test_ci_retry_bricht_einen_haengenden_versuch_ab():
    # Arrange
    umgebung = {
        "CI_RETRY_ATTEMPTS": "1",
        "CI_RETRY_DELAY_SECONDS": "0",
        "CI_RETRY_TIMEOUT_SECONDS": "1",
        "PATH": "/usr/bin:/bin:/usr/local/bin",
    }

    # Act
    ergebnis = subprocess.run(
        ["bash", str(RETRY_SCRIPT), "sleep", "30"],
        env=umgebung,
        capture_output=True,
        text=True,
        timeout=20,
    )

    # Assert
    assert ergebnis.returncode != 0, "Ein haengender Versuch muss scheitern"
    assert "Zeitgrenze" in ergebnis.stderr, ergebnis.stderr


def test_ci_retry_laesst_schnelle_befehle_durch():
    ergebnis = subprocess.run(
        ["bash", str(RETRY_SCRIPT), "true"],
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert ergebnis.returncode == 0, ergebnis.stderr
