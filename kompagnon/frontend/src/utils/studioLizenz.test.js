/**
 * Was die Grapes-Studio-Lizenz von uns verlangt (L-149).
 *
 * **Am 07.09.2026 geprüft, nachdem der Eintrag es seit dem 02.09. verlangte.**
 * Der Lizenztext steht **nicht im Paket**: `node_modules/@grapesjs/studio-sdk/
 * LICENSE.md` ist eine einzige Zeile, die auf
 * `github.com/GrapesJS/studio/blob/main/LICENSE.md` verweist. Gelesen wurde er
 * dort.
 *
 * **Der Vergleich mit dem Relume-Fall vom 06.05.2026 geht anders aus.** Dort
 * verbot die Lizenz die Weitergabe in einem konkurrierenden Erzeugnis, und die
 * Bibliothek flog raus. Diese Lizenz hat **keine** solche Klausel. Sie erlaubt
 * kommerziellen Einsatz (§1.1) und das Bündeln „with your projects, in
 * compiled or minified form" — verboten ist die Weitergabe „as a standalone
 * product" (§1.3). Wir bündeln, wir verkaufen den Editor nicht einzeln.
 *
 * **Eine Klausel können wir selbst verletzen, und nur diese prüft die Datei
 * hier:** §2.1 — „You shall not remove, disable, or alter any such Watermark,
 * except as otherwise agreed in a separate written agreement." Solange kein
 * Lizenzschlüssel gesetzt ist, zeigt das SDK sein Wasserzeichen; es
 * wegzustylen wäre ein Lizenzverstoß und zugleich der naheliegendste Griff,
 * wenn jemand die Oberfläche „aufräumt". Genau deshalb ein Wächter und keine
 * Notiz.
 *
 * **Offen und nicht durch Code zu klären:** Die Lizenz sagt nichts darüber,
 * ob ein Erwerber sie bei einer Übertragung des Systems weiterführen darf —
 * §9 regelt nur das Recht von Grapes Studio, *selbst* abzutreten. Das ist
 * genau die Frage aus dem Lagebild-Eintrag, und sie gehört schriftlich an den
 * Hersteller.
 */
import fs from 'fs';
import path from 'path';

const QUELLE = path.join(__dirname, '..');

/** Alle eigenen Quelldateien — ohne Tests, ohne node_modules. */
function dateien(ordner = QUELLE, gesammelt = []) {
  for (const eintrag of fs.readdirSync(ordner, { withFileTypes: true })) {
    const voll = path.join(ordner, eintrag.name);
    if (eintrag.isDirectory()) dateien(voll, gesammelt);
    else if (/\.(jsx?|css)$/.test(eintrag.name) && !/\.test\./.test(eintrag.name)) {
      gesammelt.push(voll);
    }
  }
  return gesammelt;
}

describe('Grapes-Studio-Lizenz — was an uns liegt', () => {
  const alle = dateien();

  test('der Quellbaum wird überhaupt gelesen', () => {
    // Ein Wächter, der seinen Gegenstand nicht findet, ist immer grün.
    expect(alle.length).toBeGreaterThan(100);
  });

  test('niemand blendet das Wasserzeichen aus (§2.1)', () => {
    // Gesucht wird das Verstecken, nicht das Wort: eine Regel, die etwas mit
    // „watermark“ oder „badge“ im Namen auf `display:none`, `visibility:
    // hidden` oder `opacity: 0` setzt — und ebenso ein Konfigurationsschalter.
    const verdacht = /(watermark|gjs-badge|studio-badge)/i;
    const versteckt = /(display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0|hide\w*\s*:\s*true|false)/i;
    const treffer = [];
    for (const datei of alle) {
      const text = fs.readFileSync(datei, 'utf8');
      text.split('\n').forEach((zeile, nr) => {
        if (verdacht.test(zeile) && versteckt.test(zeile)) {
          treffer.push(`${path.relative(QUELLE, datei)}:${nr + 1}`);
        }
      });
    }
    expect(treffer).toEqual([]);
  });

  test('der Lizenzschlüssel steht in einer Variablen, nicht im Quelltext', () => {
    // §1.2 — ein Schlüssel „may be required". Wo er einmal gesetzt wird,
    // gehört er in die Umgebung: Ein Schlüssel im Quelltext landet im Bündel
    // **und** in der Historie, und das ist im Projekt schon einmal teuer
    // gewesen.
    const konfig = fs.readFileSync(path.join(QUELLE, 'utils', 'studioEditorConfig.js'), 'utf8');
    expect(konfig).toMatch(/process\.env\.REACT_APP_GJS_LICENSE_KEY/);
    expect(konfig).not.toMatch(/STUDIO_LICENSE_KEY\s*=\s*['"][^'"]{8,}['"]/);
  });
});
