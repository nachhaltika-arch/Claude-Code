"""L-05, vierter Schritt: drei weitere Rechte, die wirklich sperren.

Stand vor dem 21.08.2026: 5 von 18 Rechten waren durchgesetzt
(`view_leads`, `view_projects`, `delete_leads`, `manage_users`,
`manage_settings`). Die uebrigen 13 liessen sich im Bildschirm „Rollen"
anhaken und abhaken, ohne dass etwas geschah — der Bildschirm kennzeichnet
sie seit dem 19.08. immerhin als *beschreibend*.

**Der Massstab, nach dem hier ausgewaehlt wurde:** Ein Recht kommt nur dazu,
wenn die heutige Sperre der Route **genau** der Vorgabe in
`DEFAULT_PERMISSIONS` entspricht. Dann ist das Durchsetzen additiv — es nimmt
niemandem etwas weg, sondern macht den Haken wirksam.

    create_leads   POST /api/leads/       heute require_innendienst
                   Vorgabe: superadmin, admin, auditor  -> deckungsgleich
    edit_leads     PATCH /api/leads/{id}  heute require_innendienst
                   Vorgabe: superadmin, admin, auditor  -> deckungsgleich
    view_users     GET /api/admin/users   heute require_admin
                   Vorgabe: superadmin, admin           -> deckungsgleich

**Bewusst nicht dazugenommen**, weil es eine Verhaltensaenderung waere und
damit eine Entscheidung:

    manage_projects   Vorgabe: superadmin, admin — die Projektrouten stehen
                      heute aber auf `require_innendienst`, also **auch** dem
                      Auditor offen. Durchsetzen naehme ihm etwas weg.
    view_settings     `GET /api/admin/settings` liefert Werte, die der
                      Bildschirm zum Anzeigen braucht; die Vorgabe kennt das
                      Recht nur fuer Admins, gelesen wird es aber auch
                      anderswo. Erst pruefen, dann sperren.
    download_pdf,     Haben laut Vorgabe **alle** Rollen. Durchsetzen
    view_audits,      aendert heute nichts und waere trotzdem richtig — der
    view_dashboard    Haken wuerde wirken, sobald jemand ihn wegnimmt. Sie
                      haengen aber an Routen, die auch oeffentlich erreichbar
                      sind (Widget, Kundenportal); das ist mehr als ein
                      Einzeiler und gehoert eigens gemessen.
    deploy_kas_pages, Hat per Vorgabe nur der Superadmin — siehe die
    manage_system_    Begruendung in `services/rechte.py`.
    settings
"""
import pytest
from sqlalchemy import text

from database import SessionLocal
from services.rechte import DURCHGESETZTE_RECHTE


NEUE_RECHTE = ("create_leads", "edit_leads", "view_users")


@pytest.fixture
def db(app):
    sitzung = SessionLocal()
    try:
        yield sitzung
    finally:
        sitzung.close()


@pytest.fixture
def recht_entziehen(db):
    """Nimmt der Rolle `auditor` bzw. `admin` ein Recht — und gibt es zurueck."""
    gesetzt = []

    def entziehen(rolle, recht):
        db.execute(text(
            "INSERT INTO role_permissions (role, permission, is_allowed) "
            "VALUES (:r, :p, false) "
            "ON CONFLICT (role, permission) DO UPDATE SET is_allowed = false"
        ), {"r": rolle, "p": recht})
        db.commit()
        gesetzt.append((rolle, recht))

    yield entziehen

    for rolle, recht in gesetzt:
        db.execute(text(
            "UPDATE role_permissions SET is_allowed = true "
            "WHERE role = :r AND permission = :p"
        ), {"r": rolle, "p": recht})
    db.commit()


class TestEintrag:
    @pytest.mark.parametrize("recht", NEUE_RECHTE)
    def test_das_recht_gilt_als_durchgesetzt(self, recht):
        """Sonst kennzeichnet der Bildschirm es weiter als beschreibend —
        er wuerde dann andersherum luegen."""
        assert recht in DURCHGESETZTE_RECHTE

    def test_die_liste_nennt_nur_rechte_die_es_gibt(self):
        from routers.admin_settings import PERM_LABELS

        assert set(DURCHGESETZTE_RECHTE) <= set(PERM_LABELS)


class TestWirkung:
    """Am Endpunkt geprueft, nicht an der Liste — eine Eintragung ist keine
    Sperre. Siehe [[feedback-am-gegenstand-pruefen]]."""

    def test_ohne_create_leads_geht_das_anlegen_nicht_mehr(
            self, client, auth_headers, recht_entziehen):
        # Arrange
        recht_entziehen("admin", "create_leads")

        # Act
        antwort = client.post("/api/leads/", headers=auth_headers, json={
            "company_name": "Probe Rechte GmbH",
            "website_url": "https://probe-rechte.example",
        })

        # Assert
        assert antwort.status_code == 403
        assert "create_leads" in antwort.text

    def test_mit_dem_recht_geht_es_wieder(self, client, auth_headers, db):
        # Act
        antwort = client.post("/api/leads/", headers=auth_headers, json={
            "company_name": "Probe Rechte GmbH 2",
            "website_url": "https://probe-rechte-2.example",
        })

        # Assert
        assert antwort.status_code in (200, 201), antwort.text

        # Aufraeumen
        db.execute(text("DELETE FROM leads WHERE company_name LIKE 'Probe Rechte%'"))
        db.commit()

    def test_ohne_view_users_bleibt_die_benutzerliste_zu(
            self, client, auth_headers, recht_entziehen):
        # Arrange
        recht_entziehen("admin", "view_users")

        # Act
        antwort = client.get("/api/admin/users", headers=auth_headers)

        # Assert
        assert antwort.status_code == 403

    def test_der_superadmin_sperrt_sich_nicht_selbst_aus(self, recht_entziehen):
        """Sonst nimmt ein Haken dem Letzten das Recht, ihn zurueckzunehmen."""
        from services.rechte import hat_recht

        # Arrange
        recht_entziehen("superadmin", "view_users")

        # Assert
        assert hat_recht("superadmin", "view_users") is True


# ── Fuenfter Schritt: view_settings (22.08.2026) ─────────────────────
#
# Derselbe enge Massstab wie bei den drei vom 21.08.: Ein Recht kommt nur
# dazu, wenn die heutige Sperre der Route **genau** der Vorgabe entspricht.
# `GET /api/admin/settings` traegt `require_admin` (superadmin, admin),
# `DEFAULT_PERMISSIONS` gibt `view_settings` an dieselben zwei. Das
# Durchsetzen ist damit additiv — es nimmt niemandem etwas weg, es macht den
# Haken im Bildschirm „Rollen" wirksam.
#
# **Nicht dazugekommen und warum:** `create_audits` haette laut Vorgabe
# superadmin, admin und auditor — die Route dahinter (`POST /api/audit/start`)
# ist aber der **oeffentliche** Widget-Weg mit Mengengrenze statt Rollenpruefung.
# Da deckt sich nichts; das gehoert eigens gemessen, so wie `download_pdf`,
# `view_audits` und `view_dashboard`.


def test_view_settings_wirkt_wirklich(client, auth_headers, app):
    """Wer das Recht entzieht, kommt nicht mehr an die Einstellungen.

    Das ist der Unterschied zwischen einem Haken, der etwas tut, und einem,
    der nur dasteht — und genau der ist L-05.
    """
    from sqlalchemy import text
    from database import SessionLocal

    db = SessionLocal()
    try:
        db.execute(text(
            "INSERT INTO role_permissions (role, permission, is_allowed) "
            "VALUES ('admin', 'view_settings', false) "
            "ON CONFLICT (role, permission) DO UPDATE SET is_allowed = false"))
        db.commit()

        gesperrt = client.get("/api/admin/settings", headers=auth_headers)

        db.execute(text(
            "UPDATE role_permissions SET is_allowed = true "
            "WHERE role = 'admin' AND permission = 'view_settings'"))
        db.commit()

        wieder_frei = client.get("/api/admin/settings", headers=auth_headers)
    finally:
        db.close()

    assert gesperrt.status_code == 403, "der entzogene Haken wirkte nicht"
    assert wieder_frei.status_code == 200, "der gesetzte Haken sperrt aus"


def test_view_settings_gilt_als_durchgesetzt():
    from services.rechte import DURCHGESETZTE_RECHTE

    assert "view_settings" in DURCHGESETZTE_RECHTE
