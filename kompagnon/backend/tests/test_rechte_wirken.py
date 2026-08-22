"""Drei Häkchen, die etwas tun.

L-05, dritter Schritt. Am 18.08. wurde die Rechtematrix lesbar gemacht
(`services/rechte.py`) und der Bildschirm sagt seither, welche Häkchen bloß
beschreibend sind. Durchgesetzt waren **zwei von achtzehn**:
`view_leads` und `view_projects`.

Ein Häkchen, das nichts tut, ist schlimmer als keins: Es sieht aus wie eine
Sperre, und jemand verlässt sich darauf.

Dieser Schritt nimmt die drei dazu, bei denen das am meisten wiegt — die, mit
denen etwas Unwiderrufliches passiert:

    delete_leads             Betriebe löschen
    manage_users            Konten anlegen, ändern, löschen, Passwort zurücksetzen
    manage_settings         Systemeinstellungen aendern

**Zwei bleiben bewusst außen vor:** `deploy_kas_pages` und
`manage_system_settings`. Beide hat per Vorgabe **nur** der Superadmin — dem
Admin gibt die Vorgabe sie ausdrücklich nicht („Admin darf bearbeiten aber
nicht deployen"). Sie durchzusetzen wäre keine Absicherung, sondern eine
Verhaltensänderung: Sie nähme dem, der heute deployt und die Rechtematrix
pflegt, genau das weg. Das ist eine Entscheidung und keine Reparatur.

Geprüft wird mit dem **Auditor**: Ihm fehlen alle drei per Vorgabe, und er ist
kein Kunde — die Sperre muss also am Recht hängen und nicht an der Rolle.
"""
import pytest
from sqlalchemy import text

GESPERRT = 403


ZU_SPERREN = (
    # Eine Nummer, die es nicht gibt: Der Test fragt nach der Berechtigung,
    # nicht nach dem Loeschen — und ein Test, der Bestand vernichtet, ist
    # ein schlechter Test.
    ("delete", "/api/leads/999999", "delete_leads"),
    ("post", "/api/admin/users", "manage_users"),
    ("patch", "/api/admin/users/1", "manage_users"),
    # **Eine Kennung, die niemandem gehoert (22.08.2026).** Hier stand `1`,
    # und `test_mit_dem_recht_geht_es_weiter` fuehrt den Aufruf wirklich aus:
    # Der Admin **loeschte** damit Nutzer 1. Solange das zufaellig ein
    # unwichtiges Konto war, fiel es nicht auf — sobald die Nummer den
    # session-weiten Testkunden traf, brach jeder folgende Test, der ihn
    # braucht, mit **401** statt mit seiner eigenen Aussage.
    #
    # Geprueft wird hier die **Sperre**, nicht die Loeschung: „nur 403 darf es
    # nicht sein". Eine Kennung, die es nicht gibt, sagt 404 und zerstoert
    # nichts.
    ("delete", "/api/admin/users/99999999", "manage_users"),
    ("post", "/api/admin/users/99999999/reset-password", "manage_users"),
    ("patch", "/api/admin/settings", "manage_settings"),
)


@pytest.mark.parametrize("methode,pfad,recht", ZU_SPERREN)
def test_ohne_das_recht_geht_es_nicht(client, auditor_headers, methode, pfad, recht):
    """Der Auditor darf das nicht — und zwar, weil ihm das Recht fehlt."""
    # Act
    aufruf = getattr(client, methode)
    antwort = (aufruf(pfad, headers=auditor_headers) if methode == "delete"
               else aufruf(pfad, json={}, headers=auditor_headers))

    # Assert
    assert antwort.status_code == GESPERRT, (
        f"{methode.upper()} {pfad} -> {antwort.status_code}: "
        f"`{recht}` ist ein Häkchen ohne Wirkung."
    )


@pytest.mark.parametrize("methode,pfad,recht", ZU_SPERREN)
def test_mit_dem_recht_geht_es_weiter(client, auth_headers, methode, pfad, recht):
    """Die Sperre darf den nicht mitnehmen, der das Recht hat.

    Der Admin trägt alle drei per Vorgabe. Ob der Aufruf danach 404 oder 422
    sagt, ist gleichgültig — nur 403 darf es nicht sein.
    """
    # Act
    aufruf = getattr(client, methode)
    antwort = (aufruf(pfad, headers=auth_headers) if methode == "delete"
               else aufruf(pfad, json={}, headers=auth_headers))

    # Assert
    assert antwort.status_code != GESPERRT, (
        f"{methode.upper()} {pfad} -> 403: Dem Admin fehlt `{recht}`, "
        "obwohl die Vorgabe es ihm gibt."
    )


# ── Der Bildschirm darf nicht wieder lügen ────────────────────────────

@pytest.mark.parametrize("recht", [
    "delete_leads", "manage_users", "manage_settings",
])
def test_das_durchgesetzte_recht_steht_auch_in_der_liste(recht):
    """Sonst kennzeichnet der Rollen-Bildschirm es weiter als wirkungslos.

    `DURCHGESETZTE_RECHTE` ist die einzige Stelle, an der der Bildschirm
    erfährt, was wirkt. Wer eine Sperre einbaut und den Eintrag vergisst,
    stellt genau den Zustand wieder her, den der 18.08. beseitigt hat — nur
    andersherum.
    """
    from services.rechte import DURCHGESETZTE_RECHTE

    assert recht in DURCHGESETZTE_RECHTE


@pytest.mark.parametrize("recht", ["view_dashboard", "download_pdf",
                                   "view_audits", "create_audits"])
def test_was_an_teils_oeffentlichen_routen_haengt_bleibt_unwirksam(recht):
    """Auslassungen mit Grund, damit sie nicht als Versehen gelesen werden.

    Alle vier haengen an Routen, die teils **ohne Anmeldung** erreichbar sind
    — das Widget, das Kundenportal, `POST /api/audit/start` mit Mengengrenze
    statt Rollenpruefung. Ein Recht dort durchzusetzen hiesse, eine
    Rollenpruefung an eine Stelle zu haengen, die bewusst keine hat. Das
    gehoert eigens gemessen, nicht nebenbei verdrahtet.

    **Der Test hat am 22.08.2026 seinen Gegenstand gewechselt.** Vorher
    standen hier `deploy_kas_pages` und `manage_system_settings` — beide sind
    seitdem entschieden und durchgesetzt (L-05). Der Test bleibt, das
    Beispiel wandert; sonst prueft er nur noch, dass irgendetwas fehlt.
    """
    from services.rechte import DURCHGESETZTE_RECHTE

    assert recht not in DURCHGESETZTE_RECHTE


# ── Nebenbefund beim Verdrahten ───────────────────────────────────────

@pytest.fixture
def betrieb_mit_zugang(app):
    """Ein **eigener** Betrieb samt Kundenkonto — nur fuer diesen Test.

    **Warum nicht `kunde_user`.** Bis zum 22.08.2026 loeschte dieser Test den
    Betrieb des session-weiten Testkunden. Solange die Route mit 409
    antwortet, faellt das nicht auf — nichts wird geloescht. Sobald sie aus
    irgendeinem Grund durchlaesst, ist der geteilte Kunde weg, und **jeder
    folgende Test**, der ihn braucht, scheitert an einer 401 statt an seiner
    eigenen Aussage. Genau das trat im Gesamtlauf ein und kostete die Suche
    nach einer Ursache, die es gar nicht gab: Der Fehler war nicht, dass der
    Zugang fehlte, sondern dass dieser Test fremden Bestand anfasst.

    Ein Test, der geteilten Zustand loescht, ist eine Falle mit
    Zeitzuender.
    """
    from auth import hash_password
    from database import Lead, SessionLocal, User

    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM users WHERE email = 'l56-zugang@example.com'"))
        db.execute(text("DELETE FROM leads WHERE company_name = 'L56 Mit Zugang'"))
        db.commit()

        lead = Lead(company_name="L56 Mit Zugang", email="l56-zugang@example.com")
        db.add(lead)
        db.commit()
        db.refresh(lead)

        db.add(User(email="l56-zugang@example.com",
                    password_hash=hash_password("egal"),
                    role="kunde", is_active=True, lead_id=lead.id))
        db.commit()
        kennung = lead.id
    finally:
        db.close()

    yield kennung

    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM users WHERE email = 'l56-zugang@example.com'"))
        db.execute(text("DELETE FROM leads WHERE company_name = 'L56 Mit Zugang'"))
        db.commit()
    finally:
        db.close()


def test_ein_betrieb_mit_kundenzugang_sagt_was_im_weg_steht(
        client, auth_headers, betrieb_mit_zugang):
    """Vorher: 500 mit einer Fremdschlüsselmeldung, aus der niemand schließen
    kann, was zu tun ist.

    Der Zugang wird bewusst **nicht** mitgelöscht — ob das Löschen eines
    Betriebs das Konto seines Kunden mitnimmt, ist eine
    Datenschutz-Entscheidung (L-56). Bis sie gefallen ist, sagt der Endpunkt
    wenigstens, was im Weg steht.
    """
    # Act
    antwort = client.delete(f"/api/leads/{betrieb_mit_zugang}", headers=auth_headers)

    # Assert
    assert antwort.status_code == 409, f"-> {antwort.status_code}: {antwort.text[:120]}"
    assert "Kundenzugang" in antwort.json()["detail"]
