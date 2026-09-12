# -*- coding: utf-8 -*-
"""Die fertige Berichtsseite: Vorlage + Daten + Hülle (L-191, 10.09.2026).

**Warum es die Hülle als eigenes Stück gibt.** Der Entwurf kommt als
Ausschnitt: kein Wurzelelement, kein Kopf, keine Schrift. Seine Grundstile lagen
im `<helmet>`-Block des Exports, der beim Auspacken wegfällt, weil er
Bündel-Adressen für Schriftdateien enthält, die es im Betrieb nicht gibt.

**Der erste Durchlauf sah deshalb falsch aus**, und zwar auf eine Art, die
man leicht für „Vorlage kaputt" hält: Die Seite rendert vollständig und
richtig, nur in der Serifen-Vorgabe des Browsers statt in Noto Sans. Die
Lehre ist dieselbe wie beim Lagebild — was am Gegenstand geprüft wird,
zeigt Dinge, die kein Test sieht.

Die Grundstile hier sind **die des Entwurfs**, Zeile für Zeile übernommen:
Hintergrund, Schriftfamilie, Linkfarben und die beiden Regeln, die den
Aufklapp-Pfeil ohne Browser-Dreieck darstellen.
"""
import logging
import pathlib

logger = logging.getLogger(__name__)

VORLAGE = pathlib.Path(__file__).resolve().parent.parent / "vorlagen" / "bericht.html"

#: Genau die Familien, die der Entwurf benutzt. Über dieselbe Quelle wie das
#: Lagebild — eine zweite Schriftquelle wäre ein zweites Ladeverhalten.
SCHRIFTEN = ("https://fonts.googleapis.com/css2?"
             "family=Noto+Sans:ital,wght@0,400;0,500;0,700;0,900;1,400"
             "&family=DM+Mono:wght@400;500&display=swap")

#: Aus dem `<helmet>` des Entwurfs übernommen.
GRUNDSTIL = """
  body { margin:0; background:#F0F4F5;
         font-family:'Noto Sans',system-ui,-apple-system,'Segoe UI',Roboto,
                     Helvetica,Arial,sans-serif;
         color:#000; -webkit-font-smoothing:antialiased; }
  a { color:#008EAA; }
  a:hover { color:#004F59; }
  summary { list-style:none; cursor:pointer; }
  summary::-webkit-details-marker { display:none; }
  .chev { transform:rotate(180deg); }
"""


def _huelle(rumpf: str, titel: str) -> str:
    return (
        "<!doctype html>\n<html lang=\"de\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        # Kein Index: Die Seite steht hinter einem Token aus einer E-Mail und
        # trägt den Befund über die Website eines Betriebs.
        "<meta name=\"robots\" content=\"noindex,nofollow\">\n"
        f"<title>{titel}</title>\n"
        "<link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">\n"
        "<link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>\n"
        f"<link rel=\"stylesheet\" href=\"{SCHRIFTEN}\">\n"
        f"<style>{GRUNDSTIL}</style>\n</head>\n<body>\n{rumpf}\n</body>\n</html>"
    )


def rendern(db, audit, token: str = "", einstellungen: dict = None) -> str:
    """Die vollständige Seite für einen Befund."""
    from services import bericht_daten, bericht_vorlage
    from services.widget_report import report_url

    einstellungen = einstellungen or {}
    daten = bericht_daten.aufbauen(db, audit, einstellungen)

    # **Die Ziele der Knöpfe stehen nicht im Entwurf.** Er trägt zwei feste
    # Stripe-Zahllinks und eine feste Terminadresse — dieselbe Falle wie im
    # Teaser: ein Kaufweg im Quelltext, der die Kasse umgeht, und eine
    # Adresse, die kein Mensch mehr findet, wenn sie sich ändert.
    # `terminUrl` bildet `bericht_daten`, weil die Kaufwege darauf
    # zurueckfallen und ihn deshalb schon brauchen.
    daten["pdfUrl"] = f"{report_url(token)}/pdf" if token else ""

    vorlage = VORLAGE.read_text(encoding="utf-8")
    rumpf = bericht_vorlage.rendern(vorlage, daten)
    return _huelle(rumpf, f"Ihr Befund — {daten.get('firma') or 'KOMPAGNON'}")
