# -*- coding: utf-8 -*-
"""Der Abmeldelink in den Sequenz-Mails (P0-11, 17.09.2026).

**Warum es ihn gibt.** Die E-Mail-Strecke geht ohne Anlass des Empfaengers
raus — Werbung im Sinne des § 7 UWG. Ohne jederzeitige, kostenfreie
Widerspruchsmoeglichkeit ist jede einzelne Mail angreifbar, und Art. 21
Abs. 2 DSGVO verlangt dasselbe. Am 17.09.2026 nachgemessen: **keine** der
drei Vorlagen trug einen Link; die Fusszeile nannte nur Firma und
`info@kompagnon.eu`.

**Warum die Tests so aussehen.** Ein Abmeldelink kann auf vier Arten still
versagen, und drei davon sehen im Betrieb wie Erfolg aus:

1. **Er steht nicht in der Mail.** Der Kern — deshalb prueft
   `test_jede_sequenzvorlage_traegt_den_abmeldelink` **alle** Vorlagen und
   nicht eine Stichprobe. Eine vierte Stufe, die spaeter dazukommt, faellt
   damit auf.
2. **Er wird geklickt und wirkt nicht.** Deshalb wird die Wirkung an der
   Datenbankzeile geprueft, nicht am Statuscode: Eine 200 sagt nur, dass die
   Route antwortet.
3. **Er wirkt auch fuer Fremde.** Ein ratbarer Link waere eine Abmeldung, die
   jeder fuer jeden ausloest. Deshalb der Test mit der gefaelschten
   Unterschrift — und, daneben, dass der **echte** Token durchkommt: Eine
   Zusicherung „falsche werden abgewiesen" ist fuer sich genommen auch dann
   gruen, wenn gar nichts durchkommt (`waechter_ohne_wirkung`).
4. **Er wird von einem Postfach-Scanner ausgeloest.** Sicherheitsprodukte
   rufen Links in Mails automatisch ab. Ein Abmeldelink muss trotzdem mit
   **einem** Klick wirken (alles andere ist keine niederschwellige
   Widerspruchsmoeglichkeit), also ist der Rueckweg die Antwort und nicht
   eine Zwischenseite: `test_die_abmeldung_laesst_sich_widerrufen`.
"""
import pytest

from database import Lead, SessionLocal
from services import abmeldung


#: Eine Kennung fuer die Token-Rechnung. Sie muss **nicht** existieren: Der
#: Token wird aus der Zahl und dem Schluessel gerechnet, ohne Datenbank.
KENNUNG = 4711


@pytest.fixture
def lead(app):
    """Ein Lead mit aktiver Sequenz, der nach dem Test wieder verschwindet.

    **Haengt an `app`, und das ist der Punkt.** Diese Fixture legt das Schema
    an (`conftest.py`); ohne sie greift der erste Test auf `leads` zu, bevor
    es die Tabelle gibt. Lokal faellt das nie auf — die Entwicklungsdatenbank
    traegt die Tabellen aus einem frueheren Lauf. In der CI, die mit einer
    leeren Postgres startet, bricht es sofort: `relation "leads" does not
    exist`. Genau so ist diese Datei am 17.09.2026 in der CI umgefallen,
    waehrend hier 4107 Tests gruen waren.
    """
    db = SessionLocal()
    try:
        eintrag = Lead(company_name="Testbetrieb Abmeldung",
                       email="abmeldung-test@example.invalid",
                       sequence_active=True, sequence_step=1)
        db.add(eintrag)
        db.commit()
        db.refresh(eintrag)
        kennung = eintrag.id
    finally:
        db.close()

    yield kennung

    db = SessionLocal()
    try:
        db.query(Lead).filter(Lead.id == kennung).delete()
        db.commit()
    finally:
        db.close()


def _stand(lead_id: int):
    db = SessionLocal()
    try:
        return db.query(Lead).filter(Lead.id == lead_id).first().sequence_active
    finally:
        db.close()


# --------------------------------------------------------------- der Token

def test_der_token_traegt_eine_unterschrift_und_die_kennung():
    token = abmeldung.token(KENNUNG)
    assert token.startswith(f"{KENNUNG}.")
    assert abmeldung.lead_aus_token(token) == KENNUNG


def test_ein_gefaelschter_token_wird_abgewiesen():
    """Daneben steht oben, dass der echte durchkommt — sonst waere gruen blind."""
    echt = abmeldung.token(KENNUNG)
    gefaelscht = f"{KENNUNG}." + ("0" * (len(echt) - len(str(KENNUNG)) - 1))
    assert gefaelscht != echt
    assert abmeldung.lead_aus_token(gefaelscht) is None


def test_der_token_eines_leads_meldet_keinen_anderen_ab():
    """Die Unterschrift geht ueber die Kennung — umschreiben macht sie ungueltig."""
    fremd = abmeldung.token(KENNUNG)
    _, unterschrift = fremd.split(".", 1)
    assert abmeldung.lead_aus_token(f"{KENNUNG + 1}.{unterschrift}") is None


def test_kaputte_eingaben_werfen_nicht():
    for murks in ("", ".", "abc", "1.", ".abc", "1.2.3", None):
        assert abmeldung.lead_aus_token(murks) is None


# --------------------------------------------------------------- die Route

def test_ein_klick_beendet_die_sequenz(client, lead):
    assert _stand(lead) is True
    antwort = client.get(f"/api/mail/abmelden/{abmeldung.token(lead)}")
    assert antwort.status_code == 200
    assert _stand(lead) is False


def test_ein_zweiter_klick_ist_harmlos(client, lead):
    pfad = f"/api/mail/abmelden/{abmeldung.token(lead)}"
    assert client.get(pfad).status_code == 200
    assert client.get(pfad).status_code == 200
    assert _stand(lead) is False


def test_ein_gefaelschter_link_meldet_niemanden_ab(client, lead):
    echt = abmeldung.token(lead)
    gefaelscht = f"{lead}." + ("0" * (len(echt) - len(str(lead)) - 1))
    antwort = client.get(f"/api/mail/abmelden/{gefaelscht}")
    assert antwort.status_code == 400
    assert _stand(lead) is True


def test_die_abmeldung_laesst_sich_widerrufen(client, lead):
    """Gegen den Postfach-Scanner: ein Klick wirkt, und ein Weg zurueck steht da."""
    client.get(f"/api/mail/abmelden/{abmeldung.token(lead)}")
    assert _stand(lead) is False

    antwort = client.get(f"/api/mail/abmelden/{abmeldung.token(lead)}/rueckgaengig")
    assert antwort.status_code == 200
    assert _stand(lead) is True


def test_die_bestaetigungsseite_nennt_den_rueckweg(client, lead):
    antwort = client.get(f"/api/mail/abmelden/{abmeldung.token(lead)}")
    assert "rueckgaengig" in antwort.text
    assert "abgemeldet" in antwort.text.lower()


def test_ein_unbekannter_lead_verraet_sich_nicht(client):
    """Kein 404 auf eine gueltige Unterschrift — sonst waere der Link ein Melder,
    ob es eine Kennung gibt. Fuer den Klickenden sieht beides gleich aus."""
    antwort = client.get(f"/api/mail/abmelden/{abmeldung.token(999999999)}")
    assert antwort.status_code == 200


# ------------------------------------------------------------- die Vorlagen

def test_jede_sequenzvorlage_traegt_den_abmeldelink(lead):
    """Am Erzeugnis geprueft, nicht an einer selbstgebauten Eingabe.

    Die Felder kommen aus `vorlagenfelder` — derselben Funktion, die der
    Versand benutzt. Ein Test, der sich seine Eingabe selbst ausdenkt, geht
    gruen durch, waehrend der Versand an einem fehlenden Feld scheitert
    (`test_ohne_den_gegenstand`); genau das ist beim ersten Lauf dieser
    Datei passiert — die erfundenen Felder kannten `firma` nicht.
    """
    from services.email_templates import SEQUENZ_TEMPLATES, render
    from services.sequence_runner import vorlagenfelder

    felder = vorlagenfelder(lead, "beispiel.de", "Beispiel",
                            top_problem="Ladezeit", tipps_html="<li>Test</li>")
    erwartet = felder["abmelde_url"]

    strecke = [n for n in SEQUENZ_TEMPLATES if n.startswith("sequence_step_")]
    assert strecke, "Ohne Vorlagen prueft dieser Test nichts."
    for name in strecke:
        fertig = render(name, felder)
        assert erwartet in fertig["html"], (
            f"Vorlage {name} traegt keinen Abmeldelink")
        assert "bmeld" in fertig["html"].lower(), (
            f"Vorlage {name} verlinkt, benennt den Link aber nicht")


def test_die_projektpost_traegt_keinen_abmeldelink(lead):
    """`phase_change` ist keine Werbung, sondern Post an einen Kunden mit
    Vertrag — ein Abmeldelink waere dort irrefuehrend: Der Klick schaltet die
    Werbestrecke ab, nicht die Projektpost. Der Empfaenger glaubte, er habe
    Projektmails abbestellt, und bekaeme sie weiter.

    **Am 17.09.2026 beim ersten Lauf gefunden.** Die Fusszeile mit dem
    Firmennamen steht in `sequence_step_1`, `sequence_step_2` **und**
    `phase_change` — aber nicht in `sequence_step_3`. Wer den Link ueber die
    Fusszeile verteilt, trifft die falschen zwei von drei.
    """
    from services.email_templates import SEQUENZ_TEMPLATES, render
    from services.sequence_runner import vorlagenfelder

    assert "phase_change" in SEQUENZ_TEMPLATES
    felder = dict(vorlagenfelder(lead, "beispiel.de", "Beispiel"))
    felder.update({"phase_name": "Technik", "phase_nr": 4,
                   "phase_beschreibung": "Ihre Website wird gebaut.",
                   "portal_url": "https://example.invalid/portal"})

    fertig = render("phase_change", felder)
    # Positiv daneben: Die Vorlage wurde wirklich gefuellt. Ohne diese Zeile
    # waere die Zusicherung darunter auch dann gruen, wenn `render` an einem
    # fehlenden Feld ein leeres Ergebnis zurueckgibt (`waechter_ohne_wirkung`).
    assert "Technik" in fertig["html"]
    assert felder["abmelde_url"] not in fertig["html"]


def test_der_versand_fuellt_den_abmeldelink(lead):
    """Die Luecke zwischen Vorlage und Versand: Ein Platzhalter, den niemand
    fuellt, bleibt als `{abmelde_url}` in der Mail stehen — sichtbar fuer den
    Empfaenger und wirkungslos."""
    from services import sequence_runner

    felder = sequence_runner.vorlagenfelder(lead, "beispiel.de", "Beispiel")
    assert felder["abmelde_url"].endswith(abmeldung.token(lead))
    assert felder["abmelde_url"].startswith("http")
