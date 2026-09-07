/**
 * Welche Schritte ein Produkt überhaupt kennt (L-168).
 *
 * **Der Befund vom 04.09.2026.** `computeStepStatus` liest Projektfelder —
 * `has_briefing`, `audit_score`, `scrape_full_at`. Die Kette ist damit
 * datengetrieben, aber nicht **produkt**getrieben: Jedes Projekt läuft durch
 * alle zwanzig Schritte, auch das, dessen Vertrag die Hälfte davon nicht
 * enthält.
 *
 * **Der Fall, an dem es auffiel.** Das Datenblatt WS-STA-01 (Websprint Start)
 * grenzt ausdrücklich ab: keine weiteren Unterseiten (A16), keine
 * Texterstellung (A17), keine von der Vorlage abweichende Gestaltung (A19).
 * Der Kunde sah in seinem Konto trotzdem Sitemap, Wireframe, Style Guide und
 * drei Entwürfe — Schritte, für die er nichts bezahlt hat und die niemand je
 * abhaken wird. Eine Kette, die an einem Schritt hängen bleibt, den es nicht
 * gibt, sperrt alles dahinter.
 *
 * **Warum hier nur ein Produkt Einträge hat.** Ausgeschlossen wird nur, was
 * im Datenblatt als Abgrenzung *dasteht*. Für Relaunch ließe sich einiges
 * vermuten — seine Mitwirkungsliste kennt weder M7 (Bauplan-Freigabe) noch
 * M8 (Text-Freigabe) —, aber vermutet ist nicht abgegrenzt. Der Fehler soll
 * in die sichtbare Richtung fallen: ein Schritt zu viel wird weggeklickt, ein
 * fehlender fällt niemandem auf.
 *
 * Ein leeres Feld ist deshalb eine **Entscheidung**, kein Versehen —
 * `produktSchritte.test.js` verlangt für jedes Bauprodukt einen Eintrag.
 */

/** Schritte, die das jeweilige Produkt nicht enthält — mit Beleg. */
export const NICHT_IM_PRODUKT = {
  // A16 (keine weiteren Unterseiten), A17 (Texte werden unverändert
  // übernommen), A19 (keine individuelle Gestaltung), Position 2.2
  // („Aufbau aus einer festen Vorlage").
  websprint_start: [
    'sitemap-ki',      // A16 — eine Seite
    'leistungsseiten', // A16 — eine Seite
    'wireframe-ki',    // 2.2 feste Vorlage; die M-Liste kennt kein M7
    'style-guide',     // A19
    'entwuerfe',       // A19 — keine drei Entwürfe zur Auswahl
    'ki-content',      // A17 — Texte unverändert
  ],
  // Bewusst leer: Das Datenblatt grenzt keinen Schritt aus. Die fehlenden
  // M7/M8 betreffen die Mitwirkung des Kunden, nicht unsere Arbeitsschritte —
  // das ist zweierlei, und nur das erste ist belegt.
  websprint_relaunch: [],
  websprint_neubau: [],  // Bauplan ist ausdrücklich enthalten (Pos. 1.2/1.3)
  websprint_system: [],
};

/**
 * Gilt dieser Schritt für dieses Paket?
 *
 * Ein unbekanntes oder fehlendes Paket schließt nichts aus — siehe oben.
 */
export function giltFuerProdukt(stepId, packageType) {
  const raus = NICHT_IM_PRODUKT[(packageType || '').trim()];
  return !raus || !raus.includes(stepId);
}

/** Die Schritte, die für dieses Paket übrig bleiben. */
export function schritteFuerProdukt(schritte, packageType) {
  return (schritte || []).filter((s) => giltFuerProdukt(s.id, packageType));
}
