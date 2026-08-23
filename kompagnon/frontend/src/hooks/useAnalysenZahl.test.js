import { analysenSatz } from './useAnalysenZahl';

/**
 * Die Regel, um die es bei L-65 geht: Der Werbetext darf nie mehr behaupten,
 * als geschehen ist — und lieber nichts sagen als etwas Falsches.
 */

test('nennt die Zahl, die der Server geliefert hat', () => {
  expect(analysenSatz(340)).toBe('Über 340 Handwerksbetriebe analysiert');
});

test('schreibt Tausender deutsch', () => {
  expect(analysenSatz(1200)).toBe('Über 1.200 Handwerksbetriebe analysiert');
});

test('unter zehn wird nichts behauptet', () => {
  // „Über 0 analysiert" waere schlechter als kein Satz.
  expect(analysenSatz(0)).toBeNull();
  expect(analysenSatz(9)).toBeNull();
});

test('ein fehlender oder unsinniger Wert sagt nichts', () => {
  expect(analysenSatz(undefined)).toBeNull();
  expect(analysenSatz(null)).toBeNull();
  expect(analysenSatz('viele')).toBeNull();
});
