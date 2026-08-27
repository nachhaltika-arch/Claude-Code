/**
 * Quelltext ohne seine Kommentare — für Wächter, die im Code suchen.
 *
 * **Warum es das gibt.** Ein Wächter, der eine verbotene Zeile sucht, findet
 * sie auch in der Erklärung, warum sie verboten ist. Am 26.08.2026 meldete
 * `keinLeeresVersprechen` die neue Oberfläche, weil deren Kopftext genau die
 * Zeile zitiert. Am 27.08. traf es `ariaWerte`: Ein Kommentar, der
 * `role="checkbox"` erwähnt, wurde als Fundstelle gezählt — und die Suche
 * nach dem umgebenden Tag griff sich das `<input>` aus demselben Kommentar.
 *
 * **Warum an einer Stelle.** Es gab die Funktion bereits zweimal, in zwei
 * Testdateien und in zwei verschiedenen Fassungen: einmal als Zustandsautomat,
 * einmal als Paar von Ersetzungen. Die zweite Fassung zerschneidet keine
 * Adressen, weil sie `[^:]` vor `//` verlangt — aber sie übersieht ein `//`
 * innerhalb einer Zeichenkette, das kein Doppelpunkt einleitet. Zwei
 * Werkzeuge mit derselben Aufgabe und verschiedenem Verhalten sind genau die
 * Bauart, die in diesem Baum schon mehrfach auseinandergelaufen ist.
 *
 * **Ein Zustandsautomat, kein Muster.** `https://` enthält `//`, und ein
 * Muster, das darauf anspringt, zerschneidet jede Adresse in einer
 * Zeichenkette. Deshalb wird zeichenweise gelesen und Zeichenketten werden
 * unangetastet durchgereicht.
 *
 * @param {string} quelltext
 * @returns {string} derselbe Text, Kommentare durch nichts ersetzt
 */
export function ohneKommentare(quelltext) {
  let raus = '';
  let i = 0;
  while (i < quelltext.length) {
    const zwei = quelltext.slice(i, i + 2);
    if (zwei === '//') {
      while (i < quelltext.length && quelltext[i] !== '\n') i += 1;
    } else if (zwei === '/*') {
      i += 2;
      while (i < quelltext.length && quelltext.slice(i, i + 2) !== '*/') i += 1;
      i += 2;
    } else if (quelltext[i] === '"' || quelltext[i] === "'" || quelltext[i] === '`') {
      // Zeichenketten bleiben, wie sie sind — samt allem, was darin nach
      // einem Kommentar aussieht.
      const ende = quelltext[i];
      raus += quelltext[i];
      i += 1;
      while (i < quelltext.length && quelltext[i] !== ende) {
        if (quelltext[i] === '\\') { raus += quelltext[i]; i += 1; }
        raus += quelltext[i];
        i += 1;
      }
      raus += ende;
      i += 1;
    } else {
      raus += quelltext[i];
      i += 1;
    }
  }
  return raus;
}

export default ohneKommentare;
