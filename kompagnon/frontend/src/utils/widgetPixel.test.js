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
 *   3. Er feuert nur bei einem ausdrücklichen Ja der Trägerseite
 *      (10.09.2026 — vorher genügte das Häkchen im Formular).
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
  test('ohne Ja der Trägerseite feuert der Pixel nicht', () => {
    // Die Umkehrung vom 10.09.2026. Vorher hing der Pixel am Häkchen im
    // Formular — das nennt Meta nicht mehr und kann die Meldung nicht
    // begründen. Grundlage ist jetzt allein das Consent-Banner der Seite.
    expect(rumpfVonMeldeLead()).toMatch(/!einwilligungErteilt\(\)/);
  });

  test('nur ein echtes Ja zählt, nicht die bloße Abwesenheit eines Nein', () => {
    // Die Gegenprobe zur Umkehrung: Ein Riegel, der bei Schweigen öffnet,
    // wäre auf jeder Einbettung ohne Banner offen — und niemand fände es.
    expect(WIDGET).toMatch(/traegerMarketing === true/);
    expect(WIDGET).toMatch(/einwilligungRoh === '1'/);
  });

  test('das Häkchen steuert den Pixel nicht mehr', () => {
    // Der Sinn der Änderung: Der Haken gehört zu den Auswertungsmails. Wer
    // ihn wieder an den Pixel hängt, braucht den Meta-Satz im Text zurück.
    expect(rumpfVonMeldeLead()).not.toMatch(/haekchenGesetzt/);
  });

  test('derselbe Zustand geht an den Server', () => {
    // Sonst hielte der Browserweg an und der Serverweg meldete weiter.
    expect(WIDGET).toMatch(/consent_tracking: einwilligungErteilt\(\)/);
  });

  test('die Adresse geht nicht mehr an Metas Skript', () => {
    // Der erweiterte Abgleich ist entfallen. Positive Hälfte daneben: der
    // Pixel wird weiterhin mit seiner ID initialisiert.
    expect(WIDGET).toMatch(/fbq\('init', FB_PIXEL_ID\)/);
    expect(WIDGET).not.toMatch(/\bem:/);
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

  test('ein fehlender Parameter gilt als Nein — und das steht dabei', () => {
    // Umgekehrt als bis zum 09.09. Damals galt „sagt nichts" als vielleicht
    // und damit als Ja; das war auf Einbettungen ohne Banner eine Messung
    // ohne Grundlage. Jetzt ist Schweigen ein Nein (§ 25 TDDDG), und weil
    // das eine stille Abschaltung ist, muss der Grund im Code stehen.
    expect(WIDGET).toMatch(/EINWILLIGUNG_NEIN = \(einwilligungRoh === '0'/);
    expect(WIDGET).toMatch(/Schweigen ist keine Zustimmung/);
  });
});

/**
 * Der Einwilligungstext deckt genau das, was das Häkchen steuert (10.09.2026).
 *
 * **Die Geschichte in zwei Sätzen.** Am 09.09. wurde der Satz erweitert, damit
 * er Meta beim Namen nennt — das Häkchen entschied damals über die Meldung.
 * Am 10.09. ist es umgekehrt gelöst: Der lange Satz kostete Abschlüsse, also
 * ist der erweiterte Abgleich entfallen und die Meta-Einwilligung in das
 * Consent-Banner der Trägerseite gewandert. Das Häkchen steuert jetzt nur noch
 * die Auswertungsmails, und der Text sagt genau das.
 *
 * **Was hier zugesichert wird, ist die Deckungsgleichheit** — nicht Kürze.
 * Der Satz darf umformuliert werden. Er darf nur nicht mehr versprechen, als
 * das Häkchen tut, und nicht weniger, als der Code macht. Deshalb prüft die
 * zweite Hälfte dieses Blocks am Code mit, nicht nur am Text.
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

  test('der E-Mail-Zweck steht da', () => {
    // Das ist, was der Haken tatsächlich steuert.
    expect(EINWILLIGUNG).toMatch(/E-Mail/);
  });

  test('der Widerruf bleibt genannt', () => {
    expect(EINWILLIGUNG).toMatch(/widerruf/i);
  });

  test('der Satz verspricht keine Meta-Übermittlung mehr', () => {
    // Die Klammer zum Code: Solange `sende_lead` keine Adresse annimmt und
    // `fbq('init')` keine mitgibt, wäre ein Meta-Satz hier eine Einwilligung
    // in etwas, das nicht passiert — und die nächste Lesung hielte ihn für
    // den Beleg, dass es passiert.
    expect(EINWILLIGUNG).not.toMatch(/Meta|Facebook|Instagram/);
  });

  test('die Freiwilligkeit steht im Aufklapper, nicht im Kleingedruckten', () => {
    // Ohne Häkchen kommt der Bericht trotzdem (`verify_token` im Backend
    // hängt nicht am Haken). Stünde das nirgends, wäre der Haken faktisch
    // Pflicht — und eine Pflicht-Einwilligung ist keine.
    const m = WIDGET.match(/class="kpg-consent-mehr"[\s\S]*?<\/details>/);
    const DETAILS = m ? m[0].replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ') : '';
    expect(DETAILS.length).toBeGreaterThan(80);
    expect(DETAILS).toMatch(/Ohne Häkchen/);
  });

  test('der Aufklapper steht außerhalb des Labels', () => {
    // Ein <summary> im <label> schaltet beim Klick die Checkbox um: Der
    // Besucher liest nach und hat ungewollt zugestimmt.
    const label = WIDGET.match(/<label class="kpg-consent"[\s\S]*?<\/label>/);
    expect(label).not.toBeNull();
    expect(label[0]).not.toMatch(/<details/);
  });
});
