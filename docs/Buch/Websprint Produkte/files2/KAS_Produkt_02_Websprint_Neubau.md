# Produkt 02 — WEBSPRINT NEUBAU
Interne ID: `websprint_neubau` · Version 1.0 · Status: **Entwurf, Prozessflow-Erweiterung nötig**

---

## 1. Positionierung in einem Satz
> Ein kompletter Neuaufbau inklusive Struktur, Texten und Bildkonzept — in 28 Tagen, zum Festpreis, mit Abnahmeprotokoll nach Homepage-Standard.

## 2. Zielkunde
Betrieb **ohne brauchbare Website** oder mit einer, die inhaltlich nicht mehr trägt: veränderte Leistungen, Generationswechsel, Umfirmierung, neue Zielgruppe. Typischer Audit-Score: **0–40 Punkte** (oder gar kein Audit möglich).

**Zusätzliches Erkennungsmerkmal:** Der Betrieb kann selbst nicht in zwei Sätzen sagen, was ihn von der Konkurrenz unterscheidet. Das ist der eigentliche Auslöser — nicht die Technik.

## 3. Leistungsumfang (verbindlich)
Alles aus Produkt 01, zusätzlich:
- **Positionierungsgespräch** (90 Min., strukturiert): Zielgruppe, Leistungsschwerpunkte, Abgrenzung, Wunschanfrage
- **Seitenstruktur/Bauplan** als Freigabedokument vor Baubeginn
- **Texterstellung** für bis zu **12 Seiten**
- **Bildkonzept + Bildbriefing** (Shotlist für Fotograf oder Auswahl aus lizenzierten Beständen)
- **2 Korrekturschleifen** im Festpreis
- **3 Monate Pflege-Abo Basic** enthalten
- **Re-Audit nach 3 Monaten** mit schriftlichem Ergebnis

**Nicht enthalten:** Fotoproduktion (nur Briefing), Logo-/CI-Entwicklung, Videoproduktion, Shop, mehrsprachige Ausführung, GEO/GAIO.

⚠️ **Abgrenzungsrisiko:** „Bildkonzept" wird von Kunden regelmäßig als „ihr macht die Fotos" verstanden. Im Angebot muss stehen: *Erstellung eines Fotobriefings; die Fotoproduktion ist nicht Bestandteil.*

## 4. Preis
**7.900 € netto**, Festpreis. Zahlung: 40 % bei Auftrag, 30 % bei Bauplan-Freigabe, 30 % bei Abnahme.

Die dreigeteilte Zahlung ist bewusst gewählt: Der Bauplan ist der Punkt, an dem der Kunde inhaltlich mitgearbeitet hat und aussteigen könnte. Eine Zahlung an dieser Stelle bindet.

## 5. Bauzeit
**28 Kalendertage** ab vollständiger Mitwirkung. Zusätzlich zu Produkt 01 gehört zur Mitwirkung:
5. Teilnahme am Positionierungsgespräch
6. Freigabe des Bauplans innerhalb von 5 Werktagen

⚠️ Die häufigste Ursache für Terminüberschreitung ist eine ausbleibende Bauplan-Freigabe. Die Frist muss **pausieren**, solange die Freigabe aussteht — sonst zahlt KOMPAGNON eine Verzugspauschale für die Langsamkeit des Kunden.

## 6. Garantien
Wie Produkt 01 (85/100 Punkte, Verzugspauschale), zusätzlich:
- **Bauplan-Garantie:** Gefällt der Bauplan nach der ersten Überarbeitung nicht, kann der Kunde gegen Zahlung der bis dahin fälligen 40 % aussteigen; keine weiteren Kosten.

Das ist die stärkste Risikoumkehr im Portfolio und rechtfertigt den Preisabstand zum RELAUNCH.

## 7. Verkaufsargumentation
**Eröffnung:**
„Sie brauchen keine neue Website. Sie brauchen erst eine Antwort auf die Frage, warum jemand Sie und nicht den Betrieb zwei Straßen weiter anruft. Die Website ist danach nur noch Handwerk."

**Metapher:** „Wir bauen nicht um. Wir reißen ab und bauen nach Bauplan neu — inklusive Statik."

**Abgrenzung nach oben verkaufen (Downsell-Schutz):** Wenn der Kunde beim RELAUNCH-Preis hängt, nicht rabattieren, sondern Umfang reduzieren: „Für 3.500 € bekommen Sie die Fertigstellung des Bestehenden. Für den Neubau brauche ich 7.900 €, weil die Texte darin stecken. Beides ist ehrlich — aber nicht dasselbe."

## 8. Technische Anforderungen in KAS
| Ebene | Anforderung | Status |
|---|---|---|
| DB | `product_type` = `websprint_neubau` | ❌ offen |
| DB | Feld für Bauplan-Freigabedatum (Fristpause!) | ❌ offen |
| Prozessflow | **Zusatzschritte:** Positionierungsgespräch, Bauplan-Freigabe, Textfreigabe | ❌ **kritisch** |
| Prozessflow | Bedingte Schrittsteuerung nach `product_type` | ❌ **kritisch** |
| Backend | Stripe: 3 Teilzahlungen statt 2 | ❌ offen |
| Backend | Angebots-PDF mit abweichendem Leistungsverzeichnis | ❌ offen |
| Frontend | Bauplan-Freigabe-Ansicht für Kunden | ❌ offen |
| Audit | wie Produkt 01 | ❌ **Blocker** |

⚠️ **Zwei Schritte voraus:** `ProzessFlowV3.jsx` ist heute auf einen festen 17-Schritt-Ablauf ausgelegt. Drei Produktvarianten mit unterschiedlicher Schrittanzahl bedeuten, dass entweder der Flow datengetrieben wird (Schrittliste aus der DB) oder es entstehen drei parallele Flow-Komponenten. Die zweite Variante wird sich nach dem dritten Bugfix rächen. **Empfehlung: Schrittdefinition in die Datenbank verlagern, bevor das zweite Produkt live geht.**

## 9. Offene Entscheidungen
- ✅ Preis entschieden: 7.900 € netto (23.08.2026)
- Werden 12 Seiten Text realistisch in 28 Tagen produziert — wer schreibt sie?
- Bildkonzept: eigene Lizenzbestände oder Kundenfotograf?
