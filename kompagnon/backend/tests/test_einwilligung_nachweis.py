# -*- coding: utf-8 -*-
"""Der Nachweis der Einwilligung — dass er entsteht, und was er nicht enthaelt.

**Warum diese Tests so aussehen (17.09.2026, L-195).** Der Nachweis hat zwei
Aufgaben, und beide lassen sich still verfehlen:

1. **Er soll ein Nachweis sein.** Entsteht keine Zeile, faellt das nirgends
   auf — bis jemand nach Art. 7 Abs. 1 DSGVO fragt.
2. **Er soll die drei Ursachen trennen** (Ablehnung, Werbeblocker,
   In-App-Browser). Wuerde `unbekannt` als `abgelehnt` verbucht, saehe die
   Auswertung vollstaendig aus und waere falsch.

Und er hat eine Grenze, die genauso wichtig ist wie seine Wirkung: **Er darf
niemanden identifizieren, der abgelehnt hat.** Deshalb prueft die Haelfte
dieser Datei, was *nicht* in der Zeile steht. Eine Zusicherung der Form „hier
steht keine volle IP" ist fuer sich genommen ein Waechter ohne Wirkung — sie
steht deshalb jeweils **neben** einer positiven Zusicherung, dass das Netz
sehr wohl ankommt (`waechter_ohne_wirkung`).
"""
import pytest

from database import Einwilligung, SessionLocal
from routers import widget_einwilligung as nw


def _kennung(suffix: str) -> str:
    """Eine gueltige Kennung mit wiedererkennbarem Ende."""
    return ("a" * (32 - len(suffix))) + suffix


@pytest.fixture
def aufraeumen():
    kennungen = []
    yield kennungen
    db = SessionLocal()
    try:
        if kennungen:
            db.query(Einwilligung).filter(
                Einwilligung.nachweis.in_(kennungen)).delete(
                    synchronize_session=False)
            db.commit()
    finally:
        db.close()


def _zeile(nachweis):
    db = SessionLocal()
    try:
        return db.query(Einwilligung).filter(
            Einwilligung.nachweis == nachweis).first()
    finally:
        db.close()


# ── Dass ueberhaupt etwas entsteht ────────────────────────────────────

def test_eine_erteilte_einwilligung_hinterlaesst_eine_zeile(client, aufraeumen):
    kennung = _kennung("0001")
    aufraeumen.append(kennung)

    antwort = client.post("/api/widget/einwilligung", json={
        "nachweis": kennung, "entscheidung": "erteilt",
        "marketing": True, "statistik": True,
        "quelle": "nachricht", "fassung": "kpg-consent-v1",
        "seite": "https://websprint.kompagnon.eu/?utm_source=facebook#analyse",
    })

    assert antwort.status_code == 204
    zeile = _zeile(kennung)
    assert zeile is not None, "ohne Zeile gibt es keinen Nachweis"
    assert zeile.entscheidung == "erteilt"
    assert zeile.marketing is True
    assert zeile.fassung == "kpg-consent-v1", "Zustimmung wozu? Ohne Fassung wertlos"


def test_die_ablehnung_wird_genauso_festgehalten_wie_die_zustimmung(
        client, aufraeumen):
    """Sonst belegt die Tabelle nur, was ohnehin niemand bestreitet.

    Der Streitfall ist nicht „hat er zugestimmt", sondern „habt ihr sein Nein
    beachtet". Eine Tabelle, die nur Zustimmungen kennt, beantwortet die
    zweite Frage nicht.
    """
    kennung = _kennung("0002")
    aufraeumen.append(kennung)

    client.post("/api/widget/einwilligung", json={
        "nachweis": kennung, "entscheidung": "abgelehnt", "marketing": False})

    zeile = _zeile(kennung)
    assert zeile is not None
    assert zeile.entscheidung == "abgelehnt"
    assert zeile.marketing is False


def test_unbekannt_ist_nicht_abgelehnt(client, aufraeumen):
    """Die Unterscheidung, derentwegen es die Tabelle gibt.

    `unbekannt` heisst: Die Traegerseite hat nichts gesagt — kein Dialog, oder
    der Besucher hat ihn stehen lassen. Wer das zu „nein" zusammenfasst,
    verliert genau die Ursachentrennung, die hier gesucht wird, und repariert
    danach am Dialog herum, obwohl der In-App-Browser das Problem ist.
    """
    kennung = _kennung("0003")
    aufraeumen.append(kennung)

    client.post("/api/widget/einwilligung", json={
        "nachweis": kennung, "entscheidung": "unbekannt"})

    zeile = _zeile(kennung)
    assert zeile.entscheidung == "unbekannt"
    assert zeile.marketing is None, "None heisst nicht mitgeteilt, False hiesse Nein"
    assert zeile.statistik is None


# ── Dass nichts doppelt gezaehlt wird ─────────────────────────────────

def test_die_zweite_meldung_aktualisiert_die_erste(client, aufraeumen):
    """Das Widget meldet zweimal: beim Laden und nach dem Klick im Dialog.

    Ohne Zusammenfuehrung ueber die Kennung zaehlte jeder Entschluss doppelt —
    und zwar ausgerechnet bei denen, die zustimmen, denn nur die aendern ihren
    Stand nachtraeglich. Die Quote saehe dadurch besser aus, als sie ist.
    """
    kennung = _kennung("0004")
    aufraeumen.append(kennung)

    client.post("/api/widget/einwilligung", json={
        "nachweis": kennung, "entscheidung": "unbekannt"})
    client.post("/api/widget/einwilligung", json={
        "nachweis": kennung, "entscheidung": "erteilt", "marketing": True})

    db = SessionLocal()
    try:
        zeilen = db.query(Einwilligung).filter(
            Einwilligung.nachweis == kennung).all()
    finally:
        db.close()

    assert len(zeilen) == 1, "eine Kennung, ein Seitenaufruf, eine Zeile"
    assert zeilen[0].entscheidung == "erteilt"


# ── Was die Zeile nicht enthalten darf ────────────────────────────────

def test_gespeichert_wird_das_netz_und_nicht_die_adresse():
    """Diese Tabelle nimmt auch die auf, die abgelehnt haben.

    Wer Tracking ablehnt und dafuer eine vollstaendig gespeicherte Adresse
    bekommt, ist schlechter dran als vorher.

    **Die Abwesenheitszusicherung steht nicht allein:** Direkt daneben wird
    geprueft, dass das Netz sehr wohl ankommt. Ein `netz_von`, das immer ""
    liefert, wuerde die erste Haelfte bestehen und waere wertlos.
    """
    assert nw.netz_von("203.0.113.45") == "203.0.113.0/24"
    assert "203.0.113.45" not in nw.netz_von("203.0.113.45")

    assert nw.netz_von("2001:db8:1234:5678::1") == "2001:db8:1234::/48"
    assert nw.netz_von("kein-ip") == "", "unlesbar heisst leer, nicht Absturz"


def test_von_der_einbettenden_seite_bleibt_nur_der_host(client, aufraeumen):
    """Der Pfad kann Suchbegriffe und Kennungen tragen.

    Fuer die Frage „wessen Dialog war das" traegt er nichts bei — und was
    nicht gespeichert wird, kann nicht abfliessen.
    """
    kennung = _kennung("0005")
    aufraeumen.append(kennung)

    client.post("/api/widget/einwilligung", json={
        "nachweis": kennung, "entscheidung": "erteilt",
        "seite": "https://websprint.kompagnon.eu/angebot/geheim?q=waermepumpe#analyse"})

    zeile = _zeile(kennung)
    assert zeile.seite == "websprint.kompagnon.eu", "Host ja"
    assert "waermepumpe" not in zeile.seite
    assert "geheim" not in zeile.seite


# ── Der In-App-Browser, wegen dessen die Messung ueberhaupt laeuft ────

def test_instagram_wird_nicht_als_facebook_gezaehlt():
    """Die Reihenfolge der Pruefung ist die ganze Aussage.

    Instagram-Kennungen tragen **auch** `FBAV`, weil beide Apps dieselbe
    Grundlage benutzen. Wer zuerst auf Facebook prueft, zaehlt jeden
    Instagram-Aufruf als Facebook — und genau diese Aufteilung ist die Frage.
    """
    instagram = ("Mozilla/5.0 (iPhone; CPU iPhone OS 16_6_1 like Mac OS X) "
                 "Mobile/20G81 Instagram 446.0.0.28.66 (iPhone13,3; IABMV/1)")
    facebook = ("Mozilla/5.0 (Linux; Android 15; 25078RA3EE) "
                "Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/577.0.0.50.72;IABMV/1;]")

    assert nw.app_browser_von(instagram) == "instagram"
    assert nw.app_browser_von(facebook) == "facebook"
    assert nw.app_browser_von(
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/153.0.0.0") == ""


# ── Der oeffentliche Endpunkt als Angriffsflaeche ─────────────────────

def test_eine_unsinnige_kennung_legt_nichts_an(client):
    """Der Endpunkt ist oeffentlich und schreibt Zeilen.

    Er antwortet auf Unsinn mit 204 statt 422: Wer ihn abklopft, soll nicht
    lernen, welche Form angenommen wird. Entscheidend ist aber, dass **nichts
    entsteht** — eine freundliche Antwort auf eine Zeile, die trotzdem
    geschrieben wird, waere das Schlechteste aus beidem.
    """
    db = SessionLocal()
    try:
        vorher = db.query(Einwilligung).count()
    finally:
        db.close()

    for unsinn in ({"nachweis": "kurz", "entscheidung": "erteilt"},
                   {"nachweis": "../../etc/passwd", "entscheidung": "erteilt"},
                   {"nachweis": _kennung("0009"), "entscheidung": "vielleicht"}):
        assert client.post("/api/widget/einwilligung", json=unsinn).status_code == 204

    db = SessionLocal()
    try:
        assert db.query(Einwilligung).count() == vorher
    finally:
        db.close()


# ── Der Lesepfad ──────────────────────────────────────────────────────

def test_die_auswertung_haengt_hinter_der_anmeldung(client):
    """Wer eingewilligt und wer abgelehnt hat, geht die Oeffentlichkeit nichts an."""
    assert client.get("/api/widget/einwilligung/auswertung").status_code in (401, 403)


def test_die_auswertung_nennt_alle_drei_entscheidungen(client, auth_headers,
                                                        aufraeumen):
    """Auch die mit null Treffern.

    Ein fehlender Schluessel liest sich wie „nicht erhoben". Hier ist die Null
    gemessen, und die Unterscheidung war in diesem Projekt schon mehrfach
    teuer (`null_ist_nicht_nichts`).
    """
    kennung = _kennung("0010")
    aufraeumen.append(kennung)
    client.post("/api/widget/einwilligung", json={
        "nachweis": kennung, "entscheidung": "erteilt", "marketing": True})

    antwort = client.get("/api/widget/einwilligung/auswertung",
                         headers=auth_headers)
    assert antwort.status_code == 200
    daten = antwort.json()

    assert set(daten["entscheidungen"]) == {"erteilt", "abgelehnt", "unbekannt"}
    assert daten["meldungen"] >= 1
    assert daten["zustimmungsquote"] is not None


def test_ohne_meldungen_ist_die_quote_nicht_erhoben_und_nicht_null(
        client, auth_headers):
    """Ein Zeitraum ohne eine einzige Meldung.

    `0.0` hiesse „niemand hat zugestimmt" und waere eine Aussage ueber die
    Besucher. Richtig ist: Es wurde nichts gemessen.
    """
    antwort = client.get(
        "/api/widget/einwilligung/auswertung?von=2020-01-01&bis=2020-01-02",
        headers=auth_headers)

    assert antwort.status_code == 200
    assert antwort.json()["meldungen"] == 0
    assert antwort.json()["zustimmungsquote"] is None


def test_ein_unlesbares_datum_wird_abgewiesen(client, auth_headers):
    antwort = client.get("/api/widget/einwilligung/auswertung?von=gestern",
                         headers=auth_headers)
    assert antwort.status_code == 400
