import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';

const N = '#0F1E3A';

const SETTINGS_NAV = [
  { label: 'Profil', path: '/app/settings/profile', icon: '👤', roles: ['admin', 'auditor', 'nutzer', 'kunde'] },
  { label: 'Sicherheit', path: '/app/settings/security', icon: '🔐', roles: ['admin', 'auditor', 'nutzer', 'kunde'] },
  { label: 'Rollenverwaltung', path: '/app/settings/roles', icon: '👥', roles: ['admin'] },
  { label: 'Benutzerverwaltung', path: '/app/settings/users', icon: '🧑‍💼', roles: ['admin'] },
  { label: 'System', path: '/app/settings/system', icon: '🏢', roles: ['admin'] },
  { label: 'Benachrichtigungen', path: '/app/settings/notifications', icon: '📧', roles: ['admin', 'auditor'] },
  { label: 'Abonnement', path: '/app/settings/subscription', icon: '💳', roles: ['admin'] },
];

export default function SettingsLayout() {
  const { user } = useAuth();
  const { isMobile } = useScreenSize();
  const navigate = useNavigate();
  const location = useLocation();
  const items = SETTINGS_NAV.filter((i) => i.roles.includes(user?.role));

  if (isMobile) {
    return (
      <div>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: N, marginBottom: 16 }}>Einstellungen</h1>
        <div style={{ display: 'flex', gap: 4, overflowX: 'auto', paddingBottom: 8, marginBottom: 20, borderBottom: '2px solid #eef0f8' }}>
          {items.map((item) => (
            <button key={item.path} onClick={() => navigate(item.path)} style={{
              padding: '8px 14px', background: 'none', border: 'none', whiteSpace: 'nowrap',
              borderBottom: location.pathname === item.path ? `3px solid ${N}` : '3px solid transparent',
              color: location.pathname === item.path ? N : '#8a9ab8', fontWeight: 700, fontSize: 13, cursor: 'pointer', marginBottom: -2,
            }}>
              {item.icon} {item.label}
            </button>
          ))}
        </div>
        <Outlet />
      </div>
    );
  }

  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 800, color: N, marginBottom: 24 }}>Einstellungen</h1>
      <div style={{ display: 'flex', gap: 24 }}>
        <nav style={{ width: 220, flexShrink: 0 }}>
          <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #eef0f8', overflow: 'hidden' }}>
            {items.map((item) => {
              const active = location.pathname === item.path;
              return (
                <button key={item.path} onClick={() => navigate(item.path)} style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px',
                  background: active ? '#f0f4ff' : 'transparent', border: 'none', borderLeft: active ? `3px solid ${N}` : '3px solid transparent',
                  color: active ? N : '#6a7a9a', fontWeight: active ? 700 : 500, fontSize: 14, cursor: 'pointer', textAlign: 'left',
                }}>
                  <span style={{ fontSize: 16 }}>{item.icon}</span> {item.label}
                </button>
              );
            })}
          </div>
        </nav>
        <div style={{ flex: 1, minWidth: 0 }}>
          <Outlet />
        </div>
      </div>
    </div>
  );
}
