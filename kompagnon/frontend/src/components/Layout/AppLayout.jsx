import React, { useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useScreenSize } from '../../utils/responsive';
import { useTheme } from '../../context/ThemeContext';
import Logo from '../Logo';
import KompagnonLogo from '../KompagnonLogo';

// ── SVG Icons (16x16) ──────────────────────────────────────────

const icons = {
  grid: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="1.5" y="1.5" width="5" height="5" rx="1"/><rect x="9.5" y="1.5" width="5" height="5" rx="1"/>
      <rect x="1.5" y="9.5" width="5" height="5" rx="1"/><rect x="9.5" y="9.5" width="5" height="5" rx="1"/>
    </svg>
  ),
  chart: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="8" width="3" height="6" rx="0.5"/><rect x="6.5" y="4" width="3" height="10" rx="0.5"/>
      <rect x="11" y="2" width="3" height="12" rx="0.5"/>
    </svg>
  ),
  users: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="6" cy="5" r="2.5"/><path d="M1.5 14c0-2.5 2-4.5 4.5-4.5s4.5 2 4.5 4.5"/>
      <circle cx="11" cy="5.5" r="1.8"/><path d="M11 9.5c1.8 0 3.5 1.3 3.5 3.5"/>
    </svg>
  ),
  docCheck: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 1.5H4a1.5 1.5 0 00-1.5 1.5v10A1.5 1.5 0 004 14.5h8a1.5 1.5 0 001.5-1.5V6L9 1.5z"/>
      <path d="M6 10l1.5 1.5L10 8"/>
    </svg>
  ),
  gradCap: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8 2L1.5 6 8 10l6.5-4L8 2z"/><path d="M4 8v3.5c0 1 1.8 2 4 2s4-1 4-2V8"/>
      <path d="M14.5 6v4.5"/>
    </svg>
  ),
  gear: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="8" cy="8" r="2"/><path d="M13.4 10a1.2 1.2 0 00.2 1.3l.04.04a1.44 1.44 0 11-2.04 2.04l-.04-.04a1.2 1.2 0 00-1.3-.2 1.2 1.2 0 00-.72 1.1v.12a1.44 1.44 0 01-2.88 0v-.06a1.2 1.2 0 00-.78-1.1 1.2 1.2 0 00-1.3.2l-.04.04a1.44 1.44 0 11-2.04-2.04l.04-.04a1.2 1.2 0 00.2-1.3 1.2 1.2 0 00-1.1-.72h-.12a1.44 1.44 0 010-2.88h.06a1.2 1.2 0 001.1-.78 1.2 1.2 0 00-.2-1.3l-.04-.04A1.44 1.44 0 114.3 2.24l.04.04a1.2 1.2 0 001.3.2h.06a1.2 1.2 0 00.72-1.1V1.26a1.44 1.44 0 012.88 0v.06a1.2 1.2 0 00.72 1.1 1.2 1.2 0 001.3-.2l.04-.04a1.44 1.44 0 112.04 2.04l-.04.04a1.2 1.2 0 00-.2 1.3v.06a1.2 1.2 0 001.1.72h.12a1.44 1.44 0 010 2.88h-.06a1.2 1.2 0 00-1.1.72z"/>
    </svg>
  ),
  key: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="10.5" cy="5.5" r="3"/><path d="M2 14l5.3-5.3"/><path d="M5.8 10.2l1.5 1.5"/>
    </svg>
  ),
  book: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 2.5A1.5 1.5 0 013.5 1h9A1.5 1.5 0 0114 2.5v11a1.5 1.5 0 01-1.5 1.5h-9A1.5 1.5 0 012 13.5V2.5z"/>
      <path d="M5 1v14M5 5h6M5 8h6M5 11h4"/>
    </svg>
  ),
  dots: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
      <circle cx="4" cy="8" r="1.2"/><circle cx="8" cy="8" r="1.2"/><circle cx="12" cy="8" r="1.2"/>
    </svg>
  ),
  logout: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 14H3a1 1 0 01-1-1V3a1 1 0 011-1h3"/><path d="M10.5 11.5L14 8l-3.5-3.5"/><path d="M14 8H6"/>
    </svg>
  ),
};

// ── Nav structure ──────────────────────────────────────────────

const NAV_SECTIONS = [
  {
    title: 'Übersicht',
    items: [
      { label: 'Dashboard', path: '/app/dashboard', icon: 'grid' },
    ],
  },
  {
    title: 'Sales',
    items: [
      { label: 'Vertriebspipeline', path: '/app/sales',     icon: 'chart' },
      { label: 'Unternehmen',       path: '/app/companies', icon: 'users', activePaths: ['/app/companies', '/app/leads/'] },
      { label: 'Domain Import',     path: '/app/import',    icon: 'users' },
      { label: 'Export',            path: '/app/export',    icon: 'docCheck' },
      { label: 'Website Audit',     path: '/app/audit',     icon: 'docCheck' },
    ],
  },
  {
    title: 'Delivery',
    items: [
      { label: 'Projektpipeline', path: '/app/leads', icon: 'chart', exactMatch: true },
      { label: 'Kundenprojekte', path: '/app/projects', icon: 'users' },
    ],
  },
  {
    title: 'Qualität',
    items: [
      { label: 'Support Tickets', path: '/app/tickets', icon: 'docCheck' },
      { label: 'Produktentwicklung', path: '/app/product', icon: 'gear', adminOnly: true },
      { label: 'QR-Generator', path: '/app/qr-generator', icon: 'qr', adminOnly: true },
    ],
  },
  {
    title: 'Inhalte',
    items: [
      { label: 'Kurse', path: '/app/courses', icon: 'book' },
      { label: 'Akademy', path: '/app/academy', icon: 'gradCap' },
      { label: 'Kurse verwalten', path: '/app/akademie/admin', icon: 'gear', adminOnly: true },
    ],
  },
  {
    title: 'Einstellungen',
    items: [
      { label: 'Einstellungen', path: '/app/settings', icon: 'gear' },
    ],
  },
];

const PAGE_NAMES = {
  '/app/dashboard': 'Dashboard',
  '/app/portal': 'Mein Projekt',
  '/app/sales': 'Vertriebspipeline',
  '/app/leads': 'Projektpipeline',
  '/app/customers': 'Kunden',
  '/app/audit': 'Website Audit',
  '/app/akademie': 'Akademy',
  '/app/courses': 'Kurse',
  '/app/academy': 'Akademy',
  '/app/akademie/admin': 'Kurse verwalten',
  '/app/academy/admin': 'Kurse verwalten',
  '/app/settings': 'Einstellungen',
  '/app/projects': 'Kundenprojekte',
  '/app/companies': 'Unternehmen',
  '/app/import': 'Domain Import',
  '/app/export': 'Export',
  '/app/tickets': 'Support Tickets',
  '/app/profile': 'Profil',
  '/app/checklists': 'Checklisten',
  '/app/product': 'Produktentwicklung',
};

const MOBILE_TABS = [
  { label: 'Dashboard', path: '/app/dashboard', icon: 'grid' },
  { label: 'Vertrieb', path: '/app/sales', icon: 'chart' },
  { label: 'Projekte', path: '/app/leads', icon: 'users' },
  { label: 'Audit', path: '/app/audit', icon: 'docCheck' },
  { label: 'Tickets', path: '/app/tickets', icon: 'key' },
];

// ── Sidebar ────────────────────────────────────────────────────

function SidebarNav({ badges }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, hasRole } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [menuOpen, setMenuOpen] = useState(false);

  const isActive = (item) => {
    const p = typeof item === 'string' ? item : item.path;
    if (item.exactMatch)  return location.pathname === p;
    if (item.activePaths) return item.activePaths.some(ap =>
      ap.endsWith('/') ? location.pathname.startsWith(ap) : location.pathname === ap
    );
    return location.pathname === p || location.pathname.startsWith(p + '/');
  };

  return (
    <aside style={{
      position: 'fixed', left: 0, top: 0, bottom: 0,
      width: 'var(--sidebar-width)', background: 'var(--bg-sidebar)',
      borderRight: '1px solid var(--border-light)',
      display: 'flex', flexDirection: 'column',
      zIndex: 40, overflowY: 'auto',
    }}>
      {/* Logo */}
      <div style={{
        padding: '20px 16px 18px', borderBottom: '1px solid var(--border-light)',
        cursor: 'pointer',
      }} onClick={() => navigate('/app/dashboard')}>
        <KompagnonLogo height={36} variant={theme === 'dark' ? 'white' : 'color'} />
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '12px 10px', overflowY: 'auto' }}>
        {user?.role === 'kunde' ? (
          /* ── Kunde: only these four items ── */
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-tertiary)', opacity: 0.4, letterSpacing: '0.1em', padding: '0 10px', marginBottom: 4 }}>
              Mein Bereich
            </div>
            {[
              { label: 'Dashboard',    path: '/app/dashboard',                                            icon: '🏠' },
              { label: 'Meine Kartei', path: user.lead_id ? `/app/leads/${user.lead_id}` : '/app/dashboard', icon: '📋' },
              { label: 'Akademie',     path: '/app/academy',                                              icon: '🎓' },
              { label: 'Einstellungen',path: '/app/settings',                                             icon: '⚙️' },
            ].map((item) => {
              const active = isActive(item);
              return (
                <button key={item.path} onClick={() => navigate(item.path)} style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: 10,
                  padding: '7px 10px', background: active ? 'var(--bg-active)' : 'transparent',
                  border: 'none', borderRadius: 'var(--radius-md)', cursor: 'pointer',
                  color: active ? 'var(--brand-primary)' : 'var(--text-secondary)', textAlign: 'left',
                  fontWeight: active ? 500 : 400, fontSize: 13, fontFamily: 'var(--font-sans)',
                  transition: 'background var(--transition-fast), color var(--transition-fast)',
                }}
                onMouseEnter={e => { if (!active) { e.currentTarget.style.background = 'var(--bg-hover)'; e.currentTarget.style.color = 'var(--text-primary)'; }}}
                onMouseLeave={e => { if (!active) { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)'; }}}
                >
                  <span style={{ fontSize: 16, flexShrink: 0 }}>{item.icon}</span>
                  {item.label}
                </button>
              );
            })}
          </div>
        ) : (
          /* ── All other roles: full NAV_SECTIONS ── */
          NAV_SECTIONS.map((section) => {
            const visibleItems = section.items.filter(i => !i.adminOnly || hasRole('admin'));
            if (visibleItems.length === 0) return null;
            return (
              <div key={section.title} style={{ marginBottom: 20 }}>
                <div style={{
                  fontSize: 10, fontWeight: 500, color: 'var(--text-tertiary)',
                  opacity: 0.4, letterSpacing: '0.1em', padding: '0 10px', marginBottom: 4,
                }}>
                  {section.title}
                </div>
                {visibleItems.map((item) => {
                  const active = isActive(item);
                  return (
                    <button
                      key={item.path}
                      onClick={() => navigate(item.path)}
                      style={{
                        width: '100%', display: 'flex', alignItems: 'center',
                        padding: '7px 10px', border: 'none', borderRadius: 'var(--radius-md)',
                        cursor: 'pointer', fontSize: 13, textAlign: 'left',
                        fontFamily: 'var(--font-sans)',
                        background: active ? 'var(--bg-active)' : 'transparent',
                        color: active ? 'var(--brand-primary)' : 'var(--text-secondary)',
                        fontWeight: active ? 500 : 400,
                        transition: 'background var(--transition-fast), color var(--transition-fast)',
                      }}
                      onMouseEnter={e => { if (!active) { e.currentTarget.style.background = 'var(--bg-hover)'; e.currentTarget.style.color = 'var(--text-primary)'; }}}
                      onMouseLeave={e => { if (!active) { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)'; }}}
                    >
                      <span>{item.label}</span>
                      {item.badgeKey && badges[item.badgeKey] > 0 && (
                        <span style={{
                          marginLeft: 'auto', fontSize: 10, padding: '1px 6px', borderRadius: 10,
                          background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', fontWeight: 600,
                        }}>
                          {badges[item.badgeKey]}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            );
          })
        )}
      </nav>

      {/* Footer */}
      {user && (
        <div style={{
          marginTop: 'auto', borderTop: '1px solid var(--border-light)',
          padding: '12px 10px', position: 'relative',
        }}>
          {/* Theme toggle */}
          <div style={{ borderBottom: '1px solid var(--border-light)', paddingBottom: 8, marginBottom: 8 }}>
            <button
              onClick={toggleTheme}
              style={{
                width: '100%', display: 'flex', alignItems: 'center', gap: 10,
                padding: '6px 8px', border: 'none', borderRadius: 'var(--radius-md)',
                background: 'transparent', cursor: 'pointer',
                color: 'var(--text-secondary)', fontFamily: 'var(--font-sans)',
                transition: 'background var(--transition-fast), color var(--transition-fast)',
              }}
              onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg-hover)'; e.currentTarget.style.color = 'var(--text-primary)'; }}
              onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)'; }}
            >
              <span style={{ fontSize: 16, display: 'flex', flexShrink: 0 }}>
                {theme === 'dark' ? '☀️' : '🌙'}
              </span>
              <span style={{ fontSize: 13, fontWeight: 400 }}>
                {theme === 'dark' ? 'Hell' : 'Dunkel'}
              </span>
            </button>
          </div>

          <div style={{
            display: 'flex', alignItems: 'center', gap: 10, padding: '6px 8px',
            borderRadius: 'var(--radius-md)',
          }}>
            <div style={{
              width: 32, height: 32, borderRadius: '50%',
              background: 'var(--brand-primary-light)', color: 'var(--brand-primary)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 13, fontWeight: 600, flexShrink: 0,
            }}>
              {(user.first_name?.[0] || 'U').toUpperCase()}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user.first_name} {user.last_name}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'capitalize' }}>
                {user.role}
              </div>
            </div>
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              style={{
                background: 'none', border: 'none', padding: 4,
                color: 'var(--text-tertiary)', cursor: 'pointer',
                display: 'flex', borderRadius: 'var(--radius-sm)',
                transition: 'color var(--transition-fast)',
              }}
            >
              {icons.dots}
            </button>
          </div>

          {menuOpen && (
            <>
              <div style={{ position: 'fixed', inset: 0, zIndex: 50 }} onClick={() => setMenuOpen(false)} />
              <div style={{
                position: 'absolute', bottom: '100%', left: 10, right: 10,
                background: 'var(--bg-elevated)', border: '1px solid var(--border-light)',
                borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-lg)',
                padding: 4, zIndex: 51, marginBottom: 4,
              }}>
                <div
                  onClick={toggleTheme}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '10px 10px', cursor: 'pointer', fontSize: 13,
                    color: 'var(--text-primary)', borderBottom: '1px solid var(--border-light)',
                    marginBottom: 4,
                  }}
                >
                  <span>{theme === 'dark' ? '☀️ Hell' : '🌙 Dunkel'}</span>
                  <div style={{
                    width: 36, height: 20, borderRadius: 10,
                    background: theme === 'dark' ? 'var(--brand-primary)' : 'var(--border-light)',
                    position: 'relative', transition: 'background 0.2s',
                  }}>
                    <div style={{
                      position: 'absolute', top: 2, left: theme === 'dark' ? 18 : 2,
                      width: 16, height: 16, borderRadius: '50%',
                      background: '#fff', transition: 'left 0.2s',
                    }} />
                  </div>
                </div>
                <button
                  onClick={() => { navigate('/app/profile'); setMenuOpen(false); }}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: 8,
                    padding: '7px 10px', border: 'none', borderRadius: 'var(--radius-sm)',
                    background: 'transparent', cursor: 'pointer', fontSize: 13,
                    color: 'var(--text-secondary)', fontFamily: 'var(--font-sans)',
                    transition: 'background var(--transition-fast)',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  Profil
                </button>
                <button
                  onClick={() => { logout(); navigate('/'); setMenuOpen(false); }}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: 8,
                    padding: '7px 10px', border: 'none', borderRadius: 'var(--radius-sm)',
                    background: 'transparent', cursor: 'pointer', fontSize: 13,
                    color: 'var(--status-danger-text)', fontFamily: 'var(--font-sans)',
                    transition: 'background var(--transition-fast)',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--status-danger-bg)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  {icons.logout}
                  <span>Abmelden</span>
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </aside>
  );
}

// ── Topbar ─────────────────────────────────────────────────────

function Topbar({ pageName, ctaLabel, ctaAction }) {
  return (
    <header style={{
      height: 52,
      borderBottom: '1px solid var(--border-light)',
      background: 'var(--bg-surface)',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 24px',
      position: 'sticky', top: 0, zIndex: 30,
      flexShrink: 0,
    }}>
      <span style={{ fontSize: 15, fontWeight: 500, color: 'var(--text-primary)' }}>
        {pageName}
      </span>
      {ctaLabel && (
        <button
          onClick={ctaAction}
          style={{
            background: 'var(--brand-primary)', color: 'var(--text-inverse)',
            border: 'none', padding: '6px 14px', borderRadius: 'var(--radius-md)',
            fontSize: 13, fontWeight: 500, cursor: 'pointer',
            fontFamily: 'var(--font-sans)',
            transition: 'background var(--transition-fast)',
          }}
          onMouseEnter={e => e.currentTarget.style.background = 'var(--brand-primary-dark)'}
          onMouseLeave={e => e.currentTarget.style.background = 'var(--brand-primary)'}
        >
          {ctaLabel}
        </button>
      )}
    </header>
  );
}

// ── Bottom Nav (Mobile) ────────────────────────────────────────

function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <nav style={{
      position: 'fixed', bottom: 0, left: 0, right: 0,
      background: 'var(--bg-surface)',
      borderTop: '1px solid var(--border-light)',
      display: 'flex', justifyContent: 'space-around',
      height: 'calc(56px + env(safe-area-inset-bottom))',
      paddingBottom: 'env(safe-area-inset-bottom)',
      alignItems: 'flex-start',
      paddingTop: 8,
      zIndex: 100,
    }}>
      {MOBILE_TABS.map((tab) => {
        const active = location.pathname === tab.path || location.pathname.startsWith(tab.path + '/');
        return (
          <button
            key={tab.path}
            onClick={() => navigate(tab.path)}
            style={{
              background: 'none', border: 'none',
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2,
              padding: '4px 8px', cursor: 'pointer', minWidth: 48,
              color: active ? 'var(--brand-primary)' : 'var(--text-tertiary)',
              transition: 'color var(--transition-fast)',
            }}
          >
            <span style={{ display: 'flex' }}>{icons[tab.icon]}</span>
            <span style={{ fontSize: 10, fontWeight: active ? 600 : 400 }}>{tab.label}</span>
          </button>
        );
      })}
    </nav>
  );
}

// ── Main Layout ────────────────────────────────────────────────

export default function AppLayout() {
  const { isMobile } = useScreenSize();
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();
  const [badges] = useState({ pipeline: 0, audits: 0 });
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const pageName = location.pathname.match(/^\/app\/leads\/\d+/) ? 'Nutzerkartei'
    : PAGE_NAMES[location.pathname]
    || Object.entries(PAGE_NAMES).find(([p]) => location.pathname.startsWith(p + '/'))?.[1]
    || 'KOMPAGNON';

  const ctaMap = {
    '/app/dashboard': null,
    '/app/leads': { label: '+ Neuer Lead', action: () => navigate('/app/import') },
    '/app/audit': { label: '+ Neues Audit', action: () => {} },
    '/app/customers': null,
  };
  const cta = ctaMap[location.pathname];

  return (
    <div style={{ height: '100vh', overflow: 'hidden', display: 'flex' }}>
      {/* Sidebar — desktop only */}
      {!isMobile && user && <SidebarNav badges={badges} />}

      {/* Main area */}
      <div style={{
        flex: 1,
        minWidth: 0,
        marginLeft: !isMobile && user ? 'var(--sidebar-width)' : 0,
        display: 'flex', flexDirection: 'column',
        height: '100vh', overflow: 'hidden',
      }}>
        {/* Topbar — desktop only */}
        {!isMobile && (
          <Topbar
            pageName={pageName}
            ctaLabel={cta?.label}
            ctaAction={cta?.action}
          />
        )}

        {/* Mobile header */}
        {isMobile && (
          <header style={{
            padding: '10px 16px', background: 'var(--bg-surface)',
            borderBottom: '1px solid var(--border-light)',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100, flexShrink: 0,
          }}>
            <div>
              <KompagnonLogo height={36} variant={theme === 'dark' ? 'white' : 'color'} />
            </div>
            <span style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-primary)' }}>
              {pageName}
            </span>
            {/* User avatar + dropdown */}
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setMobileMenuOpen(o => !o)}
                style={{
                  width: 32, height: 32, borderRadius: '50%',
                  background: 'var(--brand-primary-light)', color: 'var(--brand-primary)',
                  border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 600,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontFamily: 'var(--font-sans)',
                }}
              >
                {(user?.first_name?.[0] || 'U').toUpperCase()}
              </button>
              {mobileMenuOpen && (
                <>
                  <div
                    style={{ position: 'fixed', inset: 0, zIndex: 50 }}
                    onClick={() => setMobileMenuOpen(false)}
                  />
                  <div style={{
                    position: 'absolute', top: 'calc(100% + 8px)', right: 0,
                    background: 'var(--bg-elevated)', border: '1px solid var(--border-light)',
                    borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-lg)',
                    padding: 4, zIndex: 51, minWidth: 160,
                  }}>
                    <div style={{ padding: '8px 12px 6px', borderBottom: '1px solid var(--border-light)', marginBottom: 4 }}>
                      <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
                        {user?.first_name} {user?.last_name}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'capitalize' }}>
                        {user?.role}
                      </div>
                    </div>
                    <div
                      onClick={toggleTheme}
                      style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        padding: '10px 10px', cursor: 'pointer', fontSize: 13,
                        color: 'var(--text-primary)', borderBottom: '1px solid var(--border-light)',
                        marginBottom: 4,
                      }}
                    >
                      <span>{theme === 'dark' ? '☀️ Hell' : '🌙 Dunkel'}</span>
                      <div style={{
                        width: 36, height: 20, borderRadius: 10,
                        background: theme === 'dark' ? 'var(--brand-primary)' : 'var(--border-light)',
                        position: 'relative', transition: 'background 0.2s',
                      }}>
                        <div style={{
                          position: 'absolute', top: 2, left: theme === 'dark' ? 18 : 2,
                          width: 16, height: 16, borderRadius: '50%',
                          background: '#fff', transition: 'left 0.2s',
                        }} />
                      </div>
                    </div>
                    <button
                      onClick={() => { navigate('/app/profile'); setMobileMenuOpen(false); }}
                      style={{
                        width: '100%', display: 'flex', alignItems: 'center', gap: 8,
                        padding: '7px 10px', border: 'none', borderRadius: 'var(--radius-sm)',
                        background: 'transparent', cursor: 'pointer', fontSize: 13,
                        color: 'var(--text-secondary)', fontFamily: 'var(--font-sans)', textAlign: 'left',
                      }}
                    >
                      Profil
                    </button>
                    <button
                      onClick={() => { logout(); navigate('/'); setMobileMenuOpen(false); }}
                      style={{
                        width: '100%', display: 'flex', alignItems: 'center', gap: 8,
                        padding: '7px 10px', border: 'none', borderRadius: 'var(--radius-sm)',
                        background: 'transparent', cursor: 'pointer', fontSize: 13,
                        color: 'var(--status-danger-text)', fontFamily: 'var(--font-sans)', textAlign: 'left',
                      }}
                    >
                      {icons.logout}
                      <span>Abmelden</span>
                    </button>
                  </div>
                </>
              )}
            </div>
          </header>
        )}

        {/* Content */}
        <main style={{
          flex: 1, overflowY: 'auto', overflowX: 'hidden',
          minWidth: 0,
          padding: isMobile ? 16 : '20px 28px',
          paddingTop: isMobile ? 72 : undefined,
          paddingBottom: isMobile ? 80 : 20,
        }}>
          <div key={location.pathname} className="page-enter" style={{ maxWidth: '100%', overflowX: 'hidden' }}>
            <Outlet />
          </div>
        </main>
      </div>

      {/* Bottom nav — mobile only */}
      {isMobile && user && <BottomNav />}
    </div>
  );
}
