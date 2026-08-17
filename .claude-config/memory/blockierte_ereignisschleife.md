---
name: blockierte-ereignisschleife
description: "Ein synchroner KI-Aufruf in einer async def hält den ganzen Server an — Render antwortet dann mit 503, und die Oberfläche zeigt „Verbindungsfehler""
metadata:
  node_type: memory
  type: reference
---

**Das Muster.** Ein Endpunkt antwortet nach 6–10 Sekunden mit **503**, während
`/api/health` in 0,13 s durchläuft. Im Browser steht „Failed to fetch", in der
Oberfläche „Verbindungsfehler" — also ein Rat, beim eigenen Internet zu suchen.

**Die Ursache ist fast nie das Netz.** Am 17.08.2026 waren es zwei Zeilen in
`services/impressum_scraper.py`:

```python
from anthropic import Anthropic          # der SYNCHRONE Client
async def extract_contact_from_impressum(...):
    response = client.messages.create(...)   # ohne await
```

Ein synchroner Aufruf in einer `async def` hält die Ereignisschleife an. Bei
`timeout=20.0` steht der Server bis zu zwanzig Sekunden und beantwortet
**nichts** mehr — auch nicht Renders Gesundheitsprüfung. Deren Proxy kappt
daraufhin die laufende Anfrage. Der 503 kommt vom Proxy, nicht von der
Anwendung, und trägt deshalb **keine CORS-Kopfzeilen**: Der Browser sieht
keinen Status, sondern nur einen abgebrochenen `fetch`.

**Behebung:** `await asyncio.to_thread(lambda: client.messages.create(...))`.

**Wie man es beweist, statt zu raten:** Einen Zähler alle 10 ms ticken lassen
und prüfen, ob er während des Aufrufs drankommt. Vorher: **null Durchläufe**.
Das ist stabiler als eine Dauermessung.

**Noch offen:** Neun weitere Module rufen `messages.create` genauso auf —
`agents/qa_agent`, `agents/content_writer`, `agents/review_agent`,
`agents/seo_geo_agent`, `agents/lead_analyst`, `services/qa_scanner`,
`services/geo_optimizer`, `services/audit_ai`, `services/geo_generator`.
Die meisten laufen in Hintergrund-Threads, wo Blockieren nichts kostet — vor
einer Umstellung ist je Stelle zu prüfen, ob sie an einer Anfrage hängt.

**Merksatz für die Diagnose:** Wenn ein Aufruf scheitert und `health` gleichzeitig
antwortet, ist der Server nicht tot — er war nur beschäftigt. Erst den
Netzwerkstatus im Browser lesen (`read_network_requests`), bevor man der
Fehlermeldung glaubt. Siehe auch [[deploy-laeuft-ueber-ci]].
