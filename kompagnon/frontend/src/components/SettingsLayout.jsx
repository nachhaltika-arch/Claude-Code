import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';

const SETTINGS_NAV = [
  { label: 'Profil', path: '/app/settings/profile', icon: '👤', roles: ['admin', 'superadmin', 'mitarbeiter', 'kunde'] },
  { label: 'Sicherheit', path: '/app/settings/security', icon: '🔐', roles: ['admin', 'superadmin', 'mitarbeiter', 'kunde'] },
  { label: 'Rollenverwaltung', path: '/app/settings/roles', icon: '👥', roles: ['admin', 'superadmin'] },
  { label: 'Benutzerverwaltung', path: '/app/settings/users', icon: '🧑‍💼', roles: ['admin', 'superadmin'] },
  { label: 'System', path: '/app/settings/system', icon: '🏢', roles: ['admin', 'superadmin'] },
  { label: 'KAS Website', path: '/app/settings/kas-website', icon: '🌐', roles: ['admin', 'superadmin'] },
  { label: 'Benachrichtigungen', path: '/app/settings/notifications', icon: '📧', roles: ['admin', 'superadmin', 'mitarbeiter'] },
  { label: 'Abonnement', path: '/app/settings/subscription', icon: '💳', roles: ['kunde'] },
  { label: 'Templates', path: '/app/settings/templates', icon: '🗂️', roles: ['admin', 'superadmin'] },
  { label: 'Komponenten-Bibliothek', path: '/app/settings/component-library', icon: '🧩', roles: ['admin', 'superadmin'] },
];

function SettingRow({ icon, bg, label, val, path }) {
  const navigate = useNavigate();
  return (
    <button
      onClick={() => navigate(path)}
      style={{
        width: '100%', display: 'flex', alignItems: 'center', gap: 12,
        padding: '11px 14px', border: 'none', background: 'none',
        cursor: 'pointer', borderTop: '0.5px solid var(--border-light)', textAlign: 'left',
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
      <span style={{ flex: 1, fontSize: 14, fontWeight: 500, color: 'var(--text-primary)' }}>
        {label}
      </span>
      <span style={{ fontSize: 12, color: 'var(--text-secondary)', marginRight: 4 }}>{val}</span>
      <span style={{ fontSize: 16, color: 'var(--text-secondary)' }}>›</span>
    </button>
  );
}

function GroupLabel({ children }) {
  return (
    <div style={{
      fontSize: 9, fontWeight: 900, color: 'var(--text-secondary)',
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
      background: 'var(--bg-surface)', border: '0.5px solid var(--border-light)',
      borderRadius: 12, overflow: 'hidden', marginBottom: 10,
    }}>
      {children}
    </div>
  );
}

function LogoutButton() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  return (
    <button
      onClick={() => { logout(); navigate('/'); }}
      style={{
        width: '100%', border: 'none', background: 'var(--status-danger-bg)',
        borderRadius: 10, padding: 13, textAlign: 'center',
        fontSize: 13, fontWeight: 700, color: 'var(--status-danger-text)',
        cursor: 'pointer', marginBottom: 16, fontFamily: 'var(--font-sans)',
      }}
    >
      Abmelden
    </button>
  );
}

export default function SettingsLayout() {
  const { user } = useAuth();
  const { isMobile } = useScreenSize();
  const navigate = useNavigate();
  const location = useLocation();
  const items = SETTINGS_NAV.filter((i) => i.roles.includes(user?.role));
  const isAdmin = user?.role === 'admin' || user?.role === 'superadmin';
  const initials = ((user?.first_name?.[0] || '') + (user?.last_name?.[0] || '')).toUpperCase() || 'U';

  if (isMobile) {
    /* ── Mobile: grouped list view ── */
    if (location.pathname === '/app/settings') {
      return (
        <div style={{ background: 'var(--bg-app)', minHeight: '100%' }}>

          {/* User-Card */}
          <div style={{ background: 'var(--brand-primary)', padding: '20px 16px 18px', display: 'flex', alignItems: 'center', gap: 14 }}>
            {/* Gleiche Farbe wie die Karte darunter waere unsichtbar —
              * siehe MobileSettings, derselbe Fall. */}
            <div style={{
              width: 52, height: 52, borderRadius: '50%', background: 'var(--bg-surface)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 16, fontWeight: 900, color: 'var(--brand-primary)', fontFamily: 'var(--font-sans)',
            }}>
              {initials}
            </div>
            <div>
              <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-on-brand)', textTransform: 'uppercase', fontFamily: 'var(--font-sans)' }}>
                {user?.first_name} {user?.last_name}
              </div>
              <div style={{ fontSize: 10, fontWeight: 900, color: 'var(--kc-yellow)', textTransform: 'uppercase', letterSpacing: '.1em', marginTop: 2 }}>
                {user?.role || 'Nutzer'}
              </div>
            </div>
          </div>

          <div style={{ padding: '12px 12px 24px' }}>

          {/* Account */}
          <SettingsGroup>
            <GroupLabel>Account</GroupLabel>
            <SettingRow icon="👤" bg="var(--bg-app)" label="Profil"     val="Bearbeiten"  path="/app/settings/profile"   />
            <SettingRow icon="🔐" bg="var(--status-info-bg)" label="Sicherheit" val="2FA & Passwort" path="/app/settings/security" />
          </SettingsGroup>

          {/* Team — nur Admin */}
          {isAdmin && (
            <SettingsGroup>
              <GroupLabel>Team</GroupLabel>
              <SettingRow icon="🧑‍💼" bg="var(--bg-app)" label="Benutzerverwaltung" val="Verwalten" path="/app/settings/users" />
              <SettingRow icon="👥"  bg="var(--status-info-bg)" label="Rollenverwaltung"    val="Rollen"   path="/app/settings/roles" />
            </SettingsGroup>
          )}

          {/* System — nur Admin */}
          {isAdmin && (
            <SettingsGroup>
              <GroupLabel>System</GroupLabel>
              <SettingRow icon="🔑" bg="var(--bg-app)" label="System & API-Keys" val="Konfigurieren" path="/app/settings/system"       />
              <SettingRow icon="🌐" bg="var(--status-info-bg)" label="KAS Website"       val="Seiten"        path="/app/settings/kas-website"  />
              <SettingRow icon="🗂️" bg="var(--status-warning-bg)" label="Templates"          val="Vorlagen"      path="/app/settings/templates"    />
              <SettingRow icon="🧩" bg="var(--status-info-bg)" label="Komponenten-Bibliothek" val="Editor"   path="/app/settings/component-library" />
              <SettingRow icon="💳" bg="var(--bg-app)" label="Abonnement"         val="Zahlung & Paket"  path="/app/settings/subscription" />
            </SettingsGroup>
          )}

          {/* Produkt — nur Admin */}
          {isAdmin && (
            <SettingsGroup>
              <GroupLabel>Produkt</GroupLabel>
              <SettingRow icon="🛠️" bg="var(--bg-app)" label="Produktentwicklung" val="Roadmap"       path="/app/product"        />
              <SettingRow icon="✏️" bg="var(--status-info-bg)" label="Produkteditor"      val="Pakete & Preise" path="/app/product-editor" />
            </SettingsGroup>
          )}

          {/* Benachrichtigungen */}
          <SettingsGroup>
            <GroupLabel>Benachrichtigungen</GroupLabel>
            <SettingRow icon="🔔" bg="var(--bg-app)" label="Benachrichtigungen" val="Einstellungen" path="/app/settings/notifications" />
          </SettingsGroup>

          <LogoutButton />

          </div>
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

  // ── Am Rechner: nur der Inhalt ───────────────────────────────────
  //
  // **Die Seitenleiste ist am 27.08.2026 entfallen** (Bitte David). Sie stand
  // neben dem Hauptmenue und wiederholte es zur Haelfte: Profil, Sicherheit,
  // System, Rollen- und Benutzerverwaltung und die Komponenten-Bibliothek
  // gab es an **beiden** Stellen — teils sogar mit verschiedenen Zielen.
  // „System" im Hauptmenue fuehrte auf `/app/settings` und damit auf das
  // Profil.
  //
  // Zwei Navigationen fuer dieselben Seiten sind kein Komfort, sondern eine
  // Frage, die sich der Mensch bei jedem Klick neu stellt. Alle Eintraege
  // stehen jetzt im Hauptmenue; `menueZiele.test.js` haelt fest, dass jeder
  // davon irgendwohin fuehrt.
  //
  // **Die mobile Ansicht oben bleibt.** Dort gibt es kein dauerhaft
  // sichtbares Hauptmenue, und die gruppierte Liste **ist** der
  // Einstellungsbildschirm — sie zu entfernen hiesse, auf dem Handy einen
  // Weg zu streichen statt einen doppelten zu schliessen.
  return <Outlet />;
}
