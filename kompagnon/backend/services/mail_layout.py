"""
Der Rahmen jeder KOMPAGNON-Mail — eine Stelle für alle Anlässe.

Die Widget-Mails waren gestaltet, die Mail an einen Bestandskunden bestand aus
nacktem ``<h2>``. Derselbe Absender, zwei Anmutungen. Was hier steht, stand
vorher als ``_shell`` in ``widget_report`` und ist von dort hierher gezogen —
gleiche Bauart, nur der Fußtext ist jetzt ein Parameter: Warum eine Mail
ankommt, ist bei einer angeforderten Analyse etwas anderes als bei einem
laufenden Projekt.
"""
from services import brand


def wortmarke(farbe: str = brand.WHITE, gelb: str = brand.YELLOW) -> str:
    """KOMPAGNON als Schriftzug — der Punkt in der Akzentfarbe.

    Ein Bild wäre in der E-Mail eine Zumutung: Die meisten Postfächer laden
    externe Bilder erst auf Klick, und dann steht statt der Marke ein kaputtes
    Symbol. Als Text steht sie immer da.
    """
    return (f'<span style="font-size:13px;font-weight:900;letter-spacing:.18em;'
            f'color:{farbe}">KOMPAGNON<span style="color:{gelb}">.</span></span>')


def knopf(url: str, text: str) -> str:
    """Der eine gelbe Knopf der Mail."""
    return (f'<table role="presentation" cellpadding="0" cellspacing="0" '
            f'style="margin:24px 0"><tr><td style="background:{brand.YELLOW};'
            f'border-radius:6px"><a href="{url}" style="display:inline-block;'
            f'padding:14px 28px;font-size:15px;font-weight:900;'
            f'color:{brand.DARK};text-decoration:none">{text}</a></td></tr></table>')


def rahmen(inner: str, fusstext: str, oberzeile: str = "Homepage Standard") -> str:
    """Der Rahmen um den Inhalt einer Mail.

    Tabellen statt divs: Outlook auf Windows rendert mit der Word-Engine und
    ignoriert ``max-width`` auf einem div — die Mail lief dort über die volle
    Fensterbreite. ``role="presentation"`` hält die Tabelle aus dem
    Screenreader heraus, sie ist reines Layout.
    """
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:{brand.SURFACE};
             font-family:{brand.FONT_SANS};color:{brand.TEXT}">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       style="background:{brand.SURFACE};padding:28px 12px">
<tr><td align="center">
  <table role="presentation" width="560" cellpadding="0" cellspacing="0"
         style="width:100%;max-width:560px;background:{brand.WHITE};
                border-radius:12px;overflow:hidden">
    <tr><td style="background:{brand.DARK};padding:22px 28px">
      {wortmarke()}
      <div style="font-size:11px;letter-spacing:.14em;text-transform:uppercase;
                  color:{brand.WHITE};opacity:.7;margin-top:4px">
        {oberzeile}</div>
    </td></tr>
    <tr><td style="padding:28px">{inner}</td></tr>
    <tr><td style="padding:18px 28px;border-top:1px solid {brand.BORDER};
                   font-size:11px;line-height:1.6;color:{brand.TEXT_60}">
      {fusstext}
    </td></tr>
  </table>
</td></tr></table>
</body></html>"""
