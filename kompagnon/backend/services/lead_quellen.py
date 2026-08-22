"""Woher ein Betrieb kam — und unter welcher Rechtsgrundlage wir ihn fuehren.

Luecke L-59, gemessen am 21.08.2026. Der Befund hat zwei Haelften.

**Erste Haelfte: Wir pruefen, was wir selbst nicht fuehren.**
`services/audit_collectors.py:255` sucht auf fremden Seiten nach „Art. 6",
`services/netlify_service.py:531` schreibt sie in erzeugte Kundenseiten,
`services/pdf_generator.py:427` druckt eine Spalte dafuer. Am eigenen Lead:
79 Felder, keines nennt sie. Dieselbe Form wie L-17 — wir verkaufen die
Pruefung und bestehen sie selbst nicht.

**Zweite Haelfte: Der Wortschatz, an dem sie haengen muesste, ist ungefuehrt.**
Im Quelltext gezaehlt, was tatsaechlich geschrieben wird:

    embed_audit      routers/widget.py:186
    stripe_checkout  routers/payments.py:323, main.py:1386
    domain_import    routers/leads.py:482
    landing_audit    routers/leads.py:783  (Vorgabe; der Aufrufer darf ueber-
                                            schreiben — Freitext aus einem
                                            oeffentlichen Endpunkt)
    csv_import       routers/leads.py:1296
    Manuell          routers/leads.py:1354  (grosses M, deutsch — als einziger)
    trackdesk        routers/webhooks_trackdesk.py:224
    HWK-<Kammer>     services/hwk_scraper.py:249  (zusammengesetzt)
    facebook · linkedin · google · postkarte · telefon
                     routers/webhooks.py:107-162 ueber `_upsert_lead`
    <Kampagnenname>  routers/kampagne.py:126  (Freitext)

Dagegen `AUTO_SEQUENCE_SOURCES` in `routers/leads.py:181` — die Liste, die
entscheidet, wer eine automatische Mailstrecke bekommt:

    stripe_checkout · landing_audit · landing_page · llm_landing · postkarte
    webhook_facebook · webhook_linkedin · webhook_google

**Fuenf der acht Werte werden nirgends geschrieben** (`NIE_GESCHRIEBEN`).
`postkarte` steht in beiden Listen, greift aber trotzdem nicht: Die Webhooks
schreiben ueber `_upsert_lead` mit rohem SQL und laufen an `create_lead`
vorbei, wo die Liste gelesen wird.

**Was dieses Modul entscheidet — und was nicht.**

`herkunft` ist eine **Tatsache aus dem Quelltext**: Hat die Person sich selbst
gemeldet, oder haben wir sie gesammelt? Das laesst sich am schreibenden Pfad
ablesen und ist keine Rechtsauskunft.

`rechtsgrundlage` ist eine **Rechtsauskunft**. Eingetragen ist deshalb nur der
eine Fall, der sich nicht auslegen laesst: Bei `stripe_checkout` entsteht der
Lead in `_handle_successful_payment`, also **nach** abgeschlossener Zahlung —
dass ein Vertrag besteht, ist keine Auslegung. Alles Uebrige steht auf `None`
und laesst sich ueber `quellen_ohne_rechtsgrundlage()` auflisten.

Das ist dieselbe Entscheidung wie bei der Lebenszyklus-Phase und bei der
Kennungs-Nachfuehrung (L-54): **Raten waere schlimmer als nichts tun.** Ein
geratener Eintrag hier waere eine Rechtsbehauptung ueber fremde Daten, und er
saehe genauso aus wie eine gepruefte.
"""
from typing import Optional

# ── Herkunft: belegbar am schreibenden Pfad ──────────────────────────

#: Die Person hat sich selbst gemeldet — Formular, Kauf, Rueckruf, Lead-Ad.
EINGEHEND = "eingehend"

#: Wir haben die Daten gesammelt, ohne dass jemand danach gefragt hat.
KALTAKQUISE = "kaltakquise"

HERKUENFTE = (EINGEHEND, KALTAKQUISE)

HERKUNFT_LABEL = {
    EINGEHEND: "Selbst gemeldet",
    KALTAKQUISE: "Von uns erhoben",
}

# ── Rechtsgrundlage nach Art. 6 Abs. 1 DSGVO ─────────────────────────

EINWILLIGUNG = "art6_1_a"            # lit. a
VERTRAG = "art6_1_b"                 # lit. b, auch vorvertraglich
BERECHTIGTES_INTERESSE = "art6_1_f"  # lit. f

RECHTSGRUNDLAGE_LABEL = {
    EINWILLIGUNG: "Art. 6 Abs. 1 lit. a — Einwilligung",
    VERTRAG: "Art. 6 Abs. 1 lit. b — Vertrag oder vorvertragliche Massnahme",
    BERECHTIGTES_INTERESSE: "Art. 6 Abs. 1 lit. f — berechtigtes Interesse",
}

#: Was in der Oberflaeche steht, solange niemand entschieden hat. Der Wert
#: soll auffallen, nicht wie eine Antwort aussehen.
OFFEN_LABEL = "Rechtsgrundlage offen"


def _quelle(name: str, herkunft: str, rechtsgrundlage: Optional[str] = None,
            beleg: str = "") -> dict:
    return {
        "name": name,
        "herkunft": herkunft,
        "rechtsgrundlage": rechtsgrundlage,
        "beleg": beleg,
    }


#: Der gefuehrte Wortschatz. Schluessel = Wert in `leads.lead_source`.
QUELLEN = {
    "embed_audit": _quelle(
        "Analyse-Widget", EINGEHEND,
        beleg="routers/widget.py:186 — die Person traegt ihre Adresse selbst "
              "ein und bittet um die Analyse. Der Marketing-Haken wird "
              "getrennt in `WidgetRequest.consent_marketing` protokolliert; "
              "der Lead entsteht auch ohne ihn.",
    ),
    "stripe_checkout": _quelle(
        "Kauf", EINGEHEND, VERTRAG,
        beleg="routers/payments.py:323 — der Lead entsteht in "
              "`_handle_successful_payment`, also nach abgeschlossener "
              "Zahlung. Ein Vertrag besteht nachweislich.",
    ),
    "landing_audit": _quelle(
        "Landingpage", EINGEHEND,
        beleg="routers/leads.py:783 — Vorgabe des oeffentlichen Endpunkts. "
              "Der Aufrufer darf den Wert ueberschreiben.",
    ),
    "domain_import": _quelle(
        "Domain-Import", KALTAKQUISE,
        beleg="routers/leads.py:482 — aus einer Adressliste erzeugt, niemand "
              "hat sich gemeldet.",
    ),
    "csv_import": _quelle(
        "CSV-Import", KALTAKQUISE,
        beleg="routers/leads.py:1296 — Datei-Import durch den Innendienst.",
    ),
    "facebook": _quelle(
        "Facebook Lead-Ad", EINGEHEND,
        beleg="routers/webhooks.py:107 ueber `_upsert_lead`.",
    ),
    "linkedin": _quelle(
        "LinkedIn Lead-Ad", EINGEHEND,
        beleg="routers/webhooks.py:121 ueber `_upsert_lead`.",
    ),
    "google": _quelle(
        "Google Lead-Formular", EINGEHEND,
        beleg="routers/webhooks.py:135 ueber `_upsert_lead`.",
    ),
    "postkarte": _quelle(
        "Postkarten-Ruecklauf", EINGEHEND,
        beleg="routers/webhooks.py:148 ueber `_upsert_lead`.",
    ),
    "telefon": _quelle(
        "Telefonische Meldung", EINGEHEND,
        beleg="routers/webhooks.py:162 ueber `_upsert_lead`.",
    ),
    "trackdesk": _quelle(
        "Partner (Trackdesk)", EINGEHEND,
        beleg="routers/webhooks_trackdesk.py:224 — ueber einen Partner-Link "
              "gekommen.",
    ),
    "manual": _quelle(
        "Von Hand angelegt", EINGEHEND,
        beleg="BetriebAnlegenModal.jsx:65, CustomerProjects.jsx:167 und "
              "routers/leads.py:1354. Wer von Hand anlegt, weiss woher die "
              "Daten kommen; das Feld sagt es nicht.",
    ),
    "audit": _quelle(
        "Aus dem Audit-Werkzeug", EINGEHEND,
        beleg="AuditTool.jsx:409 — im Innendienst aus einer geprueften "
              "Adresse erzeugt.",
    ),
    "isb_impuls": _quelle(
        "ISB-Impuls", EINGEHEND,
        beleg="CustomerProjects.jsx:315.",
    ),
}

#: Zwei Schreibweisen fuer dieselbe Sache — gemessen am 21.08.2026.
#:
#: `routers/leads.py:1354` schrieb **`Manuell`** (deutsch, grosses M), waehrend
#: drei Frontend-Stellen **`manual`** schreiben. Der Quellenfilter der
#: Betriebsliste prueft `b.lead_source === 'manual'`
#: (`utils/betriebeListe.js:83`) — ein von der Backend-Seite von Hand
#: angelegter Betrieb war ueber „Von Hand" **nicht zu finden**. Er bekam
#: stattdessen eine eigene Gruppe „Manuell" und sah aus wie eine eigene
#: Quelle. Genau die Tarnung, die [[ux_methode_krug]] verbietet.
#:
#: Dasselbe bei `Audit` gegen `audit`.
#:
#: Die Zuordnung wird beim Lesen angewandt **und** einmalig auf den Bestand
#: (`migrations_runtime.py::run_migrations`), damit alte Zeilen nicht auf ewig danebenstehen.
SCHREIBWEISEN = {
    "Manuell": "manual",
    "Audit": "audit",
}

#: Bewusst **nicht** hier: `HWK-<Kammer>` aus `services/hwk_scraper.py:249`
#: und die Kampagnennamen aus `routers/kampagne.py:126`. Sie tragen eine
#: Information im Wert selbst — welche Kammer, welche Kampagne — und sind
#: damit Freitext, kein verrutschter Wortschatz. Sie geben sich ueber
#: `quelle_bekannt() == False` als ungefuehrt zu erkennen, und das ist richtig.

#: Werte, die gelesen, aber **nirgends geschrieben** werden. Gemessen am
#: 21.08.2026 gegen `AUTO_SEQUENCE_SOURCES` (`routers/leads.py:181`).
#: Sie stehen hier, damit niemand sie fuer gefuehrte Quellen haelt — und
#: damit sichtbar bleibt, dass diese Liste zu fuenf Achteln ins Leere greift.
NIE_GESCHRIEBEN = (
    "landing_page",
    "llm_landing",
    "webhook_facebook",
    "webhook_linkedin",
    "webhook_google",
)


def normalisiere(quelle: Optional[str]) -> Optional[str]:
    """Eine Schreibweise je Sache — `Manuell` und `manual` sind dasselbe."""
    if not quelle:
        return None
    return SCHREIBWEISEN.get(quelle, quelle)


def herkunft_fuer(quelle: Optional[str]) -> Optional[str]:
    """Selbst gemeldet oder von uns erhoben — `None`, wenn ungefuehrt.

    Freitext (Kampagnennamen wie `HWK-Muenchen`) ist gewollt und bekommt
    bewusst keine Herkunft: Er soll sich als ungefuehrt zu erkennen geben,
    statt in eine Klasse gedraengt zu werden.
    """
    eintrag = QUELLEN.get(normalisiere(quelle))
    return eintrag["herkunft"] if eintrag else None


def rechtsgrundlage_fuer(quelle: Optional[str]) -> Optional[str]:
    """Die Rechtsgrundlage, **sofern sie im Code belegt ist** — sonst `None`."""
    eintrag = QUELLEN.get(normalisiere(quelle))
    return eintrag["rechtsgrundlage"] if eintrag else None


def quelle_bekannt(quelle: Optional[str]) -> bool:
    return normalisiere(quelle) in QUELLEN


def quellen_ohne_rechtsgrundlage() -> list:
    """Die Liste, die David zu entscheiden hat — sortiert, damit sie sich
    Zeile fuer Zeile abarbeiten laesst."""
    return sorted(s for s, q in QUELLEN.items() if q["rechtsgrundlage"] is None)


def label_rechtsgrundlage(wert: Optional[str]) -> str:
    """Beschriftung — auch fuer den offenen Fall, der sichtbar bleiben soll."""
    if not wert:
        return OFFEN_LABEL
    return RECHTSGRUNDLAGE_LABEL.get(wert, wert)
