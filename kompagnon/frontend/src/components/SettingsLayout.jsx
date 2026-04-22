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

function SettingRow({ icon, bg, label, val, path }) {
  const navigate = useNavigate();
  return (
    <button
      onClick={() => navigate(path)}
      style={{
        width: '100%', display: 'flex', alignItems: 'center', gap: 12,
        padding: '11px 14px', border: 'none', background: 'none',
        cursor: 'pointer', borderTop: '0.5px solid #F0F4F5', textAlign: 'left',
        fontFamily: 'var(--font-sans)',
      }}
    >
      <span style={{
        width: 32, height: 32, borderRadius: 8, background: bg,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 16, flexShrink: 0,
      }}>
        {icon}
      </span>
      <span style={{ flex: 1, fontSize: 14, fontWeight: 500, color: '#1A2A2C' }}>
        {label}
      </span>
      <span style={{ fontSize: 12, color: '#9AACAE', marginRight: 4 }}>{val}</span>
      <span style={{ fontSize: 16, color: '#9AACAE' }}>›</span>
    </button>
  );
}

function GroupLabel({ children }) {
  return (
    <div style={{
      fontSize: 9, fontWeight: 900, color: '#9AACAE',
      textTransform: 'uppercase', letterSpacing: '.1em',
      padding: '10px 14px 4px',
    }}>
      {children}
    </div>
  );
}

function SettingsGroup({ children }) {
  return (
    <div style={{
      background: '#fff', border: '0.5px solid #D5E0E2',
      borderRadius: 12, overflow: 'hidden', marginBottom: 10,
    }}>
      {children}
    </div>
  );
}

export default function SettingsLayout() {
  const { user } = useAuth();
  const { isMobile } = useScreenSize();
  const navigate = useNavigate();
  const location = useLocation();
  const items = SETTINGS_NAV.filter((i) => i.roles.includes(user?.role));
  const isAdmin = user?.role === 'admin' || user?.role === 'superadmin';

  if (isMobile) {
    /* ── Mobile: grouped list view ── */
    if (location.pathname === '/app/settings') {
      return (
        <div style={{ padding: '0 12px 24px' }}>

          {/* Account */}
          <SettingsGroup>
            <GroupLabel>Account</GroupLabel>
            <SettingRow icon="👤" bg="#F0F4F5" label="Profil"     val="Bearbeiten"  path="/app/settings/profile"   />
            <SettingRow icon="🔐" bg="#E0F4F8" label="Sicherheit" val="2FA & Passwort" path="/app/settings/security" />
          </SettingsGroup>

          {/* Team — nur Admin */}
          {isAdmin && (
            <SettingsGroup>
              <GroupLabel>Team</GroupLabel>
              <SettingRow icon="🧑‍💼" bg="#F0F4F5" label="Benutzerverwaltung" val="Verwalten" path="/app/settings/users" />
              <SettingRow icon="👥"  bg="#E0F4F8" label="Rollenverwaltung"    val="Rollen"   path="/app/settings/roles" />
            </SettingsGroup>
          )}

          {/* System — nur Admin */}
          {isAdmin && (
            <SettingsGroup>
              <GroupLabel>System</GroupLabel>
              <SettingRow icon="🔑" bg="#F0F4F5" label="System & API-Keys" val="Konfigurieren" path="/app/settings/system"       />
              <SettingRow icon="🌐" bg="#E0F4F8" label="KAS Website"       val="Seiten"        path="/app/settings/kas-website"  />
              <SettingRow icon="🗂️" bg="#FFF9CC" label="Templates"          val="Vorlagen"      path="/app/settings/templates"    />
              <SettingRow icon="💳" bg="#F0F4F5" label="Abonnement"         val="Professional"  path="/app/settings/subscription" />
            </SettingsGroup>
          )}

          {/* Produkt — nur Admin */}
          {isAdmin && (
            <SettingsGroup>
              <GroupLabel>Produkt</GroupLabel>
              <SettingRow icon="🛠️" bg="#F0F4F5" label="Produktentwicklung" val="Roadmap"       path="/app/product"        />
              <SettingRow icon="✏️" bg="#E0F4F8" label="Produkteditor"      val="Pakete & Preise" path="/app/product-editor" />
            </SettingsGroup>
          )}

          {/* Benachrichtigungen */}
          <SettingsGroup>
            <GroupLabel>Benachrichtigungen</GroupLabel>
            <SettingRow icon="🔔" bg="#F0F4F5" label="Benachrichtigungen" val="Einstellungen" path="/app/settings/notifications" />
          </SettingsGroup>

        </div>
      );
    }

    /* Sub-page: horizontal tab bar */
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
