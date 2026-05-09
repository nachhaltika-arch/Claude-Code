# Claude Code Setup für KOMPAGNON

Dieses Verzeichnis enthält die Claude-Code-Konfiguration des Solo-Operators (David), checked in als Single Source of Truth, damit jeder neue Rechner (z.B. MacBook) reproduzierbar das gleiche Setup bekommt.

## Was hier liegt

| Pfad | Was |
|------|-----|
| `agents/*.md` | 3 Custom-Agents: build-error-resolver, code-reviewer, security-reviewer |
| `rules/common/*.md` | 10 globale Coding-Rules (verbindlich für alle Projekte) |
| `rules/typescript/*.md` | 5 TypeScript-spezifische Rules |
| `memory/*.md` | 16 Memory-Files (User-Profile, Resume-Points, Decisions, Plans) — wird auf Mac per Symlink gesynct |
| `settings.json.template` | User-level Settings (Plugins, Marketplaces, Hooks) |
| `settings.local.json.template` | Permission-Allowlist (Auto-Approval für häufige Commands) |
| `mcp-servers.json.template` | MCP-Server-Configs mit `${ENV_VAR}`-Placeholders (Tokens NICHT im Repo!) |

## Installation auf neuem Rechner

→ Ausführen: `bash scripts/setup-claude-code.sh` (siehe `docs/claude-code-setup.md` für Details).

Das Script:
1. Installiert Claude Code CLI global via npm
2. Kopiert agents/rules in `~/.claude/`
3. Templated `settings.json` + `settings.local.json` aus den Templates
4. Fragt nach Tokens (GitHub PAT + Render API) und schreibt sie in `~/.claude.json`
5. Installiert die 3 Plugins (claude-mem, context-mode, last30days-skill)
6. Verifiziert Setup

## Was hier NICHT liegt (intentional)

- **Anthropic-Auth** (`.credentials.json`) — wird vom Claude-CLI per OAuth-Login pro Rechner separat erzeugt
- **Tokens** (GitHub PAT, Render API Bearer) — werden zum Setup-Zeitpunkt erfragt, nie im Repo
- **Sessions/History/Cache** — sind ephemer und rechnerspezifisch
- **Plugin-Cache** — wird beim ersten Plugin-Install neu aufgebaut
