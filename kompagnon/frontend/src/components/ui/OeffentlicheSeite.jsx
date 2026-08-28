/**
 * Die Landmarke für Seiten außerhalb der App-Hülle (L-17, Gruppe Tastatur).
 *
 * **Warum es das braucht.** Lighthouse prüft unter `bypass`, ob eine
 * Tastaturbedienung die Navigation überspringen kann — über einen Sprunglink
 * oder eine Landmarke. `AppLayout` hat seit jeher ein `<main>`; die
 * **sechzehn öffentlichen Seiten** hatten keins: Login, Registrierung,
 * Kundenportal, Bestellweg, Impressum, Datenschutz — und, mit einiger Ironie,
 * `Barrierefreiheit.jsx`, die Erklärung selbst.
 *
 * **Warum eine Hülle und nicht sechzehn Änderungen.** Dieselbe Überlegung wie
 * bei `Feld.jsx` und `services/seiten_huelle.py`: Sechzehn Kopien derselben
 * Zeile driften auseinander, und die siebzehnte Seite vergisst sie. Hier steht
 * sie einmal, und `oeffentlicheLandmarke.test.js` hält fest, dass jede
 * öffentliche Route sie trägt.
 *
 * **`bypass` gilt genau dann als erfüllt**, wenn die Seite eine Landmarke
 * *oder* einen Sprunglink hat. Die Landmarke ist der ruhigere Weg: Ein
 * Sprunglink, den man nur mit der Tastatur sieht, will gepflegt werden und
 * zeigt bei jeder Umbenennung ins Leere.
 */
export default function OeffentlicheSeite({ children }) {
  // `id` bewusst gesetzt: Ein späterer Sprunglink braucht ein Ziel, und ein
  // Ziel, das erst beim Bedarf entsteht, entsteht nicht.
  return <main id="inhalt">{children}</main>;
}
