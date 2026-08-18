import fs from 'fs';
import path from 'path';

import { tabelle, wert } from './tokenwerte';

const CSS = fs.readFileSync(
  path.join(__dirname, '..', 'styles', 'tokens.css'), 'utf8',
);
const HELL = tabelle(CSS, 'hell');
const DUNKEL = tabelle(CSS, 'dunkel');

test('ein Verweis wird bis zum Farbwert verfolgt', () => {
  // --brand-primary → --kc-dark → #004F59
  expect(wert('--brand-primary', HELL).toLowerCase()).toBe('#004f59');
});

test('derselbe Name ergibt im anderen Modus einen anderen Wert', () => {
  expect(wert('--brand-primary', DUNKEL).toLowerCase()).toBe('#40c4df');
});

test('ein Wert ohne Verweis kommt unveraendert zurueck', () => {
  expect(wert('--kc-yellow', HELL)).toBe('#FAE600');
});

test('was keine Farbe ist, ergibt null', () => {
  expect(wert('--radius-md', HELL)).toBeNull();
  expect(wert('--gibt-es-nicht', HELL)).toBeNull();
});

test('ein unbekannter Modus wird abgewiesen', () => {
  expect(() => tabelle(CSS, 'daemmerung')).toThrow();
});
