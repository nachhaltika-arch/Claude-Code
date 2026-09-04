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

const WURZEL = path.join(__dirname, '..');

//: Seit dem 30.08.2026 liegen nicht mehr alle Wege unter `pages/`: Die
//: Bausteine der Kursverwaltung sind nach `components/akademie/` ausgezogen
//: (L-25), und der Bearbeiten-Knopf einer Lektion ist mitgegangen. Dieser
//: Test hat den Umzug gemeldet — er fand null `onEdit` statt einem.
const lies = (datei) => fs.readFileSync(path.join(WURZEL, datei), 'utf8');

describe('Wege im Akademie-Editor', () => {
  test('der Bearbeiten-Knopf an einer Lektion führt zum Lektions-Editor', () => {
    const quelle = lies('components/akademie/kursBausteine.jsx');

    const onEdit = quelle.match(/onEdit=\{[^}]*\}/g) || [];

    expect(onEdit.length).toBeGreaterThan(0);
    onEdit.forEach(zeile => {
      expect(zeile).toMatch(/academy\/admin\/lesson\//);
    });
  });

  test('niemand navigiert auf die Modul-Adresse, die es nicht gibt', () => {
    // `/app/akademie/admin/modul/…` landet über die Umleitung in der
    // Kursliste. Ein Knopf, der dorthin zeigt, verliert die Arbeitsstelle.
    const seiten = path.join(WURZEL, 'pages');
    const dateien = fs.readdirSync(seiten)
      .filter(d => /\.(js|jsx)$/.test(d))
      .map(d => `pages/${d}`);

    const treffer = dateien.filter(d => lies(d).includes('akademie/admin/modul'));

    expect(treffer).toEqual([]);
  });
});
