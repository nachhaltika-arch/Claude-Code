/**
 * L-17, dritte Klasse: Was mit der Maus geht, muss mit der Tastatur gehen.
 *
 * Gemessen am 21.08.2026: **167 klickbare Elemente** ohne jede
 * Tastaturbedienung — 165 `<div>`, ein `<span>`, eine `<tr>`. Sie tragen ein
 * `onClick` und sonst nichts. Das ist **WCAG 2.1.1, Stufe A**: kein „schlechter
 * bedienbar", sondern „gar nicht bedienbar".
 *
 * **113 davon sind maschinell versorgt** — die, die selbst kein weiteres
 * Bedienelement enthalten. Sie tragen jetzt `role="button"`, `tabIndex={0}`
 * und ein `onKeyDown`, das denselben Vorgang auslöst.
 *
 * **54 bleiben und stehen hier als Zahl.** In ihnen sitzt bereits ein
 * Bedienelement — eine Schaltfläche, ein Link, ein Eingabefeld. Dort wäre
 * `role="button"` falsch: Ein Bedienelement in einem Bedienelement ist ein
 * eigener Mangel, und was stattdessen richtig ist, entscheidet sich an der
 * Stelle (meist: den Klick nach innen verlegen, wo er hingehört).
 *
 * Dieser Wächter ist eine **Ratsche**. Er verlangt nicht null — er verbietet
 * mehr. Wer die Zahl senkt, senkt auch die Schranke; wer neue Stellen baut,
 * merkt es sofort. Eine Schranke, die bei null steht und rot ist, würde
 * niemandem helfen: Sie wäre am ersten Tag abgeschaltet.
 */
const fs = require('fs');
const path = require('path');

const WURZEL = path.join(__dirname, '..');

/** Der Stand vom 21.08.2026. Nur nach unten anpassen.
 *  54 → 53 beim Fertigstellen von M4: `ProductManager.jsx` ist entfernt.
 *  Er war gegen eine Produkt-Schnittstelle geschrieben, die es nicht gibt. */
const VERBLEIBEND = 53;

function tagEnde(text, start) {
  let tiefe = 0;
  let anfuehrung = null;
  for (let i = start; i < text.length; i += 1) {
    const z = text[i];
    if (anfuehrung) {
      if (z === anfuehrung) anfuehrung = null;
    } else if (z === '"' || z === "'" || z === '`') {
      anfuehrung = z;
    } else if (z === '{') tiefe += 1;
    else if (z === '}') tiefe -= 1;
    else if (z === '>' && tiefe === 0) return i;
  }
  return -1;
}

function dateien(verzeichnis, treffer = []) {
  for (const eintrag of fs.readdirSync(verzeichnis, { withFileTypes: true })) {
    const voll = path.join(verzeichnis, eintrag.name);
    if (eintrag.isDirectory()) dateien(voll, treffer);
    else if (/\.jsx?$/.test(eintrag.name) && !eintrag.name.includes('.test.')) treffer.push(voll);
  }
  return treffer;
}

function nurMitMaus() {
  const fund = [];
  for (const datei of dateien(WURZEL)) {
    const text = fs.readFileSync(datei, 'utf8');
    const muster = /<(div|span|li|tr|td)\b/g;
    let treffer = muster.exec(text);
    while (treffer !== null) {
      const ende = tagEnde(text, muster.lastIndex);
      if (ende !== -1) {
        const attrs = text.slice(muster.lastIndex, ende);
        const klickbar = attrs.includes('onClick');
        const tastatur = /onKey(Down|Press|Up)/.test(attrs);
        if (klickbar && !tastatur) {
          const zeile = text.slice(0, treffer.index).split('\n').length;
          fund.push(`${path.relative(WURZEL, datei).split(path.sep).join('/')}:${zeile}`);
        }
      }
      treffer = muster.exec(text);
    }
  }
  return fund;
}

test('kein neues Bedienelement, das nur die Maus erreicht', () => {
  const fund = nurMitMaus();

  expect(fund.length).toBeLessThanOrEqual(VERBLEIBEND);
});

test('die Ratsche steht nicht höher als nötig', () => {
  // Sonst wächst der Rückstand unbemerkt unter der Schranke weiter.
  const fund = nurMitMaus();

  expect(fund.length).toBe(VERBLEIBEND);
});
