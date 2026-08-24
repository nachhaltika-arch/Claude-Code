"""Eine Seite, die erst im Browser entsteht, wird nicht als leer gemessen.

**Gefunden am 24.08.2026 beim Probelauf von `tools/klassenlauf.py`** — gegen
die eigene Produktivoberflaeche, nicht gegen eine fremde Seite. Sie meldete
**11 Woerter**. Die Erhebung holt HTML ueber `httpx` und fuehrt kein
JavaScript aus; von einer React-Anwendung sieht sie
`<div id="root"></div>` und sonst nichts.

**Warum das mehr ist als ein schiefer Wert.** Der Bericht schrieb
`se_struktur` mit 0 von 2 und `se_lokal` mit 0 von 3 — beide als **gemessen**.
Das ist keine Luecke der Erhebung, sondern eine Aussage ueber den Betrieb:
„keine Ueberschriftenstruktur, keine lokalen Signale". Beides kann stimmen
oder auch nicht; gesehen hat es niemand. Genau diese Verwechslung ist die
Fehlerfamilie, die dieses Projekt schon zweimal getroffen hat — ein
geratener Wert an einer Stelle, die wie ein Befund gelesen wird.

Der Standard hat fuer diesen Fall bereits eine Antwort (§ 3.5): Was nicht
erhoben wurde, faellt aus Zaehler **und** Nenner. Es fehlte nur die
Erkennung.
"""
from bs4 import BeautifulSoup

from services.audit_collectors import clientseitig_aufgebaut

HUELLE = (
    '<!doctype html><html lang="de"><head><title>KOMPAGNON | KAS</title>'
    '<script defer src="/static/js/main.js"></script></head>'
    '<body><noscript>JavaScript wird benoetigt.</noscript>'
    '<div id="root"></div></body></html>'
)

ECHTE_SEITE = (
    '<html lang="de"><head><title>Muster Sanitaer GmbH — Heizung in Koblenz</title>'
    '</head><body><h1>Heizung, Sanitaer und Waermepumpen in Koblenz</h1>'
    '<p>' + ("Wir montieren und warten Heizungsanlagen im Raum Koblenz. " * 12) +
    '</p></body></html>'
)


def _pruefe(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    return clientseitig_aufgebaut(soup, len(soup.get_text(" ").split()))


def test_die_leere_huelle_einer_react_anwendung_wird_erkannt():
    assert _pruefe(HUELLE) is True


def test_eine_echte_seite_wird_nicht_faelschlich_erkannt():
    assert _pruefe(ECHTE_SEITE) is False


def test_eine_kurze_seite_ohne_einhaengepunkt_gilt_als_gemessen():
    """Wenig Text allein reicht nicht.

    Eine duenne Startseite ist ein **Befund**, keine Messluecke. Nur die
    Verbindung aus fast keinem Text **und** einem leeren Einhaengepunkt sagt,
    dass der Inhalt anderswo entsteht.
    """
    assert _pruefe('<html><body><h1>Kontakt</h1><p>Rufen Sie an.</p></body></html>') is False


def test_ein_gefuellter_einhaengepunkt_zaehlt_nicht():
    """Serverseitig vorgerendert (Next.js, Nuxt) — der Text ist da.

    Ein `<div id="__next">` mit Inhalt ist genau der Fall, den die Erhebung
    korrekt sieht. Wer hier abbricht, verliert richtige Messungen.
    """
    html = ('<html><body><div id="__next"><h1>Dachdecker Meier</h1><p>'
            + ("Wir decken Daecher in Trier und Umgebung. " * 12) +
            '</p></div></body></html>')
    assert _pruefe(html) is False
