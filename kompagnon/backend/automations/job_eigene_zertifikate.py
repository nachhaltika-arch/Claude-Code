# -*- coding: utf-8 -*-
"""Die eigenen Domains in die Ablaufüberwachung (B1.14e).

**Kriterium S1 gilt für uns selbst.** Der Standard vergibt drei Punkte für ein
gültiges Zertifikat mit einer Restlaufzeit von dreißig Tagen oder mehr — und
setzt eine Website ohne gültiges Zertifikat auf *Nicht konform*, unabhängig von
allen anderen Punkten.

**Überwacht wurden bis zum 25.08.2026 nur Kundenprojekte.**
`job_check_netlify_ssl` liest die Tabelle `projects`; unsere eigenen Adressen
stehen dort nicht, weil sie keine Projekte sind. Dasselbe Muster wie bei
L-121, wo die eigene Seite die Artefakte nicht bekam, die wir verkaufen.

**Warum eigener Abruf und nicht die Netlify-Auskunft.** Die drei Adressen
liegen nicht alle bei Netlify, und die Frage lautet ohnehin anders: nicht „hat
der Anbieter ein Zertifikat ausgestellt", sondern „was sieht ein Besucher".
Gemessen wird deshalb an der Adresse — mit demselben Prüfer, den das Audit
für fremde Seiten benutzt.
"""
import asyncio
import logging

logger = logging.getLogger(__name__)

#: Unsere eigenen Adressen. Der Buchtitel und die beiden Werkzeugadressen —
#: alle drei stehen gedruckt im Buch oder in Angeboten und dürfen nicht
#: stillschweigend ablaufen.
EIGENE_DOMAINS = (
    "https://homepage-standard.de",
    "https://homepagestandard.de",
    "https://kas.kompagnon.group",
)

#: Ab wann gewarnt wird. Dieselbe Grenze wie im Kriterium S1: Wer unter
#: dreißig Tagen liegt, bekommt dort einen Punkt Abzug.
WARNGRENZE_TAGE = 30


def job_eigene_zertifikate_pruefen() -> list:
    """Prüft die eigenen Adressen und meldet, was bald abläuft."""
    from services import audit_collectors as collectors

    befunde = []
    for adresse in EIGENE_DOMAINS:
        try:
            befund = asyncio.run(asyncio.to_thread(collectors.check_tls, adresse))
        except Exception as fehler:  # noqa: BLE001
            logger.warning("Zertifikatsprüfung für %s gescheitert: %s", adresse, fehler)
            befunde.append({"domain": adresse, "collected": False,
                            "grund": str(fehler)[:120]})
            continue

        tage = befund.get("days_left")
        eintrag = {"domain": adresse, "collected": bool(befund.get("collected")),
                   "gueltig": bool(befund.get("valid")), "tage": tage}
        befunde.append(eintrag)

        if not befund.get("collected"):
            # Nicht erreichbar ist nicht dasselbe wie abgelaufen — und wird
            # deshalb auch nicht so gemeldet.
            logger.info("Zertifikat %s: nicht erhoben (%s)", adresse,
                        befund.get("reason", "unbekannt"))
        elif not befund.get("valid"):
            logger.error("🔴 Eigene Domain ohne gültiges Zertifikat: %s — nach "
                         "unserem eigenen Maßstab wäre das 'Nicht konform'", adresse)
        elif tage is not None and tage < WARNGRENZE_TAGE:
            logger.warning("Eigene Domain %s: Zertifikat läuft in %s Tagen ab — "
                           "unter der Grenze von %s (Kriterium S1)",
                           adresse, tage, WARNGRENZE_TAGE)
        else:
            logger.info("Zertifikat %s: gültig, %s Tage Restlaufzeit", adresse, tage)

    return befunde
