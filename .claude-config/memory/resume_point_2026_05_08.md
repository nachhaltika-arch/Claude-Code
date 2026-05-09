---
name: Wiederaufnahme 2026-05-08 (Stand Ende 2026-05-08)
description: Tool-CI-Refactor P0–P5 komplett auf staging; offen ist nur noch der iterative Audit der --brand-primary Verwendungen (Links/Outlines/secondary chips → -mid)
type: project
originSessionId: 4cd24d32-85e3-4a98-b22a-82325da50d7e
---
**Why:** Heute durchgezogen: P2/P3/P4 (Wireframe/Design/StyleGuide) am Vormittag, P5.1 (V1 SitemapView löschen + xyflow/dagre raus), PR-Template für Routine-Test, P5.2 (index.css Konsolidierung) und P5.3 (--brand-primary Switch von Mid auf Dark Teal). Letzter Punkt war hochinvasiv (495 Verwendungen in 85 Dateien) — User hat das visuelle Chaos während der iterativen Migration bewusst akzeptiert.

**How to apply:** Wenn die nächste Session startet, zuerst Browser-Eindruck prüfen — Links und Focus-Rings sollten in vielen Pages "zu dunkel" wirken (waren Mid Teal, sind jetzt Dark Teal). Diese Stellen sind die Audit-Liste für den iterativen Cleanup: per Page durchgehen und `--brand-primary` auf `--brand-primary-mid` umziehen, wo es um Links / sekundäre Akzente / Focus-Rings geht.

---

## Heute komplette Push-Historie

| Commit | Was |
|--------|-----|
| `54c2ff3` | P2 WireframeView Guideline-Alignment |
| `cd6f5c8` | P3 DesignView Guideline-Alignment |
| `58a8f68` | P4 StyleGuideView Guideline-Alignment |
| `0b68291` | P5.1 V1 SitemapView löschen + @xyflow/react + dagre raus |
| `c5572f6` | PR-Template für Pre-Merge-Smoke-Test (`.github/PULL_REQUEST_TEMPLATE.md`) |
| `2f0fb61` | P5.2 index.css Konsolidierung (.kc-btn-primary 3→1, .kc-card 2→1) |
| `b3f7e4d` | P5.3 Token-Switch `--brand-primary`: Mid Teal → Dark Teal |
| `85a9781` | Login.jsx — 6 Link/Focus-Stellen auf `--brand-primary-mid` gezogen |
| `5154744` | Envato POC: hero-image-video + hero-stats (Pattern aus agon-multipurpose-agency, eigenständig neutralisiert) |

---

## Wichtige Erkenntnis aus P5.3

Die ursprüngliche Memory-Annahme "Wenn alle Views auf den parallelen `--brand-primary-dark`-Token gezogen sind, kann man den Switch hart machen" hat das Ausmaß der bestehenden `--brand-primary`-Nutzung **deutlich unterschätzt**. Tatsächlich:

- `--brand-primary` wird 495× in 85 Dateien gelesen — Buttons, Links, Spinner, Outlines, Focus-Rings, Borders.
- Nur ein Teil davon (Primary-Buttons, Headlines, Tabellenköpfe) sollte laut Doc Dark Teal sein.
- Der andere Teil (Links, sekundäre Akzente, Focus-Rings) sollte Mid Teal sein und wirkt nach dem Switch zu dunkel.

→ Künftige App-weite Token-Switches NICHT als 5-min-Edit annehmen. Erst grep'pen, dann Aufwand abschätzen.

---

## Iterativer Cleanup nach P5.3 (offen, kleiner als gedacht)

**Wichtiger Befund aus dem ersten Audit-Pass (Login + 5 Spotchecks):** Die 495-Zahl ist täuschend. Die meisten Files nutzen `--brand-primary` für legitime Primary-Use (Submit-Buttons, KPI-Werte, Theme-Toggle-active, Brand-Logo-Background, Score-Top-Indicator). Diese Stellen *sollen* nach P5.3 Dark Teal sein — keine Änderung nötig.

Nur Files mit echten **Link- oder Focus-Ring-Verwendungen** brauchen Migration auf `--brand-primary-mid`. Login.jsx war so ein Fall (Auth-Form Focus + Auth-Links).

**Audit-Status nach 2026-05-08:**
- ✅ Login.jsx — 6 Stellen migriert (`85a9781`)
- ✓ Register.jsx, ResetPassword.jsx, Dashboard.jsx, AppLayout.jsx, Sidebar.jsx — geprüft, kein Migrationsbedarf

**Audit-Methode für künftige Sessions:** Nicht blind alle 85 Files durchgehen. Browser-Check zuerst — was wirkt im Light-Mode "zu dunkel"? Diese Pages dann gezielt in Code aufmachen, je Stelle entscheiden:
- **Primary-Action / Headline / Tabellenkopf / Brand-Surface** → bleibt `--brand-primary` (Dark Teal).
- **Link / Focus-Ring / sekundärer Akzent** → auf `--brand-primary-mid` umstellen.

---

## Render-Staging Deploy-Status nach b3f7e4d

- Frontend Staging: https://kompagnon-frontend-staging.onrender.com
- Editor: `/app/projects/{id}/online-fertig` → Tabs Sitemap / Wireframe / Style-Guide / Design
- Backend Staging: https://kompagnon-backend-staging.onrender.com (unverändert)

## Production-Cut 2026-05-08 18:40 UTC

PR #33 (`staging → main`) gemerged von David, Render hat beide Produktiv-Services autodeployt.
- Merge-Commit: `b79fe5e2`
- kompagnon-frontend: live um 18:44 UTC (4 min 17 s build)
- kompagnon-backend: live um 18:42 UTC (1 min 53 s build)
- Vorheriger Produktiv-Stand: PR #25 vom 2026-05-04 — 4 Tage Cadence eingehalten.

Produktiv-URLs:
- Frontend: https://kompagnon-frontend.onrender.com
- Backend:  https://claude-code-znq2.onrender.com

## P5 NEUE Aufgaben

- [iterativer --brand-primary-Cleanup](#iterativer-cleanup-nach-p53-offen-mehrtägig) — siehe oben
- `--kc-rot` und andere Legacy-Aliases (Z. 65-134 in index.css) sind alle weiterhin definiert und werden in einigen Komponenten genutzt — wenn man wirklich Tabula rasa machen will, müssten diese auch noch ausgemustert werden. Lasse vorerst — Backwards-Compat-Aliases sind ungefährlich.

## GitHub MCP authentifiziert (Setup heute)

Token aus `$GITHUB_TOKEN`-Umgebungsvariable (40-stelliger Classic-PAT) wurde in `~/.claude.json` unter `mcpServers.github.env.GITHUB_PERSONAL_ACCESS_TOKEN` geschrieben. Backup-File: `~/.claude.json.bak.1778265500` (falls jemals revertet werden muss). Live-Reload hat funktioniert — kein Claude-Code-Restart nötig.

**Heißt für morgen:** Claude kann PRs direkt via `mcp__github__create_pull_request` öffnen, statt User die Compare-URL zu schicken. Auch `mcp__github__update_pull_request`, `list_pull_requests`, `get_pull_request_*` etc. funktionieren.

## MCP-Status (geprüft 2026-05-08)

| MCP | Auth-Status | Bemerkung |
|-----|-------------|-----------|
| render | ✅ läuft | heute mehrfach genutzt für Deploy-Status |
| github | ✅ läuft (heute eingerichtet) | siehe oben |
| claude-mem (mcp-search) | ✅ läuft | aber 0 Korpora — wenn Cross-Session-Suche genutzt werden soll, müsste erst aufgebaut werden |
| Gmail | ✅ läuft | `list_labels` returned `{}` weil keine User-Labels — System-Labels (INBOX/SENT/etc.) funktionieren |
| Google Drive | ✅ läuft | letzter Datei-Access: "Kopie von Master_Tracking_Vorlage" |
| Google Calendar | ⚠️ ungeprüft | nur `authenticate`-Tool verfügbar, würde Browser-OAuth-Flow auslösen |
| Canva | ⚠️ ungeprüft | gleiches OAuth-Setup nötig |
| ClickUp | ⚠️ ungeprüft | gleiches OAuth-Setup nötig |

## Envato Wireframe-Pipeline (Plan in separatem Memory-File)

Heute POC fertig (`5154744`): hero-image-video + hero-stats. Workflow validiert. Großer Plan im Memory-File [envato_wireframe_plan.md](envato_wireframe_plan.md) — 5 Phasen, ~30-50 Wireframes Ziel über 8-12 Sessions.

**Nächster Schritt:** Phase 0 (Inventur) starten. Claude scriptet `unzip -l` über alle 68 ZIPs, schreibt `docs/envato-template-inventory.md`. User sichtet dann ~10 Live-Demos visuell.

## Memory-Referenzen

- [KOMPAGNON UI/UX Guidelines v1.0](kompagnon_ui_guidelines.md)
- [Envato Wireframe-Pipeline Plan](envato_wireframe_plan.md)
- Routine-Test PR-Template: `.github/PULL_REQUEST_TEMPLATE.md` im Repo
