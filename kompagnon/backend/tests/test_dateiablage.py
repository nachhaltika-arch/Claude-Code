"""Hochgeladene Dateien brauchen einen Ort, der einen Deploy überlebt.

Befund vom 16.08.2026, offen geblieben: Uploads liegen auf dem flüchtigen
Dateisystem des Containers. In den Blueprints stand kein `disk:` — also ist
bei jedem Deploy alles weg. Die eine Datei, die es gab, war schon verloren.

Beim Anfassen kam dazu, dass **drei Schreibstellen drei Regeln folgten**:

    routers/assets.py                      Path(os.getenv("UPLOAD_ROOT", "uploads"))
    routers/files.py                       Path("uploads")
    services/auftragsbestaetigung_pdf.py   Path("uploads") / "auftragsbestaetigungen"

Eine davon ließ sich umstellen, zwei nicht. Ein Datenträger, der nur ein
Drittel der Dateien auffängt, ist schlimmer als keiner: Er sieht aus, als wäre
das Problem gelöst.
"""
import os
from pathlib import Path

import pytest

from services.dateiablage import lead_verzeichnis, upload_wurzel


def test_ohne_einstellung_bleibt_es_beim_bisherigen_ort(monkeypatch):
    """Lokal und in den Tests soll sich nichts ändern."""
    monkeypatch.delenv("UPLOAD_ROOT", raising=False)

    assert upload_wurzel() == Path("uploads")


def test_die_einstellung_gewinnt(monkeypatch):
    monkeypatch.setenv("UPLOAD_ROOT", "/var/data/uploads")

    assert upload_wurzel() == Path("/var/data/uploads")


def test_eine_leere_einstellung_zaehlt_nicht(monkeypatch):
    """Eine gesetzte, aber leere Variable ist keine Angabe."""
    monkeypatch.setenv("UPLOAD_ROOT", "   ")

    assert upload_wurzel() == Path("uploads")


def test_das_lead_verzeichnis_haengt_daran(monkeypatch):
    monkeypatch.setenv("UPLOAD_ROOT", "/var/data/uploads")

    assert lead_verzeichnis(42) == Path("/var/data/uploads/42")


def test_die_nummer_wird_nicht_als_pfad_gelesen(monkeypatch):
    """Sonst schreibt eine gebastelte Nummer irgendwohin."""
    monkeypatch.setenv("UPLOAD_ROOT", "/var/data/uploads")

    with pytest.raises(ValueError):
        lead_verzeichnis("../../etc")


# ── Dass wirklich alle drei Stellen dieselbe Wurzel nehmen ────────────

@pytest.mark.parametrize("modul,funktion,argument", [
    ("routers.files", "_lead_dir", 7),
    ("routers.assets", "_lead_dir", 7),
])
def test_die_schreibstellen_folgen_der_einstellung(monkeypatch, tmp_path, modul, funktion, argument):
    """Ein Datenträger, der nur ein Drittel auffängt, ist schlimmer als keiner.

    Geprüft wird jetzt das Verzeichnis, das die Stelle beim Schreiben nimmt —
    nicht mehr eine Modulkonstante. Die gab es bis zum 18.08.2026, und sie war
    beim Import festgelegt: Der Pfad hing also davon ab, ob `UPLOAD_ROOT` schon
    gesetzt war, als das Modul geladen wurde.
    """
    import importlib

    # Ein echtes Verzeichnis, kein /var/data: Die Stellen legen es an.
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path))
    m = importlib.import_module(modul)
    importlib.reload(m)

    assert str(getattr(m, funktion)(argument)).startswith(str(tmp_path))


def test_auch_die_auftragsbestaetigung(monkeypatch, tmp_path):
    """Die PDFs lagen unter `uploads/auftragsbestaetigungen` — fest verdrahtet."""
    monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path))
    from services import auftragsbestaetigung_pdf
    import importlib
    importlib.reload(auftragsbestaetigung_pdf)

    assert auftragsbestaetigung_pdf.ablage_verzeichnis() == tmp_path / "auftragsbestaetigungen"
