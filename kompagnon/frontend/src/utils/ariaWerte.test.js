/**
 * `aria-required-attr` und `aria-valid-attr-value` — die letzten beiden der
 * vier offenen Screenreader-Kriterien aus L-17.
 *
 * **Warum ein Wächter für etwas, das heute hält (26.08.2026).** Gemessen:
 * beide Klassen sind leer. `role="tab"` trägt sein `aria-selected`,
 * `role="switch"` sein `aria-checked`, und kein `aria-labelledby` zeigt ins
 * Leere — es gibt im ganzen Quellbaum keines. Eine Klasse, die heute leer
 * ist, bleibt es nur, wenn jemand hinsieht; genau das war die Begründung für
 * `linkName.test.js`, dessen vierte Klasse sich beim Messen auflöste und
 * trotzdem im Wächter blieb.
 *
 * **Was diese beiden Regeln bedeuten:**
 *
 * - `aria-required-attr`: Manche Rollen sind ohne ihr Pflicht-Attribut
 *   sinnlos. Ein `role="switch"` ohne `aria-checked` sagt „hier ist ein
 *   Schalter" und verschweigt, ob er an ist — die Auskunft, für die es ihn
 *   gibt.
 * - `aria-valid-attr-value`: Ein `aria-expanded="yes"` ist kein Fehler, den
 *   der Browser meldet; er wird schlicht ignoriert. Erlaubt sind `true`,
 *   `false` und (bei manchen) `mixed`.
 *
 * **Warum diese vier Kriterien und nicht andere:** Sie stehen in
 * `audit_pagespeed.A11Y_AUDIT_GROUPS`, Gruppe „screenreader" — es sind die,
 * die **unser eigenes Audit bei Kunden prüft**.
 */
const fs = require('fs');
const path = require('path');

const QUELLE = path.join(__dirname, '..');

/** Rollen, die ohne dieses Attribut ihre Auskunft schuldig bleiben. */
const PFLICHT = {
  checkbox: ['aria-checked'],
  switch: ['aria-checked'],
  radio: ['aria-checked'],
  tab: ['aria-selected'],
  option: ['aria-selected'],
  slider: ['aria-valuenow'],
  combobox: ['aria-expanded'],
  scrollbar: ['aria-valuenow', 'aria-controls'],
};

/** Attribute, die nur `true`/`false` (bzw. `mixed`) tragen dürfen. */
const NUR_WAHRHEITSWERT = {
  'aria-expanded': ['true', 'false', 'undefined'],
  'aria-selected': ['true', 'false', 'undefined'],
  'aria-hidden': ['true', 'false', 'undefined'],
  'aria-disabled': ['true', 'false'],
  'aria-required': ['true', 'false'],
  'aria-checked': ['true', 'false', 'mixed'],
  'aria-pressed': ['true', 'false', 'mixed'],
  'aria-current': ['true', 'false', 'page', 'step', 'location', 'date', 'time'],
  'aria-live': ['off', 'polite', 'assertive'],
};

function dateien(ordner = QUELLE, gesammelt = []) {
  for (const eintrag of fs.readdirSync(ordner, { withFileTypes: true })) {
    const voll = path.join(ordner, eintrag.name);
    if (eintrag.isDirectory()) dateien(voll, gesammelt);
    else if (/\.jsx?$/.test(eintrag.name) && !/\.test\.jsx?$/.test(eintrag.name)) {
      gesammelt.push(voll);
    }
  }
  return gesammelt;
}

/**
 * Das öffnende Tag um eine Fundstelle herum.
 *
 * **Kein `[^>]*>`** — das war der Fehler, der bei den Feldnamen gefunden
 * wurde (L-17, „Methodisch"): `onChange={e => f(e)}` enthält ein `>`, an dem
 * ein solcher Ausdruck das Tag zerschneidet. Hier wird stattdessen von der
 * Fundstelle aus rückwärts das `<` gesucht und vorwärts das schließende `>`
 * unter Mitzählen von geschweiften Klammern und Anführungszeichen.
 */
function tagUm(text, stelle) {
  let anfang = text.lastIndexOf('<', stelle);
  if (anfang === -1) return null;

  let tiefe = 0;
  let anfuehrung = null;
  for (let i = anfang; i < text.length; i++) {
    const z = text[i];
    if (anfuehrung) {
      if (z === anfuehrung) anfuehrung = null;
      continue;
    }
    if (z === '"' || z === "'" || z === '`') anfuehrung = z;
    else if (z === '{') tiefe++;
    else if (z === '}') tiefe--;
    else if (z === '>' && tiefe === 0) return text.slice(anfang, i + 1);
  }
  return null;
}

function fundstellen(muster) {
  const treffer = [];
  for (const datei of dateien()) {
    const text = fs.readFileSync(datei, 'utf8');
    const kurz = path.relative(QUELLE, datei);
    let m;
    const re = new RegExp(muster.source, 'g');
    while ((m = re.exec(text)) !== null) {
      const tag = tagUm(text, m.index);
      if (!tag) continue;
      treffer.push({ kurz, zeile: text.slice(0, m.index).split('\n').length, tag, wert: m[1] });
    }
  }
  return treffer;
}

test('jede Rolle trägt das Attribut, ohne das sie nichts aussagt', () => {
  // Arrange & Act
  const fehlend = fundstellen(/role="([a-z]+)"/)
    .filter(({ wert, tag }) => (PFLICHT[wert] || []).some(a => !tag.includes(a)))
    .map(({ kurz, zeile, wert }) => `${kurz}:${zeile} role="${wert}" ohne ${PFLICHT[wert].join('/')}`);

  // Assert
  expect(fehlend).toEqual([]);
});

test('kein aria-Attribut trägt einen Wert, den niemand versteht', () => {
  const ungueltig = [];
  for (const [attribut, erlaubt] of Object.entries(NUR_WAHRHEITSWERT)) {
    // Nur Literalwerte prüfbar — `aria-expanded={offen}` entscheidet sich
    // zur Laufzeit und ist von hier aus nicht zu sehen.
    for (const { kurz, zeile, wert } of fundstellen(new RegExp(`${attribut}="([^"]*)"`))) {
      if (!erlaubt.includes(wert)) {
        ungueltig.push(`${kurz}:${zeile} ${attribut}="${wert}" — erlaubt: ${erlaubt.join(', ')}`);
      }
    }
  }

  expect(ungueltig).toEqual([]);
});

test('kein aria-labelledby zeigt auf eine Kennung, die es nicht gibt', () => {
  const ins_leere = [];
  for (const datei of dateien()) {
    const text = fs.readFileSync(datei, 'utf8');
    const kurz = path.relative(QUELLE, datei);
    const kennungen = new Set([...text.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]));
    for (const attribut of ['aria-labelledby', 'aria-describedby', 'aria-controls']) {
      for (const m of text.matchAll(new RegExp(`${attribut}="([^"]+)"`, 'g'))) {
        for (const ziel of m[1].split(/\s+/)) {
          if (!kennungen.has(ziel)) {
            ins_leere.push(`${kurz} ${attribut}="${ziel}"`);
          }
        }
      }
    }
  }

  expect(ins_leere).toEqual([]);
});
