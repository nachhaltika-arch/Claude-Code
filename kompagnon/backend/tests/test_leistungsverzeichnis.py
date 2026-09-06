# -*- coding: utf-8 -*-
"""Was der Kunde für sein Pflege-Abo bekommt — als Daten (L-160, Rang 3).

**Der Befund.** Zwölf Positionen, für die ein Betrieb 79 € bzw. 149 € netto
**monatlich** zahlt — und **keine einzige** war im Konto abrufbar. Weder was er
bekommt, noch wie viel er genutzt hat, noch wie er es anfordert. Ein Abo,
dessen Leistungen man nicht sieht, wird gekündigt, weil es sich nach nichts
anfühlt.

**Rang 3 der Ordnung ist die billigste Hälfte davon:** die Zusagen dort
benennen, wo sie gelten. Die Reaktionszeit steht heute im Datenblatt und
nirgends am Support; die Fünf-Werktage-Frist stand nirgends an der Freigabe.
Das kostet keine Technik und macht den Vertrag sichtbar.

**Warum als Daten und nicht als Text in der Oberfläche.** Dieselbe Begründung
wie beim Mitwirkungskatalog (`services/mitwirkung.py`): Die Zusage ist eine
**Eigenschaft der Leistung**, keine Frage der Darstellung. Eine Verzweigung
nach Abo-Kennung im JSX wäre der zweite Ort, an dem das Datenblatt gepflegt
werden müsste — und der Bildschirm sagte eines Tages etwas anderes als der
Vertrag.
"""
import pytest

from services import leistungsverzeichnis as lv


# ── Der Katalog ───────────────────────────────────────────────────────

def test_pro_hat_neun_positionen_und_nicht_zwoelf():
    """**Drei Positionen ersetzen, sie addieren nicht** — und genau hier lag
    beim ersten Wurf dieses Tests mein eigener Fehler: Ich erwartete zwölf,
    weil das Verzeichnis zwölf führt.

    Das Datenblatt schreibt „Inhaltsänderungen bis 90 Minuten (**statt** 30)";
    Position 11 ersetzt die Reaktionszeit aus 6, Position 10 das Re-Audit aus
    7. Wer „zusätzlich" liest, kommt auf zwei Stunden Änderungsguthaben — der
    Fehler, den `abo_stunden` schon einmal gemacht hat.
    """
    assert len(lv.fuer_produkt("ABO-BAS")) == 7
    assert len(lv.fuer_produkt("ABO-PRO")) == 9

    fuer_pro = {p.nummer for p in lv.fuer_produkt("ABO-PRO")}
    assert fuer_pro == {1, 2, 3, 4, 8, 9, 10, 11, 12}
    assert set(lv.ERSETZT) & fuer_pro == {8, 10, 11}
    assert not set(lv.ERSETZT.values()) & fuer_pro, \
        "eine ersetzte Position darf nicht danebenstehen"


def test_ohne_abo_gibt_es_keine_zusagen():
    """**Kein geratener Vertrag.** Wer kein Pflege-Abo hat, bekommt keine
    Leistungsliste gezeigt — sonst stünde dort eine Zusage, die niemand
    gegeben hat."""
    assert lv.fuer_produkt("") == ()
    assert lv.fuer_produkt("ABO-XYZ") == ()


def test_die_reaktionszeit_unterscheidet_die_beiden_abos():
    """Der einzige Unterschied, der im Störungsfall zählt: ein Werktag gegen
    vier Stunden. Steht er falsch am Bildschirm, ist es eine Zusage zu viel
    oder eine zu wenig."""
    assert lv.reaktionszeit("ABO-BAS") == "innerhalb von einem Werktag"
    assert lv.reaktionszeit("ABO-PRO") == "innerhalb von 4 Stunden an Werktagen"
    assert lv.reaktionszeit("") is None


def test_jede_position_traegt_den_wortlaut_des_datenblatts():
    """`vertragstext` ist der Wortlaut aus KAS_DB_07 — die Zeile, die der
    Kunde unterschrieben hat. `titel` ist, was er auf dem Bildschirm liest."""
    pos5 = lv.NACH_NUMMER[5]

    assert "30 Minuten" in pos5.vertragstext
    assert pos5.titel != pos5.vertragstext, "Kundensprache ist nicht Vertragssprache"


def test_die_minutenzahlen_stimmen_mit_der_abrechnung_ueberein():
    """**„statt 30", nicht „zusätzlich".** Aus 30 + 90 wurden schon einmal
    zwei Stunden. Die Abrechnung führt die Zahl in `abo_stunden`; hier steht
    sie als Text. Zwei Fassungen derselben Zahl laufen auseinander — dieser
    Test hält sie zusammen."""
    from services import abo_stunden

    assert "30 Minuten" in lv.NACH_NUMMER[5].vertragstext
    assert abo_stunden.KONTINGENT_ABO_BAS_STUNDEN * 60 == 30
    assert "90 Minuten" in lv.NACH_NUMMER[8].vertragstext
    assert abo_stunden.KONTINGENT_ABO_PRO_STUNDEN * 60 == 90


@pytest.mark.parametrize("nummer", [p.nummer for p in lv.KATALOG])
def test_jede_position_sagt_wo_ihre_zusage_gilt(nummer):
    """**Der Kern von Rang 3.** Eine Leistung, die nirgends benannt ist, wird
    nicht wahrgenommen und trotzdem bezahlt. `ort` sagt, an welchem Bildschirm
    sie hingehört — und ein Katalogeintrag ohne Ort wäre eine Zusage ohne
    Adressat."""
    assert lv.NACH_NUMMER[nummer].ort in lv.ORTE


# ── Der Weg durch das Portal ──────────────────────────────────────────

@pytest.fixture
def ohne_abo(app, kunde_user):
    """Ein Betrieb ohne Pflegevertrag — vorher **und** nachher.

    **Warum die Fixture beides räumt.** Beim ersten Wurf legte der zweite Test
    einen Vertrag an und ließ ihn stehen. Allein liefen beide grün; im
    Gesamtlauf fielen sie um, weil ein anderer Test dem Kunden schon ein Abo
    gegeben hatte und meiner ihm danach eines hinterließ. Ein Test, der nur in
    seiner eigenen Datei stimmt, misst die Reihenfolge und nicht die Sache.
    """
    from database import AboVertrag, SessionLocal

    def leeren():
        db = SessionLocal()
        try:
            db.query(AboVertrag).filter(
                AboVertrag.lead_id == kunde_user.lead_id).delete()
            db.commit()
        finally:
            db.close()

    leeren()
    yield kunde_user.lead_id
    leeren()


def test_ohne_abo_meldet_das_konto_das_und_erfindet_nichts(client, kunde_headers, ohne_abo):
    antwort = client.get("/api/portal/leistungen", headers=kunde_headers)

    assert antwort.status_code == 200
    d = antwort.json()
    assert d["produkt"] is None
    assert d["positionen"] == []
    assert d["reaktionszeit"] is None


def test_mit_abo_stehen_die_neun_pro_positionen_da(client, kunde_headers, ohne_abo):
    from datetime import datetime

    from database import SessionLocal
    from services import abo_vertrag

    db = SessionLocal()
    try:
        abo_vertrag.anlegen(db, lead_id=ohne_abo, produkt="ABO-PRO",
                            start_monat=datetime.utcnow().strftime("%Y-%m"),
                            wer="test@kompagnon.eu")
    finally:
        db.close()

    d = client.get("/api/portal/leistungen", headers=kunde_headers).json()

    assert d["produkt"] == "ABO-PRO"
    assert len(d["positionen"]) == 9
    assert d["reaktionszeit"] == "innerhalb von 4 Stunden an Werktagen"
    assert all(p["titel"] and p["vertragstext"] for p in d["positionen"])
