"""Wo ein Betrieb im Trichter steht — getrennt davon, wie weit die Bearbeitung ist.

Aus dem HubSpot-Vergleich (`docs/hubspot-vorbild-darstellung.md`): Dort sind es
zwei Felder. **Lifecycle-Phase** sagt, wo jemand im Trichter steht;
**Leadstatus** sagt, wie weit die Bearbeitung innerhalb dieser Phase ist. Bei
uns beantwortete `Lead.status` beides gleichzeitig — und deshalb keines von
beidem richtig.

Nachgemessen am 19.08.2026. Der Wortschatz (`utils/leadStatus.js`) mischt die
zwei Achsen sichtbar:

    new  contacted  qualified  proposal_sent  won  lost  customer
    └─ wo ─┘└──────── wie weit ────────┘└─ wo ─┘└ wo ┘└─ wo ─┘

Was das kostet, steht an zwei Stellen im Quelltext:

    automations.py:104   leads_won = ... filter(Lead.status == "won").count()
    projects.py:364      filter(Lead.status == "won", ~Lead.projects.any())

Beide beantworten „ist das ein Kunde?" durch **Aufzaehlung** — und beide
uebersehen `customer`, den der Bildschirm anbietet und den `PATCH` per
`setattr` klaglos schreibt. Ein Betrieb, den jemand von Hand auf „Kunde"
gesetzt hat, zaehlt in keiner Kennzahl mit.

Die Phase macht daraus **eine** Frage mit **einer** Antwort. Der Status bleibt
unveraendert daneben stehen; niemand verliert etwas.

**Unbekannte Werte bekommen keine Phase.** `None` heisst „nicht einzuordnen",
und die Oberflaeche zeigt das. Ein unbekannter Status still nach
„Interessent" zu schieben waere genau die Tarnung, die [[ux_methode_krug]]
verbietet — auf Staging stand ein Betrieb mit `opt_in`, der in keiner Kachel
auftauchte, und **der dreissigste war weder zu sehen noch zu finden**.
"""
from typing import Optional

#: Wo im Trichter. Reihenfolge ist die des Vertriebswegs.
INTERESSENT = "interessent"
IM_GESPRAECH = "im_gespraech"
KUNDE = "kunde"
AUSGESCHIEDEN = "ausgeschieden"

PHASEN = (INTERESSENT, IM_GESPRAECH, KUNDE, AUSGESCHIEDEN)

#: Beschriftungen fuer die Oberflaeche — hier, damit sie nicht auseinanderlaufen.
PHASEN_LABEL = {
    INTERESSENT: "Interessent",
    IM_GESPRAECH: "Im Gespräch",
    KUNDE: "Kunde",
    AUSGESCHIEDEN: "Ausgeschieden",
}

#: Status → Phase. Abgeleitet aus dem Wortschatz, der wirklich vorkommt:
#: die sieben aus `utils/leadStatus.js` plus `opt_in` aus dem Widget.
PHASE_ZU_STATUS = {
    "new": INTERESSENT,
    "opt_in": INTERESSENT,          # Widget-Anmeldung, Doppel-Opt-in bestaetigt
    "contacted": IM_GESPRAECH,
    "qualified": IM_GESPRAECH,
    "proposal_sent": IM_GESPRAECH,
    "won": KUNDE,
    "customer": KUNDE,
    "lost": AUSGESCHIEDEN,
}


def phase_zu(status: Optional[str]) -> Optional[str]:
    """Die Phase zu einem Status — oder ``None``, wenn er unbekannt ist.

    Kein leerer Status ist ein Fehler: Ein Betrieb ohne Status ist ein neuer
    Betrieb, und die Vorgabe der Spalte ist ``new``.

    Ein **unbekannter** Status bekommt bewusst keine Phase. Er soll auffallen,
    nicht verschwinden.
    """
    if not status:
        return INTERESSENT
    return PHASE_ZU_STATUS.get(str(status).strip().lower())


def ist_kunde(status: Optional[str]) -> bool:
    """Die eine Frage, die vorher eine Aufzaehlung war."""
    return phase_zu(status) == KUNDE
