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

    from database import Base, engine, init_db
    Base.metadata.drop_all(bind=engine)
    init_db()

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


def pytest_sessionfinish(session, exitstatus):
    """Tabellen nach dem Lauf entfernen — die Datenbank selbst bleibt bestehen."""
    try:
        from database import Base, engine
        Base.metadata.drop_all(bind=engine)
    except Exception:
        pass
