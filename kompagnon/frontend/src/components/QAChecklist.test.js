import { altenStandUebernehmen } from './QAChecklist';

/**
 * Der Umstieg von der kurzen auf die reiche Checkliste (L-95, 24.08.2026).
 *
 * `QAChecklist` (303 Zeilen) tritt an die Stelle von `QmChecklisteEmbed`
 * (53). Beide speichern ein Verzeichnis aus Kennung → Haken, aber in
 * **verschiedene Spalten**: `qa_checklist_json` gegen `gbp_checklist_json`.
 *
 * Ein glatter Tausch hätte zweierlei verloren: die bereits gesetzten Haken
 * und sieben Prüfpunkte, die es nur in der kurzen Liste gab. Die Punkte sind
 * mit ihren alten Kennungen übernommen; diese Tests halten fest, dass auch
 * die Haken mitwandern — und wo sie es bewusst nicht tun.
 */
describe('Alten Checklisten-Stand übernehmen', () => {
  test('gesetzte Haken wandern mit', () => {
    const alt = JSON.stringify({ ssl: true, links: true, forms: true });
    expect(altenStandUebernehmen(alt)).toEqual({
      ssl: true, links: true, forms: true,
    });
  });

  test('nicht gesetzte Haken erzeugen keinen Eintrag', () => {
    const alt = JSON.stringify({ ssl: true, links: false, maps: false });
    expect(altenStandUebernehmen(alt)).toEqual({ ssl: true });
  });

  test('„analytics" heißt hier „ga_eingerichtet"', () => {
    expect(altenStandUebernehmen(JSON.stringify({ analytics: true })))
      .toEqual({ ga_eingerichtet: true });
  });

  test('„impressum" wird NICHT auf „datenschutz" übertragen', () => {
    // Die alte Zeile lautete „Impressum + Datenschutz vorhanden", die neue
    // verlangt „Datenschutzerklärung DSGVO-konform" — das ist mehr als
    // Vorhandensein. Ein übernommener Haken wäre dort eine Behauptung, die
    // niemand geprüft hat.
    const uebernommen = altenStandUebernehmen(JSON.stringify({ impressum: true }));
    expect(uebernommen.impressum).toBe(true);
    expect(uebernommen.datenschutz).toBeUndefined();
  });

  test('die PageSpeed-Zeile wird nicht übernommen', () => {
    // Die alte prüfte „> 80 (Mobile + Desktop)", die neue trennt in > 70 und
    // > 85 und setzt beide aus den tatsächlichen Messwerten.
    expect(altenStandUebernehmen(JSON.stringify({ speed: true }))).toEqual({});
  });

  test('kein alter Stand ergibt ein leeres Verzeichnis', () => {
    expect(altenStandUebernehmen(null)).toEqual({});
    expect(altenStandUebernehmen('')).toEqual({});
  });

  test('beschädigtes JSON wirft nicht', () => {
    expect(altenStandUebernehmen('{kaputt')).toEqual({});
    expect(altenStandUebernehmen('[1,2,3]')).toEqual({});
  });
});
