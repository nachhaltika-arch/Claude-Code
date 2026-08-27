"""Was in der Rechteverwaltung steht, muss auch gelten.

Lücke L-05: Es gibt eine Tabelle `role_permissions`, einen Bildschirm, der sie
bearbeitet, und einen Endpunkt, der sie speichert — **gelesen hat sie zur
Rechtevergabe niemand**. Ein Haken liess sich setzen und wegnehmen, und es
passierte nichts. Das ist die gefährlichste Sorte Fehler: eine Zusicherung,
die nicht gilt. Am 15.08. nachgeprüft und unverändert gefunden, am 18.08.
geschlossen.

Die Regel dahinter ist dieselbe wie bei den drei Zugriffslöchern desselben
Tages: Die Sperre soll nennen, **wer darf** — und zwar an *einer* Stelle,
nicht an dreissig.

Was hier **nicht** behauptet wird: dass jedes Recht der Matrix durchgesetzt
ist. Durchgesetzt sind die, die `DURCHGESETZTE_RECHTE` nennt; die Auskunft
`GET /api/admin/roles` sagt es dem Bildschirm, und der sagt es dem Menschen.
Ein Haken, der nichts tut, ist als solcher gekennzeichnet, statt so zu tun.
"""
import pytest


@pytest.fixture()
def rechte_zuruecksetzen(app):
    """Nach jedem Test wieder die Vorgabe — die Tabelle wirkt jetzt echt."""
    yield
    from database import RolePermission, SessionLocal

    db = SessionLocal()
    try:
        db.query(RolePermission).delete()
        db.commit()
    finally:
        db.close()


def _setze(rolle: str, recht: str, erlaubt: bool):
    from database import RolePermission, SessionLocal

    db = SessionLocal()
    try:
        eintrag = (db.query(RolePermission)
                     .filter(RolePermission.role == rolle,
                             RolePermission.permission == recht)
                     .first())
        if eintrag:
            eintrag.is_allowed = erlaubt
        else:
            db.add(RolePermission(role=rolle, permission=recht, is_allowed=erlaubt))
        db.commit()
    finally:
        db.close()


# ── Der Dienst ────────────────────────────────────────────────────────

def test_ohne_eintrag_gilt_die_vorgabe(app):
    from services.rechte import hat_recht

    assert hat_recht("mitarbeiter", "view_leads") is True
    # Die Gegenprobe stand hier bis zum 27.08.2026 auf der Rolle `nutzer`.
    # Die gibt es nicht mehr; `kunde` ist jetzt die Rolle, die drausen bleibt.
    assert hat_recht("kunde", "view_leads") is False


def test_ein_gesetzter_eintrag_sticht_die_vorgabe(app, rechte_zuruecksetzen):
    from services.rechte import hat_recht

    _setze("mitarbeiter", "view_leads", False)

    assert hat_recht("mitarbeiter", "view_leads") is False


def test_superadmin_darf_immer(app, rechte_zuruecksetzen):
    """Sonst sperrt ein Haken den letzten aus, der ihn wieder setzen könnte."""
    from services.rechte import hat_recht

    _setze("superadmin", "view_leads", False)

    assert hat_recht("superadmin", "view_leads") is True


def test_ein_unbekanntes_recht_ist_keins(app):
    from services.rechte import hat_recht

    assert hat_recht("admin", "die-welt-regieren") is False


# ── Die Wirkung an der Route ──────────────────────────────────────────

def test_der_mitarbeiter_kommt_an_den_bestand(client, mitarbeiter_headers):
    antwort = client.get("/api/leads/", headers=mitarbeiter_headers, follow_redirects=True)

    assert antwort.status_code == 200, antwort.text


def test_nimmt_man_ihm_das_recht_kommt_er_nicht_mehr_dran(
    client, mitarbeiter_headers, rechte_zuruecksetzen
):
    """Der Beweis, dass der Haken etwas tut."""
    _setze("mitarbeiter", "view_leads", False)

    antwort = client.get("/api/leads/", headers=mitarbeiter_headers, follow_redirects=True)

    assert antwort.status_code == 403, antwort.text


def test_dem_admin_kann_man_es_nicht_nehmen(client, auth_headers, rechte_zuruecksetzen):
    """Die Oberflaeche laesst es nicht zu — die Sperre auch nicht."""
    _setze("admin", "view_leads", False)

    antwort = client.get("/api/leads/", headers=auth_headers, follow_redirects=True)

    assert antwort.status_code == 200, antwort.text


# ── Was der Bildschirm wissen muss ────────────────────────────────────

def test_die_auskunft_sagt_welche_rechte_wirklich_gelten(client, auth_headers):
    daten = client.get("/api/admin/roles", headers=auth_headers).json()

    assert "durchgesetzt" in daten, "Der Bildschirm kann Schein nicht von Sein trennen"
    assert "view_leads" in daten["durchgesetzt"]
    # Und es behauptet nichts, was nicht stimmt.
    #
    # **Das Beispiel ist am 22.08.2026 zweimal gewandert** — erst
    # `manage_billing`, dann `manage_projects`, beide sind inzwischen
    # durchgesetzt. Der Test bleibt, das Beispiel wandert; sonst prueft er
    # nur noch, dass irgendetwas fehlt. `view_dashboard` haelt am laengsten,
    # denn es haengt an Routen, die teils ohne Anmeldung erreichbar sind
    # (Widget, Kundenportal). Dort eine Rollenpruefung zu erzwingen waere
    # kein Aufraeumen, sondern eine andere Entscheidung (L-05).
    assert "view_dashboard" not in daten["durchgesetzt"]
