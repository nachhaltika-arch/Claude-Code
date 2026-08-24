"""
Gemeinsame Fixtures fuer die Backend-Tests.

Die Tests laufen gegen eine eigene Postgres-Datenbank — nicht gegen SQLite:
das Datenmodell nutzt Postgres-Typen (JSONB), die SQLite nicht kennt. Lokal
ist das `kompagnon_test` auf localhost, in der CI der Postgres-Service-Container.

Sicherung: Der Datenbankname MUSS 'test' enthalten. Ohne diese Bedingung
bricht die Testsammlung ab, damit ein falsch gesetztes DATABASE_URL niemals
echte Daten loeschen kann.

Der TestClient wird bewusst OHNE Kontextmanager erzeugt: dadurch laeuft der
Lifespan (Migrationen, Scheduler, Seeds) nicht mit. Die Tests pruefen Routen
und Geschaeftslogik, nicht den Startvorgang — und bleiben so in Sekunden fertig.
"""
import os
import pathlib
import sys

import pytest

BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

DEFAULT_TEST_DB = "postgresql://localhost:5432/kompagnon_test"
DATABASE_URL = os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DB)

if "test" not in DATABASE_URL.rsplit("/", 1)[-1].lower():
    raise RuntimeError(
        f"Der Datenbankname in {DATABASE_URL!r} enthaelt kein 'test'. "
        "Abbruch — die Tests loeschen Tabellen und duerfen nur gegen eine "
        "Testdatenbank laufen."
    )

os.environ.update({
    "DATABASE_URL": DATABASE_URL,
    "SECRET_KEY": "test-secret-key-not-for-production",
    "ENVIRONMENT": "development",
    "USE_MOCK_EMAIL": "true",
    "ANTHROPIC_API_KEY": "",
    "STRIPE_SECRET_KEY": "",
    "FRONTEND_URL": "http://localhost:3000",
})


def _ensure_database_exists():
    """Legt die Testdatenbank an, falls sie noch nicht existiert."""
    import psycopg2
    from psycopg2 import sql
    from urllib.parse import urlparse

    parsed = urlparse(DATABASE_URL)
    db_name = parsed.path.lstrip("/")

    try:
        psycopg2.connect(DATABASE_URL).close()
        return
    except psycopg2.OperationalError as exc:
        if "does not exist" not in str(exc):
            raise

    admin_dsn = DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
    conn = psycopg2.connect(admin_dsn)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
    conn.close()

ADMIN_EMAIL = "pytest-admin@kompagnon.local"
ADMIN_PASSWORD = "pytest-admin-passwort"

# Das alte integration_test.py ist ein Print-Skript ohne Assertions und laeuft
# gegen echte KI-Agenten. Es wird nicht mit eingesammelt.
collect_ignore = ["integration_test.py"]


@pytest.fixture(scope="session")
def app():
    """Die FastAPI-App mit frisch angelegtem Schema."""
    _ensure_database_exists()

    from sqlalchemy import text
    from database import Base, engine, init_db

    # **Das ganze Schema verwerfen, nicht nur die Modelltabellen.**
    # `Base.metadata.drop_all` kennt nur, wofuer es ein Modell gibt — und
    # scheitert, sobald eine migrationserzeugte Tabelle einen Fremdschluessel
    # darauf haelt (`website_versions` → `projects`). Beim ersten Lauf faellt
    # das nicht auf, weil es die Tabelle noch nicht gibt; beim zweiten bricht
    # der Aufbau ab. Der Schutz oben stellt sicher, dass „test" im Namen steht.
    with engine.begin() as verbindung:
        verbindung.execute(text("DROP SCHEMA public CASCADE"))
        verbindung.execute(text("CREATE SCHEMA public"))

    init_db()

    # **Auch den Migrationsblock fahren.** `init_db` legt nur an, wofuer es ein
    # SQLAlchemy-Modell gibt. Tabellen, die ausschliesslich in
    # `migrations_runtime.py` als CREATE TABLE stehen — `support_tickets` etwa —
    # entstehen dadurch **nie**, und jeder Test, der sie anfasst, scheitert an
    # „relation does not exist".
    #
    # Bis zum 23.08.2026 half sich jeder solche Test selbst: Ein Test legte die
    # Tabelle **wortgetreu abgeschrieben** in einer eigenen Fixture an. Das ging
    # so lange gut, bis ein zweiter Test dieselbe Tabelle brauchte — dann fiel
    # er in der CI um, waehrend er lokal gruen war, weil die Entwicklungs-
    # datenbank sie noch aus einem frueheren echten Start trug.
    #
    # Produktiv laeuft dieser Block bei jedem Start. Die Testdatenbank soll
    # dasselbe Schema haben wie die Produktivdatenbank — sonst prueft sie etwas
    # anderes, als draussen laeuft.
    from migrations_runtime import run_migrations
    run_migrations()

    import main
    return main.app


@pytest.fixture(scope="session")
def client(app):
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture(scope="session")
def admin_user(app):
    """Ein Admin-Konto zum Anmelden. Wird einmal pro Testlauf angelegt."""
    from auth import hash_password
    from database import SessionLocal, User

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if existing:
            return existing

        user = User(
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            first_name="Pytest",
            last_name="Admin",
            role="admin",
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


@pytest.fixture(scope="session")
def auth_headers(client, admin_user):
    """Authorization-Header eines angemeldeten Admins."""
    response = client.post(
        "/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 200, f"Login fehlgeschlagen: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


AUDITOR_EMAIL = "pytest-auditor@kompagnon.local"
AUDITOR_PASSWORT = "pytest-auditor-passwort"


@pytest.fixture(scope="session")
def auditor_headers(client, app):
    """Ein Auditor — die Rolle, an der sich zeigt, ob Rechte wirken.

    Sie steht zwischen Innendienst und Kunde: laut Rechtematrix darf sie
    Betriebe sehen, aber keine loeschen und keine Benutzer verwalten.
    """
    from auth import hash_password
    from database import SessionLocal, User

    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == AUDITOR_EMAIL).first():
            db.add(User(
                email=AUDITOR_EMAIL,
                password_hash=hash_password(AUDITOR_PASSWORT),
                first_name="Pytest", last_name="Auditor",
                role="auditor", is_active=True, is_verified=True,
            ))
            db.commit()
    finally:
        db.close()

    antwort = client.post("/api/auth/login",
                          json={"email": AUDITOR_EMAIL, "password": AUDITOR_PASSWORT})
    assert antwort.status_code == 200, antwort.text
    return {"Authorization": f"Bearer {antwort.json()['access_token']}"}


KUNDE_EMAIL = "pytest-kunde@example.com"
KUNDE_PASSWORD = "Pytest-Kunde-2026!"


@pytest.fixture(scope="session")
def kunde_user(app):
    """Ein Kundenkonto samt eigenem Betrieb.

    Gebraucht für die Rollentrennung: Ein Kunde ist angemeldet, darf aber
    nur den eigenen Betrieb sehen — nicht den Bestand.
    """
    from auth import hash_password
    from database import SessionLocal, User, Lead

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == KUNDE_EMAIL).first()
        if existing:
            return existing

        eigener_betrieb = Lead(company_name="Pytest Kundenbetrieb", email=KUNDE_EMAIL)
        db.add(eigener_betrieb)
        db.commit()
        db.refresh(eigener_betrieb)

        user = User(
            email=KUNDE_EMAIL,
            password_hash=hash_password(KUNDE_PASSWORD),
            first_name="Pytest",
            last_name="Kunde",
            role="kunde",
            lead_id=eigener_betrieb.id,
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


@pytest.fixture(scope="session")
def kunde_headers(client, kunde_user):
    """Authorization-Header eines angemeldeten Kunden."""
    response = client.post(
        "/api/auth/login",
        json={"email": KUNDE_EMAIL, "password": KUNDE_PASSWORD},
    )
    assert response.status_code == 200, f"Login fehlgeschlagen: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def fremder_betrieb(app, kunde_user):
    """Ein Betrieb, der dem Kunden nicht gehört."""
    from database import SessionLocal, Lead

    db = SessionLocal()
    try:
        vorhanden = (db.query(Lead)
                       .filter(Lead.company_name == "Pytest Fremdbetrieb").first())
        if vorhanden:
            return vorhanden.id
        lead = Lead(company_name="Pytest Fremdbetrieb", email="fremd@example.com")
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead.id
    finally:
        db.close()


def pytest_sessionfinish(session, exitstatus):
    """Tabellen nach dem Lauf entfernen — die Datenbank selbst bleibt bestehen."""
    try:
        from database import Base, engine
        Base.metadata.drop_all(bind=engine)
    except Exception:
        pass


# **Aus `test_widget.py` hierher am 23.08.2026 (L-25).** Die Datei hatte 901
# Zeilen und ist in drei geteilt; alle drei brauchen diese Fixture. Sie hier zu
# fuehren ist der pytest-uebliche Weg und besser als drei Kopien — genau die
# Sorte Duplikat, die anderswo heute schon einen Fehler verdeckt hat.
#
# Sie ist **nicht** `autouse`: Wer sie nicht anfordert, merkt nichts von ihr.
@pytest.fixture
def aufraeumen():
    """Entfernt die in einem Test angelegten Anfragen wieder."""
    # **Erst hier importieren, nicht oben.** `conftest.py` setzt weiter
    # oben `DATABASE_URL` auf die Testdatenbank; ein Modulimport von
    # `database` liefe davor und traefe die falsche.
    from database import SessionLocal, WidgetRequest
    angelegte = []
    yield angelegte
    db = SessionLocal()
    try:
        db.query(WidgetRequest).filter(WidgetRequest.email.in_(angelegte)).delete(
            synchronize_session=False)
        db.commit()
    finally:
        db.close()


# Ebenfalls geteilt von allen drei Widget-Dateien (L-25, 23.08.2026):
# `fremde_analyse` legt eine Anfrage samt Audit an, `gesendete_mails` faengt
# den Versand ab. Beide werden von je zwei Dateien gebraucht — in der einen zu
# lassen und in der anderen zu wiederholen waere die schlechtere Haelfte.
@pytest.fixture
def fremde_analyse():
    """Eine Analyse, wie sie im Tool über die Lead-Akquise entsteht.

    Sie gehört zu keiner Widget-Anfrage — niemand von außen darf sie sehen.
    """
    from database import AuditResult, SessionLocal, WidgetRequest

    db = SessionLocal()
    try:
        audit = AuditResult(
            website_url="https://interner-interessent.example",
            company_name="Interner Interessent",
            status="completed",
            total_score=41,
            level="Homepage Standard Bronze",
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)
        audit_id = audit.id
    finally:
        db.close()

    yield audit_id

    db = SessionLocal()
    try:
        db.query(AuditResult).filter(AuditResult.id == audit_id).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def gesendete_mails(monkeypatch):
    """Fängt den Versand ab, statt echte Post zu verschicken."""
    from routers import widget
    briefe = []

    def _abfangen(to_email, subject, html_body, **kwargs):
        briefe.append({"an": to_email, "betreff": subject, "html": html_body})
        return True

    import services.email
    monkeypatch.setattr(services.email, "send_email", _abfangen)
    return briefe


def pytest_addoption(parser):
    """`--grundlage-neu` schreibt abgelegte Vergleichsgrundlagen neu (L-25).

    Bewusst ein ausdruecklicher Schalter und keine Selbstheilung: Eine
    Grundlage, die sich beim ersten roten Lauf selbst ueberschreibt, haelt
    gar nichts fest.
    """
    parser.addoption(
        "--grundlage-neu", action="store_true", default=False,
        help="Abgelegte Vergleichsgrundlagen neu schreiben (siehe L-25).",
    )
