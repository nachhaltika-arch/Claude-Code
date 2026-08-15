---
name: resume-point-2026-08-14
description: "Stand 2026-08-14 — 23 Commits, PR #36 gemerged; Kundendaten waren ohne Login offen, Audit misst jetzt je Branchenklasse; 9 Commits auf staging ungetestet"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2304b374-a627-442b-9197-998d31d1113e
  modified: 2026-08-14T21:46:53.145Z
---

**Vollständiger Tagesbericht im Repo: `docs/stand-2026-08-14.md`.** 23 Commits,
vier Sitzungen. PR #36 ist um 22:48 nach `main` gemerged (Sicherheitsfix,
Branchenmodell, Assistent, Widget, Zustellung).

**Das Muster des Tages:** Dreimal war die Rechnung richtig und die Aussage
trotzdem falsch, weil der Maßstab von woanders kam — der Assistent erfand
Fakten über den Kundenbetrieb, das Audit maß einen Kandidatenauftritt am
SHK-Maßstab, das PDF eines Ingenieurbüros druckte „Branche / Gewerk:
Schreiner".

**Der schwerste Befund hat damit nichts zu tun:** `GET /api/leads/` gab die
volle Leadliste ohne Login aus — **produktiv**. Dazu DELETE, PATCH,
CSV-Export und die kostenpflichtigen Läufe; 31 von 42 Lead-Routen, alle 7
Kunden-Routen, 9 Usercards, plus Alias-Router. Ursache war die Richtung: Die
Anmeldung hing an jeder Route statt am Router. Jetzt am Router, öffentliche
Ausnahmen in einem eigenen Router mit eigener Prüfung. **Offen:** ob die
Leadverwaltung nur Administratoren gehört — das Kundenportal ruft PATCH auf
seinen eigenen Lead auf.

**Audit misst jetzt je Branchenklasse, nicht nur je Text.** Sechs gemessene
Kriterien (`ih_leistungsseiten`, `cv_vertrauen`, `cv_cta`, `cv_kontakt`,
`se_meta`, `se_schema`) rechnen gegen den Maßstab der erkannten Klasse. Die
Stichworte stehen in `services/audit_industry_signals.py`, der messbaren
Entsprechung zur Prosa in `audit_industry_profiles.py` — **wer dort eine Zeile
ändert, ändert eine Bewertung.**

**Die tragende Entscheidung ist die Reihenfolge:** Die Klasse steht erst nach
der KI-Erkennung fest, also *nach* der Erhebung. Deshalb sucht die Erhebung den
Verband aller Klassen und merkt sich je Fund die Begriffe; welcher Treffer
zählt, entscheidet `audit_scoring`. Wer hier etwas ergänzt: **zusammengesetzte
Merkmale gehören in die Bewertung, nicht in die Erhebung** — sonst hätten alte
Fakten sie nie und würden dafür abgewertet, siehe [[migration-trap-main-py]]
für dieselbe Bauart.

**Die Vermutung als Befund** — der Fehler, der zum Abend führte: `scraper.py`
rät das Gewerk über Stichworte („holz" → Schreiner), und bei Widget-Analysen
gibt niemand eines mit. Der geratene Wert ging in den KI-Prompt *und* ins
PDF-Protokoll. `routers/audit.py` speichert die Vermutung nicht mehr; das PDF
zeigt die erkannte Branche samt Maßstab. `lead_enrichment.py` rät weiter —
offen, aber in einer Leadliste vertretbar.

**Nicht in `main`: neun Commits auf `staging`** — Doku-Umzug in Ordner plus die
vier Audit-Commits des Abends. Sie sind noch nie auf dem Staging-Server
gelaufen.

**Nächster Schritt:** echte Widget-Analyse über Staging, PDF-Protokoll ansehen
(erkannte Branche + vollständiger Ortsname), dann erst nach `main`. Danach: der
Katalog ist nie gegen eine echte fremde Website gelaufen (§ 6.4, dort als
wichtigster Punkt markiert).

**Render bleibt blockiert** (`unauthorized`) — daran hängen PageSpeed-Schlüssel,
Ausgangswerte der Briefing-Abschlussquote und die drei abweichenden
Mailadressen. Ein API-Schlüssel löst alle drei.

Der scharfe Lauf des Morgens und die Modell-Falle stehen in
`docs/projekt-assistent-anforderungen.md` § 9.4/9.5: Der Antwortdeckel begrenzt
bei denkenden Modellen Denken und Text gemeinsam, die übrigen KI-Router stehen
weiter auf `claude-sonnet-4-6` mit `max_tokens=800`.

Weiter offen: Qualitätsschleife Stufe C, siehe [[resume-point-2026-08-13]];
Widget-Restpunkte bei David, siehe [[resume-point-2026-08-12]].
Zum Release-Rhythmus [[feedback-pr-only-fridays]].
