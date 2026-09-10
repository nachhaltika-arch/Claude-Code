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

**Der fertige Block** (Stand 10.09.2026, am Gegenstand geprüft). Er gehört
direkt unter das `<iframe>` und ist absichtlich eigenständig: Er ändert
nichts am vorhandenen Einwilligungs-Skript der Trägerseite, sondern liest
dessen Ergebnis aus `localStorage['kpg-consent-v1']` und hört über einen
`MutationObserver` auf dem Banner zu, wann es sich ändert. Damit lässt er
sich einsetzen und wieder herausnehmen, ohne dass etwas anderes berührt wird.

Geprüft wurde an einer Nachbildung der Landingpage, nicht nur am Syntaxbaum:
`fbclid` wird durchgereicht **und vorhandene Parameter bleiben stehen** (der
erste Entwurf verschluckte ein `?api=`), ohne Einwilligung lädt kein Pixel,
nach Einwilligung schon, und eine Lead-Nachricht von fremdem Ursprung löst
nichts aus.

```html
<!-- ═══════════════════════════════════════════════════════════════════
     KOMPAGNON — Messung der Websprint-Kampagne
     Stand 10.09.2026 · gehört direkt UNTER das <iframe id="kompagnon-audit">

     Der Block ist absichtlich eigenständig: Er ändert nichts an eurem
     vorhandenen Einwilligungs-Skript, sondern liest dessen Ergebnis aus
     `localStorage['kpg-consent-v1']` und hört zu, wann es sich ändert.
     Damit könnt ihr ihn einsetzen und wieder herausnehmen, ohne dass etwas
     anderes davon berührt wird.

     Er tut drei Dinge:
       1. Herkunft durchreichen — `fbclid` und `_fbp` an das Widget, das in
          einem iframe auf fremder Domain läuft und eure Adresszeile nicht
          sieht. Ohne sie ist jede Lead-Meldung eine ohne Anzeige.
       2. Meta-Pixel laden — erst nach Marketing-Einwilligung, nie vorher.
       3. Den Lead melden — an Meta UND an GA4, wenn das Widget ihn meldet.
     ═══════════════════════════════════════════════════════════════════ -->
<script>
(function () {
  var KEY      = 'kpg-consent-v1';
  var RAHMEN   = 'kompagnon-audit';
  var URSPRUNG = 'https://kas.kompagnon.group';
  var PIXEL    = '1363198722345965';   /* aus den Widget-Einstellungen */

  function einwilligung() {
    try {
      var v = JSON.parse(localStorage.getItem(KEY));
      return (v && typeof v === 'object') ? v : null;
    } catch (e) { return null; }
  }

  /* ── 1. Herkunft an das Widget ─────────────────────────────────────
     Das Widget steht in einem iframe auf fremder Domain und sieht diese
     Adresszeile nicht. Ohne `fbclid` weiß Meta, dass jemand ein Formular
     abgeschickt hat — aber nicht, welche Anzeige ihn gebracht hat.

     Nur gesetzt, wenn es etwas durchzureichen gibt: Sonst würde das
     iframe bei jedem Aufruf ein zweites Mal laden. */
  (function herkunft() {
    var f = document.getElementById(RAHMEN);
    if (!f) return;
    var eigene = new URLSearchParams(location.search);
    var p = new URLSearchParams();

    var klick = (eigene.get('fbclid') || '').trim();
    if (/^[A-Za-z0-9._-]{1,300}$/.test(klick)) p.set('fbclid', klick);

    var fbp = (document.cookie.match(/(?:^|;\s*)_fbp=([^;]+)/) || [])[1];
    if (fbp) p.set('fbp', decodeURIComponent(fbp));

    if (!p.toString()) return;

    /* **Vorhandene Parameter bleiben stehen.** Der erste Entwurf ersetzte
       den ganzen Query-String und verschluckte damit ein `?api=`, das für
       einen Test auf Staging dranstand. Auf dieser Seite steht heute keiner
       — genau deshalb wäre es eine stille Falle für den nächsten. */
    var roh = f.getAttribute('src') || '';
    if (!roh) return;
    var teile = roh.split('?');
    var vorhanden = new URLSearchParams(teile[1] || '');
    p.forEach(function (wert, name) { vorhanden.set(name, wert); });
    f.setAttribute('src', teile[0] + '?' + vorhanden.toString());
  })();

  /* ── 2. Meta-Pixel, einwilligungsgesteuert ─────────────────────────
     Erst nach ausdrücklicher Marketing-Einwilligung. Vorher lädt kein
     fremdes Skript — § 25 TDDDG verlangt ein Ja, und Schweigen ist keins. */
  var geladen = false;
  function pixelLaden() {
    if (geladen || window.fbq) return;
    geladen = true;
    !function (f, b, e, v, n, t, s) {
      if (f.fbq) return; n = f.fbq = function () {
        n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments);
      };
      if (!f._fbq) f._fbq = n; n.push = n; n.loaded = !0; n.version = '2.0';
      n.queue = []; t = b.createElement(e); t.async = !0; t.src = v;
      s = b.getElementsByTagName(e)[0]; s.parentNode.insertBefore(t, s);
    }(window, document, 'script', 'https://connect.facebook.net/en_US/fbevents.js');
    fbq('init', PIXEL);
    fbq('track', 'PageView');
  }

  function pruefen() {
    var c = einwilligung();
    if (c && c.marketing) pixelLaden();
  }
  pruefen();

  /* Wenn der Besucher später zustimmt, schließt euer Skript das Banner.
     Darauf hören wir — so braucht es keinen Eingriff in euren Code. */
  var banner = document.getElementById('cc');
  if (banner && window.MutationObserver) {
    new MutationObserver(pruefen)
      .observe(banner, { attributes: true, attributeFilter: ['hidden'] });
  }

  /* ── 3. Der Lead ───────────────────────────────────────────────────
     Das Widget meldet ihn dem Elternfenster. Bisher hörte hier niemand zu,
     und damit feuerte weder Meta noch GA4.

     `eventID` ist dieselbe Kennung, die auch der Serverweg mitschickt —
     Meta verwirft die zweite Meldung, es wird also nicht doppelt gezählt. */
  window.addEventListener('message', function (e) {
    if (e.origin !== URSPRUNG) return;
    var d = e.data;
    if (!d || d.type !== 'kpg-audit-lead') return;

    var f = document.getElementById(RAHMEN);
    if (!f || f.contentWindow !== e.source) return;   /* nur das eigene iframe */

    if (window.fbq) {
      fbq('track', 'Lead', {}, d.eventId ? { eventID: d.eventId } : undefined);
    }
    /* `gtag` gibt es erst nach Statistik-Einwilligung. Kein Wert mitgeben:
       Eine 0 hieße in GA4 „der Lead ist nichts wert", nicht „nicht erhoben". */
    if (typeof window.gtag === 'function') {
      gtag('event', 'generate_lead', { method: 'website_analyse' });
    }
  });
})();
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
