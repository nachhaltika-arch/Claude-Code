"""Jede Deckelregel wird entweder erhoben — oder steht als nicht erhoben da.

**Der Befund (S6.1, K06-2).** Die K.-o.-Tabelle nennt zwei Regeln, die auf
Bronze deckeln: Tracking ohne Einwilligung **und** Cookies vor der
Einwilligung. `detect_blockers` erzeugt nur die erste. Die zweite kann kein
Audit ausloesen — sie steht im Katalog, im Bericht taucht sie nie auf.

Der Grund ist keine Nachlaessigkeit, sondern die Erhebungsart: Der
Cookie-Vergleich vor/nach braucht einen echten Browserlauf, und die
Einwilligungspruefung liest HTML.

**Was dieser Test verhindert.** Dass eine weitere Regel unbemerkt in dieselbe
Lage geraet. Wer eine Deckelregel ergaenzt, ohne sie zu erheben, muss sie hier
eintragen — und traegt sie damit auch in den Katalogkommentar ein, wo der
naechste Leser sie findet.
"""
import re
from pathlib import Path

from services.audit_criteria import (BLOCKING_CRITICAL, BLOCKING_MAJOR,
                                     NICHT_ERHOBENE_BLOCKER)

QUELLE = Path(__file__).resolve().parents[1] / "services" / "audit_scoring.py"


def _erzeugte_blocker() -> set:
    """Was `detect_blockers` tatsaechlich anhaengt — am Quelltext abgelesen.

    Ein Aufruf mit erfundenen Fakten wuerde nur den Zweig treffen, den die
    Fakten hergeben. Gefragt ist aber, was die Funktion ueberhaupt erzeugen
    **kann**.
    """
    text = QUELLE.read_text(encoding="utf-8")
    block = re.search(r"def detect_blockers\(.*?\n(?=\n\n# ═)", text, re.S)
    assert block, "detect_blockers nicht gefunden"
    return set(re.findall(r'blockers\.append\("(\w+)"\)', block.group(0)))


def test_jede_deckelregel_ist_entweder_erhoben_oder_als_luecke_vermerkt():
    # Arrange
    erklaert = BLOCKING_CRITICAL | BLOCKING_MAJOR

    # Act
    erzeugt = _erzeugte_blocker()
    stumm = erklaert - erzeugt - NICHT_ERHOBENE_BLOCKER

    # Assert
    assert not stumm, (
        f"Diese Deckelregeln kann kein Audit ausloesen: {sorted(stumm)}. "
        "Entweder erheben oder in `NICHT_ERHOBENE_BLOCKER` eintragen — eine "
        "Regel, die im Katalog steht und nie greift, ist ein Versprechen "
        "an den Leser, das niemand einloest."
    )


def test_es_gibt_keine_ungemessene_deckelregel_mehr():
    """**Am 26.08.2026 leer geworden.**

    Hier stand `cookies_ohne_consent` — die einzige Regel, die der Katalog
    nannte und niemand erhob. Seit dem Browserlauf wird sie gemessen: Er
    klickt kein Banner an, also steht alles, was danach im Kontext liegt,
    ohne Zustimmung dort.

    Die Zusicherung bleibt und wird schaerfer: Waechst die Liste wieder,
    faellt es hier auf. Eine Ausnahme darf entstehen — aber nicht unbemerkt.
    """
    assert NICHT_ERHOBENE_BLOCKER == frozenset()


def test_die_erhobenen_regeln_sind_auch_erklaert():
    """Gegenprobe: kein Blocker, den der Katalog nicht kennt.

    Ein erzeugter Blocker ausserhalb der beiden Mengen deckelt nichts — er
    landet im Bericht als Kennung ohne Text und ohne Wirkung.
    """
    # Arrange / Act
    unbekannt = _erzeugte_blocker() - (BLOCKING_CRITICAL | BLOCKING_MAJOR)

    # Assert
    assert not unbekannt, f"Kennt der Katalog nicht: {sorted(unbekannt)}"
