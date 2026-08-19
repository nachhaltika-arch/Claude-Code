/**
 * Die Wörter, mit denen wir über den Zustand und die Herkunft eines Betriebs
 * sprechen — an einer Stelle.
 *
 * Vorher gab es zwei Abbildungen, die nicht dasselbe konnten:
 *
 *   Customers.jsx  Label + semantische Variante, über den Badge-Baustein
 *   Companies.jsx  fest eingetragene Hex-Farben, **ohne Labels**
 *
 * Die zweite zeigte deshalb die rohen Datenbankwerte an — `new`, `won`,
 * `proposal_sent` — in einer deutschen Oberfläche. Und weil ihr `proposal_sent`
 * fehlte, stand genau dieser Status ohne Rahmen in der Liste: Der Rückfall
 * lieferte eine neutrale Farbe, aber niemand sah, dass ein Wert fehlte.
 *
 * Daraus die Regel für diese Datei: **Ein unbekannter Wert wird nie roh
 * ausgegeben.** Er bekommt eine lesbare Form und eine neutrale Variante — und
 * fällt dadurch als „kenne ich nicht" auf, statt als englisches Fragment
 * durchzurutschen.
 */

/** Zustand eines Betriebs im Vertriebsweg. Schlüssel = Wert in der Datenbank. */
export const LEAD_STATUS = {
  new:           { label: 'Neu',          variant: 'neutral' },
  contacted:     { label: 'Kontaktiert',  variant: 'info'    },
  qualified:     { label: 'Qualifiziert', variant: 'success' },
  proposal_sent: { label: 'Angebot',      variant: 'warning' },
  won:           { label: 'Gewonnen',     variant: 'success' },
  lost:          { label: 'Verloren',     variant: 'danger'  },
  customer:      { label: 'Kunde',        variant: 'info'    },
};

/**
 * Wo ein Betrieb im Trichter steht — getrennt davon, wie weit die Bearbeitung
 * ist. Der Status oben beantwortete beides gleichzeitig und deshalb keines
 * richtig (19.08.2026, aus dem HubSpot-Vergleich).
 *
 * Die Schlüssel spiegeln `backend/services/lebenszyklus.py`. Ein Test hält
 * beide Seiten zusammen — laufen sie auseinander, bekommt ein Betrieb eine
 * Phase, die hier keinen Namen hat.
 *
 * `null` ist ein gültiger Wert und heißt „nicht einzuordnen". Er wird
 * angezeigt, nicht versteckt.
 */
export const LEAD_PHASE = {
  interessent:   { label: 'Interessent',  variant: 'neutral' },
  im_gespraech:  { label: 'Im Gespräch',  variant: 'info'    },
  kunde:         { label: 'Kunde',        variant: 'success' },
  ausgeschieden: { label: 'Ausgeschieden', variant: 'danger' },
};

/** Beschriftung einer Phase — auch für den unbekannten Fall. */
export function leadPhaseLabel(phase) {
  if (!phase) return 'Phase offen';
  return LEAD_PHASE[phase]?.label || lesbar(phase) || 'Phase offen';
}

/** Woher ein Betrieb kam. Freitext ist erlaubt — Kampagnennamen stehen hier. */
export const LEAD_SOURCE = {
  domain_import:   'Domain-Import',
  landing_audit:   'Landingpage',
  audit:           'Audit',
  // Schreibt `routers/widget.py:182` — der Weg über das eingebettete Widget.
  // Fehlte hier zunächst und erschien in der Liste als „Embed audit": Der
  // Rückfall machte den Wert lesbar, aber halb englisch. Genau so soll er sich
  // verraten — und genau deshalb gehört er dann nachgetragen.
  embed_audit:     'Analyse-Widget',
  widget:          'Analyse-Widget',
  manual:          'Von Hand',
  hwk:             'Handwerkskammer',
  stripe_checkout: 'Kauf',
};

/**
 * Aus einem technischen Wert ein lesbares Wort machen.
 * `postkarte-koblenz-mai-2025` → `Postkarte koblenz mai 2025`
 */
function lesbar(wert) {
  const roh = String(wert || '').trim();
  if (!roh) return '';
  const mitLeerzeichen = roh.replace(/[_-]+/g, ' ');
  return mitLeerzeichen.charAt(0).toUpperCase() + mitLeerzeichen.slice(1);
}

/** Beschriftung eines Status. Unbekannte Werte werden lesbar gemacht, nie roh. */
export function leadStatusLabel(status) {
  const key = String(status || '').toLowerCase();
  return LEAD_STATUS[key]?.label || lesbar(status) || 'Unbekannt';
}

/** Semantische Variante für den Badge-Baustein. Unbekanntes bleibt neutral. */
export function leadStatusVariant(status) {
  const key = String(status || '').toLowerCase();
  return LEAD_STATUS[key]?.variant || 'neutral';
}

/**
 * Beschriftung einer Herkunft.
 *
 * Anders als beim Status ist Freitext hier normal: Kampagnennamen wie
 * `postkarte-koblenz-mai-2025` werden beim Import vergeben. Sie werden lesbar
 * gemacht, nicht abgewiesen.
 */
export function leadSourceLabel(source) {
  const key = String(source || '').toLowerCase();
  return LEAD_SOURCE[key] || lesbar(source) || 'Unbekannt';
}
