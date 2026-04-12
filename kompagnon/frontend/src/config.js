const API_BASE_URL = process.env.REACT_APP_API_URL ||
  'https://claude-code-znq2.onrender.com';

// ── Global fetch-Patch (Security Fix 14 Phase 2) ────────────────────
// Sorgt dafuer, dass jeder Request zur KOMPAGNON-API automatisch den
// httpOnly-Cookie mitsendet, ohne dass jede einzelne fetch()-Stelle
// manuell `credentials: 'include'` setzen muss.
//
// Das Backend akzeptiert nach Phase 2 ausschliesslich Cookies — ein
// `Authorization: Bearer ...`-Header im Request ist harmlos, da der
// Server ihn ignoriert. Der Monkey-Patch ist auf API-Base-URL
// gescoped, damit externe fetch-Calls (z.B. Google Fonts, Netlify)
// nicht beruehrt werden.
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
