/**
 * Zwei Faktoren ließen sich einschalten und nie wieder ausschalten (L-105).
 *
 * `DELETE /api/auth/2fa/disable` steht seit Langem im Backend und verlangt
 * **Passwort und gültigen Code**. Die Oberfläche rief nur `2fa/setup` und
 * `2fa/verify-setup`; „2FA verwalten" im Profil führte auf dieselbe
 * Einrichtungsmaske wie „2FA einrichten".
 *
 * **Kein Aussperrfall, und das gehört dazugesagt.** Wer sein Gerät verloren
 * hat, kommt auch mit diesem Knopf nicht weiter — die Route verlangt einen
 * gültigen Code. Was fehlte, ist das **freiwillige** Abschalten.
 *
 * Geprüft wird hier die Vorprüfung im Browser: Sie soll einen Aufruf sparen,
 * der ohnehin mit 401 zurückkäme — und sie darf **nicht** urteilen, ob
 * Passwort oder Code richtig sind. Das entscheidet der Server.
 */
import { abschaltenBereit } from '../utils/zweiFaktor';

describe('Vorprüfung vor dem Abschalten', () => {
  test('Passwort und sechsstelliger Code genügen', () => {
    expect(abschaltenBereit({ passwort: 'geheim123', code: '123456' }))
      .toBe(true);
  });

  test('ohne Passwort nicht', () => {
    expect(abschaltenBereit({ passwort: '', code: '123456' })).toBe(false);
    expect(abschaltenBereit({ passwort: '   ', code: '123456' })).toBe(false);
  });

  test('ein zu kurzer Code genügt nicht', () => {
    expect(abschaltenBereit({ passwort: 'geheim123', code: '12345' }))
      .toBe(false);
  });

  test('ein zu langer Code genügt nicht', () => {
    // Die Eingabe schneidet auf sechs; wer den Wert anders hineinbekommt,
    // soll trotzdem nicht durchkommen.
    expect(abschaltenBereit({ passwort: 'geheim123', code: '1234567' }))
      .toBe(false);
  });

  test('Buchstaben im Code genügen nicht', () => {
    expect(abschaltenBereit({ passwort: 'geheim123', code: '12345a' }))
      .toBe(false);
  });

  test('fehlende Angaben werfen nicht', () => {
    expect(abschaltenBereit({})).toBe(false);
    expect(abschaltenBereit(undefined)).toBe(false);
  });

  test('ein falsches Passwort ist trotzdem bereit', () => {
    // **Die Gegenprobe zur Vorprüfung.** Sie prüft Vollständigkeit, nicht
    // Richtigkeit. Urteilte sie über die Richtigkeit, müsste sie das
    // Passwort kennen — und dann läge es im Browser.
    expect(abschaltenBereit({ passwort: 'falsch-aber-da', code: '000000' }))
      .toBe(true);
  });
});
