# Produkt 04 — BUCH „Der Homepage-Standard"
Interne ID: `buch_homepage_standard` · Version 1.0 · Status: **Manuskript fertig, 5 Publikationsblocker offen**

---

## 1. Funktion im Portfolio
Das Buch verkauft keine Websprints. Es macht den **Mechanismus glaubwürdig**.

Ein Standard, der nur in einem Verkaufsgespräch existiert, ist eine Behauptung. Ein Standard mit ISBN, im Buchhandel gelistet, ist eine Referenz. Diese Differenz ist der gesamte Grund, warum wir 3.500 € statt 900 € nehmen können.

**Sekundärfunktion:** Das Buch ist geografisch entkoppelt. Es ist neben dem Workbook das einzige Portfolioelement, das die Kapazitätsgrenze des Kammerbezirks Koblenz (~300–370 Fälle/Jahr) nicht kennt.

## 2. Produktdaten
| | |
|---|---|
| Umfang | ~48.000 Wörter, 14 Kapitel + 3 Anhänge |
| Inhalt | 8-Kategorien-Auditsystem, 100 Punkte, Branchenklassen K1–K6 |
| Formate | Print (BoD, Print-on-Demand) + PDF/E-Book |
| Preis (Vorschlag) | **39,90 €** Print · **29,90 €** E-Book |
| Vertrieb | BoD → Buchhandel/Amazon + eigene Landingpage auf separater Netlify-Site |

## 3. 🔴 Buchpreisbindung — das teuerste Missverständnis

Das **Buchpreisbindungsgesetz (BuchPrG)** gilt in Deutschland für Printbücher **und** für E-Books. Konsequenzen, die häufig übersehen werden:

| Idee | Zulässig? |
|---|---|
| Buch als kostenloser Lead-Magnet verschicken | ❌ sehr wahrscheinlich unzulässig |
| „Buch gratis, nur Versand zahlen" (Funnel-Klassiker) | ❌ unzulässig |
| Buch im Bundle mit Workbook zum Rabattpreis | ❌ unzulässig, wenn der Buchanteil verbilligt wird |
| Kaufpreis des Buchs auf einen Websprint anrechnen | ❌ faktischer Rabatt, unzulässig |
| Buch zum vollen Ladenpreis an Innungen/Steuerberater abgeben | ✅ zulässig |
| Einzelne Kapitel als eigenständiges kostenloses PDF (kein Buch, keine ISBN) | ✅ zulässig |
| Verlagsexemplare an Presse/Rezensenten | ✅ zulässig |

**Konsequenz für die Vermarktungsstrategie:** Der Lead-Magnet ist **nicht das Buch**, sondern der kostenlose 100-Punkte-Check. Das Buch ist ein Autoritätsbeleg, kein Funnel-Einstieg.

⚠️ Ich bin kein Rechtsanwalt. Diese Einordnung ist eine Risikoauflistung, keine Rechtsberatung — sie gehört in dieselbe anwaltliche Prüfung wie Blocker B5.

## 4. Publikationsblocker (aus dem Manuskript-Stand)
| ID | Blocker | Wirkung, wenn ignoriert |
|---|---|---|
| B1 | K1–K6 Branchenklassen im Buch beschrieben, in KAS nicht implementiert | Das Buch beschreibt ein Produkt, das der Leser bei uns nicht kaufen kann |
| B2 | Score-Schwellen Frontend (85/70/50/30) ≠ Backend (95/85/70/50) | Leser rechnet nach, bekommt in der App ein anderes Ergebnis |
| B3 | Punktabzugstabellen plausibel konstruiert, nicht aus `audit_criteria.py` extrahiert | Buch und Software widersprechen sich in Zahlen |
| B4 | PageSpeed-Key fehlt → 18/100 Punkte nicht erhebbar | Der Standard ist im eigenen Werkzeug nicht vollständig messbar |
| B5 | 9 Rechtsaussagen ohne anwaltliche Prüfung | Haftung, Abmahnrisiko |

**B2 und B3 sind die gefährlichsten.** Sie erzeugen genau das, was ein Standard nicht darf: zwei Wahrheiten. Ein Handwerker, der im Buch liest „ab 85 Punkten abnahmefähig" und in der App „ab 95 Punkten" liest, verliert nicht das Vertrauen in die Software — er verliert es in den Standard. Und damit in den Preis.

## 5. Reihenfolge der Veröffentlichung
1. **B3 zuerst:** Punktetabellen aus `audit_criteria.py` generieren, nicht abschreiben. Das Buch muss aus der Software erzeugt werden, nicht neben ihr.
2. **B2:** eine einzige Schwellendefinition, an einer Stelle im Code, von der Frontend und Backend lesen.
3. **B4:** PageSpeed-Key auf Render setzen.
4. **B1:** K1–K6 implementieren — oder aus dem Buch streichen.
5. **B5:** anwaltliche Prüfung.
6. Dann BoD-Upload.

## 6. Technische Anforderungen in KAS
| Ebene | Anforderung | Status |
|---|---|---|
| Audit | `audit_criteria.py` als **einzige Quelle** für Punktetabellen | ❌ offen |
| Audit | Export-Skript: Kriterien → Markdown-Tabellen für das Manuskript | ❌ offen |
| Audit | Zentrale Schwellendefinition, FE liest vom BE | ❌ **Blocker** |
| Render | `PAGESPEED_API_KEY` gesetzt | ❌ **Blocker** |
| Shop | Verkauf läuft über BoD/Amazon — **kein eigenes Shop-Subsystem nötig** | ✅ bewusst so |
| Landingpage | Eigenständige Netlify-Site, Verweis auf Buchhandel | ❌ offen |

**Bewusste Entscheidung:** Das Buch wird **nicht** über KAS verkauft. Der Aufwand für Rechnungsstellung, GoBD-konforme Nummernkreise, Widerrufsbelehrung und 7-%-Umsatzsteuer steht in keinem Verhältnis zum Deckungsbeitrag. BoD übernimmt das.

## 7. Offene Entscheidungen
- Titel final?
- Preis 39,90 € oder 49,00 €?
- E-Book eigenständig oder nur als Bundle mit Print über BoD?
