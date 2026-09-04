# -*- coding: utf-8 -*-
"""Der Audit sieht erst hin, wenn die Vorschau wirklich da ist (L-40).

**Der Befund (27.08.2026, erster gelungener Durchstich).** Nachdem der
Netlify-Token endlich trug, lief der Deploy — und der Audit scheiterte
trotzdem. Im Protokoll liegen die Zeilen **dreihundert Millisekunden**
auseinander:

    20:28:39.386  POST …/sites/…/deploys        → 200 OK
    20:28:39.692  GET  …--kompagnon-vorschau…   → 500
    20:28:41      Audit 92 fehlgeschlagen: Website nicht erreichbar (Status 500)

Ein `curl` zwei Minuten spaeter bekam **200**. Die Seite war in Ordnung; der
Audit hat zu frueh hingesehen.

**Warum das schlimmer ist als ein Fehler, der immer auftritt.** Der Ausgang
haengt an der Tagesform von Netlify — mal ist die Vorschau in einer Sekunde
da, mal in fuenf. Und der Bericht meldete „Website nicht erreichbar", also
einen **Befund ueber die Seite**, wo in Wirklichkeit unser eigener Ablauf zu
schnell war. Ein Kunde haette gelesen, seine Seite sei kaputt.
"""
import pytest

from services import qualitaetsschleife as qs


class _Antwort:
    def __init__(self, code):
        self.status_code = code

    @property
    def is_success(self):
        return 200 <= self.status_code < 300


class _Client:
    """Ein Netlify, das erst nach `bis_erfolg` Versuchen ausliefert."""

    def __init__(self, antworten):
        self.antworten = list(antworten)
        self.versuche = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def get(self, url):
        self.versuche += 1
        naechste = self.antworten.pop(0) if self.antworten else 200
        if isinstance(naechste, Exception):
            raise naechste
        return _Antwort(naechste)


@pytest.fixture(autouse=True)
def _schnell(monkeypatch):
    """Ohne das dauerte jeder Fehlerfall eine Minute."""
    monkeypatch.setattr(qs, "BEREIT_FRIST_SEKUNDEN", 0.1)
    monkeypatch.setattr(qs, "BEREIT_ABSTAND_SEKUNDEN", 0.01)


def _mit(antworten, monkeypatch) -> _Client:
    client = _Client(antworten)
    monkeypatch.setattr(qs.httpx, "AsyncClient", lambda **_: client)
    return client


# ── Der Normalfall ────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_ist_die_seite_da_wird_nicht_gewartet(monkeypatch):
    client = _mit([200], monkeypatch)

    await qs.warte_bis_abrufbar("https://vorschau.example")

    assert client.versuche == 1, "Ein Treffer, ein Versuch"


@pytest.mark.anyio
async def test_ein_fuenfhunderter_wird_abgewartet(monkeypatch):
    """**Der eigentliche Befund.** Genau diese Folge stand im Protokoll."""
    monkeypatch.setattr(qs, "BEREIT_FRIST_SEKUNDEN", 5.0)
    client = _mit([500, 500, 200], monkeypatch)

    await qs.warte_bis_abrufbar("https://vorschau.example")

    assert client.versuche == 3


@pytest.mark.anyio
async def test_auch_ein_verbindungsfehler_wird_abgewartet(monkeypatch):
    """Eine Netlify-Adresse, deren DNS noch nicht steht, wirft statt zu
    antworten — derselbe Fall, andere Form."""
    monkeypatch.setattr(qs, "BEREIT_FRIST_SEKUNDEN", 5.0)
    client = _mit([ConnectionError("kein DNS"), 200], monkeypatch)

    await qs.warte_bis_abrufbar("https://vorschau.example")

    assert client.versuche == 2


# ── Und die Grenze ────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_nach_der_frist_wird_es_gesagt(monkeypatch):
    """Endlos zu warten waere schlimmer als aufzugeben: Der Aufruf haengt,
    und niemand erfaehrt, woran."""
    _mit([500] * 50, monkeypatch)

    with pytest.raises(qs.VorschauKamNicht) as fehler:
        await qs.warte_bis_abrufbar("https://vorschau.example")

    assert "Status 500" in str(fehler.value)
    assert "Deploy lief" in str(fehler.value)


# ── Die Gegenprobe: das Warten haengt auch am Ablauf ──────────────────

@pytest.mark.anyio
async def test_der_deploy_wartet_wirklich(monkeypatch):
    """**Ohne diese Zusicherung waere die Funktion Zierrat.**

    Sie haelt fest, dass `deploye_vorschau` sie auch ruft — und zwar mit
    genau der Adresse, die es danach zurueckgibt. Genau diese Verbindung
    fehlte vor dem 27.08.
    """
    gewartet = []

    async def _falscher_deploy(**_):
        return {"deploy_url": "https://abc--vorschau.netlify.app",
                "deploy_id": "d1", "state": "new"}

    async def _mitschreiben(url):
        gewartet.append(url)

    monkeypatch.setattr(qs, "deploy_html", _falscher_deploy)
    monkeypatch.setattr(qs, "warte_bis_abrufbar", _mitschreiben)
    monkeypatch.setenv(qs.VORSCHAU_SITE_ENV, "site-123")

    class _Seite:
        id = 151
        gjs_html = "<h1>Inhalt</h1>"
        gjs_css = ""
        page_name = "Probe"
        ki_meta_description = ""

    url = await qs.deploye_vorschau(_Seite(), firmenname="Testbetrieb")

    assert gewartet == [url], "Es wurde nicht auf die zurueckgegebene Adresse gewartet"
