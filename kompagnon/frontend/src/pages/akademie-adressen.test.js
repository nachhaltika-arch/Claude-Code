/**
 * Die Akademie hat eine Welt, nicht zwei.
 *
 * UX-42: Es gab `/app/academy/*` (8 Routen) und `/app/akademie/*` (11) — und
 * das waren keine Aliasse. Hinter `akademie/admin/:id` lag ein **anderer**
 * Kurseditor als hinter `academy/admin/course/:id`, und der Modul-Editor war
 * ueberhaupt nur ueber den alten Pfad erreichbar. Ein Klick auf „Bearbeiten"
 * wechselte den Adressraum, ohne dass man es sah.
 *
 * Der zweite Editor kann genau zwei Dinge mehr als der gelebte — `formats`
 * und die Checklisten-Punkte des Kurses —, und **beide erscheinen auf keinem
 * Bildschirm**. Deshalb wird nichts portiert, sondern aufgeloest:
 * `docs/akademie-editoren.md`.
 *
 * Die alten Adressen bleiben gueltig, aber nur als Weiterleitung — Lesezeichen
 * und alte Links sollen nicht ins Leere laufen.
 */
import fs from 'fs';
import path from 'path';

const APP = fs.readFileSync(path.join(__dirname, '..', 'App.jsx'), 'utf8');

describe('Adressen der Akademie', () => {
  test('die alten Adressen leiten weiter, statt eigene Bildschirme zu zeigen', () => {
    expect(APP).toMatch(/path="akademie\/\*"/);
  });

  test('kein eigener Bildschirm haengt mehr an einer akademie-Adresse', () => {
    const alteRouten = [...APP.matchAll(/<Route\s+path="akademie\/[^"]*"[^>]*element=\{<(\w+)/g)]
      .map((treffer) => treffer[1])
      .filter((name) => name !== 'Navigate' && name !== 'AkademieUmleitung');

    expect(alteRouten).toEqual([]);
  });

  test('der zweite Kurseditor und seine Kette sind fort', () => {
    ['AcademyEdit', 'AcademyModuleEdit', 'AcademyLesson'].forEach((name) => {
      expect(APP).not.toMatch(new RegExp(`\\b${name}\\b`));
    });
  });

  test('die Dateien dazu liegen nicht mehr herum', () => {
    ['AcademyEdit.jsx', 'AcademyModuleEdit.jsx', 'AcademyLesson.jsx'].forEach((datei) => {
      expect(fs.existsSync(path.join(__dirname, datei))).toBe(false);
    });
  });
});
