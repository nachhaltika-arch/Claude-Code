# Zwei Kurseditoren — was zu entscheiden ist

> Grundlage für **UX-42** (`docs/ux-arbeitsliste.md`, Paket 8).
> Erhoben am 2026-08-18 am laufenden Programm und am Datenmodell.

## Die Entscheidung in einem Satz

Es gibt **zwei Kurseditoren auf derselben Tabelle**, und **keiner von beiden
kann einen Kurs vollständig bearbeiten** — die Frage ist nicht, welcher
gewinnt, sondern welcher die Felder des anderen übernimmt.

---

## Die Lage

Die Akademie liegt unter **zwei Adressräumen**:

| Adresse | Bildschirm | erreichbar über |
|---|---|---|
| `/app/academy/admin` | Kursliste | Menü (seit heute) |
| `/app/academy/admin/course/:id` | **Editor A** — `AcademyAdminCourse` | „+ Neuer Kurs" |
| `/app/akademie/admin/course/:id` | **Editor A**, alte Adresse | „✏️ Bearbeiten" in der Liste |
| `/app/akademie/admin/:id` | **Editor B** — `AcademyEdit` | **nichts** |
| `/app/akademie/admin/neu` | **Editor B**, neuer Kurs | **nichts** |
| `/app/akademie/admin/modul/:id` | Modul-Editor zu B | nur aus B heraus |

**Editor A ist der gelebte Weg.** Editor B ist über die Oberfläche nicht mehr
erreichbar — aber er ist der einzige, der fünf Felder setzen kann, die es in
der Datenbank gibt.

---

## Gegenüberstellung

|  | **A · AcademyAdminCourse** | **B · AcademyEdit** |
|---|---|---|
| Adresse | `academy/admin/course/:id` | `akademie/admin/:id` |
| Umfang | 822 Zeilen + 660 (Lektions-Editor) | 316 Zeilen + 274 (Modul-Editor) |
| Aufbau | **ein Bildschirm**: Kurs, Module *und* Lektionen | **drei Ebenen**: Kurs → Modul → Lektion |
| Kurstitel, Beschreibung | ✓ | ✓ |
| Zielgruppe | ✓ (Kunden / Mitarbeiter / alle) | ✓ (Mitarbeiter / Kunde) |
| **Titelbild** | ✓ URL **und** Drag & Drop | — |
| **Veröffentlichen** | ✓ Status im Editor | — |
| **Lektionen** | ✓ anlegen, sortieren, löschen | — (nur über den Modul-Editor) |
| Module sortieren | ✓ | ✓ |
| **Kategorie + Farbe** | — | ✓ |
| **Formate** (Text, Video, Checkliste …) | — | ✓ |
| **Freischaltung** (`linear_progress`) | — | ✓ |
| **Checklisten-Punkte** | — | ✓ |
| Kleine Bildschirme | ✓ zweispaltig ab Tablet | — feste Breite |
| Löschung bestätigen | `window.confirm` (2×) | `window.confirm` (1×) |
| Fehler beim Speichern | **wird nur in die Konsole geschrieben** | **dito** |

---

## Was das praktisch heißt

**Drei der fünf Felder, die nur B kann, wirken sichtbar:**

- **Freischaltung** (`linear_progress`) steuert im Kurs-Spieler, ob Lektionen
  erst nacheinander aufgehen (`AcademyCourse.js:117`). Wer den Kurs über den
  gelebten Weg anlegt, kann das nicht einstellen — der Wert bleibt auf `false`.
- **Formate** und **Checklisten-Punkte** werden im Spieler dargestellt.

**Zwei sind Karteileichen:** `category` und `category_color` stehen in der
Tabelle, sind in B einstellbar — und werden auf **keinem** Bildschirm der
Akademie angezeigt.

**Und ein Fehler, den beide teilen:** Schlägt das Speichern fehl, sieht man
nichts. Beide fangen jeden Fehler mit `catch (e) { console.error(e); }` ab;
der Knopf hört einfach auf zu drehen. Das ist dieselbe Bauart, die am 08.08.
an 67 Stellen behoben wurde — hier nicht.

---

## Empfehlung

**A behalten, B auflösen.** Begründung:

1. A ist der Weg, den die Oberfläche geht — B ist bereits unerreichbar.
2. A kann das, was ohne Datenbankzugriff nicht nachzuholen ist: Lektionen,
   Titelbild, Veröffentlichung.
3. Bs Beitrag sind **drei Felder** — das ist ein überschaubarer Umbau, kein
   zweiter Editor.

**Die Schritte, in dieser Reihenfolge:**

1. **Freischaltung, Formate, Checklisten-Punkte in A** ergänzen (⅓ Tag).
2. **Fehler sichtbar machen** — in A und im Lektions-Editor. Ein Speichern,
   das stillschweigend scheitert, ist schlimmer als eines, das hakt (S).
3. `/app/akademie/*` **auf `/app/academy/*` umleiten**, statt zwei Räume zu
   führen; die alten Adressen bleiben als Weiterleitung gültig (S).
4. **B, den Modul-Editor und die Routen dazu entfernen** — erst nach 1.
5. Über `category`/`category_color` entscheiden: anzeigen oder aus dem Modell
   nehmen. Solange sie nirgends erscheinen, sind sie Ballast.

**Der Gegenvorschlag, der Bestand hätte:** Wer die drei Ebenen (Kurs → Modul →
Lektion) für die bessere Bedienung hält, kehrt die Richtung um — dann muss B
Titelbild, Veröffentlichung und die Lektionsverwaltung dazubekommen. Das ist
mehr Arbeit (der Lektions-Editor hängt an A) und verliert die einspaltige
Ansicht auf kleinen Bildschirmen.

---

## Die zweite Frage, die dabei aufgetaucht ist

Es gibt **eine zweite Kurs-Tabelle**:

| | `academy_courses` | `courses` |
|---|---|---|
| Modell | `AcademyCourse` | `Course` |
| Router | `routers/academy.py` | `routers/courses.py` |
| Bildschirm | Akademie + beide Editoren | `/app/courses` (`Courses.jsx`, 545 Zeilen) |
| Felder | Module, Lektionen, Formate, Fortschritt | Kategorie intern/kunde/produkt, Kapitelzahl, Teilnehmerzahl, Dauer |
| Verlinkt von | Menü | **nichts** — nur die Titelzuordnung der Brotkrume |
| Zeilen lokal | **5** | **0** |

Das ist kein dritter Bildschirm derselben Sache, sondern **eine zweite,
unabhängige Kursverwaltung**. Lokal ist sie leer. Ob produktiv Daten darin
liegen, ist ungeprüft — das entscheidet, ob sie entfernt werden kann:

```sql
SELECT count(*) FROM courses;
```

Ist das Ergebnis 0, gehören Tabelle, Router und Bildschirm weg.
