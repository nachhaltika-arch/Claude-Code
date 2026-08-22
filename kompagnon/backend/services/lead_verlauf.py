"""Was bei einem Betrieb zuletzt geschah — aus fuenf Tabellen an eine Stelle (L-82).

**Warum es das braucht.** Die Ereignisse eines Betriebs liegen verstreut:
Analysen in `audit_results`, Projekte in `projects`, Briefings in `briefings`,
und Mails gleich in **zwei** Protokollen. Keine Stelle fuehrte sie zusammen.
Auf der Betriebsseite hiess das: Wer beim Anruf sehen will, was zuletzt war,
klickt sich durch drei Reiter — und sieht es deshalb nicht.

**Die Dublette.** `email_logs` und `communications` kennen einander nicht; am
17.08.2026 wurde deshalb zweimal der falsche Absender beschuldigt. Dieselbe
Mail steht oft in beiden. Sie zweimal zu zeigen laedt dazu ein, zweimal
denselben Schluss zu ziehen — also wird sie zu **einem** Ereignis
zusammengefasst, das **beide** Quellen nennt. Wer der Sache nachgeht, weiss
dann, wo er nachsehen kann.

**Fehlende Tabellen sind der Normalfall, nicht die Ausnahme.** Ein Teil des
Schemas entsteht erst beim Start in `migrations_runtime.py`. Auf einer frischen
Datenbank fehlt `email_logs` — daran ist die CI am 22.08. schon einmal rot
geworden. Jede Quelle wird darum einzeln geprueft; faellt eine aus, fehlt sie
im Verlauf und reisst ihn nicht mit.
"""
import logging
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

log = logging.getLogger("lead_verlauf")

#: Wie viele Ereignisse hoechstens zurueckkommen. Der Verlauf steht neben der
#: Seite, nicht auf ihr — mehr als das liest dort niemand.
VERLAUF_MAX = 50


def tabelle_vorhanden(db: Session, name: str) -> bool:
    """Ob es die Tabelle in dieser Datenbank gibt."""
    return name in set(inspect(db.get_bind()).get_table_names())


def _zeit(wert):
    """Zeitstempel als Text — oder nichts, wenn keiner da ist.

    Ein Ereignis ohne Zeitpunkt laesst sich nicht einsortieren; es gehoert
    weggelassen, nicht auf „jetzt" geraten.
    """
    return wert.isoformat() if wert else None


def _minute(zeitpunkt: str) -> str:
    """Der Zeitpunkt auf die Minute genau — der Schluessel fuer die Dublette.

    Sekundengenau zu vergleichen ginge daneben: Die beiden Protokolle
    schreiben ihren Zeitstempel jeweils selbst, kurz nacheinander.
    """
    return zeitpunkt[:16] if zeitpunkt else ""


def _abfragen(db: Session, lead_id: int) -> list:
    """Je Quelle eine Abfrage. Faellt eine aus, fehlt nur sie."""
    ereignisse = []

    def sammeln(name: str, sql: str, bauen, tabelle: str = None):
        if tabelle and not tabelle_vorhanden(db, tabelle):
            return
        try:
            for zeile in db.execute(text(sql), {"id": lead_id}).fetchall():
                ereignis = bauen(zeile)
                if ereignis and ereignis["zeitpunkt"]:
                    ereignisse.append(ereignis)
        except Exception as fehler:  # noqa: BLE001 — eine Quelle darf ausfallen
            log.warning("Verlauf: Quelle %s uebersprungen — %s: %s",
                        name, type(fehler).__name__, fehler)

    sammeln("audits", "SELECT created_at, total_score FROM audit_results "
                      "WHERE lead_id = :id ORDER BY created_at DESC LIMIT 20",
            lambda z: {"art": "audit", "zeitpunkt": _zeit(z[0]),
                       "titel": f"Analyse durchgeführt (Score {z[1]})" if z[1] is not None
                                else "Analyse durchgeführt",
                       "quellen": ["audit_results"]},
            tabelle="audit_results")

    # `projects` hat keine Namensspalte — der Status ist das, was den Stand
    # sagt. Wer hier `name` erwartet, bekommt eine stille Fehlmessung: Die
    # Abfrage faellt aus, die Quelle fehlt, und nichts meldet es.
    sammeln("projekte", "SELECT created_at, status FROM projects "
                        "WHERE lead_id = :id ORDER BY created_at DESC LIMIT 20",
            lambda z: {"art": "projekt", "zeitpunkt": _zeit(z[0]),
                       "titel": "Projekt angelegt", "hinweis": z[1],
                       "quellen": ["projects"]},
            tabelle="projects")

    sammeln("briefings", "SELECT created_at FROM briefings "
                         "WHERE lead_id = :id ORDER BY created_at DESC LIMIT 5",
            lambda z: {"art": "briefing", "zeitpunkt": _zeit(z[0]),
                       "titel": "Briefing eingegangen", "quellen": ["briefings"]},
            tabelle="briefings")

    sammeln("email_logs", "SELECT sent_at, subject, status FROM email_logs "
                          "WHERE lead_id = :id ORDER BY sent_at DESC LIMIT 20",
            lambda z: {"art": "email", "zeitpunkt": _zeit(z[0]),
                       "titel": f"E-Mail: {z[1]}" if z[1] else "E-Mail versendet",
                       "hinweis": z[2], "quellen": ["email_logs"]},
            tabelle="email_logs")

    # Das zweite Mail-Protokoll haengt am Projekt, nicht am Betrieb — deshalb
    # der Umweg ueber `projects`.
    sammeln("communications",
            "SELECT c.sent_at, c.subject, c.type, c.direction FROM communications c "
            "JOIN projects p ON p.id = c.project_id "
            "WHERE p.lead_id = :id ORDER BY c.sent_at DESC LIMIT 20",
            lambda z: {"art": "email" if z[2] == "email" else "kontakt",
                       "zeitpunkt": _zeit(z[0]),
                       "titel": (f"E-Mail: {z[1]}" if z[2] == "email" and z[1]
                                 else f"{(z[2] or 'Kontakt').capitalize()}"
                                      f"{' (eingehend)' if z[3] == 'inbound' else ''}"),
                       "quellen": ["communications"]},
            tabelle="communications")

    return ereignisse


def _dubletten_zusammenfuehren(ereignisse: list) -> list:
    """Gleiche Art, gleicher Titel, gleiche Minute → ein Ereignis, zwei Quellen."""
    zusammen = {}
    for ereignis in ereignisse:
        schluessel = (ereignis["art"], ereignis["titel"], _minute(ereignis["zeitpunkt"]))
        vorhanden = zusammen.get(schluessel)
        if vorhanden is None:
            zusammen[schluessel] = {**ereignis, "quellen": list(ereignis["quellen"])}
            continue
        for quelle in ereignis["quellen"]:
            if quelle not in vorhanden["quellen"]:
                vorhanden["quellen"].append(quelle)
    return list(zusammen.values())


def verlauf_bauen(db: Session, lead, limit: int = 20) -> dict:
    """Der Verlauf eines Betriebs, neuestes zuerst.

    Das Anlegen des Betriebs steht immer dabei und ist der Anker ganz unten:
    Ab hier gibt es ihn überhaupt.
    """
    grenze = max(1, min(limit, VERLAUF_MAX))

    ereignisse = _dubletten_zusammenfuehren(_abfragen(db, lead.id))
    ereignisse.sort(key=lambda e: e["zeitpunkt"], reverse=True)

    anker = {"art": "angelegt", "zeitpunkt": _zeit(lead.created_at),
             "titel": "Betrieb angelegt", "quellen": ["leads"]}

    # Der Anker zaehlt gegen die Grenze, steht aber immer da — sonst endet ein
    # langer Verlauf im Nichts, und niemand sieht, seit wann es den Betrieb gibt.
    if anker["zeitpunkt"]:
        return {"lead_id": lead.id,
                "ereignisse": ereignisse[:grenze - 1] + [anker],
                "gesamt": len(ereignisse) + 1}

    return {"lead_id": lead.id, "ereignisse": ereignisse[:grenze],
            "gesamt": len(ereignisse)}
