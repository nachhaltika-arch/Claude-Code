import React, { createContext, useContext, useState, useEffect } from 'react';
import API_BASE_URL from '../config';

const AuthContext = createContext(null);

// ── Token-Storage ─────────────────────────────────────────────────
// Fix 14 — JWT ist jetzt primaer ein httpOnly-Cookie. Der Token
// liegt zusaetzlich waehrend der Uebergangsphase in sessionStorage
// (NICHT localStorage), damit existierende Pages, die noch
// `Authorization: Bearer ${token}` bauen, weiter funktionieren.
// sessionStorage ist tab-scoped und wird beim Schliessen des Tabs
// geloescht — eine erste Haertung gegen persistente XSS-Payloads.
// Phase 2: diesen Token-Fallback komplett entfernen, wenn alle
// fetch()-Calls auf `credentials: 'include'` umgestellt sind.
const TOKEN_KEY = 'kompagnon_token';
const USER_KEY  = 'kompagnon_user';

const readToken = () => {
  try { return sessionStorage.getItem(TOKEN_KEY); } catch { return null; }
};
const writeToken = (t) => {
  try { sessionStorage.setItem(TOKEN_KEY, t); } catch { /* ignore */ }
};
const clearToken = () => {
  try {
    sessionStorage.removeItem(TOKEN_KEY);
    // Aus altem localStorage auch entfernen, falls noch Reste aus Pre-Fix-14
    localStorage.removeItem(TOKEN_KEY);
  } catch { /* ignore */ }
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(() => readToken());

  useEffect(() => {
    // Sowohl mit Token (Bearer-Fallback) als auch ohne (Cookie-only)
    // versuchen, den User zu laden — das Backend ist dual-mode.
    loadUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadUser = async () => {
    try {
      const headers = {};
      const currentToken = readToken();
      if (currentToken) headers.Authorization = `Bearer ${currentToken}`;
      const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
        headers,
        credentials: 'include',   // httpOnly-Cookie mitsenden
      });
      if (res.ok) {
        setUser(await res.json());
      } else {
        // Kein gueltiger Cookie + kein gueltiger Token → ausloggen
        clearToken();
        setToken(null);
        setUser(null);
      }
    } catch {
      clearToken();
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = (newToken, userData) => {
    // Der Cookie wurde vom Backend bereits gesetzt (httpOnly).
    // Token wird waehrend der Transition zusaetzlich in sessionStorage
    // gespeichert, damit Pages mit Bearer-Header weiter funktionieren.
    writeToken(newToken);
    setToken(newToken);
    setUser(userData);
    // User-Objekt fuer Reload-Resilienz im sessionStorage sichern
    try { sessionStorage.setItem(USER_KEY, JSON.stringify(userData)); } catch { /* ignore */ }
  };

  const logout = () => {
    // Best-effort Server-Revokation — Cookie wird vom Backend geloescht,
    // Token kommt zusaetzlich in die Blacklist.
    const existing = readToken();
    try {
      fetch(`${API_BASE_URL}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include',
        headers: existing ? { Authorization: `Bearer ${existing}` } : {},
        keepalive: true,
      }).catch(() => {});
    } catch { /* ignore */ }

    clearToken();
    try { sessionStorage.removeItem(USER_KEY); } catch { /* ignore */ }
    setToken(null);
    setUser(null);
  };

  const hasRole = (...roles) => {
    if (!user?.role) return false;
    // Superadmin inherits admin rights — passes any admin check
    if (user.role === 'superadmin' && roles.includes('admin')) return true;
    return roles.includes(user.role);
  };

  const isSuperadmin = () => user?.role === 'superadmin';

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, hasRole, isSuperadmin }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);

export async function apiCall(url, options = {}) {
  const token = readToken();
  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    credentials: 'include',       // httpOnly-Cookie immer mitsenden
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  // Token abgelaufen oder serverseitig invalidiert (Blacklist) → sauber ausloggen.
  // Login-Endpunkte ausnehmen, sonst wird jeder fehlerhafte Login-Versuch
  // zum Force-Logout.
  if (response.status === 401 && !url.includes('/api/auth/login')) {
    clearToken();
    try { sessionStorage.removeItem(USER_KEY); } catch { /* ignore */ }
    if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
      window.location.href = '/login';
    }
  }

  return response;
}
