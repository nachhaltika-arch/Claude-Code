"""Ein Feld, das zwei Fragen beantwortet, beantwortet keine richtig.

Aus dem HubSpot-Vergleich vom 19.08.2026. `Lead.status` sagte gleichzeitig,
**wo** ein Betrieb im Trichter steht und **wie weit** die Bearbeitung ist.
Diese Datei hält die Trennung fest — und vor allem: dass niemand dabei etwas
verliert.

Der Anlass ist keine Geschmacksfrage. Zwei Stellen beantworteten „ist das ein
Kunde?" durch Aufzählung und übersahen dabei `customer`:

    automations.py:104   leads_won = ... filter(Lead.status == "won").count()
    projects.py:364      filter(Lead.status == "won", ~Lead.projects.any())

`customer` bietet der Bildschirm an (`utils/leadStatus.js`), und
`PATCH /api/leads/{id}` schreibt ihn per `setattr` klaglos. Ein Betrieb, den
jemand von Hand auf „Kunde" gesetzt hat, zählte in keiner Kennzahl mit.
"""
import pytest

from services.lebenszyklus import (
    AUSGESCHIEDEN, IM_GESPRAECH, INTERESSENT, KUNDE, PHASEN, PHASEN_LABEL,
    ist_kunde, phase_zu,
)


# ── Die Zuordnung ─────────────────────────────────────────────────────

@pytest.mark.parametrize("status,phase", [
    ("new", INTERESSENT),
    ("opt_in", INTERESSENT),
    ("contacted", IM_GESPRAECH),
    ("qualified", IM_GESPRAECH),
    ("proposal_sent", IM_GESPRAECH),
    ("won", KUNDE),
    ("customer", KUNDE),
    ("lost", AUSGESCHIEDEN),
])
def test_jeder_bekannte_status_findet_seine_phase(status, phase):
    assert phase_zu(status) == phase


def test_ohne_status_ist_es_ein_interessent(_=None):
    """Die Spaltenvorgabe ist `new` — ein Betrieb ohne Status ist ein neuer."""
    assert phase_zu(None) == INTERESSENT
    assert phase_zu("") == INTERESSENT


@pytest.mark.parametrize("status", ["WON", " won ", "Customer"])
def test_schreibweise_und_leerzeichen_stoeren_nicht(status):
    """`PATCH` schreibt per `setattr`, was hereinkommt."""
    assert phase_zu(status) == KUNDE


# ── Der wichtigste Test hier ──────────────────────────────────────────

def test_ein_unbekannter_status_bekommt_keine_phase():
    """Er soll auffallen, nicht verschwinden.

    Ihn still nach „Interessent" zu schieben wäre die Tarnung, die die
    UX-Methode verbietet — auf Staging stand ein Betrieb mit `opt_in`, der in
    keiner Kachel auftauchte, und der dreißigste war weder zu sehen noch zu
    finden.
    """
    assert phase_zu("voellig_neuer_wert") is None
    assert phase_zu("tippfehlre") is None


# ── Die eine Frage, die vorher eine Aufzählung war ────────────────────

@pytest.mark.parametrize("status", ["won", "customer"])
def test_beide_kundenzustaende_zaehlen_als_kunde(status):
    """Genau hier lag der Fehler in den zwei Kennzahlen."""
    assert ist_kunde(status) is True


@pytest.mark.parametrize("status", ["new", "opt_in", "contacted", "qualified",
                                    "proposal_sent", "lost", "unbekannt"])
def test_alles_andere_ist_kein_kunde(status):
    assert ist_kunde(status) is False


# ── Zusammenhalt ──────────────────────────────────────────────────────

def test_jede_phase_hat_eine_beschriftung():
    """Sonst zeigt die Oberfläche einen Schlüssel statt eines Wortes."""
    assert set(PHASEN_LABEL) == set(PHASEN)


def test_jede_zugeordnete_phase_gibt_es_auch():
    """Ein Tippfehler in der Zuordnung ergäbe eine Phase, die niemand kennt."""
    from services.lebenszyklus import PHASE_ZU_STATUS

    assert set(PHASE_ZU_STATUS.values()) <= set(PHASEN)


def test_der_bildschirm_und_die_zuordnung_kennen_dieselben_status():
    """Die Zuordnung darf nicht hinter dem Bildschirm zurückbleiben.

    `utils/leadStatus.js` ist die Liste, aus der die Oberfläche ihre
    Beschriftungen nimmt. Wer dort einen Status ergänzt und ihn hier vergisst,
    baut genau den unbekannten Wert, den der Test darüber beschreibt.
    """
    import re
    from pathlib import Path

    from services.lebenszyklus import PHASE_ZU_STATUS

    quelle = (Path(__file__).resolve().parents[2]
              / "frontend" / "src" / "utils" / "leadStatus.js").read_text(encoding="utf-8")
    block = re.search(r"LEAD_STATUS = \{(.*?)\n\};", quelle, re.S)
    assert block, "LEAD_STATUS nicht gefunden — hat die Datei sich bewegt?"

    im_bildschirm = set(re.findall(r"^\s*([a-z_]+):\s*\{", block.group(1), re.M))
    fehlend = im_bildschirm - set(PHASE_ZU_STATUS)

    assert not fehlend, (
        f"Der Bildschirm kennt Status, die keiner Phase zugeordnet sind: {fehlend}"
    )


def test_der_bildschirm_kennt_dieselben_phasen():
    """Beide Seiten müssen dieselben Phasen führen.

    Laufen sie auseinander, bekommt ein Betrieb eine Phase, für die die
    Oberfläche keinen Namen hat — und zeigt einen Schlüssel statt eines
    Wortes. Der Test schaut in die JS-Datei, weil es keine gemeinsame Quelle
    gibt; eine zu bauen wäre mehr Apparat als der Nutzen.
    """
    import re
    from pathlib import Path

    quelle = (Path(__file__).resolve().parents[2]
              / "frontend" / "src" / "utils" / "leadStatus.js").read_text(encoding="utf-8")
    block = re.search(r"LEAD_PHASE = \{(.*?)\n\};", quelle, re.S)
    assert block, "LEAD_PHASE nicht gefunden — hat die Datei sich bewegt?"

    im_bildschirm = set(re.findall(r"^\s*([a-z_]+):\s*\{", block.group(1), re.M))

    assert im_bildschirm == set(PHASEN), (
        f"Backend {set(PHASEN)} gegen Bildschirm {im_bildschirm}"
    )
