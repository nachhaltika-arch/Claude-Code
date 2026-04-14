import React, { createContext, useContext, useState, useEffect } from 'react';
import API_BASE_URL from '../config';

const AuthContext = createContext(null);

// ── Token-Storage ─────────────────────────────────────────────────
// Dual-Auth (Mobile-Safari-Fix):
// - Desktop / normale Browser: httpOnly-Cookie (primary)
// - Mobile Safari / iOS WebKit: localStorage + Bearer-Header (fallback),
//   weil ITP Cross-Origin httpOnly-Cookies blockiert.
// Das User-Objekt bleibt in sessionStorage fuer Reload-Resilienz.
const USER_KEY = 'kompagnon_user';
const TOKEN_KEY = 'kompagnon_access_token';
const LEGACY_TOKEN_KEY = 'kompagnon_token';

// Altreste aus Pre-Fix-14 aufraeumen (localStorage + sessionStorage)
const clearLegacyToken = () => {
  try { localStorage.removeItem(LEGACY_TOKEN_KEY); } catch { /* ignore */ }
  try { sessionStorage.removeItem(LEGACY_TOKEN_KEY); } catch { /* ignore */ }
};

const readUserFromStorage = () => {
  try {
    const raw = sessionStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => readUserFromStorage());
  const [loading, setLoading] = useState(true);
  // Token aus localStorage hydratisieren — Mobile-Safari-Fallback.
  // Auf Desktops ist der Wert oft null, weil die Auth via httpOnly-Cookie
  // laeuft; der fetch-Patch in config.js haengt den Bearer nur an wenn
  // der Wert gesetzt ist.
  const [token, setToken] = useState(() => {
    try { return localStorage.getItem(TOKEN_KEY) || null; } catch { return null; }
  });

  useEffect(() => {
    clearLegacyToken();
    loadUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadUser = async () => {
    try {
      // Browser sendet httpOnly-Cookie automatisch (via config.js fetch-patch)
      const res = await fetch(`${API_BASE_URL}/api/auth/me`);
      if (res.ok) {
        const fresh = await res.json();
        setUser(fresh);
        try { sessionStorage.setItem(USER_KEY, JSON.stringify(fresh)); } catch { /* ignore */ }
      } else {
        // Kein gueltiger Cookie / Bearer → User komplett zuruecksetzen
        setUser(null);
        setToken(null);
        try { sessionStorage.removeItem(USER_KEY); } catch { /* ignore */ }
        try { localStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ }
      }
    } catch {
      setUser(null);
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  const login = (newToken, userData) => {
    setToken(newToken);
    setUser(userData);
    try { sessionStorage.setItem(USER_KEY, JSON.stringify(userData)); } catch { /* ignore */ }
    // Mobile-Safari-Fallback: Token persistent in localStorage speichern,
    // damit er nach dem Reload wieder als Bearer-Header angehaengt werden kann.
    if (newToken) {
      try { localStorage.setItem(TOKEN_KEY, newToken); } catch { /* ignore */ }
    }
  };

  const logout = () => {
    // Best-effort Server-Revokation — Cookie wird vom Backend geloescht.
    try {
      fetch(`${API_BASE_URL}/api/auth/logout`, {
        method: 'POST',
        keepalive: true,
      }).catch(() => {});
    } catch { /* ignore */ }

    clearLegacyToken();
    try { sessionStorage.removeItem(USER_KEY); } catch { /* ignore */ }
    try { localStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ }
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
  // credentials: 'include' kommt automatisch via config.js fetch-Patch,
  // trotzdem explizit setzen fuer Klarheit.
  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  // 401 → sauber ausloggen. Login-Endpunkte ausnehmen, sonst wird
  // jeder fehlerhafte Login-Versuch zum Force-Logout.
  if (response.status === 401 && !url.includes('/api/auth/login')) {
    try { sessionStorage.removeItem(USER_KEY); } catch { /* ignore */ }
    try { localStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ }
    clearLegacyToken();
    if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
      window.location.href = '/login';
    }
  }

  return response;
}
