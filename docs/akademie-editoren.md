# Zwei Kurseditoren — was zu entscheiden ist

> Grundlage für **UX-42** (`docs/ux-arbeitsliste.md`, Paket 8).
> Erhoben am 2026-08-18 am laufenden Programm und am Datenmodell.

## Die Entscheidung in einem Satz

Es gibt **zwei Kurseditoren auf derselben Tabelle**. Der gelebte (A) kann
alles, was irgendwo angezeigt wird; der unerreichbare (B) kann vier Felder
mehr, die **auf keinem Bildschirm erscheinen**. Zu entscheiden ist also nur,
ob diese vier Felder ein Merkmal werden sollen — sonst kann B weg.

**Beim Vergleichen fiel ein Fehler heraus, der schwerer wiegt als die Frage
selbst:** Es liess sich überhaupt keine Lektion anlegen (500). Behoben, siehe
unten.

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
erreichbar — er ist aber der einzige, der vier Felder setzen kann, die es in
der Datenbank gibt: `category`, `category_color`, `formats` und die
Checklisten-Punkte des Kurses.

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
| **Freischaltung** (`linear_progress`) | ✓ *(mit Erklärung am Schalter)* | ✓ |
| **Checklisten-Punkte** | — | ✓ |
| Kleine Bildschirme | ✓ zweispaltig ab Tablet | — feste Breite |
| Löschung bestätigen | `window.confirm` (2×) | `window.confirm` (1×) |
| Fehler beim Speichern | **wird nur in die Konsole geschrieben** | **dito** |

---

## Korrektur zur ersten Fassung

Die erste Fassung dieser Gegenüberstellung führte **Freischaltung** als etwas,
das nur B kann. Das war falsch: A hat den Schalter, sogar mit erklärendem Text
(„Lektionen müssen der Reihe nach abgeschlossen werden"). Der Fehler kam
daher, dass ich die Felder aus `<label>`-Auszügen erhoben habe und A den
Schalter ohne solches Element baut. Am Bildschirm nachgesehen, nicht im
Auszug — dann stimmt es.

## Was das praktisch heißt

**B kann genau zwei Dinge mehr — und beide erscheinen nirgends:**

- **Formate** (`formats`) und die **Checklisten-Punkte des Kurses**
  (`academy_checklist_items`): Die Schnittstelle liefert sie aus, **kein
  Bildschirm zeigt sie an**.
- Dasselbe gilt für `category` und `category_color`.

**Checklisten gibt es noch an einer zweiten Stelle** — je Lektion. Bearbeitet
werden sie nur im Modul-Editor (Bs Kette), angezeigt nur im **alten**
Lektions-Spieler unter `/app/akademie/lektion/:id`. Der gelebte Kurs-Spieler
(`/app/academy/:id`) stellt sie nicht dar. Das Merkmal lebt also vollständig
in der alten Welt.

**Und ein Fehler, den beide teilen:** Schlägt das Speichern fehl, sieht man
nichts. Beide fangen jeden Fehler mit `catch (e) { console.error(e); }` ab;
der Knopf hört einfach auf zu drehen. Das ist dieselbe Bauart, die am 08.08.
an 67 Stellen behoben wurde — hier nicht.

---

## Der Fund, der beim Vergleichen herausfiel

**Es ließ sich überhaupt keine Lektion anlegen.** `POST
/api/academy/modules/{id}/lessons` antwortete mit **500**:

```
TypeError: 'checklist_items_json' is an invalid keyword argument for AcademyLesson
```

Der Router übergibt das Feld beim Anlegen; die Spalte existiert in der
Datenbank (aus `main.py::_run_migrations`), im **Modell** stand sie nicht.
Beide Editoren rufen denselben Endpunkt — der Kern der Akademie war kaputt:
Kurse und Module ließen sich anlegen, **Inhalte nicht**.

Warum es niemandem auffiel: Die Oberfläche zeigt Fehler beim Speichern nicht
an (siehe oben). Warum kein Test es fand: Das Testschema entsteht aus den
Modellen, also fehlte die Spalte dort ebenso.

**Behoben** (`database.py`), drei Tests halten es
(`tests/test_akademie_lektion_anlegen.py`). Am laufenden Backend nachgeprüft:
HTTP 200, die Checklisten-Punkte kommen zurück.

---

## Empfehlung

**A behalten, B auflösen.** Begründung:

1. A ist der Weg, den die Oberfläche geht — B ist bereits unerreichbar.
2. A kann das, was ohne Datenbankzugriff nicht nachzuholen ist: Lektionen,
   Titelbild, Veröffentlichung.
3. Bs Mehrfelder erscheinen auf **keinem** Bildschirm — es ist nichts zu
   retten, nur zu entscheiden.

**Die Schritte, in dieser Reihenfolge:**

1. **Fehler sichtbar machen** — in A und im Lektions-Editor. Ein Speichern,
   das stillschweigend scheitert, ist schlimmer als eines, das hakt (S).
   Ohne diesen Schritt bleibt der nächste Fehler dieser Art genauso lange
   unentdeckt wie der 500er oben.
2. `/app/akademie/*` **auf `/app/academy/*` umleiten**, statt zwei Räume zu
   führen; die alten Adressen bleiben als Weiterleitung gültig (S).
3. **B, den Modul-Editor, den alten Lektions-Spieler und die Routen dazu
   entfernen** (S). **Zu portieren ist nichts** — Bs zwei Mehrfelder werden
   nirgends angezeigt.
4. Entscheiden, ob **Checklisten je Lektion** ein Merkmal bleiben sollen. Wenn
   ja, gehören sie in As Lektions-Editor **und** in den gelebten Kurs-Spieler;
   das ist Neubau, kein Umzug. Wenn nein, fallen sie mit Schritt 3.
5. Über `category`, `category_color` und `formats` entscheiden: anzeigen oder
   aus dem Modell nehmen. Solange sie nirgends erscheinen, sind sie Ballast.

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
