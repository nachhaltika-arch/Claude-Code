"""Drei Rechte, die eine Entscheidung brauchten (L-05, 22.08.2026).

Sie standen offen, weil ihr Durchsetzen kein Aufräumen gewesen wäre, sondern
eine **Verhaltensänderung** — jede hätte jemandem etwas weggenommen. David hat
sie am 22.08. entschieden, und zwei davon gegen die Vorgabe:

| Recht | Vorgabe vorher | Routen tragen | Entschieden |
|---|---|---|---|
| `manage_projects` | admin, superadmin | `require_innendienst` | Matrix korrigiert — Auditor dazu |
| `deploy_kas_pages` | superadmin | `require_admin` | Matrix korrigiert — Admin dazu |
| `manage_system_settings` | superadmin | `require_admin` | Recht durchgesetzt — nur Superadmin |

**Der Gedanke hinter den ersten beiden:** Die Vorgabe wurde irgendwann
geschrieben, die Routen sind gewachsen. Wo beide auseinandergehen, ist nicht
automatisch die Route falsch — der Auditor arbeitet an Projekten, und
Ausrollen ist Tagesgeschäft im Website-Bau. Erst nachdem die Matrix die
gelebte Wirklichkeit abbildet, lässt sich das Recht durchsetzen, **ohne**
jemandem etwas wegzunehmen.

**Beim dritten umgekehrt:** Wer Rechte vergeben darf, kann sich alles geben.
Diese eine Trennung ist die Maßnahme wert — der Admin verliert die
Rechtepflege, und das ist der Sinn.
"""
import pytest
from sqlalchemy import text


@pytest.fixture
def als_auditor(client, auditor_headers):
    return auditor_headers


class TestMatrixBildetDieWirklichkeitAb:
    def test_der_auditor_darf_projekte_verwalten(self):
        from routers.admin_settings import DEFAULT_PERMISSIONS

        assert "manage_projects" in DEFAULT_PERMISSIONS["auditor"], (
            "Die 61 Routen unter /api/projects stehen auf require_innendienst — "
            "ohne diesen Eintrag naehme das Durchsetzen dem Auditor alle weg")

    def test_der_admin_darf_ausrollen(self):
        from routers.admin_settings import DEFAULT_PERMISSIONS

        assert "deploy_kas_pages" in DEFAULT_PERMISSIONS["admin"]

    def test_die_rechtepflege_bleibt_beim_superadmin(self):
        """Die eine Trennung, die nicht aufgeweicht wird."""
        from routers.admin_settings import DEFAULT_PERMISSIONS

        assert "manage_system_settings" not in DEFAULT_PERMISSIONS["admin"]
        assert "manage_system_settings" in DEFAULT_PERMISSIONS["superadmin"]


class TestDurchgesetzt:
    @pytest.mark.parametrize("recht", ["manage_projects", "deploy_kas_pages",
                                       "manage_system_settings"])
    def test_alle_drei_wirken(self, recht):
        from services.rechte import DURCHGESETZTE_RECHTE

        assert recht in DURCHGESETZTE_RECHTE

    def test_vierzehn_von_achtzehn(self):
        """Die Zahl selbst ist der Befund von L-05 — sie gehoert gezaehlt."""
        from routers.admin_settings import DEFAULT_PERMISSIONS
        from services.rechte import DURCHGESETZTE_RECHTE

        alle = {r for rechte in DEFAULT_PERMISSIONS.values() for r in rechte}
        assert len(alle) == 18, f"Die Matrix hat {len(alle)} Rechte"
        assert len(DURCHGESETZTE_RECHTE) == 14, (
            f"{len(DURCHGESETZTE_RECHTE)} durchgesetzt — Zahl im Befund anpassen")


class TestRechtepflege:
    def test_der_admin_kommt_nicht_mehr_an_die_rechtematrix(self, client, auth_headers):
        """Der Sinn der Entscheidung: Wer Rechte vergeben darf, kann sich
        alles geben."""
        antwort = client.patch("/api/admin/roles/auditor",
                               json={"permissions": {"view_leads": False}},
                               headers=auth_headers)

        assert antwort.status_code == 403, antwort.text[:200]

    def test_der_superadmin_kommt_weiterhin_durch(self, client, app):
        """**Die Ausweichtuer.** Ohne sie waere die Rechtepflege nach dieser
        Aenderung fuer niemanden mehr erreichbar — und der Bildschirm, der sie
        zurueckdrehen koennte, ebenfalls gesperrt.

        `hat_recht` gibt dem Superadmin immer recht; dieser Test haelt das
        offen. Wer ihn rot sieht, hat die Tuer zugemauert.
        """
        from auth import hash_password
        from database import SessionLocal, User

        db = SessionLocal()
        try:
            db.execute(text("DELETE FROM users WHERE email = 'super-l05@example.com'"))
            db.commit()
            db.add(User(email="super-l05@example.com",
                        password_hash=hash_password("egal"),
                        role="superadmin", is_active=True))
            db.commit()
        finally:
            db.close()

        anmeldung = client.post("/api/auth/login",
                                json={"email": "super-l05@example.com",
                                      "password": "egal"})
        assert anmeldung.status_code == 200, anmeldung.text[:200]
        kopf = {"Authorization": f"Bearer {anmeldung.json()['access_token']}"}

        antwort = client.get("/api/admin/roles", headers=kopf)

        assert antwort.status_code == 200, antwort.text[:200]
