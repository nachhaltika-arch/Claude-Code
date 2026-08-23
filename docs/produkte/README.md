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

## Was hier liegt — und was fehlt

Stand 23.08.2026. Die Datenblätter kamen über den Chat, nicht als Dateien.
Beim Kontextwechsel während derselben Sitzung ging der Volltext der meisten
verloren. **Erhalten und abgelegt sind vier:**

| Datei | Inhalt |
|---|---|
| `00-angebotsbaukasten.md` | Kataloge M/Z/G/A, Preisübersicht, Angebotsbausteine |
| `ws-neu-01.md` | Websprint Neubau — mit Korrekturkopf (L2/L3 hinfällig) |
| `ws-sys-01.md` | Websprint System — mit Korrekturkopf (L1 bestätigt = L-99) |
| `orders/prompt-08.md` | Anrechnung G5 — mit Korrekturkopf (Branch und URL tot) |

**Nicht mehr rekonstruierbar, bitte erneut senden, falls sie versioniert
werden sollen:** WS-REL-01, CHK-000 und CHK-PLU-01, BUCH-01/02, WB-01,
ABO-BAS/ABO-PRO/GEO-01, die Orders-Übersicht, die Orders-Prompts 01–07 und
der Projektplan KW35–52.

**Ihre Befunde sind trotzdem gesichert.** Was aus ihnen an offenen Punkten
hervorging, steht als reguläre Lücke im Lagebild und hängt nicht mehr an
diesen Dateien:

- **L-97** — zwei Produktwelten: die Angebotspreise und die Preise in
  `products` sind verschiedene Linien
- **L-98** — der PageSpeed-Schlüssel steht im Klartext im Protokoll
- **L-99** — GEO/GAIO wird verkauft, aber nicht ausgeliefert *(= L1 aus WS-SYS-01)*
- **L-100** — für die digitalen Produkte gibt es keinen Bestellweg
- **L-101** — das Pflege-Abo hat weder wiederkehrende Abrechnung noch Zeiterfassung

**Was sich beim Nachmessen als erledigt herausstellte** und deshalb *keine*
Lücke wurde: der PageSpeed-Schlüssel arbeitet (Blocker L2/B4), die
Score-Schwellen sind identisch (L3/B2), die Routenkollision aus A05 gibt es
nicht, Double-Opt-in (A08) und der geschützte PDF-Endpunkt (A09) sind
gebaut, A27 und A28/A29 sind seit dem 22./23.08. abgeschlossen.
