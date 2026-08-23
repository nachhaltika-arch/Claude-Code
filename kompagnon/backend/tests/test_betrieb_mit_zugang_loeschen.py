"""Einen Betrieb löschen, dessen Kunde ein Konto hat (L-56).

**Die Entscheidung, entschieden am 22.08.2026.** Bis dahin scheiterte
`DELETE /api/leads/{id}` an einem Betrieb mit Kundenzugang — erst mit 500,
seit dem 19.08. mit einem 409, der sagt, welcher Zugang im Weg steht. Offen
blieb, ob das Löschen des Betriebs das Konto mitnehmen soll.

**Antwort: nicht von selbst, aber auf ausdrückliche Anweisung.** Beides hat
einen Grund:

* **Nicht von selbst.** Wer einen Betrieb aus dem Bestand räumt — Dublette,
  kein Kunde mehr —, löscht sonst unbemerkt einen Zugang, mit dem sich ein
  Mensch anmeldet. Ein Konto darf nicht die Nebenwirkung einer Aufräumarbeit
  sein.
* **Aber ein Weg muss es geben.** Bei einem Löschverlangen nach Art. 17 DSGVO
  muss beides weg. Ohne diesen Weg müsste der Innendienst das Konto in einem
  anderen Bildschirm suchen — zwei Schritte, von denen man einen vergisst,
  und ein übriggebliebenes Konto ist genau der Verstoß, den die Vorschrift
  meint.

Deshalb `?mit_zugang=true`: Der Standardweg bleibt der 409, und wer beides
löschen will, sagt es. Die Antwort nennt danach, welches Konto mitging —
sonst ist es wieder still.
"""
import pytest
from sqlalchemy import text


@pytest.fixture
def betrieb_mit_zugang(app):
    """Ein Betrieb, an dem ein Kundenkonto hängt."""
    from auth import hash_password
    from database import SessionLocal, Lead, User

    db = SessionLocal()
    try:
        lead = Lead(company_name="Löschprobe GmbH", trade="Heizung", city="Kassel")
        db.add(lead)
        db.commit()
        db.refresh(lead)

        konto = User(email=f"loeschprobe-{lead.id}@example.com",
                     password_hash=hash_password("egal"),
                     role="kunde", lead_id=lead.id, is_active=True)
        db.add(konto)
        db.commit()
        return {"lead_id": lead.id, "email": konto.email}
    finally:
        db.close()


@pytest.fixture
def betrieb_ohne_zugang(app):
    from database import SessionLocal, Lead

    db = SessionLocal()
    try:
        lead = Lead(company_name="Ohne Zugang GmbH", trade="Elektrik", city="Kassel")
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead.id
    finally:
        db.close()


def _gibt_es(tabelle: str, spalte: str, wert) -> bool:
    from database import SessionLocal

    db = SessionLocal()
    try:
        zeile = db.execute(
            text(f"SELECT 1 FROM {tabelle} WHERE {spalte} = :w LIMIT 1"), {"w": wert}
        ).fetchone()
        return zeile is not None
    finally:
        db.close()


class TestOhneAnweisung:
    def test_der_betrieb_bleibt_und_die_antwort_nennt_den_zugang(
            self, client, auth_headers, betrieb_mit_zugang):
        antwort = client.delete(f"/api/leads/{betrieb_mit_zugang['lead_id']}",
                                headers=auth_headers)

        assert antwort.status_code == 409
        assert betrieb_mit_zugang["email"] in antwort.text
        assert _gibt_es("leads", "id", betrieb_mit_zugang["lead_id"])

    def test_das_konto_bleibt_unberuehrt(self, client, auth_headers, betrieb_mit_zugang):
        """Der abgebrochene Lauf darf nichts halb erledigt hinterlassen."""
        client.delete(f"/api/leads/{betrieb_mit_zugang['lead_id']}", headers=auth_headers)

        assert _gibt_es("users", "email", betrieb_mit_zugang["email"])

    def test_die_antwort_sagt_auch_wie_es_geht(
            self, client, auth_headers, betrieb_mit_zugang):
        """Ein 409, der den Ausweg verschweigt, ist eine Sackgasse."""
        antwort = client.delete(f"/api/leads/{betrieb_mit_zugang['lead_id']}",
                                headers=auth_headers)

        assert "mit_zugang" in antwort.text


class TestMitAnweisung:
    def test_beides_verschwindet(self, client, auth_headers, betrieb_mit_zugang):
        antwort = client.delete(
            f"/api/leads/{betrieb_mit_zugang['lead_id']}?mit_zugang=true",
            headers=auth_headers)

        assert antwort.status_code == 200, antwort.text[:200]
        assert not _gibt_es("leads", "id", betrieb_mit_zugang["lead_id"])
        assert not _gibt_es("users", "email", betrieb_mit_zugang["email"])

    def test_die_antwort_nennt_das_mitgeloeschte_konto(
            self, client, auth_headers, betrieb_mit_zugang):
        """Sonst ist das Mitlöschen genau die stille Nebenwirkung, die es
        nicht sein soll."""
        antwort = client.delete(
            f"/api/leads/{betrieb_mit_zugang['lead_id']}?mit_zugang=true",
            headers=auth_headers).json()

        assert betrieb_mit_zugang["email"] in antwort.get("zugaenge_geloescht", [])

    def test_fremde_konten_bleiben(self, client, auth_headers,
                                   betrieb_mit_zugang, betrieb_ohne_zugang):
        """Gelöscht wird, was an diesem Betrieb hängt — nichts sonst."""
        from auth import hash_password
        from database import SessionLocal, User

        db = SessionLocal()
        try:
            fremd = User(email=f"fremd-{betrieb_ohne_zugang}@example.com",
                         password_hash=hash_password("egal"), role="kunde",
                         lead_id=betrieb_ohne_zugang, is_active=True)
            db.add(fremd)
            db.commit()
            fremde_adresse = fremd.email
        finally:
            db.close()

        client.delete(f"/api/leads/{betrieb_mit_zugang['lead_id']}?mit_zugang=true",
                      headers=auth_headers)

        assert _gibt_es("users", "email", fremde_adresse)


class TestUnveraendert:
    def test_ein_betrieb_ohne_zugang_loescht_wie_bisher(
            self, client, auth_headers, betrieb_ohne_zugang):
        antwort = client.delete(f"/api/leads/{betrieb_ohne_zugang}", headers=auth_headers)

        assert antwort.status_code == 200
        assert not _gibt_es("leads", "id", betrieb_ohne_zugang)

    def test_der_parameter_aendert_daran_nichts(
            self, client, auth_headers, betrieb_ohne_zugang):
        antwort = client.delete(
            f"/api/leads/{betrieb_ohne_zugang}?mit_zugang=true", headers=auth_headers)

        assert antwort.status_code == 200
        assert antwort.json().get("zugaenge_geloescht") == []
