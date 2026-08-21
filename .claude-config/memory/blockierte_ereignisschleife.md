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

**Erledigt am 18.08.2026.** Ein AST-Durchlauf fand nicht neun, sondern
**zwölf** blockierende Stellen: zehn direkt in `async def` und zwei, bei denen
eine synchrone Zwischenebene den Aufruf verdeckte (`geo_optimizer.analyze`,
`GeoGeneratorAgent.generate_all`, das das Modell zweimal ruft). Alle laufen
jetzt über `services/ki_aufruf.frag_modell`.

Die Helfer in `agents/`, `assistant`, `audit_ai`, `component_library` blieben
unangetastet — sie laufen in FastAPIs Threadpool oder in einem eigenen Thread,
standen also nie auf der Schleife. Das sagt jetzt der Test, nicht die
Vermutung: `tests/test_keine_ki_blockiert_die_schleife.py` prüft zwei Regeln
über das ganze Backend, die zweite transitiv. **Die Auflösung nach
Funktionsnamen kann einen Fehlalarm erzeugen — das kostet einen Blick, ein
übersehener Fall einen 503.**

**Merksatz für die Diagnose:** Wenn ein Aufruf scheitert und `health` gleichzeitig
antwortet, ist der Server nicht tot — er war nur beschäftigt. Erst den
Netzwerkstatus im Browser lesen (`read_network_requests`), bevor man der
Fehlermeldung glaubt. Siehe auch [[deploy-laeuft-ueber-ci]].
