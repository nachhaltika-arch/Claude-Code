import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL ||
  'https://claude-code-znq2.onrender.com';

// ── Global HTTP-Client Konfiguration (Security Fix 14 Phase 2) ─────────
// Sorgt dafuer, dass jeder Request zur KOMPAGNON-API automatisch den
// httpOnly-Cookie mitsendet, ohne dass jede einzelne Call-Site das
// manuell konfigurieren muss.
//
// Zwei Mechanismen, weil das Projekt BEIDE HTTP-Clients nutzt:
//   1. window.fetch — Monkey-Patch fuegt credentials: 'include' hinzu
//   2. axios        — defaults.withCredentials = true
//
// Das Backend akzeptiert nach Fix 14 Phase 2 ausschliesslich Cookies —
// ohne diese Defaults landen alle Requests als 401 Unauthorized.

// ── axios: withCredentials fuer alle Requests erzwingen ──────────────
// Doppelt abgesichert:
//   1. defaults.withCredentials = true  — greift fuer neue Requests
//   2. Request-Interceptor               — forciert es auch wenn der
//      Caller-Code einen Config-Override mitgibt (z.B. { headers })
axios.defaults.withCredentials = true;
axios.interceptors.request.use((config) => {
  // API-Base-URL matchen, damit externe axios-Calls (falls vorhanden)
  // nicht beruehrt werden
  const url = config.url || '';
  const fullUrl = config.baseURL ? config.baseURL + url : url;
  if (fullUrl.startsWith(API_BASE_URL)) {
    config.withCredentials = true;
  }
  return config;
});

// ── fetch patch ───────────────────────────────────────────────────────
(function patchFetchForCookies() {
  if (typeof window === 'undefined' || !window.fetch) return;
  if (window.__kompagnon_fetch_patched) return;
  window.__kompagnon_fetch_patched = true;

  const originalFetch = window.fetch.bind(window);
  window.fetch = function patchedFetch(input, init = {}) {
    try {
      // URL aus Request-Objekt oder String extrahieren
      const url = typeof input === 'string'
        ? input
        : (input && input.url) || '';

      // Nur eigene API-Requests patchen — keine Third-Party-Calls
      if (url && url.startsWith(API_BASE_URL)) {
        return originalFetch(input, {
          ...init,
          credentials: init.credentials || 'include',
        });
      }
    } catch { /* fall through */ }
    return originalFetch(input, init);
  };
})();

export default API_BASE_URL;
