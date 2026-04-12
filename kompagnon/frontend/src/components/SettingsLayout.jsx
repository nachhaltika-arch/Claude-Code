import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';

const SETTINGS_NAV = [
  { label: 'Profil', path: '/app/settings/profile', icon: '👤', roles: ['admin', 'superadmin', 'auditor', 'nutzer', 'kunde'] },
  { label: 'Sicherheit', path: '/app/settings/security', icon: '🔐', roles: ['admin', 'superadmin', 'auditor', 'nutzer', 'kunde'] },
  { label: 'Rollenverwaltung', path: '/app/settings/roles', icon: '👥', roles: ['admin', 'superadmin'] },
  { label: 'Benutzerverwaltung', path: '/app/settings/users', icon: '🧑‍💼', roles: ['admin', 'superadmin'] },
  { label: 'System', path: '/app/settings/system', icon: '🏢', roles: ['admin', 'superadmin'] },
  { label: 'KAS Website', path: '/app/settings/kas-website', icon: '🌐', roles: ['admin', 'superadmin'] },
  { label: 'Benachrichtigungen', path: '/app/settings/notifications', icon: '📧', roles: ['admin', 'superadmin', 'auditor'] },
  { label: 'Abonnement', path: '/app/settings/subscription', icon: '💳', roles: ['nutzer', 'kunde'] },
  { label: 'Templates', path: '/app/settings/templates', icon: '🗂️', roles: ['admin', 'superadmin'] },
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
        <div style={{ display: 'flex', gap: 4, overflowX: 'auto', paddingBottom: 8, marginBottom: 20, borderBottom: '1px solid var(--border-light)' }}>
          {items.map((item) => {
            const active = location.pathname === item.path;
            return (
              <button key={item.path} onClick={() => navigate(item.path)} style={{
                padding: '7px 12px', background: 'none', border: 'none', whiteSpace: 'nowrap',
                borderBottom: active ? '2px solid var(--brand-primary)' : '2px solid transparent',
                color: active ? 'var(--brand-primary)' : 'var(--text-secondary)',
                fontWeight: active ? 500 : 400, fontSize: 13, cursor: 'pointer', marginBottom: -1,
                fontFamily: 'var(--font-sans)',
              }}>
                {item.icon} {item.label}
              </button>
            );
          })}
        </div>
        <Outlet />
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', gap: 20 }}>
      <nav style={{ width: 220, flexShrink: 0 }}>
        <div style={{
          background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-light)', overflow: 'hidden', padding: 4,
        }}>
          {items.map((item) => {
            const active = location.pathname === item.path;
            return (
              <button key={item.path} onClick={() => navigate(item.path)}
              className={`kc-nav-item${active ? ' kc-nav-item--active' : ''}`}
              style={{
                width: '100%', display: 'flex', alignItems: 'center', gap: 8,
                padding: '7px 12px', borderRadius: 'var(--radius-md)',
                border: 'none', fontSize: 13, cursor: 'pointer',
                textAlign: 'left', fontFamily: 'var(--font-sans)',
              }}
              >
                <span style={{ fontSize: 14 }}>{item.icon}</span> {item.label}
              </button>
            );
          })}
        </div>
      </nav>
      <div style={{ flex: 1, minWidth: 0 }}>
        <Outlet />
      </div>
    </div>
  );
}
