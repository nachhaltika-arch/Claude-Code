# KOMPAGNON — Claude Code Regeln

## PFLICHT-CHECK bei jeder Session
Bevor irgendein Code angefasst wird, führe aus:
  git remote -v
  git branch --show-current

Erwartetes Ergebnis:
  origin → https://github.com/nachhaltika-arch/Claude-Code
  current branch → claude/kompagnon-automation-system-FapM9

Falls EINES davon nicht stimmt:
  → STOPPE sofort
  → Melde: "Falsches Repo oder falscher Branch. Bitte prüfen."
  → Führe NICHTS aus bis der Nutzer bestätigt

## Branch-Regel
- Immer auf Branch: main
- NIE automatisch neue Branches erstellen
- NIE auf claude/* Branches pushen
- Nach jedem Commit sofort: git push origin main

## Repo-Regel
- Einziges erlaubtes Repo: nachhaltika-arch/Claude-Code
- NIE in Silva-Viridis-Portal arbeiten
- NIE in anderen Repos Änderungen machen

## Commit-Regel
- Nach jedem Prompt: genau ein Commit + sofortiger Push
- Commit-Message immer auf Englisch
- Branch immer main
