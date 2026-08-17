---
name: deploy-laeuft-ueber-ci
description: "Render deployt nicht per Webhook, sondern als letzter CI-Job — nach einem Push dauert es, bis Playwright durch ist"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 458bef95-0615-4eb2-85b8-f2842368b8c2
  modified: 2026-08-17T17:54:44.404Z
---

Render deployt **nicht** über einen GitHub-Webhook, sondern über den letzten
Job in `.github/workflows/ci.yml`:

```yaml
deploy:
  name: Deploy — Render
  needs: [backend-lint, backend-import, backend-tests, frontend-build, e2e, secrets-scan]
```

**Was daraus folgt:** Nach `git push origin staging` ist auf dem
Staging-Server minutenlang noch der alte Stand. Das ist kein Fehler und kein
Zurückrollen — der Deploy wartet auf alle sechs Prüfjobs, und der
Playwright-E2E-Job ist der langsamste.

**Wie man den Stand wirklich misst:** Nicht am Verhalten raten, sondern
`GET /openapi.json` holen und nachsehen, ob ein Pfad oder eine Methode aus dem
neuen Commit im Schema steht. Ein Statuscode taugt nicht als Beweis — bei
einem Router mit Anmeldung antworten vorhandene und nicht vorhandene Pfade
beide mit 401.

**Falle beim Prüfen mit der Shell:** `grep -c` gibt bei null Treffern `0` aus
**und** beendet sich mit Fehlercode. Ein angehängtes `|| echo 0` erzeugt dann
zwei Nullen, und `[ "$n" != "0" ]` ist wahr — ein falscher Treffer. Am
17.08.2026 habe ich David deshalb einen zurückgerollten Deploy gemeldet, den
es nie gab.

Siehe auch [[feedback-ci-pruefen-nach-push]].
