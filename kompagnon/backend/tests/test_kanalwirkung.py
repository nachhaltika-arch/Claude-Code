"""Welcher Kanal bringt Kunden? (L-84)

**Der Befund.** Die Herkunft steht seit langem in `leads.lead_source`, und
`services/lead_quellen.py` führt dazu einen gepflegten Wortschatz — Name,
Herkunftsart, Rechtsgrundlage, Beleg. Was fehlte, ist die Frage, für die man
das alles erhebt: **Welcher Kanal bringt Kunden?** Ohne sie ist jede Aussage
über Kanalwirkung geschätzt.

**Warum die Lebenszyklus-Phase und nicht der Status.** `Lead.status`
beantwortete zwei Fragen gleichzeitig — wo im Trichter und wie weit in der
Bearbeitung —, und zwei Stellen übersahen dabei `customer` (L-26, 19.08.).
`lifecycle_phase` ist die Antwort auf genau eine Frage und wird von einem
Ereignis mitgezogen. Eine Kennzahl, die auf der falschen Spalte rechnet, ist
schlimmer als keine.

**Unbekannte Quellen werden ausgewiesen, nicht weggelassen.** Ein Kanal, den
der Wortschatz nicht kennt, ist der interessanteste Fall: Entweder schreibt
jemand einen Wert, den niemand gepflegt hat — oder der Wortschatz hinkt
hinterher. Beides gehört gesehen, nicht stillschweigend aussortiert.
"""
import pytest
from sqlalchemy import text


@pytest.fixture
def bestand(app):
    """Ein Bestand mit drei Kanälen und einem unbekannten Wert."""
    from database import Lead, SessionLocal

    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM leads WHERE company_name LIKE 'L84 %'"))
        db.commit()
        db.add_all([
            # Widget: drei Betriebe, einer davon Kunde
            Lead(company_name="L84 A", lead_source="embed_audit", lifecycle_phase="kunde"),
            Lead(company_name="L84 B", lead_source="embed_audit", lifecycle_phase="interessent"),
            Lead(company_name="L84 C", lead_source="embed_audit", lifecycle_phase="im_gespraech"),
            # Kauf: einer, und der ist Kunde
            Lead(company_name="L84 D", lead_source="stripe_checkout", lifecycle_phase="kunde"),
            # Kaltakquise: zwei, keiner Kunde
            Lead(company_name="L84 E", lead_source="csv_import", lifecycle_phase="interessent"),
            Lead(company_name="L84 F", lead_source="csv_import", lifecycle_phase="ausgeschieden"),
            # Ein Wert, den der Wortschatz nicht kennt
            Lead(company_name="L84 G", lead_source="irgendwoher", lifecycle_phase="kunde"),
            # Und einer ganz ohne Herkunft
            Lead(company_name="L84 H", lead_source=None, lifecycle_phase="interessent"),
        ])
        db.commit()
    finally:
        db.close()

    yield

    # **Hinterher aufraeumen, nicht nur vorher.** Diese acht Betriebe haben
    # keine `website_url`; im vollen Lauf stolperte `test_leads_public`
    # darueber, das seine Dubletten ueber die Domain sucht. Ein Test, der
    # seinen Bestand stehen laesst, macht den naechsten unzuverlaessig — und
    # genau solche Wechselwirkungen sind nur im Gesamtlauf zu sehen.
    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM leads WHERE company_name LIKE 'L84 %'"))
        db.commit()
    finally:
        db.close()


def _kanaele(client, headers):
    antwort = client.get("/api/leads/quellen/wirkung", headers=headers)
    assert antwort.status_code == 200, antwort.text[:200]
    return {k["quelle"]: k for k in antwort.json()["kanaele"]}


class TestZugriff:
    def test_der_kunde_sieht_die_kanalwirkung_nicht(self, client, kunde_headers):
        """Sie verraet den gesamten Bestand in Zahlen."""
        antwort = client.get("/api/leads/quellen/wirkung", headers=kunde_headers)

        assert antwort.status_code == 403

    def test_ohne_anmeldung_gar_nicht(self, client):
        assert client.get("/api/leads/quellen/wirkung").status_code in (401, 403)


class TestZahlen:
    def test_zaehlt_betriebe_und_kunden_je_kanal(self, client, auth_headers, bestand):
        kanaele = _kanaele(client, auth_headers)

        assert kanaele["embed_audit"]["betriebe"] == 3
        assert kanaele["embed_audit"]["kunden"] == 1
        assert kanaele["stripe_checkout"]["kunden"] == 1
        assert kanaele["csv_import"]["kunden"] == 0

    def test_traegt_den_gepflegten_namen_und_die_herkunftsart(
            self, client, auth_headers, bestand):
        """Sonst steht dort `embed_audit`, und niemand ausser dem Entwickler
        weiss, was gemeint ist."""
        kanaele = _kanaele(client, auth_headers)

        assert kanaele["embed_audit"]["name"] == "Analyse-Widget"
        assert kanaele["csv_import"]["herkunft"] == "kaltakquise"

    def test_die_quote_sagt_was_der_kanal_taugt(self, client, auth_headers, bestand):
        kanaele = _kanaele(client, auth_headers)

        assert kanaele["embed_audit"]["quote"] == 0.33
        assert kanaele["stripe_checkout"]["quote"] == 1.0
        assert kanaele["csv_import"]["quote"] == 0.0


class TestEhrlichkeit:
    def test_ein_unbekannter_kanal_wird_ausgewiesen(self, client, auth_headers, bestand):
        """Der interessanteste Fall: Entweder schreibt jemand einen Wert, den
        niemand gepflegt hat — oder der Wortschatz hinkt hinterher."""
        kanaele = _kanaele(client, auth_headers)

        assert "irgendwoher" in kanaele
        assert kanaele["irgendwoher"]["bekannt"] is False

    def test_betriebe_ohne_herkunft_werden_nicht_verschwiegen(
            self, client, auth_headers, bestand):
        """Sie stillschweigend wegzulassen hiesse, die Summe der Kanaele als
        Gesamtbestand zu lesen — und die waere zu klein."""
        antwort = client.get("/api/leads/quellen/wirkung",
                             headers=auth_headers).json()

        assert antwort["ohne_herkunft"] >= 1

    def test_die_summe_geht_auf(self, client, auth_headers, bestand):
        """Eine Kennzahl, deren Teile sich nicht zum Ganzen fuegen, laedt zum
        Weiterrechnen mit falschen Zahlen ein."""
        antwort = client.get("/api/leads/quellen/wirkung",
                             headers=auth_headers).json()

        summe = sum(k["betriebe"] for k in antwort["kanaele"])
        assert summe + antwort["ohne_herkunft"] == antwort["betriebe_gesamt"]
