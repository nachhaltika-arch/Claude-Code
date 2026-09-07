# -*- coding: utf-8 -*-
"""Was alle Portalmodule gemeinsam brauchen.

**Am 07.09.2026 aus `routers/portal.py` herausgeloest (L-25).** Die Datei war
auf 1.630 Zeilen gewachsen, doppelt ueber der Grenze — und der groesste Teil
dieses Wachstums stammt aus den Sitzungen vom 06. und 07.09.: Kundenkonto,
Mitwirkung, Dazubuchen, Zugaenge. Geschnitten ist nach **Zustaendigkeit**,
nicht nach Groesse; dasselbe Vorgehen wie bei `academy.py` am 23.08.

Hier steht nur, was mehr als ein Modul braucht. **Ein eigener Ort dafuer ist
der Punkt und nicht Ordnungsliebe:** Laege `verlangt_geldblick` weiterhin in
`portal.py` und importierte `portal_geld` es von dort, waeren die beiden
gegenseitig abhaengig — und die Ladereihenfolge entschiede darueber, ob der
Dienst startet.
"""
import logging

from fastapi import Depends, HTTPException

from routers.auth_router import get_current_user

logger = logging.getLogger(__name__)


# ── Phase metadata ────────────────────────────────────────────────

PHASE_META = [
    (1, "Kickoff & Strategie",    "Ziele, Zielgruppe und Sitemap definiert"),
    (2, "Texterstellung",          "Alle Seiteninhalte verfasst und freigegeben"),
    (3, "Design & Mockup",         "Startseite & Unterseiten im Design-Tool"),
    (4, "Entwicklung",             "Technische Umsetzung im CMS"),
    (5, "SEO & GEO-Optimierung",  "Meta-Tags, Ladezeit, lokale Sichtbarkeit"),
    (6, "Review & Freigabe",       "Gemeinsame Abnahme aller Seiten"),
    (7, "Go-live & Übergabe",      "Domain live schalten, Einweisung, Support"),
]

STATUS_LABEL = {
    "phase_1": "Kickoff läuft",    "phase_2": "Texterstellung",
    "phase_3": "Design & Mockup",  "phase_4": "In Entwicklung",
    "phase_5": "SEO & Optimierung","phase_6": "Review",
    "phase_7": "Go-live",          "completed": "Abgeschlossen",
}


def _phase_number(status: str) -> int:
    for i in range(1, 8):
        if status == f"phase_{i}":
            return i
    return 7 if status == "completed" else 1


def _customer_id(user) -> int:
    """Stable identifier for a customer's portal data."""
    return user.lead_id if user.lead_id else user.id


#
# **Die Zahlungsart aendert er bei Stripe, nicht bei uns.** Ein eigenes
# Kartenformular hiesse, Kartendaten durch unseren Server zu fuehren. Stripes
# Billing-Portal ist dafuer da; wir erzeugen eine Sitzung und leiten weiter.


# ── Wer darf ans Geld? (L-160 Rang 4) ─────────────────────────────────
#
# **Steht hier oben, weil drei Bloecke darunter sie brauchen** — Zahlungen,
# Vertragsunterlagen und Rechnungen. FastAPI wertet die Abhaengigkeit beim
# Import aus; eine Sperre, die spaeter in der Datei steht, gibt es zu dem
# Zeitpunkt noch nicht.


def _stufe(user) -> str:
    from services.kundenzugang import stufe_von
    return stufe_von(user)


def verlangt_geldblick(user=Depends(get_current_user)):
    """Sperrt die schwache Stufe vor Rechnungen, Zahlungsart und Unterlagen.

    **Ohne diese Sperre waere die Stufe eine Behauptung.** Der Entwurf sagt
    dem Betrieb zu: „sieht alles ausser Rechnungen, Zahlungsart und
    Vertragsunterlagen." Steht die Zusage im Konto und wirkt nicht, ist sie
    schlimmer als keine — der Betrieb hat dann im guten Glauben jemandem
    Einblick gegeben, den er ausdruecklich ausschliessen wollte.
    """
    from services.kundenzugang import darf_geld_sehen

    if not darf_geld_sehen(_stufe(user)):
        raise HTTPException(
            403, "Dieser Zugang darf keine Rechnungen und Zahlungsdaten sehen")
    return user
