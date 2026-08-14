"""Was der Projekt-Assistent sehen darf — und was nicht.

Entscheidung 3.4 aus `docs/projekt-assistent-anforderungen.md`: Für jeden Modus
steht hier ausdrücklich, welche Felder in den Kontext geladen werden. Alles
andere erreicht das Modell nie.

Der Grund ist konkret: Marge, Stundensatz, KI-Kosten, geleistete Stunden und
interne Notizen hängen am selben `Project`- und `Lead`-Datensatz wie die
Angaben, die der Kunde sehen darf. Eine Anweisung im Prompt („erwähne keine
Preise") ist keine Grenze — sie ist eine Bitte. Eine Feldliste ist eine Grenze.

**Die wichtigste Eigenschaft: Neue Felder sind unsichtbar.** Wer morgen eine
Spalte `deckungsbeitrag` ergänzt, hat sie nicht versehentlich im Kundenkontext,
sondern muss sie hier bewusst freigeben.
"""
from typing import Any, Dict, Optional

MODUS_KUNDE = "kunde"
MODUS_TEAM = "team"

# `auditor` ist im Backend nicht abgegrenzt (`require_auditor` ist definiert,
# aber an keiner Route eingehängt) — § 2.1 der Anforderungen nennt das als offen.
# Bis das entschieden ist, gilt die engere Sicht. Wer mehr sehen soll, wird hier
# ausdrücklich eingetragen.
ROLLEN_MIT_TEAMSICHT = frozenset({"admin", "superadmin"})

# ── Die Freigabelisten ──────────────────────────────────────────────────
#
# Je Bereich: welches Attribut am Objekt wird unter welchem Namen übernommen.

_BETRIEB_KUNDE = {
    "company_name": "firma",
    "city": "ort",
    "trade": "gewerk",
}
_BETRIEB_TEAM = {
    **_BETRIEB_KUNDE,
    "email": "email",
    "phone": "telefon",
    "lead_score": "lead_score",
}

# Das Briefing ist die Arbeitsgrundlage des Assistenten — hier ist alles
# freigegeben, weil der Nutzer es selbst ausfüllt.
_BRIEFING_FELDER = (
    "gewerk", "leistungen", "einzugsgebiet", "usp", "mitbewerber", "vorbilder",
    "farben", "wunschseiten", "stil", "hauptziel", "aktionen", "typischer_kunde",
    "haeufige_anfrage",
)

_PROJEKT_KUNDE = {
    "id": "id",
    "status": "status",
}
_PROJEKT_TEAM = {
    **_PROJEKT_KUNDE,
    "fixed_price": "fixed_price",
    "hourly_rate": "hourly_rate",
    "actual_hours": "actual_hours",
    "ai_tool_costs": "ai_tool_costs",
    "margin_percent": "margin_percent",
    "target_go_live": "target_go_live",
}

_AUDIT_FELDER = {
    "score": "score",
    "level": "level",
}

FREIGABE = {
    MODUS_KUNDE: {"betrieb": _BETRIEB_KUNDE, "projekt": _PROJEKT_KUNDE},
    MODUS_TEAM: {"betrieb": _BETRIEB_TEAM, "projekt": _PROJEKT_TEAM},
}


def modus_fuer_rolle(rolle: Optional[str]) -> str:
    """Der Modus kommt aus der Rolle des angemeldeten Nutzers — nie vom Client.

    Alles, was nicht ausdrücklich Teamsicht hat, bekommt die Kundensicht.
    """
    return MODUS_TEAM if (rolle or "") in ROLLEN_MIT_TEAMSICHT else MODUS_KUNDE


def _uebernehmen(objekt: Any, liste: Dict[str, str]) -> Dict[str, Any]:
    """Nur was in der Liste steht, und nur wenn es einen Wert hat."""
    if objekt is None:
        return {}
    ergebnis = {}
    for attribut, name in liste.items():
        wert = getattr(objekt, attribut, None)
        if wert is None or wert == "":
            continue
        ergebnis[name] = wert
    return ergebnis


def baue_kontext(modus: str, *, lead=None, briefing=None, projekt=None,
                 audit=None) -> Dict[str, Any]:
    """Der vollständige Kontext für einen Assistenten-Aufruf.

    Wirft bei unbekanntem Modus — lieber ein Fehler als versehentlich die weite
    Sicht.
    """
    if modus not in FREIGABE:
        raise ValueError(f"Unbekannter Modus '{modus}' — erlaubt: "
                         f"{', '.join(sorted(FREIGABE))}")
    listen = FREIGABE[modus]

    briefing_werte, offen = {}, []
    for feld in _BRIEFING_FELDER:
        wert = getattr(briefing, feld, None) if briefing is not None else None
        if wert is None or str(wert).strip() == "":
            offen.append(feld)
        else:
            briefing_werte[feld] = wert

    return {
        "modus":          modus,
        "betrieb":        _uebernehmen(lead, listen["betrieb"]),
        "briefing":       briefing_werte,
        # Was noch fehlt, ist die Hauptaufgabe des Assistenten — also gehört es
        # ausdrücklich in den Kontext und nicht als Leerstelle.
        "briefing_offen": offen,
        "projekt":        _uebernehmen(projekt, listen["projekt"]),
        "audit":          _uebernehmen(audit, _AUDIT_FELDER),
    }
