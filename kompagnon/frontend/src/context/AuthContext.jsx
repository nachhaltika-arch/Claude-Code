import React, { createContext, useContext, useState, useEffect } from 'react';
import API_BASE_URL from '../config';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('kompagnon_token'));

  useEffect(() => {
    if (token) loadUser();
    else setLoading(false);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const loadUser = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setUser(await res.json());
      } else {
        logout();
      }
    } catch {
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = (newToken, userData) => {
    localStorage.setItem('kompagnon_token', newToken);
    setToken(newToken);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('kompagnon_token');
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
    // `refreshUser` gibt es, seit die Zwei-Faktor-Anmeldung sich abschalten
    // laesst (L-105): Ohne ihn stuende `totp_enabled` nach dem Abschalten
    // weiter auf `true`, bis jemand die Seite neu laedt — die Anzeige wuerde
    // also das Gegenteil dessen behaupten, was gerade passiert ist.
    <AuthContext.Provider value={{ user, token, loading, login, logout, hasRole, isSuperadmin, refreshUser: loadUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);

export async function apiCall(url, options = {}) {
  const token = localStorage.getItem('kompagnon_token');
  return fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
}
