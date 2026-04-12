import React, { createContext, useContext, useState, useEffect } from 'react';
import API_BASE_URL from '../config';

const AuthContext = createContext(null);

// ── Token-Storage ─────────────────────────────────────────────────
// Fix 14 Phase 2 — JWT ist ausschliesslich ein httpOnly-Cookie.
// Kein Token mehr in sessionStorage, kein Token in localStorage.
// Das User-Objekt bleibt in sessionStorage fuer Reload-Resilienz
// (keine sensiblen Credentials enthalten).
//
// Pages, die noch `Authorization: Bearer ${token}` bauen, sind
// harmlos: `token` ist dann `null`, das Backend akzeptiert aber
// nur noch Cookies (Phase 2 Backend-Removal), der Header wird
// ignoriert.
const USER_KEY = 'kompagnon_user';
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
  // token wird nur noch im React-State gehalten (fuer Alt-Pages, die
  // useAuth().token lesen) und verschwindet beim Reload. Die echte
  // Authentifizierung laeuft ueber den httpOnly-Cookie.
  const [token, setToken] = useState(null);

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
        // Kein gueltiger Cookie → User komplett zuruecksetzen
        setUser(null);
        setToken(null);
        try { sessionStorage.removeItem(USER_KEY); } catch { /* ignore */ }
      }
    } catch {
      setUser(null);
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  const login = (newToken, userData) => {
    // newToken wird nur noch als React-State gehalten — fuer Alt-Pages
    // die ihn ueber useAuth().token lesen. Das Backend hat bereits den
    // httpOnly-Cookie gesetzt, Token im Body ist reine Uebergangs-Info.
    setToken(newToken);
    setUser(userData);
    try { sessionStorage.setItem(USER_KEY, JSON.stringify(userData)); } catch { /* ignore */ }
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
    clearLegacyToken();
    if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
      window.location.href = '/login';
    }
  }

  return response;
}
