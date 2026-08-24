# Aufgabe 1.1 · Tabellen einsetzen — Teilstand

**Datum:** 24.08.2026
**Wichtig:** Phase 1 hat als Eingangsbedingung Tor 0. **Tor 0 ist nicht geschlossen** — `BUCH-F1` und `F2` sind nicht im Repo. Was hier steht, ist der heute erzeugbare Teil.

---

## Eingesetzt — erzeugt statt getippt

| Stelle | Tabelle | Quelle |
|---|---|---|
| Kapitel 3.2 | Kategorieübersicht | erzeugt, Beschreibungsspalte erhalten |
| Kapitel 5.1 bis 12.1 | **acht Kriterientabellen** | erzeugt |
| Kapitel 13.2 | Klassenmaxima | geprüft, stimmte bereits |
| Kapitel 13.8 | Stufen | geprüft, stimmte bereits |
| Anhang B | vollständig | erzeugt |

## 🔴 Was der Abgleich gefunden hat

**Drei verschiedene Spaltenstrukturen über acht Kapitel.**

| Kapitel | Spalten vorher |
|---|---|
| 5, 6, 7, 8, 9 | Code · Kriterium · Punkte · Gilt für |
| 10 | Code · Kriterium · Punkte · Erhebung |
| 11 | Code · Kriterium · Punkte · Erhebung · Klasse |
| 12 | Code · Kriterium · Punkte · Erhebung · Gilt für |

**Ein Leser, der Teil II durchgeht, findet dieselbe Tabelle in drei Formen.** Das ist beim Schreiben nicht aufgefallen und wäre beim Lektorat vermutlich auch nicht — es fällt erst auf, wenn eine Maschine dieselbe Tabelle achtmal erzeugt.

**Jetzt einheitlich:** Code · Kriterium · Punkte · Erhebung · Gilt für.

**Nebengewinn:** Die Erhebungsart steht jetzt in allen acht Kategoriekapiteln. Kapitel 3.4 verspricht dem Leser, dass jedes Kriterium gekennzeichnet ist — in fünf von acht Kapiteln stand es bisher nicht.

## ✅ Was übereinstimmte

| Geprüft | Ergebnis |
|---|---|
| Acht Kategoriesummen | **8 von 8 stimmen** |
| Klassenmaxima 103/103/103/100/103/81 | stimmen |
| Stufenschwellen 95/85/70/50/0 | stimmen |
| Alle 39 Kriterienbezeichnungen | stimmen |
| Gesamtsumme 103, 39 Kriterien | stimmt |

**Kein einziger Zahlenfehler in den handgetippten Tabellen.** Der Fehler lag in der Form, nicht im Inhalt.

## ⚠️ Eine Zeile, die jetzt einen bekannten Widerspruch druckt

`B4 · Semantik und Struktur · 2 · **abgeleitet** · alle Klassen`

Der Katalog sagt „abgeleitet", die Bewertung schreibt „gemessen" — Befund C1. **Die erzeugte Tabelle druckt den Katalogwert, weil er die Quelle ist.** Sie wechselt beim nächsten Export von selbst, sobald **S2.1** im Repo erledigt ist. Vermerkt in Kapitel 8.

---

## 🔴 Was heute nicht geht

| Fehlt | Warum |
|---|---|
| **Alle Punktabstufungstabellen** in Kapitel 5–12 | Die Abstufungen stehen als Bedingungen im Bewertungscode. **`BUCH-F1` überführt sie in Daten — vorher nicht erzeugbar** |
| **Anhang B, Abschnitt B.7** | dito |
| Die Prüfliste in 13.3–13.5 | Die Prüfhandlungen sind Prosa, keine Katalogdaten. Nur die Punktwerte stammen aus dem Export |

**Etwa dreißig Abstufungstabellen bleiben handgetippt** — und damit ungeschützt gegen die nächste Katalogänderung. Das ist genau der Zustand, den `BUCH-F3` beenden soll.

---

## Was das für Tor 0 bedeutet

**Aufgabe 1.1 ist zu etwa 60 % erledigt** und kann erst nach `BUCH-F1` und `F2` abgeschlossen werden.

Die vier Tabellenarten, gemessen an ihrer Anzahl im Buch:

| Art | Anzahl | Erzeugt |
|---|---|---|
| Kategorieübersicht | 2 | ✅ |
| Kriterientabellen | 8 | ✅ |
| Stufen und Maxima | 4 | ✅ |
| **Punktabstufungen** | **~30** | ❌ |

**Der Schritt, der noch fehlt, ist der größte.**
