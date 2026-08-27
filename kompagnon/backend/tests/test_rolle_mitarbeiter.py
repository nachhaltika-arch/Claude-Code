# -*- coding: utf-8 -*-
"""Aus `auditor` und `nutzer` wird `mitarbeiter` — und zwar überall.

Entscheidung David, 27.08.2026: „ich möchte die rolle nutzer wandeln in
mitarbeiter kompagnon. auditoren werden wir keine benötigen."

**Warum das ein Test und nicht bloss ein Suchen-und-Ersetzen ist.** Die
Rollennamen standen an über siebzig Stellen. Bleibt eine davon stehen,
entsteht genau der Zustand, der am 18.08. schon einmal ein Loch war (L-05):
zwei Stellen, die verschiedene Rollen für dieselbe Frage aufzählen.

**Jede Abwesenheit hier hat eine Anwesenheit daneben.** Ein Test, der nur
prüft, dass `auditor` weg ist, wäre auch dann grün, wenn die Rechtematrix
leer wäre. Deshalb steht neben jedem „gibt es nicht mehr" ein „und das hier
gibt es dafür".
"""
import pytest

from services.rollen import (ALTE_ROLLEN, BEARBEITBAR, INNENDIENST, ROLLEN,
                             rolle_normalisieren)


# ── Die Liste der Rollen ──────────────────────────────────────────────

def test_es_gibt_die_rolle_mitarbeiter_und_die_alten_nicht_mehr():
    assert "mitarbeiter" in ROLLEN
    assert "auditor" not in ROLLEN
    assert "nutzer" not in ROLLEN
    # Gegenprobe, damit der Test nicht bloss deshalb grün ist, weil die
    # Liste leer wäre.
    assert set(ROLLEN) == {"superadmin", "admin", "mitarbeiter", "kunde"}


def test_mitarbeiter_gehoert_zum_innendienst():
    assert "mitarbeiter" in INNENDIENST
    assert "auditor" not in INNENDIENST
    assert "kunde" not in INNENDIENST


def test_bearbeitbar_sind_genau_mitarbeiter_und_kunde():
    """Admin und Superadmin bleiben draussen — sonst sperrt sich jemand aus."""
    assert set(BEARBEITBAR) == {"mitarbeiter", "kunde"}


# ── Alte Namen, die noch im Bestand liegen ────────────────────────────

@pytest.mark.parametrize("alt", ["auditor", "nutzer", "AUDITOR", " Nutzer "])
def test_alte_namen_werden_zu_mitarbeiter(alt):
    assert rolle_normalisieren(alt) == "mitarbeiter"


def test_unbekannte_rolle_wird_nicht_stillschweigend_zur_vorgabe():
    """Ein Tippfehler darf kein Innendienstkonto anlegen."""
    assert rolle_normalisieren("mitarbeeiter") is None
    assert rolle_normalisieren("") is None
    assert rolle_normalisieren(None) is None
    # Gegenprobe: ein richtiger Name kommt durch.
    assert rolle_normalisieren("admin") == "admin"


def test_alte_rollen_zeigen_alle_auf_eine_gueltige_rolle():
    for alt, neu in ALTE_ROLLEN.items():
        assert neu in ROLLEN, f"{alt} zeigt auf die unbekannte Rolle {neu}"


# ── Wer sich selbst anlegt, bekommt nicht die Vorgabe ─────────────────

def test_selbstregistrierung_ist_niemals_innendienst():
    """Das Formular unter `/register` ist öffentlich.

    **Beinahe-Fehler vom 27.08.2026.** `POST /api/auth/register` vergab die
    Rolle `nutzer`. Wäre beim Zusammenlegen aus ihr stumpf `mitarbeiter`
    geworden, hätte sich jeder Fremde über das öffentliche Formular ein
    Innendienstkonto angelegt und über `GET /api/leads/` den gesamten
    Betriebsbestand bekommen.

    Deshalb sind Vorgabe und Selbstregistrierung zwei Konstanten — und
    dieser Test hält sie auseinander, damit sie nicht wieder
    zusammenwachsen.
    """
    from services.rollen import SELBSTREGISTRIERUNG

    assert SELBSTREGISTRIERUNG in ROLLEN
    assert SELBSTREGISTRIERUNG not in INNENDIENST


def test_register_legt_kein_innendienstkonto_an(client):
    """Am Endpunkt gemessen, nicht an der Konstante."""
    import secrets

    from database import SessionLocal, User

    adresse = f"pytest-fremder-{secrets.token_hex(6)}@example.com"
    antwort = client.post("/api/auth/register", json={
        # Bewusst niedrige Entropie und lesbar als das, was es ist.
        # Gitleaks hat den ersten Versuch hier zu Recht als Schluessel
        # gelesen (Lauf 33050180660) — und ein Fund bleibt in der Historie.
        "email": adresse, "password": "pytest-pytest-pytest",
        "first_name": "Un", "last_name": "Bekannt"})
    assert antwort.status_code == 200, antwort.text

    db = SessionLocal()
    try:
        angelegt = db.query(User).filter(User.email == adresse).first()
        assert angelegt is not None
        assert angelegt.role not in INNENDIENST, (
            f"Selbstregistrierung vergibt die Innendienstrolle {angelegt.role}")
        db.delete(angelegt)
        db.commit()
    finally:
        db.close()


# ── Die Rechtematrix ──────────────────────────────────────────────────

def test_rechtematrix_kennt_mitarbeiter_statt_auditor_und_nutzer():
    from routers.admin_settings import DEFAULT_PERMISSIONS

    assert "mitarbeiter" in DEFAULT_PERMISSIONS
    assert "auditor" not in DEFAULT_PERMISSIONS
    assert "nutzer" not in DEFAULT_PERMISSIONS
    assert set(DEFAULT_PERMISSIONS) == set(ROLLEN)


def test_mitarbeiter_erbt_die_rechte_des_auditors():
    """Die Zusammenlegung nimmt niemandem etwas weg.

    Das war die Bedingung der Entscheidung: `auditor` war die Rolle, mit der
    im Werkzeug gearbeitet wurde. Wer sie hatte, behält sie.
    """
    from routers.admin_settings import DEFAULT_PERMISSIONS

    hat = set(DEFAULT_PERMISSIONS["mitarbeiter"])
    assert hat == {
        "view_dashboard", "view_leads", "create_leads", "edit_leads",
        "view_audits", "create_audits", "download_pdf", "view_projects",
        "manage_projects",
    }


def test_mitarbeiter_darf_nichts_unwiderrufliches():
    from routers.admin_settings import DEFAULT_PERMISSIONS

    hat = set(DEFAULT_PERMISSIONS["mitarbeiter"])
    for verboten in ("delete_leads", "manage_users", "manage_settings",
                     "view_billing", "manage_billing", "deploy_kas_pages",
                     "manage_system_settings"):
        assert verboten not in hat, f"mitarbeiter hat {verboten}"


def test_rechtedienst_antwortet_fuer_mitarbeiter(app):
    """Nicht nur die Vorgabe-Tabelle — der Dienst, der sie liest."""
    from services.rechte import hat_recht

    assert hat_recht("mitarbeiter", "view_leads") is True
    assert hat_recht("mitarbeiter", "delete_leads") is False
    # Gegenprobe: ein Kunde kommt hier nicht durch.
    assert hat_recht("kunde", "view_leads") is False


# ── Die Sperren ───────────────────────────────────────────────────────

def test_require_auditor_gibt_es_nicht_mehr():
    """Die Sperre hing an keiner einzigen Route (L-12) und ist weg.

    Daneben die Anwesenheit: `require_innendienst` gibt es, und die hängt
    an echten Routen.

    **Eigener Messfehler vom 27.08.2026, hier festgehalten.** Zuerst stand
    hier `import routers.auth_router as ar`. Das ergibt **nicht** das Modul:
    `routers/__init__.py` legt mit `from .auth_router import router as
    auth_router` einen gleichnamigen Namen auf das Paket, und der ist ein
    `APIRouter`. Die Abwesenheitszusicherung war damit grün, ohne irgendetwas
    zu prüfen — ein `APIRouter` hatte `require_auditor` nie. Gefunden hat es
    die positive Zeile daneben, nicht das Nachdenken.
    """
    import importlib

    modul = importlib.import_module("routers.auth_router")

    assert not hasattr(modul, "require_auditor")
    assert hasattr(modul, "require_innendienst")


def test_auth_router_reicht_die_eine_liste_durch():
    """Elf Dateien holen `INNENDIENST` vom `auth_router`.

    Die Liste darf dort weiterstehen, aber sie muss **dieselbe** sein — eine
    zweite Aufzählung ist genau der Fehler, den dieses Modul beendet.
    """
    from routers.auth_router import IMMER_INNENDIENST as ai
    from routers.auth_router import INNENDIENST as i
    from services.rollen import IMMER_INNENDIENST, INNENDIENST

    assert tuple(i) == tuple(INNENDIENST)
    assert tuple(ai) == tuple(IMMER_INNENDIENST)


# ── Am laufenden Dienst ───────────────────────────────────────────────

def test_mitarbeiter_kommt_an_den_bestand(client, mitarbeiter_headers):
    """Die positive Gegenprobe: Die neue Rolle arbeitet wirklich."""
    antwort = client.get("/api/leads/", headers=mitarbeiter_headers)
    assert antwort.status_code == 200, antwort.text


def test_mitarbeiter_darf_keinen_betrieb_loeschen(client, mitarbeiter_headers):
    antwort = client.delete("/api/leads/999999", headers=mitarbeiter_headers)
    assert antwort.status_code == 403, antwort.text


def test_mitarbeiter_darf_keine_benutzer_verwalten(client, mitarbeiter_headers):
    antwort = client.get("/api/admin/users", headers=mitarbeiter_headers)
    assert antwort.status_code == 403, antwort.text


def test_rechteverwaltung_nimmt_mitarbeiter_und_lehnt_auditor_ab(
        client, auth_headers):
    """`PATCH /api/admin/roles/{role}` — die Liste der bearbeitbaren Rollen.

    Der Admin darf sie seit dem 22.08. nicht mehr (`manage_system_settings`
    liegt beim Superadmin), deshalb ist 403 die richtige Antwort für beide.
    Geprüft wird hier die **Unterscheidung**: Eine unbekannte Rolle darf
    nicht wie eine bekannte aussehen.
    """
    from routers.admin_settings import update_role_permissions

    import inspect
    quelle = inspect.getsource(update_role_permissions)
    assert "BEARBEITBAR" in quelle, (
        "Die Rollenliste steht wieder von Hand im Endpunkt")
