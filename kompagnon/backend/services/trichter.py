# -*- coding: utf-8 -*-
"""Der Trichter als Zusammenfassung — welche Stufe leckt (L-192).

**Der Befund vom 10.09.2026.** Jede Zeile in `widget_requests` traegt alle
Stufen als Zeitstempel, und `GET /api/acquisition/widget/requests` gibt sie
einzeln aus. Was fehlte, war die Zusammenfassung. Ohne sie steht nach zwei
Wochen Budget nicht fest, **welche Stufe leckt** — und die Entscheidung ueber
die naechste Kampagne faellt auf Gefuehl statt auf Zahlen.

**Was diese Datei nicht tut, und warum das die wichtigere Haelfte ist.**

*Sie erfindet keine Null.* Die Klicks auf die Anzeige stehen bei Meta, die
gebuchten Termine im Google-Kalender. Beides erfaehrt dieses System nicht.
Eine `0` an dieser Stelle laese sich als „niemand hat geklickt" lesen — eine
Falschaussage ueber den Erfolg einer bezahlten Kampagne. Sie stehen deshalb
unter `nicht_erhoben`, **mit Grund**, und nicht als Stufe. Dieselbe Regel wie
in L-165 und im Audit: 0 heisst „geprueft und nicht erfuellt", fehlend heisst
„nicht erhoben".

*Sie rechnet keine Quote aus nichts.* Ohne Anfragen im Zeitraum bleiben die
Anteile `None`. „0 %" hiesse, es sei gemessen worden und niemand kam durch.

*Sie verschweigt nicht, wenn die Grundgesamtheit zu klein ist.* Bei drei
Anfragen ist „33 % Abbruch" eine Zahl ohne Aussage; wer danach ein Budget
verschiebt, entscheidet auf Rauschen. `zu_wenig_daten` sagt es mit.
"""
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

#: Standardzeitraum. Vier Wochen: lang genug fuer eine Kampagnenrunde, kurz
#: genug, dass eine Aenderung an der Strecke sich noch abbildet.
STANDARD_TAGE = 30

#: Ab wann eine Quote ueberhaupt etwas behauptet. Keine statistische Groesse,
#: sondern eine Anstandsgrenze: Darunter wird die Zahl **mit Warnung**
#: gezeigt, nicht verschwiegen — verschwiegen waere sie erst recht ein Raetsel.
MINDESTZAHL = 20

#: Die Stufen des Trichters, in der Reihenfolge, in der sie durchlaufen
#: werden. Je Stufe: Schluessel, Klartext, und das Feld, dessen Vorhandensein
#: sie belegt (``None`` = alle Zeilen, also die Grundgesamtheit).
#:
#: **`analyse_fertig` haengt an der Erhebung, nicht am Mailversand.** Die
#: naheliegende Abkuerzung waere `verify_sent_at` gewesen — die Mail geht nur
#: nach einer fertigen Analyse raus. Dann truege die Stufe aber zwei Aussagen
#: auf einmal, und ein Mailproblem saehe aus wie eine gescheiterte Erhebung.
#: Genau diese Verwechslung war L-184.
STUFEN = (
    ("angefragt", "Analyse angefordert", None),
    ("analyse_fertig", "Analyse durchgelaufen", "audit_completed"),
    ("bestaetigung_angefragt", "Bestätigung angefragt", "verify_sent_at"),
    ("bestaetigt", "Adresse bestätigt", "verified_at"),
    ("bericht_versendet", "Bericht versendet", "report_sent_at"),
    ("bericht_geoeffnet", "Bericht geöffnet", "report_confirmed_at"),
)

#: Was zum Trichter gehoert und hier nicht gemessen werden **kann**.
NICHT_ERHOBEN = (
    ("anzeigenklicks", "Klicks auf die Anzeige",
     "Steht bei Meta und in GA4, nicht in diesem System. Erst ab der "
     "Landingpage wird hier etwas sichtbar."),
    ("termine", "Gebuchte Termine",
     "Der Terminkalender liegt bei Google; eine Buchung dort meldet sich "
     "nicht zurück. Gezählt werden kann nur, wer den Bericht geöffnet hat."),
)


def _anteil(zaehler: int, nenner: int):
    """Prozent auf eine Stelle — oder ``None``, wenn nichts zu teilen ist."""
    if not nenner:
        return None
    return round(zaehler * 100.0 / nenner, 1)


def auswerten(db, tage: int = STANDARD_TAGE, jetzt: datetime = None,
              nur_anzeige: bool = False) -> dict:
    """Die Stufen des Trichters mit Anzahl und Anteil.

    `nur_anzeige` schraenkt auf Anfragen ein, die mit einer Klickkennung
    ankamen — die einzige Herkunft, die sich von hier aus trennen laesst.
    """
    from modelle_audit import AuditResult
    from modelle_widget import WidgetRequest

    jetzt = jetzt or datetime.utcnow()
    ab = jetzt - timedelta(days=int(tage))

    abfrage = db.query(WidgetRequest).filter(WidgetRequest.created_at >= ab)
    if nur_anzeige:
        abfrage = abfrage.filter(WidgetRequest.aus_anzeige.is_(True))
    zeilen = abfrage.all()

    # **Eine Abfrage fuer alle Analysestaende**, nicht eine je Zeile. Dieselbe
    # Form wie in `acquisition._analysestaende` (L-184) — dort war sie noetig,
    # um die Anfrageliste nicht in N+1 Abfragen zu verwandeln.
    kennungen = {z.audit_id for z in zeilen if z.audit_id}
    fertige = set()
    if kennungen:
        fertige = {
            k for (k,) in db.query(AuditResult.id)
            .filter(AuditResult.id.in_(kennungen),
                    AuditResult.status == "completed").all()
        }

    def erreicht(zeile, feld) -> bool:
        if feld is None:
            return True
        if feld == "audit_completed":
            return zeile.audit_id in fertige
        return getattr(zeile, feld, None) is not None

    gesamt = len(zeilen)
    stufen, vorherige = [], None
    for schluessel, name, feld in STUFEN:
        anzahl = sum(1 for zeile in zeilen if erreicht(zeile, feld))
        stufen.append({
            "schluessel": schluessel,
            "name": name,
            "anzahl": anzahl,
            "anteil_gesamt": _anteil(anzahl, gesamt),
            # Die erste Stufe hat keine Vorstufe — nicht 100 %, sondern nichts.
            "anteil_vorstufe": None if vorherige is None
            else _anteil(anzahl, vorherige),
        })
        vorherige = anzahl

    return {
        "zeitraum_tage": int(tage),
        "von": ab.isoformat() + "Z",
        "bis": jetzt.isoformat() + "Z",
        "grundgesamtheit": gesamt,
        "aus_anzeige": sum(1 for zeile in zeilen if zeile.aus_anzeige),
        "nur_anzeige": bool(nur_anzeige),
        "zu_wenig_daten": gesamt < MINDESTZAHL,
        "mindestzahl": MINDESTZAHL,
        "stufen": stufen,
        "nicht_erhoben": [
            {"schluessel": s, "name": n, "grund": g} for s, n, g in NICHT_ERHOBEN
        ],
    }
