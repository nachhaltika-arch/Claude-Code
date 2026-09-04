# Produkt 03 — WEBSPRINT SYSTEM
Interne ID: `websprint_system` · Version 1.0 · Status: 🔴 **NICHT VERKAUFBAR — Kernleistung nicht in Produktion**

---

## ⛔ Verkaufssperre

Dieses Produkt verspricht Sichtbarkeit in KI-Assistenten über `llms.txt`, `schema.org`-Auszeichnung und Ground Page. **Diese Artefakte werden derzeit nicht in die auf Netlify ausgelieferten Kundenseiten injiziert.** Dasselbe gilt für GA4, Meta Pixel und die Tracking-Grundlage der Quartals-Re-Audits.

Ein Verkauf vor Schließung von Blocker L1 wäre eine Zusicherung einer Eigenschaft, die das Werk nicht hat — mangelhafte Leistung nach § 633 BGB und zugleich irreführende geschäftliche Handlung nach § 5 UWG.

**Freigabe erst nach:** technischer Verifikation an einer echten Kundendomain, dokumentiert.

---

## 1. Positionierung in einem Satz
> Gefunden werden bei Google — und genannt werden von KI-Assistenten. Mit vierteljährlichem Nachweis über zwölf Monate.

## 2. Zielkunde
Betrieb mit **Wachstums- oder Personaldruck**, der Marketing nicht als Kostenstelle, sondern als Beschaffungskanal versteht. Meist: 15+ Mitarbeiter, mehrere Standorte oder ausgeprägter Fachkräftemangel.

**Erkennungsmerkmal:** Der Betrieb hat bereits Geld für Werbung ausgegeben und weiß nicht, was es gebracht hat.

## 3. Leistungsumfang (verbindlich)
Alles aus Produkt 02, zusätzlich:
- Bis **20 Seiten** Umfang
- **Karriere-/Recruitingseite** mit Bewerbungsformular
- **GEO/GAIO-Layer:** `llms.txt`, vollständige `schema.org`-Auszeichnung (LocalBusiness, Service, FAQ, JobPosting), Ground Page
- **Messgrundlage:** GA4 + Consent-konforme Einbindung, Microsoft Clarity (EU-Residenz, Text maskiert, IP anonymisiert)
- **12 Monate Pflege-Abo Pro**
- **Quartalsweises Re-Audit** (4×) mit schriftlichem Bericht und Maßnahmenliste
- **Jahresgespräch** (90 Min.)

## 4. Preis
**12.900 € netto.** Zahlung: 40 % Auftrag, 30 % Bauplan, 30 % Abnahme. Pflege ab Monat 13 regulär.

**Preisbegründung gegenüber dem Kunden:** Der reine Bauanteil entspricht dem NEUBAU. Die Differenz von 6.000 € entfällt auf Recruitingseite, GEO-Layer und zwölf Monate begleitete Instandhaltung mit vier dokumentierten Prüfungen. Das ist rechenbar, nicht gefühlt.

## 5. Bauzeit
**42 Kalendertage** ab vollständiger Mitwirkung.

## 6. Garantien
- Standard-Garantie 85/100 bei Abnahme
- **Quartals-Garantie:** Fällt der Score in einem der vier Re-Audits unter 85, Nachbesserung ohne Berechnung
- Bauzeit-Garantie 42 Tage, 100 €/Verzugstag, max. 2.000 €

⚠️ Die Quartals-Garantie ist eine **Zwölf-Monats-Verpflichtung mit unbestimmtem Aufwand**. Ein Score kann durch externe Faktoren fallen (Google-Update, Änderung der Bewertungskriterien, Kunde ändert Inhalte selbst). Der Garantietext muss ausschließen: kundenseitige Änderungen, Änderungen des Homepage-Standards selbst, höhere Gewalt bei Drittdiensten.

## 7. Verkaufsargumentation
**Eröffnung:**
„Wenn jemand heute ein Angebot für eine Heizungssanierung sucht, fragt er nicht mehr nur Google. Er fragt ChatGPT. Die Frage ist, ob Ihr Betrieb in dieser Antwort vorkommt — und das entscheidet sich an Dateien auf Ihrem Server, die es bei Ihnen aktuell nicht gibt."

**Metapher:** „Google ist das Branchenbuch. KI-Assistenten sind der Kollege, den man fragt. Sie sind im Branchenbuch — aber der Kollege kennt Sie nicht."

## 8. Technische Anforderungen in KAS
| Ebene | Anforderung | Status |
|---|---|---|
| Deploy | **Injection von `llms.txt`, `schema.org`, GA4, Clarity in Netlify-Build** | 🔴 **Blocker L1** |
| Deploy | Verifikation der Injection nach Go-Live (automatisch) | ❌ offen |
| Backend | Quartals-Re-Audit als APScheduler-Job (eigene `SessionLocal()`, `finally: db.close()`) | ❌ offen |
| Backend | Berichtsversand über Brevo | ❌ offen (überschneidet sich mit Hebel #5) |
| DB | `product_type` = `websprint_system`, Feld `audit_schedule` | ❌ offen |
| Prozessflow | Zusatzschritte GEO-Setup, Karriereseite, Messgrundlage | ❌ offen |
| Frontend | Kundenansicht Quartalsberichte | ❌ offen |
| Recht | Consent-Management für GA4/Clarity in der Kundenseite | ❌ **offen und haftungsrelevant** |

⚠️ **Zwei Schritte voraus — DSGVO-Kettenhaftung:** Wenn KOMPAGNON GA4 und Clarity in Kundenseiten einbaut, wird KOMPAGNON zum Auftragsverarbeiter des Kunden. Das erfordert einen **AV-Vertrag je Kunde** und einen Consent-Layer, der *vor* dem Laden der Skripte greift. Ohne beides haftet am Ende der Kunde — und regressiert gegen uns. Das ist kein Detail, das man nach dem Verkauf klärt.

## 9. Offene Entscheidungen
- Produkt zurückstellen bis L1 geschlossen ist, oder ohne GEO-Layer als „SYSTEM light" starten?
- 12.900 € oder 9.900 €?
- Quartals-Garantie überhaupt geben, oder nur Quartalsbericht ohne Nachbesserungszusage?
