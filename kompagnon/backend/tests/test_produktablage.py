# -*- coding: utf-8 -*-
"""Wo verkaufte Dateien liegen (L-100, ORDERS_06).

**Die Entscheidung, die davor stand.** ORDERS_06 hält den Bau an und verlangt
eine Wahl: Render-Datenträger, Objektspeicher oder Datei in der Datenbank.
Entscheidung David am 29.08.2026: **Cloudflare R2**.

**Warum das keine Geschmacksfrage war.** Das Dateisystem auf Render ist
flüchtig — bei jedem Deploy wird der Container neu gebaut. Ein Workbook, das
in ein Verzeichnis auf dem Server gelegt wird, ist nach dem nächsten Bugfix
weg, und mit ihm die Abruf-Adressen aller Käufer. Der Fehler tritt nicht beim
Ablegen auf, sondern beim übernächsten Deploy — die unangenehmste Sorte.

**Netlify wäre die falsche Rettung gewesen:** Dort liegen die Kundenwebsites,
also läge das verkaufte Produkt öffentlich unter einer erratbaren Adresse.

**Was hier geprüft wird und was nicht.** Ohne Zugangsdaten läuft kein Test
gegen R2 — geprüft wird die Rechnung drumherum: dass eine unvollständige
Einrichtung als solche erkannt wird und **sagt, was fehlt**, dass keine
Adresse ohne Ablaufzeit entsteht, und dass eine fehlende Einrichtung nicht als
leeres Ergebnis durchgeht. Der Lauf gegen den echten Speicher ist die
Messseite und braucht Davids Schlüssel.
"""
import pytest

ALLE = {
    "R2_ACCOUNT_ID": "abc123",
    "R2_ACCESS_KEY_ID": "schluessel",
    "R2_SECRET_ACCESS_KEY": "geheim",
    "R2_BUCKET": "kompagnon-produkte",
}


@pytest.fixture()
def eingerichtet(monkeypatch):
    for name, wert in ALLE.items():
        monkeypatch.setenv(name, wert)
    return ALLE


@pytest.fixture()
def leer(monkeypatch):
    for name in ALLE:
        monkeypatch.delenv(name, raising=False)


class TestEinrichtung:
    def test_ohne_zugangsdaten_nicht_eingerichtet(self, leer):
        # Arrange
        from services import produktablage as dateiablage

        # Act & Assert
        assert dateiablage.ist_eingerichtet() is False

    def test_mit_allen_vier_werten_eingerichtet(self, eingerichtet):
        # Arrange
        from services import produktablage as dateiablage

        # Act & Assert
        assert dateiablage.ist_eingerichtet() is True

    def test_drei_von_vier_gilt_nicht_als_eingerichtet(self, eingerichtet,
                                                       monkeypatch):
        """Eine halbe Einrichtung ist keine. Sonst scheitert erst der
        Abruf des Käufers, und zwar nach der Zahlung."""
        # Arrange
        from services import produktablage as dateiablage
        monkeypatch.delenv("R2_BUCKET")

        # Act & Assert
        assert dateiablage.ist_eingerichtet() is False

    def test_fehlende_werte_werden_benannt(self, eingerichtet, monkeypatch):
        """„Nicht eingerichtet" schickt niemanden an die richtige Stelle."""
        # Arrange
        from services import produktablage as dateiablage
        monkeypatch.delenv("R2_SECRET_ACCESS_KEY")
        monkeypatch.delenv("R2_BUCKET")

        # Act
        fehlt = dateiablage.was_fehlt()

        # Assert
        assert fehlt == ["R2_BUCKET", "R2_SECRET_ACCESS_KEY"]

    def test_leerraum_zaehlt_nicht_als_wert(self, eingerichtet, monkeypatch):
        # Arrange
        from services import produktablage as dateiablage
        monkeypatch.setenv("R2_BUCKET", "   ")

        # Act & Assert
        assert dateiablage.ist_eingerichtet() is False
        assert "R2_BUCKET" in dateiablage.was_fehlt()


class TestSignierteAdresse:
    def test_ohne_einrichtung_gibt_es_keine_adresse(self, leer):
        """`None` und keine Ausnahme: Der Aufrufer entscheidet, wie er das
        meldet — der Käufer bekommt 503, nicht 500."""
        # Arrange
        from services import produktablage as dateiablage

        # Act & Assert
        assert dateiablage.signierte_adresse("workbook.pdf") is None

    def test_ohne_dateikennung_gibt_es_keine_adresse(self, eingerichtet):
        """Ein Produkt ohne hinterlegte Datei darf keine Adresse bekommen —
        sonst zeigt der Abruf-Link auf den Bucket-Wurzelpfad."""
        # Arrange
        from services import produktablage as dateiablage

        # Act & Assert
        assert dateiablage.signierte_adresse("") is None
        assert dateiablage.signierte_adresse(None) is None

    def test_adresse_wird_mit_ablauf_signiert(self, eingerichtet, monkeypatch):
        # Arrange
        from services import produktablage as dateiablage

        gesehen = {}

        class FalscherKlient:
            def generate_presigned_url(self, vorgang, Params, ExpiresIn):
                gesehen.update(vorgang=vorgang, params=Params, ablauf=ExpiresIn)
                return "https://r2.example/signiert"

        monkeypatch.setattr(dateiablage, "_klient", lambda: FalscherKlient())

        # Act
        adresse = dateiablage.signierte_adresse("workbook.pdf", sekunden=900)

        # Assert
        assert adresse == "https://r2.example/signiert"
        assert gesehen["vorgang"] == "get_object"
        assert gesehen["params"] == {"Bucket": "kompagnon-produkte",
                                     "Key": "workbook.pdf"}
        assert gesehen["ablauf"] == 900

    def test_ablaufzeit_ist_nach_oben_begrenzt(self, eingerichtet, monkeypatch):
        """Ein Link, der ein Jahr gilt, ist kein signierter Link, sondern
        eine öffentliche Adresse mit Umweg."""
        # Arrange
        from services import produktablage as dateiablage

        gesehen = {}

        class FalscherKlient:
            def generate_presigned_url(self, vorgang, Params, ExpiresIn):
                gesehen["ablauf"] = ExpiresIn
                return "https://r2.example/signiert"

        monkeypatch.setattr(dateiablage, "_klient", lambda: FalscherKlient())

        # Act
        dateiablage.signierte_adresse("workbook.pdf", sekunden=999_999)

        # Assert
        assert gesehen["ablauf"] == dateiablage.ABLAUF_MAX

    def test_ein_fehler_des_speichers_wird_nicht_zur_ausnahme(
            self, eingerichtet, monkeypatch):
        """Der Käufer hat bezahlt. Ein Absturz hier gibt ihm 500 statt einer
        Auskunft — und im Protokoll steht ein Stapelabzug statt einer Aussage."""
        # Arrange
        from services import produktablage as dateiablage

        class KaputterKlient:
            def generate_presigned_url(self, *_, **__):
                raise RuntimeError("R2 nicht erreichbar")

        monkeypatch.setattr(dateiablage, "_klient", lambda: KaputterKlient())

        # Act & Assert
        assert dateiablage.signierte_adresse("workbook.pdf") is None
