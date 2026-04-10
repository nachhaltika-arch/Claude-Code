/**
 * Zentrale API-Fehlermeldungs-Übersetzung.
 * Gibt immer einen lesbaren deutschen String zurück.
 */

const ERROR_MAP = {
  'Slug fehlt':                       'Bitte einen URL-Bezeichner (Slug) eingeben, z.B. "homepage-standard".',
  'Slug bereits vergeben':            'Dieser Slug ist bereits vergeben — bitte einen anderen wählen.',
  'Ungültiger Slug':                  'Der Slug darf nur Kleinbuchstaben, Zahlen und Bindestriche enthalten.',
  'Could not validate credentials':   'Sitzung abgelaufen — bitte erneut anmelden.',
  'Not authenticated':                'Nicht angemeldet — bitte einloggen.',
  'Forbidden':                        'Keine Berechtigung für diese Aktion.',
  'Not found':                        'Eintrag nicht gefunden — möglicherweise gelöscht.',
  'Lead nicht gefunden':              'Kundeneintrag nicht gefunden.',
  'Projekt nicht gefunden':           'Projekt nicht gefunden — bitte Seite neu laden.',
  'field required':                   'Pflichtfeld fehlt — bitte alle markierten Felder ausfüllen.',
  'value is not a valid integer':     'Ungültige Zahl eingegeben.',
  'value is not a valid email':       'Ungültige E-Mail-Adresse.',
  'Internal Server Error':            'Serverfehler — bitte in 30 Sekunden erneut versuchen.',
  'Service Unavailable':              'Server vorübergehend nicht erreichbar — bitte kurz warten.',
  'Bad Gateway':                      'Verbindung zum Server unterbrochen — bitte Seite neu laden.',
  'Crawl bereits läuft':              'Der Crawler analysiert bereits — bitte warten.',
  'ANTHROPIC_API_KEY fehlt':          'KI-Dienst nicht konfiguriert — bitte Administrator kontaktieren.',
  'NETLIFY_TOKEN fehlt':              'Netlify ist nicht konfiguriert — bitte Administrator kontaktieren.',
  'STRIPE_SECRET_KEY fehlt':          'Stripe ist nicht konfiguriert — bitte Administrator kontaktieren.',
};

const INTERNAL_PATTERNS = [
  /object has no attribute/i, /NoneType/i, /KeyError/i,
  /AttributeError/i, /TypeError:/i, /ValueError:/i,
  /Exception:/i, /Traceback/i, /line \d+/i,
];

export function parseApiError(raw, statusCode) {
  if (Array.isArray(raw)) {
    const msgs = raw.map(e => {
      const field = Array.isArray(e.loc) ? e.loc[e.loc.length - 1] : '';
      const msg = e.msg || '';
      return ERROR_MAP[msg] || (field ? `Feld "${field}": ${ERROR_MAP[msg] || msg || 'Ungültig'}` : (ERROR_MAP[msg] || msg));
    }).filter(Boolean);
    return msgs.length > 0 ? msgs.join(' · ') : 'Eingabe ungültig — bitte alle Felder prüfen.';
  }
  if (raw && typeof raw === 'object' && raw.detail) return parseApiError(raw.detail, statusCode);
  if (raw instanceof Error) return parseApiError(raw.message, statusCode);
  if (typeof raw === 'string') {
    const t = raw.trim();
    if (ERROR_MAP[t]) return ERROR_MAP[t];
    for (const [key, val] of Object.entries(ERROR_MAP)) {
      if (t.toLowerCase().includes(key.toLowerCase())) return val;
    }
    if (INTERNAL_PATTERNS.some(p => p.test(t))) {
      return statusCode === 500
        ? 'Serverfehler — das Team wurde benachrichtigt.'
        : 'Technischer Fehler — bitte Seite neu laden.';
    }
    if (t.length < 120 && !t.startsWith('{')) return t;
  }
  if (statusCode === 401) return 'Sitzung abgelaufen — bitte erneut anmelden.';
  if (statusCode === 403) return 'Keine Berechtigung für diese Aktion.';
  if (statusCode === 404) return 'Nicht gefunden — bitte Seite neu laden.';
  if (statusCode === 409) return 'Eintrag existiert bereits.';
  if (statusCode === 422) return 'Eingabe ungültig — bitte alle Pflichtfelder prüfen.';
  if (statusCode === 429) return 'Zu viele Anfragen — bitte kurz warten.';
  if (statusCode >= 500) return 'Serverfehler — bitte in 30 Sekunden erneut versuchen.';
  return 'Ein unbekannter Fehler ist aufgetreten.';
}

export async function parseResponseJson(response) {
  try {
    const text = await response.text();
    if (!text.trim()) return {};
    return JSON.parse(text);
  } catch { return {}; }
}
