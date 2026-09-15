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

#: Woher eine Zahl in dieser Auswertung stammt — Entscheidung E17 des
#: Vertriebsplans („Kennzeichnung GEMESSEN / ERFAHREN / ANGENOMMEN, ueberall").
#:
#: **Warum das hier keine Formsache ist.** Neben sechs gemessenen Stufen
#: sieht eine angenommene Zahl aus wie eine gemessene. Der Vertriebsplan vom
#: 15.09.2026 rechnet einen Monat durch — rund 60 Leads, 42 Scores, 4
#: Gespraeche, 2 Check PLUS — und **keine** dieser Zahlen ist erhoben. Wer
#: sie ohne Kennzeichen danebenstellt, hat aus einer Planung eine Messung
#: gemacht, ohne dass es jemand beschlossen haette.
GEMESSEN, ANGENOMMEN = "gemessen", "angenommen"

#: Die Quelle aller Annahmen unten. Sie steht an jeder einzelnen, nicht nur
#: hier: Eine Annahme, deren Herkunft man erst suchen muss, wird beim
#: naechsten Lesen fuer eine Messung gehalten.
PLANQUELLE = "Vertriebsplan 15.09.2026, Rechenbeispiel (angenommen)"

#: Wo eine Planquote sich gegen eine **gemessene** Stufe halten laesst.
#: Heute gibt es genau eine: Der Plan rechnet mit 20 bis 40 Prozent Verlust
#: im Double-Opt-in, also bleiben 60 bis 80 Prozent uebrig.
#:
#: Die Spanne gehoert an die Stufe, nicht in den Kopf der Ansicht: „unter
#: Erwartung" ist eine Aussage ueber **diesen** Schritt.
ERWARTUNG_VORSTUFE = {
    "bestaetigt": (60.0, 80.0),
}

#: Was der Plan **nach** der letzten gemessenen Stufe erwartet. Gerechnet
#: wird auf der gemessenen Basis, nicht die Planzahl angezeigt: Neben drei
#: zugestellten Berichten stuende sonst eine 60 aus dem Plan, und niemand
#: wuesste, worauf sie sich bezieht.
#:
#: (Schluessel, Klartext, Basisstufe, Quote in Prozent, Hinweis)
ANNAHMEN = (
    ("gespraech", "15-Minuten-Gespräch", "bericht_versendet", 10.0,
     "rund 10 % der zugestellten Berichte"),
    ("check_plus", "Check PLUS", "gespraech", 50.0,
     "rund die Hälfte der Gespräche"),
    ("auftrag", "Relaunch oder Neubau", "check_plus", 50.0,
     "0 bis 1 je Monat, innerhalb von 6 Monaten nach Check PLUS"),
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
    erreicht_je_stufe = {}
    for schluessel, name, feld in STUFEN:
        anzahl = sum(1 for zeile in zeilen if erreicht(zeile, feld))
        anteil_vorstufe = (None if vorherige is None
                           else _anteil(anzahl, vorherige))
        von, bis = ERWARTUNG_VORSTUFE.get(schluessel, (None, None))
        stufen.append({
            "schluessel": schluessel,
            "name": name,
            "anzahl": anzahl,
            "art": GEMESSEN,
            "anteil_gesamt": _anteil(anzahl, gesamt),
            # Die erste Stufe hat keine Vorstufe — nicht 100 %, sondern nichts.
            "anteil_vorstufe": anteil_vorstufe,
            "erwartet_von": von,
            "erwartet_bis": bis,
            # **Ohne Vorstufe wird nicht gewarnt.** Sonst meldet eine leere
            # Ansicht „unter Erwartung" — ein Alarm ueber nichts, und der
            # naechste echte wird dann nicht mehr gelesen.
            "unter_erwartung": bool(von is not None
                                    and anteil_vorstufe is not None
                                    and vorherige
                                    and anteil_vorstufe < von),
        })
        erreicht_je_stufe[schluessel] = anzahl
        vorherige = anzahl

    # **Die Annahmen rechnen auf dem Gemessenen.** Jede Stufe nimmt die
    # vorige als Basis — auch wenn die selbst schon eine Annahme ist. Dann
    # steht das in `basis` und die Kennzeichnung traegt es weiter.
    angenommen, werte = [], dict(erreicht_je_stufe)
    for schluessel, name, basis, quote, hinweis in ANNAHMEN:
        grundlage = werte.get(basis)
        # **Ohne Basis bleibt es leer, nicht 0.** Null hiesse „der Plan
        # erwartet keinen Termin"; richtig ist „es gibt nichts, worauf sich
        # die Quote beziehen koennte".
        erwartet = None if not grundlage else round(grundlage * quote / 100.0, 1)
        werte[schluessel] = erwartet or 0
        angenommen.append({
            "schluessel": schluessel,
            "name": name,
            "art": ANGENOMMEN,
            "erwartet": erwartet,
            "basis": basis,
            "quote": quote,
            "hinweis": hinweis,
            "herkunft": PLANQUELLE,
        })

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
        "angenommen": angenommen,
        "nicht_erhoben": [
            {"schluessel": s, "name": n, "grund": g} for s, n, g in NICHT_ERHOBEN
        ],
    }
