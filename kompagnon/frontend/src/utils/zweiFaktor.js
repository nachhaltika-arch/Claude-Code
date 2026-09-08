/**
 * Die Vorprüfung vor dem Abschalten der Zwei-Faktor-Anmeldung (L-105).
 *
 * **Sie prüft Vollständigkeit, nicht Richtigkeit.** Ob Passwort und Code
 * stimmen, entscheidet `DELETE /api/auth/2fa/disable` — hier zu urteilen
 * hieße, das Passwort im Browser zu kennen.
 *
 * Eigene Datei und nicht in `TwoFactorSetup.jsx`: Die Seite zieht
 * `react-router-dom` herein, und das lässt sich im Testlauf nicht auflösen.
 * Eine Regel, die niemand prüfen kann, ist keine.
 */

/** Wie viele Ziffern ein TOTP-Code hat. */
export const CODE_LAENGE = 6;

/**
 * Sind Passwort und Code vollständig genug für einen Versuch?
 *
 * @param {{ passwort?: string, code?: string }} eingaben
 * @returns {boolean}
 */
export function abschaltenBereit(eingaben) {
  const passwort = (eingaben?.passwort || '').trim();
  const code = eingaben?.code || '';
  return passwort.length > 0 && new RegExp(`^\\d{${CODE_LAENGE}}$`).test(code);
}

/** `12a3b4 5` → `1234` — die Eingabe nimmt nur Ziffern, höchstens sechs. */
export function nurZiffern(eingabe) {
  return (eingabe || '').replace(/\D/g, '').slice(0, CODE_LAENGE);
}
