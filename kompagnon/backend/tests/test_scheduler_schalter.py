"""Zwei Dienste, eine Jobtabelle — und ein Job, den niemand mehr anlegt.

**Gefunden am 2026-08-23 beim Umzug nach Frankfurt (L-34).** Seit dem 19.08.
laufen zwei Produktiv-Dienste gegen **dieselbe** Datenbank: Oregon trägt den
Verkehr, Frankfurt steht als Ersatz daneben. Beide starten beim Hochfahren
einen `BackgroundScheduler`, und beide hängen ihn an denselben
`SQLAlchemyJobStore` (`apscheduler_jobs`, 14 Zeilen).

APScheduler kennt keine Sperre über Prozessgrenzen. Zwei Scheduler auf einem
Jobstore heißt: Ein fälliger Job kann **zweimal** laufen. Unter den vierzehn
ist `email_sequence_runner`.

Schaden ist keiner entstanden — produktiv ging seit dem 19.08. keine einzige
Mail hinaus, weil keine Strecke fällig war. Das ist Glück, keine Absicherung.

**Zwei Dinge fehlten:**

1. **Kein Schalter.** `start_scheduler()` startete bedingungslos. Ein Dienst
   ohne Verkehr konnte seinen Scheduler nicht abstellen, ohne den ganzen
   Dienst abzustellen.
2. **Kein Abgleich mit dem Code.** Der Jobstore ist dauerhaft, die
   Registrierung nicht: `netlify_dns_check_every_10min` stand in der Tabelle
   und lief alle zehn Minuten, obwohl der heutige Code **nur**
   `netlify_dns_check_every_15min` anlegt. Ein umbenannter Job hinterlässt
   seinen Vorgänger, und niemand sieht es.

**Die Falle beim Aufräumen** — deshalb der letzte Test hier: Es gibt auch
Jobs, die **zur Laufzeit** entstehen (`golive_day30_upsell_{project_id}`, ein
Termin je Projekt). Wer pauschal alles entfernt, was nicht in der Tagesliste
steht, löscht Kundentermine. Aufgeräumt wird deshalb nur, was weder registriert
wurde noch einem bekannten Laufzeit-Präfix folgt.
"""
import pytest

from automations.scheduler import (
    scheduler_ist_eingeschaltet,
    verwaiste_jobs,
    LAUFZEIT_PRAEFIXE,
)


# ── Der Schalter ─────────────────────────────────────────────────────────

def test_ohne_variable_laeuft_der_scheduler(monkeypatch):
    """Die Vorgabe muss `an` sein — sonst stellt ein Umzug produktiv alles ab."""
    # Arrange
    monkeypatch.delenv("SCHEDULER_ENABLED", raising=False)

    # Act / Assert
    assert scheduler_ist_eingeschaltet() is True


@pytest.mark.parametrize("wert", ["false", "False", "FALSE", "0", "no", "nein"])
def test_der_schalter_haelt_den_scheduler_an(monkeypatch, wert):
    # Arrange
    monkeypatch.setenv("SCHEDULER_ENABLED", wert)

    # Act / Assert
    assert scheduler_ist_eingeschaltet() is False


@pytest.mark.parametrize("wert", ["true", "True", "1", "yes", "ja"])
def test_ausdrueckliches_an_laeuft_auch(monkeypatch, wert):
    # Arrange
    monkeypatch.setenv("SCHEDULER_ENABLED", wert)

    # Act / Assert
    assert scheduler_ist_eingeschaltet() is True


def test_ein_unverstaendlicher_wert_laesst_laufen(monkeypatch):
    """Im Zweifel läuft er. Ein Tippfehler darf die Automatik nicht abstellen."""
    # Arrange
    monkeypatch.setenv("SCHEDULER_ENABLED", "vielleicht")

    # Act / Assert
    assert scheduler_ist_eingeschaltet() is True


# ── Der Abgleich mit dem Code ────────────────────────────────────────────

def test_ein_job_den_niemand_mehr_anlegt_gilt_als_verwaist():
    """Der produktive Fall: der 10-Minuten-Job neben dem 15-Minuten-Job."""
    # Arrange
    vorhanden = ["netlify_dns_check_every_10min", "netlify_dns_check_every_15min"]
    registriert = {"netlify_dns_check_every_15min"}

    # Act
    uebrig = verwaiste_jobs(vorhanden, registriert)

    # Assert
    assert uebrig == ["netlify_dns_check_every_10min"]


def test_ein_laufzeit_job_wird_nicht_angetastet():
    """Die Falle: `golive_day30_upsell_7` gehört einem Projekt, nicht der Liste."""
    # Arrange
    vorhanden = ["daily_update_margins", "golive_day30_upsell_7"]
    registriert = {"daily_update_margins"}

    # Act
    uebrig = verwaiste_jobs(vorhanden, registriert)

    # Assert
    assert uebrig == []


def test_jedes_bekannte_laufzeit_praefix_ist_geschuetzt():
    # Arrange
    vorhanden = [p + "42" for p in LAUFZEIT_PRAEFIXE]

    # Act
    uebrig = verwaiste_jobs(vorhanden, set())

    # Assert
    assert uebrig == []


def test_was_registriert_wurde_bleibt():
    # Arrange
    vorhanden = ["daily_update_margins", "email_sequence_runner"]

    # Act
    uebrig = verwaiste_jobs(vorhanden, set(vorhanden))

    # Assert
    assert uebrig == []


# ── Der Abgleich am laufenden Scheduler ──────────────────────────────────
#
# Die Prüfungen oben halten die *Regel* fest. Diese hier hält fest, dass sie
# beim Start auch **angewendet** wird — der Unterschied, an dem L-79 hing:
# Die Funktion war da, nur rief sie niemand auf.

def test_der_start_raeumt_einen_verwaisten_job_weg(monkeypatch):
    # Arrange — Scheduler im Speicher, damit kein Jobstore angefasst wird
    monkeypatch.setenv("SCHEDULER_JOBSTORE", "memory")
    from automations.scheduler import CompagnonScheduler

    s = CompagnonScheduler()
    s.scheduler.add_job(lambda: None, "interval", hours=99,
                        id="netlify_dns_check_every_10min")

    # Act
    s.start()
    try:
        kennungen = {j.id for j in s.scheduler.get_jobs()}

        # Assert
        assert "netlify_dns_check_every_10min" not in kennungen
        assert "netlify_dns_check_every_15min" in kennungen, "der echte bleibt"
    finally:
        s.stop()


def test_der_start_laesst_einen_laufzeit_job_stehen(monkeypatch):
    """Ein Projekttermin darf einen Neustart überleben."""
    # Arrange
    monkeypatch.setenv("SCHEDULER_JOBSTORE", "memory")
    from automations.scheduler import CompagnonScheduler

    s = CompagnonScheduler()
    s.scheduler.add_job(lambda: None, "interval", hours=99,
                        id="golive_day30_upsell_4711")

    # Act
    s.start()
    try:
        kennungen = {j.id for j in s.scheduler.get_jobs()}

        # Assert
        assert "golive_day30_upsell_4711" in kennungen
    finally:
        s.stop()
