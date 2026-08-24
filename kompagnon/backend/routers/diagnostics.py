"""
Betriebsdiagnose: welche Integrationen sind im laufenden Prozess konfiguriert?

Entstanden, weil sich nicht feststellen ließ, ob eine im Render-Dashboard
eingetragene Variable auch tatsächlich im Prozess ankommt. Ein leerer Wert
sieht im Dashboard aus wie „gesetzt", verhält sich im Code aber wie „fehlt".

Es werden ausschließlich Metadaten zurückgegeben — nie ein Wert. Die Länge
unterscheidet „nicht gesetzt" von „gesetzt, aber leer" und von „gesetzt, aber
offensichtlich zu kurz", ohne das Geheimnis preiszugeben.
"""
import os

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import User, get_db
from routers.auth_router import require_admin

router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])

# (Anzeigename, Umgebungsvariable, Zweck, alternative Schreibweisen)
WATCHED_SETTINGS = (
    ("PageSpeed Insights", "GOOGLE_PAGESPEED_API_KEY",
     "Performance und Barrierefreiheit im Website-Audit", ("PAGESPEED_API_KEY",)),
    ("Anthropic", "ANTHROPIC_API_KEY",
     "KI-Bewertung von Design, Conversion und Textqualität", ()),
    ("Datenbank", "DATABASE_URL", "Persistenz", ()),
    ("Brevo", "BREVO_API_KEY", "E-Mail-Versand", ()),
    ("Stripe", "STRIPE_SECRET_KEY", "Zahlungen", ()),
    ("Netlify", "NETLIFY_API_TOKEN", "Kunden-Hosting", ()),
)


def _describe(env_var: str, aliases: tuple = ()) -> dict:
    raw = os.getenv(env_var)
    if raw is None or not raw.strip():
        for alias in aliases:
            alt = os.getenv(alias)
            if alt and alt.strip():
                return {"status": "gesetzt (als " + alias + ")", "configured": True,
                        "length": len(alt.strip())}
    if raw is None:
        return {"status": "fehlt", "configured": False, "length": 0}
    if not raw.strip():
        return {"status": "leer", "configured": False, "length": len(raw)}
    return {"status": "gesetzt", "configured": True, "length": len(raw.strip())}


def _betriebsschalter() -> list:
    """Der **wirksame** Zustand der Schalter, die das Verhalten bestimmen.

    **Warum das nicht dieselbe Frage ist wie oben (L-104, 24.08.2026).**
    `_describe` meldet „gesetzt" oder „fehlt". Für einen Schalter ist das die
    falsche Auskunft: ``USE_MOCK_EMAIL=false`` ist **gesetzt** und bedeutet
    „versendet echt an Kunden".

    **Und genau darin lag der Fehler:** Die Umgebung sagte ``true``, der
    Scheduler setzte den Schalter beim Start auf ``False`` zurück. Wer nur die
    Umgebungsvariable liest, sieht das nie. Gelesen wird deshalb über
    ``probemodus()`` und ``scheduler_ist_eingeschaltet()`` — die Funktionen,
    an denen das Verhalten wirklich hängt.
    """
    from automations.scheduler import scheduler_ist_eingeschaltet
    from automations.versandmodus import probemodus

    probe = probemodus()
    zeit = scheduler_ist_eingeschaltet()
    return [
        {
            "name": "Mailversand",
            "env_var": "USE_MOCK_EMAIL",
            "wirksam": "Probemodus" if probe else "versendet echt",
            "bedeutung": (
                "Mails werden nur protokolliert, nicht zugestellt."
                if probe else
                "Mails gehen tatsaechlich an die hinterlegten Adressen."
            ),
        },
        {
            "name": "Zeitauftraege",
            "env_var": "SCHEDULER_ENABLED",
            "wirksam": "laeuft" if zeit else "abgeschaltet",
            "bedeutung": (
                "Der Scheduler fuehrt seine Jobs aus, darunter versendende."
                if zeit else
                "Dieser Dienst faehrt keine Hintergrundjobs."
            ),
        },
    ]


@router.get("/config")
def config_status(_: User = Depends(require_admin)):
    """Zeigt je Integration, ob der laufende Prozess sie sieht — ohne Werte."""
    settings = [
        {"name": name, "env_var": env_var, "purpose": purpose,
         **_describe(env_var, aliases)}
        for name, env_var, purpose, aliases in WATCHED_SETTINGS
    ]
    return {
        "settings": settings,
        "missing": [s["env_var"] for s in settings if not s["configured"]],
        "schalter": _betriebsschalter(),
    }


@router.get("/wiederherstellbarkeit")
def wiederherstellbarkeit(_: User = Depends(require_admin)):
    """Waere eine Wiederherstellung vollstaendig? (L-11)

    **Eine andere Frage als `/config`.** Dort geht es darum, ob eine
    Integration heute arbeitet. Hier darum, ob der Betrieb nach einem
    Datenverlust **zurueckzuholen** waere — und das haengt an Schluesseln, die
    im laufenden Betrieb monatelang niemand vermisst.

    Ohne `CREDENTIALS_KEY` bekommt man nach einer vollstaendigen
    Wiederherstellung einen laufenden Dienst mit unlesbaren Kundenzugaengen:
    kein Fehler, keine Meldung, nur leere Felder.

    Gibt **keine** Schluesselwerte zurueck, auch nicht gekuerzt.
    """
    from services.wiederherstellbarkeit import schluessel_bericht

    return schluessel_bericht()


# ── Drei Auskuenfte ueber die laufende Datenbank (L-53, L-106) ────────

#: Spalten, an denen eine offene Luecke haengt. Je Eintrag steht dabei, was
#: der eine und was der andere Befund bedeuten wuerde — eine Zahl ohne
#: Deutung wird beim Lesen falsch gedeutet.
VERDACHTSSPALTEN = (
    {
        "tabelle": "projects",
        "spalte": "start_date",
        "luecke": "L-53",
        "harmlos": "timestamp without time zone",
        "bedeutung_wenn_abweichend":
            "Ist die Spalte `timestamptz`, wirft "
            "`datetime.utcnow() - project.start_date` einen TypeError und "
            "nimmt die ganze Alarmliste mit — die gesuchte Ursache.",
    },
    {
        "tabelle": "time_tracking",
        "spalte": "hours",
        "luecke": "L-53",
        "harmlos": "NO",          # is_nullable
        "bedeutung_wenn_abweichend":
            "Ist die Spalte nullbar, kann `sum(entry.hours)` an einer "
            "NULL-Stunde scheitern — die zweite plausible Ursache.",
    },
)

#: Tabellen, deren blosse Zeilenzahl eine Frage beantwortet.
ZAEHLTABELLEN = (
    {
        "tabelle": "usercards",
        "luecke": "L-106",
        "bedeutung_wenn_leer":
            "Die Tabelle ist leer. `CustomerDashboard.jsx` liest sie ueber "
            "`/api/usercards/{lead_id}/profile` — jeder Kunde bekommt auf "
            "seiner Startseite einen 404.",
    },
    {"tabelle": "leads", "luecke": "", "bedeutung_wenn_leer": ""},
    {"tabelle": "customers", "luecke": "", "bedeutung_wenn_leer": ""},
)


def _spalte_lesen(db, tabelle: str, spalte: str) -> dict:
    from sqlalchemy import text

    zeile = db.execute(text("""
        SELECT data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = :t AND column_name = :s
    """), {"t": tabelle, "s": spalte}).fetchone()
    if not zeile:
        return {"vorhanden": False, "data_type": "", "is_nullable": ""}
    return {"vorhanden": True, "data_type": zeile[0], "is_nullable": zeile[1]}


@router.get("/schema")
def schema_bericht(_: User = Depends(require_admin),
                   db: Session = Depends(get_db)):
    """Form und Anzahl — nie ein Datenwert (L-53, L-106).

    **Warum es diesen Endpunkt gibt.** Zwei Luecken hingen am 24.08.2026 an
    je einer Zeile aus der Produktiv-Datenbank, und beide Wege dorthin waren
    zu: Das Render-Werkzeug scheitert am Verbindungsaufbau
    (`SSL/TLS required`), die Staging-Abfrage an der Berechtigung.

    Ein Lesekonto oder eine geoeffnete Inbound-Regel loeste die Frage einmal
    und **oeffnete die Datenbank dauerhaft** — gegen die Richtung von L-44.
    Dieser Endpunkt beantwortet genau die drei Fragen, hinter `require_admin`,
    und laesst sich wiederholen, wenn dieselbe Frage wieder aufkommt.

    Herausgegeben werden **Datentyp, Nullbarkeit und Zeilenzahl** — nichts,
    was einen Betrieb oder eine Person nennt.
    """
    from sqlalchemy import text

    spalten, hinweise = [], []
    for eintrag in VERDACHTSSPALTEN:
        befund = _spalte_lesen(db, eintrag["tabelle"], eintrag["spalte"])
        gemessen = (befund["data_type"] if eintrag["spalte"] == "start_date"
                    else befund["is_nullable"])
        weicht_ab = befund["vorhanden"] and gemessen != eintrag["harmlos"]
        spalten.append({
            "tabelle": eintrag["tabelle"],
            "spalte": eintrag["spalte"],
            "luecke": eintrag["luecke"],
            "erwartet_harmlos": eintrag["harmlos"],
            "gemessen": gemessen,
            "weicht_ab": weicht_ab,
            **befund,
        })
        if weicht_ab:
            hinweise.append(
                f"{eintrag['luecke']}: {eintrag['bedeutung_wenn_abweichend']}")

    zeilenzahlen = []
    for eintrag in ZAEHLTABELLEN:
        try:
            anzahl = db.execute(text(
                f"SELECT count(*) FROM {eintrag['tabelle']}"  # noqa: S608
            )).scalar()
        except Exception:
            anzahl = None
        zeilenzahlen.append({
            "tabelle": eintrag["tabelle"],
            "zeilen": anzahl,
            "luecke": eintrag["luecke"],
        })
        if eintrag["bedeutung_wenn_leer"] and anzahl == 0:
            hinweise.append(
                f"{eintrag['luecke']}: {eintrag['bedeutung_wenn_leer']}")

    # **Je Luecke ein Satz, auch wenn nichts auffaellt.** Ein Bericht, der
    # ueber eine Frage schweigt, laesst den Leser raten, ob sie ueberhaupt
    # geprueft wurde — dieselbe Sorte Luecke, die dieser Endpunkt schliesst.
    saetze = []
    l53 = [h for h in hinweise if h.startswith("L-53")]
    saetze.append(" ".join(l53) if l53 else (
        "L-53: Beide Verdachtsspalten haben die harmlose Form "
        "(`timestamp without time zone`, `hours NOT NULL`). Dann ist die "
        "Ursache der 500er eine dritte und noch zu suchen."
    ))
    l106 = [h for h in hinweise if h.startswith("L-106")]
    saetze.append(" ".join(l106) if l106 else (
        "L-106: `usercards` traegt Zeilen — das Kundendashboard findet "
        "also etwas."
    ))
    bewertung = " ".join(saetze)

    return {
        "spalten": spalten,
        "zeilenzahlen": zeilenzahlen,
        "bewertung": bewertung,
    }
