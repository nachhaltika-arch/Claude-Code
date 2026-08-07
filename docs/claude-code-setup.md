# Claude Code Setup — neuer Rechner (z.B. MacBook)

Schritt-für-Schritt Anleitung um auf einem neuen Rechner exakt das gleiche Claude-Code-Setup zu bekommen wie auf dem Haupt-Windows-Rechner.

## TL;DR

```bash
git clone https://github.com/nachhaltika-arch/Claude-Code.git
cd Claude-Code
git checkout staging
bash scripts/setup-claude-code.sh
# ... interaktiv: GitHub PAT + Render API Token eingeben
claude auth   # OAuth-Login bei Anthropic im Browser
claude        # läuft, mit identischem Setup wie Windows
```

## Voraussetzungen

| Tool | Mac-Install |
|------|-------------|
| Node.js >= 18 | `brew install node` |
| jq | `brew install jq` |
| GitHub PAT | https://github.com/settings/tokens (Classic, Scopes: `repo`, `workflow`) |
| Render API Token | https://dashboard.render.com/u/settings#api-keys → "Create API Key" |
| Anthropic-Account | für OAuth-Login bei `claude auth` |

## Was das Setup-Script macht

`scripts/setup-claude-code.sh` orchestriert (idempotent — kann mehrfach laufen):

1. **Prerequisites** prüfen (node, npm, jq)
2. **Claude Code CLI** global installieren (`npm install -g @anthropic-ai/claude-code`)
3. **`~/.claude/agents/`** anlegen + die 3 Custom-Agents kopieren (build-error-resolver, code-reviewer, security-reviewer)
4. **`~/.claude/rules/`** anlegen + alle 15 Rule-Files kopieren (10 common + 5 TS)
5. **`~/.claude/settings.json`** + **`settings.local.json`** aus Templates erstellen (skip falls bereits da)
6. **MCP-Tokens** interaktiv erfragen (oder aus ENV vars `GITHUB_PERSONAL_ACCESS_TOKEN` + `RENDER_API_TOKEN` ziehen)
7. **MCP-Server registrieren** via `claude mcp add` (Render HTTP, GitHub stdio)
8. **Plugins installieren** via Marketplaces:
   - `claude-mem@thedotmack` (Cross-Session-Memory + Search)
   - `context-mode@context-mode` (Prisma + Context-Awareness)
   - `last30days@last30days-skill` (Activity-Reports)
9. **Verify** mit `claude mcp list`

## Was NICHT vom Script gemacht wird (manuell)

| Task | Wie |
|------|-----|
| Anthropic-OAuth | `claude auth` (Browser-Flow, einmalig pro Rechner) |
| Skills installieren | Werden via Marketplaces auto-discovered nach Plugin-Install |
| Render Workspace setzen | Beim ersten Render-MCP-Call wird gefragt |
| Repo clone | Manuell vor Setup-Script-Ausführung |

## Was im Repo NICHT enthalten ist

- **Tokens** (GitHub PAT, Render Bearer) — werden zum Setup-Zeitpunkt erfragt
- **Anthropic-Auth** (`~/.claude/.credentials.json`) — pro Rechner separat per OAuth
- **Sessions/History/Cache** — ephemer, rechnerspezifisch
- **Plugin-Cache** — wird beim Plugin-Install neu aufgebaut

## Memory-Sync (NEU)

Ab Commit `b1fb0ad` ist Claude-Memory über das Repo synchronisiert:

- `<repo>/.claude-config/memory/*.md` — 16 Memory-Files (Resume-Points, Rules, User-Profile, Plans, Decisions)
- Setup-Script symlinkt auf Mac: `~/.claude/projects/{encoded-path}/memory/` → `<repo>/.claude-config/memory/`
- Mac Claude-Sessions schreiben Memory-Updates direkt in den Repo-Pfad
- `git add .claude-config/memory && git commit && git push` synchronisiert nach Windows

### Windows auch symlinken (optional)

Windows nutzt aktuell den realen Ordner unter `~/.claude/projects/.../memory/` (Status quo, keine Symlink). Wenn du Memory-Updates **auf Windows** auch automatisch im Repo haben willst, einmalig (in PowerShell als Admin oder mit Developer Mode aktiv):

```powershell
# Backup + Symlink
$projectDir = "$env:USERPROFILE\.claude\projects\C--Users-DavidV-th-Desktop-KAS-Kompagnon-Automatisierungs-System"
Move-Item "$projectDir\memory" "$projectDir\memory.bak.$(Get-Date -Format yyyyMMdd-HHmmss)"
New-Item -ItemType SymbolicLink -Path "$projectDir\memory" -Target "C:\Users\DavidVäth\Desktop\KAS Kompagnon Automatisierungs System\.claude-config\memory"
```

Ohne diesen Schritt: Windows-Memory ist getrennt vom Repo. Du müsstest Memory-Änderungen auf Windows manuell in `.claude-config/memory/` kopieren um sie an Mac zu syncen.

### Sync-Workflow im Alltag

1. Auf Rechner A schreibt Claude Memory-Updates (z.B. neue Resume-Points, Decisions)
2. `git status` zeigt geänderte Files in `.claude-config/memory/`
3. Commit + Push → staging-Branch
4. Auf Rechner B `git pull` → Memory ist synchron

## Nach dem Setup

Test:
```bash
cd /pfad/zum/Claude-Code
claude
```

Erste Session sollte die gleichen Settings/Rules/Agents haben wie auf Windows. Verify im Claude-Prompt: ist die Memory-Datei `~/.claude/projects/.../MEMORY.md` neu (lokal-leer) oder geclonen? Memory-Files sind PER RECHNER — auf Mac fängst du mit leerer Memory an, das ist OK. Die wichtigen Project-Memories sind in CLAUDE.md im Repo.

## Updates synchronisieren (Mac ← Windows)

Wenn du auf Windows neue Rules/Agents hinzufügst:
1. Auf Windows: `cp ~/.claude/agents/*.md /pfad/zum/repo/.claude-config/agents/`
2. Auf Windows: `cp ~/.claude/rules/common/*.md /pfad/zum/repo/.claude-config/rules/common/`
3. Commit + push staging
4. Auf Mac: `git pull` + `bash scripts/setup-claude-code.sh` (überschreibt Agents/Rules)

## Troubleshooting

**"command not found: claude"** — npm global bin nicht im PATH. Mac: `export PATH="$(npm config get prefix)/bin:$PATH"` in `~/.zshrc`.

**MCP-Auth-Fehler** — Token abgelaufen/falsch. Re-add: `claude mcp remove render && claude mcp add render --transport http --header "Authorization=Bearer $NEU" https://mcp.render.com/mcp`.

**Plugin-Install scheitert** — Marketplace nicht refresht. `claude plugin marketplace update <name>` dann re-install.

**Anthropic-Login schlägt fehl** — Browser-Flow benötigt Localhost-Callback. Ggf. Browser-Pop-up-Blocker deaktivieren.
