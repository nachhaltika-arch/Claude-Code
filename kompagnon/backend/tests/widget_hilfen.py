"""Gemeinsame Helfer der Widget-Tests (L-25).

**Warum eigene Datei, 23.08.2026.** `test_widget.py` hatte 901 Zeilen und ist
in drei geteilt. `_anfrage_anlegen` wird von zweien davon gebraucht — und ist
**keine** Fixture, also injiziert pytest sie nicht ueber `conftest.py`. Eine
Kopie in beiden Dateien waere genau das Duplikat, das heute anderswo schon
einen Fehler verdeckt hat.

Die drei Fixtures (`aufraeumen`, `fremde_analyse`, `gesendete_mails`) stehen
dagegen in `conftest.py` — dort holt pytest sie von selbst.
"""
from database import SessionLocal, WidgetRequest


def _anfrage_anlegen(email, audit_id, aufraeumen, **felder):
    aufraeumen.append(email)
    db = SessionLocal()
    try:
        row = WidgetRequest(
            email=email, website_url="https://interner-interessent.example",
            audit_id=audit_id, verify_token=felder.pop("verify_token", "v-tok"),
            report_token=felder.pop("report_token", "r-tok"),
            poll_token=felder.pop("poll_token", "p-tok"), **felder)
        db.add(row)
        db.commit()
        return row.id
    finally:
        db.close()


def _beleg(token: str) -> str:
    """Der Wert, den die Seite erst bei einer echten Geste mitschickt.

    Seit dem 17.08.2026 traegt er den Zeitpunkt seiner Ausgabe und gilt erst
    nach einer Wartezeit — sonst genuegte es, die Seite zu lesen und den Wert
    sofort zurueckzuschicken. Genau das tun Postfach-Scanner.

    Die Tests stellen ihn deshalb rueckdatiert aus. Ohne diese Zeile wuerden
    sie die neue Huerde messen statt das, was sie pruefen wollen.
    """
    import time

    from services import widget_report

    return widget_report.gestenbeleg(
        token, zeitpunkt=time.time() - (widget_report.BELEG_MINDESTALTER_S + 1))
