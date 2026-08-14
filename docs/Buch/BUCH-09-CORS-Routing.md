# BUCH-09 — CORS & Routing: die Verbindung Netlify ↔ Render

## Warum dieser Schritt eine eigene Datei bekommt

Du hast beschrieben, dass bei Iterationen immer wieder Fehler auftreten, weil das Backend
entwickelt ist, aber keine Verbindung zum Frontend hat. **Das hier ist der Musterfall
dafür** — und der einzige Schritt in diesem gesamten Projekt, bei dem der Fehler
vollständig unsichtbar bleibt, wenn man nicht gezielt hinsieht.

### Was passiert, wenn CORS fehlt

Der Browser sieht: Seite liegt auf `homepage-standard.netlify.app`, Anfrage geht an
`claude-code-znq2.onrender.com`. Zwei verschiedene Adressen. Der Browser fragt das Backend
vorab: „Darfst du von dieser Seite angesprochen werden?" Antwortet das Backend nicht mit
der ausdrücklichen Erlaubnis, **blockiert der Browser die Anfrage, bevor sie das Backend
erreicht**.

Konsequenz:

| Wo du suchst | Was du siehst |
|---|---|
| Render-Log | **nichts** — die Anfrage kam nie an |
| Stripe-Dashboard | **nichts** — keine Session wurde erstellt |
| Datenbank | **nichts** — keine Bestellung |
| Netlify-Log | **nichts** — statische Seiten loggen keine API-Fehler |
| Browser-Konsole (F12) | die Wahrheit: `blocked by CORS policy` |

Du würdest also einen kaputten Shop betreiben, ohne dass ein einziges Log etwas meldet.
Deshalb steht dieser Schritt zwingend **vor** dem Live-Gang der Landingpage.

---

## PFLICHT-CHECK

```bash
git remote -v && git branch --show-current
```

**Zusätzlich brauchst du:** die exakte Netlify-URL aus `BUCH-08` Schritt 7.

---

## PROMPT FÜR CLAUDE CODE

```
Führe zuerst aus: git remote -v && git branch --show-current
Erwartet: origin = nachhaltika-arch/Claude-Code, branch = claude/kompagnon-automation-system-FapM9
Bei Abweichung: stoppe und melde.

SCHRITT 0 — Bestand analysieren
Zeige mir die aktuelle CORSMiddleware-Konfiguration in der FastAPI-Hauptdatei.
Ich will genau sehen: allow_origins, allow_credentials, allow_methods, allow_headers.
Aendere noch nichts.

SCHRITT 1 — Origins konfigurierbar machen
Die erlaubten Herkuenfte duerfen NICHT hart im Code stehen. Baue sie auf eine
Umgebungsvariable um:

  CORS_ORIGINS = kommaseparierte Liste aus der ENV-Variable ALLOWED_ORIGINS,
  Fallback wenn nicht gesetzt: die bisher hart kodierten Werte.

Beim Start soll die App die aktive Liste loggen:
  logger.info("CORS erlaubte Origins: %s", origins)
So siehst du in den Render-Logs sofort, ob die Netlify-Domain dabei ist.

WICHTIG:
- allow_origins darf NICHT ["*"] sein, wenn allow_credentials=True gesetzt ist.
  Diese Kombination ist nach Spezifikation ungueltig und wird vom Browser
  kommentarlos ignoriert - der klassische stille Fehler.
- Origins werden OHNE abschliessenden Schraegstrich angegeben.
  "https://beispiel.netlify.app/" mit Slash funktioniert NICHT.
- Nur https, kein http.

SCHRITT 2 — Diagnose-Endpunkt
Lege GET /api/health/cors an. Gibt zurueck:
  {
    "allowed_origins": [...],
    "request_origin": <Origin-Header des Aufrufs oder null>,
    "origin_allowed": true/false,
    "backend_version": <git commit sha, falls verfuegbar>
  }
Damit kannst du von der Netlify-Seite aus in einem Aufruf pruefen, ob die
Verbindung steht - ohne einen Testkauf ausloesen zu muessen.

SCHRITT 3 — Preflight sicherstellen
Pruefe, dass OPTIONS-Anfragen auf /api/book/checkout nicht durch eine
Authentifizierungs-Middleware abgefangen werden, bevor CORSMiddleware greift.
Reihenfolge der Middleware ist entscheidend: CORSMiddleware muss ZUERST
registriert sein. Zeige mir die Reihenfolge.

SCHRITT 4 — Verifikationsskript
Lege scripts/check-cors.sh an:

  #!/bin/bash
  ORIGIN="$1"
  API="${2:-https://claude-code-znq2.onrender.com}"
  echo "Pruefe Origin: $ORIGIN"
  echo "--- Preflight (OPTIONS) ---"
  curl -s -i -X OPTIONS "$API/api/book/checkout" \
    -H "Origin: $ORIGIN" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: content-type" | grep -i "access-control\|HTTP/"
  echo "--- Health ---"
  curl -s "$API/api/health/cors" -H "Origin: $ORIGIN"

SCHRITT 5 — Verifikation
bash scripts/check-cors.sh https://DEINE-NETLIFY-DOMAIN.netlify.app

SCHRITT 6
git add -A
git commit -m "Make CORS origins configurable and add CORS diagnostics endpoint"
git push origin claude/kompagnon-automation-system-FapM9
```

---

## MANUELLER SCHRITT: Render-Umgebungsvariable

Render → dein Backend-Service → **Environment** → Variable hinzufügen:

```
ALLOWED_ORIGINS = https://kompagnon-frontend.onrender.com,https://DEINE-NETLIFY-DOMAIN.netlify.app
```

Falls du später eine eigene Domain aufschaltest, **beide** Adressen eintragen — Netlify
behält die `.netlify.app`-Adresse zusätzlich zur eigenen Domain.

Nach dem Speichern startet Render den Dienst neu. **Warte, bis der Deploy grün ist**,
bevor du testest.

---

## VERIFIKATION

**1. Render-Log prüfen** — direkt nach dem Neustart muss dort stehen:
```
CORS erlaubte Origins: ['https://kompagnon-frontend.onrender.com', 'https://…netlify.app']
```
Steht deine Netlify-Domain nicht in dieser Zeile, ist die ENV-Variable nicht angekommen.

**2. Preflight prüfen**
```bash
bash scripts/check-cors.sh https://DEINE-NETLIFY-DOMAIN.netlify.app
```

Erwartete Ausgabe im Preflight-Teil:
```
HTTP/2 200
access-control-allow-origin: https://DEINE-NETLIFY-DOMAIN.netlify.app
access-control-allow-methods: ...POST...
access-control-allow-headers: ...content-type...
```

**Fehlt `access-control-allow-origin` komplett → CORS greift nicht.** Nicht weitermachen.

**3. Im Browser prüfen**
Landingpage öffnen → F12 → Reiter „Konsole" → Kaufformular absenden.
- Kein roter CORS-Fehler → Verbindung steht
- `blocked by CORS policy` → Origin stimmt nicht exakt (Tippfehler, Slash am Ende, http statt https)

---

## COMMIT-MESSAGE

```
Make CORS origins configurable and add CORS diagnostics endpoint
```

---

## Die vier häufigsten Ursachen, wenn es trotzdem nicht geht

| Symptom | Ursache |
|---|---|
| `access-control-allow-origin` fehlt ganz | Origin nicht in der Liste, oder Tippfehler |
| Origin stimmt, aber trotzdem blockiert | Schrägstrich am Ende der URL in `ALLOWED_ORIGINS` |
| Funktioniert bei GET, nicht bei POST | Preflight wird von Auth-Middleware abgefangen (Schritt 3) |
| Funktionierte gestern, heute nicht | Netlify-Deploy-Preview hat eine andere Subdomain |

Der letzte Punkt ist tückisch: Netlify erzeugt für jeden Branch-Deploy eine eigene
Adresse wie `deploy-preview-3--seite.netlify.app`. Die steht nicht in deiner Liste.
Teste immer gegen die Produktionsadresse.

---

## ZWEI SCHRITTE VORAUS

- **Dieses Muster wiederholt sich bei jeder Kundenwebsite.** Sobald eine
  Netlify-Kundenseite ein Kontaktformular an dein Backend schickt, hast du dasselbe
  Problem — dann aber mit *n* Domains. Die ENV-basierte Lösung skaliert dafür bereits;
  langfristig brauchst du eine Origin-Prüfung, die Kundendomains aus der Datenbank liest.
- **Der Diagnose-Endpunkt gehört in dein Standard-Repertoire.** Baue ihn beim nächsten
  ähnlichen Problem als Erstes — er verwandelt eine unsichtbare Blockade in eine Zeile
  Klartext.
- **Nach dem Aufschalten der eigenen Domain musst du hierher zurück.** Das ist der
  Schritt, der beim Domain-Umzug am häufigsten vergessen wird.
