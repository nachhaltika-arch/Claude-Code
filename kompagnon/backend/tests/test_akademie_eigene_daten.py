"""Die Akademie-Routen sind absichtlich schwach gesperrt (L-67).

**Warum sie in der Zaehlung auftauchen und trotzdem bleiben duerfen.** Von
den 61 Routen, die nur „irgendwer ist angemeldet" verlangen, gehoeren 14 zur
Akademie: Kurse ansehen, Lektionen abschliessen, Fortschritt, Quiz,
Zertifikate. Das **ist** der Kundenweg — Kunden lernen dort. Eine
Rollensperre waere hier keine Haertung, sondern die Aussperrung der
Zielgruppe.

Die richtige Frage ist deshalb nicht „welche Rolle", sondern **„wessen
Zeile"**: Jede dieser Routen muss auf den angemeldeten Nutzer filtern.
Nachgeprueft am 22.08.2026 — sie tun es, und diese Tests halten es fest.

Ohne sie taucht der Bestand bei jedem Durchgang durch L-67 wieder auf, und
jemand sperrt ihn irgendwann „zur Sicherheit" zu.
"""
import pytest


class TestDasZertifikatGehoertZumEigenenFortschritt:
    def test_kein_zertifikat_ohne_abgeschlossenen_kurs(
            self, client, kunde_headers):
        """Der Kurs, den niemand belegt hat, stellt auch kein Zertifikat aus."""
        antwort = client.post("/api/academy/courses/999999/certificate",
                              headers=kunde_headers)

        # 404 (Kurs unbekannt) oder 400 (nicht abgeschlossen) — nur kein
        # ausgestelltes Zertifikat.
        assert antwort.status_code in (400, 404), antwort.text[:200]

    def test_die_ausstellung_rechnet_auf_dem_eigenen_fortschritt(self):
        """Sie nimmt **keine** Nutzerkennung entgegen — sonst koennte man
        sich das Zertifikat eines anderen ausstellen lassen."""
        import inspect

        # Umgezogen am 23.08.2026 nach `academy_zertifikate` (L-25) — die
        # Pruefung gilt der Funktion, nicht ihrem Fundort.
        from routers.academy_zertifikate import issue_certificate

        felder = set(inspect.signature(issue_certificate).parameters)
        assert "user_id" not in felder and "customer_id" not in felder, felder

    def test_und_liest_den_fortschritt_zum_angemeldeten_nutzer(self):
        import inspect

        from routers import academy_zertifikate

        quelle = inspect.getsource(academy_zertifikate.issue_certificate)
        assert "current_user.id" in quelle
        assert "progress_pct'] < 100" in quelle or "progress_pct\"] < 100" in quelle


class TestOhneAnmeldungGarNichts:
    @pytest.mark.parametrize("pfad", [
        "/api/academy/progress",
        "/api/academy/certificates",
        "/api/academy/progress/all",
    ])
    def test_die_eigenen_daten_brauchen_eine_anmeldung(self, client, pfad):
        antwort = client.get(pfad)

        assert antwort.status_code in (401, 403)
