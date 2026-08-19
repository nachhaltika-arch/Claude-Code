import fs from 'fs';
import path from 'path';

/**
 * Der Bearbeiten-Knopf muss dorthin führen, wo bearbeitet wird.
 *
 * Befund vom 19.08.2026 beim Einbau der Modulbeschreibung: Im Kurseditor
 * zeigten **beide** Bearbeiten-Knöpfe — der am Modul und der an der Lektion —
 * auf `/app/akademie/admin/modul/{id}`. Diese Adresse gibt es nicht; die
 * Umleitung in `App.jsx` bildet sie auf `/app/academy/admin` ab, also auf die
 * **Kursliste**.
 *
 * Praktisch hieß das: Wer im Kurseditor eine Lektion bearbeiten wollte, wurde
 * aus dem Kurs geworfen — und der Lektions-Editor, den es unter
 * `/app/academy/admin/lesson/{id}` sehr wohl gibt, war von dort nicht
 * erreichbar. Es ist derselbe Fehlertyp wie am 18.08., als sich keine Lektion
 * anlegen ließ: Der Weg endet woanders, als der Knopf verspricht, und nichts
 * schlägt fehl.
 *
 * Geprüft wird an der Quelle, weil das Ziel eine Zeichenkette ist: Ein Test,
 * der die Seite rendert, würde den falschen Weg genauso klaglos gehen wie ein
 * Mensch.
 */

const SEITEN = path.join(__dirname, '..', 'pages');

const lies = (datei) => fs.readFileSync(path.join(SEITEN, datei), 'utf8');

describe('Wege im Akademie-Editor', () => {
  test('der Bearbeiten-Knopf an einer Lektion führt zum Lektions-Editor', () => {
    const quelle = lies('AcademyAdminCourse.js');

    const onEdit = quelle.match(/onEdit=\{[^}]*\}/g) || [];

    expect(onEdit.length).toBeGreaterThan(0);
    onEdit.forEach(zeile => {
      expect(zeile).toMatch(/academy\/admin\/lesson\//);
    });
  });

  test('niemand navigiert auf die Modul-Adresse, die es nicht gibt', () => {
    // `/app/akademie/admin/modul/…` landet über die Umleitung in der
    // Kursliste. Ein Knopf, der dorthin zeigt, verliert die Arbeitsstelle.
    const dateien = fs.readdirSync(SEITEN).filter(d => /\.(js|jsx)$/.test(d));

    const treffer = dateien.filter(d => lies(d).includes('akademie/admin/modul'));

    expect(treffer).toEqual([]);
  });
});
