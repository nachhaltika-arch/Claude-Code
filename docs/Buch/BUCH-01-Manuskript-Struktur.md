# BUCH-01 — Manuskript-Struktur & Single Source of Truth

## Warum dieser Schritt zuerst kommt

Bevor auch nur ein Satz geschrieben wird, brauchen wir einen Ort im Repository, an dem
das Buch lebt, und **eine einzige Datei, in der die Bewertungslogik des Homepage
Standards steht**.

Der Grund: Die 100 Punkte stehen heute an drei verschiedenen Stellen im Code
(`AuditReport.jsx`, `HomepageChecklist.jsx`, `audit-widget.html`). Wenn du eine davon
änderst und das Buch bereits gedruckt ist, widersprechen sich Produkt und Buch. Wir legen
deshalb eine gemeinsame Definitionsdatei an und einen Prüfbefehl, der Abweichungen meldet.

**Was du danach hast:** Einen Ordner `/buch/` im Repo, eine Datei
`shared/homepage-standard.json` als verbindliche Wahrheit, und einen Befehl
`npm run check:standard`, der dir sagt, ob Buch und Audit noch übereinstimmen.

---

## PFLICHT-CHECK

```bash
git remote -v
git branch --show-current
```

Erwartet: `nachhaltika-arch/Claude-Code` · `staging`
Abweichung → **STOPP**.

---

## PROMPT FÜR CLAUDE CODE

> Zeilenweise eingeben (Windows-Regel: nicht als Block einfügen).

```
Führe zuerst aus: git remote -v && git branch --show-current
Erwartet: origin = nachhaltika-arch/Claude-Code, branch = staging
Bei Abweichung: stoppe und melde.

SCHRITT 1
Lies die Datei frontend/src/components/AuditReport.jsx und extrahiere daraus vollständig:
- alle 6 Kategorien mit key, label, max-Punktzahl, color
- alle Unterkriterien je Kategorie mit key, label, max
Lies zusätzlich frontend/src/components/HomepageChecklist.jsx und extrahiere je Item:
id, label, desc, law, critical, auditField, maxScore.
Lies frontend/public/embed/audit-widget.html und extrahiere die Stufen-Schwellen.

SCHRITT 2
Lege die Datei shared/homepage-standard.json an. Struktur:
{
  "version": "2026.1",
  "released": "2026-09-01",
  "total_points": 100,
  "levels": [
    { "name": "Platin",  "min": 85 },
    { "name": "Gold",    "min": 70 },
    { "name": "Silber",  "min": 50 },
    { "name": "Bronze",  "min": 30 },
    { "name": "Nicht konform", "min": 0 }
  ],
  "categories": [ ... aus Schritt 1 ... ],
  "checklist": [ ... aus Schritt 1 ... ]
}
Die Summe aller category.max MUSS exakt 100 ergeben. Prüfe das und melde das Ergebnis.

SCHRITT 3
Lege folgende Ordnerstruktur an:

buch/
  README.md
  manuskript/
    00-titelei.md
    01-warum.md
    02-das-system.md
    03-recht.md
    04-performance.md
    05-barrierefreiheit.md
    06-sicherheit.md
    07-seo.md
    08-ux.md
    09-selbsttest.md
    10-top20-fehler.md
    11-massnahmenplan.md
    12-grenzen-des-selbermachens.md
    90-anhang-glossar.md
    91-anhang-punktetabelle.md
    92-anhang-vorlagen.md
  assets/
    .gitkeep
  build/
    .gitkeep

Jede Manuskript-Datei bekommt einen YAML-Frontmatter-Kopf:
---
kapitel: 3
titel: "Rechtliche Compliance"
punkte: 30
status: entwurf
zuletzt_geprueft: 2026-08-14
---
und darunter nur die Überschrift des Kapitels als Platzhalter.

SCHRITT 4
Lege scripts/check-homepage-standard.js an. Das Skript:
- liest shared/homepage-standard.json
- liest die Kategorien/Punkte aus frontend/src/components/AuditReport.jsx per Regex
- vergleicht beide
- gibt bei Abweichung eine Liste der Unterschiede aus und beendet mit exit code 1
- gibt bei Übereinstimmung "OK: Buch und Audit stimmen ueberein (Version X)" aus
Trage in package.json unter scripts ein: "check:standard": "node scripts/check-homepage-standard.js"

SCHRITT 5
Lege buch/README.md an mit: Zweck des Ordners, Erklaerung der Single-Source-of-Truth-Regel,
Hinweis dass nach jeder Aenderung am Audit "npm run check:standard" laufen muss.

SCHRITT 6
Verifiziere:
node -e "const d=require('./shared/homepage-standard.json'); console.log('Summe:', d.categories.reduce((a,c)=>a+c.max,0))"
npm run check:standard
ls -R buch/

SCHRITT 7
git add -A
git commit -m "Add book manuscript structure and Homepage Standard single source of truth"
git push origin staging
```

---

## VERIFIKATION (das prüfst du selbst)

| Befehl | Erwartete Ausgabe |
|---|---|
| `node -e "..."` (Schritt 6) | `Summe: 100` |
| `npm run check:standard` | `OK: Buch und Audit stimmen ueberein (Version 2026.1)` |
| `ls buch/manuskript/` | 15 `.md`-Dateien |

**Wenn die Summe nicht 100 ist:** Das ist ein echter Fund. Dann stimmt schon heute etwas
im Audit nicht. Melde mir das Ergebnis, bevor du weitermachst.

---

## COMMIT-MESSAGE

```
Add book manuscript structure and Homepage Standard single source of truth
```

---

## ZWEI SCHRITTE VORAUS

- **Version 2026.1** ist bewusst gesetzt. Sobald das Buch gedruckt ist, darf sich diese
  Zahl nur mit einer neuen Auflage ändern. Die Versionsnummer gehört später sichtbar in
  den Audit-Report und aufs Buchcover — dann sieht der Kunde sofort, ob beide zusammenpassen.
- **Der Drift-Check gehört später in die CI.** Sobald du GitHub Actions nutzt, läuft
  `npm run check:standard` bei jedem Push. Dann kann niemand mehr unbemerkt das Audit
  ändern, während das Buch im Druck ist.
