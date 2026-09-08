# -*- coding: utf-8 -*-
"""Hochgeladene Dateien gehoeren nicht ins Repository (08.09.2026).

**Gefunden beim Oeffnen eines Pull Requests.** Im Diff nach `main` standen
zwei PDFs aus `uploads/` — eine Auftragsbestaetigung und eine Testattrappe.
Beide waren Testdaten („Probe L09 GmbH", „Anna Beispiel"), der Weg dorthin
war es nicht:

`kompagnon/backend/.gitignore` fuehrt `uploads/` seit Langem. Diese Regel
gilt aber nur **unterhalb ihres eigenen Verzeichnisses** — und die Anwendung
legt ihre Dateien in `uploads/` an der **Wurzel** ab. Dort galt keine Regel.
Ein `git add -A` nahm sie mit, und **das Repository ist oeffentlich**.

Was heute eine Probe-Auftragsbestaetigung war, ist beim naechsten Mal die
eines echten Kunden — mit Namen, Anschrift und Auftragswert. Deshalb steht
die Regel jetzt auch in der Wurzel, und dieser Test haelt sie fest.

**Beide Richtungen.** „Keine Datei ist versioniert" waere auch dann gruen,
wenn jemand das Verzeichnis geloescht haette; „die Regel greift" waere auch
dann gruen, wenn schon Dateien drinstuenden.
"""
import pathlib
import subprocess

WURZEL = pathlib.Path(__file__).resolve().parents[3]


def _git(*args) -> str:
    return subprocess.run(("git", *args), cwd=WURZEL, capture_output=True,
                          text=True, check=False).stdout


def test_keine_hochgeladene_datei_ist_versioniert():
    versioniert = [z for z in _git("ls-files", "uploads").splitlines() if z]
    assert versioniert == [], (
        "Diese hochgeladenen Dateien liegen im oeffentlichen Repository:\n  "
        + "\n  ".join(versioniert)
        + "\nMit `git rm --cached <datei>` herausnehmen."
    )


def test_die_ignorierregel_greift_an_der_wurzel():
    # Die positive Haelfte: Ein Pfad, den es noch nicht gibt, muss von der
    # Regel erfasst sein — sonst faengt der Test oben nur den Ist-Zustand.
    treffer = _git("check-ignore", "-v",
                   "uploads/auftragsbestaetigungen/AB-99999999-echt.pdf")
    assert "uploads/" in treffer, (
        "uploads/ an der Wurzel ist nicht ignoriert — die naechste "
        "Auftragsbestaetigung landet im oeffentlichen Repository."
    )
