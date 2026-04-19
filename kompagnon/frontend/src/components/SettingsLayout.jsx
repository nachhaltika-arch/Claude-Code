import React, { useEffect } from 'react';
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

// ── Hilfskomponente: Settings-Zeile ─────────────────────────────
function SettingRow({ icon, bg, label, val, path, isLast }) {
  const navigate = useNavigate();
  return (
    <div
      onClick={() => navigate(path)}
      style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '13px 14px',
        borderBottom: isLast ? 'none' : '0.5px solid #D5E0E2',
        cursor: 'pointer',
        minHeight: 52,
        fontFamily: 'var(--font-sans)',
      }}
    >
      <div style={{
        width: 32, height: 32, borderRadius: 8,
        background: bg,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 16, flexShrink: 0,
      }}>
        {icon}
      </div>
      <span style={{ flex: 1, fontSize: 13, fontWeight: 700, color: '#000' }}>{label}</span>
      <span style={{ fontSize: 11, color: '#9AACAE' }}>{val}</span>
      <span style={{ color: '#9AACAE', fontSize: 14 }}>›</span>
    </div>
  );
}

// ── Hilfskomponente: Abmelden-Button ────────────────────────────
function LogoutButton() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  return (
    <div
      onClick={() => { logout(); navigate('/'); }}
      style={{
        background: '#FDECEA',
        border: '0.5px solid rgba(192,57,43,.2)',
        borderRadius: 10,
        padding: '13px',
        textAlign: 'center',
        fontSize: 13, fontWeight: 700,
        color: '#C0392B',
        textTransform: 'uppercase',
        letterSpacing: '.04em',
        cursor: 'pointer',
        marginBottom: 16,
        fontFamily: 'var(--font-sans)',
      }}
    >
      Abmelden
    </div>
  );
}

// ── Mobile: iOS Grouped List Hub ────────────────────────────────
function MobileSettingsHub() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin' || user?.role === 'superadmin';

  const accountRows = [
    { icon: '👤', bg: '#E0F4F8', label: 'Profil', val: `${user?.first_name || ''} ${user?.last_name || ''}`.trim() || 'Anzeigen', path: '/app/settings/profile' },
    { icon: '🔐', bg: '#E3F6EF', label: 'Sicherheit & 2FA', val: 'Einstellungen', path: '/app/settings/security' },
  ];

  const teamRows = [
    { icon: '🧑', bg: '#FFFBE0', label: 'Benutzerverwaltung', val: 'Verwalten', path: '/app/settings/users' },
    { icon: '👥', bg: '#FDECEA', label: 'Rollenverwaltung', val: 'Verwalten', path: '/app/settings/roles' },
  ];

  const systemRows = [
    { icon: '🔑', bg: '#F0F4F5', label: 'API-Keys & System', val: 'Konfigurieren', path: '/app/settings/system' },
    { icon: '🌐', bg: '#E0F4F8', label: 'KAS Website',       val: 'Verwalten',     path: '/app/settings/kas-website' },
    { icon: '🗂️', bg: '#F0F4F5', label: 'Templates',         val: 'Bibliothek',    path: '/app/settings/templates' },
    { icon: '💳', bg: '#FFFBE0', label: 'Abonnement',        val: 'Verwalten',     path: '/app/settings/subscription' },
  ];

  const productRows = [
    { icon: '🛠️', bg: '#F0F4F5', label: 'Produktentwicklung', val: 'Roadmap',        path: '/app/product' },
    { icon: '✏️', bg: '#E0F4F8', label: 'Produkteditor',      val: 'Pakete & Preise', path: '/app/product-editor' },
  ];

  const groupStyle = {
    background: '#fff',
    border: '0.5px solid #D5E0E2',
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 10,
  };

  const groupLabelStyle = {
    fontSize: 9, fontWeight: 900,
    color: '#9AACAE',
    textTransform: 'uppercase',
    letterSpacing: '.1em',
    padding: '10px 14px 4px',
    fontFamily: 'var(--font-sans)',
  };

  return (
    <div style={{ background: 'var(--surface, #F0F4F5)', minHeight: '100%', fontFamily: 'var(--font-sans)' }}>

      {/* User-Card */}
      <div style={{
        background: '#004F59',
        padding: '20px 16px 18px',
        display: 'flex', alignItems: 'center', gap: 14,
      }}>
        <div style={{
          width: 52, height: 52, borderRadius: '50%',
          background: '#008EAA',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 16, fontWeight: 900, color: '#fff',
          fontFamily: 'var(--font-sans)',
          flexShrink: 0,
        }}>
          {((user?.first_name?.[0] || '') + (user?.last_name?.[0] || '')) || 'U'}
        </div>
        <div style={{ minWidth: 0 }}>
          <div style={{
            fontFamily: "'Barlow Condensed', var(--font-sans)",
            fontSize: 18, fontWeight: 700, color: '#fff',
            textTransform: 'uppercase',
            letterSpacing: '.02em',
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }}>
            {user?.first_name} {user?.last_name}
          </div>
          <div style={{
            fontSize: 10, fontWeight: 900,
            color: '#FAE600',
            textTransform: 'uppercase',
            letterSpacing: '.1em',
            marginTop: 2,
          }}>
            {user?.role || 'Nutzer'}
          </div>
        </div>
      </div>

      {/* Grouped List */}
      <div style={{ padding: 12 }}>

        {/* Account */}
        <div style={groupStyle}>
          <div style={groupLabelStyle}>Account</div>
          {accountRows.map((item, i) => (
            <SettingRow key={item.path} {...item} isLast={i === accountRows.length - 1} />
          ))}
        </div>

        {/* Team — nur Admin */}
        {isAdmin && (
          <div style={groupStyle}>
            <div style={groupLabelStyle}>Team</div>
            {teamRows.map((item, i) => (
              <SettingRow key={item.path} {...item} isLast={i === teamRows.length - 1} />
            ))}
          </div>
        )}

        {/* System — nur Admin */}
        {isAdmin && (
          <div style={groupStyle}>
            <div style={groupLabelStyle}>System</div>
            {systemRows.map((item, i) => (
              <SettingRow key={item.path} {...item} isLast={i === systemRows.length - 1} />
            ))}
          </div>
        )}

        {/* Produkt — nur Admin */}
        {isAdmin && (
          <div style={groupStyle}>
            <div style={groupLabelStyle}>Produkt</div>
            {productRows.map((item, i) => (
              <SettingRow key={item.path} {...item} isLast={i === productRows.length - 1} />
            ))}
          </div>
        )}

        {/* Benachrichtigungen */}
        <div style={groupStyle}>
          <div style={groupLabelStyle}>Benachrichtigungen</div>
          <SettingRow
            icon="🔔"
            bg="#E3F6EF"
            label="Benachrichtigungen"
            val="Einstellungen"
            path="/app/settings/notifications"
            isLast
          />
        </div>

        <LogoutButton />

      </div>
    </div>
  );
}

// ── Haupt-Layout ────────────────────────────────────────────────
export default function SettingsLayout() {
  const { user } = useAuth();
  const { isMobile } = useScreenSize();
  const navigate = useNavigate();
  const location = useLocation();
  const items = SETTINGS_NAV.filter((i) => i.roles.includes(user?.role));

  // Mobile + root /app/settings → iOS Grouped List Hub
  const isRootSettings = location.pathname === '/app/settings' || location.pathname === '/app/settings/';

  // Desktop: wenn irgendwie auf /app/settings gelandet, direkt zu /profile
  useEffect(() => {
    if (!isMobile && isRootSettings) {
      navigate('/app/settings/profile', { replace: true });
    }
  }, [isMobile, isRootSettings, navigate]);

  if (isMobile && isRootSettings) {
    return <MobileSettingsHub />;
  }

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
    <div style={{ flex: 1, minWidth: 0 }}>
      <Outlet />
    </div>
  );
}
