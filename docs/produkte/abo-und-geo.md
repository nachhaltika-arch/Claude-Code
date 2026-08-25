# PRODUKTDATENBLATT · ABO-BAS / ABO-PRO / GEO-01
## PFLEGE-ABONNEMENTS und GEO/GAIO ADD-ON


> ## Zum Stand am 23.08.2026
>
> - **GEO-01 ist im Lagebild als [L-99] geführt.** Die Leistung wird
>   beschrieben, aber nicht ausgeliefert: `qa_scanner` **prüft** `llms.txt` an
>   fremden Seiten, wir **erzeugen** es an unseren nicht. Kein Erzeuger, keine
>   Vorlage, kein Deploy-Schritt.
> - **ABO-BAS und ABO-PRO stehen als [L-101].** Es fehlen drei Dinge: eine
>   wiederkehrende Abrechnung (Stripe kann Abonnements, das System nutzt nur
>   Einmalzahlungen), eine **Zeiterfassung** für die zugesagten Stunden, und
>   ein Termingeber für das Quartals-Re-Audit. Der Termingeber ist der
>   kleinste Teil — der Scheduler läuft und führt bereits vierzehn Jobs.
> - **Die Zeiterfassung ist der riskanteste Punkt**, nicht der größte: G4
>   verspricht Nachbesserung ohne Berechnung. Ohne Erfassung ist nicht
>   bestimmbar, was schon verbraucht war.
> - Die mit ⚠️ markierten Preisannahmen sind weiterhin offen — in Stripe steht
>   heute kein Abonnement-Preis, mit dem sich abgleichen ließe.

---

# Teil A — PFLEGE BASIC (ABO-BAS)

| | |
|---|---|
| Artikelnummer | ABO-BAS |
| Preis | **79 € netto / Monat** ⚠️ Annahme, mit Stripe abgleichen |
| Umsatzsteuer | 19 % |
| Zahlungsbedingung | **Z4** (monatlich im Voraus, SEPA) |
| Laufzeit | 12 Monate, danach monatlich kündbar mit 1 Monat Frist |
| Freigabestatus | 🟠 Angebotszeitpunkt und Abwicklung unklar |

## Leistungsverzeichnis
| Pos. | Leistung | Frequenz |
|---|---|---|
| 1 | Hosting, SSL-Zertifikat, Domainverwaltung | laufend |
| 2 | Sicherheits- und Systemaktualisierungen | laufend |
| 3 | Tägliche Sicherung, Rücksicherung auf Anforderung | täglich |
| 4 | Verfügbarkeitsüberwachung mit Störungsmeldung | laufend |
| 5 | **Inhaltsänderungen bis 30 Minuten** | je Monat |
| 6 | Störungsbehebung bei Ausfällen, Reaktion innerhalb 1 Werktag | nach Bedarf |
| 7 | Jährliches Re-Audit nach Homepage-Standard | 1× jährlich |

**Nicht enthalten:** neue Seiten, Gestaltungsänderungen, Texterstellung, Kampagnen, Rechtstextaktualisierung.
Nicht verbrauchte Änderungsminuten verfallen und werden nicht übertragen.

---

# Teil B — PFLEGE PRO (ABO-PRO)

| | |
|---|---|
| Artikelnummer | ABO-PRO |
| Preis | **149 € netto / Monat** ⚠️ Annahme |
| Sonstiges | wie ABO-BAS |

## Zusätzlich zu Pflege Basic
| Pos. | Leistung | Frequenz |
|---|---|---|
| 8 | **Inhaltsänderungen bis 90 Minuten** (statt 30) | je Monat |
| 9 | **Monatlicher Leistungsbericht**: Aufrufe, Anfragen, Auffindbarkeit, Ladezeit | monatlich |
| 10 | **Quartalsweises Re-Audit** statt jährlich | 4× jährlich |
| 11 | Reaktionszeit bei Störungen 4 Stunden an Werktagen | nach Bedarf |
| 12 | Eine neue Unterseite pro Jahr enthalten | 1× jährlich |

---

## Verkaufszeitpunkt — kritisch

**Das Pflege-Abo muss im Moment der Abnahme angeboten werden, nicht danach.**

Bei der Abnahme ist der Kunde zufrieden, das Ergebnis ist sichtbar, die Beziehung ist warm. Vier Wochen später ist die Seite Alltag, und ein Abo wirkt wie ein Nachschlag. Der Angebotszeitpunkt ist der einzige echte Hebel bei diesem Produkt.

**Technische Folge:** Das Abo-Angebot gehört als **Pflichtschritt** in den Prozessflow, direkt nach dem Abnahmeprotokoll. Nicht als Erinnerung, nicht als Aufgabe — als Schritt, der abgeschlossen werden muss.

## Angebotstext (Baustein)

> **Instandhaltung und Gewährleistung**
>
> Eine abgenommene Website bleibt nicht von allein auf Standard. Browser, Suchmaschinen und Rechtslage ändern sich, Inhalte veralten.
>
> **Pflege Basic — 79 € netto monatlich:** Hosting, SSL, Sicherheitsaktualisierungen, tägliche Sicherung, Verfügbarkeitsüberwachung, 30 Minuten Inhaltsänderungen monatlich, jährliches Re-Audit.
>
> **Pflege Pro — 149 € netto monatlich:** zusätzlich 90 Minuten Änderungen monatlich, monatlicher Leistungsbericht, quartalsweises Re-Audit, verkürzte Reaktionszeit und eine neue Unterseite pro Jahr.

## Offene Punkte
| # | Punkt |
|---|---|
| 1 | 🔴 Tatsächliche Preise in Stripe prüfen — die hier genannten sind Annahmen |
| 2 | 🔴 Produkt trägt intern drei verschiedene Namen — vereinheitlichen |
| 3 | 🔴 Abo-Angebot als Pflichtschritt nach der Abnahme in den Prozessflow |
| 4 | Endpunkt `/api/maintenance/checkout` und Stripe-Webhook |
| 5 | Monatsbericht — überschneidet sich mit Hebel #5, gemeinsam bauen |
| 6 | Zeitkontingente müssen erfasst werden, sonst sind sie nicht durchsetzbar |

⚠️ **Punkt 6 wird unterschätzt.** Ein Kontingent, das niemand misst, ist eine Flatrate. Ohne Zeiterfassung je Kunde wird Pflege Pro zum Verlustgeschäft beim ersten anspruchsvollen Kunden.

---

# Teil C — GEO/GAIO ADD-ON (GEO-01)

| | |
|---|---|
| Artikelnummer | GEO-01 |
| Preis | **1.200 € netto** einmalig ⚠️ Annahme |
| Umsatzsteuer | 19 % |
| Zahlungsbedingung | **Z1** |
| Lieferzeit | 10 Werktage |
| Freigabestatus | 🔴 **gesperrt — Blocker L1** |

## Leistungsverzeichnis
| Pos. | Leistung |
|---|---|
| 1 | `llms.txt` mit Betriebs-, Leistungs- und Einzugsgebietsprofil |
| 2 | Vollständige `schema.org`-Auszeichnung: LocalBusiness, Service, FAQPage, ggf. JobPosting |
| 3 | **Ground Page** — maschinenlesbare Faktenseite |
| 4 | Strukturierung bestehender Inhalte in beantwortbare Frage-Antwort-Blöcke |
| 5 | Eintragskonsistenz prüfen: Name, Anschrift, Telefon über die wichtigsten Verzeichnisse |
| 6 | Automatisierte Verifikation der Auslieferung nach Veröffentlichung |
| 7 | Wirkungsbericht nach 60 Tagen |

**Nicht enthalten:** Garantie auf Nennung in KI-Antworten, Platzierungsgarantie bei Suchmaschinen, laufende Optimierung.

⚠️ **Die Abgrenzung ist verkaufsentscheidend.** Niemand kann eine Nennung in KI-Antworten garantieren. Wer es andeutet, verkauft eine Zusicherung, die er nicht halten kann. Der ehrliche Satz lautet: *„Wir stellen sicher, dass die technischen Voraussetzungen erfüllt sind. Ob und wie ein Assistent Sie nennt, entscheidet der Anbieter."*

## Offene Punkte
| # | Punkt |
|---|---|
| 1 | ✅ **erledigt 25.08.2026 — L1 ist zu.** Die Injektion stand bereits: `llms.txt` und die `schema.org`-Auszeichnung gehen mit **derselben** Auslieferung hoch wie die Seiten (`netlify_service.deploy_html`, Parameter `zusatzdateien`). Was fehlte, war Position 6 des Leistungsverzeichnisses — die **Nachschau**. Sie steht jetzt in `services/geo_auslieferung.py` und läuft nach jedem Deploy: Die veröffentlichte Adresse wird abgerufen, wie ein KI-Crawler sie abrufen würde. **Eine 200er-Antwort genügt dabei nicht** — viele Hosts liefern die Startseite für jede unbekannte Adresse aus, und eine Prüfung, die das durchgehen lässt, ist falsch grün. Antwortet die Seite selbst nicht, steht **nichts** im Befund: Über Dateien auf einer schweigenden Seite ist nichts bekannt, und eine Fehlanzeige wäre eine Behauptung |
| 2 | 🔴 Preis mit tatsächlichem Aufwand abgleichen — 1.200 € ist eine Annahme |
| 3 | 🟡 **Wirkungsbericht nach 60 Tagen: die Messmethode gibt es jetzt.** Seit dem 25.08. misst `services/ki_sichtbarkeit.py` die Nennung in vier KI-Systemen und schreibt einen Verlauf fort. Was fehlt, ist die Auswertung „nach 60 Tagen" gegen den Stand bei Auslieferung — eine Abfrage auf vorhandene Daten, kein neues Verfahren |
| 4 | Formulierung der Nicht-Garantie anwaltlich prüfen |
