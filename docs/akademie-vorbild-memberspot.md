# Was Memberspot besser macht — und was davon zu uns passt

> Audit am 2026-08-19 im laufenden Memberspot-Konto (`nachhaltika`), Kursvorlage
> „[Demo] Mitarbeiter Schulung und Training": 12 Module, 91 Lektionen, 3:03 h.
> Gegenübergestellt: unsere Akademie (`AcademyCourse` → `AcademyModule` →
> `AcademyLesson`, `routers/academy.py`, 31 Endpunkte).

---

## Vorbemerkung: Was hier gemessen wurde und was nicht

Der Testzeitraum des Kontos ist abgelaufen. **Zugänglich** war die
Kursübersicht, der Kursbaum mit Modulen, Ordnern und Lektionen samt Status,
die Navigation und die vollständige Funktionsmatrix der Tarife.
**Gesperrt** waren Lektionsdetails, der Prüfungs- und Aufgabenbereich sowie
der Mitgliederbereich (`member-area-disabled`).

Über den *Inhalt* einer einzelnen Lektion sagt dieses Audit deshalb nichts.
Über die **Architektur** sagt es alles Nötige — und die ist der interessante
Teil, denn dort unterscheiden wir uns.

Ein zweiter Vorbehalt: Die Lektionen der Vorlage sind fast alle **0:18 lang**,
also Platzhalter-Clips. Aus den Laufzeiten lässt sich **keine** didaktische
Länge ableiten. Was zählt, sind Zuschnitt und Benennung.

---

## 1. Vier Ebenen statt drei

Memberspot:

```
Kurs
└── Modul                     (Titel, Beschreibung, Vorschaubild, Status)
    ├── Lektion               (Titel, Vorschaubild, Dauer, Status)
    └── Ordner                (Titel, Status, eigener Klapp-Pfeil)
        └── Lektion
```

Nachgewiesen in Modul III: Zwischen dreizehn Lektionen stehen zwei Einträge
**mit Ordner-Symbol und ohne Dauer** — „Formalitäten" und „Belehrungen und
Pflichtschulungen für Mitarbeiter". Darin liegen Sicherheitseinweisung,
Arbeitsschutz und Infektionsschutz.

Wir haben drei Ebenen: Kurs → Modul → Lektion.

**Empfehlung: die Ordner-Ebene *nicht* nachbauen.** Sie löst ein Problem, das
wir noch nicht haben — sie taucht genau dort auf, wo ein Modul über zehn
Lektionen bekommt. Solange unsere Module das nicht tun, ist es Vorrat. Der
Punkt gehört notiert, nicht gebaut.

## 2. Status auf **jeder** Ebene — das ist der eigentliche Unterschied

Jedes Modul, jeder Ordner und jede Lektion trägt bei Memberspot ein eigenes
Status-Feld. Zwei Werte waren im Bestand zu sehen:

| Status | Bedeutung im Bestand |
|---|---|
| **Veröffentlicht** (grün) | für alle sichtbar |
| **Manuell** (blau) | nur für ausdrücklich Zugewiesene |

Und daraus baut die Vorlage ihr didaktisches Grundmuster:

- **Startmodul** 🚩 — veröffentlicht, das kostenlose Training. Ein Werbeträger
  *innerhalb* des Kurses
- **I.–IV.** — veröffentlicht, der Pflichtstrang, den jeder durchläuft
- **Sechs Abteilungs-Module** 🎓 (Vertrieb, Marketing, Customer Support,
  Personalwesen, IT/EDV, Buchhaltung) — **alle auf „Manuell"**
- **Bonus** 🏆 — veröffentlicht

Also: **ein Pflichtweg für alle, sechs Rollenzweige für die jeweils
Betroffenen, ein Gratis-Einstieg vorneweg.** Ein Vertriebler sieht nicht die
Buchhaltungsschulung — nicht weil sie versteckt wäre, sondern weil ihm das
Modul nie zugewiesen wurde.

Bei uns steht die Freigabe **nur am Kurs**: `AcademyCourse.is_published` und
`AcademyCustomerAccess` (Zuweisung je Kurs). `AcademyModule` hat ein
`is_locked`, das eine Sperre kennt, aber keine Zuweisung; `AcademyLesson` hat
gar nichts.

**Empfehlung — der wichtigste Punkt dieses Audits:** Zuweisung auf
**Modulebene** ergänzen. Damit wird aus einem Kurs pro Zielgruppe *ein* Kurs
mit Zweigen. Für uns heißt das konkret: ein Kunden-Onboarding, in dem der
Pflichtteil für jeden gilt und die gewerkespezifischen Teile (Wärmepumpe,
Wallbox) nur bei den passenden Betrieben auftauchen. Das ist genau die
Struktur, die [[niche_phase1]] verlangt, ohne dass wir Kurse duplizieren.

## 3. Jedes Modul erklärt sich in einer Zeile

Jedes der zwölf Module trägt eine Beschreibung:

> „Dieses Modul schafft den Kontext für neue Mitarbeiter/innen, …"
> „Durch eine ausführliche Beschreibung der Wertschöpfungskette…"

`AcademyModule` hat bei uns **nur** `title`, `position`, `is_locked`,
`sort_order`. Keine Beschreibung, kein Bild.

**Empfehlung: `description` und `thumbnail_url` an `AcademyModule`.** Zwei
Spalten, und die Modulliste hört auf, eine Aufzählung zu sein. Das ist der
billigste Gewinn auf dieser Liste.

## 4. Benennung trägt die Struktur

- **Römische Ziffern** für den Pflichtstrang (I.–IV.) — die Reihenfolge steht
  im Namen, nicht nur in der Sortierung
- **Emoji als Gattungsmarke**: 🚩 Einstieg, 🎓 Rollenzweig, 🏆 Bonus. Auf
  einen Blick unterscheidbar, ganz ohne zusätzliche Spalte
- **Wiederholte Präfixe** gruppieren („Unser Unternehmen erklärt – Rahmen",
  „… – Abläufe und Organisatorisches")

Das kostet nichts und ist sofort übernehmbar — es ist eine Redaktionsregel,
kein Feature. Achtung bei der Übernahme: Unsere Tool-CI erlaubt
[[kompagnon_ui_guidelines]] kein beliebiges Farbwerk; Emoji im Titel sind
davon unberührt, ein neues Status-Farbschema wäre es nicht.

## 5. Drei Zahlen je Kurs

Die Kursliste zeigt je Kurs **Module · Lektionen · Gesamtdauer**
(12 · 91 · 3:03:19). Nicht mehr, nicht weniger — und genau diese drei
beantworten „Wie groß ist das hier?".

Unsere Kursliste hat die Zahlen teilweise, aber im **falschen Modell**: Die
Tabelle `courses` führt `chapter_count`, `participant_count` und
`duration_minutes` als **mitgeführte Zähler**, während die echte Struktur in
`academy_*` liegt. Zähler, die niemand nachrechnet, driften.

**Empfehlung:** Die drei Zahlen aus `academy_*` **berechnen**, nicht speichern.

## 6. Der große Fund: wir haben zwei Kurssysteme

| | `academy_courses` (+ modules, lessons, quiz, …) | `courses` |
|---|---|---|
| Struktur | Module und Lektionen, echte Hierarchie | **keine** — nur `chapter_count` als Zahl |
| Fortschritt | `AcademyProgress`, `AcademyLessonProgress` | — |
| Prüfung | `AcademyQuizQuestion` | — |
| Zertifikat | `AcademyCertificate` + öffentliche Prüfung | — |
| Zuweisung | `AcademyCustomerAccess` | — |
| Im Menü | „Akademie" | „Kurse verwalten" |

Beide sind produktiv befüllt, beide erscheinen im Werkzeug, und der Kurs
**„Gratis Mitgliedschaft" steht in beiden Welten** — bei Memberspot und in
unserer `courses`-Tabelle.

**Empfehlung: `courses` abschaffen und auf `academy_courses` zusammenführen** —
vor jeder neuen Funktion. Solange zwei Editoren dasselbe zu tun vorgeben,
kostet jede Verbesserung doppelt, und die Redaktion rät, wo sie pflegen soll.
Das ist der Punkt, an dem ich anfangen würde.

---

## Was wir schon haben und Memberspot erst ab 39 €/Monat verkauft

Der Vergleich fällt nicht einseitig aus. Unsere Akademie kann heute:

- Module, Lektionen, Reihenfolge, drei Lektionstypen (`video`|`text`|`quiz`)
- Fortschritt je Lektion **mit Punktzahl**
- Quiz je Lektion, samt Verwaltungsweg
- **Zertifikate mit öffentlicher Prüfung** (`/api/academy/certificates/{code}/verify`)
  — bei Memberspot ein Tarifmerkmal
- Kursweise Zuweisung an Kunden
- `linear_progress` je Kurs (erzwungene Reihenfolge)
- Checklisten je Kurs (`AcademyChecklistItem`)

**Die Lücke ist nicht die Technik. Es ist die Struktur** — und zwei
Kleinigkeiten: die Modulbeschreibung und die Zuweisung je Modul.

---

## Funktionsmatrix Memberspot (Stand 19.08., zur Einordnung)

Was eine ausgereifte Plattform für nötig hält, nach Tarifstufe:

- **Starter (39 €):** 1 Kurs, 1 Admin, 100 Mitglieder · unbegrenzte
  Video-Uploads, Videoaufnahme im Tool, eigenes Branding, Community,
  Integrationen (Zoom, GTM, Zahlung), **Prüfungen und Zertifikate**
- **Grow (99 €):** unbegrenzte Kurse, 2.500 Mitglieder · AI-Transkriptionen,
  AI-Prüfungen, **Abgaben**, individuelle Portale, **Stimmungsbarometer**,
  DRM/Fingerprint, eigene Domain, Web-App, eigene Admin-Rollen
- **Scale (199 €):** AI Search, AI Assistant, eigene AI-Agenten,
  Agent-Erweiterungen (HTTP/MCP), Background Agents
- **Quer durch:** Umfragen, CSV-Import, benutzerdefinierte Eigenschaften,
  Attributsgruppen, API-Zugriff, SSO (Enterprise)

Drei Dinge daraus sind für uns überhaupt erwägenswert: **Abgaben** (der Kunde
lädt etwas hoch, wir sehen es durch), **Umfragen/Stimmungsbarometer** (misst,
ob das Onboarding trägt) und **Prüfungen auf Kursebene** statt nur Quiz je
Lektion. Der Rest ist Plattformgeschäft, nicht unseres.

---

## Reihenfolge, wenn es an die Umsetzung geht

1. **Die zwei Kurssysteme zusammenführen** (`courses` → `academy_*`). Ohne das
   verdoppelt jede weitere Änderung ihren Preis
2. **`description` + `thumbnail_url` an `AcademyModule`** — zwei Spalten, größte
   sichtbare Wirkung
3. **Zuweisung je Modul** — macht aus Kursduplikaten einen Kurs mit Zweigen
4. **Modul/Lektion/Dauer je Kurs berechnen** statt als Zähler zu führen
5. Redaktionsregel für Benennung: Ziffern für den Pflichtweg, Emoji als
   Gattungsmarke, wiederholte Präfixe für Gruppen
6. *Später, wenn ein Modul über zehn Lektionen bekommt:* Ordner-Ebene
7. *Wenn Kunden etwas einreichen sollen:* Abgaben

Punkte 2 und 4 sind je unter einem Tag. Punkt 1 ist die eigentliche Arbeit.
