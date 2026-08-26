# -*- coding: utf-8 -*-
"""Die Hülle um eine Vorschau — einmal statt dreimal.

**Der Anlass (26.08.2026).** Dieselbe HTML-Hülle stand an drei Stellen fast
gleich: `portal.version_preview`, `projects_versionen.version_preview` und
`templates.get_preview`. Alle drei trugen `lang="de"` und **keinen** `<title>`.
Drei Kopien driften; hier waren sie noch gleich, und genau deshalb ist jetzt
der richtige Zeitpunkt, sie zusammenzulegen.

**Warum der Titel kein Beiwerk ist.** `document-title` ist eines der acht
Lighthouse-Kriterien, die unser eigenes Audit beim Kunden prüft. Eine Seite
ohne Titel meldet dem Browser-Tab nichts und der Vorlesehilfe nichts — wer
drei Vorschauen offen hat, sieht dreimal dieselbe leere Beschriftung.

**Der Titel wird maskiert.** Er kommt aus Namen, die jemand eingetippt hat.
Ein `<` darin schriebe sonst den Kopf der Seite um.
"""
import html as _html


def vorschau_huelle(inhalt: str, css: str = "", titel: str = "Vorschau") -> str:
    """Ein vollständiges Dokument um Inhalt und Stil.

    `inhalt` ist bewusst **nicht** maskiert — es ist der gespeicherte
    Seiteninhalt und soll als Markup wirken. Das ist der Zweck einer
    Vorschau. Maskiert wird der Titel, denn der ist eine Beschriftung.
    """
    return (
        f'<!DOCTYPE html><html lang="de"><head><meta charset="UTF-8">\n'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f'<title>{_html.escape(titel or "Vorschau")}</title>\n'
        f'<style>{css}</style></head><body>{inhalt}</body></html>'
    )
