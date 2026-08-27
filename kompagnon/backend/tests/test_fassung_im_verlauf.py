"""Die Audit-Liste eines Betriebs nennt die Fassung des Standards (S6.2).

Das Buch sagt in 2.7 zu, jedes Ergebnis nenne den Maßstab, gegen den es
entstanden ist. Gemessen am 24.08.2026 stimmte das nicht: Die Spalte
`standard_version` wird seit der Fassung 2026.2 geschrieben, aber weder von
`/api/leads/{id}/audits` ausgeliefert noch irgendwo angezeigt.

Ohne die Angabe rechnet der Verlauf aus dem aeltesten und dem neuesten
Ergebnis eine „Verbesserung" — auch dann, wenn dazwischen der Katalog
gewechselt hat. Das ist kein Fortschritt, sondern ein Massstabswechsel.
"""
from services.audit_scoring import STANDARD_VERSION


def test_die_liste_liefert_die_fassung_mit(client, app, auth_headers):
    # Arrange
    from database import AuditResult, Lead, SessionLocal
    from sqlalchemy import text

    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM leads WHERE email = 'fassung@test.invalid'"))
        db.commit()
        lead = Lead(company_name="Fassungstest", email="fassung@test.invalid")
        db.add(lead)
        db.commit()
        db.add_all([
            AuditResult(lead_id=lead.id, status="completed", total_score=72,
                        company_name="Fassungstest",
                        level="Homepage Standard Silber",
                        website_url="https://fassung.test",
                        standard_version=STANDARD_VERSION),
            # Ein Altbestand ohne Vermerk — genau der Fall, den die
            # Trennlinie meint.
            AuditResult(lead_id=lead.id, status="completed", total_score=55,
                        company_name="Fassungstest",
                        level="Homepage Standard Bronze",
                        website_url="https://fassung.test"),
        ])
        db.commit()
        lead_id = lead.id
    finally:
        db.close()

    try:
        # Act
        antwort = client.get(f"/api/leads/{lead_id}/audits", headers=auth_headers)

        # Assert
        assert antwort.status_code == 200
        fassungen = [a["standard_version"] for a in antwort.json()]
        assert STANDARD_VERSION in fassungen
        assert "" in fassungen, (
            "Der Altbestand muss als „ohne Vermerk\" durchkommen und nicht "
            "stillschweigend die aktuelle Fassung erben."
        )
    finally:
        db = SessionLocal()
        try:
            db.execute(text("DELETE FROM audit_results WHERE website_url = "
                            "'https://fassung.test'"))
            db.execute(text("DELETE FROM leads WHERE email = 'fassung@test.invalid'"))
            db.commit()
        finally:
            db.close()
