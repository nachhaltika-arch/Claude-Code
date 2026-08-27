"""Drei Rechte, die eine Entscheidung brauchten (L-05, 22.08.2026).

Sie standen offen, weil ihr Durchsetzen kein Aufräumen gewesen wäre, sondern
eine **Verhaltensänderung** — jede hätte jemandem etwas weggenommen. David hat
sie am 22.08. entschieden, und zwei davon gegen die Vorgabe:

| Recht | Vorgabe | Routen tragen | Entschieden |
|---|---|---|---|
| `manage_projects` | admin, superadmin | `require_innendienst` | Matrix korrigiert — Auditor dazu |
| `deploy_kas_pages` | superadmin | `require_superadmin` | unverändert — siehe unten |
| `manage_system_settings` | superadmin | `require_admin` | Recht durchgesetzt — nur Superadmin |

**Der Gedanke bei `manage_projects`:** Die Vorgabe wurde irgendwann
geschrieben, die Routen sind gewachsen. Wo beide auseinandergehen, ist nicht
automatisch die Route falsch — der Auditor arbeitet an Projekten. Erst
nachdem die Matrix die gelebte Wirklichkeit abbildet, lässt sich das Recht
durchsetzen, **ohne** jemandem etwas wegzunehmen.

**Bei `manage_system_settings` umgekehrt:** Wer Rechte vergeben darf, kann
sich alles geben. Diese eine Trennung ist die Maßnahme wert — der Admin
verliert die Rechtepflege, und das ist der Sinn.

**`deploy_kas_pages` ist ein korrigierter Irrtum, noch am selben Tag.** Es lag
kurz beim Admin und war an den **Kundenseiten**-Deploys verdrahtet — beides
auf Grund einer Fehldeutung des Namens: KAS heißt **KOMPAGNON Agentur
Seiten**, die eigene Marketingseite. Sie live zu stellen ist kein
Tagesgeschäft im Website-Bau, sondern eine Veröffentlichung im eigenen Namen;
`POST /api/kas/deploy` trägt seit jeher `require_superadmin`, und Matrix und
Route waren widerspruchsfrei. Es gab hier nichts zu entscheiden, nur etwas zu
verdrahten.

Der Fehler fällt in dieselbe Familie wie die Befunde, die er beheben sollte:
Ein Name legte etwas nahe, was nicht stimmte — und keine rote Zeile hätte es
gemeldet.
"""
import pytest
from sqlalchemy import text


@pytest.fixture
def als_mitarbeiter(client, mitarbeiter_headers):
    return mitarbeiter_headers


class TestMatrixBildetDieWirklichkeitAb:
    def test_der_mitarbeiter_darf_projekte_verwalten(self):
        from routers.admin_settings import DEFAULT_PERMISSIONS

        assert "manage_projects" in DEFAULT_PERMISSIONS["mitarbeiter"], (
            "Die 61 Routen unter /api/projects stehen auf require_innendienst — "
            "ohne diesen Eintrag naehme das Durchsetzen dem Mitarbeiter alle weg")

    def test_die_eigene_agenturseite_bleibt_beim_superadmin(self):
        """**Korrigiert am 22.08.2026, noch am selben Tag.**

        `deploy_kas_pages` war kurz beim Admin und an den **Kundenseiten**-
        Deploys verdrahtet. Beides beruhte auf einem Irrtum ueber den Namen:
        KAS heisst **KOMPAGNON Agentur Seiten** — die eigene Marketingseite.
        Sie live zu stellen ist kein Tagesgeschaeft im Website-Bau, sondern
        eine Veroeffentlichung im eigenen Namen; `POST /api/kas/deploy` traegt
        seit jeher `require_superadmin`, und Matrix und Route waren
        widerspruchsfrei.

        Der Fehler faellt in dieselbe Familie wie die Befunde, die er
        beheben sollte: Ein Name legte etwas nahe, was nicht stimmte, und
        niemand haette es an einer roten Zeile gemerkt.
        """
        from routers.admin_settings import DEFAULT_PERMISSIONS

        assert "deploy_kas_pages" not in DEFAULT_PERMISSIONS["admin"]
        assert "deploy_kas_pages" in DEFAULT_PERMISSIONS["superadmin"]

    def test_das_recht_haengt_an_den_eigenen_seiten(self):
        """Und nicht an den Kundenseiten — dort trug es kurzzeitig."""
        import pathlib

        from routers import kas_router, projects_netlify

        eigene = pathlib.Path(kas_router.__file__).read_text(encoding="utf-8")
        kunden = pathlib.Path(projects_netlify.__file__).read_text(encoding="utf-8")

        assert 'verlangt_recht("deploy_kas_pages")' in eigene
        assert 'verlangt_recht("deploy_kas_pages")' not in kunden

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
        antwort = client.patch("/api/admin/roles/mitarbeiter",
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
                        role="superadmin", is_active=True,
                        # Seit dem 27.08.2026 liest die Anmeldung dieses
                        # Feld (Bestaetigungsriegel). Ein Testkonto steht
                        # fuer einen eingerichteten Zugang.
                        is_verified=True))
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
