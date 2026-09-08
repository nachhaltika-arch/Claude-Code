# KOMPAGNON Audit-Widget — Einbindung auf fremden Websites

`audit-widget.html` ist ein eigenständiges Widget (Vanilla JS, kein Build).
Gehostet wird es auf dem KOMPAGNON-Frontend, eingebunden wird es per `<iframe>`.

**Live-URL (nach Deploy):**
`https://kas.kompagnon.group/embed/audit-widget.html`

## Warum iframe statt Code-Copy-Paste?

Das Backend erlaubt API-Calls per CORS nur von erlaubten Origins
(`kas.kompagnon.group`, `*.netlify.app`, localhost).
Im iframe stammen die Fetches vom **Widget-Origin** (= erlaubt) — nicht von der
Kundendomain. So funktioniert das Widget auf **jeder** fremden Seite, ohne dass
für jede Kundendomain etwas freigeschaltet werden muss.

## Einbindung (Standard — eine Zeile)

```html
<iframe
  src="https://kas.kompagnon.group/embed/audit-widget.html"
  style="width:100%;max-width:680px;height:760px;border:0;display:block;margin:0 auto;"
  title="KOMPAGNON Website-Analyse"
  loading="lazy"></iframe>
```

## Einbindung mit automatischer Höhe (empfohlen)

Das Widget meldet seine Höhe per `postMessage`, damit kein Scrollbalken /
Leerraum entsteht (Eingabe → Laden → Ergebnis sind unterschiedlich hoch).

```html
<iframe id="kpg-audit"
  src="https://kas.kompagnon.group/embed/audit-widget.html"
  style="width:100%;max-width:680px;height:760px;border:0;display:block;margin:0 auto;"
  title="KOMPAGNON Website-Analyse"
  loading="lazy"></iframe>

<script>
  window.addEventListener('message', function (e) {
    if (e.data && e.data.type === 'kpg-audit-height') {
      var f = document.getElementById('kpg-audit');
      if (f) f.style.height = e.data.height + 'px';
    }
  });
</script>
```

## Zwischenspeicher

`public/serve.json` schickt für `/embed/**` ein `Cache-Control: no-cache`.
Der Browser fragt damit bei jedem Aufruf nach, ob sich etwas geändert hat
(er lädt nur bei Änderung neu — ein 304 kostet fast nichts). Ohne diesen
Header hielten Browser eine einmal geladene Fassung fest: nach einem Deploy
sah man weiter die alte, und wer die Seite vorher aufgerufen hatte, als
`/embed/…` noch von der React-App verschluckt wurde, bekam dauerhaft das
Tool-Dashboard im Widget-Rahmen zu sehen.

## Meta-Pixel: was die Trägerseite durchreichen muss

Das Widget steht in einem iframe auf **fremder** Domain. Es sieht die
Adresszeile der Seite darüber nicht — und damit auch nicht die Klick-ID
`fbclid`, die eine Meta-Anzeige beim Klick anhängt. Eine Lead-Meldung ohne
Klick-ID ist eine Meldung ohne Herkunft: Meta weiß, dass jemand das Formular
abgeschickt hat, aber nicht, welche Anzeige ihn gebracht hat.

**Deshalb reicht die Trägerseite drei Dinge im iframe-Aufruf durch:**

| Parameter | Woher | Wozu |
|---|---|---|
| `fbclid` | aus der eigenen Adresszeile | Zuordnung zur Anzeige |
| `fbp` | aus dem `_fbp`-Cookie, falls die Seite ein eigenes Pixel hat | zweiter Abgleichschlüssel |
| `consent` | vom Consent-Banner: `1` erlaubt, `0` abgelehnt | schaltet Browser- **und** Serverweg ab |

`consent=0` wird respektiert. Fehlt der Parameter, verhält sich das Widget wie
bisher — diese Änderung verschiebt keine Rechtslage still.

```html
<iframe id="kpg-audit"
  style="width:100%;max-width:680px;height:760px;border:0;display:block;margin:0 auto;"
  title="KOMPAGNON Website-Analyse"
  loading="lazy"></iframe>

<script>
  (function () {
    var basis  = 'https://kas.kompagnon.group/embed/audit-widget.html';
    var eigene = new URLSearchParams(location.search);
    var p = new URLSearchParams();

    var klick = (eigene.get('fbclid') || '').trim();
    if (/^[A-Za-z0-9._-]{1,300}$/.test(klick)) p.set('fbclid', klick);

    var fbp = (document.cookie.match(/(?:^|;\s*)_fbp=([^;]+)/) || [])[1];
    if (fbp) p.set('fbp', decodeURIComponent(fbp));

    /* Hier den echten Wert des Consent-Werkzeugs einsetzen.
       Beispiel Usercentrics: der Dienst „Facebook Pixel" ist zugestimmt. */
    /* p.set('consent', hatMarketingEinwilligung() ? '1' : '0'); */

    var f = document.getElementById('kpg-audit');
    f.src = basis + (p.toString() ? '?' + p.toString() : '');
  })();

  window.addEventListener('message', function (e) {
    if (e.origin !== 'https://kas.kompagnon.group') return;
    if (!e.data) return;
    if (e.data.type === 'kpg-audit-height') {
      var f = document.getElementById('kpg-audit');
      if (f) f.style.height = e.data.height + 'px';
    }
    /* Sobald die Trägerseite ein eigenes Pixel hat, meldet sie den Lead
       selbst — mit derselben Kennung, damit Meta nicht doppelt zählt. */
    if (e.data.type === 'kpg-audit-lead' && window.fbq) {
      fbq('track', 'Lead', {}, e.data.eventId ? { eventID: e.data.eventId } : undefined);
    }
  });
</script>
```

**Wichtig zur Doppelzählung:** Browser- und Servermeldung tragen dieselbe
`event_id` (`kpg-widget-<Anfragenummer>`). Meta verwirft die zweite. Deshalb
dürfen Widget-Pixel, Trägerseiten-Pixel und Conversions API gleichzeitig laufen,
ohne dass ein Lead mehrfach gezählt wird.

## Optionale Parameter

Per Query-String an die `src`-URL anhängbar:

- `?api=https://…` — anderer Backend-Host (z. B. Staging)
- `?fbclid=…`, `?fbp=…`, `?consent=1|0` — siehe Abschnitt oben
- Checkout-Ziel ist im Widget fest auf das KOMPAGNON-Frontend gesetzt.

Beispiel Staging:
`…/embed/audit-widget.html?api=https://kompagnon-backend-staging.onrender.com`
(Staging-Origin muss dann in `CORS_ALLOWED_ORIGINS` des Staging-Backends stehen.)

## Direkter Code (ohne iframe) — nur bei CORS-Freischaltung

Wer den Widget-Code direkt in seine Seite kopiert, dessen Domain muss in der
Backend-Env `CORS_ALLOWED_ORIGINS` eingetragen sein — sonst blockt der Browser
die API-Calls. Für fremde Kundenseiten daher **iframe bevorzugen**.
