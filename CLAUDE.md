# KOMPAGNON — Claude Code Regeln

## PFLICHT-CHECK bei jeder Session
Bevor irgendein Code angefasst wird, führe aus:
  git remote -v
  git branch --show-current

Erwartetes Ergebnis:
  origin → https://github.com/nachhaltika-arch/Claude-Code
  current branch → staging

Falls EINES davon nicht stimmt:
  → STOPPE sofort
  → Melde: "Falsches Repo oder falscher Branch. Bitte prüfen."
  → Führe NICHTS aus bis der Nutzer bestätigt

## Branch-Regeln

| Branch  | Zweck            | Wer darf pushen                  |
|---------|------------------|----------------------------------|
| main    | Produktiv / Live | Nur via Pull Request aus staging |
| staging | Test / Stage     | Claude Code direkt               |

- Claude Code arbeitet IMMER auf: staging
- NIE direkt auf main pushen
- NIE neue zusätzliche Branches erstellen
- Nach jedem Commit sofort: git push origin staging

## Repo-Regel
- Einziges erlaubtes Repo: nachhaltika-arch/Claude-Code
- NIE in anderen Repos Änderungen machen

## Commit-Regel
- Nach jedem Prompt: genau ein Commit + sofortiger Push
- Commit-Message immer auf Englisch
- Branch immer staging

## Deploy-Info
Render.com deployt automatisch bei jedem Push:
- staging → Stage-Server (Test)
- main    → Produktiv-Server (Live, nur nach PR-Merge)

Frontend Stage: https://kompagnon-frontend.onrender.com
Backend Stage:  https://claude-code-znq2.onrender.com

## Release-Prozess (Stage → Produktion)
1. Auf staging entwickeln und testen
2. Auf GitHub: Pull Request staging → main erstellen
3. PR prüfen und manuell mergen
4. Render deployt automatisch auf Produktion

Claude Code erstellt NIEMALS selbst einen PR oder merged in main.
