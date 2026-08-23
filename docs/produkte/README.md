# Produktdatenblätter und Angebotsbaukasten

Stand der Ablage: 23.08.2026 · Quelle: von David erstellt, hier versioniert.

| Datei | Inhalt |
|---|---|
| `00-angebotsbaukasten.md` | Kataloge M (Mitwirkung), Z (Zahlung), G (Garantien), A (Abgrenzung), Preise, Textbausteine |
| `ws-rel-01.md` | Websprint Relaunch, 3.500 € |
| `ws-neu-01.md` | Websprint Neubau, 7.900 € |
| `ws-sys-01.md` | Websprint System, 12.900 € — **Verkaufssperre** |
| `chk-000-und-plus.md` | 100-Punkte-Check (0 €) und Check PLUS (249 €) |
| `buch-01-02.md` | „Der Homepage-Standard", Print und E-Book |
| `wb-01.md` | Workbook, 149 € |
| `abo-und-geo.md` | Pflege Basic/Pro, GEO/GAIO Add-on |
| `projektplan-kw35-52.md` | Projektplan bis 18.12.2026, drei Bahnen |
| `orders/` | Acht Prompts für das Bestell-Subsystem |

## Wie diese Dateien zum Lagebild stehen

Die Datenblätter tragen eine **eigene** Blockernummerierung (L1, L2, L3, B1–B5).
Sie ist **nicht** die des Lagebilds (`docs/soll-ist-analyse.md`, L-01 bis L-99).

Beim Abgleich am 23.08.2026 stellte sich heraus: Ein großer Teil dieser Blocker
ist bereits behoben. Die Lückenliste führt seither die **verbliebenen** Punkte
als reguläre Einträge und verweist von dort auf das jeweilige Datenblatt —
damit es eine Liste gibt und nicht zwei.

**Regel:** Was hier als Blocker steht, gilt erst, wenn es auch in der
Lückenliste steht. Diese Dateien beschreiben Produkte; der Zustand des Systems
steht im Lagebild.

---

## Was hier liegt

Stand 23.08.2026, vollständig. Die Datenblätter kamen zuerst über den Chat und
gingen bei einem Kontextwechsel verloren; David hat sie am selben Tag als
Dateien nachgeliefert. **Maßgeblich ist die Datei**, nicht die Chat-Fassung —
alle Blätter unten stammen aus den gelieferten Dateien, ergänzt um einen
Korrekturkopf, wo eine Angabe am laufenden System widerlegt wurde.

| Datei | Produkt | Katalogstand |
|---|---|---|
| `00-angebotsbaukasten.md` | Kataloge M/Z/G/A, Preise, Angebotsbausteine | — |
| `ws-rel-01.md` | Websprint Relaunch, 3.500 € netto | **live** |
| `ws-neu-01.md` | Websprint Neubau, 7.900 € netto | **live** |
| `ws-sys-01.md` | Websprint System, 12.900 € netto | Entwurf (L-99) |
| `chk-000-und-plus.md` | 100-Punkte-Check und Check PLUS | Check frei · PLUS braucht L-100 |
| `buch-01-02.md` | Buch und E-Book | verlagsseitig, nicht im System |
| `wb-01.md` | Workbook, 149 € netto | braucht L-100 |
| `abo-und-geo.md` | Pflege Basic/Pro und GEO-Add-on | L-99, L-101 |
| `orders/prompt-08.md` | Anrechnung G5 | braucht L-100 |

**Die Blockernummern der Datenblätter (L1, L2, L3, B1–B5) sind nicht die des
Lagebilds.** Was dort als Blocker steht, gilt erst, wenn es auch in der
Lückenliste steht. Diese Dateien beschreiben Produkte; der Zustand des Systems
steht im Lagebild.

## Was beim Nachmessen von den 13 Blockern übrig blieb

**Fünf sind echt** und werden als reguläre Lücken gezählt:

- **L-97** — zwei Produktwelten *(geschlossen am 23.08.: die Websprints sind
  jetzt der Katalog)*
- **L-98** — der PageSpeed-Schlüssel steht im Klartext im Protokoll
- **L-99** — GEO/GAIO wird verkauft, aber nicht ausgeliefert *(= L1 aus WS-SYS-01)*
- **L-100** — für die digitalen Produkte gibt es keinen Bestellweg
- **L-101** — das Pflege-Abo hat weder wiederkehrende Abrechnung noch Zeiterfassung

**Acht haben sich aufgelöst:** Der PageSpeed-Schlüssel arbeitet (L2/B4), die
Score-Schwellen sind beidseitig 95/85/70/50 identisch (L3/B2), die
Routenkollision aus A05 gibt es nicht, Double-Opt-in (A08) und der geschützte
PDF-Endpunkt (A09) sind gebaut, A27 und A28/A29 waren am 22./23.08. bereits
fertig — zusammen rund 20 geplante Entwicklungstage.

**Dass L2 und L3 fielen, hat zwei Produkte freigegeben:** WS-REL-01 nannte
genau diese beiden als Freigabebedingung, WS-NEU-01 zusätzlich die
Prozessflow-Erweiterung (ein interner Ablauf, kein Verkaufshindernis). Beide
stehen seither im Katalog auf `live`.

## Die acht Orders-Prompts

Nur `orders/prompt-08.md` liegt vor. **Alle acht nennen zwei tote Angaben** —
den Branch `claude/kompagnon-automation-system-FapM9` (existiert nicht, die
`claude/*`-Branches wurden am 01.05.2026 verworfen) und die Backend-URL
`claude-code-znq2.onrender.com` (antwortet 503; der Dienst läuft seit dem
23.08. in Frankfurt unter `api.kompagnon.group`). Wer sie ausführt, ohne das
zu korrigieren, arbeitet gegen nichts.
