/**
 * Der Facebook-Pixel im Analyse-Widget (Wunsch David, 08.09.2026).
 *
 * Das Widget ist eine einzelne HTML-Datei, die eingebettet auf **fremden**
 * Seiten läuft; es gibt dort keine Bausteine, die man einzeln aufrufen
 * könnte. Geprüft wird deshalb am Text der Datei — aber an **Eigenschaften**,
 * nicht am Wortlaut.
 *
 * **Warum das hier ausdrücklich dasteht.** Die erste Fassung dieser Datei
 * prüfte Zeichenketten: `meldeLead();` und `fbq('track', 'Lead')`. Als der
 * Serverweg dazukam, hieß es `meldeLead(eventId, email)` und
 * `fbq('track', 'Lead', {}, …)` — fünf von elf Prüfungen wurden rot, **ohne
 * dass sich eine der zugesicherten Eigenschaften geändert hätte**. Ein
 * Wächter, der bei jeder Umbenennung anschlägt, wird beim dritten Fehlalarm
 * abgeschaltet; dann fängt er auch den echten Fund nicht mehr. Dieselbe
 * Lehre wie beim Kanarienvogel des Routen-Werkzeugs.
 *
 * Zugesichert sind vier Eigenschaften:
 *
 *   1. Der Pixel lädt **erst beim Absenden**, nicht beim Anzeigen. Ein
 *      Pixel, der beim Aufruf lädt, setzt Tracking ohne Einwilligung
 *      (§ 25 TTDSG) — und das Widget bringt auf einer fremden Seite keinen
 *      Cookie-Banner mit.
 *   2. Gemeldet wird **ein** Ereignis, `Lead`, und erst, wenn das Backend
 *      die Anfrage angenommen hat.
 *   3. Ein ausdrückliches Nein der Trägerseite schaltet ihn ab.
 *   4. Die Adressfelder stehen in der Reihenfolge Domain → E-Mail.
 *
 * **Jede Abwesenheits-Prüfung hat eine positive daneben.** „Kein PageView"
 * wäre auch dann grün, wenn der ganze Pixel verschwunden ist.
 */
import fs from 'fs';
import path from 'path';

const WIDGET = fs.readFileSync(
  path.join(__dirname, '..', '..', 'public', 'embed', 'audit-widget.html'),
  'utf8',
);

/** Der Rumpf von `meldeLead`, unabhängig von seiner Unterschrift. */
function rumpfVonMeldeLead() {
  const start = WIDGET.search(/function\s+meldeLead\s*\(/);
  if (start < 0) return null;
  const auf = WIDGET.indexOf('{', start);
  let tiefe = 0;
  for (let i = auf; i < WIDGET.length; i += 1) {
    if (WIDGET[i] === '{') tiefe += 1;
    if (WIDGET[i] === '}') {
      tiefe -= 1;
      if (tiefe === 0) return WIDGET.slice(auf, i + 1);
    }
  }
  return null;
}

/** Alle Aufrufe von `meldeLead(…)` — ohne die Definition selbst. */
function aufrufeVonMeldeLead() {
  return [...WIDGET.matchAll(/(^|[^\w.])meldeLead\s*\(/g)]
    .filter((t) => !/function\s+$/.test(WIDGET.slice(0, t.index + t[1].length)));
}

describe('Reihenfolge der Formularfelder', () => {
  test('die Webseiten-Adresse steht vor der E-Mail', () => {
    const url = WIDGET.indexOf('id="kpg-url"');
    const email = WIDGET.indexOf('id="kpg-email"');
    expect(url).toBeGreaterThan(-1);
    expect(email).toBeGreaterThan(-1);
    expect(url).toBeLessThan(email);
  });

  test('beide Felder sind Pflicht geblieben', () => {
    // Die Gegenprobe zur Reihenfolge: Ein Feld, das beim Umstellen sein
    // `required` verliert, stünde weiterhin an der richtigen Stelle.
    expect(WIDGET).toMatch(/id="kpg-url" type="text" required/);
    expect(WIDGET).toMatch(/id="kpg-email" type="email" required/);
  });
});

describe('Wann der Pixel lädt', () => {
  test('das Skript von Facebook kommt genau einmal vor', () => {
    const treffer = WIDGET.match(/connect\.facebook\.net/g) || [];
    expect(treffer).toHaveLength(1);
  });

  test('es steht nicht als eigenes script-Tag im Kopf der Seite', () => {
    // Ein `<script src="…fbevents.js">` im Markup lüde beim Anzeigen — genau
    // das, was hier nicht passieren soll.
    expect(WIDGET).not.toMatch(/<script[^>]+connect\.facebook\.net/);
  });

  test('geladen wird im Rumpf von meldeLead', () => {
    // Die positive Hälfte: Das Skript ist da, und es steht in der Funktion,
    // die erst beim Absenden läuft.
    const rumpf = rumpfVonMeldeLead();
    expect(rumpf).not.toBeNull();
    expect(rumpf).toMatch(/connect\.facebook\.net/);
  });

  test('kein fbq-Aufruf außerhalb von meldeLead', () => {
    const rumpf = rumpfVonMeldeLead() || '';
    const gesamt = (WIDGET.match(/fbq\s*\(/g) || []).length;
    const drinnen = (rumpf.match(/fbq\s*\(/g) || []).length;
    expect(gesamt).toBeGreaterThan(0);
    expect(drinnen).toBe(gesamt);
  });

  test('ohne Pixel-ID passiert nichts', () => {
    expect(rumpfVonMeldeLead()).toMatch(/!FB_PIXEL_ID/);
  });

  test('die ID kommt aus der Konfiguration und wird dort geprüft', () => {
    expect(WIDGET).toMatch(/cfg\.facebook_pixel_id/);
    expect(WIDGET).toMatch(/\\d\{10,20\}/);
  });
});

describe('Was gemeldet wird', () => {
  test('genau ein Ereignistyp, und das ist Lead', () => {
    const ereignisse = [...WIDGET.matchAll(/fbq\(\s*'track'\s*,\s*'(\w+)'/g)]
      .map((t) => t[1]);
    expect([...new Set(ereignisse)]).toEqual(['Lead']);
  });

  test('kein PageView — und der Lead ist trotzdem da', () => {
    // Ohne die zweite Zusicherung wäre dieser Test auch dann grün, wenn
    // jemand den Pixel ganz entfernt hätte.
    expect(WIDGET).not.toMatch(/'PageView'/);
    expect(WIDGET).toMatch(/fbq\(\s*'track'\s*,\s*'Lead'/);
  });

  test('gemeldet wird erst, wenn das Backend die Anfrage angenommen hat', () => {
    // Die Meldung muss hinter der Stelle stehen, an der die Antwort des
    // Servers ausgewertet wird — vorher zählte sie auch abgelehnte Versuche.
    const annahme = WIDGET.search(/if \(!start\./);
    const [erster] = aufrufeVonMeldeLead();
    expect(annahme).toBeGreaterThan(-1);
    expect(erster).toBeDefined();
    expect(erster.index).toBeGreaterThan(annahme);
  });

  test('gemeldet wird an genau einer Stelle', () => {
    // Zwei Aufrufe wären zwei Leads für eine Anfrage. Die Sperre in der
    // Funktion fängt das ab, aber ein zweiter Aufruf wäre ein Zeichen, dass
    // jemand die Regel nicht kannte.
    expect(aufrufeVonMeldeLead()).toHaveLength(1);
  });
});

describe('Wer zugestimmt haben muss', () => {
  test('ohne Häkchen im Formular feuert der Pixel nicht', () => {
    // Der Fund vom 08.09.2026: Der Pixel hing allein am Parameter der
    // Trägerseite. Wer das Häkchen wegließ, weil er keine Werbepost will,
    // wurde trotzdem an Meta gemeldet.
    expect(rumpfVonMeldeLead()).toMatch(/!haekchenGesetzt/);
  });

  test('das Häkchen wird von der Absendestelle durchgereicht', () => {
    // Die Gegenprobe: Ein Riegel, dem niemand den Wert gibt, wäre entweder
    // immer zu oder immer offen — beides unbemerkt.
    expect(WIDGET).toMatch(/meldeLead\([^)]*consentMarketing\)/);
  });

  test('das Nein der Trägerseite geht auch an den Server', () => {
    // Sonst hielte der Browserweg an und der Serverweg meldete weiter.
    expect(WIDGET).toMatch(/consent_tracking: einwilligungVerweigert\(\)/);
  });
});

describe('Was die Trägerseite nachträglich sagen kann', () => {
  test('das Widget hört auf eine Einwilligungsnachricht', () => {
    expect(WIDGET).toMatch(/'kpg-consent'/);
    expect(WIDGET).toMatch(/addEventListener\('message'/);
  });

  test('nur das eigene Elternfenster wird gehört', () => {
    // Ohne diese Prüfung könnte jedes eingebettete Fenster eine
    // Einwilligung behaupten, die niemand gegeben hat.
    expect(WIDGET).toMatch(/e\.source !== parent/);
  });

  test('es wird einmal nachgefragt', () => {
    // Wer das iframe vor seinem Banner rendert, verpasst die Antwort sonst.
    expect(WIDGET).toMatch(/'kpg-consent-request'/);
  });

  test('nur ein echter Wahrheitswert zählt als Antwort', () => {
    // „marketing: 'nein'" ist eine Zeichenkette und in JavaScript wahr —
    // ein Nein, das als Ja durchginge.
    expect(WIDGET).toMatch(/typeof n\.marketing !== 'boolean'/);
  });
});

describe('Was die Trägerseite abschalten kann', () => {
  test('ein ausdrückliches Nein hält den Pixel an', () => {
    // Geprüft wird die Kette, nicht ein Name: Der Rumpf fragt die
    // Ablehnung ab, und die Ablehnung kennt beide Quellen — den
    // Aufrufparameter und die nachträgliche Nachricht der Trägerseite.
    expect(rumpfVonMeldeLead()).toMatch(/einwilligungVerweigert\(\)/);
    expect(WIDGET).toMatch(/traegerMarketing === false/);
    expect(WIDGET).toMatch(/einwilligungRoh === '0'/);
  });

  test('ein fehlender Parameter schaltet nicht still ab', () => {
    // Die Gegenprobe: „sagt nichts" darf nicht als Nein gelten — sonst wäre
    // der Pixel überall dort tot, wo die Einbettung nichts mitgibt, und
    // niemand fände den Grund.
    expect(WIDGET).not.toMatch(/EINWILLIGUNG_NEIN\s*=\s*!/);
    expect(WIDGET).toMatch(/EINWILLIGUNG_NEIN = \(einwilligungRoh === '0'/);
  });
});

/**
 * Der Einwilligungstext nennt Meta beim Namen (09.09.2026).
 *
 * **Der Anlass.** Seit dem 08.09. entscheidet das Häkchen im Formular
 * darüber, ob der Lead an Meta gemeldet wird — `meta_conversions.darf_melden`
 * verlangt ein Ja. Der Satz daneben sagte aber nur, KOMPAGNON dürfe „per
 * E-Mail kontaktieren". Eine Einwilligung, die einen Zweck nicht nennt, deckt
 * ihn nicht; die Auslegung war die vorsichtigere, nicht die saubere. Genau so
 * stand es im Kopf von `test_meta_einwilligung.py`, mit dem Zusatz, das sei
 * eine Textentscheidung und gehöre David. Er hat sie am 09.09. getroffen.
 *
 * **Geprüft werden Eigenschaften, nicht der Wortlaut** — wie im Rest dieser
 * Datei. Der Satz darf umformuliert werden; er darf nur nicht aufhören, die
 * drei Dinge zu sagen, an denen die Einwilligung hängt: **wer** meldet,
 * **wohin**, und dass sie **widerruflich** ist.
 */
describe('Was der Besucher zustimmt', () => {
  /** Der Text im Häkchen — unabhängig von Auszeichnung und Umbrüchen. */
  const EINWILLIGUNG = (() => {
    const m = WIDGET.match(/class="kpg-consent"[\s\S]*?<\/label>/);
    return m ? m[0].replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ') : '';
  })();

  test('der Text ist überhaupt auffindbar', () => {
    // Die positive Probe zuerst: Ohne sie wären alle folgenden Prüfungen
    // auch dann grün, wenn das Häkchen aus dem Formular verschwindet.
    expect(EINWILLIGUNG.length).toBeGreaterThan(80);
    expect(EINWILLIGUNG).toMatch(/type="checkbox"|kpg-consent/);
  });

  test('Meta wird beim Namen genannt', () => {
    // Der eigentliche Fund. Vorher stand hier nur „per E-Mail kontaktiert".
    expect(EINWILLIGUNG).toMatch(/Meta/);
  });

  test('der Kontaktzweck steht weiterhin da', () => {
    // Die Gegenprobe: Der neue Zweck darf den alten nicht verdrängen — die
    // Bestätigungsmail und der Bericht hängen an ihm.
    expect(EINWILLIGUNG).toMatch(/E-Mail/);
  });

  test('es steht dabei, dass die Adresse nicht im Klartext geht', () => {
    // Sonst liest der Satz sich schlimmer, als der Vorgang ist: Übermittelt
    // wird ein SHA-256-Hash, nicht die Adresse.
    expect(EINWILLIGUNG).toMatch(/unkenntlich|verschlüsselt|pseudonym/i);
  });

  test('der Widerruf bleibt genannt', () => {
    expect(EINWILLIGUNG).toMatch(/widerruf/i);
  });
});
