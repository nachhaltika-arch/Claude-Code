# -*- coding: utf-8 -*-
"""Jeder Aufruf von `send_email` muss zu ihrer Unterschrift passen.

**Der Fund (26.08.2026).** Beim Verdrahten der Auftragsbestätigung (L-95)
zeigte sich, dass sie längst verdrahtet ist — nur falsch. Zwei Stellen rufen

    send_email(..., attachment_path=..., attachment_name=...)

und `send_email` kennt weder das eine noch das andere. Ihre Anhänge heißen
`attachments` und sind Tupel. Der Aufruf wirft also einen `TypeError`, **bevor
irgendeine Mail entsteht** — und beide Stellen fangen breit ab und schreiben
eine Zeile ins Protokoll:

- `routers/payments.py:598` — die **Willkommensmail nach der Stripe-Zahlung**.
  Sie trägt die Zugangsdaten des neuen Kunden. Es fehlte also nicht der
  Anhang, sondern die ganze Mail.
- `routers/leads_kaltakquise.py:239` — die Kaltakquise-Mail mit der Analyse.

**Warum das niemandem auffiel:** Es gibt keinen Absturz und keinen roten Test.
Im Protokoll steht „Willkommens-E-Mail Fehler", und wer nicht danach sucht,
sieht nichts. Genau die Form, die schon zweimal zugeschlagen hat — die
unerreichbaren Reiter (L-128) und die zwölf blockierenden KI-Aufrufe.

**Warum ein statischer Wächter und nicht nur zwei Korrekturen:** Ein falsch
benanntes Schlüsselwort ist in Python erst zur Laufzeit ein Fehler. `send_email`
wird an über vierzig Stellen gerufen; ein Test je Stelle wäre nicht zu halten.
Dieser hier vergleicht **jeden** Aufruf mit der tatsächlichen Unterschrift.
"""
import ast
import inspect
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parent.parent

#: Die Mailfunktionen, deren Aufrufe geprüft werden.
GEPRUEFT = ("send_email", "send_email_detailed")


def _erlaubte_namen(funktionsname: str) -> set:
    from services import email as mail_modul

    funktion = getattr(mail_modul, funktionsname)
    return set(inspect.signature(funktion).parameters)


def _quelldateien():
    for ordner in ("routers", "services", "automations"):
        pfad = WURZEL / ordner
        if pfad.is_dir():
            yield from sorted(pfad.rglob("*.py"))


def _namen_je_datei(baum):
    """Welche Namen in dieser Datei auf `services.email` zeigen.

    **Warum nicht einfach nach `send_email(` suchen:** Der erste Versuch tat
    das und meldete drei Fehltreffer — `widget_report.verify_email(company=…)`
    und `EmailService.send_email(to=…)` sind **andere** Funktionen mit eigenen
    Unterschriften. Ein Waechter, der Fehltreffer liefert, wird abgeschaltet;
    also wird der Name aufgeloest, statt ihn zu raten.
    """
    direkt, modul = {}, set()
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.ImportFrom):
            if knoten.module == "services.email":
                for teil in knoten.names:
                    if teil.name in GEPRUEFT:
                        direkt[teil.asname or teil.name] = teil.name
            elif knoten.module == "services":
                for teil in knoten.names:
                    if teil.name == "email":
                        modul.add(teil.asname or teil.name)
        elif isinstance(knoten, ast.Import):
            for teil in knoten.names:
                if teil.name == "services.email":
                    modul.add(teil.asname or "services.email")
    return direkt, modul


def _aufrufe():
    """Jeder Aufruf einer der Mailfunktionen, samt Schluesselwoertern.

    Ueber den Syntaxbaum, nicht ueber einen Suchausdruck: Ein Aufruf ueber
    mehrere Zeilen mit Kommentaren dazwischen ist der Normalfall in diesem
    Bestand, und ein Muster darueber waere geraten.
    """
    for pfad in _quelldateien():
        baum = ast.parse(pfad.read_text(encoding="utf-8"), filename=str(pfad))
        direkt, modul = _namen_je_datei(baum)
        if not direkt and not modul:
            continue
        for knoten in ast.walk(baum):
            if not isinstance(knoten, ast.Call):
                continue
            ziel = knoten.func
            if isinstance(ziel, ast.Name):
                funktion = direkt.get(ziel.id)
            elif (isinstance(ziel, ast.Attribute)
                  and isinstance(ziel.value, ast.Name)
                  and ziel.value.id in modul and ziel.attr in GEPRUEFT):
                funktion = ziel.attr
            else:
                funktion = None
            if funktion is None:
                continue
            yield (f"{pfad.parent.name}/{pfad.name}", knoten.lineno, funktion,
                   [s.arg for s in knoten.keywords if s.arg])


@pytest.mark.parametrize("funktion", GEPRUEFT)
def test_die_unterschrift_ist_die_erwartete(funktion):
    """Wenn sich `send_email` ändert, soll dieser Test es merken — nicht die
    Produktion."""
    namen = _erlaubte_namen(funktion)

    assert "attachments" in namen, (
        f"{funktion} hat keinen Parameter `attachments` mehr — dann stimmt "
        f"auch die Prüfung unten nicht mehr.")


def test_kein_aufruf_uebergibt_ein_wort_das_es_nicht_gibt():
    """Der eigentliche Wächter."""
    falsch = []
    for datei, zeile, funktion, woerter in _aufrufe():
        erlaubt = _erlaubte_namen(funktion)
        for wort in woerter:
            if wort not in erlaubt:
                falsch.append(f"{datei}:{zeile} {funktion}(… {wort}=…) — "
                              f"erlaubt: {', '.join(sorted(erlaubt))}")

    assert falsch == [], (
        "Aufrufe, die zur Laufzeit einen TypeError werfen:\n  "
        + "\n  ".join(falsch))


def test_der_waechter_sieht_ueberhaupt_etwas():
    """Eine Prüfung, die nichts findet, weil sie nichts liest, ist grün und
    wertlos. Diese hier bestätigt, dass Aufrufe gefunden werden."""
    gefunden = list(_aufrufe())

    assert len(gefunden) >= 10, f"nur {len(gefunden)} Mailaufrufe gefunden"
