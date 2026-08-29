# -*- coding: utf-8 -*-
"""Wo verkaufte Dateien liegen — Cloudflare R2 (L-100, ORDERS_06).

**Die Entscheidung (David, 29.08.2026): R2.** ORDERS_06 hält den Bau davor an
und stellt drei Möglichkeiten zur Wahl. Der Grund, warum es überhaupt eine
Wahl ist:

**Das Dateisystem auf Render ist flüchtig.** Bei jedem Deploy wird der
Container neu gebaut. Ein Workbook, das in ein Verzeichnis auf dem Server
gelegt wird, ist nach dem nächsten Bugfix weg — und mit ihm die Abruf-Adressen
aller Käufer. Der Fehler tritt nicht beim Ablegen auf, sondern beim
übernächsten Deploy; das ist die Sorte, die niemand mit dem Ablegen in
Verbindung bringt.

**Netlify wäre die falsche Rettung.** Dort liegen die Kundenwebsites: Die
Datei läge öffentlich unter einer erratbaren Adresse — verkauftes Produkt,
frei abrufbar.

**Ein Datenträger an Render hätte einen zweiten Preis.** L-94 hält fest, dass
ein Dienst mit Datenträger nur **eine** Instanz haben darf und deshalb bei
jedem Deploy rund 40 Sekunden steht. Dieselbe Eigenschaft noch einmal
einzukaufen, nur für zwei PDF-Dateien, wäre teuer bezahlt.

**Warum signierte Adressen und kein eigener Auslieferungsweg.** Die Datei
durch das Backend zu reichen hieße, jeden Abruf über die Ereignisschleife zu
schicken — bei einem 20-MB-PDF ist das genau die Blockade, die am 18.08. an
zwölf Stellen behoben wurde. R2 liefert selbst aus; wir vergeben nur einen
Schlüssel mit Ablauf.

**Die Ablaufzeit ist kurz und gedeckelt.** Der Käufer bekommt nicht die
signierte Adresse per Mail, sondern einen Abruf-Link auf uns
(`/api/shop/download/{token}`), der dreißig Tage gilt; die signierte Adresse
entsteht erst beim Klick und lebt Minuten. Ein Link, der ein Jahr gilt, ist
kein signierter Link, sondern eine öffentliche Adresse mit Umweg.
"""
import logging
import os
from typing import List, Optional

logger = logging.getLogger(__name__)

#: Was R2 braucht. Die Reihenfolge ist die, in der Cloudflare sie anzeigt.
ERFORDERLICH = ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY",
                "R2_BUCKET")

#: Wie lange eine signierte Adresse höchstens gilt. Fünfzehn Minuten reichen
#: für einen Abruf und für einen zweiten Versuch, wenn der erste abbricht.
ABLAUF_MAX = 900

#: Vorgabe, wenn der Aufrufer nichts sagt.
ABLAUF_VORGABE = 300


def _wert(name: str) -> str:
    return os.getenv(name, "").strip()


def was_fehlt() -> List[str]:
    """Welche Zugangsdaten fehlen — sortiert, damit die Meldung stabil ist.

    **„Nicht eingerichtet" schickt niemanden an die richtige Stelle.** Diese
    Liste steht in der Protokollzeile und in der Antwort an den Innendienst.
    """
    return sorted(name for name in ERFORDERLICH if not _wert(name))


def ist_eingerichtet() -> bool:
    """Alle vier Werte da? Eine halbe Einrichtung ist keine.

    Sonst scheitert erst der Abruf des Käufers — also **nach** der Zahlung,
    und das ist der teuerste Zeitpunkt für einen Einrichtungsfehler.
    """
    return not was_fehlt()


def _klient():
    """Der S3-kompatible Zugang zu R2.

    Eigene Funktion, damit die Prüfungen sie ersetzen können, ohne
    Zugangsdaten zu brauchen — und damit der Import von `boto3` erst beim
    ersten wirklichen Abruf geschieht statt beim Start des Dienstes.
    """
    import boto3
    from botocore.config import Config

    return boto3.client(
        "s3",
        endpoint_url=f"https://{_wert('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
        aws_access_key_id=_wert("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=_wert("R2_SECRET_ACCESS_KEY"),
        # R2 verlangt `auto` als Region und SigV4 — mit der Vorgabe von boto3
        # scheitert die Signatur mit einer Meldung über die Region, die nicht
        # auf die Ursache zeigt.
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def signierte_adresse(schluessel: Optional[str],
                      sekunden: int = ABLAUF_VORGABE) -> Optional[str]:
    """Eine Adresse, unter der die Datei kurz abrufbar ist — oder `None`.

    **`None` statt einer Ausnahme.** Der Aufrufer entscheidet, wie er das
    meldet: Der Käufer bekommt 503 („noch nicht eingerichtet"), nicht 500 —
    er hat bezahlt, und ein Stapelabzug im Protokoll ist keine Aussage.

    **Ohne Dateikennung keine Adresse.** Ein Produkt, an dem keine Datei
    hinterlegt ist, bekäme sonst eine signierte Adresse auf den Wurzelpfad
    des Buckets.
    """
    if not schluessel or not str(schluessel).strip():
        return None

    fehlt = was_fehlt()
    if fehlt:
        logger.error("Dateiablage nicht eingerichtet — es fehlt: %s",
                     ", ".join(fehlt))
        return None

    dauer = max(1, min(int(sekunden), ABLAUF_MAX))

    try:
        return _klient().generate_presigned_url(
            "get_object",
            Params={"Bucket": _wert("R2_BUCKET"), "Key": str(schluessel).strip()},
            ExpiresIn=dauer,
        )
    except Exception as fehler:                          # noqa: BLE001
        logger.error("Signierte Adresse fuer %r nicht erzeugt: %s",
                     schluessel, fehler)
        return None
