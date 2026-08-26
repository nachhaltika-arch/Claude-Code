# -*- coding: utf-8 -*-
"""Der Kunde lädt Bilder und Dokumente hoch — angemeldet, ohne Token.

**Der Auftrag (26.08.2026, David).** Zum Briefing gehören Logo, Fotos und
Unterlagen. Ohne sie ist ein Briefing eine Beschreibung von Bildern, die
niemand hat.

**Was schon da war:** Die ganze Ablage. `POST /api/files/upload/{lead_id}`
für den Innendienst, `POST /api/files/portal/{token}/upload` für das
QR-Portal, `services/dateiablage.py` mit `UPLOAD_ROOT` auf dem eingehängten
Datenträger. Der **angemeldete** Kunde hatte keinen Weg: Der ganze Router
liegt hinter `require_innendienst`, und einen Token hat er nicht in der Hand.

**Warum nicht einfach die Sperre lockern:** Diese Routen führen die Dateien
aller Betriebe — Verträge, Angebote, Zugangsdaten. `GET /{lead_id}` listete
sie bis zum 22.08. für **jeden** Angemeldeten auf (L-67). Ein eigener
Kundenweg mit Eigentumsprüfung nimmt dem Innendienst nichts und öffnet
nichts, was zu war.

**Grenzen, die bleiben:** Dateityp (Bilder, PDF, Office, ZIP) und 20 MB.
Beides galt schon; hier wird nur festgehalten, dass es auch auf dem neuen
Weg gilt — eine Grenze, die nur an einer von drei Türen hängt, ist keine.
"""
import io

import pytest

pytestmark = pytest.mark.usefixtures("app")

EIN_PNG = (b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)


def _hochladen(client, headers, lead_id, name="logo.png", inhalt=EIN_PNG,
               art="logo"):
    return client.post(
        f"/api/files/mein/{lead_id}/upload", headers=headers,
        files={"file": (name, io.BytesIO(inhalt), "application/octet-stream")},
        data={"file_type": art, "note": "vom Kunden"})


def _liste(client, headers, lead_id):
    return client.get(f"/api/files/mein/{lead_id}", headers=headers)


@pytest.fixture(autouse=True)
def _aufraeumen(app, kunde_user):
    yield
    from pathlib import Path

    from database import SessionLocal
    from sqlalchemy import text

    db = SessionLocal()
    try:
        pfade = [z[0] for z in db.execute(
            text("SELECT file_path FROM project_files WHERE lead_id = :l"),
            {"l": kunde_user.lead_id}).fetchall()]
        db.execute(text("DELETE FROM project_files WHERE lead_id = :l"),
                   {"l": kunde_user.lead_id})
        db.commit()
    finally:
        db.close()
    for pfad in pfade:
        try:
            Path(pfad).unlink()
        except OSError:
            pass


class TestHochladen:
    def test_er_laedt_sein_logo_hoch(self, client, kunde_headers, kunde_user):
        # Act
        antwort = _hochladen(client, kunde_headers, kunde_user.lead_id)

        # Assert
        assert antwort.status_code == 200, antwort.text
        assert antwort.json()["original_filename"] == "logo.png"

    def test_die_datei_liegt_wirklich_auf_der_platte(self, client, kunde_headers,
                                                     kunde_user):
        """Ein Eintrag in der Tabelle ohne Datei daneben waere die
        unangenehmste Sorte Fehler: Die Liste zeigt sie, der Download nicht."""
        from pathlib import Path

        _hochladen(client, kunde_headers, kunde_user.lead_id)

        eintrag = _liste(client, kunde_headers, kunde_user.lead_id).json()[0]
        assert Path(eintrag["file_path"]).exists()

    def test_sie_ist_als_vom_kunden_gekennzeichnet(self, client, kunde_headers,
                                                   kunde_user):
        """Der Innendienst muss sehen, was der Kunde selbst beigesteuert hat."""
        _hochladen(client, kunde_headers, kunde_user.lead_id)

        eintrag = _liste(client, kunde_headers, kunde_user.lead_id).json()[0]
        assert eintrag["uploaded_by_role"] == "kunde"

    def test_er_sieht_sie_in_seiner_liste(self, client, kunde_headers,
                                          kunde_user):
        _hochladen(client, kunde_headers, kunde_user.lead_id, name="grundriss.pdf",
                   inhalt=b"%PDF-1.4 Probe", art="sonstiges")

        namen = [d["original_filename"]
                 for d in _liste(client, kunde_headers, kunde_user.lead_id).json()]

        assert namen == ["grundriss.pdf"]

    def test_er_laedt_sie_wieder_herunter(self, client, kunde_headers,
                                          kunde_user):
        _hochladen(client, kunde_headers, kunde_user.lead_id,
                   name="grundriss.pdf", inhalt=b"%PDF-1.4 Probe")
        kennung = _liste(client, kunde_headers, kunde_user.lead_id).json()[0]["id"]

        antwort = client.get(f"/api/files/mein/download/{kennung}",
                             headers=kunde_headers)

        assert antwort.status_code == 200
        assert antwort.content == b"%PDF-1.4 Probe"


class TestDieGrenzenDerAblage:
    def test_eine_ausfuehrbare_datei_wird_abgewiesen(self, client, kunde_headers,
                                                     kunde_user):
        """Der naheliegendste Missbrauch einer Ablage ist, etwas
        Ausfuehrbares hineinzulegen."""
        antwort = _hochladen(client, kunde_headers, kunde_user.lead_id,
                             name="schaedling.exe", inhalt=b"MZ")

        assert antwort.status_code == 400
        assert "nicht erlaubt" in antwort.text

    def test_zu_grosse_dateien_werden_abgewiesen(self, client, kunde_headers,
                                                 kunde_user):
        antwort = _hochladen(client, kunde_headers, kunde_user.lead_id,
                             name="riesig.png", inhalt=b"\x89PNG" + b"0" * (21 * 1024 * 1024))

        assert antwort.status_code == 413


class TestDieGrenzenZwischenBetrieben:
    def test_er_laedt_nichts_in_einen_fremden_betrieb(
            self, client, kunde_headers, fremder_betrieb):
        assert _hochladen(client, kunde_headers, fremder_betrieb).status_code == 403

    def test_er_sieht_die_dateien_eines_fremden_betriebs_nicht(
            self, client, kunde_headers, fremder_betrieb):
        assert _liste(client, kunde_headers, fremder_betrieb).status_code == 403

    def test_er_laedt_keine_fremde_datei_herunter(
            self, client, kunde_headers, auth_headers, fremder_betrieb):
        """Die Dateikennung ist eine fortlaufende Zahl — hochzuzaehlen ist
        der naheliegendste Angriff, und der Pfad nennt keinen Betrieb."""
        # Arrange — der Innendienst legt eine Datei in einen fremden Betrieb
        client.post(f"/api/files/upload/{fremder_betrieb}", headers=auth_headers,
                    files={"file": ("fremd.pdf", io.BytesIO(b"%PDF-1.4 fremd"),
                                    "application/pdf")},
                    data={"file_type": "sonstiges", "note": ""})
        fremde = client.get(f"/api/files/{fremder_betrieb}",
                            headers=auth_headers).json()[0]["id"]

        # Act
        antwort = client.get(f"/api/files/mein/download/{fremde}",
                             headers=kunde_headers)

        # Assert
        assert antwort.status_code == 403

    def test_ohne_anmeldung_gar_nichts(self, client, kunde_user):
        assert _liste(client, {}, kunde_user.lead_id).status_code in (401, 403)
