# Produkt 01 — WEBSPRINT RELAUNCH
Interne ID: `websprint_relaunch` · Version 1.0 · Status: **verkaufbar nach Blocker-Fix L2/L3**

---

## 1. Positionierung in einem Satz
> Wir bauen Ihre bestehende Website in 14 Tagen auf den Homepage-Standard fertig — zum Festpreis, mit Abnahmeprotokoll.

## 2. Zielkunde
Handwerks- oder KMU-Betrieb mit **vorhandener Website**, die inhaltlich im Kern stimmt, aber technisch, rechtlich oder gestalterisch unter Standard liegt. Typischer Audit-Score bei Erstkontakt: **35–70 Punkte**.

**Erkennungsmerkmale:** Website 4+ Jahre alt · nicht mobil optimiert · kein SSL oder gemischte Inhalte · Impressum/Datenschutz veraltet · keine messbaren Conversion-Elemente · Ladezeit > 4 s.

**Nicht dieser Kunde:** Betrieb ohne Website, Betrieb mit Rebranding-Bedarf, Betrieb mit Recruiting als Hauptmotiv → siehe Produkt 02 / 03.

## 3. Leistungsumfang (verbindlich)
- HS-100 Eingangsaudit, dokumentiert
- Bis **6 Seiten** Umfang
- Übernahme und redaktionelle Optimierung vorhandener Texte (keine Neuerstellung)
- Aufbau in GrapesJS Studio, Komponentenbibliothek KOMPAGNON
- Responsive Umsetzung, Barrierefreiheits-Grundlagen
- Rechtstexte-Einbindung (Impressum, Datenschutz, ggf. Cookie-Hinweis) — **Texte vom Kunden oder dessen Anwalt**
- Deployment auf Netlify, DNS-Umstellung auf Kundendomain
- HS-100 Abnahmeaudit + **Abnahmeprotokoll als PDF**
- Einweisung 30 Minuten

**Ausdrücklich nicht enthalten:** Texterstellung, Fotografie, Logo/CI, Shop, Buchungssystem, mehrsprachige Ausführung, GEO/GAIO, laufende Pflege.

## 4. Preis
**3.500 € netto**, Festpreis. Zahlung: 50 % bei Auftrag, 50 % bei Abnahme.

## 5. Bauzeit und Fristbeginn ⚠️
**14 Kalendertage** — Fristbeginn ist **nicht** der Auftragseingang, sondern der Tag, an dem **alle Mitwirkungsleistungen** des Kunden vollständig vorliegen:
1. Zugang zur Domain/DNS-Verwaltung
2. Freigabe der zu übernehmenden Inhalte
3. Logo und Bildmaterial in verwendbarer Auflösung
4. Rechtstexte

Ohne diese Definition ist die 14-Tage-Garantie nicht haltbar. **Muss in AGB und Angebot identisch formuliert sein.**

## 6. Garantien
| Garantie | Inhalt | Rechtsfolge |
|---|---|---|
| Standard-Garantie | mind. **85/100** Punkte bei Abnahme | kostenfreie Nachbesserung bis erreicht |
| Bauzeit-Garantie | 14 Tage ab Mitwirkungsvollständigkeit | 100 € Nachlass je angefangenem Verzugstag, max. 1.000 € |

⚠️ **Die Standard-Garantie ist heute nicht erfüllbar**, weil ohne `PAGESPEED_API_KEY` auf Render 18 von 100 Punkten nicht erhoben werden können. Maximal erreichbarer Score aktuell: 82. Siehe Blocker L2.

## 7. Verkaufsargumentation
**Eröffnung (nach Check-Zustellung):**
„Ihr Betrieb steht bei 47 von 100 Punkten. Das heißt nicht, dass Ihre Website schlecht ist — es heißt, dass sie nicht fertig ist. 53 Punkte fehlen, und die meisten davon sind in 14 Tagen zu holen."

**Metapher:** „Sie würden ein Haus nicht ohne Abnahme beziehen. Ihre Website ist seit Jahren ohne Abnahme in Betrieb."

**Häufigste Einwände:**
| Einwand | Antwort |
|---|---|
| „Mein Neffe hat die gemacht." | „Dann hat er den Rohbau gestellt. Wir machen die Abnahme — er kann sie danach weiter pflegen." |
| „3.500 € ist viel." | „Was kostet Sie ein Auftrag, den Sie nicht bekommen, weil der Kunde die Seite auf dem Handy nicht lesen konnte?" |
| „Das kann ich für 900 € haben." | „Können Sie. Aber Sie bekommen kein Abnahmeprotokoll und keine Punktzahl. Sie bekommen wieder eine Behauptung." |

## 8. Technische Anforderungen in KAS
| Ebene | Anforderung | Status |
|---|---|---|
| DB | `product_type` muss `websprint_relaunch` kennen | ❌ offen |
| DB | Migration bestehender `website`-Deals auf neuen Wert | ❌ offen |
| Backend | Stripe Price ID Mapping | ❌ offen |
| Backend | Angebots-PDF-Template | ❌ offen |
| Prozessflow | 17-Schritt-Flow passt unverändert | ✅ |
| Frontend | Produktauswahl im Deal, Preisseite | ❌ offen |
| Audit | PageSpeed-Key auf Render | ❌ **Blocker** |
| Audit | Einheitliche Score-Schwellen FE/BE | ❌ **Blocker** |

## 9. Offene Entscheidungen
- Endgültiger Produktname (RELAUNCH vs. STANDARD vs. FERTIGSTELLUNG)
- Höhe der Verzugspauschale
- Ob 85 Punkte oder 80 Punkte garantiert werden (abhängig von Blocker L2)
