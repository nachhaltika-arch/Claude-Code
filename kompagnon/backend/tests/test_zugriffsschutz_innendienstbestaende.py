"""Verkaufschancen, Kampagnen und Newsletter sind Innendienst (L-67).

**Die Frage von L-67 ist nicht die von L-51.** Dort wurde gezählt, was
**ohne** Anmeldung antwortet. Hier geht es um die Stufe danach: Wer
angemeldet ist, darf deshalb noch lange nicht alles — und **Kunden haben
Konten**. L-66 war ein bewiesener Fall aus diesem Bestand, nicht der einzige
seiner Art, nur der erste, den jemand nachgesehen hat.

**Am 22.08.2026 nachgemessen:** 120 Routen tragen nur `require_any_auth`,
`get_current_user` oder `optional_auth`. Ein Teil davon ist richtig so —
`/api/portal/*` ist der Kundenweg, `/api/auth/2fa/*` sind eigene Daten. Diese
drei Router sind es nicht:

    deals        7 Routen   Verkaufschancen mit Betrag und Betriebsbezug
    campaigns    7 Routen   Kampagnen, Empfängerkreise, Auswertung
    newsletter   9 Routen   Empfängerlisten und Versandverläufe

**Vor dem Sperren gemessen, wer sie aufruft** — das ist die Vorgabe aus L-67,
je Router zu entscheiden statt pauschal zu sperren. Ergebnis: ausschließlich
Innendienst-Bildschirme (`Dashboard`, `LeadProfile`, `Deals`,
`CampaignManager`, `Newsletter`). **Kein einziger Pfad unter
`pages/customer/`.** Die Sperre nimmt also niemandem etwas weg, das er
benutzt — anders als eine Pauschalsperre, die das Kundenportal ausgesperrt
hätte.

Gesetzt wird sie am **Router**, nicht je Route: Sonst ist die nächste Route,
die jemand hinzufügt, wieder offen — genau die Bauart, die am 19.08. 55
offene Werkzeug-Routen erzeugt hat (L-51).
"""
import pytest


#: Nur die drei Tabellen, die diese Proben lesen.
#:
#: **Nicht `_run_migrations()`**, obwohl das der dokumentierte Weg fuer
#: fehlende Spalten ist: Der Lauf legt rund vierzig Tabellen ausserhalb von
#: `Base.metadata` an, und am `drop_all()` der `app`-Fixture scheitert danach
#: der **naechste** Testlauf an deren Fremdschluesseln
#: (`courses_created_by_fkey` auf `users`). Am 22.08.2026 einmal
#: heruntergerissen und wieder aufgebaut — hier reicht das Notwendige.
TABELLEN = (
    """CREATE TABLE IF NOT EXISTS deals (
        id SERIAL PRIMARY KEY, title VARCHAR(255), company_id INTEGER,
        lead_id INTEGER, value NUMERIC, currency VARCHAR(8) DEFAULT 'EUR',
        status VARCHAR(40) DEFAULT 'open', stage VARCHAR(40),
        probability INTEGER, expected_close DATE, owner_id INTEGER,
        notes TEXT, created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW())""",
    """CREATE TABLE IF NOT EXISTS campaigns (
        id SERIAL PRIMARY KEY, name VARCHAR(255), slug VARCHAR(255),
        status VARCHAR(40) DEFAULT 'draft', channel VARCHAR(40),
        budget NUMERIC, started_at TIMESTAMP, ended_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT NOW())""",
    """CREATE TABLE IF NOT EXISTS newsletter_lists (
        id SERIAL PRIMARY KEY, name VARCHAR(255), description TEXT,
        brevo_list_id INTEGER, source VARCHAR(60),
        created_at TIMESTAMP DEFAULT NOW())""",
    # Die Kampagnenliste verbindet auf `leads.kampagne_id` — auch das eine
    # Spalte, die erst beim Serverstart entsteht.
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS kampagne_id INTEGER",
    "ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP",
    """CREATE TABLE IF NOT EXISTS newsletter_contacts (
        id SERIAL PRIMARY KEY, list_id INTEGER, email VARCHAR(255),
        first_name VARCHAR(120), last_name VARCHAR(120),
        status VARCHAR(40) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT NOW())""",
)


@pytest.fixture(scope="module", autouse=True)
def _tabellen(app):
    """Die drei Bestaende entstehen sonst erst beim Serverstart."""
    from sqlalchemy import text
    from database import SessionLocal

    db = SessionLocal()
    try:
        for sql in TABELLEN:
            db.execute(text(sql))
        db.commit()
    finally:
        db.close()


#: Je Router eine lesende Route, die es ohne Vorbedingung gibt.
PROBEN = [
    ("deals", "/api/deals"),
    ("campaigns", "/api/campaigns"),
    ("newsletter", "/api/newsletter/lists"),
]


@pytest.mark.parametrize("modul,pfad", PROBEN, ids=[m for m, _ in PROBEN])
def test_der_kunde_kommt_nicht_heran(client, kunde_headers, modul, pfad):
    antwort = client.get(pfad, headers=kunde_headers)

    assert antwort.status_code == 403, (
        f"{pfad} liess einen Kunden durch ({antwort.status_code}). "
        f"Der Router {modul} traegt keine Innendienst-Sperre.")


@pytest.mark.parametrize("modul,pfad", PROBEN, ids=[m for m, _ in PROBEN])
def test_ohne_anmeldung_erst_recht_nicht(client, modul, pfad):
    antwort = client.get(pfad)

    assert antwort.status_code in (401, 403), antwort.text[:160]


@pytest.mark.parametrize("modul,pfad", PROBEN, ids=[m for m, _ in PROBEN])
def test_der_innendienst_kommt_weiterhin_durch(client, auth_headers, modul, pfad):
    """Die Sperre darf dem Innendienst nichts wegnehmen — sonst ist sie
    keine Absicherung, sondern ein Ausfall.

    Geprueft wird **nicht 403**, nicht „erfolgreich": Einige dieser Abfragen
    verbinden ueber Tabellen und Spalten, die erst der Serverstart anlegt und
    die Testeinrichtung bewusst auslaesst. An denen darf die Abfrage hier
    scheitern — an der Berechtigung nicht. Der Unterschied ist genau das,
    was diese Aenderung angefasst hat.
    """
    antwort = client.get(pfad, headers=auth_headers)

    assert antwort.status_code != 403, (
        f"{pfad} weist den Innendienst ab — die Sperre nimmt ihm etwas weg. "
        f"{antwort.text[:160]}")


def test_die_sperre_haengt_am_router_und_nicht_an_einzelnen_routen():
    """Sonst ist die nächste hinzugefügte Route wieder offen.

    Genau diese Bauart hat am 19.08.2026 die 55 offenen Werkzeug-Routen
    erzeugt (L-51): Jede Route trug ihre Sperre selbst, und wer eine neue
    schrieb, vergass sie.
    """
    from routers import campaigns, deals, newsletter

    for modul in (deals, campaigns, newsletter):
        namen = {
            getattr(d.dependency, "__name__", "")
            for d in (modul.router.dependencies or [])
        }
        assert "require_innendienst" in namen, (
            f"{modul.__name__} traegt die Sperre nicht am Router: {namen}")
