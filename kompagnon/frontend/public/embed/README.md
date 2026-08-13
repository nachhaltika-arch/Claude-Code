# KOMPAGNON Audit-Widget — Einbindung auf fremden Websites

`audit-widget.html` ist ein eigenständiges Widget (Vanilla JS, kein Build).
Gehostet wird es auf dem KOMPAGNON-Frontend, eingebunden wird es per `<iframe>`.

**Live-URL (nach Deploy):**
`https://kompagnon-frontend.onrender.com/embed/audit-widget.html`

## Warum iframe statt Code-Copy-Paste?

Das Backend erlaubt API-Calls per CORS nur von erlaubten Origins
(`kompagnon-frontend.onrender.com`, `*.netlify.app`, localhost).
Im iframe stammen die Fetches vom **Widget-Origin** (= erlaubt) — nicht von der
Kundendomain. So funktioniert das Widget auf **jeder** fremden Seite, ohne dass
für jede Kundendomain etwas freigeschaltet werden muss.

## Einbindung (Standard — eine Zeile)

```html
<iframe
  src="https://kompagnon-frontend.onrender.com/embed/audit-widget.html"
  style="width:100%;max-width:680px;height:760px;border:0;display:block;margin:0 auto;"
  title="KOMPAGNON Website-Analyse"
  loading="lazy"></iframe>
```

## Einbindung mit automatischer Höhe (empfohlen)

Das Widget meldet seine Höhe per `postMessage`, damit kein Scrollbalken /
Leerraum entsteht (Eingabe → Laden → Ergebnis sind unterschiedlich hoch).

```html
<iframe id="kpg-audit"
  src="https://kompagnon-frontend.onrender.com/embed/audit-widget.html"
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

## Optionale Parameter

Per Query-String an die `src`-URL anhängbar:

- `?api=https://…` — anderer Backend-Host (z. B. Staging)
- Checkout-Ziel ist im Widget fest auf das KOMPAGNON-Frontend gesetzt.

Beispiel Staging:
`…/embed/audit-widget.html?api=https://kompagnon-backend-staging.onrender.com`
(Staging-Origin muss dann in `CORS_ALLOWED_ORIGINS` des Staging-Backends stehen.)

## Direkter Code (ohne iframe) — nur bei CORS-Freischaltung

Wer den Widget-Code direkt in seine Seite kopiert, dessen Domain muss in der
Backend-Env `CORS_ALLOWED_ORIGINS` eingetragen sein — sonst blockt der Browser
die API-Calls. Für fremde Kundenseiten daher **iframe bevorzugen**.
