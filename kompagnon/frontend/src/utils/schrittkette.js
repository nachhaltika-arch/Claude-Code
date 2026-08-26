/**
 * Welcher Schritt eines Projekts erreichbar ist.
 *
 * **Warum eine eigene Datei.** Die Funktion sass im `OnlineFertigEditor` und
 * war damit nur pruefbar, wenn man den halben Editor mitlaedt — ueber
 * `ProzessFlow` und `BrandGuideline` bis zu einem `import.meta`, an dem der
 * Testlauf abbricht. Eine Entscheidung, die ein ganzes Projekt sperren kann,
 * darf nicht ungetestet bleiben, weil ihre Nachbarn schwer zu laden sind.
 *
 * **Die Regel.** Freigegeben ist die lueckenlose Kette erledigter Schritte
 * plus der naechste. Alles dahinter ist gesperrt, bis der Nutzer aufholt.
 */
import { SCHRITTE } from '../components/KASSidebar';

export function computeStepStatus(project, wireframeData, confirmedSteps) {
  if (!project) return {};
  const status = {};

  // Phase 1 — Analyse
  // Wir haben keine direkten boolean-Flags fürs Briefing/Audit hier — heuristisch
  status['briefing-unternehmen'] = project.has_briefing ? 'completed' : 'pending';
  status['audit'] = project.audit_score ? 'completed' : 'pending';
  // **Der Schritt las bis zum 26.08.2026 ein Feld, das nie ankam.**
  // `project.scrape_full_at` steht in der Datenbank, aber
  // `GET /api/projects/{id}` trug es nie in seine Antwort — hier stand also
  // immer `undefined`, und der Schritt blieb ewig auf `pending`, obwohl der
  // Lauf stattgefunden hatte. Ein Wert, der nicht ueber die Schnittstelle
  // geht, ist fuer die Oberflaeche nicht vorhanden.
  //
  // Seit Davids Entscheidung („der crawler ist der richtige, den anderen
  // weg") gibt es nur noch einen Scraper — den, den `AnalyseCentrale` ruft.
  // Sein Zeitstempel kommt jetzt als `content_analysiert_am` mit.
  status['content-vollanalyse'] = project.content_analysiert_am ? 'completed' : 'pending';
  status['briefing-website'] = project.has_briefing ? 'completed' : 'pending';
  status['zugangsdaten'] = 'pending'; // optional, kein eindeutiges Signal
  // Beide sind optional und tragen deshalb keine Sperre. Die Heuristik sagt
  // trotzdem, ob etwas da ist — der Punkt in der Seitenleiste soll stimmen.
  status['geo-optimierung'] = project.geo_score ? 'completed' : 'pending';
  status['leistungsseiten'] = 'pending';

  // Phase 2 — Sitemap + Wireframe
  // Sitemap-Pages werden separat geladen, hier prüfen wir nur den wireframe
  const hasWireframe = Array.isArray(wireframeData?.pages) && wireframeData.pages.length > 0;
  status['sitemap-ki'] = hasWireframe ? 'completed' : 'pending';
  status['wireframe-ki'] = hasWireframe ? 'completed' : 'pending';

  // Phase 3 — Style Guide + Design
  status['style-guide'] = wireframeData?.style_guide_approved ? 'completed' : (wireframeData?.style_guide ? 'active' : 'pending');
  status['finales-design'] = project.netlify_deploy_id ? 'completed' : 'pending';

  // Phase 4 — Produktion
  status['ki-content'] = 'pending'; // braucht Content-Generation-Tracking
  status['netlify-deploy'] = project.netlify_site_id ? 'completed' : 'pending';

  // Phase 5 — Go Live
  status['dns'] = project.netlify_domain_status === 'active' ? 'completed' : 'pending';
  status['qa'] = project.qa_score && project.qa_score >= 70 ? 'completed' : 'pending';
  status['abnahme'] = project.customer_approved_at ? 'completed' : 'pending';

  // Phase 6 — Post-Launch
  status['umami'] = 'pending';
  status['heatmap'] = 'pending';
  status['monats-report'] = 'pending';

  // User-Bestätigung überschreibt Heuristik (höchste Priorität).
  // Schema: confirmedSteps = { stepId: { confirmed: true, confirmed_at: '…' } }
  Object.entries(confirmedSteps || {}).forEach(([stepId, val]) => {
    if (val && val.confirmed) status[stepId] = 'completed';
  });

  // Lock-Logik (Variante C): nur consecutive-completed + nächster Schritt sind
  // freigegeben. Spätere Schritte sind 'locked' bis der User aufholt.
  //
  // **Ein optionaler Schritt reisst die Kette nicht ab** (21.08.2026). Vorher
  // tat er es: `zugangsdaten` traegt seit jeher `optional: true`, hat aber
  // keine Heuristik — die Kette blieb dort stehen, und alles dahinter war
  // gesperrt. `tests/seed_e2e.py` musste den Schritt eigens bestaetigen, um an
  // die interessanten Ansichten zu kommen; der Kommentar dort beschreibt genau
  // dieses Verhalten als Hindernis. Das war kein Entwurf, sondern ein
  // Widerspruch zur eigenen Kennzeichnung: Ein Schritt, der als „kein
  // Pflichtschritt fuer Fortschritt" gilt, darf den Fortschritt nicht
  // aufhalten. Ohne diese Korrektur haetten die beiden am selben Tag
  // eingefuegten Legacy-Schritte jedes laufende Projekt an Schritt 3 gesperrt.
  let consecutiveDoneIdx = -1;
  for (let i = 0; i < SCHRITTE.length; i++) {
    if (status[SCHRITTE[i].id] === 'completed' || SCHRITTE[i].optional) consecutiveDoneIdx = i;
    else break;
  }
  SCHRITTE.forEach((s, idx) => {
    if (status[s.id] === 'completed') return;
    if (idx <= consecutiveDoneIdx + 1) status[s.id] = 'ready';
    else status[s.id] = 'locked';
  });

  return status;
}
