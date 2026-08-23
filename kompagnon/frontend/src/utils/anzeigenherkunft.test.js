import { herkunftAusAdresse } from './anzeigenherkunft';

/**
 * Die Regel: mitnehmen, was da ist — und nichts raten.
 */

test('liest die drei Felder aus der Adresse', () => {
  const adresse = 'https://kompagnon.eu/?utm_source=google&utm_medium=cpc&utm_campaign=wp-nord';

  expect(herkunftAusAdresse(adresse)).toEqual({
    utm_source: 'google', utm_medium: 'cpc', utm_campaign: 'wp-nord',
  });
});

test('nimmt mit, was da ist, und erfindet den Rest nicht', () => {
  expect(herkunftAusAdresse('https://kompagnon.eu/?utm_source=google'))
    .toEqual({ utm_source: 'google' });
});

test('ohne Anzeige bleibt es leer', () => {
  expect(herkunftAusAdresse('https://kompagnon.eu/')).toEqual({});
});

test('nimmt nur die drei bekannten Felder', () => {
  // Ein Widget haengt auf fremden Seiten; deren Adressen tragen alles Moegliche.
  const adresse = 'https://fremde.de/?utm_source=x&gclid=abc&fbclid=def&sitzung=geheim';

  expect(herkunftAusAdresse(adresse)).toEqual({ utm_source: 'x' });
});

test('kuerzt uebermaessig lange Werte', () => {
  const adresse = `https://kompagnon.eu/?utm_source=${'x'.repeat(500)}`;

  expect(herkunftAusAdresse(adresse).utm_source).toHaveLength(200);
});

test('eine unlesbare Adresse laesst das Formular nicht scheitern', () => {
  expect(herkunftAusAdresse('kein::url')).toEqual({});
  expect(herkunftAusAdresse(null)).toEqual({});
  expect(herkunftAusAdresse(undefined)).toEqual({});
});
