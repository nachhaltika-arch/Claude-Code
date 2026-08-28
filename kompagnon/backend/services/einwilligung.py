# -*- coding: utf-8 -*-
"""Einwilligung fuer erzeugte Kundenseiten (L-144).

**Der Anlass.** Am 27.08.2026 beim Pruefen des Umami-Plans gemessen: „consent"
kommt im Bestand **nur auf der Mess-Seite** vor — `audit_collectors`,
`audit_criteria`, `qa_scanner`, `seitenbrowser`. Auf der **Bau**-Seite
nirgends. Wir pruefen bei Kunden etwas, das wir selbst nicht ausliefern.

**Warum heute trotzdem nichts erscheint.** Eine Seite, die nichts verfolgt und
nichts auf dem Endgeraet ablegt, braucht kein Banner. Ein Banner ohne Anlass
ist selbst ein Fehler: Es trainiert Wegklicken und senkt die Aufmerksamkeit
fuer die Faelle, in denen wirklich etwas zu entscheiden ist. Ohne
Tracking-Skript liefert dieses Modul deshalb **die leere Zeichenkette**, und
das ausgelieferte Dokument sieht aus wie vorher.

**Was es dann leistet.** Der eigentliche Zweck ist nicht das Banner, sondern
die **Reihenfolge**: Ein Skript, das vor der Einwilligung feuert, ist der
Mangel — nicht das fehlende Banner. Deshalb wird ein Tracking-Skript hier
niemals als ausfuehrbares `<script src=…>` ausgeliefert, sondern als
`type="text/plain"` mit der Adresse in `data-src`. Der Browser laedt es dann
nicht; erst die Zustimmung baut daraus ein echtes Skript-Element.

**Warum das die harte Zusicherung ist.** `_build_full_html` nimmt Tracking nur
noch ueber diesen Weg entgegen. Wer kuenftig Umami einbaut (L-142), kann es
nicht versehentlich ungesperrt tun — es gibt keinen zweiten Eingang.

**Was hier bewusst NICHT passiert: unser eigener Pruefer erkennt das nicht.**
`detect_consent` fragt nicht „gibt es eine Einwilligung", sondern „steht einer
von 19 Anbieternamen im HTML" (`cookiebot`, `usercentrics`, …). Ein
selbstgebautes Banner — unseres wie das eines Kunden — ist dafuer unsichtbar.
Einen dieser Namen hier hineinzuschreiben, damit der eigene Pruefer gruen
wird, waere das Gegenteil von Sorgfalt: gruen und blind. Die Messseite zu
aendern verschiebt die Punkte **realer, bereits gepruefter** Seiten und ist
deshalb eine Massstabsfrage (Fassung 2027.1), keine Bauentscheidung.

**Speicherung.** Die Entscheidung selbst liegt in `localStorage`. Das ist nach
§ 25 Abs. 2 TTDSG der Fall „unbedingt erforderlich": Ohne sie muesste bei
jedem Aufruf erneut gefragt werden. Gespeichert wird nur `ja`/`nein` und das
Datum — keine Kennung, kein Verlauf.
"""
import html as _html
import json

#: Woran diese Loesung erkennbar ist. Bewusst ein eigener Name und **kein**
#: Anbietername aus `CMP_SIGNATURES` — siehe Modulkopf.
MARKIERUNG = "kompagnon-einwilligung"

#: Schluessel im `localStorage`. Versioniert, damit eine spaetere Aenderung
#: der Zwecke die alte Zustimmung nicht stillschweigend weitergelten laesst.
SPEICHERSCHLUESSEL = "kompagnon_einwilligung_v1"


def _skript_marke(skript: dict) -> str:
    """Ein gesperrtes Skript — als Text, nicht als Programm.

    `type="text/plain"` ist der Kern: So behandelt der Browser den Inhalt als
    Datei ohne Bedeutung und laedt `data-src` nicht. Ein `<script src=…>` mit
    `defer` waere **kein** Ersatz — es laedt trotzdem, nur spaeter.
    """
    attribute = "".join(
        f' data-{_html.escape(str(k))}="{_html.escape(str(v))}"'
        for k, v in sorted((skript.get("attribute") or {}).items())
    )
    return (
        f'<script type="text/plain" data-{MARKIERUNG}="1"'
        f' data-src="{_html.escape(skript["src"])}"'
        f' data-zweck="{_html.escape(skript.get("zweck", "statistik"))}"'
        f'{attribute}></script>'
    )


def einwilligungs_block(tracking_skripte=None, datenschutz_pfad="/datenschutz") -> str:
    """Banner, Sperre und gesperrte Skripte — oder nichts.

    `tracking_skripte` ist eine Liste von `{"src": …, "zweck": …,
    "attribute": {…}}`. Ist sie leer, gibt es nichts zu entscheiden und diese
    Funktion liefert `""`.
    """
    skripte = [s for s in (tracking_skripte or []) if s.get("src")]
    if not skripte:
        return ""

    marken = "\n  ".join(_skript_marke(s) for s in skripte)
    schluessel = json.dumps(SPEICHERSCHLUESSEL)
    marke = json.dumps(MARKIERUNG)
    pfad = _html.escape(datenschutz_pfad)

    return f"""
<!-- Einwilligung (KOMPAGNON, L-144). Ohne Tracking steht hier nichts. -->
  {marken}
  <div id="{MARKIERUNG}" class="{MARKIERUNG}" role="dialog" aria-modal="true"
       aria-labelledby="{MARKIERUNG}-titel" hidden>
    <div class="{MARKIERUNG}__inhalt">
      <h2 id="{MARKIERUNG}-titel">Dürfen wir messen, wie diese Seite genutzt wird?</h2>
      <p>Wir erheben anonyme Nutzungsstatistiken, um die Seite zu verbessern.
         Ohne Ihre Zustimmung geschieht das nicht. Mehr dazu in der
         <a href="{pfad}">Datenschutzerklärung</a>.</p>
      <div class="{MARKIERUNG}__knoepfe">
        <button type="button" data-{MARKIERUNG}-antwort="nein">Nur das Nötige</button>
        <button type="button" data-{MARKIERUNG}-antwort="ja">Einverstanden</button>
      </div>
    </div>
  </div>
  <!-- Der Widerruf wird **mitgeliefert**, nicht nur vorgesehen. Ein Empfaenger
       ohne Knopf waere eine Zusage ohne Weg dorthin; das Skript unten blendet
       ihn ein, sobald eine Entscheidung gespeichert ist. -->
  <p class="{MARKIERUNG}__widerruf" hidden>
    <a href="#" id="{MARKIERUNG}-widerruf">Einwilligung widerrufen</a>
  </p>
  <script>
  (function () {{
    var SCHLUESSEL = {schluessel}, MARKE = {marke};
    var kasten = document.getElementById(MARKE);

    function gespeichert() {{
      try {{ return JSON.parse(localStorage.getItem(SCHLUESSEL) || "null"); }}
      catch (e) {{ return null; }}   // privater Modus wirft beim Lesen
    }}

    function freigeben() {{
      var marken = document.querySelectorAll('script[data-' + MARKE + ']');
      Array.prototype.forEach.call(marken, function (alt) {{
        var neu = document.createElement("script");
        neu.src = alt.getAttribute("data-src");
        neu.async = true;
        Array.prototype.forEach.call(alt.attributes, function (a) {{
          // `data-src`, `data-zweck` und die Marke gehoeren zur Sperre, nicht
          // zum Skript — alles andere wird durchgereicht (Umami braucht etwa
          // `data-website-id`).
          if (a.name.indexOf("data-") === 0 &&
              a.name !== "data-src" && a.name !== "data-zweck" &&
              a.name !== "data-" + MARKE) {{
            neu.setAttribute(a.name, a.value);
          }}
        }});
        alt.parentNode.replaceChild(neu, alt);
      }});
    }}

    function antworten(ja) {{
      try {{
        localStorage.setItem(SCHLUESSEL, JSON.stringify(
          {{ statistik: ja, datum: new Date().toISOString().slice(0, 10) }}));
      }} catch (e) {{ /* ohne Speicher wird beim naechsten Aufruf erneut gefragt */ }}
      if (kasten) kasten.hidden = true;
      widerrufZeigen(true);
      if (ja) freigeben();
    }}

    var widerruf = document.querySelector("." + MARKE + "__widerruf");

    function widerrufZeigen(sichtbar) {{
      if (widerruf) widerruf.hidden = !sichtbar;
    }}

    var stand = gespeichert();
    if (stand && stand.statistik === true) {{
      freigeben();
      widerrufZeigen(true);
    }} else if (stand) {{
      widerrufZeigen(true);          // auch ein Nein ist eine Entscheidung
    }} else {{
      if (kasten) kasten.hidden = false;
    }}

    if (kasten) {{
      kasten.addEventListener("click", function (e) {{
        var antwort = e.target.getAttribute("data-" + MARKE + "-antwort");
        if (antwort) antworten(antwort === "ja");
      }});
    }}

    // Widerruf: eine Seite muss die Entscheidung zuruecknehmen lassen. Ein
    // Link mit dieser Kennung genuegt, ueblicherweise in der
    // Datenschutzerklaerung.
    document.addEventListener("click", function (e) {{
      var ziel = e.target.closest && e.target.closest("#" + MARKE + "-widerruf");
      if (!ziel) return;
      e.preventDefault();
      try {{ localStorage.removeItem(SCHLUESSEL); }} catch (err) {{}}
      location.reload();
    }});
  }})();
  </script>
"""
