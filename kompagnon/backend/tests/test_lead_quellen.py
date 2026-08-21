"""L-59: Wir pruefen bei Kunden die Rechtsgrundlage und fuehren sie selbst nicht.

`audit_collectors.py:255` sucht auf fremden Seiten nach „Art. 6",
`netlify_service.py:531` schreibt sie in erzeugte Seiten, `pdf_generator.py:427`
druckt eine Spalte dafuer. Am eigenen Lead: 79 Felder, keines nennt sie.

Beim Nachmessen am 21.08.2026 zeigte sich, dass der Wortschatz der Quelle —
an dem eine Rechtsgrundlage haengen muesste — selbst nicht gefuehrt wird:

    geschrieben  embed_audit · stripe_checkout · domain_import · landing_audit
                 csv_import · Manuell · trackdesk · HWK-<Kammer>
                 facebook · linkedin · google · postkarte · telefon
                 + Freitext aus Kampagnen und aus einem oeffentlichen Endpunkt

    gelesen      AUTO_SEQUENCE_SOURCES nennt acht Werte, davon werden
                 fuenf nirgends geschrieben (landing_page, llm_landing,
                 webhook_facebook, webhook_linkedin, webhook_google)

Dieser Test haelt beide Seiten zusammen.
"""
import pytest

from services import lead_quellen as lq


class TestWortschatz:
    def test_jede_quelle_die_der_code_schreibt_ist_bekannt(self):
        """Was geschrieben wird, muss auch benannt sein — sonst steht in der
        Liste ein Wert, den niemand erklaeren kann."""
        # Arrange — am 21.08.2026 im Quelltext gezaehlt
        geschrieben = {
            "embed_audit", "stripe_checkout", "domain_import", "landing_audit",
            "csv_import", "trackdesk", "facebook", "linkedin", "google",
            "postkarte", "telefon",
        }

        # Assert
        unbekannt = geschrieben - set(lq.QUELLEN)
        assert unbekannt == set(), f"Nicht benannt: {sorted(unbekannt)}"

    def test_jede_benannte_quelle_traegt_eine_herkunft(self):
        for slug, quelle in lq.QUELLEN.items():
            assert quelle["herkunft"] in lq.HERKUENFTE, slug

    def test_freitext_bleibt_erlaubt_und_meldet_sich_als_unbekannt(self):
        """Kampagnennamen wie `HWK-Muenchen` sind gewollt — sie duerfen nur
        nicht so tun, als waeren sie gefuehrt."""
        # Act
        herkunft = lq.herkunft_fuer("HWK-Muenchen")

        # Assert
        assert herkunft is None


class TestHerkunft:
    """Die Herkunft ist eine Tatsache aus dem Quelltext, keine Rechtsauskunft:
    Hat die Person sich selbst gemeldet, oder haben wir sie gesammelt?"""

    @pytest.mark.parametrize("quelle", [
        "embed_audit", "stripe_checkout", "landing_audit",
        "facebook", "linkedin", "google", "postkarte", "telefon", "trackdesk",
    ])
    def test_wer_sich_selbst_gemeldet_hat_ist_eingehend(self, quelle):
        assert lq.herkunft_fuer(quelle) == lq.EINGEHEND

    @pytest.mark.parametrize("quelle", ["domain_import", "csv_import"])
    def test_wen_wir_gesammelt_haben_ist_kaltakquise(self, quelle):
        assert lq.herkunft_fuer(quelle) == lq.KALTAKQUISE

    def test_eine_leere_quelle_bekommt_keine_herkunft(self):
        assert lq.herkunft_fuer("") is None
        assert lq.herkunft_fuer(None) is None


class TestRechtsgrundlage:
    """Eingetragen wird nur, was **im Code belegbar** ist. Alles Uebrige bleibt
    offen und sichtbar — dieselbe Entscheidung wie bei der Lebenszyklus-Phase:
    Raten waere hier schlimmer als nichts tun, denn es ist eine Rechtsauskunft.
    """

    def test_ein_kauf_belegt_den_vertrag(self):
        """`_handle_successful_payment` legt den Lead erst nach abgeschlossener
        Zahlung an. Dass ein Vertrag besteht, ist keine Auslegung."""
        assert lq.rechtsgrundlage_fuer("stripe_checkout") == lq.VERTRAG

    @pytest.mark.parametrize("quelle", [
        "embed_audit", "domain_import", "csv_import", "landing_audit",
        "facebook", "linkedin", "google", "postkarte", "telefon", "trackdesk",
    ])
    def test_alles_uebrige_bleibt_offen_statt_geraten(self, quelle):
        assert lq.rechtsgrundlage_fuer(quelle) is None

    def test_offene_quellen_lassen_sich_auflisten(self):
        """Damit die Entscheidung eine Liste hat und keine Suche."""
        # Act
        offen = lq.quellen_ohne_rechtsgrundlage()

        # Assert
        assert "stripe_checkout" not in offen
        assert "domain_import" in offen
        assert offen == sorted(offen)


class TestPhantomwerte:
    """Fund vom 21.08.: Fuenf der acht Werte in `AUTO_SEQUENCE_SOURCES`
    werden nirgends geschrieben — sie koennen also nie greifen."""

    def test_die_phantomwerte_sind_benannt_und_als_solche_gekennzeichnet(self):
        # Assert
        for wert in ("landing_page", "llm_landing", "webhook_facebook",
                     "webhook_linkedin", "webhook_google"):
            assert wert in lq.NIE_GESCHRIEBEN

    def test_kein_phantomwert_steht_zugleich_im_gefuehrten_wortschatz(self):
        """Sonst behauptet die eine Seite, was die andere widerlegt."""
        assert set(lq.NIE_GESCHRIEBEN) & set(lq.QUELLEN) == set()


# ── Am Endpunkt geprueft, nicht am Werkzeug ───────────────────────────
#
# Ein gruenes Modul beweist nicht, dass die Antwort das Feld traegt. Siehe
# [[feedback-am-gegenstand-pruefen]] — am 19.08. hat ein Test die falsche
# Route gemessen und dabei nichts bemerkt.
#
# Und beim ersten Lauf hier genau wieder: `GET /api/leads/{id}` antwortete
# mit 200, aber ohne `lead` — es ist ein `LeadResponse` und nicht die Route,
# die das Betriebsblatt laedt. Die ist `/{id}/profile`
# (`LeadProfile.jsx:385`). Der Statuscode allein haette nichts verraten.

class TestAmEndpunkt:
    @pytest.fixture
    def betrieb(self, client, auth_headers):
        """Ein Betrieb aus einer gefuehrten Kaltakquise-Quelle."""
        from database import Lead, SessionLocal

        sitzung = SessionLocal()
        try:
            lead = Lead(company_name="Pruefbetrieb Rechtsgrundlage",
                        website_url="https://probe-l59.example",
                        status="new", lead_source="domain_import")
            sitzung.add(lead)
            sitzung.commit()
            sitzung.refresh(lead)
            lead_id = lead.id
        finally:
            sitzung.close()

        yield lead_id

        sitzung = SessionLocal()
        try:
            sitzung.query(Lead).filter(Lead.id == lead_id).delete()
            sitzung.commit()
        finally:
            sitzung.close()

    def test_das_betriebsblatt_nennt_herkunft_und_rechtsgrundlage(
            self, client, auth_headers, betrieb):
        # Act
        antwort = client.get(f"/api/leads/{betrieb}/profile", headers=auth_headers)

        # Assert
        assert antwort.status_code == 200, antwort.text
        lead = antwort.json()["lead"]
        assert lead["datenherkunft"] == lq.KALTAKQUISE
        assert lead["rechtsgrundlage"] is None
        assert lead["quelle_gefuehrt"] is True

    def test_eine_ungefuehrte_quelle_gibt_sich_zu_erkennen(
            self, client, auth_headers, betrieb):
        """Ein Kampagnenname darf nicht aussehen wie eine gefuehrte Quelle."""
        from database import Lead, SessionLocal

        # Arrange
        sitzung = SessionLocal()
        try:
            sitzung.query(Lead).filter(Lead.id == betrieb).update(
                {"lead_source": "HWK-Muenchen"})
            sitzung.commit()
        finally:
            sitzung.close()

        # Act
        antwort = client.get(f"/api/leads/{betrieb}/profile", headers=auth_headers)

        # Assert
        lead = antwort.json()["lead"]
        assert lead["quelle_gefuehrt"] is False
        assert lead["datenherkunft"] is None
        assert lead["rechtsgrundlage"] is None


# ── Zwei Schreibweisen, ein Filter, der nur eine kennt ────────────────

class TestSchreibweisen:
    """Gemessen am 21.08.2026: `routers/leads.py:1354` schrieb `Manuell`,
    drei Frontend-Stellen schreiben `manual`, und `betriebeListe.js:83`
    filtert auf `manual`. Ein von der Backend-Seite von Hand angelegter
    Betrieb war ueber „Von Hand" nicht zu finden."""

    def test_manuell_und_manual_sind_dieselbe_quelle(self):
        assert lq.normalisiere("Manuell") == "manual"
        assert lq.herkunft_fuer("Manuell") == lq.herkunft_fuer("manual")

    def test_audit_gross_und_klein_sind_dieselbe_quelle(self):
        assert lq.normalisiere("Audit") == "audit"
        assert lq.quelle_bekannt("Audit") is True

    def test_die_zielschreibweise_steht_selbst_im_wortschatz(self):
        """Sonst zeigt die Zuordnung auf einen Wert, den niemand fuehrt."""
        for ziel in lq.SCHREIBWEISEN.values():
            assert ziel in lq.QUELLEN, ziel

    def test_keine_zuordnung_zeigt_auf_sich_selbst(self):
        for von, nach in lq.SCHREIBWEISEN.items():
            assert von != nach

    def test_der_bestand_wird_einmalig_mitgezogen(self):
        """Die Zuordnung beim Lesen reicht nicht: Der Filter vergleicht den
        gespeicherten Wert. Deshalb laeuft sie auch ueber den Bestand."""
        import re
        import pathlib

        quelle = pathlib.Path(__file__).resolve().parent.parent / "main.py"
        text = quelle.read_text(encoding="utf-8")

        assert re.search(r"UPDATE leads SET lead_source", text), (
            "Der Bestand wird nicht nachgezogen — alte Zeilen bleiben im "
            "Filter unsichtbar."
        )


# ── Beide Seiten müssen dieselben Wörter führen ───────────────────────
#
# Dasselbe Verfahren wie bei der Lebenszyklus-Phase (`test_lebenszyklus.py`):
# Es gibt keine gemeinsame Quelle für Backend und Bildschirm, und eine zu
# bauen wäre mehr Apparat als Nutzen. Der Test schaut deshalb in die JS-Datei.

def _js_quelle():
    from pathlib import Path
    return (Path(__file__).resolve().parents[2]
            / "frontend" / "src" / "utils" / "leadStatus.js").read_text(encoding="utf-8")


def _js_block(name, muster=r"^\s*([a-z0-9_]+):"):
    import re
    treffer = re.search(rf"{name} = \{{(.*?)\n\}};", _js_quelle(), re.S)
    assert treffer, f"{name} nicht gefunden — hat die Datei sich bewegt?"
    return set(re.findall(muster, treffer.group(1), re.M))


def test_der_bildschirm_kennt_dieselben_herkuenfte():
    assert _js_block("DATEN_HERKUNFT") == set(lq.HERKUENFTE)


def test_der_bildschirm_kennt_dieselben_rechtsgrundlagen():
    assert _js_block("RECHTSGRUNDLAGE") == set(lq.RECHTSGRUNDLAGE_LABEL)


def test_jede_gefuehrte_quelle_hat_am_bildschirm_einen_namen():
    """Sonst steht dort ein Schluessel statt eines Wortes.

    Der Rueckfall `lesbar()` macht daraus zwar keinen rohen Wert mehr, aber
    „Isb impuls" ist auch keine Beschriftung, die jemand geschrieben hat.
    """
    im_bildschirm = _js_block("LEAD_SOURCE")
    fehlend = set(lq.QUELLEN) - im_bildschirm

    assert not fehlend, f"Ohne Namen am Bildschirm: {sorted(fehlend)}"
